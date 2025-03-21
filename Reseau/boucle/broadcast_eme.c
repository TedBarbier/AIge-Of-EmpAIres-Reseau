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

void send_broadcast_message(const char *message) {
#ifdef _WIN32
    SOCKET sock;
#else
    int sock;
#endif
    struct sockaddr_in broadcast_addr;
    int broadcast_enable = 1;

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

    // Activer le broadcast sur le socket
#ifdef _WIN32
    if (setsockopt(sock, SOL_SOCKET, SO_BROADCAST, (char*)&broadcast_enable, sizeof(broadcast_enable)) == SOCKET_ERROR) {
        printf("Erreur lors de l'activation du broadcast: %d\n", WSAGetLastError());
        CLOSE_SOCKET(sock);
        exit(EXIT_FAILURE);
    }
#else
    if (setsockopt(sock, SOL_SOCKET, SO_BROADCAST, &broadcast_enable, sizeof(broadcast_enable)) < 0) {
        perror("setsockopt");
        CLOSE_SOCKET(sock);
        exit(EXIT_FAILURE);
    }
#endif

    // Configurer l'adresse de broadcast
    memset(&broadcast_addr, 0, sizeof(broadcast_addr));
    broadcast_addr.sin_family = AF_INET;
    broadcast_addr.sin_addr.s_addr = inet_addr("255.255.255.255");  // Adresse de broadcast
    broadcast_addr.sin_port = htons(BROADCAST_PORT);

    // Envoyer le message
    if (sendto(sock, message, strlen(message), 0, 
               (struct sockaddr *)&broadcast_addr, sizeof(broadcast_addr)) < 0) {
#ifdef _WIN32
        printf("Erreur lors de l'envoi du message: %d\n", WSAGetLastError());
#else
        perror("sendto");
#endif
        CLOSE_SOCKET(sock);
        exit(EXIT_FAILURE);
    }

    printf("Message envoyé avec succès: %s\n", message);
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

    char message[MAX_MSG_SIZE];
    printf("Entrez votre message (max %d caractères): ", MAX_MSG_SIZE - 1);
    fgets(message, MAX_MSG_SIZE, stdin);
    
    // Supprimer le retour à la ligne
    message[strcspn(message, "\n")] = 0;
    
    send_broadcast_message(message);

#ifdef _WIN32
    WSACleanup();
#endif
    return 0;
}
