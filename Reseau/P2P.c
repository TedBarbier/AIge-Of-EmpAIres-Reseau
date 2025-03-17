#include <arpa/inet.h>
#include <netinet/in.h>
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <unistd.h>

char name[20];
int PORT;
int port_used[20];

void sending();
void receiving(int server_fd);
void *receive_thread(void *server_fd);
void announce_to_port(int target_port);
void discover_peers();

int main(int argc, char const *argv[]) {
  printf("Enter name:");
  scanf("%s", name);

  // Initialiser le tableau port_used
  for (int i = 0; i < 20; i++) {
    port_used[i] = 0;
  }

  PORT = choose_port();

  int server_fd, new_socket, valread;
  struct sockaddr_in address;
  int k = 0;

  // Creating socket file descriptor
  if ((server_fd = socket(AF_INET, SOCK_STREAM, 0)) == -1) {
    perror("socket failed");
    exit(EXIT_FAILURE);
  }
  // Forcefully attaching socket to the port

  address.sin_family = AF_INET;
  address.sin_addr.s_addr = INADDR_ANY;
  address.sin_port = htons(PORT);

  // Printed the server socket addr and port
  printf("IP address is: %s\n", inet_ntoa(address.sin_addr));
  printf("port is: %d\n", (int)ntohs(address.sin_port));

  if (bind(server_fd, (struct sockaddr *)&address, sizeof(address)) < 0) {
    perror("bind failed");
    exit(EXIT_FAILURE);
  }
  if (listen(server_fd, 5) < 0) {
    perror("listen");
    exit(EXIT_FAILURE);
  }
  int ch;
  pthread_t tid;
  pthread_create(
      &tid, NULL, &receive_thread,
      &server_fd); // Creating thread to keep receiving message in real time
  printf("\n*****At any point in time press the following:*****\n");
  printf("1. Send message\n");
  printf("2. Discover peers\n");
  printf("0. Quit\n");
  printf("\nEnter choice:");

  printf("Initializing peer-to-peer network...\n");
  discover_peers();  // Rechercher des pairs au démarrage

  do {

    scanf("%d", &ch);
    switch (ch) {
    case 1:
      sending();
      break;
    case 2:
      discover_peers();
      break;
    case 0:
      printf("\nLeaving\n");
      break;
    default:
      printf("\nWrong choice\n");
    }
  } while (ch);

  close(server_fd);

  return 0;
}

// Sending messages to all known ports
void sending() {
  char buffer[2000] = {0};
  char hello[1024] = {0};
  int success_count = 0;
  
  // Afficher les ports connus pour le débogage
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
  
  char dummy;
  printf("Enter your message: ");
  scanf("%c", &dummy); // Clear buffer
  scanf("%[^\n]s", hello);
  sprintf(buffer, "%s[PORT:%d] says: %s", name, PORT, hello);
  
  // Envoyer le message à tous les ports connus (sauf le nôtre)
  for (int i = 0; i < 20; i++) {
    if (port_used[i] != 0 && port_used[i] != PORT) {
      int PORT_server = port_used[i];
      int sock = 0;
      struct sockaddr_in serv_addr;
      
      if ((sock = socket(AF_INET, SOCK_STREAM, 0)) < 0) {
        printf("\nErreur création socket pour port %d\n", PORT_server);
        continue;
      }
      
      serv_addr.sin_family = AF_INET;
      serv_addr.sin_addr.s_addr = INADDR_ANY; // INADDR_ANY = 0.0.0.0 (localhost)
      serv_addr.sin_port = htons(PORT_server);
      
      if (connect(sock, (struct sockaddr *)&serv_addr, sizeof(serv_addr)) < 0) {
        printf("\nÉchec connexion au port %d\n", PORT_server);
        close(sock);
        continue;
      }
      
      send(sock, buffer, strlen(buffer), 0);
      printf("Message envoyé au port %d\n", PORT_server);
      success_count++;
      close(sock);
    }
  }
  
  if (success_count > 0) {
    printf("\nMessage envoyé à %d ports\n", success_count);
  } else {
    printf("\nAucun message envoyé. Aucun port connecté trouvé.\n");
  }
}

// Calling receiving every 2 seconds
void *receive_thread(void *server_fd) {
  int s_fd = *((int *)server_fd);
  while (1) {
    sleep(2);
    receiving(s_fd);
  }
}

// Receiving messages on our port
void receiving(int server_fd) {
  struct sockaddr_in address;
  int valread;
  char buffer[2000] = {0};
  int addrlen = sizeof(address);
  fd_set current_sockets, ready_sockets;

  // Initialize my current set
  FD_ZERO(&current_sockets);
  FD_SET(server_fd, &current_sockets);
  int k = 0;
  while (1) {
    k++;
    ready_sockets = current_sockets;

    if (select(FD_SETSIZE, &ready_sockets, NULL, NULL, NULL) < 0) {
      perror("Error");
      exit(EXIT_FAILURE);
    }

    for (int i = 0; i < FD_SETSIZE; i++) {
      if (FD_ISSET(i, &ready_sockets)) {

        if (i == server_fd) {
          int client_socket;

          if ((client_socket = accept(server_fd, (struct sockaddr *)&address,
                                      (socklen_t *)&addrlen)) < 0) {
            perror("accept");
            exit(EXIT_FAILURE);
          }
          FD_SET(client_socket, &current_sockets);
        } else {
          valread = recv(i, buffer, sizeof(buffer) - 1, 0);
          if (valread > 0) {
            buffer[valread] = '\0';  // Ajouter cette ligne pour garantir que la chaîne est bien terminée
            printf("\n%s\n", buffer);
            
            // Vérifier s'il s'agit d'un message d'annonce
            if (strncmp(buffer, "ANNOUNCE[PORT:", 14) == 0) {
              char *port_start = buffer + 14;
              char *port_end = strchr(port_start, ']');
              if (port_end != NULL) {
                *port_end = '\0';
                int sender_port = atoi(port_start);
                *port_end = ']';
                
                if (sender_port > 0 && sender_port != PORT) {
                  // Ajouter ce port à notre liste
                  int already_registered = 0;
                  for (int j = 0; j < 20; j++) {
                    if (port_used[j] == sender_port) {
                      already_registered = 1;
                      break;
                    }
                  }
                  
                  if (!already_registered) {
                    for (int j = 0; j < 20; j++) {
                      if (port_used[j] == 0) {
                        port_used[j] = sender_port;
                        printf("Nouveau pair découvert sur port %d\n", sender_port);
                        
                        // Répondre avec notre propre annonce
                        announce_to_port(sender_port);
                        break;
                      }
                    }
                  }
                }
              }
            } else {
              // Traitement normal des messages (comme avant)
              char *port_start = strstr(buffer, "[PORT:");
              if (port_start != NULL) {
                port_start += 6; // Sauter "[PORT:"
                char *port_end = strchr(port_start, ']');
                if (port_end != NULL) {
                  *port_end = '\0'; // Terminer temporairement la chaîne
                  int sender_port = atoi(port_start);
                  *port_end = ']'; // Remettre le caractère d'origine
                  
                  // Ajouter ce port à notre liste s'il n'y est pas déjà
                  if (sender_port > 0 && sender_port != PORT) {
                    int already_registered = 0;
                    for (int j = 0; j < 20; j++) {
                      if (port_used[j] == sender_port) {
                        already_registered = 1;
                        break;
                      }
                    }
                    
                    if (!already_registered) {
                      for (int j = 0; j < 20; j++) {
                        if (port_used[j] == 0) {
                          port_used[j] = sender_port;
                          printf("Nouveau port enregistré: %d\n", sender_port);
                          break;
                        }
                      }
                    }
                  }
                }
              }
            }
          }
          FD_CLR(i, &current_sockets);
          close(i);
        }
      }
    }

    if (k == (FD_SETSIZE * 2))
      break;
  }
}

// Choose an available port by actually testing if it can be bound
int choose_port() {
  int port = 8000; // Starting port number
  
  for (int attempt = 0; attempt < 1000; attempt++) {
    // Try to create a socket and bind to the port
    int sock = socket(AF_INET, SOCK_STREAM, 0);
    if (sock < 0) {
      perror("Socket creation failed");
      return -1;
    }
    
    // Set socket option to reuse address
    int opt = 1;
    if (setsockopt(sock, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt)) < 0) {
      close(sock);
      port++;
      continue;
    }
    
    struct sockaddr_in addr;
    memset(&addr, 0, sizeof(addr));
    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = INADDR_ANY;
    addr.sin_port = htons(port);
    
    // Try to bind to the port
    if (bind(sock, (struct sockaddr *)&addr, sizeof(addr)) == 0) {
      close(sock); // Close the socket, we'll reopen it properly later
      
      // Store the port in the port_used array
      for (int i = 0; i < 20; i++) {
        if (port_used[i] == 0) {
          port_used[i] = port;
          break;
        }
      }
      
      printf("Successfully found available port: %d\n", port);
      return port;
    }
    
    // If we couldn't bind, try the next port
    close(sock);
    port++;
  }
  
  printf("Could not find an available port after 1000 attempts\n");
  return -1; // No available ports found
}

// Fonction pour annoncer notre présence à un autre port
void announce_to_port(int target_port) {
  int sock = 0;
  struct sockaddr_in serv_addr;
  char announcement[100] = {0};
  
  if ((sock = socket(AF_INET, SOCK_STREAM, 0)) < 0) {
    return; // Échec silencieux
  }
  
  serv_addr.sin_family = AF_INET;
  serv_addr.sin_addr.s_addr = INADDR_ANY;
  serv_addr.sin_port = htons(target_port);
  
  if (connect(sock, (struct sockaddr *)&serv_addr, sizeof(serv_addr)) < 0) {
    close(sock);
    return; // Échec silencieux
  }
  
  // Envoyer un message d'annonce avec notre port
  sprintf(announcement, "ANNOUNCE[PORT:%d]", PORT);
  send(sock, announcement, strlen(announcement), 0);
  close(sock);
  printf("Annonce envoyée au port %d\n", target_port);
}

// Fonction pour annoncer notre présence à une plage de ports
void discover_peers() {
  printf("Recherche de pairs...\n");
  
  // Parcourir une plage de ports pour trouver d'autres instances
  for (int port = 8000; port < 8050; port++) {
    if (port != PORT) {
      announce_to_port(port);
    }
  }
  
  printf("Recherche terminée.\n");
}

