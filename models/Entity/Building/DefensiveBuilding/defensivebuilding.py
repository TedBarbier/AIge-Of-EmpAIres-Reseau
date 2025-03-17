from Entity.Building.building import *
from Entity.Unit.unit import Unit
from math import ceil
from PACKAGE_IMPORT import *
PACKAGE_DYNAMIC_IMPORT("Projectile")

PROJECTILE_TYPE_MAPPING = {
    "pa":Arrow,
    "ps":Spear,
    "fpa":FireArrow,
    "fps":FireSpear 
}

class DefensiveBuilding(Building):

    def __init__(self, id_gen,cell_Y, cell_X, position, team,representation, sq_size, hp, cost, build_time, attack, attack_speed, _range, projectile_type):
        super().__init__(id_gen,cell_Y, cell_X, position, team,representation, sq_size, hp, cost, build_time)
        self.attack = attack
        self.attack_speed = attack_speed
        self.range = _range
        self.projectile_type = projectile_type
        self.entity_target_id = None
        self.attack_time_acc = 0
        self.projetctile_padding = None
        self.detect_time_acc = 0

    def detect_unit_around(self,dt):
        self.detect_time_acc += dt
        if self.detect_time_acc > ONE_SEC:
            self.detect_time_acc =0
            offset = ceil(self.range/self.linked_map.region_division)
            shortest_dist = None
            self_region_Y, self_region_X = self.cell_Y//self.linked_map.region_division, self.cell_X//self.linked_map.region_division

            for offset_reg_Y in range(-offset, offset + 1):
                for offset_reg_X in range(-offset, offset + 1):
                    current_reg_Y, current_reg_X = self_region_Y + offset_reg_Y, self_region_X + offset_reg_X

                    current_region = self.linked_map.entity_matrix.get((current_reg_Y, current_reg_X), None)

                    if current_region != None:
                        for team in current_region:
                            if team != 0 and self.team != team:
                                current_team_region = current_region.get(team, None)

                                for entities in current_team_region.values():

                                    for entity in entities:
                                        if isinstance(entity, Unit):
                                            current_distance = self.position.abs_distance(entity.position) 
                                            range_status = self.linked_map.tile_size_2d * self.range + entity.box_size >= current_distance
                                            if shortest_dist == None or current_distance < shortest_dist and range_status:
                                                shortest_dist = current_distance
                                                self.entity_target_id = entity.id 

    def try_to_attack(self,dt):

        if (self.state == BUILDING_ACTIVE):

            if self.entity_target_id != None:
                entity = self.linked_map.get_entity_by_id(self.entity_target_id)
                
                if (entity != None):
                    
                    if (entity.team != 0 and entity.team != self.team):
                        
                        if (entity.is_dead() == False):
                            current_distance = self.position.abs_distance(entity.position)
                            range_status = self.linked_map.tile_size_2d * self.range + entity.box_size >= current_distance
                            
                            if range_status:
                                self.try_to_damage(dt, entity)
                            else:
                                self.detect_unit_around(dt)
                        else:
                            self.detect_unit_around(dt)
                    else:
                        self.detect_unit_around(dt)
                else:
                    self.detect_unit_around(dt)
            else:
                self.detect_unit_around(dt)

    def try_to_damage(self, dt, _entity):
        global PROJECTILE_TYPE_MAPPING
        self.attack_time_acc += dt
        if (self.attack_time_acc > self.attack_speed * ONE_SEC):

            self.attack_time_acc = 0
            
            ProjectileClass = PROJECTILE_TYPE_MAPPING.get(self.projectile_type, None)

            arrow = ProjectileClass(self.cell_Y, self.cell_X, PVector2(self.position.x - self.projetctile_padding, self.position.y - self.projetctile_padding), _entity, self.linked_map, self.attack)
            self.linked_map.add_projectile(arrow)


    def update(self, dt, camera = None, screen = None):
        super().update(dt, camera, screen)
        self.try_to_attack(dt)

    def display(self, dt, screen, camera, g_width, g_height):
        #draw_isometric_circle(camera, screen, self.position.x, self.position.y, self.range*TILE_SIZE_2D, TEAM_COLORS.get(self.team)) 

        super().display(dt, screen, camera, g_width, g_height)        

    def is_free(self):
        return True