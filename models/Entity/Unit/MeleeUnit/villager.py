from Entity.Unit.MeleeUnit.meleeunit import *
from Entity.Building.farm import Farm

from Entity.Resources.resources import Resources

class Villager(MeleeUnit):

    def __init__(self,id_gen, cell_Y, cell_X, position, team, representation = 'v', hp = 25, cost = {"gold":0,"wood":0,"food":50}, training_time = 5, speed = 0.8, attack = 2, attack_speed= 1.4, collect_ratio_per_min = 25):
        super().__init__(id_gen,cell_Y, cell_X, position, team, representation, hp, cost, training_time, speed, attack, attack_speed)
        
        self.resources = {"gold":0, "wood":0, "food":0}

        self.resource_target_id = None 
        self.drop_target_id = None

        self.build_target_id = None
        
        self.collect_ratio_per_min = collect_ratio_per_min
        self.collect_capacity = 20

        self.collect_speed = 60/self.collect_ratio_per_min
        self.will_collect = False

        self.attack_frame = 27
        self.collect_frame = 26

        self.animation_speed = [60, 30, 60, 30, 60/self.collect_speed]
        self.adapte_attack_delta_time()
        
    def drop_gathered(self, entity):
        for resource, amount in self.resources.items():
            entity.storage.add_resource(resource, amount)
            self.resources[resource] = 0

    def try_to_drop(self, dt, camera, screen):
        if (self.state != UNIT_DYING and self.entity_defend_from_id == None):
            if self.drop_target_id != None:
                entity = self.linked_map.get_entity_by_id(self.drop_target_id)
                     
                if (entity != None): 
                    if (entity.team == self.team):
                        if (entity.is_dead() == False):
                            
                            if (entity.representation in ["C", "T"]):

                                if (self.collide_with_entity(entity)):
                                    
                                    self.drop_gathered(entity)
                                    self.drop_target_id = None
                                    if not(self.state == UNIT_IDLE):
                                        self.change_state(UNIT_IDLE)
                                    self.reset_task()
                                    
                                else:
                                    if not(self.state == UNIT_WALKING):
                                        self.change_state(UNIT_WALKING)

                                    self._entity_optional_target_id = entity.id

                                    self.move_position.x = entity.position.x
                                    self.move_position.y = entity.position.y
                                    
                                    self.try_to_move(dt, camera, screen)
                            else:
                                if not(self.state == UNIT_IDLE):
                                    self.change_state(UNIT_IDLE)
                                self.reset_task()
                        else:
                            if not(self.state == UNIT_IDLE):
                                self.change_state(UNIT_IDLE)
                            self.reset_task()
                    else:
                        if not(self.state == UNIT_IDLE):
                            self.change_state(UNIT_IDLE)
                        self.reset_task()
                else:
                    if not(self.state == UNIT_IDLE):
                        self.change_state(UNIT_IDLE)
                    self.reset_task()



    def is_full(self):
        checker = 0
        for _, amount in self.resources.items():
            checker += amount

        return checker >= self.collect_capacity
    
    

    def try_to_gather(self, dt, entity):   
        
        
        if self.state == UNIT_TASK:
            if 59>self.animation_frame >= self.collect_frame and self.will_collect:
                self.will_collect = False
                # collect calculations

                amount_to_remove = 1
                self.resources[entity.resource_indicator] += entity.remove_resources(amount_to_remove)
                
                if isinstance(entity, Resources):
                    
                    if entity.is_dead():
                        self.linked_map.remove_entity(entity)
                elif isinstance(entity, Farm):

                    if entity.is_empty():
                        self.linked_map.dead_entities[entity.id] = entity
                        entity.hp = 0
                        entity.change_state(STATES.get(entity.representation, None).get("dying", None))
                        



            elif self.animation_frame == self.len_current_animation_frames() - 1:
                self.will_collect = True 
            
        
    def try_to_collect(self,dt, camera, screen):
        if (self.state != UNIT_DYING and self.entity_defend_from_id == None):
            if self.resource_target_id != None:
                if not(self.is_full()):
                    entity = self.linked_map.get_entity_by_id(self.resource_target_id)
                    
                    if (entity != None): 
                        if (entity.team == 0 or entity.team == self.team):
                            if (entity.is_dead() == False):
                                
                                if (isinstance(entity, Resources) or (isinstance(entity, Farm) and not(entity.is_empty())) ):
                                    if (self.collide_with_entity(entity)):
                                        if not(self.state == UNIT_TASK):
                                            self.change_state(UNIT_TASK)
                                        
                                        self.try_to_gather(dt, entity)
                                        
                                    else:
                                        if not(self.state == UNIT_WALKING):
                                            self.change_state(UNIT_WALKING)
                                            
                                        self.move_position.x = entity.position.x
                                        self.move_position.y = entity.position.y
                                        self._entity_optional_target_id = entity.id
                                        self.try_to_move(dt, camera, screen)
                                else:
                                    if not(self.state == UNIT_IDLE):
                                        self.change_state(UNIT_IDLE)
                                    self.reset_task()     
                            else:
                                if not(self.state == UNIT_IDLE):
                                    self.change_state(UNIT_IDLE)
                                self.reset_task()
                        else:
                            if not(self.state == UNIT_IDLE):
                                self.change_state(UNIT_IDLE)
                            self.reset_task()
                    else:
                        if not(self.state == UNIT_IDLE):
                            self.change_state(UNIT_IDLE)
                        self.reset_task()
                else:
                    if not(self.state == UNIT_IDLE):
                        self.change_state(UNIT_IDLE)
                    self.reset_task()


    def try_to_build(self, dt, camera, screen):
        if (self.state != UNIT_DYING and self.entity_defend_from_id == None):
            if self.build_target_id != None:
                entity = self.linked_map.get_entity_by_id(self.build_target_id)
                
                if (entity != None):
                    if (entity.team == self.team and entity.state == BUILDING_INPROGRESS):
                        if (entity.is_dead() == False):
                            if (self.collide_with_entity(entity)):
                                
                                entity.builders[self.id] = None
                                if not(self.state == UNIT_TASK):
                                    self.change_state(UNIT_TASK)
                            else:
            
                                if not(self.state == UNIT_WALKING):

                                    self.change_state(UNIT_WALKING)

                                self.move_position.x = entity.position.x
                                self.move_position.y = entity.position.y
                                self._entity_optional_target_id = entity.id
                                

                                self.try_to_move(dt, camera, screen)
                                  
                        else:
                            if not(self.state == UNIT_IDLE):
                                self.change_state(UNIT_IDLE)
                            self.reset_task()

                    else:
                        if not(self.state == UNIT_IDLE):
                            self.change_state(UNIT_IDLE)
                        self.reset_task()
                else:
                    if not(self.state == UNIT_IDLE):
                        self.change_state(UNIT_IDLE)
                    self.reset_task()

            
    
    def collect_entity(self, resource_target_id):
        self.entity_target_id = None # if attacking we stop and collect
        self.drop_target_id = None
        self.build_target_id = None

        self.resource_target_id = resource_target_id
        if self.resource_target_id == None:
            if not(self.state == UNIT_IDLE):
                self.change_state(UNIT_IDLE)

    def attack_entity(self, entity_id):
        self.resource_target_id = None # if collecting we stop and attack
        self.drop_target_id = None
        self.build_target_id = None

        self.entity_target_id = entity_id
        if self.entity_target_id == None:
            if not(self.state == UNIT_IDLE):
                self.change_state(UNIT_IDLE)
        self.check_range_with_target = False
        self.locked_with_target = False

    def drop_to_entity(self, drop_target_id):
        self.resource_target_id = None # if collecting we stop and attack
        self.entity_target_id = None
        self.build_target_id = None

        self.drop_target_id = drop_target_id
        if self.drop_target_id == None:
            if not(self.state == UNIT_IDLE):
                self.change_state(UNIT_IDLE)

    def build_entity(self, build_target_id):
        self.resource_target_id = None # if collecting we stop and attack
        self.entity_target_id = None  
        self.drop_target_id = None

        self.build_target_id = build_target_id
        if self.build_target_id == None:
            
            if not(self.state == UNIT_IDLE):
                self.change_state(UNIT_IDLE)


    def update(self, dt, camera = None, screen = None):
        super().update(dt, camera, screen)
        self.try_to_collect(dt, camera,screen)
        self.try_to_drop(dt, camera, screen)
        self.try_to_build(dt, camera, screen)
    
    def display(self, dt, screen, camera, g_width, g_height):
        super().display(dt, screen, camera, g_width, g_height)
        if self.is_full():
            ex_iso_x, ex_iso_y = camera.convert_to_isometric_2d(self.position.x - self.linked_map.tile_size_2d/2, self.position.y - self.linked_map.tile_size_2d/2)
            draw_text("!",ex_iso_x, ex_iso_y, screen, int(camera.zoom * camera.img_scale*20))

    def change_state(self, new_state):
        super().change_state(new_state)
        

    def is_free(self):
        return super().is_free() and self.resource_target_id == None and self.drop_target_id == None and self.build_target_id == None

    def reset_task(self):
        self.resource_target_id = None
        self.drop_target_id = None
        self.build_target_id = None
        self.entity_target_id = None

