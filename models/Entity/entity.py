from GLOBAL_VAR import *
from idgen import *
#from AITools.player import *
from shapely.geometry import Point, Polygon
import math
from shape import *
import json

class Entity():
    def __init__(self, id_gen, cell_Y, cell_X, position, team, representation, sq_size = 1,id = None):
        self.cell_Y = cell_Y
        self.cell_X = cell_X
        self.position = position
        self.team = team
        self.representation = representation
        if id:
            self.id = id
        else:
            self.id = id_gen.give_ticket()
        self.sq_size = sq_size
        self.image = None
        self.dict_repr = {
            'wood':"Wood",
            'gold':"Gold",
            'food':"Food",
            'v':"Villager",
            's':"Swordsman",
            'h':"Horseman",
            'a':"Archer",
            'am':"AxeMan",
            'ca':"CavalryArcher",
            'sm':"SpearMan",
            'T':"TownCenter",
            'H':"House",
            'C':"Camp",
            'F':"Farm",
            'B':"Barracks",
            'S':"Stable",
            'A':"ArcheryRange",
            'K':"Keep"
            }

        self.box_size = None
        self.HitboxClass = None
        self.walkable = False
        
    def __repr__(self):
        return f"ent<{self.id},{self.representation},Y:{self.cell_Y},X:{self.cell_X},sz:{self.sq_size}>"
    
    def collide_with_shape(self, shape):
        Class = SHAPE_MAPPING.get(self.HitboxClass, None)

        shape_self = Class(self.position.x, self.position.y, self.box_size)

        return shape_self.collide_with(shape)
    
    def collide_with_entity(self, entity):
        Class = SHAPE_MAPPING.get(self.HitboxClass, None)
        shape_self = Class(self.position.x, self.position.y, self.box_size)

        entClass = SHAPE_MAPPING.get(entity.HitboxClass, None)
        ent_shape = entClass(entity.position.x, entity.position.y, entity.box_size)
        
        Status = False
  
        if shape_self.collide_with(ent_shape):
            Status = True
        # i wrote it like this on purpose incase there is some future update
        return Status

    def update(self, dt, camera = None, screen = None):
        return None

    def is_free(self):
        return True
    
    """Méthodes de conversion pour transmission réseau"""    
    def to_network_dict(self):
        """Convertit l'entité en dictionnaire pour transmission réseau"""
        entity_data = {
            "id": self.id,
            # "type": self.__class__.__name__,
            "representation": self.representation,
            "team": self.team,
            "cell_X": self.cell_X,
            "cell_Y": self.cell_Y,
            "sq_size": self.sq_size
            # "walkable": self.walkable
        }
        
        # Ajout de la position si elle existe
        if self.position:
            entity_data["position"] = {
                "x": self.position.x,
                "y": self.position.y
            }
            
        # Ajout des propriétés spécifiques aux sous-classes
        if hasattr(self, "hp"):
            entity_data["hp"] = self.hp
            # entity_data["max_hp"] = self.max_hp if hasattr(self, "max_hp") else self.hp
            
        # if hasattr(self, "state"):
        #     entity_data["state"] = self.state
        
        # if hasattr(self, "animation_frame"):
        #     entity_data["animation_frame"] = self.animation_frame
            
        #  if hasattr(self, "animation_direction"):
        #      entity_data["animation_direction"] = self.animation_direction
        
        
        return entity_data
    
    def from_network_dict(self, data):
        """Met à jour l'entité à partir d'un dictionnaire reçu du réseau"""
        # Mise à jour des attributs de base
        if "cell_X" in data:
            self.cell_X = data["cell_X"]
            
        if "cell_Y" in data:
            self.cell_Y = data["cell_Y"]
            
        if "team" in data:
            self.team = data["team"]
            
        if "sq_size" in data:
            self.sq_size = data["sq_size"]
            
        if "walkable" in data:
            self.walkable = data["walkable"]
        
        # Mise à jour de la position
        if "position" in data and self.position:
            self.position.x = data["position"]["x"]
            self.position.y = data["position"]["y"]
            
        # Mise à jour des attributs spécifiques
        if hasattr(self, "hp") and "hp" in data:
            self.hp = data["hp"]
            
        if hasattr(self, "state") and "state" in data:
            self.state = data["state"]
            
        if hasattr(self, "animation_frame") and "animation_frame" in data:
            self.animation_frame = data["animation_frame"]
            
        if hasattr(self, "animation_direction") and "animation_direction" in data:
            self.animation_direction = data["animation_direction"]
            
    def to_network_json(self):
        """Convertit l'entité en JSON pour transmission réseau"""
        return json.dumps(self.to_network_dict())
        
    @classmethod
    def from_network_json(cls, json_data, id_gen, game_map=None):
        """Crée une entité à partir de données JSON"""
        from GLOBAL_IMPORT import CLASS_MAPPING  # Import ici pour éviter les imports circulaires
        
        data = json.loads(json_data) if isinstance(json_data, str) else json_data
        
        # Récupérer la classe correspondant au type d'entité
        entity_repr = data.get("representation")
        
        if entity_repr in CLASS_MAPPING:
            EntityClass = CLASS_MAPPING[entity_repr]
            
            # Création de l'entité
            position_data = data.get("position", {"x": 0, "y": 0})
            from pvector2 import PVector2  # Import ici pour éviter les imports circulaires
            position = PVector2(position_data["x"], position_data["y"])
            
            # Créer l'instance avec les paramètres minimaux
            entity = EntityClass(
                id_gen=id_gen,
                cell_Y=data.get("cell_Y", 0),
                cell_X=data.get("cell_X", 0),
                position=position,
                team=data.get("team", 0),
                id=data.get("id")
            )
            
            # Mettre à jour avec les données réseau
            entity.from_network_dict(data)
            
            # Associer au game_map si fourni
            if game_map:
                entity.linked_map = game_map
                
            return entity
        
        return None