from Entity.Building.building import *
from habitat import *
class House(Building):

    def __init__(self,id_gen, cell_Y, cell_X, position, team,representation = 'H', sq_size = 2, hp = 200, cost = {"gold":0,"wood":25,"food":0}, build_time = 25):
        global HOUSES_ARRAY_3D
        super().__init__(id_gen,cell_Y, cell_X, position, team,representation, sq_size, hp, cost, build_time)
        self.habitat = Habitat(5)
        self.display_choice = random.randint(0, len(HOUSES_ARRAY_3D) - 1)
    
    def display(self, dt, screen, camera, g_width, g_height):
        super().display(dt, screen, camera, g_width, g_height)
        if self.state == BUILDING_ACTIVE:
            pro_iso_x, pro_iso_y = camera.convert_to_isometric_2d(self.position.x + self.linked_map.tile_size_2d/3, self.position.y + self.linked_map.tile_size_2d/3)
            draw_text(str(self.habitat.current_population),pro_iso_x, pro_iso_y, screen, int(camera.zoom * camera.img_scale*20))
        
