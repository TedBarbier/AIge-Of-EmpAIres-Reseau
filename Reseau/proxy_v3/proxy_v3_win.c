#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifdef _WIN32
#include <winsock2.h>
#include <ws2tcpip.h>
#include <windows.h>
#pragma comment(lib, "Ws2_32.lib")
#else
#include <arpa/inet.h>
#include <netinet/in.h>
#include <sys/select.h>
#include <unistd.h>
#endif

#define PORT_12345 12345
#define PORT_1234 1234
#define MULTICAST_PORT 8000
#define BUFFER_SIZE 16384
#define MULTICAST_IP "239.255.255.250"

void set_nonblocking(int socket) {
#ifdef _WIN32
    u_long mode = 1;
    if (ioctlsocket(socket, FIONBIO, &mode) == SOCKET_ERROR) {
        printf("Failed to set non-blocking mode: %d\n", WSAGetLastError());
    }
#else
    int flags = fcntl(socket, F_GETFL, 0);
    fcntl(socket, F_SETFL, flags | O_NONBLOCK);
#endif
}

void join_multicast_group(int socket, const char *multicast_ip) {
    struct ip_mreq mreq;
    mreq.imr_multiaddr.s_addr = inet_addr(multicast_ip);
    mreq.imr_interface.s_addr = htonl(INADDR_ANY);
    if (setsockopt(socket, IPPROTO_IP, IP_ADD_MEMBERSHIP, (char*)&mreq, sizeof(mreq)) < 0) {
#ifdef _WIN32
        printf("setsockopt failed: %d\n", WSAGetLastError());
#else
        perror("setsockopt");
#endif
        exit(EXIT_FAILURE);
    }
}

void get_local_ip(char *local_ip) {
    int sock;
    struct sockaddr_in serv_addr, local_addr;
    socklen_t addrlen = sizeof(local_addr);

    if ((sock = socket(AF_INET, SOCK_DGRAM, 0)) < 0) {
#ifdef _WIN32
        printf("socket failed: %d\n", WSAGetLastError());
#else
        perror("socket");
#endif
        exit(EXIT_FAILURE);
    }

    memset(&serv_addr, 0, sizeof(serv_addr));
    serv_addr.sin_family = AF_INET;
    serv_addr.sin_addr.s_addr = inet_addr("8.8.8.8"); // Google DNS
    serv_addr.sin_port = htons(53);

    if (connect(sock, (struct sockaddr *)&serv_addr, sizeof(serv_addr)) < 0) {
#ifdef _WIN32
        printf("connect failed: %d\n", WSAGetLastError());
#else
        perror("connect");
#endif
        closesocket(sock);
        exit(EXIT_FAILURE);
    }

    getsockname(sock, (struct sockaddr *)&local_addr, &addrlen);
    inet_ntop(AF_INET, &(local_addr.sin_addr), local_ip, INET_ADDRSTRLEN);

    closesocket(sock);
}

int main(int argc, char *argv[]) {
#ifdef _WIN32
    WSADATA wsaData;
    if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0) {
        fprintf(stderr, "WSAStartup failed.\n");
        return 1;
    }
#endif

    int socket_fd_12345, socket_fd_multicast;
    struct sockaddr_in address_12345, multicast_addr, client_address;
    socklen_t addrlen = sizeof(address_12345);

    // Create socket for port 12345
    if ((socket_fd_12345 = socket(AF_INET, SOCK_DGRAM, 0)) < 0) {
#ifdef _WIN32
        printf("socket failed: %d\n", WSAGetLastError());
#else
        perror("socket failed");
#endif
#ifdef _WIN32
        WSACleanup();
#endif
        exit(EXIT_FAILURE);
    }

    set_nonblocking(socket_fd_12345);

    address_12345.sin_family = AF_INET;
    address_12345.sin_addr.s_addr = INADDR_ANY;
    address_12345.sin_port = htons(PORT_12345);

    if (bind(socket_fd_12345, (struct sockaddr *)&address_12345, sizeof(address_12345)) < 0) {
#ifdef _WIN32
        printf("bind failed: %d\n", WSAGetLastError());
#else
        perror("bind failed");
#endif
        closesocket(socket_fd_12345);
#ifdef _WIN32
        WSACleanup();
#endif
        exit(EXIT_FAILURE);
    }

    printf("Proxy listening on port 12345\n");

    // Create socket for multicast
    if ((socket_fd_multicast = socket(AF_INET, SOCK_DGRAM, 0)) < 0) {
#ifdef _WIN32
        printf("socket failed: %d\n", WSAGetLastError());
#else
        perror("socket failed");
#endif
        closesocket(socket_fd_12345);
#ifdef _WIN32
        WSACleanup();
#endif
        exit(EXIT_FAILURE);
    }

    set_nonblocking(socket_fd_multicast);

    // Allow the socket to be reused
    int reuse = 1;
    if (setsockopt(socket_fd_multicast, SOL_SOCKET, SO_REUSEADDR, (char*)&reuse, sizeof(reuse)) < 0) {
#ifdef _WIN32
        printf("setsockopt failed: %d\n", WSAGetLastError());
#else
        perror("setsockopt");
#endif
        closesocket(socket_fd_12345);
        closesocket(socket_fd_multicast);
#ifdef _WIN32
        WSACleanup();
#endif
        exit(EXIT_FAILURE);
    }

    // Bind the socket to the multicast port
    memset(&multicast_addr, 0, sizeof(multicast_addr));
    multicast_addr.sin_family = AF_INET;
    multicast_addr.sin_addr.s_addr = htonl(INADDR_ANY);
    multicast_addr.sin_port = htons(MULTICAST_PORT);

    if (bind(socket_fd_multicast, (struct sockaddr *)&multicast_addr, sizeof(multicast_addr)) < 0) {
#ifdef _WIN32
        printf("bind failed: %d\n", WSAGetLastError());
#else
        perror("bind failed");
#endif
        closesocket(socket_fd_12345);
        closesocket(socket_fd_multicast);
#ifdef _WIN32
        WSACleanup();
#endif
        exit(EXIT_FAILURE);
    }

    // Join the multicast group
    join_multicast_group(socket_fd_multicast, MULTICAST_IP);

    printf("Listening for multicast messages on %s:%d\n", MULTICAST_IP, MULTICAST_PORT);

    fd_set readfds;
    struct timeval timeout;
    timeout.tv_sec = 1;
    timeout.tv_usec = 0;

    // Get the local machine's IP address
    char local_ip[INET_ADDRSTRLEN];
    get_local_ip(local_ip);

    // Print the local IP address
    printf("Local IP address: %s\n", local_ip);

    while (1) {
        FD_ZERO(&readfds);
        FD_SET(socket_fd_12345, &readfds);
        FD_SET(socket_fd_multicast, &readfds);

        int activity = select(FD_SETSIZE, &readfds, NULL, NULL, &timeout);

        if ((activity < 0) && (errno != EINTR)) {
#ifdef _WIN32
            printf("select error: %d\n", WSAGetLastError());
#else
            perror("select error");
#endif
            break;
        }

        if (FD_ISSET(socket_fd_12345, &readfds)) {
            char buffer[BUFFER_SIZE];
            int bytes_received = recvfrom(socket_fd_12345, buffer, BUFFER_SIZE, 0,
                                        (struct sockaddr *)&client_address, &addrlen);
            if (bytes_received > 0) {
                buffer[bytes_received] = '\0'; // Null-terminate the received data
                printf("Received message from Python: %s\n", buffer);
                printf("Forward it to multicast group: %s\n", MULTICAST_IP);

                // Send to multicast group
                struct sockaddr_in multicast_send_addr;
                multicast_send_addr.sin_family = AF_INET;
                multicast_send_addr.sin_addr.s_addr = inet_addr(MULTICAST_IP);
                multicast_send_addr.sin_port = htons(MULTICAST_PORT);
                sendto(socket_fd_multicast, buffer, bytes_received, 0,
                       (struct sockaddr *)&multicast_send_addr, sizeof(multicast_send_addr));
            }
        }

        if (FD_ISSET(socket_fd_multicast, &readfds)) {
            char buffer[BUFFER_SIZE];
            int bytes_received = recvfrom(socket_fd_multicast, buffer, BUFFER_SIZE, 0,
                                        (struct sockaddr *)&client_address, &addrlen);
            if (bytes_received > 0) {
                buffer[bytes_received] = '\0'; // Null-terminate the received data
                printf("Received message from multicast group: %s\n", buffer);

                // Check if the message is from the local machine
                char sender_ip[INET_ADDRSTRLEN];
                inet_ntop(AF_INET, &(client_address.sin_addr), sender_ip, INET_ADDRSTRLEN);
                if (strcmp(sender_ip, local_ip) != 0) {
                    printf("Forward it to Python server on localhost\n");

                    // Forward to Python server on localhost:1234
                    struct sockaddr_in local_address;
                    local_address.sin_family = AF_INET;
                    local_address.sin_addr.s_addr = inet_addr("127.0.0.1");
                    local_address.sin_port = htons(PORT_1234);
                    sendto(socket_fd_multicast, buffer, bytes_received, 0,
                           (struct sockaddr *)&local_address, sizeof(local_address));
                } else {
                    printf("Message from self; ignoring.\n");
                }
            }
        }
    }

    closesocket(socket_fd_12345);
    closesocket(socket_fd_multicast);

#ifdef _WIN32
    WSACleanup();
#endif

    return 0;
}
