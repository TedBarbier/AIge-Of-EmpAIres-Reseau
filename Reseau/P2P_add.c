#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <arpa/inet.h>

// Variable globale pour stocker l'adresse IP
char *global_ip_address;

// Modification de la fonction main pour traiter l'argument d'adresse IP
int main(int argc, char const *argv[]) {
    printf("Enter name: ");
    scanf("%s", name);

    // Vérifier si une adresse IP a été fournie en argument
    if (argc > 1) {
        global_ip_address = argv[1];
        printf("Using IP address: %s\n", global_ip_address);
    } else {
        global_ip_address = "127.0.0.1";
        printf("No IP address provided, using default: %s\n", global_ip_address);
    }

    // Trouver un port disponible pour le serveur
    PORT = find_available_port();
    if (PORT == -1) {
        printf("No available ports\n");
        exit(EXIT_FAILURE);
    }

    int server_fd;
    struct sockaddr_in address;

    // Creating socket file descriptor
    if ((server_fd = socket(AF_INET, SOCK_STREAM, 0)) == -1) {
        perror("socket failed");
        exit(EXIT_FAILURE);
    }

    // Forcefully attaching socket to the port
    address.sin_family = AF_INET;
    // Au lieu de INADDR_ANY, utiliser l'adresse IP fournie
    if (inet_pton(AF_INET, global_ip_address, &address.sin_addr) <= 0) {
        perror("Invalid IP address");
        exit(EXIT_FAILURE);
    }
    address.sin_port = htons(PORT);

    printf("IP address is: %s\n", global_ip_address);
    printf("Port is: %d\n", PORT);

    // Reste du code inchangé...
}

// Dans sending(), remplacez INADDR_ANY par l'adresse IP spécifiée
void sending() {
    // ... code existant ...
    
    for (int i = 0; i < 20; i++) {
        if (port_used[i] != 0 && port_used[i] != PORT) {
            int PORT_server = port_used[i];
            int sock = 0;
            struct sockaddr_in serv_addr;
            
            if ((sock = socket(AF_INET, SOCK_STREAM, 0)) < 0) {
                printf("\nSocket creation error for port %d\n", PORT_server);
                continue;
            }
            
            serv_addr.sin_family = AF_INET;
            // Au lieu de INADDR_ANY
            if (inet_pton(AF_INET, global_ip_address, &serv_addr.sin_addr) <= 0) {
                printf("\nInvalid IP address\n");
                close(sock);
                continue;
            }
            serv_addr.sin_port = htons(PORT_server);
            
            // Reste du code inchangé...
        }
    }
    
    // ... reste du code ...
} 