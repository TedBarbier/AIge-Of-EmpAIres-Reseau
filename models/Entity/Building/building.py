from GLOBAL_VAR import *
from idgen import *
#from AITools.player import *
from Entity.entity import * 
class Building(Entity):

    def __init__(self, id_gen,cell_Y, cell_X, position, team,representation, sq_size, hp, cost, build_time, walkable = False):
        super().__init__(id_gen,cell_Y, cell_X, position, team, representation, sq_size)
        self.hp = hp
        self.max_hp = hp
        self.cost = cost
        self.build_time = build_time
        self.walkable = walkable
        self.linked_map = None
        self.display_choice = 0
        self.animation_time_acc = 0
        self.animation_frame = 0
        self.state = BUILDING_ACTIVE
        self.animation_speed = [1, 1, 20]
        self.HitboxClass = "Square"
        self.builders = {}
        self.build_progress = 0

    def len_current_animation_frames(self):
        return len(SPRITES.get(self.representation, None).get(self.state,None).get(self.display_choice, None)) #the length changes with respect to the state but the zoom and direction does not change the animation frame count

    def affordable_by(self, resources):
        for resource, amount in resources.items():
            if amount < self.cost.get(resource, None):
                return False
        
        return True 
    
    def update_animation_frame(self, dt):
        global ONE_SEC
        
        self.animation_time_acc += dt

        time_per_frame = ONE_SEC / self.animation_speed[self.state]  

        frames_to_advance = int(self.animation_time_acc / time_per_frame)

        if frames_to_advance > 0:
            self.animation_frame = (self.animation_frame + frames_to_advance) % self.len_current_animation_frames()

            water_mark_list =WATER_MARK_SKIP.get(self.representation)
            if (water_mark_list):
                if (self.state, self.display_choice, self.animation_frame) in water_mark_list:
                    self.animation_frame = (self.animation_frame + frames_to_advance)%(self.len_current_animation_frames()) #the length changes with respect to the state but the zoom and direction does not change the animation frame count

            self.animation_time_acc %= time_per_frame


        """
        self.animation_time_acc += dt
        if self.animation_time_acc > ONE_SEC/self.animation_speed[self.state]:

            
            self.animation_time_acc = 0

            self.animation_frame = (self.animation_frame + 1)%(self.len_current_animation_frames()) #the length changes with respect to the state but the zoom and direction does not change the animation frame count
            
            water_mark_list =WATER_MARK_SKIP.get(self.representation)
            if (water_mark_list):
                if (self.state, self.display_choice, self.animation_frame) in water_mark_list:
                    self.animation_frame = (self.animation_frame + 1)%(self.len_current_animation_frames()) #the length changes with respect to the state but the zoom and direction does not change the animation frame count
        """
    def display(self, dt, screen, camera, g_width, g_height):
        
        iso_x, iso_y = camera.convert_to_isometric_2d(self.position.x, self.position.y)
        
        px, py = camera.convert_to_isometric_2d(self.cell_X*TILE_SIZE_2D + TILE_SIZE_2D/2, self.cell_Y*TILE_SIZE_2D + TILE_SIZE_2D/2)
        if (camera.check_in_point_of_view(iso_x, iso_y, g_width, g_height)):
            
            #camera.draw_box(screen, self)

            display_image(META_SPRITES_CACHE_HANDLE(camera.zoom, list_keys = [self.representation, self.state, self.display_choice, self.animation_frame], camera = camera), iso_x, iso_y, screen, 0x04, 1)
            if not(self.is_dead()):
                draw_percentage_bar(screen, camera, iso_x, iso_y, self.hp, self.max_hp, self.sq_size, self.team)
            #draw_point(screen, (0, 0, 0), px, py, radius=5)

            if self.state == BUILDING_INPROGRESS:

                pro_iso_x, pro_iso_y = camera.convert_to_isometric_2d(self.position.x + self.linked_map.tile_size_2d/3, self.position.y + self.linked_map.tile_size_2d/3)
                draw_percentage_bar(screen, camera,pro_iso_x, pro_iso_y, self.build_progress*self.build_time, self.build_time, self.sq_size)
                draw_text(str(len(self.builders)),pro_iso_x, pro_iso_y, screen, int(camera.zoom * camera.img_scale*20))

    """         
    def display(self,dt, screen, camera, g_width, g_height):

        iso_x, iso_y = camera.convert_to_isometric_2d(self.position.x, self.position.y)
        if (camera.check_in_point_of_view(iso_x, iso_y, g_width, g_height)):
            camera.draw_box(screen, self)
            display_image(META_SPRITES_CACHE_HANDLE(camera.zoom, list_keys = [self.representation], camera = camera),iso_x, iso_y, screen, 0x04, 3)
            draw_percentage_bar(screen, camera, iso_x, iso_y, self.hp, self.max_hp, self.sq_size, self.team)
    """

    def change_state(self, state):
        self.state = state
        self.animation_frame = 0
        
    def is_dead(self):
        return self.hp <= 0
    
    def will_vanish(self):
        return self.is_dead() and ((self.animation_frame == self.len_current_animation_frames() - 1))

    def update(self, dt, camera = None, screen = None):
        self.update_animation_frame(dt)
        self.update_construction(dt)
        

    def update_builders(self):
        for builder_id in list(self.builders.keys()):
            builder = self.linked_map.get_entity_by_id(builder_id)

            if builder != None:
                if builder.build_target_id != self.id or builder.is_dead() or not(self.collide_with_entity(builder)):
                    self.builders.pop(builder_id)
            else:
                self.builders.pop(builder_id)
    def update_construction(self, dt):
        if self.state == BUILDING_INPROGRESS:
            self.update_builders()
            number_of_builder = len(self.builders)
            
            if number_of_builder > 0:
                        # formula of the effective we need to update the effective time cause of dynamic updates

            
                if self.hp < self.max_hp: 
                    effective_time = (3 * self.max_hp/self.build_time * ONE_SEC) / (number_of_builder + 2)

                    missing_health = (self.max_hp - self.hp)

                    if missing_health>1:
                        repair_progress = (dt / effective_time) * missing_health

                        # Increment the health by the repair amount
                        self.hp += repair_progress
                    else:
                        self.hp = self.max_hp


                else: 
                    effective_time = (3 * self.build_time * ONE_SEC) / (number_of_builder + 2)

                    progress_ratio = dt/effective_time

                    self.build_progress += progress_ratio
                    self.build_progress = min(self.build_progress, 1)

                    if self.build_progress >= 1:
                        self.change_state(BUILDING_ACTIVE)


    def get_html(self):
        return f'<li class="building">{self.dict_repr.get(self.representation)}<br> Position : {self.position}</li>'