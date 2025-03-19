import socket
import sys
import time
import msvcrt  # Pour Windows

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
    
    while True:
        try:
            # Vérifier si une touche a été pressée
            if msvcrt.kbhit():
                char = msvcrt.getch()
                
                if char == b'\r':  # Enter
                    if message_buffer:
                        client_socket.sendto(message_buffer.encode('utf-8'), target_address)
                        print(f"\nMessage envoyé: {message_buffer}")
                        message_buffer = ""
                        print()  # Nouvelle ligne
                else:
                    # Afficher le caractère et l'ajouter au buffer
                    char_str = char.decode()
                    print(char_str, end='', flush=True)
                    message_buffer += char_str
            
            # Vérifier si des messages sont reçus
            try:
                data, addr = server_socket.recvfrom(1024)
                print(f"\nReçu de {addr}: {data.decode('utf-8')}")
            except BlockingIOError:
                pass  # Pas de données disponibles
            
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
