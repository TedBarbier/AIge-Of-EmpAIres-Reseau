#include "tls_utils.h"
#include <winsock2.h>
#include <ws2tcpip.h>
#include <iphlpapi.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <windows.h>

#pragma comment(lib, "ws2_32.lib")
#pragma comment(lib, "iphlpapi.lib")

#define PORT_12345 12345
#define PORT_1234 1234
#define MULTICAST_PORT 8000
#define BUFFER_SIZE 1024
#define MULTICAST_IP "239.255.255.250"

void set_nonblocking(SOCKET socket) {
    u_long mode = 1;
    if (ioctlsocket(socket, FIONBIO, &mode) == SOCKET_ERROR) {
        perror("ioctlsocket");
        exit(EXIT_FAILURE);
    }
}

void join_multicast_group(SOCKET socket, const char *multicast_ip, const char *interface_ip) {
    struct ip_mreq mreq;
    mreq.imr_multiaddr.s_addr = inet_addr(multicast_ip);
    mreq.imr_interface.s_addr = inet_addr(interface_ip);
    if (setsockopt(socket, IPPROTO_IP, IP_ADD_MEMBERSHIP, (char*)&mreq, sizeof(mreq)) == SOCKET_ERROR) {
        perror("setsockopt IP_ADD_MEMBERSHIP");
        exit(EXIT_FAILURE);
    }
}

void set_multicast_interface(SOCKET socket, const char *interface_ip) {
    struct in_addr interface_addr;
    interface_addr.s_addr = inet_addr(interface_ip);
    if (setsockopt(socket, IPPROTO_IP, IP_MULTICAST_IF, (char*)&interface_addr, sizeof(interface_addr)) == SOCKET_ERROR) {
        perror("setsockopt IP_MULTICAST_IF");
        exit(EXIT_FAILURE);
    }
}

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
                
                const char* interface_type = "Unknown";
                switch (pAdapterInfo->Type) {
                    case MIB_IF_TYPE_ETHERNET:
                        interface_type = "Ethernet";
                        break;
                    case MIB_IF_TYPE_PPP:
                        interface_type = "PPP";
                        break;
                    case IF_TYPE_IEEE80211:
                        interface_type = "WiFi";
                        break;
                    case IF_TYPE_IEEE1394:
                        interface_type = "FireWire";
                        break;
                    case IF_TYPE_TUNNEL:
                        interface_type = "Tunnel";
                        break;
                }

                printf("%d: %s (%s) - %s\n", 
                       index, 
                       pAdapterInfo->Description, 
                       pAdapterInfo->IpAddressList.IpAddress.String,
                       interface_type);
                
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

int main(int argc, char *argv[]) {
    WSADATA wsaData;
    SOCKET socket_fd_12345, socket_fd_multicast;
    struct sockaddr_in address_12345, multicast_addr, client_address;
    int addrlen = sizeof(address_12345);

    // Initialize Winsock
    if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0) {
        printf("WSAStartup failed\n");
        return 1;
    }

    /* Create socket for port 12345 */
    if ((socket_fd_12345 = socket(AF_INET, SOCK_DGRAM, 0)) == INVALID_SOCKET) {
        perror("socket failed");
        WSACleanup();
        exit(EXIT_FAILURE);
    }

    set_nonblocking(socket_fd_12345);

    address_12345.sin_family = AF_INET;
    address_12345.sin_addr.s_addr = INADDR_ANY;
    address_12345.sin_port = htons(PORT_12345);

    if (bind(socket_fd_12345, (struct sockaddr *)&address_12345, sizeof(address_12345)) == SOCKET_ERROR) {
        perror("bind failed");
        closesocket(socket_fd_12345);
        WSACleanup();
        exit(EXIT_FAILURE);
    }

    printf("Proxy listening on port 12345\n");

    /* Create socket for multicast */
    if ((socket_fd_multicast = socket(AF_INET, SOCK_DGRAM, 0)) == INVALID_SOCKET) {
        perror("socket failed");
        closesocket(socket_fd_12345);
        WSACleanup();
        exit(EXIT_FAILURE);
    }

    set_nonblocking(socket_fd_multicast);

    /* Allow the socket to be reused */
    int reuse = 1;
    if (setsockopt(socket_fd_multicast, SOL_SOCKET, SO_REUSEADDR, (char*)&reuse, sizeof(reuse)) == SOCKET_ERROR) {
        perror("setsockopt SO_REUSEADDR");
        closesocket(socket_fd_12345);
        closesocket(socket_fd_multicast);
        WSACleanup();
        exit(EXIT_FAILURE);
    }

    /* Bind the socket to the multicast port */
    memset(&multicast_addr, 0, sizeof(multicast_addr));
    multicast_addr.sin_family = AF_INET;
    multicast_addr.sin_addr.s_addr = htonl(INADDR_ANY);
    multicast_addr.sin_port = htons(MULTICAST_PORT);

    if (bind(socket_fd_multicast, (struct sockaddr *)&multicast_addr, sizeof(multicast_addr)) == SOCKET_ERROR) {
        perror("bind failed");
        closesocket(socket_fd_12345);
        closesocket(socket_fd_multicast);
        WSACleanup();
        exit(EXIT_FAILURE);
    }

    /* List available interfaces */
    printf("Available interfaces:\n");
    char selected_interface_ip[INET_ADDRSTRLEN];
    list_interfaces(selected_interface_ip, 0);

    /* Prompt user to select an interface */
    int selected_interface;
    printf("Select an interface by number: ");
    scanf("%d", &selected_interface);

    /* Get the selected interface IP */
    list_interfaces(selected_interface_ip, selected_interface);

    /* Join the multicast group on the selected interface */
    join_multicast_group(socket_fd_multicast, MULTICAST_IP, selected_interface_ip);
    printf("Joined multicast group on interface: %s\n", selected_interface_ip);

    printf("Listening for multicast messages on %s:%d\n", MULTICAST_IP, MULTICAST_PORT);

    fd_set readfds;
    struct timeval timeout;
    timeout.tv_sec = 1;
    timeout.tv_usec = 0;

    /* Print the local IP address */
    printf("Local IP address: %s\n", selected_interface_ip);

    unsigned char key[KEY_LENGTH];
    unsigned char iv[IV_LENGTH];
    memset(key, 'A', KEY_LENGTH);
    memset(iv, 'B', IV_LENGTH);

    while (1) {
        FD_ZERO(&readfds);
        FD_SET(socket_fd_12345, &readfds);
        FD_SET(socket_fd_multicast, &readfds);

        int activity = select(0, &readfds, NULL, NULL, &timeout);

        if (activity == SOCKET_ERROR) {
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

                /* Encrypt the message */
                unsigned char encrypted_message[BUFFER_SIZE];
                int encrypted_length;
                encrypt_message(key, iv, buffer, encrypted_message, &encrypted_length);

                /* Send to multicast group on the selected interface */
                set_multicast_interface(socket_fd_multicast, selected_interface_ip);
                struct sockaddr_in multicast_send_addr;
                multicast_send_addr.sin_family = AF_INET;
                multicast_send_addr.sin_addr.s_addr = inet_addr(MULTICAST_IP);
                multicast_send_addr.sin_port = htons(MULTICAST_PORT);
                sendto(socket_fd_multicast, (char*)encrypted_message, encrypted_length, 0,
                       (struct sockaddr *)&multicast_send_addr, sizeof(multicast_send_addr));
            }
        }

        if (FD_ISSET(socket_fd_multicast, &readfds)) {
            unsigned char buffer[BUFFER_SIZE];
            int bytes_received = recvfrom(socket_fd_multicast, (char*)buffer, BUFFER_SIZE, 0,
                                        (struct sockaddr *)&client_address, &addrlen);
            if (bytes_received > 0) {
                printf("Received message from multicast group\n");

                /* Debugging: Print the received encrypted data */
                printf("Received encrypted data: ");
                for (int i = 0; i < bytes_received; i++) {
                    printf("%02x", buffer[i]);
                }
                printf("\n");

                /* Decrypt the message */
                unsigned char decrypted_message[BUFFER_SIZE];
                int decrypted_length = bytes_received;
                decrypt_message(key, iv, buffer, decrypted_message, &decrypted_length);

                /* Forward to Python server on localhost:1234 */
                struct sockaddr_in local_address;
                local_address.sin_family = AF_INET;
                local_address.sin_addr.s_addr = inet_addr("127.0.0.1");
                local_address.sin_port = htons(PORT_1234);
                sendto(socket_fd_multicast, (char*)decrypted_message, decrypted_length, 0,
                       (struct sockaddr *)&local_address, sizeof(local_address));
            }
        }
    }

    closesocket(socket_fd_12345);
    closesocket(socket_fd_multicast);
    WSACleanup();

    return 0;
} 