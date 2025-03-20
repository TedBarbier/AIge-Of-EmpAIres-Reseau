#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifdef _WIN32
    #include <winsock2.h>
    #include <ws2tcpip.h>
    #define CLOSE_SOCKET(sock) closesocket(sock)
    #define SOCKET_ERROR_CODE WSAGetLastError()
#else
    #include <unistd.h>
    #include <sys/socket.h>
    #include <netinet/in.h>
    #include <arpa/inet.h>
    #define CLOSE_SOCKET(sock) close(sock)
    #define SOCKET_ERROR_CODE errno
#endif

#define BROADCAST_PORT 8000
#define MAX_MSG_SIZE 1024

void receive_broadcast_message() {
#ifdef _WIN32
    SOCKET sock;
#else
    int sock;
#endif
    struct sockaddr_in receiver_addr;
    char buffer[MAX_MSG_SIZE];
#ifdef _WIN32
    int addr_len = sizeof(receiver_addr);
#else
    socklen_t addr_len = sizeof(receiver_addr);
#endif

    // Créer un socket UDP
    sock = socket(AF_INET, SOCK_DGRAM, 0);
#ifdef _WIN32
    if (sock == INVALID_SOCKET) {
        printf("Erreur lors de la création du socket: %d\n", WSAGetLastError());
        exit(EXIT_FAILURE);
    }
#else
    if (sock < 0) {
        perror("socket");
        exit(EXIT_FAILURE);
    }
#endif

    // Permettre la réutilisation de l'adresse
    int reuse = 1;
#ifdef _WIN32
    if (setsockopt(sock, SOL_SOCKET, SO_REUSEADDR, (char*)&reuse, sizeof(reuse)) == SOCKET_ERROR) {
        printf("Erreur lors de la configuration du socket: %d\n", WSAGetLastError());
        CLOSE_SOCKET(sock);
        exit(EXIT_FAILURE);
    }
#else
    if (setsockopt(sock, SOL_SOCKET, SO_REUSEADDR, &reuse, sizeof(reuse)) < 0) {
        perror("setsockopt");
        CLOSE_SOCKET(sock);
        exit(EXIT_FAILURE);
    }
#endif

    // Configurer l'adresse de réception
    memset(&receiver_addr, 0, sizeof(receiver_addr));
    receiver_addr.sin_family = AF_INET;
    receiver_addr.sin_addr.s_addr = htonl(INADDR_ANY);
    receiver_addr.sin_port = htons(BROADCAST_PORT);

    // Lier le socket au port
    if (bind(sock, (struct sockaddr *)&receiver_addr, sizeof(receiver_addr)) < 0) {
#ifdef _WIN32
        printf("Erreur lors de la liaison: %d\n", WSAGetLastError());
#else
        perror("bind");
#endif
        CLOSE_SOCKET(sock);
        exit(EXIT_FAILURE);
    }

    printf("En écoute des messages broadcast sur le port %d...\n", BROADCAST_PORT);

    // Boucle de réception des messages
    while (1) {
        int bytes_received = recvfrom(sock, buffer, sizeof(buffer), 0,
                                    (struct sockaddr *)&receiver_addr, &addr_len);
#ifdef _WIN32
        if (bytes_received == SOCKET_ERROR) {
            printf("Erreur lors de la réception: %d\n", WSAGetLastError());
            CLOSE_SOCKET(sock);
            exit(EXIT_FAILURE);
        }
#else
        if (bytes_received < 0) {
            perror("recvfrom");
            CLOSE_SOCKET(sock);
            exit(EXIT_FAILURE);
        }
#endif
        buffer[bytes_received] = '\0';
        printf("Message reçu: %s de %s:%d\n", buffer,
               inet_ntoa(receiver_addr.sin_addr), ntohs(receiver_addr.sin_port));
    }

    CLOSE_SOCKET(sock);
}

int main() {
#ifdef _WIN32
    WSADATA wsaData;
    if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0) {
        printf("Erreur d'initialisation de Winsock\n");
        return 1;
    }
#endif

    receive_broadcast_message();

#ifdef _WIN32
    WSACleanup();
#endif
    return 0;
}
