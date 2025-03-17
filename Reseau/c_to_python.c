#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
// #include <sys/socket.h>
// #include <netinet/in.h>
// #include <arpa/inet.h>
#include <unistd.h> /* Pour close() sous Windows avec MinGW */
#include <winsock2.h> /* Pour Winsock2 (sockets Windows) */
#include <ws2tcpip.h> /* Pour inet_pton et inet_ntop sous Windows */

#define PORT 12345
#define SERVER_IP "127.0.0.1"

void handle_client(SOCKET client_socket); // Utilisez SOCKET au lieu de int pour les sockets Windows

int main(int argc, char *argv[]) {
    if (argc != 2) {
        fprintf(stderr, "Usage: %s <mode>\nModes: server, client\n", argv[0]);
        return EXIT_FAILURE;
    }

    char *mode = argv[1];

    // Initialisation de Winsock
    WSADATA wsaData;
    int iResult = WSAStartup(MAKEWORD(2, 2), &wsaData);
    if (iResult != 0) {
        fprintf(stderr, "WSAStartup failed: %d\n", iResult);
        return EXIT_FAILURE;
    }

    if (strcmp(mode, "server") == 0) {
        printf("Démarrage en mode serveur...\n");
        SOCKET server_fd, new_socket; // Utilisez SOCKET pour les sockets Windows
        struct sockaddr_in address;
        int addrlen = sizeof(address);

        // Créer le socket serveur (utilisation de SOCK_STREAM et IPPROTO_TCP)
        if ((server_fd = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP)) == INVALID_SOCKET) {
            perror("socket failed");
            WSACleanup(); // Nettoyage Winsock en cas d'erreur
            return EXIT_FAILURE;
        }

        address.sin_family = AF_INET;
        address.sin_addr.s_addr = INADDR_ANY; // Écouter sur toutes les interfaces
        address.sin_port = htons(PORT);

        // Liaison du socket au port
        if (bind(server_fd, (struct sockaddr *)&address, sizeof(address)) == SOCKET_ERROR) {
            perror("bind failed");
            closesocket(server_fd); // Utilisez closesocket pour fermer les sockets Windows
            WSACleanup();
            return EXIT_FAILURE;
        }
        if (listen(server_fd, 3) == SOCKET_ERROR) { // 3 connexions en attente max
            perror("listen");
            closesocket(server_fd);
            WSACleanup();
            return EXIT_FAILURE;
        }
        if ((new_socket = accept(server_fd, (struct sockaddr *)&address, &addrlen)) == INVALID_SOCKET) {
            perror("accept");
            closesocket(server_fd);
            WSACleanup();
            return EXIT_FAILURE;
        }
        handle_client(new_socket);
        closesocket(server_fd); // Fermer le socket serveur après avoir servi une connexion

    } else if (strcmp(mode, "client") == 0) {
        printf("Démarrage en mode client...\n");
        SOCKET sockfd = INVALID_SOCKET; // Utilisez SOCKET et initialisez à INVALID_SOCKET
        struct sockaddr_in serv_addr;
        char message[] = "Bonjour Python depuis C!";

        if ((sockfd = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP)) == INVALID_SOCKET) {
            perror("Erreur lors de la création du socket");
            WSACleanup();
            return EXIT_FAILURE;
        }

        serv_addr.sin_family = AF_INET;
        serv_addr.sin_port = htons(PORT);
        if (inet_pton(AF_INET, SERVER_IP, &serv_addr.sin_addr) <= 0) {
            perror("Adresse invalide/ Adresse non supportée");
            closesocket(sockfd);
            WSACleanup();
            return EXIT_FAILURE;
        }

        if (connect(sockfd, (struct sockaddr *)&serv_addr, sizeof(serv_addr)) == SOCKET_ERROR) {
            perror("Erreur de connexion au serveur");
            closesocket(sockfd);
            WSACleanup();
            return EXIT_FAILURE;
        }

        if (send(sockfd, message, strlen(message), 0) == SOCKET_ERROR) {
            perror("Erreur lors de l'envoi du message");
            closesocket(sockfd);
            WSACleanup();
            return EXIT_FAILURE;
        }

        printf("Message envoyé depuis C: \"%s\"\n", message);
        closesocket(sockfd);
    } else {
        fprintf(stderr, "Mode invalide. Utilisez 'server' ou 'client'.\n");
        WSACleanup();
        return EXIT_FAILURE;
    }

    WSACleanup(); // Nettoyage de Winsock avant de quitter
    return EXIT_SUCCESS;
}

void handle_client(SOCKET client_socket) { // Utilisez SOCKET pour les sockets Windows
    char buffer[1024] = {0};
    int valread;
    char expected_message[] = "Bonjour Python depuis C!";

    valread = recv(client_socket, buffer, 1024, 0); // Utilisez recv pour recevoir sous Windows
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
    closesocket(client_socket); // Utilisez closesocket pour fermer les sockets Windows
}