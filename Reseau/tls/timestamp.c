#include "tls_utils_v1.h"
#include <errno.h>
#include <openssl/err.h>
#include <openssl/evp.h>
#include <openssl/hmac.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/time.h>
#include <time.h>
#include <unistd.h>
#include <math.h>

#ifdef _WIN32
#include <iphlpapi.h>
#include <windows.h>
#include <winsock2.h>
#include <ws2tcpip.h>
#pragma comment(lib, "ws2_32.lib")
#pragma comment(lib, "iphlpapi.lib")
typedef SOCKET socket_t;
#define SOCKET_ERROR_VAL INVALID_SOCKET
#define CLOSE_SOCKET(s) closesocket(s)
#define SOCKET_ERRNO WSAGetLastError()
#else
#include <arpa/inet.h>
#include <fcntl.h>
#include <ifaddrs.h>
#include <netdb.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <sys/types.h>
typedef int socket_t;
#define SOCKET_ERROR_VAL -1
#define CLOSE_SOCKET(s) close(s)
#define SOCKET_ERRNO errno
#define INVALID_SOCKET -1
#define SOCKET_ERROR -1
#endif

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define PORT_12345 12345
#define PORT_1234 1234
#define MULTICAST_PORT 8000
#define BUFFER_SIZE 8192
#define MULTICAST_IP "239.255.255.250"
#define MAX_MSG_SIZE 8192
#define MULTICAST_GROUP "239.0.0.1"
#define PORT 5000
#define MAX_INTERFACES 10
#define MAX_MESSAGE_AGE 30  // Âge maximum du message en secondes
#define MAX_TIME_DIFF 3600  // Différence maximale de temps entre les systèmes (1 heure)

#ifdef _WIN32
void set_nonblocking(socket_t socket) {
  u_long mode = 1;
  if (ioctlsocket(socket, FIONBIO, &mode) == SOCKET_ERROR) {
    perror("ioctlsocket");
    exit(EXIT_FAILURE);
  }
}
#else
void set_nonblocking(socket_t socket) {
  int flags = fcntl(socket, F_GETFL, 0);
  if (flags == -1) {
    perror("fcntl F_GETFL");
    exit(EXIT_FAILURE);
  }
  if (fcntl(socket, F_SETFL, flags | O_NONBLOCK) == -1) {
    perror("fcntl F_SETFL");
    exit(EXIT_FAILURE);
  }
}
#endif

#ifdef _WIN32
void list_interfaces(char *selected_interface_ip, int selected_interface) {
  PIP_ADAPTER_INFO AdapterInfo;
  DWORD dwBufLen = sizeof(IP_ADAPTER_INFO);
  AdapterInfo = (IP_ADAPTER_INFO *)malloc(sizeof(IP_ADAPTER_INFO));

  if (GetAdaptersInfo(AdapterInfo, &dwBufLen) == ERROR_BUFFER_OVERFLOW) {
    free(AdapterInfo);
    AdapterInfo = (IP_ADAPTER_INFO *)malloc(dwBufLen);
  }

  if (GetAdaptersInfo(AdapterInfo, &dwBufLen) == NO_ERROR) {
    PIP_ADAPTER_INFO pAdapterInfo = AdapterInfo;
    int index = 1;

    while (pAdapterInfo) {
      if (pAdapterInfo->IpAddressList.IpAddress.String[0] != '0' &&
          strcmp(pAdapterInfo->IpAddressList.IpAddress.String, "0.0.0.0") !=
              0) {
        printf("%d: %s (%s)\n", index, pAdapterInfo->Description,
               pAdapterInfo->IpAddressList.IpAddress.String);
        if (index == selected_interface) {
          strcpy(selected_interface_ip,
                 pAdapterInfo->IpAddressList.IpAddress.String);
        }
        index++;
      }
      pAdapterInfo = pAdapterInfo->Next;
    }
  }
  free(AdapterInfo);
}
#else
void list_interfaces(char *selected_interface_ip, int selected_interface) {
  struct ifaddrs *ifaddr, *ifa;
  if (getifaddrs(&ifaddr) == -1) {
    perror("getifaddrs");
    exit(EXIT_FAILURE);
  }

  int index = 1;
  for (ifa = ifaddr; ifa != NULL; ifa = ifa->ifa_next) {
    if (ifa->ifa_addr == NULL)
      continue;
    if (ifa->ifa_addr->sa_family == AF_INET) {
      char interface_ip[INET_ADDRSTRLEN];
      getnameinfo(ifa->ifa_addr, sizeof(struct sockaddr_in), interface_ip,
                  INET_ADDRSTRLEN, NULL, 0, NI_NUMERICHOST);
      printf("%d: %s (%s)\n", index, ifa->ifa_name, interface_ip);
      if (index == selected_interface) {
        strcpy(selected_interface_ip, interface_ip);
      }
      index++;
    }
  }
  freeifaddrs(ifaddr);
}
#endif

void join_multicast_group(socket_t socket, const char *multicast_ip,
                          const char *interface_ip) {
  struct ip_mreq mreq;
  mreq.imr_multiaddr.s_addr = inet_addr(multicast_ip);
  mreq.imr_interface.s_addr = inet_addr(interface_ip);
#ifdef _WIN32
  if (setsockopt(socket, IPPROTO_IP, IP_ADD_MEMBERSHIP, (char *)&mreq,
                 sizeof(mreq)) == SOCKET_ERROR) {
#else
  if (setsockopt(socket, IPPROTO_IP, IP_ADD_MEMBERSHIP, &mreq, sizeof(mreq)) <
      0) {
#endif
    perror("setsockopt IP_ADD_MEMBERSHIP");
    exit(EXIT_FAILURE);
  }
}

void set_multicast_interface(socket_t socket, const char *interface_ip) {
  struct in_addr interface_addr;
  interface_addr.s_addr = inet_addr(interface_ip);
#ifdef _WIN32
  if (setsockopt(socket, IPPROTO_IP, IP_MULTICAST_IF, (char *)&interface_addr,
                 sizeof(interface_addr)) == SOCKET_ERROR) {
#else
  if (setsockopt(socket, IPPROTO_IP, IP_MULTICAST_IF, &interface_addr,
                 sizeof(interface_addr)) < 0) {
#endif
    perror("setsockopt IP_MULTICAST_IF");
    exit(EXIT_FAILURE);
  }
}

// Fonction pour convertir une chaîne hexadécimale en tableau d'octets
int hex_to_bytes(const char *hex, unsigned char *bytes, size_t len) {
  for (size_t i = 0; i < len; i++) {
    if (sscanf(hex + 2 * i, "%2hhx", &bytes[i]) != 1) {
      return 0;
    }
  }
  return 1;
}

// Fonction pour lire une clé depuis le fichier de configuration
int read_key_from_file(const char *filename, const char *key_name,
                       unsigned char *key, size_t key_len) {
  FILE *file = fopen(filename, "r");
  if (!file) {
    fprintf(stderr, "Erreur lors de l'ouverture du fichier %s\n", filename);
    return 0;
  }

  char line[256];
  char *value = NULL;
  while (fgets(line, sizeof(line), file)) {
    if (line[0] == '#' || line[0] == '\n')
      continue; // Ignorer les commentaires et lignes vides
    if (strncmp(line, key_name, strlen(key_name)) == 0 &&
        line[strlen(key_name)] == '=') {
      value = line + strlen(key_name) + 1;
      // Supprimer le retour à la ligne si présent
      char *newline = strchr(value, '\n');
      if (newline)
        *newline = '\0';
      break;
    }
  }
  fclose(file);

  if (!value) {
    fprintf(stderr, "Clé %s non trouvée dans le fichier\n", key_name);
    return 0;
  }

  if (!hex_to_bytes(value, key, key_len)) {
    fprintf(stderr, "Format de clé invalide pour %s\n", key_name);
    return 0;
  }

  return 1;
}

// Fonction pour vérifier si le message vient de notre propre interface
int is_own_message(const struct sockaddr_in *source_addr,
                   const char *selected_interface_ip) {
  char source_ip[INET_ADDRSTRLEN];
  inet_ntop(AF_INET, &(source_addr->sin_addr), source_ip, INET_ADDRSTRLEN);
  return (strcmp(source_ip, selected_interface_ip) == 0);
}

// Structure pour le message avec timestamp
#pragma pack(push, 1)  // Désactiver l'alignement pour la compatibilité
typedef struct {
    uint64_t timestamp;  // 8 bytes
    uint32_t data_length;  // 4 bytes
    char data[MAX_MSG_SIZE];  // Données
} MessageWithTimestamp;
#pragma pack(pop)  // Restaurer l'alignement par défaut

// Fonction pour vérifier si le message est trop vieux
int is_message_too_old(uint64_t message_timestamp) {
    uint64_t current_time = (uint64_t)time(NULL);
    uint64_t time_diff = (current_time > message_timestamp) ? 
                        (current_time - message_timestamp) : 
                        (message_timestamp - current_time);
    
    printf("Time check - Current: %llu, Message: %llu, Diff: %llu seconds\n", 
           current_time, message_timestamp, time_diff);
    
    // Si la différence est supérieure à 1 heure, c'est probablement un problème de synchronisation
    if (time_diff > MAX_TIME_DIFF) {
        printf("Warning: Large time difference detected (%llu seconds). This might be a system time synchronization issue.\n", time_diff);
        return 0;  // Accepter le message malgré la grande différence de temps
    }
    
    // Si la différence est supérieure à 30 secondes, c'est probablement un replay attack
    return time_diff > MAX_MESSAGE_AGE;
}

// Fonction pour parser le message avec timestamp
int parse_message_with_timestamp(const char* message, int message_length, MessageWithTimestamp* msg) {
    if (message_length < sizeof(uint64_t) + sizeof(uint32_t)) {
        printf("Message too short: %d bytes (minimum: %lu)\n", 
               message_length, sizeof(uint64_t) + sizeof(uint32_t));
        return 0;
    }
    
    // Extraire le timestamp (premiers 8 bytes)
    memcpy(&msg->timestamp, message, sizeof(uint64_t));
    
    // Extraire la longueur des données (4 bytes après le timestamp)
    memcpy(&msg->data_length, message + sizeof(uint64_t), sizeof(uint32_t));
    
    // Vérifier la longueur des données
    if (msg->data_length > MAX_MSG_SIZE) {
        printf("Data too long: %u bytes (max: %d)\n", msg->data_length, MAX_MSG_SIZE);
        return 0;
    }
    
    // Vérifier que nous avons reçu toutes les données
    if (message_length < sizeof(uint64_t) + sizeof(uint32_t) + msg->data_length) {
        printf("Incomplete message: expected %lu bytes, got %d\n", 
               sizeof(uint64_t) + sizeof(uint32_t) + msg->data_length, message_length);
        return 0;
    }
    
    // Extraire les données
    memcpy(msg->data, message + sizeof(uint64_t) + sizeof(uint32_t), msg->data_length);
    msg->data[msg->data_length] = '\0';  // Assurer la null-termination
    
    return 1;
}

int main(int argc, char *argv[]) {
#ifdef _WIN32
  WSADATA wsaData;
  if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0) {
    printf("WSAStartup failed\n");
    return 1;
  }
#endif

  socket_t socket_fd_12345, socket_fd_multicast;
  struct sockaddr_in address_12345, multicast_addr, client_address;
  socklen_t addrlen = sizeof(address_12345);

  if ((socket_fd_12345 = socket(AF_INET, SOCK_DGRAM, 0)) == SOCKET_ERROR_VAL) {
    perror("socket failed");
#ifdef _WIN32
    WSACleanup();
#endif
    exit(EXIT_FAILURE);
  }

  set_nonblocking(socket_fd_12345);

  address_12345.sin_family = AF_INET;
  address_12345.sin_addr.s_addr = INADDR_ANY;
  address_12345.sin_port = htons(PORT_12345);

  if (bind(socket_fd_12345, (struct sockaddr *)&address_12345,
           sizeof(address_12345)) == SOCKET_ERROR_VAL) {
    perror("bind failed");
    CLOSE_SOCKET(socket_fd_12345);
#ifdef _WIN32
    WSACleanup();
#endif
    exit(EXIT_FAILURE);
  }

  printf("Proxy listening on port 12345\n");

  if ((socket_fd_multicast = socket(AF_INET, SOCK_DGRAM, 0)) ==
      SOCKET_ERROR_VAL) {
    perror("socket failed");
    CLOSE_SOCKET(socket_fd_12345);
#ifdef _WIN32
    WSACleanup();
#endif
    exit(EXIT_FAILURE);
  }

  set_nonblocking(socket_fd_multicast);

  int reuse = 1;
#ifdef _WIN32
  if (setsockopt(socket_fd_multicast, SOL_SOCKET, SO_REUSEADDR, (char *)&reuse,
                 sizeof(reuse)) == SOCKET_ERROR) {
#else
  if (setsockopt(socket_fd_multicast, SOL_SOCKET, SO_REUSEADDR, &reuse,
                 sizeof(reuse)) < 0) {
#endif
    perror("setsockopt SO_REUSEADDR");
    CLOSE_SOCKET(socket_fd_12345);
    CLOSE_SOCKET(socket_fd_multicast);
#ifdef _WIN32
    WSACleanup();
#endif
    exit(EXIT_FAILURE);
  }

  memset(&multicast_addr, 0, sizeof(multicast_addr));
  multicast_addr.sin_family = AF_INET;
  multicast_addr.sin_addr.s_addr = htonl(INADDR_ANY);
  multicast_addr.sin_port = htons(MULTICAST_PORT);

  if (bind(socket_fd_multicast, (struct sockaddr *)&multicast_addr,
           sizeof(multicast_addr)) == SOCKET_ERROR_VAL) {
    perror("bind failed");
    CLOSE_SOCKET(socket_fd_12345);
    CLOSE_SOCKET(socket_fd_multicast);
#ifdef _WIN32
    WSACleanup();
#endif
    exit(EXIT_FAILURE);
  }

  printf("Available interfaces:\n");
  char selected_interface_ip[INET_ADDRSTRLEN];
  list_interfaces(selected_interface_ip, 0);

  int selected_interface;
  printf("Select an interface by number: ");
  scanf("%d", &selected_interface);

  list_interfaces(selected_interface_ip, selected_interface);

  join_multicast_group(socket_fd_multicast, MULTICAST_IP,
                       selected_interface_ip);
  printf("Joined multicast group on interface: %s\n", selected_interface_ip);

  printf("Listening for multicast messages on %s:%d\n", MULTICAST_IP,
         MULTICAST_PORT);

  fd_set readfds;
  struct timeval timeout;
  timeout.tv_sec = 1;
  timeout.tv_usec = 0;

  printf("Local IP address: %s\n", selected_interface_ip);

  // Lire les clés depuis le fichier
  unsigned char encryption_key[KEY_LENGTH];
  unsigned char iv[IV_LENGTH];
  unsigned char hmac_key[HMAC_KEY_LENGTH];

  if (!read_key_from_file("clef.txt", "encryption_key", encryption_key,
                          KEY_LENGTH) ||
      !read_key_from_file("clef.txt", "iv", iv, IV_LENGTH) ||
      !read_key_from_file("clef.txt", "hmac_key", hmac_key, HMAC_KEY_LENGTH)) {
    fprintf(stderr, "Erreur lors de la lecture des clés\n");
    return 1;
  }

  while (1) {
    FD_ZERO(&readfds);
    FD_SET(socket_fd_12345, &readfds);
    FD_SET(socket_fd_multicast, &readfds);

#ifdef _WIN32
    int activity = select(0, &readfds, NULL, NULL, &timeout);
#else
    int activity = select(FD_SETSIZE, &readfds, NULL, NULL, &timeout);
#endif

    if (activity == SOCKET_ERROR_VAL) {
      perror("select error");
      break;
    }

    if (FD_ISSET(socket_fd_12345, &readfds)) {
      char buffer[BUFFER_SIZE];
      int bytes_received =
          recvfrom(socket_fd_12345, buffer, BUFFER_SIZE - 1, 0,
                   (struct sockaddr *)&client_address, &addrlen);
      if (bytes_received > 0) {
        buffer[bytes_received] = '\0';
        printf("Received message from Python: %s\n", buffer);
        printf("Forward it to multicast group: %s\n", MULTICAST_IP);

        // S'assurer que le message ne dépasse pas MAX_MSG_SIZE
        if (bytes_received > MAX_MSG_SIZE) {
          printf("Message too large, truncating to %d bytes\n", MAX_MSG_SIZE);
          bytes_received = MAX_MSG_SIZE;
          buffer[MAX_MSG_SIZE] = '\0';
        }

        // Ajouter le timestamp au message
        MessageWithTimestamp msg_with_timestamp;
        msg_with_timestamp.timestamp = (uint64_t)time(NULL);
        msg_with_timestamp.data_length = bytes_received;
        memcpy(msg_with_timestamp.data, buffer, bytes_received);
        msg_with_timestamp.data[bytes_received] = '\0';

        printf("Sending message with timestamp: %llu\n", msg_with_timestamp.timestamp);

        // Calculer la taille totale du message avec timestamp
        int total_message_size = sizeof(MessageWithTimestamp) - MAX_MSG_SIZE + bytes_received;

        unsigned char encrypted_message[BUFFER_SIZE];
        int encrypted_length = total_message_size;  // Passer la taille totale
        encrypt_message(encryption_key, iv, (char*)&msg_with_timestamp, encrypted_message,
                        &encrypted_length);

        printf("Message size: original=%d, encrypted=%d\n", total_message_size, encrypted_length);

        unsigned char hmac[HMAC_LENGTH];
        generate_hmac(hmac_key, encrypted_message, encrypted_length, hmac);

        unsigned char final_message[BUFFER_SIZE + HMAC_LENGTH];
        memcpy(final_message, encrypted_message, encrypted_length);
        memcpy(final_message + encrypted_length, hmac, HMAC_LENGTH);
        int final_length = encrypted_length + HMAC_LENGTH;

        set_multicast_interface(socket_fd_multicast, selected_interface_ip);
        struct sockaddr_in multicast_send_addr;
        multicast_send_addr.sin_family = AF_INET;
        multicast_send_addr.sin_addr.s_addr = inet_addr(MULTICAST_IP);
        multicast_send_addr.sin_port = htons(MULTICAST_PORT);
#ifdef _WIN32
        sendto(socket_fd_multicast, (char *)final_message, final_length, 0,
#else
        sendto(socket_fd_multicast, final_message, final_length, 0,
#endif
               (struct sockaddr *)&multicast_send_addr,
               sizeof(multicast_send_addr));
      }
    }

    if (FD_ISSET(socket_fd_multicast, &readfds)) {
      unsigned char buffer[BUFFER_SIZE + HMAC_LENGTH];
#ifdef _WIN32
      int bytes_received = recvfrom(
          socket_fd_multicast, (char *)buffer, BUFFER_SIZE + HMAC_LENGTH, 0,
#else
      int bytes_received =
          recvfrom(socket_fd_multicast, buffer, BUFFER_SIZE + HMAC_LENGTH, 0,
#endif
          (struct sockaddr *)&client_address, &addrlen);
      if (bytes_received > HMAC_LENGTH) {
        // Vérifier si le message vient de notre propre interface
        if (is_own_message(&client_address, selected_interface_ip)) {
          printf("Ignoring message from own interface\n");
          continue;
        }

        printf("Received message from multicast group\n");

        int encrypted_length = bytes_received - HMAC_LENGTH;
        unsigned char *encrypted_message = buffer;
        unsigned char *received_hmac = buffer + encrypted_length;

        if (!verify_hmac(hmac_key, encrypted_message, encrypted_length,
                         received_hmac)) {
          printf("HMAC verification failed - message may be tampered\n");
          continue;
        }
        printf("HMAC verification successful\n");

        unsigned char decrypted_message[BUFFER_SIZE];
        int decrypted_length = encrypted_length;
        decrypt_message(encryption_key, iv, encrypted_message,
                        decrypted_message, &decrypted_length);

        printf("Decrypted message length: %d bytes\n", decrypted_length);

        // Vérifier le timestamp du message
        MessageWithTimestamp received_msg;
        if (!parse_message_with_timestamp((char*)decrypted_message, decrypted_length, &received_msg)) {
            printf("Failed to parse message with timestamp (decrypted length: %d, expected minimum: %lu)\n", 
                   decrypted_length, sizeof(uint64_t) + sizeof(uint32_t));
            continue;
        }

        printf("Received message timestamp: %llu\n", received_msg.timestamp);

        if (is_message_too_old(received_msg.timestamp)) {
            printf("REPLAY ATTACK DETECTED: Message is too old (timestamp: %llu)\n", received_msg.timestamp);
            continue;
        }

        struct sockaddr_in local_address;
        local_address.sin_family = AF_INET;
        local_address.sin_addr.s_addr = inet_addr("127.0.0.1");
        local_address.sin_port = htons(PORT_1234);
#ifdef _WIN32
        sendto(socket_fd_multicast, (char *)received_msg.data, received_msg.data_length,
               0,
#else
        sendto(socket_fd_multicast, received_msg.data, received_msg.data_length, 0,
#endif
               (struct sockaddr *)&local_address, sizeof(local_address));
      }
    }
  }

  CLOSE_SOCKET(socket_fd_12345);
  CLOSE_SOCKET(socket_fd_multicast);
#ifdef _WIN32
  WSACleanup();
#endif

  return 0;
}
