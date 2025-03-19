#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <winsock2.h>

#define PORT 12345
#define BUFFER_SIZE 1024

int main() {
    WSADATA wsa;
    SOCKET sockfd;
    struct sockaddr_in server_addr, client_addr;
    char buffer[BUFFER_SIZE];
    int addr_len = sizeof(client_addr);

    // Initialiser Winsock
    if (WSAStartup(MAKEWORD(2, 2), &wsa) != 0) {
        printf("WSAStartup failed. Error Code: %d\n", WSAGetLastError());
        return 1;
    }

    // Création du socket UDP
    if ((sockfd = socket(AF_INET, SOCK_DGRAM, 0)) == INVALID_SOCKET) {
        perror("Erreur de création du socket");
        WSACleanup();
        return 1;
    }

    // Configuration de l'adresse du serveur
    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_addr.s_addr = INADDR_ANY;  // Écouter sur toutes les interfaces
    server_addr.sin_port = htons(PORT);

    // Lier le socket à l'adresse et au port
    if (bind(sockfd, (struct sockaddr *)&server_addr, sizeof(server_addr)) == SOCKET_ERROR) {
        perror("Erreur de bind");
        closesocket(sockfd);
        WSACleanup();
        return 1;
    }

    printf("Serveur UDP en écoute sur %s:%d...\n", "127.0.0.1", PORT);

    // Boucle infinie pour recevoir des messages
    while (1) {
        int n = recvfrom(sockfd, buffer, BUFFER_SIZE, 0, (struct sockaddr *)&client_addr, &addr_len);
        if (n == SOCKET_ERROR) {
            perror("Erreur de réception");
            break;
        }

        buffer[n] = '\0';  // Ajouter le caractère de fin de chaîne
        printf("Message reçu : %s\n", buffer);
    }

    // Fermer le socket et nettoyer
    closesocket(sockfd);
    WSACleanup();
    return 0;
}
