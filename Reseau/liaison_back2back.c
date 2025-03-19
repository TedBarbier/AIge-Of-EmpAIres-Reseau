#ifdef _WIN32
    #define _WIN32_WINNT 0x0600
    #include <winsock2.h>
    #include <ws2tcpip.h>
    typedef SOCKET socket_t;
    #define SOCKET_ERROR_TYPE SOCKET_ERROR
    #define INVALID_SOCKET_TYPE INVALID_SOCKET
    #define CLOSE_SOCKET(s) closesocket(s)
    #define SET_NONBLOCKING(sock) { u_long mode = 1; ioctlsocket(sock, FIONBIO, &mode); }
    #define SLEEP(ms) Sleep(ms)
    #define INET_NTOP(af, src, dst, size) { \
        struct sockaddr_in temp = {0}; \
        temp.sin_family = af; \
        temp.sin_addr = *(struct in_addr*)src; \
        getnameinfo((struct sockaddr*)&temp, sizeof(struct sockaddr_in), \
                   dst, size, NULL, 0, NI_NUMERICHOST); \
    }
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
    #define SET_NONBLOCKING(sock) fcntl(sock, F_SETFL, O_NONBLOCK)
    #define SLEEP(ms) usleep(ms * 1000)
    #define INET_NTOP(af, src, dst, size) inet_ntop(af, src, dst, size)
#endif

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define PYTHON_PORT 12345
#define P2P_PORT 8000
#define BUFFER_SIZE 2000
#define SLEEP_TIME 1

void forward_to_peer(const char *data, const char *target_ip) {
    socket_t sock;
    struct sockaddr_in serv_addr;
    
    if ((sock = socket(AF_INET, SOCK_DGRAM, 0)) == INVALID_SOCKET_TYPE) {
        printf("\nSocket creation error\n");
        return;
    }

    serv_addr.sin_family = AF_INET;
    serv_addr.sin_port = htons(P2P_PORT);
    serv_addr.sin_addr.s_addr = inet_addr(target_ip);
    
    sendto(sock, data, strlen(data), 0, (const struct sockaddr *)&serv_addr,
           sizeof(serv_addr));
    printf("Data forwarded to peer at %s\n", target_ip);
    CLOSE_SOCKET(sock);
}

void send_to_python(const char *message) {
    socket_t client_socket;
    struct sockaddr_in server_addr;

    if ((client_socket = socket(AF_INET, SOCK_DGRAM, 0)) == INVALID_SOCKET_TYPE) {
        printf("Python client socket creation failed\n");
        return;
    }

    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(PYTHON_PORT);
    server_addr.sin_addr.s_addr = inet_addr("127.0.0.1");

    sendto(client_socket, message, strlen(message), 0, 
           (struct sockaddr *)&server_addr, sizeof(server_addr));
           
    CLOSE_SOCKET(client_socket);
}

int main(int argc, char const *argv[]) {
    #ifdef _WIN32
        WSADATA wsa;
        if (WSAStartup(MAKEWORD(2,2), &wsa) != 0) {
            printf("WSAStartup failed\n");
            return 1;
        }
    #endif

    if (argc != 2) {
        printf("Usage: %s <target_ip>\n", argv[0]);
        return 1;
    }

    const char *target_ip = argv[1];
    socket_t python_sock, peer_sock;
    struct sockaddr_in python_addr, peer_addr, client_addr;
    socklen_t addr_len = sizeof(client_addr);
    char buffer[BUFFER_SIZE];

    // Sockets setup
    if ((python_sock = socket(AF_INET, SOCK_DGRAM, 0)) == INVALID_SOCKET_TYPE ||
        (peer_sock = socket(AF_INET, SOCK_DGRAM, 0)) == INVALID_SOCKET_TYPE) {
        printf("Socket creation failed\n");
        return 1;
    }
    SET_NONBLOCKING(python_sock);
    SET_NONBLOCKING(peer_sock);

    // Bind setup
    python_addr.sin_family = AF_INET;
    python_addr.sin_addr.s_addr = INADDR_ANY;
    python_addr.sin_port = htons(PYTHON_PORT);

    peer_addr.sin_family = AF_INET;
    peer_addr.sin_addr.s_addr = INADDR_ANY;
    peer_addr.sin_port = htons(P2P_PORT);

    if (bind(python_sock, (struct sockaddr *)&python_addr, sizeof(python_addr)) < 0 ||
        bind(peer_sock, (struct sockaddr *)&peer_addr, sizeof(peer_addr)) < 0) {
        printf("Bind failed\n");
        return 1;
    }

    printf("Network bridge running\n");
    printf("Python port: %d, P2P port: %d\n", PYTHON_PORT, P2P_PORT);
    printf("Target IP: %s\n", target_ip);

    while (1) {
        // Python -> Peer
        int n = recvfrom(python_sock, buffer, BUFFER_SIZE-1, 0,
                        (struct sockaddr *)&client_addr, &addr_len);
        if (n > 0) {
            buffer[n] = '\0';
            printf("Python -> Peer: %s\n", buffer);
            forward_to_peer(buffer, target_ip);
        }

        // Peer -> Python
        n = recvfrom(peer_sock, buffer, BUFFER_SIZE-1, 0,
                    (struct sockaddr *)&client_addr, &addr_len);
        if (n > 0) {
            buffer[n] = '\0';
            printf("Peer -> Python: %s\n", buffer);
            send_to_python(buffer);
        }

        SLEEP(SLEEP_TIME);
    }

    CLOSE_SOCKET(python_sock);
    CLOSE_SOCKET(peer_sock);
    #ifdef _WIN32
        WSACleanup();
    #endif
    return 0;
}