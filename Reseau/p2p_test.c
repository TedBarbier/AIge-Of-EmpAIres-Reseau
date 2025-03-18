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
    #define SLEEP(ms) sleep(ms)
    #define SET_NONBLOCKING(sock) fcntl(sock, F_SETFL, O_NONBLOCK)
#endif

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int PORT = 8000;
char target_ip[16];

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

    socket_t server_fd;
    struct sockaddr_in address;

    // Creating socket file descriptor
    if ((server_fd = socket(AF_INET, SOCK_DGRAM, 0)) == INVALID_SOCKET_TYPE) {
        perror("socket failed");
        exit(EXIT_FAILURE);
    }

    // Set socket to non-blocking mode
    SET_NONBLOCKING(server_fd);

    address.sin_family = AF_INET;
    address.sin_addr.s_addr = INADDR_ANY;
    address.sin_port = htons(PORT);

    // Bind the socket to the port
    if (bind(server_fd, (struct sockaddr *)&address, sizeof(address)) < 0) {
        perror("bind failed");
        exit(EXIT_FAILURE);
    }

    printf("Ready to send messages. Type your message and press Enter to send:\n");

    char message[1024];

    while (1) {
        // Check if there's data to receive
        receiving(server_fd);

        // Check if there's input available (non-blocking)
        #ifdef _WIN32
            if (_kbhit()) {  // Windows-specific check for keyboard input
                if (fgets(message, sizeof(message), stdin)) {
                    message[strcspn(message, "\n")] = '\0';
                    sending(message);
                }
            }
        #else
            // On Linux, we can use non-blocking stdin
            int flags = fcntl(0, F_GETFL, 0);
            fcntl(0, F_SETFL, flags | O_NONBLOCK);
            if (fgets(message, sizeof(message), stdin)) {
                message[strcspn(message, "\n")] = '\0';
                sending(message);
            }
            fcntl(0, F_SETFL, flags);  // Reset stdin to blocking mode
        #endif

        // Small delay to prevent CPU overuse
        SLEEP(10);  // 10ms delay
    }

    CLOSE_SOCKET(server_fd);
    #ifdef _WIN32
        WSACleanup();
    #endif
    return 0;
}

// Sending messages to the specified IP address
void sending(const char *message) {
    char buffer[2000] = {0};
    sprintf(buffer, "Message: %s", message);

    socket_t sock = INVALID_SOCKET_TYPE;
    struct sockaddr_in serv_addr;

    if ((sock = socket(AF_INET, SOCK_DGRAM, 0)) == INVALID_SOCKET_TYPE) {
        printf("\nSocket creation error\n");
        return;
    }

    // Set socket to non-blocking mode
    SET_NONBLOCKING(sock);

    serv_addr.sin_family = AF_INET;
    serv_addr.sin_port = htons(PORT);

    // Convert IPv4 and IPv6 addresses from text to binary form
    if (inet_pton(AF_INET, target_ip, &serv_addr.sin_addr) <= 0) {
        printf("\nInvalid address/ Address not supported\n");
        CLOSE_SOCKET(sock);
        return;
    }

    sendto(sock, buffer, strlen(buffer), 0, (const struct sockaddr *)&serv_addr,
           sizeof(serv_addr));
    printf("Message sent to %s\n", target_ip);
    CLOSE_SOCKET(sock);
}

// Receiving messages on our port
void receiving(socket_t server_fd) {
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
