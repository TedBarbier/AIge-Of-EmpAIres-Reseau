#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <winsock2.h>
#include <ws2tcpip.h>
#include <stdint.h>

#define PORT 12345
#define BUFFER_SIZE 1024

// Fonction pour afficher les données reçues
void process_game_data(char *data) {
    printf("Données reçues : %s\n", data);
}

int main() {
    WSADATA wsa;
    if (WSAStartup(MAKEWORD(2,2), &wsa) != 0) {
        printf("Échec de l'initialisation de Winsock\n");
        return 1;
    }

    int sockfd;
    struct sockaddr_in server_addr, client_addr;
    socklen_t addr_len = sizeof(client_addr);
    char buffer[BUFFER_SIZE];

    // Création du socket UDP
    if ((sockfd = socket(AF_INET, SOCK_DGRAM, 0)) < 0) {
        perror("Erreur de création du socket");
        exit(EXIT_FAILURE);
    }

    // Configuration de l'adresse du serveur
    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_addr.s_addr = INADDR_ANY;
    server_addr.sin_port = htons(PORT);

    // Lier le socket à l'adresse et au port
    if (bind(sockfd, (const struct sockaddr *)&server_addr, sizeof(server_addr)) < 0) {
        perror("Erreur de binding");
        close(sockfd);
        exit(EXIT_FAILURE);
    }

    printf("Serveur UDP en attente sur le port %d...\n", PORT);

    while (1) {
        // Réception des données du client
        int n = recvfrom(sockfd, buffer, sizeof(buffer) - 1, 0, 
                         (struct sockaddr *)&client_addr, &addr_len);

        if (n < 0) {
            perror("Erreur de réception");
            int error_code = WSAGetLastError();
            printf("Code d'erreur: %d\n", error_code);
            continue;
        }

        // S'assurer que le buffer est bien terminé par un '\0'
        buffer[n] = '\0';

        // Afficher l'adresse du client et les données reçues
        printf("Reçu de %s:%d\n", 
               inet_ntoa(client_addr.sin_addr), 
               ntohs(client_addr.sin_port));
        process_game_data(buffer);
    }

    WSACleanup();
    closesocket(sockfd);
    return 0;
}
