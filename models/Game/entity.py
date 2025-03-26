# Ajouter ces attributs et méthodes à la classe Entity
import time
class Entity:
    # ...existing code...
    
    def __init__(self, id, cell_Y, cell_X, position, team):
        # ...existing code...
        
        # Propriétés réseau
        self.network_owner = team  # Par défaut, le propriétaire réseau est l'équipe de l'entité
        self.last_sync_time = time.time()  # Timestamp de la dernière synchronisation
    
    # ...existing code...
    
    def can_be_modified_by(self, player_id):
        """Vérifie si le joueur a l'autorité pour modifier cette entité."""
        # Si l'entité a un propriétaire réseau défini, vérifier que c'est ce joueur
        if hasattr(self, 'network_owner'):
            return self.network_owner == player_id
        
        # Sinon, vérifier que l'entité appartient au joueur (équipe)
        return self.team == player_id
    
    def to_network_dict(self):
        """Convertit l'entité en dictionnaire pour la synchronisation réseau."""
        entity_dict = {
            "id": self.id,
            "type": self.__class__.__name__,
            "team": self.team,
            "position": {
                "x": self.position.x if hasattr(self, 'position') else None,
                "y": self.position.y if hasattr(self, 'position') else None
            },
            "cell": {
                "x": self.cell_X,
                "y": self.cell_Y
            },
            "network_owner": getattr(self, 'network_owner', self.team),
            "last_sync": time.time()
        }
        
        # Ajouter d'autres propriétés si elles existent
        if hasattr(self, 'hp'):
            entity_dict["hp"] = self.hp
            
        if hasattr(self, 'target'):
            entity_dict["target"] = self.target
            
        if hasattr(self, 'state'):
            entity_dict["state"] = self.state
            
        if hasattr(self, 'resources'):
            entity_dict["resources"] = self.resources
            
        return entity_dict
    
    def from_network_dict(self, entity_dict):
        """Met à jour l'entité à partir d'un dictionnaire réseau."""
        # Mettre à jour les propriétés de base
        if 'position' in entity_dict and hasattr(self, 'position'):
            if entity_dict['position']['x'] is not None:
                self.position.x = entity_dict['position']['x']
            if entity_dict['position']['y'] is not None:
                self.position.y = entity_dict['position']['y']
                
        # Mettre à jour la cellule
        if 'cell' in entity_dict:
            if entity_dict['cell']['x'] is not None:
                self.cell_X = entity_dict['cell']['x']
            if entity_dict['cell']['y'] is not None:
                self.cell_Y = entity_dict['cell']['y']
                
        # Mettre à jour les autres propriétés si elles existent
        if hasattr(self, 'hp') and 'hp' in entity_dict:
            self.hp = entity_dict['hp']
            
        if hasattr(self, 'target') and 'target' in entity_dict:
            self.target = entity_dict['target']
            
        if hasattr(self, 'state') and 'state' in entity_dict:
            self.state = entity_dict['state']
            
        if hasattr(self, 'resources') and 'resources' in entity_dict:
            self.resources = entity_dict['resources']
            
        # Mettre à jour les propriétés réseau
        self.network_owner = entity_dict.get('network_owner', self.team)
        self.last_sync_time = entity_dict.get('last_sync', time.time())