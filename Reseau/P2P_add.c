#ifdef _WIN32
    #include <winsock2.h>
    #include <ws2tcpip.h>
    #pragma comment(lib, "ws2_32.lib")
    typedef SOCKET socket_t;
    #define SOCKET_ERROR_TYPE SOCKET_ERROR
    #define INVALID_SOCKET_TYPE INVALID_SOCKET
    #define CLOSE_SOCKET(s) closesocket(s)
#else
    #include <unistd.h>
    #include <sys/socket.h>
    #include <netinet/in.h>
    #include <arpa/inet.h>
    typedef int socket_t;
    #define SOCKET_ERROR_TYPE -1
    #define INVALID_SOCKET_TYPE -1
    #define CLOSE_SOCKET(s) close(s)
#endif

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// Variables globales
char name[20];
int PORT;
int port_used[20];
char global_ip_address[16] = "127.0.0.1";  // IP par défaut

// Fonction d'envoi de messages
void sending() {
    char buffer[2000] = {0};
    char hello[1024] = {0};
    int success_count = 0;
    char target_ip[16] = {0};
    int target_port = 0;
    int broadcast_mode = 0;
    
    // Afficher les ports connus
    printf("\nPorts connectés: ");
    int port_count = 0;
    for (int i = 0; i < 20; i++) {
        if (port_used[i] != 0 && port_used[i] != PORT) {
            printf("%d ", port_used[i]);
            port_count++;
        }
    }
    if (port_count == 0) {
        printf("Aucun");
    }
    printf("\n");
    
    printf("Envoyer à tous les clients connus (1) ou à une adresse IP spécifique (2) ? ");
    int choice;
    scanf("%d", &choice);
    
    char dummy;
    scanf("%c", &dummy); // Clear buffer
    
    if (choice == 2) {
        printf("Entrez l'adresse IP cible: ");
        scanf("%15s", target_ip);
        printf("Entrez le port cible: ");
        scanf("%d", &target_port);
        scanf("%c", &dummy); // Clear buffer
    } else {
        broadcast_mode = 1;
    }
    
    printf("Enter your message: ");
    scanf("%[^\n]s", hello);
    sprintf(buffer, "%s[PORT:%d] says: %s", name, PORT, hello);
    
    if (broadcast_mode) {
        // Envoyer le message à tous les ports connus
        for (int i = 0; i < 20; i++) {
            if (port_used[i] != 0 && port_used[i] != PORT) {
                int PORT_server = port_used[i];
                socket_t sock = INVALID_SOCKET_TYPE;
                struct sockaddr_in serv_addr;
                
                if ((sock = socket(AF_INET, SOCK_STREAM, 0)) == INVALID_SOCKET_TYPE) {
                    printf("\nSocket creation error for port %d\n", PORT_server);
                    continue;
                }
                
                serv_addr.sin_family = AF_INET;
                if (inet_pton(AF_INET, global_ip_address, &serv_addr.sin_addr) <= 0) {
                    printf("\nInvalid IP address\n");
                    CLOSE_SOCKET(sock);
                    continue;
                }
                serv_addr.sin_port = htons(PORT_server);
                
                if (connect(sock, (struct sockaddr *)&serv_addr, sizeof(serv_addr)) == SOCKET_ERROR_TYPE) {
                    printf("\nConnection Failed to port %d\n", PORT_server);
                    CLOSE_SOCKET(sock);
                    continue;
                }
                
                if (send(sock, buffer, strlen(buffer), 0) > 0) {
                    printf("Message sent to port %d\n", PORT_server);
                    success_count++;
                } else {
                    printf("Failed to send message to port %d\n", PORT_server);
                }
                
                CLOSE_SOCKET(sock);
            }
        }
        
        if (success_count > 0) {
            printf("\nMessage sent to %d ports\n", success_count);
        } else {
            printf("\nNo messages were sent. No active ports found.\n");
        }
    } else {
        // Envoyer à une adresse IP et port spécifiques
        socket_t sock = INVALID_SOCKET_TYPE;
        struct sockaddr_in serv_addr;
        
        if ((sock = socket(AF_INET, SOCK_STREAM, 0)) == INVALID_SOCKET_TYPE) {
            printf("\nSocket creation error\n");
            return;
        }
        
        serv_addr.sin_family = AF_INET;
        if (inet_pton(AF_INET, target_ip, &serv_addr.sin_addr) <= 0) {
            printf("\nInvalid IP address\n");
            CLOSE_SOCKET(sock);
            return;
        }
        serv_addr.sin_port = htons(target_port);
        
        if (connect(sock, (struct sockaddr *)&serv_addr, sizeof(serv_addr)) == SOCKET_ERROR_TYPE) {
            printf("\nConnection Failed to %s:%d\n", target_ip, target_port);
            CLOSE_SOCKET(sock);
            return;
        }
        
        if (send(sock, buffer, strlen(buffer), 0) > 0) {
            printf("Message sent to %s:%d\n", target_ip, target_port);
            
            // Ajouter ce port à notre liste s'il n'y est pas déjà
            int already_exists = 0;
            for (int i = 0; i < 20; i++) {
                if (port_used[i] == target_port) {
                    already_exists = 1;
                    break;
                }
            }
            
            if (!already_exists) {
                for (int i = 0; i < 20; i++) {
                    if (port_used[i] == 0) {
                        port_used[i] = target_port;
                        printf("New port %d registered\n", target_port);
                        break;
                    }
                }
            }
        } else {
            printf("Failed to send message to %s:%d\n", target_ip, target_port);
        }
        
        CLOSE_SOCKET(sock);
    }
}