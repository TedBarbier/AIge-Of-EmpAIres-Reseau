import socket
import argparse

HOST = '127.0.0.1'
PORT = 12345

def handle_connection(conn, addr):
    with conn:
        print(f"Connecté par {addr}")
        data = conn.recv(1024)
        if not data:
            print("Aucune donnée reçue.")
            return

        received_message = data.decode('utf-8')
        expected_message = "Bonjour Python depuis C!"

        print(f"Message reçu: \"{received_message}\"")

        if received_message == expected_message:
            print("Message vérifié avec succès!")
        else:
            print("Erreur: Message reçu ne correspond pas au message attendu.")

def server_mode():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        conn, addr = s.accept()
        handle_connection(conn, addr)

def client_mode():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((HOST, PORT))
            message = "Bonjour Python depuis C!" # Bien que ce soit Python qui envoie ici en mode client, on peut adapter
            s.sendall(message.encode('utf-8')) # Utilisation de sendall pour s'assurer que tout est envoyé
            print(f"Message envoyé: \"{message}\"")

            # Optionnellement, on pourrait aussi recevoir une réponse ici si nécessaire
            # data = s.recv(1024)
            # if data:
            #     print(f"Réponse reçue: {data.decode('utf-8')}")

        except ConnectionRefusedError:
            print("Connexion refusée. Assurez-vous que le serveur est en écoute.")

def main():
    parser = argparse.ArgumentParser(description="Programme Python flexible pour communication socket.")
    parser.add_argument("mode", choices=['server', 'client'], help="Mode de fonctionnement: 'server' ou 'client'")
    args = parser.parse_args()

    if args.mode == 'server':
        print("Démarrage en mode serveur...")
        server_mode()
    elif args.mode == 'client':
        print("Démarrage en mode client...")
        client_mode()

if __name__ == "__main__":
    main()