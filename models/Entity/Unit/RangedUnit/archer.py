from Entity.Unit.RangedUnit.rangedunit import *
from Projectile.arrow import *

class Archer(RangedUnit):

    def __init__(self,id_gen, cell_Y, cell_X, position, team, representation = 'a', hp = 30, cost = {"gold":45,"wood":25,"food":0}, training_time = 5, speed = 1, attack = 4, attack_speed = 1.2, _range = 5, _projectile_type = "pa"):
        super().__init__(id_gen,cell_Y, cell_X, position, team, representation, hp, cost, training_time, speed, attack, attack_speed, _range, _projectile_type)
        self.last_time_sent_arrow = pygame.time.get_ticks()
        self.projetctile_padding = TILE_SIZE_2D/2
        self.animation_speed = [60,30,30,30]
        self.attack_frame = 17
        self.adapte_attack_delta_time()

        
        
   