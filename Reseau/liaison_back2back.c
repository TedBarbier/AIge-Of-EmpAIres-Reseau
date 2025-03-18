#ifdef _WIN32
    #define _WIN32_WINNT 0x0600
    #include <winsock2.h>
    #include <ws2tcpip.h>
    typedef SOCKET socket_t;
    #define SOCKET_ERROR_TYPE SOCKET_ERROR
    #define INVALID_SOCKET_TYPE INVALID_SOCKET
    #define CLOSE_SOCKET(s) closesocket(s)
    #define SET_NONBLOCKING(sock) { u_long mode = 1; ioctlsocket(sock, FIONBIO, &mode); }
    #define SLEEP(ms) Sleep(ms)
    #define INET_NTOP(af, src, dst, size) inet_ntop(af, (void*)src, dst, size)
#else
    #include <unistd.h>
    #include <sys/socket.h>
    #include <netinet/in.h>
    #include <arpa/inet.h>
    #include <fcntl.h>
    typedef int socket_t;
    #define SOCKET_ERROR_TYPE -1
    #define INVALID_SOCKET_TYPE -1
    #define CLOSE_SOCKET(s) close(s)
    #define SET_NONBLOCKING(sock) fcntl(sock, F_SETFL, O_NONBLOCK)
    #define SLEEP(ms) usleep(ms * 1000)
    #define INET_NTOP(af, src, dst, size) inet_ntop(af, src, dst, size)
#endif

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define PYTHON_PORT 12345
#define P2P_PORT 8000
#define BUFFER_SIZE 2000
#define SLEEP_TIME 1

// Structure pour stocker les informations des clients connectés
typedef struct {
    struct sockaddr_in addr;
    int active;
    char ip[INET_ADDRSTRLEN];
} client_info;

#define MAX_CLIENTS 10
client_info clients[MAX_CLIENTS];
int num_clients = 0;

// Fonction pour recevoir les messages du pair
void receive_from_peer(socket_t peer_sock) {
    struct sockaddr_in addr;
    socklen_t addr_len = sizeof(addr);
    char buffer[BUFFER_SIZE] = {0};

    int n = recvfrom(peer_sock, buffer, sizeof(buffer) - 1, 0,
                     (struct sockaddr *)&addr, &addr_len);
    
    if (n > 0) {
        buffer[n] = '\0';
        char ip_str[INET_ADDRSTRLEN];
        INET_NTOP(AF_INET, &(addr.sin_addr), ip_str, INET_ADDRSTRLEN);
        printf("Received from peer %s: %s\n", ip_str, buffer);
        
        // Vérifier si c'est un nouveau client
        int client_found = 0;
        for (int i = 0; i < num_clients; i++) {
            if (clients[i].addr.sin_addr.s_addr == addr.sin_addr.s_addr) {
                client_found = 1;
                clients[i].active = 1;
                break;
            }
        }
        
        // Ajouter le nouveau client
        if (!client_found && num_clients < MAX_CLIENTS) {
            clients[num_clients].addr = addr;
            clients[num_clients].active = 1;
            INET_NTOP(AF_INET, &(addr.sin_addr), clients[num_clients].ip, INET_ADDRSTRLEN);
            printf("New client connected: %s\n", clients[num_clients].ip);
            num_clients++;
        }
    }
}

void forward_to_peer(const char *data, const char *target_ip) {
    socket_t sock;
    struct sockaddr_in serv_addr;
    
    if ((sock = socket(AF_INET, SOCK_DGRAM, 0)) == INVALID_SOCKET_TYPE) {
        printf("\nSocket creation error\n");
        return;
    }

    serv_addr.sin_family = AF_INET;
    serv_addr.sin_port = htons(P2P_PORT);
    serv_addr.sin_addr.s_addr = inet_addr(target_ip);
    
    if (serv_addr.sin_addr.s_addr == INADDR_NONE) {
        printf("\nInvalid address/ Address not supported\n");
        CLOSE_SOCKET(sock);
        return;
    }

    sendto(sock, data, strlen(data), 0, (const struct sockaddr *)&serv_addr,
           sizeof(serv_addr));
    printf("Data forwarded to peer at %s\n", target_ip);
    CLOSE_SOCKET(sock);
}

// Fonction pour envoyer un message à tous les clients connectés
void broadcast_to_peers(const char *data) {
    for (int i = 0; i < num_clients; i++) {
        if (clients[i].active) {
            forward_to_peer(data, clients[i].ip);
        }
    }
}

// Mode serveur pour écouter les connexions Python
void run_python_server(socket_t python_sock) {
    struct sockaddr_in client_addr;
    socklen_t client_addr_len = sizeof(client_addr);
    char buffer[BUFFER_SIZE] = {0};
    
    int recv_len = recvfrom(python_sock, buffer, BUFFER_SIZE - 1, 0, 
                           (struct sockaddr *)&client_addr, &client_addr_len);
    
    if (recv_len > 0) {
        buffer[recv_len] = '\0';
        char ip_str[INET_ADDRSTRLEN];
        INET_NTOP(AF_INET, &(client_addr.sin_addr), ip_str, INET_ADDRSTRLEN);
        printf("Message from Python client %s: \"%s\"\n", ip_str, buffer);
        
        char expected_message[] = "Rejoindre la partie";
        if (strcmp(buffer, expected_message) == 0) {
            printf("Message verified successfully!\n");
            // On pourrait envoyer une confirmation ici
            const char *confirm = "Connection accepted";
            sendto(python_sock, confirm, strlen(confirm), 0, 
                  (struct sockaddr *)&client_addr, client_addr_len);
        }
        
        // Transférer le message à tous les pairs connectés
        broadcast_to_peers(buffer);
    }
}

// Mode client pour envoyer des messages à Python
void send_to_python(const char *message, const char *server_ip) {
    socket_t client_socket;
    struct sockaddr_in server_addr;

    if ((client_socket = socket(AF_INET, SOCK_DGRAM, 0)) == INVALID_SOCKET_TYPE) {
        printf("Python client socket creation failed\n");
        return;
    }

    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(PYTHON_PORT);
    server_addr.sin_addr.s_addr = inet_addr(server_ip);
    
    if (server_addr.sin_addr.s_addr == INADDR_NONE) {
        printf("Invalid Python server address\n");
        CLOSE_SOCKET(client_socket);
        return;
    }

    if (sendto(client_socket, message, strlen(message), 0, 
              (struct sockaddr *)&server_addr, sizeof(server_addr)) == SOCKET_ERROR_TYPE) {
        printf("Failed to send message to Python server\n");
        CLOSE_SOCKET(client_socket);
        return;
    }

    printf("Message sent to Python server: \"%s\"\n", message);
    CLOSE_SOCKET(client_socket);
}

void print_usage(char const *program_name) {
    printf("Usage: %s <mode> [options]\n", program_name);
    printf("Modes:\n");
    printf("  bridge <target_ip>    - Act as a bridge between Python and P2P network\n");
    printf("  server                - Run as a UDP server waiting for Python client connections\n");
    printf("  client <server_ip>    - Run as a UDP client to send messages to a Python server\n");
}

int main(int argc, char const *argv[]) {
    #ifdef _WIN32
        WSADATA wsa;
        if (WSAStartup(MAKEWORD(2,2), &wsa) != 0) {
            printf("WSAStartup failed\n");
            return 1;
        }
    #endif

    if (argc < 2) {
        print_usage(argv[0]);
        return 1;
    }

    // Initialiser le tableau des clients
    for (int i = 0; i < MAX_CLIENTS; i++) {
        clients[i].active = 0;
    }

    // Mode bridge - fonctionnalité originale de liaison_back2back.c
    if (strcmp(argv[1], "bridge") == 0) {
        if (argc != 3) {
            printf("Usage: %s bridge <target_ip>\n", argv[0]);
            return 1;
        }

        const char *target_ip = argv[2];
        socket_t python_sock, peer_sock;
        struct sockaddr_in python_addr, peer_addr, client_addr;
        socklen_t addr_len = sizeof(client_addr);
        char buffer[BUFFER_SIZE];

        // Socket pour Python
        if ((python_sock = socket(AF_INET, SOCK_DGRAM, 0)) == INVALID_SOCKET_TYPE) {
            perror("Python socket creation failed");
            return 1;
        }
        SET_NONBLOCKING(python_sock);

        // Socket pour P2P
        if ((peer_sock = socket(AF_INET, SOCK_DGRAM, 0)) == INVALID_SOCKET_TYPE) {
            perror("Peer socket creation failed");
            return 1;
        }
        SET_NONBLOCKING(peer_sock);

        // Configuration du socket Python
        memset(&python_addr, 0, sizeof(python_addr));
        python_addr.sin_family = AF_INET;
        python_addr.sin_addr.s_addr = INADDR_ANY;
        python_addr.sin_port = htons(PYTHON_PORT);

        // Configuration du socket P2P
        memset(&peer_addr, 0, sizeof(peer_addr));
        peer_addr.sin_family = AF_INET;
        peer_addr.sin_addr.s_addr = INADDR_ANY;
        peer_addr.sin_port = htons(P2P_PORT);

        if (bind(python_sock, (struct sockaddr *)&python_addr, sizeof(python_addr)) < 0) {
            perror("Python socket bind failed");
            return 1;
        }

        if (bind(peer_sock, (struct sockaddr *)&peer_addr, sizeof(peer_addr)) < 0) {
            perror("Peer socket bind failed");
            return 1;
        }

        printf("Bridge mode activated\n");
        printf("Listening on ports - Python: %d, P2P: %d\n", PYTHON_PORT, P2P_PORT);
        printf("Will forward to %s:%d\n", target_ip, P2P_PORT);

        while (1) {
            // Vérifier les messages de Python
            int n = recvfrom(python_sock, buffer, BUFFER_SIZE-1, 0,
                            (struct sockaddr *)&client_addr, &addr_len);
            if (n > 0) {
                buffer[n] = '\0';
                printf("Received from Python: %s\n", buffer);
                forward_to_peer(buffer, target_ip);
            }

            // Vérifier les messages des pairs
            receive_from_peer(peer_sock);

            SLEEP(SLEEP_TIME);
        }

        CLOSE_SOCKET(python_sock);
        CLOSE_SOCKET(peer_sock);
    } 
    // Mode serveur - fonctionnalité de c_to_python.c (mode serveur)
    else if (strcmp(argv[1], "server") == 0) {
        printf("Starting UDP server mode...\n");
        socket_t server_socket;
        struct sockaddr_in server_addr;

        if ((server_socket = socket(AF_INET, SOCK_DGRAM, 0)) == INVALID_SOCKET_TYPE) {
            perror("Server socket creation failed");
            #ifdef _WIN32
                WSACleanup();
            #endif
            return 1;
        }
        SET_NONBLOCKING(server_socket);

        memset(&server_addr, 0, sizeof(server_addr));
        server_addr.sin_family = AF_INET;
        server_addr.sin_addr.s_addr = INADDR_ANY;
        server_addr.sin_port = htons(PYTHON_PORT);

        if (bind(server_socket, (struct sockaddr *)&server_addr, sizeof(server_addr)) < 0) {
            perror("Server socket bind failed");
            CLOSE_SOCKET(server_socket);
            #ifdef _WIN32
                WSACleanup();
            #endif
            return 1;
        }

        printf("UDP server listening on port %d...\n", PYTHON_PORT);

        while (1) {
            run_python_server(server_socket);
            SLEEP(SLEEP_TIME);
        }

        CLOSE_SOCKET(server_socket);
    } 
    // Mode client - fonctionnalité de c_to_python.c (mode client)
    else if (strcmp(argv[1], "client") == 0) {
        if (argc != 3) {
            printf("Usage: %s client <server_ip>\n", argv[0]);
            return 1;
        }

        const char *server_ip = argv[2];
        printf("Starting UDP client mode...\n");
        
        // Par défaut, envoyer un message de connexion
        char message[] = "Rejoindre la partie";
        send_to_python(message, server_ip);
        
        printf("You can now send messages to the Python server.\n");
        printf("Type your message and press Enter (or 'exit' to quit):\n");
        
        char input[BUFFER_SIZE];
        while (1) {
            fgets(input, BUFFER_SIZE, stdin);
            input[strcspn(input, "\n")] = '\0';
            
            if (strcmp(input, "exit") == 0) {
                break;
            }
            
            send_to_python(input, server_ip);
        }
    } 
    else {
        print_usage(argv[0]);
    }

    #ifdef _WIN32
        WSACleanup();
    #endif
    return 0;
}