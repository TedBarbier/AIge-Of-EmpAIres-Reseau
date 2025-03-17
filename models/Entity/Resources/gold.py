from Entity.Resources.resources import *
class Gold(Resources):
    def __init__(self,id_gen, cell_Y, cell_X, position, representation = 'G', storage = GOLD_CAPACITY, resource_indicator = "gold"):
        super().__init__(id_gen,cell_Y, cell_X, position, representation, storage, resource_indicator)
        self.resources = {"gold":storage}
        self.display_choice = random.randint(0, len(GOLD_ARRAY_1D) - 1)
