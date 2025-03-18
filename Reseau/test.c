#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <winsock2.h>
#include <ws2tcpip.h>
#include <stdint.h>
#include "cJSON.h"  // Inclure la bibliothèque cJSON

#define PORT 12345
#define BUFFER_SIZE 1024

// Fonction pour traiter les données JSON reçues
void process_game_data(char *data) {
    printf("Données reçues : %s\n", data);

    // Parser le JSON
    cJSON *json = cJSON_Parse(data);
    if (json == NULL) {
        printf("Erreur : JSON invalide\n");
        return;
    }

    // Extraire les données JSON
    cJSON *action_name = cJSON_GetObjectItemCaseSensitive(json, "action_name");
    cJSON *parameters = cJSON_GetObjectItemCaseSensitive(json, "parameters");

    if (cJSON_IsString(action_name) && (action_name->valuestring != NULL)) {
        printf("Action : %s\n", action_name->valuestring);
    }

    if (cJSON_IsObject(parameters)) {
        printf("Paramètres :\n");
        cJSON *param = NULL;
        cJSON_ArrayForEach(param, parameters) {
            if (cJSON_IsNumber(param)) {
                printf("  %s: %d\n", param->string, param->valueint);
            } else if (cJSON_IsString(param)) {
                printf("  %s: %s\n", param->string, param->valuestring);
            }
        }
    }

    // Libérer la mémoire JSON
    cJSON_Delete(json);
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

    printf("Serveur UDP en attente des données JSON...\n");

    while (1) {
        // Réception des données du client sous forme de JSON
        int n = recvfrom(sockfd, buffer, sizeof(buffer) - 1, 0, 
                         (struct sockaddr *)&client_addr, &addr_len);

        int error_code = WSAGetLastError();
        printf("Erreur de réception (code %d)\n", error_code);
        if (n < 0) {
            perror("Erreur de réception");
            continue;
        }

        // S'assurer que le buffer est bien terminé par un '\0'
        buffer[n] = '\0';

        // Traiter les données reçues
        process_game_data(buffer);
    }

    WSACleanup();
    close(sockfd);
    return 0;
}
