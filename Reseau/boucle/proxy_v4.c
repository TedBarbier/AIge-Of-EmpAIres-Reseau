#include <errno.h>
#include <fcntl.h>
// #include <netdb.h> // Include this header for getnameinfo and NI_NUMERICHOST - No longer needed, functionality in ws2tcpip.h on Windows
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifdef _WIN32
#include <winsock2.h>
#include <ws2tcpip.h>
#include <iphlpapi.h> // Required for GetAdaptersAddresses
#pragma comment(lib, "Ws2_32.lib")
#pragma comment(lib, "Iphlpapi.lib") // Link with Iphlpapi.lib
#else
#include <arpa/inet.h>
#include <ifaddrs.h>
#include <netinet/in.h>
#include <sys/select.h>
#include <unistd.h>
#endif

#define PORT_12345 12345
#define PORT_1234 1234
#define MULTICAST_PORT 8000
#define BUFFER_SIZE 1024
#define MULTICAST_IP "239.255.255.250"

void set_nonblocking(int socket) {
#ifdef _WIN32
  u_long mode = 1;
  ioctlsocket(socket, FIONBIO, &mode);
#else
  int flags = fcntl(socket, F_GETFL, 0);
  fcntl(socket, F_SETFL, flags | O_NONBLOCK);
#endif
}

void join_multicast_group(int socket, const char *multicast_ip,
                          const char *interface_ip) {
  struct ip_mreq mreq;
  mreq.imr_multiaddr.s_addr = inet_addr(multicast_ip);
  mreq.imr_interface.s_addr = inet_addr(interface_ip);
  if (setsockopt(socket, IPPROTO_IP, IP_ADD_MEMBERSHIP,
#ifdef _WIN32
                 (const char *)&mreq,
#else
                 &mreq,
#endif
                 sizeof(mreq)) < 0) {
    perror("setsockopt IP_ADD_MEMBERSHIP");
    exit(EXIT_FAILURE);
  }
}

void set_multicast_interface(int socket, const char *interface_ip) {
  struct in_addr interface_addr;
  interface_addr.s_addr = inet_addr(interface_ip);
  if (setsockopt(socket, IPPROTO_IP, IP_MULTICAST_IF,
#ifdef _WIN32
                 (const char *)&interface_addr,
#else
                 &interface_addr,
#endif
                 sizeof(interface_addr)) < 0) {
    perror("setsockopt IP_MULTICAST_IF");
    exit(EXIT_FAILURE);
  }
}

void get_local_ip(char *local_ip) {
  int sock;
  struct sockaddr_in serv_addr, local_addr;
  socklen_t addrlen = sizeof(local_addr);

  if ((sock = socket(AF_INET, SOCK_DGRAM, 0)) < 0) {
    perror("socket");
    exit(EXIT_FAILURE);
  }

  memset(&serv_addr, 0, sizeof(serv_addr));
  serv_addr.sin_family = AF_INET;
  serv_addr.sin_addr.s_addr = inet_addr("8.8.8.8"); // Google DNS
  serv_addr.sin_port = htons(53);

  if (connect(sock, (struct sockaddr *)&serv_addr, sizeof(serv_addr)) < 0) {
    perror("connect");
    close(sock);
    exit(EXIT_FAILURE);
  }

  getsockname(sock, (struct sockaddr *)&local_addr, &addrlen);
  inet_ntop(AF_INET, &(local_addr.sin_addr), local_ip, INET_ADDRSTRLEN);

  close(sock);
}

int main(int argc, char *argv[]) {
#ifdef _WIN32
  WSADATA wsaData;
  if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0) {
    fprintf(stderr, "WSAStartup failed.\n");
    return 1;
  }
#endif

  int socket_fd_12345, socket_fd_multicast;
  struct sockaddr_in address_12345, multicast_addr, client_address;
  socklen_t addrlen = sizeof(address_12345);

  // Create socket for port 12345
  if ((socket_fd_12345 = socket(AF_INET, SOCK_DGRAM, 0)) < 0) {
    perror("socket failed");
#ifdef _WIN32
    WSACleanup();
#endif
    exit(EXIT_FAILURE);
  }

  set_nonblocking(socket_fd_12345);

  address_12345.sin_family = AF_INET;
  address_12345.sin_addr.s_addr = INADDR_ANY;
  address_12345.sin_port = htons(PORT_12345);

  if (bind(socket_fd_12345, (struct sockaddr *)&address_12345,
           sizeof(address_12345)) < 0) {
    perror("bind failed");
    close(socket_fd_12345);
#ifdef _WIN32
    WSACleanup();
#endif
    exit(EXIT_FAILURE);
  }

  printf("Proxy listening on port 12345\n");

  // Create socket for multicast
  if ((socket_fd_multicast = socket(AF_INET, SOCK_DGRAM, 0)) < 0) {
    perror("socket failed");
    close(socket_fd_12345);
#ifdef _WIN32
    WSACleanup();
#endif
    exit(EXIT_FAILURE);
  }

  set_nonblocking(socket_fd_multicast);

  // Allow the socket to be reused
  int reuse = 1;
  if (setsockopt(socket_fd_multicast, SOL_SOCKET, SO_REUSEADDR,
#ifdef _WIN32
                 (const char *)&reuse,
#else
                 &reuse,
#endif
                 sizeof(reuse)) < 0) {
    perror("setsockopt SO_REUSEADDR");
    close(socket_fd_12345);
    close(socket_fd_multicast);
#ifdef _WIN32
    WSACleanup();
#endif
    exit(EXIT_FAILURE);
  }

  // Bind the socket to the multicast port
  memset(&multicast_addr, 0, sizeof(multicast_addr));
  multicast_addr.sin_family = AF_INET;
  multicast_addr.sin_addr.s_addr = htonl(INADDR_ANY);
  multicast_addr.sin_port = htons(MULTICAST_PORT);

  if (bind(socket_fd_multicast, (struct sockaddr *)&multicast_addr,
           sizeof(multicast_addr)) < 0) {
    perror("bind failed");
    close(socket_fd_12345);
    close(socket_fd_multicast);
#ifdef _WIN32
    WSACleanup();
#endif
    exit(EXIT_FAILURE);
  }

  // Join the multicast group on all interfaces
#ifndef _WIN32
  struct ifaddrs *ifaddr, *ifa;
  if (getifaddrs(&ifaddr) == -1) {
    perror("getifaddrs");
    exit(EXIT_FAILURE);
  }

  for (ifa = ifaddr; ifa != NULL; ifa = ifa->ifa_next) {
    if (ifa->ifa_addr == NULL)
      continue;
    if (ifa->ifa_addr->sa_family == AF_INET) {
      char interface_ip[INET_ADDRSTRLEN];
      getnameinfo(ifa->ifa_addr, sizeof(struct sockaddr_in), interface_ip,
                  INET_ADDRSTRLEN, NULL, 0, NI_NUMERICHOST);
      join_multicast_group(socket_fd_multicast, MULTICAST_IP, interface_ip);
      printf("Joined multicast group on interface: %s\n", interface_ip);
    }
  }

  freeifaddrs(ifaddr);
#else
  // Windows implementation to join multicast group on all interfaces
  PIP_ADAPTER_ADDRESSES pAddresses = NULL, pCurrentAddress = NULL;
  ULONG flags = GAA_FLAG_INCLUDE_PREFIX;
  ULONG family = AF_INET; // IPv4 addresses
  ULONG outBufLen = 0;
  DWORD dwRet = 0;

  // Make an initial call to GetAdaptersAddresses to get the necessary size into outBufLen
  dwRet = GetAdaptersAddresses(family, flags, NULL, pAddresses, &outBufLen);
  if (dwRet == ERROR_BUFFER_OVERFLOW) {
    pAddresses = (PIP_ADAPTER_ADDRESSES)malloc(outBufLen);
    if (pAddresses == NULL) {
      perror("malloc for GetAdaptersAddresses failed");
      exit(EXIT_FAILURE);
    }
    dwRet = GetAdaptersAddresses(family, flags, NULL, pAddresses, &outBufLen);
  }

  if (dwRet == NO_ERROR) {
    pCurrentAddress = pAddresses;
    while (pCurrentAddress) {
      if (pCurrentAddress->OperStatus == IfOperStatusUp &&
          pCurrentAddress->FirstUnicastAddress != NULL &&
          pCurrentAddress->FirstUnicastAddress->Address.lpSockaddr->sa_family == AF_INET) {
        SOCKADDR_IN *pIPv4Addr = (SOCKADDR_IN *)pCurrentAddress->FirstUnicastAddress->Address.lpSockaddr;
        char interface_ip_str[INET_ADDRSTRLEN];
        inet_ntop(AF_INET, &(pIPv4Addr->sin_addr), interface_ip_str, INET_ADDRSTRLEN);
        join_multicast_group(socket_fd_multicast, MULTICAST_IP, interface_ip_str);
        printf("Joined multicast group on interface: %s\n", interface_ip_str);
      }
      pCurrentAddress = pCurrentAddress->Next;
    }
  } else {
    fprintf(stderr, "GetAdaptersAddresses failed with error: %ld\n", dwRet);
    free(pAddresses);
    exit(EXIT_FAILURE);
  }

  if (pAddresses) {
    free(pAddresses);
  }
#endif

  printf("Listening for multicast messages on %s:%d\n", MULTICAST_IP,
         MULTICAST_PORT);

  fd_set readfds;
  struct timeval timeout;
  timeout.tv_sec = 1;
  timeout.tv_usec = 0;

  // Get the local machine's IP address
  char local_ip[INET_ADDRSTRLEN];
  get_local_ip(local_ip);

  // Print the local IP address
  printf("Local IP address: %s\n", local_ip);

  while (1) {
    FD_ZERO(&readfds);
    FD_SET(socket_fd_12345, &readfds);
    FD_SET(socket_fd_multicast, &readfds);

    int activity = select(FD_SETSIZE, &readfds, NULL, NULL, &timeout);

    if ((activity < 0) && (errno != EINTR)) {
      perror("select error");
      break;
    }

    if (FD_ISSET(socket_fd_12345, &readfds)) {
      char buffer[BUFFER_SIZE];
      int bytes_received =
          recvfrom(socket_fd_12345, buffer, BUFFER_SIZE, 0,
                   (struct sockaddr *)&client_address, &addrlen);
      if (bytes_received > 0) {
        buffer[bytes_received] = '\0'; // Null-terminate the received data
        printf("Received message from Python: %s\n", buffer);
        printf("Forward it to multicast group: %s\n", MULTICAST_IP);

        // Send to multicast group on all interfaces
#ifndef _WIN32
        struct ifaddrs *ifaddr_send, *ifa_send;
        if (getifaddrs(&ifaddr_send) == -1) {
          perror("getifaddrs in send loop");
          continue; // Or handle error more robustly
        }
        for (ifa_send = ifaddr_send; ifa_send != NULL; ifa_send = ifa_send->ifa_next) {
          if (ifa_send->ifa_addr == NULL)
            continue;
          if (ifa_send->ifa_addr->sa_family == AF_INET) {
            char interface_ip[INET_ADDRSTRLEN];
            getnameinfo(ifa_send->ifa_addr, sizeof(struct sockaddr_in), interface_ip,
                        INET_ADDRSTRLEN, NULL, 0, NI_NUMERICHOST);
            set_multicast_interface(socket_fd_multicast, interface_ip);
            struct sockaddr_in multicast_send_addr;
            multicast_send_addr.sin_family = AF_INET;
            multicast_send_addr.sin_addr.s_addr = inet_addr(MULTICAST_IP);
            multicast_send_addr.sin_port = htons(MULTICAST_PORT);
            sendto(socket_fd_multicast, buffer, bytes_received, 0,
                   (struct sockaddr *)&multicast_send_addr,
                   sizeof(multicast_send_addr));
          }
        }
        freeifaddrs(ifaddr_send);

#else
        // Windows implementation to send multicast on all interfaces
        PIP_ADAPTER_ADDRESSES pAddressesSend = NULL, pCurrentAddressSend = NULL;
        ULONG flagsSend = GAA_FLAG_INCLUDE_PREFIX;
        ULONG familySend = AF_INET;
        ULONG outBufLenSend = 0;
        DWORD dwRetSend = 0;

        dwRetSend = GetAdaptersAddresses(familySend, flagsSend, NULL, pAddressesSend, &outBufLenSend);
        if (dwRetSend == ERROR_BUFFER_OVERFLOW) {
          pAddressesSend = (PIP_ADAPTER_ADDRESSES)malloc(outBufLenSend);
          if (!pAddressesSend) {
            perror("malloc for GetAdaptersAddresses (send) failed");
            continue; // Non-fatal error in send loop, try next select loop.
          }
          dwRetSend = GetAdaptersAddresses(familySend, flagsSend, NULL, pAddressesSend, &outBufLenSend);
        }

        if (dwRetSend == NO_ERROR) {
          pCurrentAddressSend = pAddressesSend;
          while (pCurrentAddressSend) {
            if (pCurrentAddressSend->OperStatus == IfOperStatusUp &&
                pCurrentAddressSend->FirstUnicastAddress != NULL &&
                pCurrentAddressSend->FirstUnicastAddress->Address.lpSockaddr->sa_family == AF_INET) {
              SOCKADDR_IN *pIPv4Addr = (SOCKADDR_IN *)pCurrentAddressSend->FirstUnicastAddress->Address.lpSockaddr;
              char interface_ip_str[INET_ADDRSTRLEN];
              inet_ntop(AF_INET, &(pIPv4Addr->sin_addr), interface_ip_str, INET_ADDRSTRLEN);
              set_multicast_interface(socket_fd_multicast, interface_ip_str);
              struct sockaddr_in multicast_send_addr;
              multicast_send_addr.sin_family = AF_INET;
              multicast_send_addr.sin_addr.s_addr = inet_addr(MULTICAST_IP);
              multicast_send_addr.sin_port = htons(MULTICAST_PORT);
              sendto(socket_fd_multicast, buffer, bytes_received, 0,
                     (struct sockaddr *)&multicast_send_addr,
                     sizeof(multicast_send_addr));
            }
            pCurrentAddressSend = pCurrentAddressSend->Next;
          }
        } else {
          fprintf(stderr, "GetAdaptersAddresses (send) failed with error: %ld\n", dwRetSend);
        }
        if (pAddressesSend) {
          free(pAddressesSend);
        }
#endif
      }
    }

    if (FD_ISSET(socket_fd_multicast, &readfds)) {
      char buffer[BUFFER_SIZE];
      int bytes_received =
          recvfrom(socket_fd_multicast, buffer, BUFFER_SIZE, 0,
                   (struct sockaddr *)&client_address, &addrlen);
      if (bytes_received > 0) {
        buffer[bytes_received] = '\0'; // Null-terminate the received data
        printf("Received message from multicast group: %s\n", buffer);

        // Check if the message is from the local machine
        char sender_ip[INET_ADDRSTRLEN];
        inet_ntop(AF_INET, &(client_address.sin_addr), sender_ip,
                  INET_ADDRSTRLEN);
        if (strcmp(sender_ip, local_ip) != 0) {
          printf("Forward it to Python server on localhost\n");

          // Forward to Python server on localhost:1234
          struct sockaddr_in local_address;
          local_address.sin_family = AF_INET;
          local_address.sin_addr.s_addr = inet_addr("127.0.0.1");
          local_address.sin_port = htons(PORT_1234);
          sendto(socket_fd_multicast, buffer, bytes_received, 0,
                 (struct sockaddr *)&local_address, sizeof(local_address));
        } else {
          printf("Message from self; ignoring.\n");
        }
      }
    }
  }

  close(socket_fd_12345);
  close(socket_fd_multicast);

#ifdef _WIN32
  WSACleanup();
#endif

  return 0;
}