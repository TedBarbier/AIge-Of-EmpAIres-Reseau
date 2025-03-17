#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>

#define PORT 12345
#define SERVER_IP "127.0.0.1"

void handle_client(int client_socket);

int main(int argc, char *argv[]) {
    if (argc != 2) {
        fprintf(stderr, "Usage: %s <mode>\nModes: server, client\n", argv[0]);
        return EXIT_FAILURE;
    }

    char *mode = argv[1];

    if (strcmp(mode, "server") == 0) {
        printf("Démarrage en mode serveur...\n");
        int server_fd, new_socket;
        struct sockaddr_in address;
        int addrlen = sizeof(address);

        // Créer le socket serveur
        if ((server_fd = socket(AF_INET, SOCK_STREAM, 0)) == 0) {
            perror("socket failed");
            return EXIT_FAILURE;
        }

        address.sin_family = AF_INET;
        address.sin_addr.s_addr = INADDR_ANY; // Écouter sur toutes les interfaces
        address.sin_port = htons(PORT);

        // Liaison du socket au port
        if (bind(server_fd, (struct sockaddr *)&address, sizeof(address)) < 0) {
            perror("bind failed");
            return EXIT_FAILURE;
        }
        if (listen(server_fd, 3) < 0) { // 3 connexions en attente max
            perror("listen");
            return EXIT_FAILURE;
        }
        if ((new_socket = accept(server_fd, (struct sockaddr *)&address, (socklen_t*)&addrlen)) < 0) {
            perror("accept");
            return EXIT_FAILURE;
        }
        handle_client(new_socket);
        close(server_fd); // Fermer le socket serveur après avoir servi une connexion
    } else if (strcmp(mode, "client") == 0) {
        printf("Démarrage en mode client...\n");
        int sockfd = 0;
        struct sockaddr_in serv_addr;
        char message[] = "Bonjour Python depuis C!";

        if ((sockfd = socket(AF_INET, SOCK_STREAM, 0)) < 0) {
            perror("Erreur lors de la création du socket");
            return EXIT_FAILURE;
        }

        serv_addr.sin_family = AF_INET;
        serv_addr.sin_port = htons(PORT);
        if (inet_pton(AF_INET, SERVER_IP, &serv_addr.sin_addr) <= 0) {
            perror("Adresse invalide/ Adresse non supportée");
            return EXIT_FAILURE;
        }

        if (connect(sockfd, (struct sockaddr *)&serv_addr, sizeof(serv_addr)) < 0) {
            perror("Erreur de connexion au serveur");
            return EXIT_FAILURE;
        }

        if (send(sockfd, message, strlen(message), 0) < 0) {
            perror("Erreur lors de l'envoi du message");
            return EXIT_FAILURE;
        }

        printf("Message envoyé depuis C: \"%s\"\n", message);
        close(sockfd);
    } else {
        fprintf(stderr, "Mode invalide. Utilisez 'server' ou 'client'.\n");
        return EXIT_FAILURE;
    }

    return EXIT_SUCCESS;
}

void handle_client(int client_socket) {
    char buffer[1024] = {0};
    int valread;
    char expected_message[] = "Bonjour Python depuis C!";

    valread = read(client_socket, buffer, 1024);
    if (valread > 0) {
        printf("Message reçu depuis le client: \"%s\"\n", buffer);
        if (strcmp(buffer, expected_message) == 0) {
            printf("Message vérifié avec succès!\n");
        } else {
            printf("Erreur: Message reçu ne correspond pas au message attendu.\n");
        }
    } else if (valread == 0) {
        printf("Client déconnecté.\n");
    } else {
        perror("Erreur de lecture");
    }
    close(client_socket);
}