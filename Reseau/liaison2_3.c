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
#endif

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define PYTHON_PORT 12345
#define P2P_PORT 8000
#define BUFFER_SIZE 2000
#define SLEEP_TIME 1

// Fonction pour recevoir les messages du pair
void receive_from_peer(socket_t peer_sock) {
    struct sockaddr_in addr;
    socklen_t addr_len = sizeof(addr);
    char buffer[BUFFER_SIZE] = {0};

    int n = recvfrom(peer_sock, buffer, sizeof(buffer) - 1, 0,
                     (struct sockaddr *)&addr, &addr_len);
    
    if (n > 0) {
        buffer[n] = '\0';
        printf("Received from peer: %s\n", buffer);
    }
}

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
    
    if (serv_addr.sin_addr.s_addr == INADDR_NONE) {
        printf("\nInvalid address/ Address not supported\n");
        CLOSE_SOCKET(sock);
        return;
    }

    sendto(sock, data, strlen(data), 0, (const struct sockaddr *)&serv_addr,
           sizeof(serv_addr));
    printf("Data forwarded to peer at %s\n", target_ip);
    CLOSE_SOCKET(sock);
}

int main(int argc, char const *argv[]) {
    if (argc != 2) {
        printf("Usage: %s <target_ip>\n", argv[0]);
        return 1;
    }

    const char *target_ip = argv[1];
    socket_t python_sock, peer_sock;
    struct sockaddr_in python_addr, peer_addr, client_addr;
    socklen_t addr_len = sizeof(client_addr);
    char buffer[BUFFER_SIZE];

    #ifdef _WIN32
        WSADATA wsa;
        if (WSAStartup(MAKEWORD(2,2), &wsa) != 0) {
            printf("WSAStartup failed\n");
            return 1;
        }
    #endif

    // Socket pour Python
    if ((python_sock = socket(AF_INET, SOCK_DGRAM, 0)) == INVALID_SOCKET_TYPE) {
        perror("Python socket creation failed");
        return 1;
    }
    SET_NONBLOCKING(python_sock);

    // Socket pour P2P
    if ((peer_sock = socket(AF_INET, SOCK_DGRAM, 0)) == INVALID_SOCKET_TYPE) {
        perror("Peer socket creation failed");
        return 1;
    }
    SET_NONBLOCKING(peer_sock);

    // Configuration du socket Python
    memset(&python_addr, 0, sizeof(python_addr));
    python_addr.sin_family = AF_INET;
    python_addr.sin_addr.s_addr = INADDR_ANY;
    python_addr.sin_port = htons(PYTHON_PORT);

    // Configuration du socket P2P
    memset(&peer_addr, 0, sizeof(peer_addr));
    peer_addr.sin_family = AF_INET;
    peer_addr.sin_addr.s_addr = INADDR_ANY;
    peer_addr.sin_port = htons(P2P_PORT);

    if (bind(python_sock, (struct sockaddr *)&python_addr, sizeof(python_addr)) < 0) {
        perror("Python socket bind failed");
        return 1;
    }

    if (bind(peer_sock, (struct sockaddr *)&peer_addr, sizeof(peer_addr)) < 0) {
        perror("Peer socket bind failed");
        return 1;
    }

    printf("Listening on ports - Python: %d, P2P: %d\n", PYTHON_PORT, P2P_PORT);
    printf("Will forward to %s:%d\n", target_ip, P2P_PORT);

    while (1) {
        // Vérifier les messages de Python
        int n = recvfrom(python_sock, buffer, BUFFER_SIZE-1, 0,
                        (struct sockaddr *)&client_addr, &addr_len);
        if (n > 0) {
            buffer[n] = '\0';
            printf("Received from Python: %s\n", buffer);
            forward_to_peer(buffer, target_ip);
        }

        // Vérifier les messages des pairs
        receive_from_peer(peer_sock);

        SLEEP(SLEEP_TIME);
    }

    CLOSE_SOCKET(python_sock);
    CLOSE_SOCKET(peer_sock);
    #ifdef _WIN32
        WSACleanup();
    #endif
    return 0;
}