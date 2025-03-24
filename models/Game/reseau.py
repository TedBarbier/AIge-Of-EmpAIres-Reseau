import socket
import json
# from AITools.game_event_handler import *

class Send:
    def __init__(self):
        self.udp_host = '127.0.0.1'
        self.udp_port = 12345
        # Création du socket UDP
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.setblocking(0)
        # Compteurs de paquets
        self.packets_sent = 0
        self.packets_received = 0

    def send_action_via_udp(self, context_to_send):
            try:
                #print("try \n")
                # Encapsuler l'action dans un objet JSON
                action_data = context_to_send
                action_json = json.dumps(action_data)  # Convertir en JSON
                #print(f"Envoi de : {action_json} à {self.udp_host}:{self.udp_port} \n")
                self.udp_socket.sendto(action_json.encode('utf-8'), (self.udp_host, self.udp_port))
                self.packets_sent += 1
                print(f"Paquets envoyés: {self.packets_sent}, Paquets reçus: {self.packets_received}")
                #print(f"Action envoyée via UDP : {action_json} \n")
            except BlockingIOError:
                # Handle the error if the socket is non-blocking and the send buffer is full
                print("Socket send buffer is full, data not sent.")
            except Exception as e:
                print(f"Erreur lors de l'envoi de l'action UDP : {e}")
