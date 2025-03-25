import asyncio
import json
from typing import Dict, Any, Callable, Optional, Tuple, Union
import socket

# Singleton pour garder une référence à l'instance unique
_NETWORK_MANAGER_INSTANCE = None

class NetworkManager:
    def __init__(self, message_handler: Callable = None):
        """
        Initialise le gestionnaire de réseau asynchrone.
        
        Args:
            message_handler: Fonction appelée lors de la réception d'un message
        """
        global _NETWORK_MANAGER_INSTANCE
        
        # Si une instance existe déjà, réutiliser sa configuration
        if _NETWORK_MANAGER_INSTANCE is not None:
            self.transport = _NETWORK_MANAGER_INSTANCE.transport
            self.protocol = _NETWORK_MANAGER_INSTANCE.protocol
            self.packets_sent = _NETWORK_MANAGER_INSTANCE.packets_sent
            self.packets_received = _NETWORK_MANAGER_INSTANCE.packets_received
            # Mais mettre à jour le gestionnaire de messages
            self.message_handler = message_handler
            self.loop = _NETWORK_MANAGER_INSTANCE.loop
            self.receive_address = _NETWORK_MANAGER_INSTANCE.receive_address
            self.send_address = _NETWORK_MANAGER_INSTANCE.send_address
            _NETWORK_MANAGER_INSTANCE = self
            return
            
        # Nouvelle instance
        self.message_handler = message_handler
        # Port fixe pour la réception: 1234
        self.receive_address = ('127.0.0.1', 1234)
        # Port fixe pour l'envoi: 12345
        self.send_address = ('127.0.0.1', 12345)
        self.transport = None
        self.protocol = None
        self.packets_sent = 0
        self.packets_received = 0
        self.loop = None
        
        # Définir cette instance comme singleton
        _NETWORK_MANAGER_INSTANCE = self
        
    @classmethod
    def get_instance(cls, message_handler=None):
        """Récupère l'instance unique du NetworkManager, ou en crée une si nécessaire."""
        global _NETWORK_MANAGER_INSTANCE
        if _NETWORK_MANAGER_INSTANCE is None:
            _NETWORK_MANAGER_INSTANCE = cls(message_handler)
        elif message_handler is not None:
            _NETWORK_MANAGER_INSTANCE.message_handler = message_handler
        return _NETWORK_MANAGER_INSTANCE
        
    async def start(self):
        """Démarre les sockets UDP pour l'envoi et la réception de messages via asyncio."""
        # Si le transport existe déjà, nous sommes déjà connectés
        if self.transport is not None:
            print("Socket réseau déjà initialisée")
            return True
            
        self.loop = asyncio.get_event_loop()
        
        # Créer le protocole de réception - Simplifié comme dans test2.py
        class UDPServerProtocol(asyncio.DatagramProtocol):
            def __init__(self, network_manager):
                self.network_manager = network_manager
            
            def connection_made(self, transport):
                self.network_manager.transport = transport
                # Configurer la socket pour de meilleures performances
                sock = transport.get_extra_info('socket')
                if sock:
                    # Augmenter considérablement les buffers socket
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 16 * 1024 * 1024)  # 16Mo
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 16 * 1024 * 1024)  # 16Mo
                
            def datagram_received(self, data, addr):
                # Version simplifiée comme dans test2.py
                received_message = data.decode('utf-8')
                self.network_manager.packets_received += 1
                
                # Traitement immédiat sans attendre - plus rapide
                if self.network_manager.message_handler:
                    # Traitement immédiat, sans create_task qui pourrait retarder l'exécution
                    self.network_manager.loop.create_task(
                        self.network_manager._process_message_directly(received_message, addr)
                    )
        
        # Créer le point de terminaison pour la réception
        try:
            self.transport, self.protocol = await self.loop.create_datagram_endpoint(
                lambda: UDPServerProtocol(self),
                local_addr=self.receive_address,
                allow_broadcast=True,  # Permettre broadcast pour plus de flexibilité
                reuse_port=False  # Ne pas réutiliser le port pour éviter les conflits
            )
            print(f"Réseau initialisé : écoute sur {self.receive_address}")
            return True
        except OSError as e:
            print(f"Erreur lors de l'initialisation du réseau (port déjà utilisé?) : {e}")
            return False
        except Exception as e:
            print(f"Erreur lors de l'initialisation du réseau : {e}")
            return False
        
    async def _process_message_directly(self, message: str, addr: Tuple[str, int]):
        """Traite directement les messages sans file d'attente intermédiaire."""
        try:
            dict_message = json.loads(message)
            if self.message_handler:
                await self.message_handler(dict_message, message)
        except json.JSONDecodeError:
            # Ne pas afficher le message complet, juste le nombre pour gagner du temps
            print(f"Erreur : message mal formaté reçu : paquet {message}#{self.packets_received}")
        except Exception as e:
            print(f"Erreur lors du traitement du message : {e}")
    
    # Version deprecated - Gardée pour compatibilité
    async def _process_message(self, message: str, addr: Tuple[str, int]):
        await self._process_message_directly(message, addr)
    
    async def send_message(self, message: Union[Dict, str]):
        """Envoie un message réseau de façon asynchrone."""
        if not self.transport:
            print("Tentative d'envoi sans transport initialisé")
            return False
            
        try:
            # Optimiser l'envoi en minimisant les conversions
            if isinstance(message, dict):
                message_json = json.dumps(message)
                bytes_data = message_json.encode('utf-8')
            elif isinstance(message, str):
                bytes_data = message.encode('utf-8')
            else:
                # Fallback pour tout autre type
                message_json = json.dumps({"data": str(message)})
                bytes_data = message_json.encode('utf-8')
                
            # Envoyer le message directement
            self.transport.sendto(bytes_data, self.send_address)
            self.packets_sent += 1
            return True
        except Exception as e:
            print(f"Erreur lors de l'envoi du message : {e}")
            return False
    
    def close(self):
        """Ferme les connexions réseau."""
        global _NETWORK_MANAGER_INSTANCE
        if self.transport:
            try:
                self.transport.close()
            except Exception as e:
                print(f"Erreur lors de la fermeture du transport réseau : {e}")
            finally:
                self.transport = None
                self.protocol = None
                print("Transport réseau fermé")
                _NETWORK_MANAGER_INSTANCE = None
