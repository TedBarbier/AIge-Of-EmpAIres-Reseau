from Entity.Building.building import *
class Farm(Building):

    def __init__(self,id_gen,cell_Y, cell_X, position, team,representation = 'F', sq_size = 2, hp = 100, cost = {"gold":0,"wood":60,"food":0}, build_time = 50, storage_capacity = FARM_CAPACITY, resource_indicator = "food"):
        super().__init__(id_gen,cell_Y, cell_X, position, team,representation, sq_size, hp, cost, build_time, walkable = True)
        self.resource_indicator = resource_indicator
        self.max_storage = storage_capacity 
        self.resources = {resource_indicator:storage_capacity}

    def remove_resources(self, amount):

        self.resources[self.resource_indicator] -= amount

        return amount

    def is_empty(self):
        return self.resources[self.resource_indicator] <= 0

    def display(self, dt, screen, camera, g_width, g_height):
        super().display(dt, screen, camera, g_width, g_height)
    
        iso_x, iso_y = camera.convert_to_isometric_2d(self.position.x - self.linked_map.tile_size_2d/2, self.position.y - self.linked_map.tile_size_2d/2)
        if self.state == BUILDING_ACTIVE:
            draw_percentage_bar(screen, camera, iso_x, iso_y, self.resources[self.resource_indicator], self.max_storage, self.sq_size)
        #display_image(META_SPRITES_CACHE_HANDLE(camera.zoom, list_keys = ["Mi"], camera = camera), iso_x, iso_y, screen, 0x04, 1)

