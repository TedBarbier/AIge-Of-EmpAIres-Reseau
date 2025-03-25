import socket
import asyncio
from Game.network_manager import NetworkManager

class GameEventHandler:
    def __init__(self, map, players, ai_profiles, network_manager=None):
        """
        Initialise le gestionnaire d'événements de jeu.
        
        Args:
            map: La carte du jeu
            players: Les joueurs
            ai_profiles: Les profils d'IA
            network_manager: Un NetworkManager déjà initialisé (optionnel)
        """
        self.map = map
        self.players = players
        self.ai_profiles = ai_profiles
        # Utiliser le NetworkManager fourni, ou créer une référence à initialiser plus tard
        self.network_manager = network_manager
        self.pending_messages = []
        
    async def ensure_network_initialized(self):
        """S'assure que le réseau est initialisé avant d'envoyer des messages."""
        print("ensure network initialized",type(self.network_manager))#, self.network_manager.transport)
        if self.network_manager is None:
            self.network_manager = NetworkManager()
            await self.network_manager.start()
        elif self.network_manager.transport is None:
            await self.network_manager.start()
    
    async def process_ai_decisions_async(self, tree):
        """Version asynchrone de process_ai_decisions"""
        # S'assurer que le réseau est initialisé
        await self.ensure_network_initialized()
        
        all_action = []
        context = self.get_context_for_player()
        actions = self.ai_profiles.decide_action(tree, context)
        dict_actions = {"update": actions, "get_context_to_send": self.get_context_to_send()}
        dict_actions['get_context_to_send']["build_repr"] = self.ai_profiles.repr
        
        # Ajoute l'action à la liste des actions en attente
        self.pending_messages.append(dict_actions)
        
        # Utilisation uniquement de la version asynchrone
        await self.network_manager.send_message(dict_actions)
            
        dict_actions['get_context_to_send']["build_repr"] = None
        all_action.append(actions)
        return all_action
    
    def process_ai_decisions(self, tree):
        """Méthode de compatibilité pour l'ancienne interface synchrone"""
        all_action = []
        context = self.get_context_for_player()
        actions = self.ai_profiles.decide_action(tree, context)
        dict_actions = {"update": actions, "get_context_to_send": self.get_context_to_send()}
        dict_actions['get_context_to_send']["build_repr"] = self.ai_profiles.repr
        
        # Utilise asyncio même pour l'API synchrone
        # Mais s'assure d'abord que le réseau est initialisé
        asyncio.create_task(self.ensure_and_send_message(dict_actions))
        
        dict_actions['get_context_to_send']["build_repr"] = None
        all_action.append(actions)
        return all_action
    
    async def ensure_and_send_message(self, message):
        """S'assure que le réseau est initialisé avant d'envoyer un message."""
        await self.ensure_network_initialized()
        await self.network_manager.send_message(message)

    async def receive_context_async(self):
        """Reçoit un contexte de façon asynchrone"""
        host = '127.0.0.1'
        port = 12345
        
        try:
            transport, protocol = await asyncio.get_event_loop().create_datagram_endpoint(
                lambda: AsyncUDPReceiver(),
                local_addr=(host, port)
            )
            
            # Attendre de recevoir un message (avec timeout)
            message = await asyncio.wait_for(protocol.message_received(), timeout=1.0)
            transport.close()
            return message
            
        except asyncio.TimeoutError:
            print("Timeout lors de l'attente d'un message")
            return None
        except Exception as e:
            print(f"Erreur lors de la réception du message : {e}")
            return None
    
    # La méthode receive_context synchrone est supprimée car nous n'utilisons plus les sockets directs
    # Tout code qui utilise receive_context doit être mis à jour pour utiliser receive_context_async

    def get_context_for_player(self):
        context = {
            'desired_villager_count': len(self.players.get_entities_by_class(['T','H','C','F','B','S','A','K']))+2,
            'resources': self.players.get_current_resources(),
            'ratio_military': len(self.players.get_entities_by_class(['h', 'a', 's', 'x', 'm', 'c'])) / len(self.players.get_entities_by_class(['h', 'a', 's', 'v', 'x', 'm', 'c'])) if len(self.players.get_entities_by_class(['h', 'a', 's', 'v', 'x', 'm', 'c'])) != 0 else 0,
            'buildings': {
                'storage': self.players.get_entities_by_class(['T','C']),
                'training': self.players.get_entities_by_class(['B','S','A']),
                'ratio': {
                    'T': len(self.players.entities_dict['T']) / sum(len(self.players.entities_dict[k]) for k in self.players.entities_dict.keys()) if 'T' in self.players.entities_dict.keys() else 0,
                    'H': len(self.players.entities_dict['H']) / sum(len(self.players.entities_dict[k]) for k in self.players.entities_dict.keys()) if 'H' in self.players.entities_dict.keys() else 0,
                    'C': len(self.players.entities_dict['C']) / sum(len(self.players.entities_dict[k]) for k in self.players.entities_dict.keys()) if 'C' in self.players.entities_dict.keys() else 0,
                    'F': len(self.players.entities_dict['F']) / sum(len(self.players.entities_dict[k]) for k in self.players.entities_dict.keys()) if 'F' in self.players.entities_dict.keys() else 0,
                    'B': len(self.players.entities_dict['B']) / sum(len(self.players.entities_dict[k]) for k in self.players.entities_dict.keys()) if 'B' in self.players.entities_dict.keys() else 0,
                    'S': len(self.players.entities_dict['S']) / sum(len(self.players.entities_dict[k]) for k in self.players.entities_dict.keys()) if 'S' in self.players.entities_dict.keys() else 0,
                    'A': len(self.players.entities_dict['A']) / sum(len(self.players.entities_dict[k]) for k in self.players.entities_dict.keys()) if 'A' in self.players.entities_dict.keys() else 0,
                    'K': len(self.players.entities_dict['K']) / sum(len(self.players.entities_dict[k]) for k in self.players.entities_dict.keys()) if 'K' in self.players.entities_dict.keys() else 0,
                }
            },
            'units': {
                'military_free': [self.players.linked_map.get_entity_by_id(m_id) for m_id in self.players.get_entities_by_class(['h', 'a', 's', 'm', 'c', 'x'], is_free=True)],
                'villager': [self.players.linked_map.get_entity_by_id(v_id) for v_id in self.players.get_entities_by_class(['v'])],
                'villager_free': [self.players.linked_map.get_entity_by_id(v_id) for v_id in self.players.get_entities_by_class(['v'], is_free=True)],
            },
            'enemy_id': None,
            'drop_off_id': self.players.ect(['T', 'C'], self.players.cell_Y, self.players.cell_X)[0] if self.players.ect(['T', 'C'], self.players.cell_Y, self.players.cell_X) else None,
            'player': self.players,
            'housing_crisis': (self.players.current_population >= self.players.get_current_population_capacity())
        }
        return context

    def get_context_to_send(self):
        context ={
            'resources': self.players.get_current_resources(),
            'buildings': {
                'storage': self.players.get_entities_by_class(['T','C']),
                'training': self.players.get_entities_by_class(['B','S','A']),
                'ratio': {
                    'T': len(self.players.entities_dict['T']) / sum(len(self.players.entities_dict[k]) for k in self.players.entities_dict.keys()) if 'T' in self.players.entities_dict.keys() else 0,
                    'H': len(self.players.entities_dict['H']) / sum(len(self.players.entities_dict[k]) for k in self.players.entities_dict.keys()) if 'H' in self.players.entities_dict.keys() else 0,
                    'C': len(self.players.entities_dict['C']) / sum(len(self.players.entities_dict[k]) for k in self.players.entities_dict.keys()) if 'C' in self.players.entities_dict.keys() else 0,
                    'F': len(self.players.entities_dict['F']) / sum(len(self.players.entities_dict[k]) for k in self.players.entities_dict.keys()) if 'F' in self.players.entities_dict.keys() else 0,
                    'B': len(self.players.entities_dict['B']) / sum(len(self.players.entities_dict[k]) for k in self.players.entities_dict.keys()) if 'B' in self.players.entities_dict.keys() else 0,
                    'S': len(self.players.entities_dict['S']) / sum(len(self.players.entities_dict[k]) for k in self.players.entities_dict.keys()) if 'S' in self.players.entities_dict.keys() else 0,
                    'A': len(self.players.entities_dict['A']) / sum(len(self.players.entities_dict[k]) for k in self.players.entities_dict.keys()) if 'A' in self.players.entities_dict.keys() else 0,
                    'K': len(self.players.entities_dict['K']) / sum(len(self.players.entities_dict[k]) for k in self.players.entities_dict.keys()) if 'K' in self.players.entities_dict.keys() else 0,
                }
            },
            'units': {
                'military_free': [self.players.get_entities_by_class(['h', 'a', 's', 'm', 'c', 'x'], is_free=True)],
                'villager': [self.players.get_entities_by_class(['v'])],
                'villager_free': [self.players.get_entities_by_class(['v'], is_free=True)],
            },
            'enemy_id': None,
            'drop_off_id': self.players.ect(['T', 'C'], self.players.cell_Y, self.players.cell_X)[0] if self.players.ect(['T', 'C'], self.players.cell_Y, self.players.cell_X) else None,
            'player': self.players.team,
            'strategy': self.players.ai_profile.strategy,
            'build_repr' : None
        }
        return context
    
    def get_all_context(self):
        return self.players.all_context

    def update_all_context(self, send):
        all_context=self.players.all_context
        all_context[send['player']]=send

# Classe auxiliaire pour la réception UDP asynchrone
class AsyncUDPReceiver(asyncio.DatagramProtocol):
    def __init__(self):
        self.message = None
        self.transport = None
        self.future = asyncio.Future()
        
    def connection_made(self, transport):
        self.transport = transport
        
    def datagram_received(self, data, addr):
        message = data.decode('utf-8')
        self.future.set_result(message)
        
    def connection_lost(self, exc):
        if not self.future.done():
            self.future.set_exception(exc or ConnectionError("Connection perdue"))
            
    def message_received(self):
        return self.future
