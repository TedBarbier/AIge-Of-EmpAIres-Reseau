from Entity.Building.building import *
from storage import *

class Camp(Building):

    def __init__(self,id_gen, cell_Y, cell_X, position, team,representation = 'C', sq_size = 2, hp = 200, cost = {"gold":0,"wood":100,"food":0}, build_time = 25):
        global CAMP_ARRAY_3D
        super().__init__(id_gen,cell_Y, cell_X, position, team,representation, sq_size, hp, cost, build_time)
        self.storage = Storage()

    def display(self, dt, screen, camera, g_width, g_height):
        super().display(dt, screen, camera, g_width, g_height)
        tile_size_2d = self.linked_map.tile_size_2d
        wood_iso_x, wood_iso_y = camera.convert_to_isometric_2d(self.position.x - tile_size_2d/2, self.position.y - tile_size_2d/2)
        gold_iso_x, gold_iso_y= camera.convert_to_isometric_2d(self.position.x, self.position.y - tile_size_2d)
        food_iso_x, food_iso_y = camera.convert_to_isometric_2d(self.position.x - tile_size_2d, self.position.y)

        if self.state == BUILDING_ACTIVE:
            display_image(META_SPRITES_CACHE_HANDLE(camera.zoom, list_keys = ["Gi"], camera = camera), gold_iso_x, gold_iso_y, screen, 0x04, 1)
            display_image(META_SPRITES_CACHE_HANDLE(camera.zoom, list_keys = ["Wi"], camera = camera), wood_iso_x, wood_iso_y, screen, 0x04, 1)
            display_image(META_SPRITES_CACHE_HANDLE(camera.zoom, list_keys = ["Mi"], camera = camera), food_iso_x, food_iso_y, screen, 0x04, 1)

            draw_text(str(self.storage.resources["gold"]),gold_iso_x, gold_iso_y, screen, int(camera.zoom * camera.img_scale*20))
            draw_text(str(self.storage.resources["wood"]),wood_iso_x, wood_iso_y, screen, int(camera.zoom * camera.img_scale*20))
            draw_text(str(self.storage.resources["food"]),food_iso_x, food_iso_y, screen, int(camera.zoom * camera.img_scale*20))
        
        