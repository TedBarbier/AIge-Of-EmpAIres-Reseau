from GameField.cell import *
from ImageProcessingDisplay.minimap import *
from AITools.isorange import *
import random
import math
from AITools.player import *
from AITools.clustergenerator import *

class Map:

    def __init__(self,_nb_CellX , _nb_CellY):
        
        
        self.nb_CellX = _nb_CellX
        self.nb_CellY = _nb_CellY
        self.tile_size_2d = TILE_SIZE_2D
        self.region_division = REGION_DIVISION
        self.entity_matrix = {} #sparse matrix

        self.entity_id_dict = {} # each element of this is an id
        self.resource_id_dict = {} # specially for the resources so the bots can easily decide to go to the closest resource ...
        self.dead_entities = {}
        self.score_players = [] # couple (team, life_time)
        self.projectile_set = set()

        self.refresh_time_acc = 0 # refresh for the terminal display
        self.iso_refresh_time_acc = 0 # refresh for the iso

        self.players_dict = {} # each element is a player, and the key is the team number 1 : team1 2 : team2

        # for the minimap
        self.minimap = MiniMap(PVector2(1000,300), _nb_CellX, _nb_CellY)
        
        self.id_generator = IdGenerator()
        self.state = "normal"


    def get_entity_by_id(self, _entity_id):
        return self.entity_id_dict.get(_entity_id, None)

    def check_cell(self, Y_to_check, X_to_check):
        if 0<=Y_to_check<self.nb_CellY and 0<=X_to_check<self.nb_CellX:
            REG_Y_to_check, REG_X_to_check = Y_to_check//self.region_division, X_to_check//self.region_division

            region = self.entity_matrix.get((REG_Y_to_check, REG_X_to_check),None)

            if (region):
                for team_region in region.values():
                    if team_region.get((Y_to_check, X_to_check), None) != None:
                        return 1 
            
            return 0
        else:
            return 0xff

    def add_entity(self, _entity):

        assert (_entity != None), 0x0001 # to check if the entity is not null in case there were some problem in the implementation

        entity_in_matrix = (_entity.cell_X - (_entity.sq_size - 1) >= 0 and _entity.cell_Y - (_entity.sq_size - 1) >= 0) and ( _entity.cell_X < self.nb_CellX and _entity.cell_Y < self.nb_CellY)

        if (entity_in_matrix == False):
            
            return 0 # to check if all the cells that will be occupied by the entity are in the map
        
        cell_padding = 0

        if not(isinstance(_entity, Unit)):# or isinstance(_entity, Farm) or (_entity.representation in ["W", "G"])):
            cell_padding = 1
        
        for Y_to_check in range(_entity.cell_Y + cell_padding,_entity.cell_Y - _entity.sq_size - cell_padding, -1): # we add minus 1 cause we need at least one cell free so that the units can reach this target
            for X_to_check in range(_entity.cell_X + cell_padding,_entity.cell_X - _entity.sq_size - cell_padding, -1):
                
                if self.check_cell(Y_to_check, X_to_check):
                    return 0 # not all the cells are free to put the entity 
        
        for Y_to_set in range(_entity.cell_Y,_entity.cell_Y - _entity.sq_size, -1):
            for X_to_set in range(_entity.cell_X,_entity.cell_X - _entity.sq_size, -1):

                REG_Y_to_set, REG_X_to_set = Y_to_set//self.region_division, X_to_set//self.region_division
                current_region = self.entity_matrix.get((REG_Y_to_set, REG_X_to_set),None)

                if (current_region == None):
                    self.entity_matrix[(REG_Y_to_set, REG_X_to_set)] = {}
                    current_region = self.entity_matrix.get((REG_Y_to_set, REG_X_to_set),None)

                current_team_region = current_region.get(_entity.team, None)

                if current_team_region == None:
                    current_region[_entity.team] = {}
                    current_team_region = current_region.get(_entity.team, None)

                current_cell = current_team_region.get((Y_to_set, X_to_set), None)
                
                if (current_cell == None):
                    current_team_region[(Y_to_set, X_to_set)] = set()
                    current_cell = current_team_region.get((Y_to_set, X_to_set), None)
                
                current_cell.add(_entity)

        topleft_cell = PVector2(self.tile_size_2d/2 + ( _entity.cell_X - (_entity.sq_size - 1))*self.tile_size_2d, self.tile_size_2d/2 + (_entity.cell_Y - (_entity.sq_size - 1))*self.tile_size_2d) 
        bottomright_cell =  PVector2(self.tile_size_2d/2 + ( _entity.cell_X )*self.tile_size_2d, self.tile_size_2d/2 + (_entity.cell_Y )*self.tile_size_2d) 

        _entity.position = (bottomright_cell + topleft_cell ) * (0.5)
        _entity.box_size = bottomright_cell.x - _entity.position.x  # distance from the center to the corners of the collision box

        
        if isinstance(_entity, Unit):
            _entity.box_size += TILE_SIZE_2D/(2 * 2.5) # for the units hitbox is smaller 
            _entity.move_position.x = _entity.position.x
            _entity.move_position.y = _entity.position.y # well when the unit is added its target pos to move its it self se it doesnt move
            
        else:
            _entity.box_size += TILE_SIZE_2D/(2) # the factors used the box_size lines are to choosen values for a well scaled collision system with respec to the type and size of the entity
        if _entity.team != 0:
            player = self.players_dict.get(_entity.team, None)

            if player:
                player.add_entity(_entity)
        else:
            resource_set = self.resource_id_dict.get(_entity.representation, None)

            if resource_set == None:
                self.resource_id_dict[_entity.representation] = set()
                resource_set = self.resource_id_dict.get(_entity.representation, None)

            resource_set.add(_entity.id)
        _entity.linked_map = self

        # at the end add the entity pointer to the id dict with the id dict 

        self.entity_id_dict[_entity.id] = _entity
        return 1 # added the entity succesfully
    
    def add_entity_to_closest(self, entity, cell_Y, cell_X, random_padding = 0x00, min_spacing = 4, max_spacing = 5):
        
        
        startY = cell_Y 
        startX = cell_X

        endY = cell_Y
        endX = cell_X

        added = False
        ite_list = None
        offsetX = 1
        offsetY = 1

        while not(added):
            
            startX -=1
            startY -=1
            endY += 1
            endX += 1

            ite_list = []

            if random_padding:
                offsetY = random.randint(min_spacing, max_spacing)
                offsetX = random.randint(min_spacing, max_spacing)
            
            for current_Y in range(endY, (startY - 1), -offsetY):
                for current_X in range(endX, (startX - 1), -offsetX):
                    ite_list.append((current_Y, current_X))
        
            if random_padding:
                random.shuffle(ite_list)

            for current_Y, current_X in ite_list:
                if not(added):
                    entity.cell_Y = current_Y
                    entity.cell_X = current_X

                    if (self.add_entity(entity)):
                        added = True
                else:
                    break


    def add_projectile(self, _projectile):
        self.projectile_set.add(_projectile)

    def remove_projectile(self, _projectile):
        self.projectile_set.discard(_projectile)

    def update_all_projectiles(self, dt):
        for proj in self.projectile_set.copy():
            proj.update_event(dt)

            if proj.reached_target:
                self.remove_projectile(proj)


    def remove_entity(self,_entity, unit_moving = False):

        assert _entity is not None, "Entity cannot be None (Error 0x0011)"

        for Y_to_remove in range(_entity.cell_Y, _entity.cell_Y - _entity.sq_size, -1):
            for X_to_remove in range(_entity.cell_X, _entity.cell_X - _entity.sq_size, -1):
                REG_Y, REG_X = Y_to_remove // self.region_division, X_to_remove // self.region_division
                region = self.entity_matrix.get((REG_Y, REG_X))

                if region:
                    team_region = region.get(_entity.team, None)
                    if team_region:
                        current_set = team_region.get((Y_to_remove, X_to_remove))

                        if current_set:
                            current_set.discard(_entity)  # Safe removal

                            if not current_set:
                                team_region.pop((Y_to_remove, X_to_remove), None)  # Safely remove key if set is empty

                    if not team_region:  # Remove empty regions
                        region.pop(_entity.team, None)
                if not region:  # Remove empty regions
                    self.entity_matrix.pop((REG_Y, REG_X), None)

        if not(unit_moving):
            self.entity_id_dict.pop(_entity.id, None)
            self.id_generator.free_ticket(_entity.id)
            if _entity.team != 0:
                player = self.players_dict.get(_entity.team, None)

                if player:
                    player.remove_entity(_entity)
            else:
                resource_set = self.resource_id_dict.get(_entity.representation, None)

                if resource_set:
                    if _entity.id in resource_set:
                        resource_set.remove(_entity.id)

                if not(resource_set):
                    self.resource_id_dict.pop(_entity.represantation, None)


        return _entity  # Return the entity if needed elsewhere


    def display(self, dt, screen, camera, g_width, g_height):
        
        self.iso_refresh_time_acc += dt
        if self.iso_refresh_time_acc >= ONE_SEC/60:
            screen.fill(BLACK_COLOR)
            self.iso_refresh_time_acc = 0
            tmp_cell = Cell(0, 0, PVector2(0,0))
            tmp_topleft = PVector2(0, 0)
            tmp_bottomright = PVector2(0, 0)

            (top_Y, top_X), (left_Y, left_X), (right_Y, right_X), (bottom_Y, bottom_X) = camera.indexes_in_point_of_view(g_width, g_height)

            top_Xt = max(0, min(top_X, self.nb_CellX - 1))
            top_Yt = max(0, min(top_Y, self.nb_CellY - 1))

            right_Xt = max(0, min(right_X, self.nb_CellX - 1))
            right_Yt = max(0, min(right_Y, self.nb_CellY - 1))

            left_Xt = max(0, min(left_X, self.nb_CellX - 1))
            left_Yt = max(0, min(left_Y, self.nb_CellY - 1))

            bottom_Xt = max(0, min(bottom_X, self.nb_CellX - 1))
            bottom_Yt  = max(0, min(bottom_Y, self.nb_CellY - 1))
            
            top = (top_Yt, top_Xt)
            left = (left_Yt, left_Xt)
            right = (right_Yt, right_Xt)
            bottom = (bottom_Yt, bottom_Xt)

            range_top = (top[0] // self.region_division, top[1] // self.region_division)
            range_left = (left[0] // self.region_division, left[1] // self.region_division)
            range_right = (right[0] // self.region_division, right[1] // self.region_division) 
            range_bottom = (bottom[0] // self.region_division, bottom[1] // self.region_division) 
    

            entity_to_display = set()
            

            min_X, min_Y = range_left[1], range_top[0]
            max_X, max_Y = range_right[1], range_bottom[0]

            for proj in self.projectile_set:
                if min_Y <= proj.cell_Y//self.region_division <= max_Y and \
                    min_X <= proj.cell_X//self.region_division <= max_X :
                        entity_to_display.add(proj)


            for region_Y_to_display, region_X_to_display in isoRange(range_top, range_left, range_right, range_bottom):

                    if region_Y_to_display >= 0 and region_Y_to_display < self.nb_CellY//self.region_division \
                        and region_X_to_display>=0 and region_X_to_display < self.nb_CellX//self.region_division:

                        # these are the real X Y of the region in the sparse matrix

                        REG_X, REG_Y = region_X_to_display * (self.region_division ), region_Y_to_display * (self.region_division )
                        
                        tmp_topleft.x = TILE_SIZE_2D/2 + REG_X*TILE_SIZE_2D
                        tmp_topleft.y = TILE_SIZE_2D/2 + REG_Y*TILE_SIZE_2D

                        tmp_bottomright.x = TILE_SIZE_2D/2 + (REG_X + (self.region_division - 1))*TILE_SIZE_2D
                        tmp_bottomright.y = TILE_SIZE_2D/2 + (REG_Y + (self.region_division - 1))*TILE_SIZE_2D

                        tmp_cell.position = (tmp_bottomright + tmp_topleft) * (0.5)

                        tmp_cell.display(screen, camera)

                        #check if this region contains entity
                        region_entities = self.entity_matrix.get((region_Y_to_display, region_X_to_display), None)
                        if region_entities != None:
                            for team_region in region_entities.values():
                                for entities in team_region.values(): # each value the region is a dict of the cells
                                    for entity in entities:
                                        entity_to_display.add(entity)
            """             
            for Y_to_display in range(start_Y, end_Y + 1):
                for X_to_display in range(start_X, end_X + 1):
                    
                    tmp_cell.position.x = X_to_display*camera.tile_size_2d + camera.tile_size_2d/2
                    tmp_cell.position.y = Y_to_display*camera.tile_size_2d + camera.tile_size_2d/2
                    iso_x, iso_y = camera.convert_to_isometric_2d(tmp_cell.position.x, tmp_cell.position.y)

                    pygame.draw.circle(screen, (255, 0, 0), (iso_x, iso_y), 1, 0) 
            """ # debug purposes 

                                                                                    # priority to the farm ( they are like grass so the ground is displayed first) then the normal deep sort 
            for current_entity in sorted(entity_to_display, key=lambda entity: (not(isinstance(entity, Farm)), entity.position.z, entity.position.y + entity.position.x, entity.position.y)):
            
                current_entity.display(dt, screen, camera, g_width, g_height)


            # minimap display 
            self.minimap.update_position(g_width, g_height)
            
            self.minimap.display_ground(screen)

            for current_region in self.entity_matrix.values():
                for current_team_region in current_region.values():
                    for entity_set in current_team_region.values():
                        for entity in entity_set:
                            if not(isinstance(entity, Building)):
                                self.minimap.display_on_cart(screen, entity)
            
            self.minimap.display_camera(screen, top_X, top_Y, bottom_X, bottom_Y)

        

    def terminal_display(self, dt, terminal_camera):
        self.refresh_time_acc += dt
        if self.refresh_time_acc >= ONE_SEC*(0.05):
            self.refresh_time_acc = 0
            startX, startY, endX, endY = terminal_camera.indexes_in_point_of_view_terminal()

            # Clear the terminal screen for animation
            
            os.system('cls' if os.name == 'nt' else 'clear') # cls if windows clear if

            sys.stdout.write(f"[+] View Start: ({startX}, {startY}), View End: ({endX}, {endY})\n")
            endY -= 1 # we took a line for the display info

            for currentY in range(startY, endY + 1):
                current_string=""
                for currentX in range(startX, endX + 1):
                    if 0 <= currentX < self.nb_CellX and 0 <= currentY < self.nb_CellY:
                        REG_X, REG_Y = currentX // 5, currentY // 5
                        added = False
                        current_region = self.entity_matrix.get((REG_Y, REG_X))
                        if current_region:
                            for team_region in current_region.values():
                                current_entity_set = team_region.get((currentY, currentX))
                                if current_entity_set:

                                    for current_entity in current_entity_set:
                                        current_string += current_entity.representation
                                        added = True
                                        break
                            if not added:
                                current_string += "."
                        else:
                            current_string += "."
                    else:
                        current_string += " "
                        
                sys.stdout.write(current_string)
                
                sys.stdout.flush()







    def generate_gold_center(self, num_players):
        center_Y, center_X = self.nb_CellY//2, self.nb_CellX//2
        gold_adjustment = (self.nb_CellY*self.nb_CellX)/14400

        tiles_factor = (num_players*7500)/800

        total_tiles = int(tiles_factor * gold_adjustment)

        number_gold = num_players*int(self.region_division/(1.5))

        for _ in range(total_tiles):
            current_gold = Gold(self.id_generator,center_Y, center_X, None)
            self.add_entity_to_closest(current_gold, center_Y, center_X, random_padding=0x1)

    def generate_map(self,gen_mode = MAP_NORMAL , mode = MARINES ,num_players=3):

        # Ensure consistent random generation

        #random.seed(0xba)
        
        if gen_mode == "Carte Centrée":
            self.generate_gold_center(num_players)
        self._place_player_starting_areas(mode, num_players)

        self.c_generate_clusters(num_players, gen_mode)

    def c_generate_clusters(self, num_players, gen_mode):

        current_directory = os.path.dirname(__file__)

        file_path = os.path.join(current_directory,"tree_clusters.gen")
        file_path2 = os.path.join(current_directory,"gold_clusters.gen")
        tree_cluster_generator = ClusterGenerator(file_path)
        gold_cluster_generator = ClusterGenerator(file_path2)

        spiral = spiral_distribution(self.nb_CellY, self.nb_CellX, self.region_division, num_players)
        gen_n = 0
        for top_X, top_Y in spiral:

            if gen_n%2 == 0:
                cluster_offsets = tree_cluster_generator.generate_offsets()

                for offset_Y, offset_X in cluster_offsets:

                    current_Y, current_X = top_Y + offset_Y, top_X + offset_X
                    if 0 <= current_X < self.nb_CellX and 0 <= current_Y < self.nb_CellY:
                        if not(self.check_cell(current_Y, current_X)):
                            tree = Tree(self.id_generator,current_Y, current_X, None)
                            self.add_entity(tree)
            elif gen_mode == "Carte Normal":
                cluster_offsets = gold_cluster_generator.generate_offsets()

                for offset_Y, offset_X in cluster_offsets:

                    current_Y, current_X = top_Y + offset_Y, top_X + offset_X
                    if 0 <= current_X < self.nb_CellX and 0 <= current_Y < self.nb_CellY:
                        if not(self.check_cell(current_Y, current_X)):
                            gold = Gold(self.id_generator,current_Y, current_X, None)
                            self.add_entity(gold)
            gen_n += 1

            
    def _generate_forests(self, forest_count=30, forest_size_range=(14, 28)):
        
        for _ in range(forest_count):
            # Randomly pick a forest center
            center_X = random.randint(0, self.nb_CellX - 1)
            center_Y = random.randint(0, self.nb_CellY - 1)
            forest_size = random.randint(*forest_size_range)

            GEN_DIS = 3
            for _ in range(forest_size):
                # Generate trees around the center
                offset_X = random.randint(-GEN_DIS, GEN_DIS)
                offset_Y = random.randint(-GEN_DIS, GEN_DIS)
                tree_X = center_X + offset_X
                tree_Y = center_Y + offset_Y

                # Add tree if position is valid and unoccupied
                if 0 <= tree_X < self.nb_CellX and 0 <= tree_Y < self.nb_CellY:
                    if not(self.check_cell(tree_Y, tree_X)):
                        tree = Tree(self.id_generator,tree_Y, tree_X, None)
                        self.add_entity(tree)
    
    def _generate_gold(self, gold_veins=30, vein_size_range=(8, 20)):
        
        for _ in range(gold_veins):
            # Randomly pick a vein center
            center_X = random.randint(0, self.nb_CellX - 1)
            center_Y = random.randint(0, self.nb_CellY - 1)
            vein_size = random.randint(*vein_size_range)

            GEN_DIS = 2

            for _ in range(vein_size):
                # Generate gold around the center
                offset_X = random.randint(-GEN_DIS, GEN_DIS)
                offset_Y = random.randint(-GEN_DIS, GEN_DIS)
                
                gold_X = center_X + offset_X
                gold_Y = center_Y + offset_Y

                # Add gold if position is valid and unoccupied
                if 0 <= gold_X < self.nb_CellX and 0 <= gold_Y < self.nb_CellY:
                    if not(self.check_cell(gold_Y, gold_X)):
                        gold = Gold(self.id_generator,gold_Y, gold_X, None)
                        self.add_entity(gold)
    




    def _place_player_starting_areas(self, mode, num_players):
        
        polygon = angle_distribution(self.nb_CellY, self.nb_CellX, num_players, scale=0.75, rand_rot=0x1)
        for i in range(len(polygon)):
            
            # Base position for this player's starting area
            center_Y, center_X = polygon[i][1], polygon[i][0]
 

            current_player = Player(center_Y, center_X, i + 1)
            current_player.linked_map = self
            self.players_dict[current_player.team] = current_player

            if not(self.check_cell(center_Y, center_X)) :
                gen_option = MODE_GENERATION.get(mode)
                
                entities_gen = gen_option.get("entities")
                for entity_type, number in entities_gen.items():

                    EntityClass = CLASS_MAPPING.get(entity_type, None)
                    
                    
                    for i in range(number):
                        
                        entity_instance = EntityClass(self.id_generator,None, None, None, current_player.team)
                        if isinstance(entity_instance, Unit):
                            current_player.add_population()
                            current_player.current_population += 1

                        self.add_entity_to_closest(entity_instance, current_player.cell_Y, current_player.cell_X, random_padding=0x01)
            
            current_player_resources = gen_option.get("resources").copy() # we dont want togive it as a pointer else all players will share the same resources haha
            current_player.add_resources(current_player_resources)
            
            
        

    def _add_starting_resources(self, center_Y, center_X):

        GEN_DIS_G = 2
        GEN_DIS_T = 1
        for offset_X, offset_Y in [(-GEN_DIS_G, GEN_DIS_G), (GEN_DIS_G, -GEN_DIS_G), (GEN_DIS_G, GEN_DIS_G)]:
            gold_X = center_X + offset_X
            gold_Y = center_Y + offset_Y
            if not(self.check_cell(gold_X, gold_Y)):
                
                gold = Gold(self.id_generator,gold_Y, gold_X, None)
                self.add_entity(gold)

        for offset_X, offset_Y in [(GEN_DIS_T, GEN_DIS_T), (GEN_DIS_T, -GEN_DIS_T), (-GEN_DIS_T, GEN_DIS_T)]:
            tree_X = center_X + offset_X
            tree_Y = center_Y + offset_Y
            if not(self.check_cell(tree_Y, tree_Y)):  
                tree = Tree(self.id_generator,tree_Y, tree_X, None)
                self.add_entity(tree)

    def mouse_get_entity(self, camera, iso_x, iso_y):

        res_entity = None

        x, y = camera.convert_from_isometric_2d(iso_x, iso_y)

        cell_X, cell_Y = int(x/camera.tile_size_2d), int(y/camera.tile_size_2d)

        region = self.entity_matrix.get((cell_Y//self.region_division, cell_X//self.region_division))

        if region:
            current_set = region.get((cell_Y, cell_X))

            if (current_set):
                for entity in current_set:    
                    res_entity = entity.id
                    break
        
        return res_entity

    def update_all_projectiles(self, dt):
        for proj in self.projectile_set.copy():
            proj.update_event(dt)

            if proj.reached_target:
                self.remove_projectile(proj)

    def update_all_dead_entities(self, dt):
        for key in list(self.dead_entities.keys()):
            entity = self.dead_entities.get(key, None)
            if entity:
                if entity.will_vanish():
                    self.dead_entities.pop(key, 0)
                    self.remove_entity(entity)

    def update_all_entities(self, dt, camera, screen):
        battle = False
        for id in list(self.entity_id_dict.keys()):
            
            entity = self.entity_id_dict.get(id)
            if entity:
                if isinstance(entity ,Unit):
                    if not(entity.is_dead()) and (entity.entity_target_id != None or entity.entity_defend_from_id != None):
                        battle = True
                entity.update(dt, camera, screen)

        if battle:
            self.state = "battle"
        else:
            self.state = "normal"

    def update_all_players(self, dt):
        for player in self.players_dict.values():
            player.update(dt)

        for team in list(self.players_dict.keys()):

            player = self.players_dict.get(team, None)

            if player:
                if player.is_dead():
                    self.players_dict.pop(team, None)
                    self.score_players.append((player.team, convert_seconds(player.life_time)))

        if len(self.players_dict) == 1:
            player = list(self.players_dict.values())[0]
            self.state = "end"
            self.score_players.append((player.team, convert_seconds(player.life_time)))
            self.score_players.reverse()


    def update_all_events(self, dt, camera, screen):
        if self.state != "end":
            self.update_all_entities(dt, camera, screen)
            self.update_all_projectiles(dt)
            self.update_all_dead_entities(dt)
            self.update_all_players(dt)












def angle_distribution(Y, X, player_number, scale=1, rand_rot=False):

    Cx = X / 2
    Cy = Y / 2

    return ellipse_distribution(Y/2*scale, X/2 * scale, Cy, Cx, player_number, rand_rot)



def ellipse_distribution(ry, rx, Cy, Cx, angle_num, rand_rot = False):
    if angle_num > 1:
        points = []

        theta = (2 * math.pi) / angle_num
        phi = 0

        if rand_rot:
            phi += random.uniform(0, 2 * math.pi)

        for i in range(angle_num):
            current_theta = i * theta + phi
            x = int(Cx + rx  * math.cos(current_theta))
            y = int(Cy + ry  * math.sin(current_theta))
            points.append((x, y))
        
        return points
    else:
        return [(int(Cx),int(Cy))]

def spiral_distribution(Y, X, reg_div, player_num):
    points = []
    spiral_lvl = int(min(Y, X) /(reg_div**(math.sqrt(reg_div))))

    Y_step = Y/2 /spiral_lvl
    X_step = X/2 /spiral_lvl

    Cy, Cx = Y/2, X/2
    
    angle_num = 0
    angle_step = math.ceil(1*player_num)

    for lvl in range(spiral_lvl):
        rY, rX = lvl*Y_step, lvl*X_step
        points += ellipse_distribution(rY, rX, Cy, Cx, angle_num, rand_rot=True)
        angle_num += angle_step

    return points
