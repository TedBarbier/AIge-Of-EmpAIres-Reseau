import asyncio
import json
from typing import Dict, Any, Callable, Optional, Tuple, Union

class NetworkManager:
    def __init__(self, message_handler: Callable = None):
        """
        Initialise le gestionnaire de réseau asynchrone.
        
        Args:
            message_handler: Fonction appelée lors de la réception d'un message
        """
        self.message_handler = message_handler
        self.receive_address = ('127.0.0.1', 1234)
        self.send_address = ('127.0.0.1', 12345)
        self.transport = None
        self.protocol = None
        self.packets_sent = 0
        self.packets_received = 0
        self.loop = None
    
    async def start(self):
        """Démarre les sockets UDP pour l'envoi et la réception de messages via asyncio."""
        self.loop = asyncio.get_event_loop()
        
        # Créer le protocole de réception
        class UDPServerProtocol(asyncio.DatagramProtocol):
            def __init__(self, network_manager):
                self.network_manager = network_manager
            
            def connection_made(self, transport):
                self.network_manager.transport = transport
                
            def datagram_received(self, data, addr):
                received_message = data.decode('utf-8')
                self.network_manager.packets_received += 1
                if self.network_manager.message_handler:
                    asyncio.create_task(self.network_manager._process_message(received_message, addr))
            
        # Créer le point de terminaison pour la réception
        try:
            self.transport, self.protocol = await self.loop.create_datagram_endpoint(
                lambda: UDPServerProtocol(self),
                local_addr=self.receive_address
            )
            print(f"Réseau initialisé : écoute sur {self.receive_address}")
        except Exception as e:
            print(f"Erreur lors de l'initialisation du réseau : {e}")
            return False
            
        return True
        
    async def _process_message(self, message: str, addr: Tuple[str, int]):
        """Traite les messages reçus et appelle le gestionnaire de messages."""
        try:
            dict_message = json.loads(message)
            if self.message_handler:
                await self.message_handler(dict_message, message)
        except json.JSONDecodeError:
            print(f"Erreur : message mal formaté reçu : {message}")
        except Exception as e:
            print(f"Erreur lors du traitement du message : {e}")
    
    async def send_message(self, message: Union[Dict, str]):
        """Envoie un message réseau de façon asynchrone."""
        if not self.transport:
            print("Tentative d'envoi sans transport initialisé")
            return False
            
        try:
            # Convertir en JSON si c'est un dictionnaire
            if isinstance(message, dict):
                message_json = json.dumps(message)
            else:
                message_json = message
                
            # Envoyer le message
            self.transport.sendto(message_json.encode('utf-8'), self.send_address)
            self.packets_sent += 1
            return True
        except Exception as e:
            print(f"Erreur lors de l'envoi du message : {e}")
            return False
    
    def close(self):
        """Ferme les connexions réseau."""
        if self.transport:
            self.transport.close()
            self.transport = None
