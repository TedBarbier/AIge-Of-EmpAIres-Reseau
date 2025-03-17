from Entity.Building.TrainingBuilding.trainingbuilding import *
from storage import *
from habitat import *
class TownCenter(TrainingBuilding):

    def __init__(self, id_gen,cell_Y, cell_X, position, team, representation = 'T', sq_size = 4, hp = 1000, cost = {"gold":0,"wood":350,"food":0}, build_time = 150, trainable_units = ['v']):
        
        super().__init__(id_gen,cell_Y, cell_X, position, team, representation, sq_size, hp, cost, build_time, trainable_units)
        self.storage = Storage()
        self.habitat = Habitat(5)

    def display(self, dt, screen, camera, g_width, g_height):
        super().display(dt, screen, camera, g_width, g_height)
        
        if self.state == BUILDING_ACTIVE:
            pro_iso_x, pro_iso_y = camera.convert_to_isometric_2d(self.position.x + self.linked_map.tile_size_2d/3, self.position.y + self.linked_map.tile_size_2d/3)
            draw_text(str(self.habitat.current_population),pro_iso_x, pro_iso_y, screen, int(camera.zoom * camera.img_scale*20))
            tile_size_2d = self.linked_map.tile_size_2d
            wood_iso_x, wood_iso_y = camera.convert_to_isometric_2d(self.position.x - tile_size_2d/2, self.position.y - tile_size_2d/2)
            gold_iso_x, gold_iso_y= camera.convert_to_isometric_2d(self.position.x, self.position.y - tile_size_2d)
            food_iso_x, food_iso_y = camera.convert_to_isometric_2d(self.position.x - tile_size_2d, self.position.y)

            display_image(META_SPRITES_CACHE_HANDLE(camera.zoom, list_keys = ["Gi"], camera = camera), gold_iso_x, gold_iso_y, screen, 0x04, 1)
            display_image(META_SPRITES_CACHE_HANDLE(camera.zoom, list_keys = ["Wi"], camera = camera), wood_iso_x, wood_iso_y, screen, 0x04, 1)
            display_image(META_SPRITES_CACHE_HANDLE(camera.zoom, list_keys = ["Mi"], camera = camera), food_iso_x, food_iso_y, screen, 0x04, 1)
            
            draw_text(str(self.storage.resources["gold"]),gold_iso_x, gold_iso_y, screen, int(camera.zoom * camera.img_scale*20))
            draw_text(str(self.storage.resources["wood"]),wood_iso_x, wood_iso_y, screen, int(camera.zoom * camera.img_scale*20))
            draw_text(str(self.storage.resources["food"]),food_iso_x, food_iso_y, screen, int(camera.zoom * camera.img_scale*20))
        
