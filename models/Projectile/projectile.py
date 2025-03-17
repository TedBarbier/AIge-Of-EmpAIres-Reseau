from GLOBAL_VAR import *
from math import floor


class Projectile:
    
    def __init__(self, cell_Y, cell_X, position, entity_target, _map, team, damage, representation = 'p', element =""):

        self.cell_Y = cell_Y
        self.cell_X = cell_X

        self.position = position 
        self.team = team
        self.damage = damage
        self.entity_target = entity_target
        self.reached_target = False
        self.element = element
        self.distance_left = self.position.abs_distance(entity_target.position)
        self.time_to_get_target = (ONE_SEC/5.3) * self.distance_left/_map.tile_size_2d

        self.time_left = self.time_to_get_target
        self.direction = self.position.alpha_angle(entity_target.position)

        self.image = None
        self.animation_time_acc = 0
        self.animation_direction = MAP_ANGLE_INDEX(self.direction, PROJECTILE_ANGLE_MAPPING)
        self.animation_frame = 0

        self.projectile_peak = self.position.abs_distance(entity_target.position)
        self.representation = representation

        self.linked_map = _map

    def update_event(self, dt):
        
        
        self.update_cell_on_map()
        if dt > 0:
            
            # Calculate the angle to the target
            if (self.entity_target):
                
                if (self.position == self.entity_target.position and not(self.entity_target.is_dead())):

                    self.reached_target = True
                    self.entity_target.hp -= self.damage
                    if self.entity_target.is_dead():
                        if self.entity_target.representation in ['C','T','v']:
                            if self.entity_target.state != STATES.get(self.entity_target.representation, None).get("dying", None):
                                resources = {}
                                if self.entity_target.representation == 'v':
                                    resources = self.entity_target.resources
                                else:
                                    resources = self.entity_target.storage.lose_resource()
                                player_gained = self.linked_map.players_dict.get(self.team,None)
                                if player_gained:
                                    player_gained.add_resources(resources)

                        self.linked_map.dead_entities[self.entity_target.id] = self.entity_target
                        self.entity_target.change_state(STATES.get(self.entity_target.representation, None).get("dying", None))

                elif not(self.entity_target.is_dead()):

                    self.direction = self.position.alpha_angle(self.entity_target.position)
                    self.distance_left = self.position.abs_distance(self.entity_target.position)
                else:
                    self.reached_target = True

                if self.time_left > 0 and not(self.reached_target):
                    distance_to_add = self.distance_left / (self.time_left / dt)
                    self.position.x = self.position.x + math.cos(self.direction) * distance_to_add 
                    self.position.y = self.position.y + math.sin(self.direction) * distance_to_add
                    

                    progress_ratio = (self.time_to_get_target - self.time_left)/self.time_to_get_target
                    # f(x) = -a*(x**(b) - 0.5)**2 + peak , the function that returns the value of z where x is the ratio, lets find a 
                    # or f(x) = peak*(sqrt(1 - (x-0.5)**2/0.25))
                    a = self.projectile_peak/(0.5)**2
                    b = 2 
                    # f(progress_ratio)
                    self.position.z = -a*((progress_ratio)**(b) - 0.5)**2 + self.projectile_peak
                    
                    #self.position.z = self.projectile_peak * math.sqrt(1 - (progress_ratio - 0.5)**2 / 0.25)
                    
                    self.time_left -= dt
                    self.distance_left = - self.distance_left - distance_to_add
                else:
                    distance_to_add = self.distance_left   

                    self.position.x = self.position.x + math.cos(self.direction) * distance_to_add 
                    self.position.y = self.position.y + math.sin(self.direction) * distance_to_add
            else:
                self.reached_target = True 
    def update_cell_on_map(self):
        if self.changed_cell_position():
            
            self.change_cell_on_map()
    
    def is_in_region(self, reg_Y, reg_X):
        return self.cell_Y//self.linked_map.region_division == reg_Y and \
                self.cell_X//self.linked_map.region_division == reg_X
    
    def changed_cell_position(self):
        topleft = PVector2(self.cell_X*self.linked_map.tile_size_2d, self.cell_Y*self.linked_map.tile_size_2d)
        bottomright = PVector2((self.cell_X + 1)*self.linked_map.tile_size_2d, (self.cell_Y + 1)*self.linked_map.tile_size_2d)

        return not(self.position < bottomright and self.position > topleft)

    def change_cell_on_map(self): # to change the cell position on the map 
        live_cell_X = int(floor(self.position.x//self.linked_map.tile_size_2d))
        live_cell_Y = int(floor(self.position.y//self.linked_map.tile_size_2d))

        self.cell_Y = live_cell_Y
        self.cell_X = live_cell_X

    
    def update_animation_frame(self, dt):
        self.animation_time_acc += dt
        if self.animation_time_acc > self.time_to_get_target/10:
            self.animation_time_acc = 0
            self.animation_frame = (self.animation_frame + 1)%len(SPRITES.get(self.representation, None).get(0,None))
        
    def display(self, dt, screen, camera, g_width, g_height):
        
        self.update_animation_frame(dt)
        iso_x, iso_y = camera.convert_to_isometric_3d(self.position.x, self.position.y, self.position.z)
        display_image(META_SPRITES_CACHE_HANDLE(camera.zoom, list_keys = [self.representation, self.animation_direction, self.animation_frame], camera = camera),iso_x, iso_y, screen, 0x04)
        if self.element != "":
            display_image(META_SPRITES_CACHE_HANDLE(camera.zoom, list_keys = [self.element + self.representation, self.animation_direction, self.animation_frame], camera = camera),iso_x, iso_y, screen, 0x04)

    def save(self):

        data_to_save = {}
        current_data_to_save = None

        for attr_name, attr_value in self.__dict__.items():

            if hasattr(attr_value, "save"):
                current_data_to_save = attr_value.save()
            else:
                current_data_to_save = attr_value

            data_to_save[attr_name] = current_data_to_save

        return data_to_save
    
    @classmethod
    def load(cls, data_to_load):
        global SAVE_MAPPING
        instance = cls.__new__(cls) # skip the __init__()
        current_attr_value = None
        for attr_name, attr_value in data_to_load.items():
            
            if (isinstance(attr_value, dict)): # has the attribute representation then we will see
                
                ClassLoad = SAVE_MAPPING.get(attr_value.get("element", None) + attr_value.get("representation", None), None)
                if (ClassLoad): # has a load method in the method specified in it
                    
                    current_attr_value = ClassLoad.load(attr_value)
                else:
                    current_attr_value = attr_value
            else:
                current_attr_value = attr_value
        
            setattr(instance, attr_name, current_attr_value)

        return instance
    
    def __str__(self):
        return f"Y:{self.cell_Y}, X:{self.cell_X}, reached:{self.reached_target}"