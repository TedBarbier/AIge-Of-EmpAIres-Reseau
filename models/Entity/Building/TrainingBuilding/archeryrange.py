from Entity.Building.TrainingBuilding.trainingbuilding import *
class ArcheryRange(TrainingBuilding):

    def __init__(self,id_gen, cell_Y, cell_X, position, team,representation = 'A', sq_size = 3, hp = 500, cost = {"gold":0,"wood":175,"food":0}, build_time = 50, trainable_units = ['a','m']):
        global ARCHERYRANGE_ARRAY_3D
        super().__init__(id_gen,cell_Y, cell_X, position, team,representation, sq_size, hp, cost, build_time, trainable_units)
