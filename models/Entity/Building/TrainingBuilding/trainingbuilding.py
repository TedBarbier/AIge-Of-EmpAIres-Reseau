from Entity.Building.building import *
from Entity.Unit.MeleeUnit.horseman import HorseMan
from Entity.Unit.MeleeUnit.villager import Villager
from Entity.Unit.MeleeUnit.swordman import SwordMan
from Entity.Unit.RangedUnit.archer import Archer
from Entity.Unit.RangedUnit.cavalryarcher import CavalryArcher
from Entity.Unit.MeleeUnit.axeman import AxeMan
from Entity.Unit.RangedUnit.spearman import SpearMan

TRAINABLE_UNITS = {
    "h":HorseMan,
    "v":Villager,
    "a":Archer,
    "s":SwordMan,
    "x":AxeMan,
    "m":SpearMan,
    "c":CavalryArcher
}



class TrainingBuilding(Building):

    def __init__(self, id_gen,cell_Y, cell_X, position, team,representation, sq_size, hp, cost, build_time, trainable_units):
        super().__init__(id_gen,cell_Y, cell_X, position, team,representation, sq_size, hp, cost, build_time)
        self.trainable_units = trainable_units

        self.time_left = None
        
        self.unit_being_trained = None


    def try_to_train(self, dt):
        
        if self.time_left != None and self.unit_being_trained:# if not None
            
            if self.time_left > (1e-5):
                
                self.time_left = self.time_left - dt
            else:
                
                if self.unit_being_trained:
                    
                    self.linked_map.add_entity_to_closest(self.unit_being_trained, self.cell_Y, self.cell_X)

                    self.unit_being_trained = None
                    self.time_left = None



    def train_unit(self, player, entity_repr):
        if self.state == BUILDING_ACTIVE:
            if self.unit_being_trained == None:
                if entity_repr in self.trainable_units:
                    UnitClass = TRAINABLE_UNITS.get(entity_repr, None)
                    unit = UnitClass(self.linked_map.id_generator, None, None, None, player.team)

                    if unit.affordable_by(player.get_current_resources()):
                        if player.get_current_population_capacity() > player.current_population:
                            player.remove_resources(unit.cost)
                            player.add_population()
                            player.current_population += 1
                            self.unit_being_trained = unit

                            self.time_left = self.unit_being_trained.training_time * ONE_SEC
                    else:
                        self.linked_map.id_generator.free_ticket(unit.id)
                        return TRAIN_NOT_AFFORDABLE
                else:
                    return TRAIN_NOT_FOUND_UNIT
            else:
                return TRAIN_BUSY
        else:
            return TRAIN_NOT_ACTIVE
                    
            
    def display(self, dt, screen, camera, g_width, g_height):
        super().display(dt, screen, camera, g_width, g_height)
        if self.unit_being_trained:
            iso_x, iso_y = camera.convert_to_isometric_2d(self.position.x - self.linked_map.tile_size_2d/2, self.position.y - self.linked_map.tile_size_2d/2)
            draw_percentage_bar(screen, camera, iso_x, iso_y, self.unit_being_trained.training_time - self.time_left/ONE_SEC, self.unit_being_trained.training_time, self.sq_size)
            display_image(META_SPRITES_CACHE_HANDLE(camera.zoom, list_keys = [self.unit_being_trained.representation + "i"], camera = camera), iso_x, iso_y, screen, 0x04, 1)


    def update(self, dt, camera=None, screen=None):
        super().update(dt, camera, screen)
        self.try_to_train(dt)

    def is_free(self):
        return self.unit_being_trained == None and self.time_left == None

