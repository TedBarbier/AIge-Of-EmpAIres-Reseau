from Entity.Resources.resources import *
class Tree(Resources):
    
    def __init__(self, id_gen,cell_Y, cell_X, position, representation = 'W', storage= TREE_CAPACITY, resource_indicator = "wood"):
        super().__init__(id_gen,cell_Y, cell_X, position, representation, storage, resource_indicator)
        self.resources = {"wood":storage}
        self.display_choice = random.randint(0,len(TREES_ARRAY_1D) - 1)
