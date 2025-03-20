#include <arpa/inet.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

void receive_multicast_message(const char *multicast_ip, int port) {
  int sock;
  struct sockaddr_in receiver_addr;
  struct ip_mreq mreq;
  char buffer[1024];
  socklen_t addr_len = sizeof(receiver_addr);

  // Create a UDP socket
  sock = socket(AF_INET, SOCK_DGRAM, 0);
  if (sock < 0) {
    perror("socket");
    exit(EXIT_FAILURE);
  }

  // Allow the socket to be reused
  int reuse = 1;
  if (setsockopt(sock, SOL_SOCKET, SO_REUSEADDR, &reuse, sizeof(reuse)) < 0) {
    perror("setsockopt");
    close(sock);
    exit(EXIT_FAILURE);
  }

  // Bind the socket to the port and all interfaces
  memset(&receiver_addr, 0, sizeof(receiver_addr));
  receiver_addr.sin_family = AF_INET;
  receiver_addr.sin_addr.s_addr = htonl(INADDR_ANY);
  receiver_addr.sin_port = htons(port);

  if (bind(sock, (struct sockaddr *)&receiver_addr, sizeof(receiver_addr)) <
      0) {
    perror("bind");
    close(sock);
    exit(EXIT_FAILURE);
  }

  // Join the multicast group on all interfaces
  mreq.imr_multiaddr.s_addr = inet_addr(multicast_ip);
  mreq.imr_interface.s_addr = htonl(INADDR_ANY);
  if (setsockopt(sock, IPPROTO_IP, IP_ADD_MEMBERSHIP, &mreq, sizeof(mreq)) <
      0) {
    perror("setsockopt");
    close(sock);
    exit(EXIT_FAILURE);
  }

  printf("Listening for multicast messages on %s:%d...\n", multicast_ip, port);

  // Receive messages
  while (1) {
    int bytes_received = recvfrom(sock, buffer, sizeof(buffer), 0,
                                  (struct sockaddr *)&receiver_addr, &addr_len);
    if (bytes_received < 0) {
      perror("recvfrom");
      close(sock);
      exit(EXIT_FAILURE);
    }
    buffer[bytes_received] = '\0';
    printf("Received message: %s from %s:%d\n", buffer,
           inet_ntoa(receiver_addr.sin_addr), ntohs(receiver_addr.sin_port));
  }

  // Close the socket
  close(sock);
}

int main() {
  receive_multicast_message("239.255.255.250", 8000);
  return 0;
}
