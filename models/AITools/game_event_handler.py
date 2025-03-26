import socket
import asyncio
import time
import json
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
        # Dernier temps de synchronisation complète du jeu
        self.last_full_sync = time.time()
        # Intervalle de synchronisation complète (5 secondes)
        self.full_sync_interval = 5.0
        
    async def ensure_network_initialized(self):
        """S'assure que le réseau est initialisé avant d'envoyer des messages."""
        
        # Si le gestionnaire de réseau n'existe pas, obtenir l'instance existante ou créer une nouvelle
        if self.network_manager is None:
            self.network_manager = NetworkManager.get_instance()
            if self.network_manager.transport is None:
                success = await self.network_manager.start()
                if not success:
                    print("Échec de l'initialisation du réseau. Utilisation du mode hors ligne.")
                    return False
            return True
        # Si le gestionnaire existe mais n'est pas correctement initialisé
        elif self.network_manager.transport is None:
            success = await self.network_manager.start()
            if not success:
                print("Échec de l'initialisation du réseau. Utilisation du mode hors ligne.")
                return False
        
        return self.network_manager.transport is not None
    
    async def process_ai_decisions_async(self, tree):
        """Version asynchrone de process_ai_decisions avec gestion de la propriété réseau"""
        # S'assurer que le réseau est initialisé
        await self.ensure_network_initialized()
        
        all_action = []
        context = self.get_context_for_player()
        actions = self.ai_profiles.decide_action(tree, context)
        
        # Construire le message réseau avec identifiant unique et timestamp
        message_id = f"{self.players.team}-{time.time()}-{len(self.pending_messages)}"
        dict_actions = {
            "update": actions, 
            "get_context_to_send": self.get_context_to_send(),
            "message_id": message_id,
            "timestamp": time.time(),
            "player_authority": self.players.team  # Identifiant du joueur ayant l'autorité
        }
        
        # Ajouter la liste des représentations de bâtiments à construire
        dict_actions['get_context_to_send']["build_repr"] = self.ai_profiles.repr
        
        # Ajoute l'action à la liste des actions en attente
        self.pending_messages.append(dict_actions)
        
        # Envoyer le message
        await self.network_manager.send_message(dict_actions)
        
        # Envoyer une synchronisation complète si nécessaire
        current_time = time.time()
        if current_time - self.last_full_sync > self.full_sync_interval:
            await self.send_full_state_sync()
            self.last_full_sync = current_time
        
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

    def verify_network_authority(self, entity_id, player_id=None):
        """Vérifie si le joueur a l'autorité sur l'entité spécifiée."""
        if player_id is None:
            player_id = self.players.team
            
        entity = self.map.get_entity_by_id(entity_id)
        if not entity:
            return False
            
        # Si l'entité a un propriétaire réseau défini, vérifier que c'est ce joueur
        if hasattr(entity, 'network_owner'):
            return entity.network_owner == player_id
        
        # Sinon, vérifier que l'entité appartient au joueur (équipe)
        if hasattr(entity, 'team'):
            return entity.team == player_id
            
        # Par défaut, pas d'autorité
        return False
    
    async def send_full_state_sync(self):
        """Envoie une synchronisation complète de l'état pour assurer la cohérence."""
        if not self.network_manager:
            return
            
        # Collecter toutes les entités appartenant au joueur actuel
        player_entities = {}
        for entity_type, entities in self.players.entities_dict.items():
            for entity_id in entities:
                entity = self.map.get_entity_by_id(entity_id)
                if entity:
                    # Ajouter l'entité à la liste si elle existe
                    player_entities[entity_id] = self.entity_to_dict(entity)
        
        # Construire le message de synchronisation
        sync_message = {
            "type": "full_sync",
            "timestamp": time.time(),
            "player_id": self.players.team,
            "resources": self.players.get_current_resources(),
            "entities": player_entities
        }
        
        # Envoyer le message de synchronisation
        await self.network_manager.send_message(sync_message)
    
    def entity_to_dict(self, entity):
        """Convertit une entité en dictionnaire pour la synchronisation réseau."""
        entity_dict = {
            "id": entity.id,
            "type": entity.__class__.__name__,
            "team": getattr(entity, 'team', None),
            "position": {
                "x": entity.position.x if hasattr(entity, 'position') else None,
                "y": entity.position.y if hasattr(entity, 'position') else None
            },
            "cell": {
                "x": entity.cell_X if hasattr(entity, 'cell_X') else None,
                "y": entity.cell_Y if hasattr(entity, 'cell_Y') else None
            },
            "hp": getattr(entity, 'hp', None),
            "target": getattr(entity, 'target', None),
            "state": getattr(entity, 'state', None),
            "network_owner": getattr(entity, 'network_owner', self.players.team),
            "last_sync": time.time()
        }
        
        # Ajouter d'autres propriétés spécifiques si nécessaire
        if hasattr(entity, 'resources'):
            entity_dict["resources"] = entity.resources
            
        return entity_dict
    
    async def handle_sync_message(self, sync_data):
        """Traite un message de synchronisation d'état."""
        player_id = sync_data.get("player_id")
        if player_id not in self.map.players_dict:
            # Joueur inconnu, ignorer le message
            return
            
        player = self.map.players_dict[player_id]
        timestamp = sync_data.get("timestamp", time.time())
        
        # Mettre à jour les ressources du joueur si nécessaire
        resources = sync_data.get("resources")
        if resources:
            for resource_type, amount in resources.items():
                player.set_resource(resource_type, amount)
        
        # Mettre à jour les entités
        entities = sync_data.get("entities", {})
        for entity_id, entity_data in entities.items():
            # Convertir l'ID en entier si nécessaire
            entity_id = int(entity_id) if isinstance(entity_id, str) else entity_id
            
            # Obtenir l'entité locale
            entity = self.map.get_entity_by_id(entity_id)
            
            # Si l'entité existe localement
            if entity:
                # Vérifier si la mise à jour est plus récente
                if entity_data.get("last_sync", 0) > getattr(entity, 'last_sync_time', 0):
                    # Mettre à jour l'entité
                    self.update_entity_from_dict(entity, entity_data)
            else:
                # L'entité n'existe pas localement, la créer si le joueur a l'autorité
                if entity_data.get("network_owner") == player_id:
                    self.create_entity_from_dict(entity_data, player_id)
    
    def update_entity_from_dict(self, entity, entity_data):
        """Met à jour une entité existante à partir des données de synchronisation."""
        # Mettre à jour les propriétés de base
        if hasattr(entity, 'position') and 'position' in entity_data:
            if entity_data['position']['x'] is not None:
                entity.position.x = entity_data['position']['x']
            if entity_data['position']['y'] is not None:
                entity.position.y = entity_data['position']['y']
                
        # Mettre à jour les autres propriétés si elles existent
        if hasattr(entity, 'hp') and 'hp' in entity_data:
            entity.hp = entity_data['hp']
            
        if hasattr(entity, 'target') and 'target' in entity_data:
            entity.target = entity_data['target']
            
        if hasattr(entity, 'state') and 'state' in entity_data:
            entity.state = entity_data['state']
            
        if hasattr(entity, 'resources') and 'resources' in entity_data:
            entity.resources = entity_data['resources']
            
        # Mettre à jour les propriétés réseau
        entity.network_owner = entity_data.get('network_owner', getattr(entity, 'network_owner', None))
        entity.last_sync_time = entity_data.get('last_sync', time.time())
    
    def create_entity_from_dict(self, entity_data, player_id):
        """Crée une nouvelle entité à partir des données de synchronisation."""
        # Cette méthode nécessiterait une implémentation spécifique au jeu pour créer les bonnes classes d'entités
        # Un exemple simplifié:
        entity_id = entity_data.get('id')
        entity_type = entity_data.get('type')
        cell_x = entity_data.get('cell', {}).get('x')
        cell_y = entity_data.get('cell', {}).get('y')
        
        # Vérifier si nous avons les informations nécessaires
        if entity_id is None or cell_x is None or cell_y is None:
            return None
            
        # Créer l'entité en fonction de son type
        # Cette partie dépend fortement de l'architecture du jeu
        player = self.map.players_dict.get(player_id)
        if not player:
            return None
            
        # Le reste de l'implémentation dépend de comment sont créées les entités dans le jeu

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
