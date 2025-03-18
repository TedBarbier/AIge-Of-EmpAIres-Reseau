#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#ifdef _WIN32
    #include <winsock2.h>
    #include <ws2tcpip.h>
    #pragma comment(lib, "ws2_32.lib")
#else
    #include <sys/socket.h>
    #include <netinet/in.h>
    #include <unistd.h>
#endif


#define PORT 12345
#define SERVER_IP "127.0.0.1"
#define BUFFER_SIZE 1024

int main(int argc, char *argv[]) {
    if (argc != 2) {
        fprintf(stderr, "Usage: %s <mode>\nModes: server, client\n", argv[0]);
        return EXIT_FAILURE;
    }

    char *mode = argv[1];

    WSADATA wsaData;
    int iResult = WSAStartup(MAKEWORD(2, 2), &wsaData);
    if (iResult != 0) {
        fprintf(stderr, "WSAStartup failed: %d\n", iResult);
        return EXIT_FAILURE;
    }

    if (strcmp(mode, "server") == 0) {
        printf("Démarrage en mode serveur UDP...\n");
        SOCKET server_socket;
        struct sockaddr_in server_addr, client_addr;
        int client_addr_len = sizeof(client_addr);
        char buffer[BUFFER_SIZE];

        // Créer le socket UDP (SOCK_DGRAM et IPPROTO_UDP)
        if ((server_socket = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)) == INVALID_SOCKET) {
            perror("socket creation failed");
            WSACleanup();
            return EXIT_FAILURE;
        }

        memset(&server_addr, 0, sizeof(server_addr));
        server_addr.sin_family = AF_INET;
        server_addr.sin_addr.s_addr = INADDR_ANY;
        server_addr.sin_port = htons(PORT);

        if (bind(server_socket, (struct sockaddr *)&server_addr, sizeof(server_addr)) == SOCKET_ERROR) {
            perror("bind failed");
            closesocket(server_socket);
            WSACleanup();
            return EXIT_FAILURE;
        }

        printf("Serveur UDP en écoute sur le port %d...\n", PORT);

        while (1) { // Boucle pour recevoir continuellement
            memset(buffer, 0, BUFFER_SIZE);
            int recv_len = recvfrom(server_socket, buffer, BUFFER_SIZE - 1, 0, (struct sockaddr *)&client_addr, &client_addr_len);
            if (recv_len == SOCKET_ERROR) {
                perror("recvfrom failed");
                closesocket(server_socket);
                WSACleanup();
                return EXIT_FAILURE;
            }

            if (recv_len > 0) {
                printf("Message reçu de %s:%d: \"%s\"\n", inet_ntoa(client_addr.sin_addr), ntohs(client_addr.sin_port), buffer);
                char expected_message[] = "Rejoindre la partie";
                if (strcmp(buffer, expected_message) == 0) {
                    printf("Message vérifié avec succès!\n");
                } else {
                    printf("Erreur: Message reçu ne correspond pas au message attendu.\n");
                }
            }
        }
        closesocket(server_socket); // Ne sera probablement jamais atteint dans cette boucle infinie, mais pour la bonne forme
    } else if (strcmp(mode, "client") == 0) {
        printf("Démarrage en mode client UDP...\n");
        SOCKET client_socket;
        struct sockaddr_in server_addr;
        char message[] = "Rejoindre la partie";

        if ((client_socket = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)) == INVALID_SOCKET) {
            perror("socket creation failed");
            WSACleanup();
            return EXIT_FAILURE;
        }

        memset(&server_addr, 0, sizeof(server_addr));
        server_addr.sin_family = AF_INET;
        server_addr.sin_port = htons(PORT);
        if (inet_pton(AF_INET, SERVER_IP, &server_addr.sin_addr) <= 0) {
            perror("inet_pton failed");
            closesocket(client_socket);
            WSACleanup();
            return EXIT_FAILURE;
        }

        // Envoyer le message avec sendto (pas de connect pour UDP)
        if (sendto(client_socket, message, strlen(message), 0, (struct sockaddr *)&server_addr, sizeof(server_addr)) == SOCKET_ERROR) {
            perror("sendto failed");
            closesocket(client_socket);
            WSACleanup();
            return EXIT_FAILURE;
        }

        printf("Message UDP envoyé: \"%s\"\n", message);
        closesocket(client_socket);
    } else {
        fprintf(stderr, "Mode invalide. Utilisez 'server' ou 'client'.\n");
        WSACleanup();
        return EXIT_FAILURE;
    }

    WSACleanup();
    return EXIT_SUCCESS;
}