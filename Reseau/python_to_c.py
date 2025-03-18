import socket
import time

HOST = '127.0.0.1'
PORT = 12345

class PythonToCClient:
    def __init__(self):
        pass

    def envoyer_action_via_udp(self, player_context):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            server_address = (HOST, PORT)
            
            # Structure des données à envoyer sous forme de chaîne ASCII
            # Utilisation de formatage de chaîne pour créer une chaîne avec les données
            villager_count = 10
            wood = 100
            food = 200
            stone = 50
            gold = 30
            military_ratio = 2.0
            storage_count = 5
            training_count = 3
            military_free = 2
            villager_total = 12
            villager_free = 8
            housing_crisis = 0  # 0 = No, 1 = Yes

            # Créer une chaîne de caractères avec toutes les données (séparées par des espaces)
            message = f"{villager_count} {wood} {food} {stone} {gold} {military_ratio} {storage_count} {training_count} {military_free} {villager_total} {villager_free} {housing_crisis}"
            
            print(f"Envoi du message : {message}")
            s.sendto(message.encode('ascii'), server_address)
            print("Message UDP envoyé avec les données du GameState")

if __name__ == "__main__":
    client = PythonToCClient()
    while True:
        client.envoyer_action_via_udp(None)
        time.sleep(10)
