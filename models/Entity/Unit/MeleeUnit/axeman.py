from Entity.Unit.MeleeUnit.meleeunit import *
class AxeMan(MeleeUnit):

    def __init__(self,id_gen, cell_Y, cell_X, position, team, representation = 'x', hp = 60, cost = {"gold":25, "wood":0, "food":80}, training_time = 14, speed = 0.8, attack = 11, attack_speed = 2):
        global AXEMAN_ARRAY_3D
        super().__init__(id_gen,cell_X, cell_Y, position, team, representation, hp, cost, training_time, speed, attack, attack_speed)
        self.animation_speed = [60,30,30,30]
        self.attack_frame = 19
        self.adapte_attack_delta_time()