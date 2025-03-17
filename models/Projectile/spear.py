from Projectile.projectile import *

class Spear(Projectile):

    def __init__(self, cell_Y, cell_X, position, entity_target, _map, team,  damage = 4, representation = 'ps', element = ""):
        super().__init__(cell_Y, cell_X, position, entity_target,_map, team, damage, representation = representation, element = element)
        self.projectile_peak = self.projectile_peak/3
