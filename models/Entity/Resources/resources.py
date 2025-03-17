from Entity.entity import *
from GLOBAL_VAR import *
from idgen import *
#from AITools.player import *

class Resources(Entity):

    def __init__(self, id_gen, cell_Y, cell_X, position, representation, storage_capacity, resource_indicator, team = 0):
        super().__init__(id_gen,cell_Y, cell_X, position, team, representation)
        self.resources = None
        self.resource_indicator = resource_indicator
        self.max_storage = storage_capacity
        self.display_choice = 0
        self.linked_map = None
        self.HitboxClass = "RoundedSquare"
    def display(self, dt, screen, camera, g_width, g_height):
        iso_x, iso_y = camera.convert_to_isometric_2d(self.position.x, self.position.y)
        #camera.draw_box(screen, self)
        #if (camera.check_in_point_of_view(iso_x, iso_y, g_width, g_height)):
        display_image(META_SPRITES_CACHE_HANDLE(camera.zoom, list_keys = [self.representation, self.display_choice],camera = camera), iso_x, iso_y, screen, 0x04)
        draw_percentage_bar(screen, camera, iso_x, iso_y, self.resources.get(self.resource_indicator, None), self.max_storage, self.sq_size)

    def is_dead(self):
        return self.resources[self.resource_indicator] <= 0
    
    def remove_resources(self, amount):
        
        self.resources[self.resource_indicator] -= amount

        return amount

def get_resource_html(self):
        return f'<li class="resource">f"{self.dict_repr.get(self.representation)} : {self.position}</li>'