from Projectile.arrow import *

class FireArrow(Arrow):

    def __init__(self, cell_Y, cell_X, position, entity_target, _map,team,  damage = 4, representation = 'pa', element = "f"):

        super().__init__(cell_Y, cell_X, position, entity_target,_map, team, damage, representation , element)
