#include "tls_utils.h"
#include <arpa/inet.h>
#include <errno.h>
#include <fcntl.h>
#include <ifaddrs.h>
#include <netdb.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#define PORT_12345 12345
#define PORT_1234 1234
#define MULTICAST_PORT 8000
#define BUFFER_SIZE 1024
#define MULTICAST_IP "239.255.255.250"

void set_nonblocking(int socket) {
  int flags = fcntl(socket, F_GETFL, 0);
  fcntl(socket, F_SETFL, flags | O_NONBLOCK);
}

void join_multicast_group(int socket, const char *multicast_ip,
                          const char *interface_ip) {
  struct ip_mreq mreq;
  mreq.imr_multiaddr.s_addr = inet_addr(multicast_ip);
  mreq.imr_interface.s_addr = inet_addr(interface_ip);
  if (setsockopt(socket, IPPROTO_IP, IP_ADD_MEMBERSHIP, &mreq, sizeof(mreq)) <
      0) {
    perror("setsockopt IP_ADD_MEMBERSHIP");
    exit(EXIT_FAILURE);
  }
}

void set_multicast_interface(int socket, const char *interface_ip) {
  struct in_addr interface_addr;
  interface_addr.s_addr = inet_addr(interface_ip);
  if (setsockopt(socket, IPPROTO_IP, IP_MULTICAST_IF, &interface_addr,
                 sizeof(interface_addr)) < 0) {
    perror("setsockopt IP_MULTICAST_IF");
    exit(EXIT_FAILURE);
  }
}

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

int main(int argc, char *argv[]) {
  int socket_fd_12345, socket_fd_multicast;
  struct sockaddr_in address_12345, multicast_addr, client_address;
  socklen_t addrlen = sizeof(address_12345);

  /* Create socket for port 12345 */
  if ((socket_fd_12345 = socket(AF_INET, SOCK_DGRAM, 0)) < 0) {
    perror("socket failed");
    exit(EXIT_FAILURE);
  }

  set_nonblocking(socket_fd_12345);

  address_12345.sin_family = AF_INET;
  address_12345.sin_addr.s_addr = INADDR_ANY;
  address_12345.sin_port = htons(PORT_12345);

  if (bind(socket_fd_12345, (struct sockaddr *)&address_12345,
           sizeof(address_12345)) < 0) {
    perror("bind failed");
    close(socket_fd_12345);
    exit(EXIT_FAILURE);
  }

  printf("Proxy listening on port 12345\n");

  /* Create socket for multicast */
  if ((socket_fd_multicast = socket(AF_INET, SOCK_DGRAM, 0)) < 0) {
    perror("socket failed");
    close(socket_fd_12345);
    exit(EXIT_FAILURE);
  }

  set_nonblocking(socket_fd_multicast);

  /* Allow the socket to be reused */
  int reuse = 1;
  if (setsockopt(socket_fd_multicast, SOL_SOCKET, SO_REUSEADDR, &reuse,
                 sizeof(reuse)) < 0) {
    perror("setsockopt SO_REUSEADDR");
    close(socket_fd_12345);
    close(socket_fd_multicast);
    exit(EXIT_FAILURE);
  }

  /* Bind the socket to the multicast port */
  memset(&multicast_addr, 0, sizeof(multicast_addr));
  multicast_addr.sin_family = AF_INET;
  multicast_addr.sin_addr.s_addr = htonl(INADDR_ANY);
  multicast_addr.sin_port = htons(MULTICAST_PORT);

  if (bind(socket_fd_multicast, (struct sockaddr *)&multicast_addr,
           sizeof(multicast_addr)) < 0) {
    perror("bind failed");
    close(socket_fd_12345);
    close(socket_fd_multicast);
    exit(EXIT_FAILURE);
  }

  /* List available interfaces */
  printf("Available interfaces:\n");
  char selected_interface_ip[INET_ADDRSTRLEN];
  list_interfaces(selected_interface_ip, 0);

  /* Prompt user to select an interface */
  int selected_interface;
  printf("Select an interface by number: ");
  scanf("%d", &selected_interface);

  /* Get the selected interface IP */
  list_interfaces(selected_interface_ip, selected_interface);

  /* Join the multicast group on the selected interface */
  join_multicast_group(socket_fd_multicast, MULTICAST_IP,
                       selected_interface_ip);
  printf("Joined multicast group on interface: %s\n", selected_interface_ip);

  printf("Listening for multicast messages on %s:%d\n", MULTICAST_IP,
         MULTICAST_PORT);

  fd_set readfds;
  struct timeval timeout;
  timeout.tv_sec = 1;
  timeout.tv_usec = 0;

  /* Print the local IP address */
  printf("Local IP address: %s\n", selected_interface_ip);

  unsigned char key[KEY_LENGTH];
  unsigned char iv[IV_LENGTH];
  memset(key, 'A', KEY_LENGTH);
  memset(iv, 'B', IV_LENGTH);

  while (1) {
    FD_ZERO(&readfds);
    FD_SET(socket_fd_12345, &readfds);
    FD_SET(socket_fd_multicast, &readfds);

    int activity = select(FD_SETSIZE, &readfds, NULL, NULL, &timeout);

    if ((activity < 0) && (errno != EINTR)) {
      perror("select error");
      break;
    }

    if (FD_ISSET(socket_fd_12345, &readfds)) {
      char buffer[BUFFER_SIZE];
      int bytes_received =
          recvfrom(socket_fd_12345, buffer, BUFFER_SIZE, 0,
                   (struct sockaddr *)&client_address, &addrlen);
      if (bytes_received > 0) {
        buffer[bytes_received] = '\0';
        printf("Received message from Python: %s\n", buffer);
        printf("Forward it to multicast group: %s\n", MULTICAST_IP);

        /* Encrypt the message */
        unsigned char encrypted_message[BUFFER_SIZE];
        int encrypted_length;
        encrypt_message(key, iv, buffer, encrypted_message, &encrypted_length);

        /* Send to multicast group on the selected interface */
        set_multicast_interface(socket_fd_multicast, selected_interface_ip);
        struct sockaddr_in multicast_send_addr;
        multicast_send_addr.sin_family = AF_INET;
        multicast_send_addr.sin_addr.s_addr = inet_addr(MULTICAST_IP);
        multicast_send_addr.sin_port = htons(MULTICAST_PORT);
        sendto(socket_fd_multicast, encrypted_message, encrypted_length, 0,
               (struct sockaddr *)&multicast_send_addr,
               sizeof(multicast_send_addr));
      }
    }

    if (FD_ISSET(socket_fd_multicast, &readfds)) {
      unsigned char buffer[BUFFER_SIZE];
      int bytes_received =
          recvfrom(socket_fd_multicast, buffer, BUFFER_SIZE, 0,
                   (struct sockaddr *)&client_address, &addrlen);
      if (bytes_received > 0) {
        printf("Received message from multicast group\n");

        /* Debugging: Print the received encrypted data */
        printf("Received encrypted data: ");
        for (int i = 0; i < bytes_received; i++) {
          printf("%02x", buffer[i]);
        }
        printf("\n");

        /* Decrypt the message */
        unsigned char decrypted_message[BUFFER_SIZE];
        int decrypted_length =
            bytes_received; // Initialize with received length
        decrypt_message(key, iv, buffer, decrypted_message, &decrypted_length);

        /* Forward to Python server on localhost:1234 */
        struct sockaddr_in local_address;
        local_address.sin_family = AF_INET;
        local_address.sin_addr.s_addr = inet_addr("127.0.0.1");
        local_address.sin_port = htons(PORT_1234);
        sendto(socket_fd_multicast, decrypted_message, decrypted_length, 0,
               (struct sockaddr *)&local_address, sizeof(local_address));
      }
    }
  }

  close(socket_fd_12345);
  close(socket_fd_multicast);

  return 0;
}
