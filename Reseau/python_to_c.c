#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
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
#define BUFFER_SIZE 1024

typedef struct {
    int villager_count;
    struct {
        int wood;
        int food;
        int stone;
        int gold;
    } resources;
    float military_ratio;
    unsigned short storage_count;
    unsigned short training_count;
    unsigned short military_free;
    unsigned short villager_total;
    unsigned short villager_free;
    unsigned char housing_crisis;
} GameState;

void init_winsock(void) {
    #ifdef _WIN32
    WSADATA wsa_data;
    if (WSAStartup(MAKEWORD(2, 2), &wsa_data) != 0) {
        fprintf(stderr, "WSAStartup failed\n");
        exit(1);
    }
    #endif
}

int main(void) {
    SOCKET udp_socket;
    struct sockaddr_in local_addr, client_addr;
    char buffer[BUFFER_SIZE];
    int addr_len = sizeof(client_addr);

    init_winsock();

    // Création socket UDP
    if ((udp_socket = socket(AF_INET, SOCK_DGRAM, 0)) == INVALID_SOCKET) {
        perror("Socket creation failed");
        return 1;
    }

    // Configuration adresse
    local_addr.sin_family = AF_INET;
    local_addr.sin_addr.s_addr = INADDR_ANY;
    local_addr.sin_port = htons(PORT);

    // Bind
    if (bind(udp_socket, (struct sockaddr*)&local_addr, sizeof(local_addr)) < 0) {
        perror("Bind failed");
        return 1;
    }

    printf("Listening for UDP packets on port %d...\n", PORT);

    while (1) {
        // Recevoir les données
        int recv_size = recvfrom(udp_socket, buffer, sizeof(buffer), 0,
                                 (struct sockaddr*)&client_addr, &addr_len);

        if (recv_size < 0) {
            perror("recvfrom failed");
            continue; // Passe à la prochaine itération
        }

        buffer[recv_size] = '\0'; // Terminer la chaîne de caractères
        printf("Received packet from %s:%d\n", inet_ntoa(client_addr.sin_addr), ntohs(client_addr.sin_port));
        printf("Received message: %s\n", buffer);

        // Parser la chaîne
        GameState state = {0};
        sscanf(buffer, "%d %d %d %d %d %f %hd %hd %hd %hd %hd %hhd",
               &state.villager_count,
               &state.resources.wood, &state.resources.food, &state.resources.stone, &state.resources.gold,
               &state.military_ratio,
               &state.storage_count, &state.training_count,
               &state.military_free, &state.villager_total, &state.villager_free,
               &state.housing_crisis);

        // Affichage de l'état du jeu
        printf("\nGame State Update:\n");
        printf("Villager Count: %d\n", state.villager_count);
        printf("Resources - Wood: %d, Food: %d, Stone: %d, Gold: %d\n",
               state.resources.wood, state.resources.food,
               state.resources.stone, state.resources.gold);
        printf("Military Ratio: %.2f\n", state.military_ratio);
        printf("Buildings - Storage: %d, Training: %d\n",
               state.storage_count, state.training_count);
        printf("Units - Military Free: %d, Villagers: %d (Free: %d)\n",
               state.military_free, state.villager_total, state.villager_free);
        printf("Housing Crisis: %s\n", state.housing_crisis ? "Yes" : "No");
    }

    #ifdef _WIN32
        closesocket(udp_socket);
        WSACleanup();
    #else
        close(udp_socket);
    #endif

    return 0;
}
