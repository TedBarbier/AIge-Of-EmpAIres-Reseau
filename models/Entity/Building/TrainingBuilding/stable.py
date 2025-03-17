from Entity.Building.TrainingBuilding.trainingbuilding import *

class Stable(TrainingBuilding):

    def __init__(self,id_gen, cell_Y, cell_X, position, team,representation = 'S', sq_size = 3, hp = 500, cost = {"gold":0,"wood":175,"food":0}, build_time = 50, trainable_units = ['h', 'c']):

        super().__init__(id_gen,cell_Y, cell_X, position, team,representation, sq_size, hp, cost, build_time, trainable_units)
        self.animation_frame= 0
        self.animation_speed = [27/2, 27/2, 20]

