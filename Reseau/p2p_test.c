#include <arpa/inet.h>
#include <netinet/in.h>
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <unistd.h>

int PORT = 8000;
char target_ip[16];

void sending(const char *message);
void receiving(int server_fd);
void *receive_thread(void *server_fd);

int main(int argc, char const *argv[]) {
  if (argc != 2) {
    printf("Usage: %s <target_ip>\n", argv[0]);
    return 1;
  }

  strncpy(target_ip, argv[1], sizeof(target_ip));

  int server_fd;
  struct sockaddr_in address;

  // Creating socket file descriptor
  if ((server_fd = socket(AF_INET, SOCK_DGRAM, 0)) == -1) {
    perror("socket failed");
    exit(EXIT_FAILURE);
  }

  address.sin_family = AF_INET;
  address.sin_addr.s_addr = INADDR_ANY;
  address.sin_port = htons(PORT);

  // Bind the socket to the port
  if (bind(server_fd, (struct sockaddr *)&address, sizeof(address)) < 0) {
    perror("bind failed");
    exit(EXIT_FAILURE);
  }

  pthread_t tid;
  pthread_create(
      &tid, NULL, &receive_thread,
      &server_fd); // Creating thread to keep receiving messages in real time

  printf(
      "Ready to send messages. Type your message and press Enter to send:\n");

  char message[1024];
  while (1) {
    fgets(message, sizeof(message), stdin);
    message[strcspn(message, "\n")] = '\0'; // Remove newline character
    sending(message);
  }

  close(server_fd);
  return 0;
}

// Sending messages to the specified IP address
void sending(const char *message) {
  char buffer[2000] = {0};
  sprintf(buffer, "Message: %s", message);

  int sock = 0;
  struct sockaddr_in serv_addr;

  if ((sock = socket(AF_INET, SOCK_DGRAM, 0)) < 0) {
    printf("\nSocket creation error\n");
    return;
  }

  serv_addr.sin_family = AF_INET;
  serv_addr.sin_port = htons(PORT);

  // Convert IPv4 and IPv6 addresses from text to binary form
  if (inet_pton(AF_INET, target_ip, &serv_addr.sin_addr) <= 0) {
    printf("\nInvalid address/ Address not supported\n");
    close(sock);
    return;
  }

  sendto(sock, buffer, strlen(buffer), 0, (const struct sockaddr *)&serv_addr,
         sizeof(serv_addr));
  printf("Message sent to %s\n", target_ip);
  close(sock);
}

// Calling receiving every 2 seconds
void *receive_thread(void *server_fd) {
  int s_fd = *((int *)server_fd);
  while (1) {
    receiving(s_fd);
    sleep(1); // Sleep for a short time to prevent busy-waiting
  }
}

// Receiving messages on our port
void receiving(int server_fd) {
  struct sockaddr_in address;
  int addrlen = sizeof(address);
  char buffer[2000] = {0};

  int valread = recvfrom(server_fd, buffer, sizeof(buffer) - 1, 0,
                         (struct sockaddr *)&address, (socklen_t *)&addrlen);
  if (valread > 0) {
    buffer[valread] = '\0'; // Ensure the string is null-terminated
    printf("\nReceived: %s\n", buffer);
  }
}
