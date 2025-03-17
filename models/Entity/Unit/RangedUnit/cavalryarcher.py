from Entity.Unit.RangedUnit.rangedunit import *


class CavalryArcher(RangedUnit):

    def __init__(self,id_gen, cell_Y, cell_X, position, team, representation = 'c', hp = 50, cost = {"gold":60,"wood":40,"food":0}, training_time = 34, speed = 1.4, attack = 6, attack_speed = 0.9, _range = 5.5, _projectile_type = "fpa"):
        super().__init__(id_gen,cell_Y, cell_X, position, team, representation, hp, cost, training_time, speed, attack, attack_speed, _range, _projectile_type)
        self.last_time_sent_arrow = pygame.time.get_ticks()
        self.projetctile_padding = TILE_SIZE_2D
        self.animation_speed = [45,60,45,45]
        self.attack_frame = 27
        self.adapte_attack_delta_time()

        
        
   