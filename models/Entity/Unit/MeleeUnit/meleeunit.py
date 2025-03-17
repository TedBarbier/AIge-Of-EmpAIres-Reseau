from Entity.Unit.unit import *

class MeleeUnit(Unit):
    def __init__(self,id_gen, cell_Y, cell_X, position, team, representation, hp, cost, training_time, speed, attack, attack_speed):
        super().__init__(id_gen,cell_Y, cell_X, position, team, representation, hp, cost, training_time, speed, attack, attack_speed)
        self.start = pygame.time.get_ticks()
    def try_to_damage(self, dt, entity):

        self.attack_time_acc += dt 
        if self.first_time_pass or (self.attack_time_acc > self.attack_delta_time):

            if (self.first_time_pass):
                self.first_time_pass = False
            if not(self.state == UNIT_ATTACKING):
                self.start = pygame.time.get_ticks()
                self.change_state(UNIT_ATTACKING)
            self.attack_time_acc = 0

            self.will_attack = True

        if self.state == UNIT_ATTACKING:
            if self.animation_frame >= self.attack_frame and self.will_attack:
                self.will_attack = False
                entity.hp -= self.attack
                self.last = pygame.time.get_ticks()
                if entity.is_dead():
                    if entity.representation in ['C','T','v']:
                            if entity.state != STATES.get(entity.representation, None).get("dying", None):
                                resources = {}
                                if entity.representation == 'v':
                                    resources = entity.resources
                                else:
                                    resources = entity.storage.lose_resource()
                                player_gained = self.linked_map.players_dict.get(self.team,None)
                                if player_gained:
                                    player_gained.add_resources(resources)
                    self.linked_map.dead_entities[entity.id] = entity
                    entity.change_state(STATES.get(entity.representation, None).get("dying", None))
                    self.path_to_position = None

            elif self.animation_frame == (self.len_current_animation_frames() - 1):

                self.check_range_with_target = False # we need to recheck if it is still in range
                #self.change_state(UNIT_IDLE) # if the entity is killed we stop 

    def try_to_attack(self,dt, camera, screen):
        if (self.state != UNIT_DYING):
            entity = None

            if self.entity_target_id != None:
                entity = self.linked_map.get_entity_by_id(self.entity_target_id)
                if entity != None:
                    if entity.is_dead():
                        self.entity_target_id = None
                        enemy = self.linked_map.players_dict.get(entity.team, None)

                        if enemy:
                            target_id = enemy.entity_closest_to(BUILDINGS, self.cell_Y, self.cell_X, is_dead = True)

                            if target_id == None:
                                target_id = enemy.entity_closest_to(UNITS, self.cell_Y, self.cell_X, is_dead = True)
                            self.entity_target_id = target_id
                            self.check_range_with_target = False
                            if self.entity_target_id == None:
                                if not(self.state == UNIT_IDLE):
                                    self.change_state(UNIT_IDLE)
                                

                else:
                    players = self.linked_map.players_dict 
                    cteam = None
                    cdist = float('inf')

                    for team, player in players.items():

                        if self.team != team:
                            dist = math.sqrt((self.cell_X - player.cell_X)**2 + (self.cell_Y - player.cell_Y)**2)

                            if dist < cdist:
                                cdist = dist
                                cteam = team

                    if cteam != None:
                        enemy = players.get(cteam, None)
                        if enemy:
                            target_id = enemy.entity_closest_to(BUILDINGS, self.cell_Y, self.cell_X, is_dead = True)

                            if target_id == None:
                                target_id = enemy.entity_closest_to(UNITS, self.cell_Y, self.cell_X, is_dead = True)
                            self.entity_target_id = target_id
                            self.check_range_with_target = False

                            if self.entity_target_id == None:
                                if not(self.state == UNIT_IDLE):
                                    self.change_state(UNIT_IDLE)
            """
            if self.entity_defend_from_id != None:
                entity = self.linked_map.get_entity_by_id(self.entity_defend_from_id)

                if entity != None:

                    if entity.is_dead() or entity.team == self.team:
                        self.entity_defend_from_id = None
                        entity = None

                    else:

                        dist = math.sqrt((self.cell_X - entity.cell_X)**2 + (self.cell_Y - entity.cell_Y)**2)

                        if dist > 10:
                            self.entity_defend_from_id = None
                            entity = None
            """

            if self.entity_defend_from_id != None:
                entity = self.linked_map.get_entity_by_id(self.entity_defend_from_id)
            elif self.entity_target_id != None:
                entity = self.linked_map.get_entity_by_id(self.entity_target_id)

            if (entity != None): 
                if (entity.team != 0 and entity.team != self.team):
                    if (entity.is_dead() == False):
                        
                        if not(self.check_range_with_target):
                            if (self.collide_with_entity(entity)):
                                self.check_range_with_target = True
                                self.locked_with_target = True
                                    
                            else:
                                if not(self.state == UNIT_WALKING):
                                    self.change_state(UNIT_WALKING)

                                self._entity_optional_target_id = entity.id
                                self.move_position.x = entity.position.x
                                self.move_position.y = entity.position.y
                                
                                self.locked_with_target = False
                                self.first_time_pass = True
                                self.try_to_move(dt, camera, screen )
                        else: # collided 
                            self.target_direction = self.position.alpha_angle(entity.position)
                            dist_to_entity = self.position.abs_distance(entity.position)

                            if (dist_to_entity <= ((entity.sq_size) * TILE_SIZE_2D + entity.box_size + self.box_size)):
                                self.try_to_damage(dt, entity)
                            else:
                                self.check_range_with_target = False

                    else:
                        if ((self.entity_defend_from_id == entity.id and self.entity_target_id == None) or (self.entity_target_id == entity.id)) and not(self.state == UNIT_IDLE):
                            self.change_state(UNIT_IDLE)
                        self.reset_target()
                        self.locked_with_target = False
                else:
                    if not(self.state == UNIT_IDLE):
                        self.change_state(UNIT_IDLE)
                    self.reset_target()

