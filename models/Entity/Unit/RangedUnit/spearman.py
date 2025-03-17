from Entity.Unit.RangedUnit.rangedunit import *


class SpearMan(RangedUnit):

    def __init__(self,id_gen, cell_Y, cell_X, position, team, representation = 'm', hp = 35, cost = {"gold":0,"wood":35,"food":25}, training_time = 32, speed = 1, attack = 3, attack_speed = 0.5, _range = 5, _projectile_type = "fps"):
        super().__init__(id_gen,cell_Y, cell_X, position, team, representation, hp, cost, training_time, speed, attack, attack_speed, _range, _projectile_type)
        self.last_time_sent_arrow = pygame.time.get_ticks()
        self.projetctile_padding = TILE_SIZE_2D/2
        self.animation_speed = [60,30,45,30]
        self.attack_frame = 12
        self.adapte_attack_delta_time()

        
        
   