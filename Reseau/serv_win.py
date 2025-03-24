import socket
import sys
import time

def create_nonblocking_socket():
    """Crée un socket UDP non-bloquant"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(0.0)  # Rend le socket non-bloquant
    return sock

def main():
    # Créer les sockets
    server_socket = create_nonblocking_socket()
    client_socket = create_nonblocking_socket()

    # Configuration
    server_socket.bind(('localhost', 1234))
    target_address = ('localhost', 12345)

    print("Serveur Python en écoute sur le port 1234")
    print("Tapez votre message et appuyez sur Enter pour l'envoyer")
    print("Tapez 'quit' pour quitter")

    message_buffer = ""

    # Importation conditionnelle de msvcrt uniquement sur Windows
    if sys.platform == 'win32':
        import msvcrt
        print("Mode Windows détecté, utilisant msvcrt pour l'entrée non-bloquante.")
        def kbhit():
            return msvcrt.kbhit()
        def getch():
            return msvcrt.getch().decode('utf-8')  # Décode en utf-8 pour gérer correctement les caractères
    else: # Pour les autres plateformes (Unix-like), on garde select
        import select
        print("Mode non-Windows détecté, utilisant select pour l'entrée non-bloquante.")
        def kbhit():
            return sys.stdin in select.select([sys.stdin], [], [], 0)[0]
        def getch():
            return sys.stdin.read(1)


    while True:
        try:
            # Vérifier si des messages sont reçus
            try:
                data, addr = server_socket.recvfrom(1024)
                print(f"\nReçu de {addr}: {data.decode('utf-8')}")
            except BlockingIOError:
                pass  # Pas de données disponibles

            # Vérifier si une entrée clavier est disponible
            if kbhit():
                char = getch()
                if char == '\r':  # Enter (Windows utilise souvent \r pour Enter en console)
                    char = '\n' # Normaliser en \n pour le reste du code
                    if message_buffer:
                        client_socket.sendto(message_buffer.encode('utf-8'), target_address)
                        print(f"\nMessage envoyé: {message_buffer}")
                        message_buffer = ""
                        print()  # Nouvelle ligne
                elif char == '\x03': # Ctrl+C pour quitter
                    raise KeyboardInterrupt
                else:
                    # Afficher le caractère et l'ajouter au buffer
                    print(char, end='', flush=True)
                    message_buffer += char

            # Petit délai pour éviter de surcharger le CPU
            time.sleep(0.01)

        except KeyboardInterrupt:
            print("\nArrêt du programme...")
            break
        except Exception as e:
            print(f"\nErreur: {e}")
            time.sleep(1)  # Attendre un peu avant de réessayer

if __name__ == "__main__":
    main()