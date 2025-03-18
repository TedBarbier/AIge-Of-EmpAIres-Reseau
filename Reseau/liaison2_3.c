#define _WIN32_WINNT 0x0600
#include <winsock2.h>
#include <ws2tcpip.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define PYTHON_PORT 12345
#define P2P_PORT 8000
#define BUFFER_SIZE 2000

// Fonction pour envoyer les données vers un autre PC
void forward_to_peer(const char *data, const char *target_ip) {
    SOCKET sock;
    struct sockaddr_in serv_addr;
    
    if ((sock = socket(AF_INET, SOCK_DGRAM, 0)) == INVALID_SOCKET) {
        printf("\nSocket creation error\n");
        return;
    }

    serv_addr.sin_family = AF_INET;
    serv_addr.sin_port = htons(P2P_PORT);

    // Using inet_addr instead of inet_pton for better compatibility
    serv_addr.sin_addr.s_addr = inet_addr(target_ip);
    if (serv_addr.sin_addr.s_addr == INADDR_NONE) {
        printf("\nInvalid address/ Address not supported\n");
        closesocket(sock);
        return;
    }

    // Envoyer les données
    sendto(sock, data, strlen(data), 0, (const struct sockaddr *)&serv_addr,
           sizeof(serv_addr));
    printf("Data forwarded to peer at %s\n", target_ip);
    closesocket(sock);
}

int main(int argc, char const *argv[]) {
    if (argc != 2) {
        printf("Usage: %s <target_ip>\n", argv[0]);
        return 1;
    }

    const char *target_ip = argv[1];
    WSADATA wsa;
    SOCKET sockfd;
    struct sockaddr_in server_addr, client_addr;
    int addr_len = sizeof(client_addr);
    char buffer[BUFFER_SIZE];

    // Initialiser Winsock
    if (WSAStartup(MAKEWORD(2,2), &wsa) != 0) {
        printf("WSAStartup failed\n");
        return 1;
    }

    // Créer socket UDP pour recevoir de Python
    if ((sockfd = socket(AF_INET, SOCK_DGRAM, 0)) == INVALID_SOCKET) {
        perror("Socket creation failed");
        WSACleanup();
        return 1;
    }

    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_addr.s_addr = INADDR_ANY;
    server_addr.sin_port = htons(PYTHON_PORT);

    if (bind(sockfd, (struct sockaddr *)&server_addr, sizeof(server_addr)) < 0) {
        perror("Bind failed");
        closesocket(sockfd);
        WSACleanup();
        return 1;
    }

    printf("Waiting for Python data on port %d to forward to %s:%d...\n", 
           PYTHON_PORT, target_ip, P2P_PORT);

    while (1) {
        int n = recvfrom(sockfd, buffer, BUFFER_SIZE-1, 0,
                        (struct sockaddr *)&client_addr, &addr_len);

        if (n > 0) {
            buffer[n] = '\0';
            printf("Received from Python: %s\n", buffer);
            
            // Transférer les données vers le pair
            forward_to_peer(buffer, target_ip);
        }
    }

    closesocket(sockfd);
    WSACleanup();
    return 0;
}