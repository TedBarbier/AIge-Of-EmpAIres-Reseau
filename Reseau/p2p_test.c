#ifdef _WIN32
    #include <winsock2.h>
    #include <ws2tcpip.h>
    #include <conio.h>  // Pour _kbhit()
    #pragma comment(lib, "ws2_32.lib")
    typedef SOCKET socket_t;
    #define SOCKET_ERROR_TYPE SOCKET_ERROR
    #define INVALID_SOCKET_TYPE INVALID_SOCKET
    #define CLOSE_SOCKET(s) closesocket(s)
    #define SLEEP(ms) Sleep(ms)
    #define SET_NONBLOCKING(sock) { u_long mode = 1; ioctlsocket(sock, FIONBIO, &mode); }
    #define STDIN_FILENO 0
#else
    #include <unistd.h>
    #include <sys/socket.h>
    #include <netinet/in.h>
    #include <arpa/inet.h>
    #include <fcntl.h>
    typedef int socket_t;
    #define SOCKET_ERROR_TYPE -1
    #define INVALID_SOCKET_TYPE -1
    #define CLOSE_SOCKET(s) close(s)
    #define SLEEP(ms) usleep(ms * 1000)  // Convert ms to microseconds
    #define SET_NONBLOCKING(sock) fcntl(sock, F_SETFL, O_NONBLOCK)
#endif

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define BUFFER_SIZE 2000
#define MAX_MESSAGE_SIZE 1024
#define SLEEP_TIME 1  // Reduced to 1ms for faster response

int PORT = 8000;
char target_ip[16];
socket_t send_sock = INVALID_SOCKET_TYPE;  // Global socket for sending
struct sockaddr_in serv_addr;  // Global address structure

void sending(const char *message);
void receiving(socket_t server_fd);

int main(int argc, char const *argv[]) {
    #ifdef _WIN32
        WSADATA wsaData;
        if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0) {
            printf("WSAStartup failed\n");
            return 1;
        }
    #endif

    if (argc != 2) {
        printf("Usage: %s <target_ip>\n", argv[0]);
        return 1;
    }

    strncpy(target_ip, argv[1], sizeof(target_ip));

    // Initialize sending socket once
    if ((send_sock = socket(AF_INET, SOCK_DGRAM, 0)) == INVALID_SOCKET_TYPE) {
        printf("\nSocket creation error\n");
        return 1;
    }
    SET_NONBLOCKING(send_sock);

    serv_addr.sin_family = AF_INET;
    serv_addr.sin_port = htons(PORT);

    if (inet_pton(AF_INET, target_ip, &serv_addr.sin_addr) <= 0) {
        printf("\nInvalid address/ Address not supported\n");
        CLOSE_SOCKET(send_sock);
        return 1;
    }

    socket_t server_fd;
    struct sockaddr_in address;

    if ((server_fd = socket(AF_INET, SOCK_DGRAM, 0)) == INVALID_SOCKET_TYPE) {
        perror("socket failed");
        exit(EXIT_FAILURE);
    }

    SET_NONBLOCKING(server_fd);

    address.sin_family = AF_INET;
    address.sin_addr.s_addr = INADDR_ANY;
    address.sin_port = htons(PORT);

    if (bind(server_fd, (struct sockaddr *)&address, sizeof(address)) < 0) {
        perror("bind failed");
        exit(EXIT_FAILURE);
    }

    printf("Ready to send messages. Type your message and press Enter to send:\n");

    char message[MAX_MESSAGE_SIZE];
    char buffer[BUFFER_SIZE];

    while (1) {
        // Check if there's data to receive
        receiving(server_fd);

        // Check if there's input available (non-blocking)
        #ifdef _WIN32
            if (_kbhit()) {
                if (fgets(message, sizeof(message), stdin)) {
                    message[strcspn(message, "\n")] = '\0';
                    sending(message);
                }
            }
        #else
            int flags = fcntl(0, F_GETFL, 0);
            fcntl(0, F_SETFL, flags | O_NONBLOCK);
            if (fgets(message, sizeof(message), stdin)) {
                message[strcspn(message, "\n")] = '\0';
                sending(message);
            }
            fcntl(0, F_SETFL, flags);
        #endif

        SLEEP(SLEEP_TIME);
    }

    CLOSE_SOCKET(server_fd);
    CLOSE_SOCKET(send_sock);
    #ifdef _WIN32
        WSACleanup();
    #endif
    return 0;
}

void sending(const char *message) {
    char buffer[BUFFER_SIZE];
    snprintf(buffer, sizeof(buffer), "Message: %s", message);
    
    sendto(send_sock, buffer, strlen(buffer), 0, 
           (const struct sockaddr *)&serv_addr, sizeof(serv_addr));
    printf("Message sent to %s\n", target_ip);
}

void receiving(socket_t server_fd) {
    struct sockaddr_in address;
    socklen_t addrlen = sizeof(address);
    char buffer[BUFFER_SIZE] = {0};

    int valread = recvfrom(server_fd, buffer, sizeof(buffer) - 1, 0,
                          (struct sockaddr *)&address, &addrlen);
    if (valread > 0) {
        buffer[valread] = '\0';
        printf("\nReceived: %s\n", buffer);
    }
}
