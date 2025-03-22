#include "tls_utils.h"

#ifdef _WIN32
    #include <winsock2.h>
    #include <ws2tcpip.h>
    #include <iphlpapi.h>
    #include <windows.h>
    #pragma comment(lib, "ws2_32.lib")
    #pragma comment(lib, "iphlpapi.lib")
    #define SOCKET_ERROR_VAL SOCKET_ERROR
    #define INVALID_SOCK INVALID_SOCKET
    #define CLOSE_SOCKET closesocket
    typedef SOCKET sock_t;
    typedef int socklen_t;
#else
    #include <arpa/inet.h>
    #include <sys/socket.h>
    #include <sys/types.h>
    #include <netinet/in.h>
    #include <netdb.h>
    #include <ifaddrs.h>
    #include <unistd.h>
    #include <fcntl.h>
    #define SOCKET_ERROR_VAL -1
    #define INVALID_SOCK -1
    #define CLOSE_SOCKET close
    typedef int sock_t;
#endif

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define PORT_12345 12345
#define PORT_1234 1234
#define MULTICAST_PORT 8000
#define BUFFER_SIZE 1024
#define MULTICAST_IP "239.255.255.250"

#ifdef _WIN32
void set_nonblocking(sock_t socket) {
    u_long mode = 1;
    if (ioctlsocket(socket, FIONBIO, &mode) == SOCKET_ERROR) {
        perror("ioctlsocket");
        exit(EXIT_FAILURE);
    }
}
#else
void set_nonblocking(sock_t socket) {
    int flags = fcntl(socket, F_GETFL, 0);
    fcntl(socket, F_SETFL, flags | O_NONBLOCK);
}
#endif

#ifdef _WIN32
void list_interfaces(char *selected_interface_ip, int selected_interface) {
    PIP_ADAPTER_INFO AdapterInfo;
    DWORD dwBufLen = sizeof(IP_ADAPTER_INFO);
    AdapterInfo = (IP_ADAPTER_INFO *)malloc(sizeof(IP_ADAPTER_INFO));
    
    if (GetAdaptersInfo(AdapterInfo, &dwBufLen) == ERROR_BUFFER_OVERFLOW) {
        free(AdapterInfo);
        AdapterInfo = (IP_ADAPTER_INFO *)malloc(dwBufLen);
    }
    
    if (GetAdaptersInfo(AdapterInfo, &dwBufLen) == NO_ERROR) {
        PIP_ADAPTER_INFO pAdapterInfo = AdapterInfo;
        int index = 1;
        
        while (pAdapterInfo) {
            if (pAdapterInfo->IpAddressList.IpAddress.String[0] != '0' && 
                strcmp(pAdapterInfo->IpAddressList.IpAddress.String, "0.0.0.0") != 0) {
                printf("%d: %s (%s)\n", index, pAdapterInfo->Description,
                       pAdapterInfo->IpAddressList.IpAddress.String);
                if (index == selected_interface) {
                    strcpy(selected_interface_ip, pAdapterInfo->IpAddressList.IpAddress.String);
                }
                index++;
            }
            pAdapterInfo = pAdapterInfo->Next;
        }
    }
    free(AdapterInfo);
}
#else
void list_interfaces(char *selected_interface_ip, int selected_interface) {
    struct ifaddrs *ifaddr, *ifa;
    if (getifaddrs(&ifaddr) == -1) {
        perror("getifaddrs");
        exit(EXIT_FAILURE);
    }

    int index = 1;
    for (ifa = ifaddr; ifa != NULL; ifa = ifa->ifa_next) {
        if (ifa->ifa_addr == NULL)
            continue;
        if (ifa->ifa_addr->sa_family == AF_INET) {
            char interface_ip[INET_ADDRSTRLEN];
            getnameinfo(ifa->ifa_addr, sizeof(struct sockaddr_in), interface_ip,
                      INET_ADDRSTRLEN, NULL, 0, NI_NUMERICHOST);
            printf("%d: %s (%s)\n", index, ifa->ifa_name, interface_ip);
            if (index == selected_interface) {
                strcpy(selected_interface_ip, interface_ip);
            }
            index++;
        }
    }
    freeifaddrs(ifaddr);
}
#endif

void join_multicast_group(sock_t socket, const char *multicast_ip, const char *interface_ip) {
    struct ip_mreq mreq;
    mreq.imr_multiaddr.s_addr = inet_addr(multicast_ip);
    mreq.imr_interface.s_addr = inet_addr(interface_ip);
    #ifdef _WIN32
    if (setsockopt(socket, IPPROTO_IP, IP_ADD_MEMBERSHIP, (char*)&mreq, sizeof(mreq)) == SOCKET_ERROR) {
    #else
    if (setsockopt(socket, IPPROTO_IP, IP_ADD_MEMBERSHIP, &mreq, sizeof(mreq)) < 0) {
    #endif
        perror("setsockopt IP_ADD_MEMBERSHIP");
        exit(EXIT_FAILURE);
    }
}

void set_multicast_interface(sock_t socket, const char *interface_ip) {
    struct in_addr interface_addr;
    interface_addr.s_addr = inet_addr(interface_ip);
    #ifdef _WIN32
    if (setsockopt(socket, IPPROTO_IP, IP_MULTICAST_IF, (char*)&interface_addr, sizeof(interface_addr)) == SOCKET_ERROR) {
    #else
    if (setsockopt(socket, IPPROTO_IP, IP_MULTICAST_IF, &interface_addr, sizeof(interface_addr)) < 0) {
    #endif
        perror("setsockopt IP_MULTICAST_IF");
        exit(EXIT_FAILURE);
    }
}

int main(int argc, char *argv[]) {
    #ifdef _WIN32
    WSADATA wsaData;
    if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0) {
        printf("WSAStartup failed\n");
        return 1;
    }
    #endif

    sock_t socket_fd_12345, socket_fd_multicast;
    struct sockaddr_in address_12345, multicast_addr, client_address;
    socklen_t addrlen = sizeof(address_12345);

    if ((socket_fd_12345 = socket(AF_INET, SOCK_DGRAM, 0)) == INVALID_SOCK) {
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

    if (bind(socket_fd_12345, (struct sockaddr *)&address_12345, sizeof(address_12345)) == SOCKET_ERROR_VAL) {
        perror("bind failed");
        CLOSE_SOCKET(socket_fd_12345);
        #ifdef _WIN32
        WSACleanup();
        #endif
        exit(EXIT_FAILURE);
    }

    printf("Proxy listening on port 12345\n");

    if ((socket_fd_multicast = socket(AF_INET, SOCK_DGRAM, 0)) == INVALID_SOCK) {
        perror("socket failed");
        CLOSE_SOCKET(socket_fd_12345);
        #ifdef _WIN32
        WSACleanup();
        #endif
        exit(EXIT_FAILURE);
    }

    set_nonblocking(socket_fd_multicast);

    int reuse = 1;
    #ifdef _WIN32
    if (setsockopt(socket_fd_multicast, SOL_SOCKET, SO_REUSEADDR, (char*)&reuse, sizeof(reuse)) == SOCKET_ERROR) {
    #else
    if (setsockopt(socket_fd_multicast, SOL_SOCKET, SO_REUSEADDR, &reuse, sizeof(reuse)) < 0) {
    #endif
        perror("setsockopt SO_REUSEADDR");
        CLOSE_SOCKET(socket_fd_12345);
        CLOSE_SOCKET(socket_fd_multicast);
        #ifdef _WIN32
        WSACleanup();
        #endif
        exit(EXIT_FAILURE);
    }

    memset(&multicast_addr, 0, sizeof(multicast_addr));
    multicast_addr.sin_family = AF_INET;
    multicast_addr.sin_addr.s_addr = htonl(INADDR_ANY);
    multicast_addr.sin_port = htons(MULTICAST_PORT);

    if (bind(socket_fd_multicast, (struct sockaddr *)&multicast_addr, sizeof(multicast_addr)) == SOCKET_ERROR_VAL) {
        perror("bind failed");
        CLOSE_SOCKET(socket_fd_12345);
        CLOSE_SOCKET(socket_fd_multicast);
        #ifdef _WIN32
        WSACleanup();
        #endif
        exit(EXIT_FAILURE);
    }

    printf("Available interfaces:\n");
    char selected_interface_ip[INET_ADDRSTRLEN];
    list_interfaces(selected_interface_ip, 0);

    int selected_interface;
    printf("Select an interface by number: ");
    scanf("%d", &selected_interface);

    list_interfaces(selected_interface_ip, selected_interface);

    join_multicast_group(socket_fd_multicast, MULTICAST_IP, selected_interface_ip);
    printf("Joined multicast group on interface: %s\n", selected_interface_ip);

    printf("Listening for multicast messages on %s:%d\n", MULTICAST_IP, MULTICAST_PORT);

    fd_set readfds;
    struct timeval timeout;
    timeout.tv_sec = 1;
    timeout.tv_usec = 0;

    printf("Local IP address: %s\n", selected_interface_ip);

    unsigned char key[KEY_LENGTH];
    unsigned char iv[IV_LENGTH];
    unsigned char hmac_key[HMAC_KEY_LENGTH];
    memset(key, 'A', KEY_LENGTH);
    memset(iv, 'B', IV_LENGTH);
    memset(hmac_key, 'C', HMAC_KEY_LENGTH);

    while (1) {
        FD_ZERO(&readfds);
        FD_SET(socket_fd_12345, &readfds);
        FD_SET(socket_fd_multicast, &readfds);

        #ifdef _WIN32
        int activity = select(0, &readfds, NULL, NULL, &timeout);
        #else
        int activity = select(FD_SETSIZE, &readfds, NULL, NULL, &timeout);
        #endif

        if (activity == SOCKET_ERROR_VAL) {
            perror("select error");
            break;
        }

        if (FD_ISSET(socket_fd_12345, &readfds)) {
            char buffer[BUFFER_SIZE];
            int bytes_received = recvfrom(socket_fd_12345, buffer, BUFFER_SIZE, 0,
                                        (struct sockaddr *)&client_address, &addrlen);
            if (bytes_received > 0) {
                buffer[bytes_received] = '\0';
                printf("Received message from Python: %s\n", buffer);
                printf("Forward it to multicast group: %s\n", MULTICAST_IP);

                unsigned char encrypted_message[BUFFER_SIZE];
                int encrypted_length;
                encrypt_message(key, iv, buffer, encrypted_message, &encrypted_length);

                unsigned char hmac[HMAC_LENGTH];
                generate_hmac(hmac_key, encrypted_message, encrypted_length, hmac);

                unsigned char final_message[BUFFER_SIZE + HMAC_LENGTH];
                memcpy(final_message, encrypted_message, encrypted_length);
                memcpy(final_message + encrypted_length, hmac, HMAC_LENGTH);
                int final_length = encrypted_length + HMAC_LENGTH;

                set_multicast_interface(socket_fd_multicast, selected_interface_ip);
                struct sockaddr_in multicast_send_addr;
                multicast_send_addr.sin_family = AF_INET;
                multicast_send_addr.sin_addr.s_addr = inet_addr(MULTICAST_IP);
                multicast_send_addr.sin_port = htons(MULTICAST_PORT);
                #ifdef _WIN32
                sendto(socket_fd_multicast, (char*)final_message, final_length, 0,
                #else
                sendto(socket_fd_multicast, final_message, final_length, 0,
                #endif
                       (struct sockaddr *)&multicast_send_addr, sizeof(multicast_send_addr));
            }
        }

        if (FD_ISSET(socket_fd_multicast, &readfds)) {
            unsigned char buffer[BUFFER_SIZE + HMAC_LENGTH];
            #ifdef _WIN32
            int bytes_received = recvfrom(socket_fd_multicast, (char*)buffer, BUFFER_SIZE + HMAC_LENGTH, 0,
            #else
            int bytes_received = recvfrom(socket_fd_multicast, buffer, BUFFER_SIZE + HMAC_LENGTH, 0,
            #endif
                                        (struct sockaddr *)&client_address, &addrlen);
            if (bytes_received > HMAC_LENGTH) {
                printf("Received message from multicast group\n");

                int encrypted_length = bytes_received - HMAC_LENGTH;
                unsigned char *encrypted_message = buffer;
                unsigned char *received_hmac = buffer + encrypted_length;

                if (!verify_hmac(hmac_key, encrypted_message, encrypted_length, received_hmac)) {
                    printf("HMAC verification failed - message may be tampered\n");
                    continue;
                }
                printf("HMAC verification successful\n");

                unsigned char decrypted_message[BUFFER_SIZE];
                int decrypted_length = encrypted_length;
                decrypt_message(key, iv, encrypted_message, decrypted_message, &decrypted_length);

                struct sockaddr_in local_address;
                local_address.sin_family = AF_INET;
                local_address.sin_addr.s_addr = inet_addr("127.0.0.1");
                local_address.sin_port = htons(PORT_1234);
                #ifdef _WIN32
                sendto(socket_fd_multicast, (char*)decrypted_message, decrypted_length, 0,
                #else
                sendto(socket_fd_multicast, decrypted_message, decrypted_length, 0,
                #endif
                       (struct sockaddr *)&local_address, sizeof(local_address));
            }
        }
    }

    CLOSE_SOCKET(socket_fd_12345);
    CLOSE_SOCKET(socket_fd_multicast);
    #ifdef _WIN32
    WSACleanup();
    #endif

    return 0;
} 