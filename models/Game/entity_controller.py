import asyncio
import time
from typing import Dict, Any, Optional

class EntityController:
    """
    Contrôleur qui gère l'interaction réseau avec les entités.
    Sert d'intermédiaire pour assurer la cohérence des entités entre les instances réseau.
    """
    
    def __init__(self, game_map, network_manager=None):
        self.game_map = game_map
        self.network_manager = network_manager
        self.entity_updates_queue = {}  # File d'attente des mises à jour par entité
        self.authority_cache = {}       # Cache des autorisations d'entités
        self.last_sync_time = time.time()
        self.sync_interval = 3.0        # Intervalle de synchronisation en secondes
        
    def register_entity(self, entity, owner_id):
        """Enregistre une entité avec un propriétaire réseau."""
        if not hasattr(entity, 'network_owner'):
            entity.network_owner = owner_id
            entity.last_sync_time = time.time()
        
        # Ajouter à la file d'attente des mises à jour
        if entity.id not in self.entity_updates_queue:
            self.entity_updates_queue[entity.id] = []
        
        return entity
    
    def has_authority(self, entity_id, player_id) -> bool:
        """Vérifie si un joueur a l'autorité pour modifier une entité."""
        # Vérifier d'abord dans le cache
        cache_key = f"{entity_id}:{player_id}"
        if cache_key in self.authority_cache:
            return self.authority_cache[cache_key]
            
        entity = self.game_map.get_entity_by_id(entity_id)
        if not entity:
            return False
            
        result = False
        if hasattr(entity, 'can_be_modified_by'):
            result = entity.can_be_modified_by(player_id)
        else:
            # Vérifier directement la propriété network_owner ou la team
            network_owner = getattr(entity, 'network_owner', entity.team)
            result = network_owner == player_id
        
        # Mettre en cache le résultat
        self.authority_cache[cache_key] = result
        return result
    
    def queue_update(self, entity_id, update_type, data):
        """Ajoute une mise à jour à la file d'attente pour une entité."""
        if entity_id not in self.entity_updates_queue:
            self.entity_updates_queue[entity_id] = []
            
        # Ajouter la mise à jour avec un timestamp
        update_data = {
            "type": update_type,
            "data": data,
            "timestamp": time.time()
        }
        
        self.entity_updates_queue[entity_id].append(update_data)
        
    async def process_updates(self):
        """Traite les mises à jour en attente et les envoie au réseau."""
        if not self.network_manager:
            return
            
        # Traiter les mises à jour par entité
        for entity_id, updates in list(self.entity_updates_queue.items()):
            if not updates:
                continue
                
            entity = self.game_map.get_entity_by_id(entity_id)
            if not entity:
                # L'entité n'existe plus, supprimer de la file
                del self.entity_updates_queue[entity_id]
                continue
            
            # Prendre la mise à jour la plus récente
            update = updates.pop()
            
            # Si c'est pour synchroniser l'état complet
            if update["type"] == "sync_state":
                await self.send_entity_state(entity)
            # Autres types de mises à jour spécifiques
            elif update["type"] == "position":
                await self.send_entity_position(entity, update["data"])
            elif update["type"] == "hp":
                await self.send_entity_hp(entity, update["data"])
        
        # Vérifier s'il faut faire une synchronisation complète
        current_time = time.time()
        if current_time - self.last_sync_time > self.sync_interval:
            await self.send_full_sync()
            self.last_sync_time = current_time
    
    async def send_entity_state(self, entity):
        """Envoie l'état complet d'une entité au réseau."""
        if not self.network_manager:
            return
            
        entity_data = entity.to_network_dict()
        message = {
            "entity_state": entity_data,
            "timestamp": time.time(),
        }
        
        await self.network_manager.send_message(message)
    
    async def send_entity_position(self, entity, position_data):
        """Envoie uniquement la mise à jour de position d'une entité."""
        if not self.network_manager:
            return
            
        message = {
            "entity_position": {
                "id": entity.id,
                "position": position_data,
                "timestamp": time.time(),
            }
        }
        
        await self.network_manager.send_message(message)
    
    async def send_entity_hp(self, entity, hp_data):
        """Envoie uniquement la mise à jour de HP d'une entité."""
        if not self.network_manager:
            return
            
        message = {
            "entity_hp": {
                "id": entity.id,
                "hp": hp_data,
                "timestamp": time.time(),
            }
        }
        
        await self.network_manager.send_message(message)
    
    async def send_full_sync(self):
        """Envoie une synchronisation complète des entités dont nous sommes propriétaires."""
        if not self.network_manager:
            return
        
        # Collecter toutes les entités du jeu
        entities_data = {}
        for entity_id, entity in self.game_map.get_all_entities().items():
            # Ne synchroniser que les entités dont nous sommes propriétaires
            if hasattr(entity, 'network_owner') and entity.network_owner == self.game_map.local_player_id:
                entities_data[entity_id] = entity.to_network_dict()
        
        message = {
            "full_sync": {
                "entities": entities_data,
                "timestamp": time.time()
            }
        }
        
        await self.network_manager.send_message(message)
    
    def apply_entity_update(self, entity_id, update_data):
        """Applique une mise à jour reçue du réseau à une entité locale."""
        entity = self.game_map.get_entity_by_id(entity_id)
        if not entity:
            return False
        
        # Vérifier si la mise à jour est plus récente que l'état actuel
        if update_data.get("timestamp", 0) <= getattr(entity, "last_sync_time", 0):
            return False  # Ignorer les mises à jour trop anciennes
            
        # Fusionner les données
        if hasattr(entity, 'from_network_dict'):
            entity.from_network_dict(update_data)
            return True
        
        return False
