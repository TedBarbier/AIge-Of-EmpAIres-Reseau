import asyncio
import time

class PlayerUIController:
    """
    Contrôleur qui gère l'interaction entre l'interface utilisateur, les actions du joueur
    et la synchronisation réseau, assurant que les actions respectent les autorisations.
    """
    def __init__(self, player, entity_controller, network_manager=None):
        self.player = player
        self.entity_controller = entity_controller
        self.network_manager = network_manager
        self.pending_actions = []
        self.last_action_time = time.time()
        self.action_cooldown = 0.1  # Temps minimum entre les actions (secondes)
    
    def select_entity(self, entity_id):
        """Sélectionne une entité pour le joueur courant."""
        entity = self.player.linked_map.get_entity_by_id(entity_id)
        if not entity:
            return False
            
        # Les entités peuvent être sélectionnées même si on n'a pas l'autorité
        # pour les modifier (pour voir les informations)
        self.player.selected_entity_id = entity_id
        return True
    
    async def issue_command(self, command_type, target_entity_id=None, position=None, extra_data=None):
        """
        Émet une commande pour l'entité sélectionnée actuellement.
        Vérifie les autorisations et synchronise avec le réseau.
        """
        # Vérifier le cooldown entre les actions
        current_time = time.time()
        if current_time - self.last_action_time < self.action_cooldown:
            return False
            
        self.last_action_time = current_time
        
        # Vérifier si une entité est sélectionnée
        entity_id = self.player.selected_entity_id
        if not entity_id:
            return False
            
        # Vérifier si le joueur a l'autorité sur cette entité
        if not self.entity_controller.has_authority(entity_id, self.player.team):
            print(f"Pas d'autorité pour contrôler l'entité {entity_id}")
            return False
        
        # Obtenir l'entité
        entity = self.player.linked_map.get_entity_by_id(entity_id)
        if not entity:
            return False
        
        # Préparer les données de commande
        command_data = {
            "command": command_type,
            "entity_id": entity_id,
            "target_id": target_entity_id,
            "position": position,
            "extra": extra_data,
            "player_id": self.player.team,
            "timestamp": current_time
        }
        
        # Exécuter la commande localement en utilisant les méthodes existantes
        success = self._execute_command(entity, command_data)
        
        # Si la commande réussit, l'envoyer sur le réseau
        if success and self.network_manager:
            message = {
                "command": command_data
            }
            await self.network_manager.send_message(message)
            
            # Mettre à jour l'état de l'entité pour la synchronisation
            self.entity_controller.queue_update(entity_id, "sync_state", None)
        
        return success
    
    def _execute_command(self, entity, command_data):
        """Exécute une commande sur une entité en utilisant les méthodes existantes."""
        command_type = command_data["command"]
        target_id = command_data.get("target_id")
        position = command_data.get("position")
        extra = command_data.get("extra", {})
        
        try:
            # Utiliser les méthodes existantes des entités
            if command_type == "move":
                if hasattr(entity, "set_move_target"):
                    entity.set_move_target(position.x, position.y)
                    return True
                    
            elif command_type == "attack":
                if hasattr(entity, "set_attack_target"):
                    target = self.player.linked_map.get_entity_by_id(target_id)
                    if target:
                        entity.set_attack_target(target_id)
                        return True
                        
            elif command_type == "build":
                if hasattr(entity, "set_build_target"):
                    building_type = extra.get("building_type")
                    if building_type:
                        # Utiliser la méthode build_entity du joueur
                        result = self.player.build_entity([entity.id], building_type)
                        return isinstance(result, tuple) and result[0] != "error"
                        
            elif command_type == "train":
                if hasattr(entity, "train_unit"):
                    unit_type = extra.get("unit_type")
                    if unit_type:
                        result = entity.train_unit(self.player, unit_type)
                        return result not in [1, 2, 3, 4]  # Codes d'erreur
                        
            elif command_type == "gather":
                if hasattr(entity, "set_resource_target"):
                    entity.set_resource_target(target_id)
                    return True
                    
            elif command_type == "drop_off":
                if hasattr(entity, "set_drop_target"):
                    entity.set_drop_target(target_id)
                    return True
                    
        except Exception as e:
            print(f"Erreur lors de l'exécution de la commande {command_type}: {e}")
        
        return False
    
    async def receive_command(self, command_data):
        """Reçoit et exécute une commande provenant du réseau."""
        # Vérifier que la commande est destinée à une entité que nous gérons
        entity_id = command_data.get("entity_id")
        if not entity_id:
            return False
        
        entity = self.player.linked_map.get_entity_by_id(entity_id)
        if not entity:
            return False
        
        # Si ce n'est pas notre entité ou si nous ne sommes pas le propriétaire réseau, refuser
        if entity.team != self.player.team:
            network_owner = getattr(entity, "network_owner", None)
            if network_owner != command_data.get("player_id"):
                print(f"Rejet de commande: entité {entity_id} n'appartient pas au joueur {command_data.get('player_id')}")
                return False
        
        # Exécuter la commande
        return self._execute_command(entity, command_data)
