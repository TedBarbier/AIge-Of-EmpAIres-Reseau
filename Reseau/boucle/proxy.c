#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifdef _WIN32
#include <winsock2.h>
#include <ws2tcpip.h>
#pragma comment(lib, "Ws2_32.lib")
#else
#include <arpa/inet.h>
#include <netinet/in.h>
#include <sys/select.h>
#include <unistd.h>
#endif

#define PORT_12345 12345
#define PORT_8000 8000
#define BUFFER_SIZE 1024

void set_nonblocking(int socket) {
#ifdef _WIN32
  u_long mode = 1;
  ioctlsocket(socket, FIONBIO, &mode);
#else
  int flags = fcntl(socket, F_GETFL, 0);
  fcntl(socket, F_SETFL, flags | O_NONBLOCK);
#endif
}

int main(int argc, char *argv[]) {
  if (argc != 2) {
    fprintf(stderr, "Usage: %s <target_ip>\n", argv[0]);
    return 1;
  }

#ifdef _WIN32
  WSADATA wsaData;
  if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0) {
    fprintf(stderr, "WSAStartup failed.\n");
    return 1;
  }
#endif

  int socket_fd_12345, socket_fd_8000;
  struct sockaddr_in address_12345, address_8000, target_address,
      client_address;
  socklen_t addrlen = sizeof(address_12345);

  // Create socket for port 12345
  if ((socket_fd_12345 = socket(AF_INET, SOCK_DGRAM, 0)) < 0) {
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
           sizeof(address_12345)) < 0) {
    perror("bind failed");
    close(socket_fd_12345);
#ifdef _WIN32
    WSACleanup();
#endif
    exit(EXIT_FAILURE);
  }

  printf("C proxy listening on port 12345\n");

  // Create socket for port 8000
  if ((socket_fd_8000 = socket(AF_INET, SOCK_DGRAM, 0)) < 0) {
    perror("socket failed");
    close(socket_fd_8000);
#ifdef _WIN32
    WSACleanup();
#endif
    exit(EXIT_FAILURE);
  }

  set_nonblocking(socket_fd_8000);

  address_8000.sin_family = AF_INET;
  address_8000.sin_addr.s_addr = INADDR_ANY;
  address_8000.sin_port = htons(PORT_8000);

  if (bind(socket_fd_8000, (struct sockaddr *)&address_8000,
           sizeof(address_8000)) < 0) {
    perror("bind failed");
    close(socket_fd_8000);
#ifdef _WIN32
    WSACleanup();
#endif
    exit(EXIT_FAILURE);
  }

  printf("C proxy listening on port 8000\n");

  // Set up target address
  target_address.sin_family = AF_INET;
  target_address.sin_port = htons(PORT_8000);
  if (inet_pton(AF_INET, argv[1], &target_address.sin_addr) <= 0) {
    perror("invalid address/ Address not supported");
    close(socket_fd_12345);
    close(socket_fd_8000);
#ifdef _WIN32
    WSACleanup();
#endif
    exit(EXIT_FAILURE);
  }

  fd_set readfds;
  struct timeval timeout;
  timeout.tv_sec = 1;
  timeout.tv_usec = 0;

  while (1) {
    FD_ZERO(&readfds);
    FD_SET(socket_fd_12345, &readfds);
    FD_SET(socket_fd_8000, &readfds);

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
        buffer[bytes_received] = '\0'; // Null-terminate the received data
        printf("Received message from Python: %s\n", buffer);
        printf("Forward it to: %s\n", argv[1]);
        sendto(socket_fd_12345, buffer, bytes_received, 0,
               (struct sockaddr *)&target_address, sizeof(target_address));
      }
    }

    if (FD_ISSET(socket_fd_8000, &readfds)) {
      char buffer[BUFFER_SIZE];
      int bytes_received =
          recvfrom(socket_fd_8000, buffer, BUFFER_SIZE, 0,
                   (struct sockaddr *)&client_address, &addrlen);
      if (bytes_received > 0) {
        buffer[bytes_received] = '\0'; // Null-terminate the received data
        printf("Received message from Target: %s\n", buffer);
        printf("Forward it to: localhost\n");

        // Correctly forward to Python server on localhost:1234
        struct sockaddr_in local_address;
        local_address.sin_family = AF_INET;
        local_address.sin_addr.s_addr = inet_addr("127.0.0.1");
        local_address.sin_port = htons(1234);
        sendto(socket_fd_8000, buffer, bytes_received, 0,
               (struct sockaddr *)&local_address, sizeof(local_address));
      }
    }
  }

  close(socket_fd_12345);
  close(socket_fd_8000);

#ifdef _WIN32
  WSACleanup();
#endif

  return 0;
}
