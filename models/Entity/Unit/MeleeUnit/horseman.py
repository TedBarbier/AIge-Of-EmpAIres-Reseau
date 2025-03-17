from Entity.Unit.MeleeUnit.meleeunit import *
class HorseMan(MeleeUnit):

    def __init__(self,id_gen, cell_Y, cell_X, position, team, representation = 'h', hp = 45, cost = {"gold":20, "wood":0, "food":80}, training_time = 30, speed = 1.2, attack = 4, attack_speed = 1):
        global HORSEMAN_ARRAY_3D
        super().__init__(id_gen,cell_X, cell_Y, position, team, representation, hp, cost, training_time, speed, attack, attack_speed)
        self.animation_speed = [45,55,30,45]
        self.attack_frame = 18
        self.adapte_attack_delta_time()