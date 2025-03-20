#include <arpa/inet.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

void send_multicast_message(const char *message, const char *multicast_ip,
                            int port) {
  int sock;
  struct sockaddr_in multicast_addr;
  int ttl = 1; // Time-to-live for multicast packets

  // Create a UDP socket
  sock = socket(AF_INET, SOCK_DGRAM, 0);
  if (sock < 0) {
    perror("socket");
    exit(EXIT_FAILURE);
  }

  // Set the TTL (Time-to-live) for multicast packets
  if (setsockopt(sock, IPPROTO_IP, IP_MULTICAST_TTL, &ttl, sizeof(ttl)) < 0) {
    perror("setsockopt");
    close(sock);
    exit(EXIT_FAILURE);
  }

  // Define the multicast address and port
  memset(&multicast_addr, 0, sizeof(multicast_addr));
  multicast_addr.sin_family = AF_INET;
  multicast_addr.sin_addr.s_addr = inet_addr(multicast_ip);
  multicast_addr.sin_port = htons(port);

  // Send the message
  if (sendto(sock, message, strlen(message), 0,
             (struct sockaddr *)&multicast_addr, sizeof(multicast_addr)) < 0) {
    perror("sendto");
    close(sock);
    exit(EXIT_FAILURE);
  }

  printf("Message sent: %s\n", message);

  // Close the socket
  close(sock);
}

int main() {
  send_multicast_message("Hello, multicast group!", "239.255.255.250", 8000);
  return 0;
}
