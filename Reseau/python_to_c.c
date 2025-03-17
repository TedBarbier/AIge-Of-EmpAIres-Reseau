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
    SOCKET listen_socket;
    struct sockaddr_in local_addr, client_addr;
    char buffer[BUFFER_SIZE];
    int addr_len = sizeof(client_addr);
    uint32_t data_size;
    GameState state = {0};

    init_winsock();

    // Création socket UDP
    if ((listen_socket = socket(AF_INET, SOCK_DGRAM, 0)) == INVALID_SOCKET) {
        perror("Socket creation failed");
        return 1;
    }

    // Configuration adresse
    local_addr.sin_family = AF_INET;
    local_addr.sin_addr.s_addr = INADDR_ANY;
    local_addr.sin_port = htons(PORT);

    // Bind
    if (bind(listen_socket, (struct sockaddr*)&local_addr, sizeof(local_addr)) < 0) {
        perror("Bind failed");
        return 1;
    }

    printf("Listening on port %d...\n", PORT);

    while (1) {
        // Receive data
        if (recvfrom(listen_socket, buffer, sizeof(buffer), 0, (struct sockaddr*)&client_addr, &addr_len) > 0) {
            printf("Received message from %s:%d\n", 
                   inet_ntoa(client_addr.sin_addr), 
                   ntohs(client_addr.sin_port));

            // Unpack data in order
            int offset = 0;

            memcpy(&state.villager_count, buffer + offset, sizeof(int));
            offset += sizeof(int);

            memcpy(&state.resources.wood, buffer + offset, sizeof(int));
            offset += sizeof(int);
            memcpy(&state.resources.food, buffer + offset, sizeof(int));
            offset += sizeof(int);
            memcpy(&state.resources.stone, buffer + offset, sizeof(int));
            offset += sizeof(int);
            memcpy(&state.resources.gold, buffer + offset, sizeof(int));
            offset += sizeof(int);

            memcpy(&state.military_ratio, buffer + offset, sizeof(float));
            offset += sizeof(float);

            memcpy(&state.storage_count, buffer + offset, sizeof(unsigned short));
            offset += sizeof(unsigned short);
            memcpy(&state.training_count, buffer + offset, sizeof(unsigned short));
            offset += sizeof(unsigned short);

            memcpy(&state.military_free, buffer + offset, sizeof(unsigned short));
            offset += sizeof(unsigned short);
            memcpy(&state.villager_total, buffer + offset, sizeof(unsigned short));
            offset += sizeof(unsigned short);
            memcpy(&state.villager_free, buffer + offset, sizeof(unsigned short));
            offset += sizeof(unsigned short);

            memcpy(&state.housing_crisis, buffer + offset, sizeof(unsigned char));

            // Print received state
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
    }

    return 0;
}
