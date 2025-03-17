from Projectile.spear import *

class FireSpear(Spear):

    def __init__(self, cell_Y, cell_X, position, entity_target, _map,team,  damage = 4, representation = 'ps', element = "f"):

        super().__init__(cell_Y, cell_X, position, entity_target,_map, team, damage, representation = representation, element = element)
