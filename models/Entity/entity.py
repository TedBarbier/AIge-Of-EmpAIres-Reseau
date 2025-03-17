from GLOBAL_VAR import *
from idgen import *
#from AITools.player import *
from shapely.geometry import Point, Polygon
import math
from shape import *

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