import socket
import argparse

HOST = '127.0.0.1'
PORT = 12345
BUFFER_SIZE = 1024

def server_mode():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s: # SOCK_DGRAM pour UDP
        s.bind((HOST, PORT))
        print(f"Serveur UDP en écoute sur le port {PORT}...")
        while True: # Boucle pour recevoir continuellement
            data, addr = s.recvfrom(BUFFER_SIZE) # recvfrom pour UDP
            if data:
                received_message = data.decode('utf-8')
                expected_message = "Bonjour Python depuis C!"
                print(f"Message reçu de {addr}: \"{received_message}\"")
                if received_message == expected_message:
                    print("Message vérifié avec succès!")
                else:
                    print("Erreur: Message reçu ne correspond pas au message attendu.")

def client_mode():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s: # SOCK_DGRAM pour UDP
        server_address = (HOST, PORT)
        message = "Bonjour Python depuis C!"
        s.sendto(message.encode('utf-8'), server_address) # sendto pour UDP
        print(f"Message UDP envoyé: \"{message}\"")

def main():
    parser = argparse.ArgumentParser(description="Programme Python flexible pour communication socket UDP.")
    parser.add_argument("mode", choices=['server', 'client'], help="Mode de fonctionnement: 'server' ou 'client'")
    args = parser.parse_args()

    if args.mode == 'server':
        server_mode()
    elif args.mode == 'client':
        client_mode()

if __name__ == "__main__":
    main()