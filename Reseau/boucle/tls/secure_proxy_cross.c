#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <errno.h>
#include <time.h>
#include <sys/time.h>
#include <openssl/err.h>
#include <openssl/evp.h>
#include <openssl/hmac.h>
#include "tls_utils.h"

#ifdef _WIN32
    #include <winsock2.h>
    #include <ws2tcpip.h>
    #include <iphlpapi.h>
    #include <windows.h>
    #pragma comment(lib, "ws2_32.lib")
    #pragma comment(lib, "iphlpapi.lib")
    typedef SOCKET socket_t;
    #define SOCKET_ERROR_VAL INVALID_SOCKET
    #define CLOSE_SOCKET(s) closesocket(s)
    #define SOCKET_ERRNO WSAGetLastError()
#else
    #include <arpa/inet.h>
    #include <sys/socket.h>
    #include <sys/types.h>
    #include <netinet/in.h>
    #include <netdb.h>
    #include <ifaddrs.h>
    #include <fcntl.h>
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
#define BUFFER_SIZE 1024
#define MULTICAST_IP "239.255.255.250"
#define MAX_MSG_SIZE 1024
#define MULTICAST_GROUP "239.0.0.1"
#define PORT 5000
#define MAX_INTERFACES 10

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
                strcmp(pAdapterInfo->IpAddressList.IpAddress.String, "0.0.0.0") != 0) {
                printf("%d: %s (%s)\n", index, pAdapterInfo->Description,
                       pAdapterInfo->IpAddressList.IpAddress.String);
                if (index == selected_interface) {
                    strcpy(selected_interface_ip, pAdapterInfo->IpAddressList.IpAddress.String);
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

void join_multicast_group(socket_t socket, const char *multicast_ip, const char *interface_ip) {
    struct ip_mreq mreq;
    mreq.imr_multiaddr.s_addr = inet_addr(multicast_ip);
    mreq.imr_interface.s_addr = inet_addr(interface_ip);
    #ifdef _WIN32
    if (setsockopt(socket, IPPROTO_IP, IP_ADD_MEMBERSHIP, (char*)&mreq, sizeof(mreq)) == SOCKET_ERROR) {
    #else
    if (setsockopt(socket, IPPROTO_IP, IP_ADD_MEMBERSHIP, &mreq, sizeof(mreq)) < 0) {
    #endif
        perror("setsockopt IP_ADD_MEMBERSHIP");
        exit(EXIT_FAILURE);
    }
}

void set_multicast_interface(socket_t socket, const char *interface_ip) {
    struct in_addr interface_addr;
    interface_addr.s_addr = inet_addr(interface_ip);
    #ifdef _WIN32
    if (setsockopt(socket, IPPROTO_IP, IP_MULTICAST_IF, (char*)&interface_addr, sizeof(interface_addr)) == SOCKET_ERROR) {
    #else
    if (setsockopt(socket, IPPROTO_IP, IP_MULTICAST_IF, &interface_addr, sizeof(interface_addr)) < 0) {
    #endif
        perror("setsockopt IP_MULTICAST_IF");
        exit(EXIT_FAILURE);
    }
}

// Fonction pour convertir une chaîne hexadécimale en tableau d'octets
int hex_to_bytes(const char *hex, unsigned char *bytes, size_t len) {
    for (size_t i = 0; i < len; i++) {
        if (sscanf(hex + 2*i, "%2hhx", &bytes[i]) != 1) {
            return 0;
        }
    }
    return 1;
}

// Fonction pour lire une clé depuis le fichier de configuration
int read_key_from_file(const char *filename, const char *key_name, unsigned char *key, size_t key_len) {
    FILE *file = fopen(filename, "r");
    if (!file) {
        fprintf(stderr, "Erreur lors de l'ouverture du fichier %s\n", filename);
        return 0;
    }

    char line[256];
    char *value = NULL;
    while (fgets(line, sizeof(line), file)) {
        if (line[0] == '#' || line[0] == '\n') continue; // Ignorer les commentaires et lignes vides
        if (strncmp(line, key_name, strlen(key_name)) == 0 && line[strlen(key_name)] == '=') {
            value = line + strlen(key_name) + 1;
            // Supprimer le retour à la ligne si présent
            char *newline = strchr(value, '\n');
            if (newline) *newline = '\0';
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

// Fonction pour générer un IV aléatoire
void generate_random_iv(unsigned char *iv) {
    for (int i = 0; i < IV_LENGTH; i++) {
        iv[i] = rand() % 256;
    }
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

    if (bind(socket_fd_12345, (struct sockaddr *)&address_12345, sizeof(address_12345)) == SOCKET_ERROR_VAL) {
        perror("bind failed");
        CLOSE_SOCKET(socket_fd_12345);
        #ifdef _WIN32
        WSACleanup();
        #endif
        exit(EXIT_FAILURE);
    }

    printf("Proxy listening on port 12345\n");

    if ((socket_fd_multicast = socket(AF_INET, SOCK_DGRAM, 0)) == SOCKET_ERROR_VAL) {
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
    if (setsockopt(socket_fd_multicast, SOL_SOCKET, SO_REUSEADDR, (char*)&reuse, sizeof(reuse)) == SOCKET_ERROR) {
    #else
    if (setsockopt(socket_fd_multicast, SOL_SOCKET, SO_REUSEADDR, &reuse, sizeof(reuse)) < 0) {
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

    if (bind(socket_fd_multicast, (struct sockaddr *)&multicast_addr, sizeof(multicast_addr)) == SOCKET_ERROR_VAL) {
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

    join_multicast_group(socket_fd_multicast, MULTICAST_IP, selected_interface_ip);
    printf("Joined multicast group on interface: %s\n", selected_interface_ip);

    printf("Listening for multicast messages on %s:%d\n", MULTICAST_IP, MULTICAST_PORT);

    fd_set readfds;
    struct timeval timeout;
    timeout.tv_sec = 1;
    timeout.tv_usec = 0;

    printf("Local IP address: %s\n", selected_interface_ip);

    // Lire les clés depuis le fichier
    unsigned char encryption_key[KEY_LENGTH];
    unsigned char iv[IV_LENGTH];
    unsigned char hmac_key[HMAC_KEY_LENGTH];

    if (!read_key_from_file("clef.txt", "encryption_key", encryption_key, KEY_LENGTH) ||
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
            int bytes_received = recvfrom(socket_fd_12345, buffer, BUFFER_SIZE, 0,
                                        (struct sockaddr *)&client_address, &addrlen);
            if (bytes_received > 0) {
                buffer[bytes_received] = '\0';
                printf("Received message from Python: %s\n", buffer);
                printf("Forward it to multicast group: %s\n", MULTICAST_IP);

                // Générer un IV aléatoire
                unsigned char iv[IV_LENGTH];
                generate_random_iv(iv);

                // Préparer le message final
                struct final_message final_msg;
                memcpy(final_msg.iv, iv, IV_LENGTH);

                // Chiffrer le message
                int encrypted_length;
                encrypt_message(encryption_key, iv, buffer, final_msg.encrypted_data, &encrypted_length);
                printf("Original message length: %d\n", strlen(buffer));
                printf("Encrypted length: %d\n", encrypted_length);

                // Générer le HMAC sur les données chiffrées
                generate_hmac(hmac_key, final_msg.encrypted_data, encrypted_length, final_msg.hmac);

                // Envoyer le message complet
                set_multicast_interface(socket_fd_multicast, selected_interface_ip);
                struct sockaddr_in multicast_send_addr;
                multicast_send_addr.sin_family = AF_INET;
                multicast_send_addr.sin_addr.s_addr = inet_addr(MULTICAST_IP);
                multicast_send_addr.sin_port = htons(MULTICAST_PORT);

                // Envoyer d'abord la taille du message
                uint32_t msg_size = htonl(IV_LENGTH + encrypted_length + HMAC_LENGTH);
                printf("Sending message size: %d bytes\n", ntohl(msg_size));
                printf("IV length: %d, Encrypted length: %d, HMAC length: %d\n", 
                       IV_LENGTH, encrypted_length, HMAC_LENGTH);
                
                // Créer un buffer temporaire pour le message
                unsigned char *temp_buffer = malloc(IV_LENGTH + encrypted_length + HMAC_LENGTH);
                if (!temp_buffer) {
                    fprintf(stderr, "Failed to allocate memory for message\n");
                    continue;
                }

                // Copier les données dans le buffer temporaire
                memcpy(temp_buffer, final_msg.iv, IV_LENGTH);
                memcpy(temp_buffer + IV_LENGTH, final_msg.encrypted_data, encrypted_length);
                memcpy(temp_buffer + IV_LENGTH + encrypted_length, final_msg.hmac, HMAC_LENGTH);

                // Envoyer la taille et le message
                #ifdef _WIN32
                sendto(socket_fd_multicast, (char*)&msg_size, sizeof(uint32_t), 0,
                       (struct sockaddr *)&multicast_send_addr, sizeof(multicast_send_addr));
                sendto(socket_fd_multicast, (char*)temp_buffer, 
                       IV_LENGTH + encrypted_length + HMAC_LENGTH, 0,
                       (struct sockaddr *)&multicast_send_addr, sizeof(multicast_send_addr));
                #else
                sendto(socket_fd_multicast, &msg_size, sizeof(uint32_t), 0,
                       (struct sockaddr *)&multicast_send_addr, sizeof(multicast_send_addr));
                sendto(socket_fd_multicast, temp_buffer, 
                       IV_LENGTH + encrypted_length + HMAC_LENGTH, 0,
                       (struct sockaddr *)&multicast_send_addr, sizeof(multicast_send_addr));
                #endif

                free(temp_buffer);
            }
        }

        if (FD_ISSET(socket_fd_multicast, &readfds)) {
            // D'abord recevoir la taille du message
            uint32_t msg_size;
            #ifdef _WIN32
            int size_received = recvfrom(socket_fd_multicast, (char*)&msg_size, sizeof(uint32_t), 0,
                                       (struct sockaddr *)&client_address, &addrlen);
            #else
            int size_received = recvfrom(socket_fd_multicast, &msg_size, sizeof(uint32_t), 0,
                                       (struct sockaddr *)&client_address, &addrlen);
            #endif
            if (size_received > 0) {
                msg_size = ntohl(msg_size);  // Convertir de network à host byte order
                
                // Vérifier que la taille est raisonnable
                if (msg_size > BUFFER_SIZE + IV_LENGTH + HMAC_LENGTH) {
                    printf("Received invalid message size: %d bytes\n", msg_size);
                    continue;
                }
                
                printf("Received message size: %d bytes\n", msg_size);
                
                // Recevoir le message avec la taille exacte
                unsigned char *temp_buffer = malloc(msg_size);
                if (!temp_buffer) {
                    fprintf(stderr, "Failed to allocate memory for received message\n");
                    continue;
                }

                #ifdef _WIN32
                int bytes_received = recvfrom(socket_fd_multicast, (char*)temp_buffer, msg_size, 0,
                                            (struct sockaddr *)&client_address, &addrlen);
                #else
                int bytes_received = recvfrom(socket_fd_multicast, temp_buffer, msg_size, 0,
                                            (struct sockaddr *)&client_address, &addrlen);
                #endif

                if (bytes_received > 0 && bytes_received == msg_size) {
                    printf("Received message from multicast group\n");
                    printf("Message size: %d bytes\n", bytes_received);

                    // Copier les données dans la structure
                    struct final_message received_msg;
                    memcpy(received_msg.iv, temp_buffer, IV_LENGTH);
                    memcpy(received_msg.encrypted_data, temp_buffer + IV_LENGTH, msg_size - IV_LENGTH - HMAC_LENGTH);
                    memcpy(received_msg.hmac, temp_buffer + msg_size - HMAC_LENGTH, HMAC_LENGTH);

                    // Calculer la taille réelle des données chiffrées
                    int actual_encrypted_length = msg_size - IV_LENGTH - HMAC_LENGTH;
                    printf("Actual encrypted data length: %d\n", actual_encrypted_length);
                    printf("IV length: %d, HMAC length: %d\n", IV_LENGTH, HMAC_LENGTH);

                    // Vérifier le HMAC sur les données chiffrées
                    printf("Verifying HMAC...\n");
                    printf("HMAC key length: %d\n", HMAC_KEY_LENGTH);
                    printf("HMAC length: %d\n", HMAC_LENGTH);
                    printf("Data being verified: ");
                    for(int i = 0; i < actual_encrypted_length; i++) {
                        printf("%02x", received_msg.encrypted_data[i]);
                    }
                    printf("\n");

                    if (!verify_hmac(hmac_key, received_msg.encrypted_data, 
                                   actual_encrypted_length, received_msg.hmac)) {
                        printf("HMAC verification failed - message may be tampered\n");
                        printf("Expected HMAC: ");
                        for(int i = 0; i < HMAC_LENGTH; i++) {
                            printf("%02x", received_msg.hmac[i]);
                        }
                        printf("\n");
                        free(temp_buffer);
                        continue;
                    }
                    printf("HMAC verification successful\n");

                    // Déchiffrer le message avec l'IV reçu
                    unsigned char decrypted_message[BUFFER_SIZE];
                    int decrypted_length = actual_encrypted_length;
                    printf("Decrypting with IV: ");
                    for(int i = 0; i < IV_LENGTH; i++) {
                        printf("%02x", received_msg.iv[i]);
                    }
                    printf("\n");
                    decrypt_message(encryption_key, received_msg.iv, received_msg.encrypted_data, 
                                  decrypted_message, &decrypted_length);
                    printf("Decrypted length: %d\n", decrypted_length);
                    decrypted_message[decrypted_length] = '\0';  // Assurer la null-termination
                    printf("Decrypted message: %s\n", decrypted_message);

                    struct sockaddr_in local_address;
                    local_address.sin_family = AF_INET;
                    local_address.sin_addr.s_addr = inet_addr("127.0.0.1");
                    local_address.sin_port = htons(PORT_1234);
                    #ifdef _WIN32
                    sendto(socket_fd_multicast, (char*)decrypted_message, decrypted_length, 0,
                           (struct sockaddr *)&local_address, sizeof(local_address));
                    #else
                    sendto(socket_fd_multicast, decrypted_message, decrypted_length, 0,
                           (struct sockaddr *)&local_address, sizeof(local_address));
                    #endif
                } else {
                    printf("Failed to receive complete message. Expected %d bytes, got %d\n", 
                           msg_size, bytes_received);
                }
                free(temp_buffer);
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