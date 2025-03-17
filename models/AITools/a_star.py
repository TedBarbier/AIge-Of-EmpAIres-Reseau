import heapq
import math




CELL_DIVISION = 3
class Node:
    def __init__(self, _X, _Y):
        self.X = _X
        self.Y = _Y
        self.G_cost = 0  # Cost from start node
        self.H_cost = 0  # Heuristic cost to target
        self.F_cost = 0  # Total cost
        self.previus = None

    def __lt__(self, other):
        return self.F_cost < other.F_cost or (self.F_cost == other.F_cost and self.H_cost < other.H_cost)

    def dist_to(self, other):
        return math.sqrt((other.X - self.X)**2 + (other.Y - self.Y)**2) * 10

    def update_F_cost(self):
        self.F_cost = self.H_cost + self.G_cost

    def __eq__(self, other):
        return self.X == other.X and self.Y == other.Y

    def __str__(self):
        return f"({self.X},{self.Y}): G={self.G_cost} H={self.H_cost} F={self.F_cost}"

def A_STAR(start_X, start_Y, end_X, end_Y, _map, the_moving_unit, pass_flags = 0):
    if not (0 <= start_X < _map.nb_CellX and 0 <= start_Y < _map.nb_CellY and 
            0 <= end_X < _map.nb_CellX and 0 <= end_Y < _map.nb_CellY):
        return None # Invalid start or end
    start_node = Node(start_X, start_Y)
    
    target_node = Node(end_X, end_Y)

    start_node.H_cost = start_node.dist_to(target_node)
    start_node.update_F_cost()

    searching = []
    heapq.heappush(searching, (start_node.F_cost, start_node))

    discoverd = {}
    searched = set()

    region = _map.entity_matrix.get((end_Y//_map.region_division, end_X//_map.region_division), None)

    if the_moving_unit._entity_optional_target_id == None and not(pass_flags): # in this case we are only moving to a certan position so we need to see if it is reachable
       
        if (region != None):
            
            entities = region.get((end_Y, end_X), None)
            if(entities): # entities exists so the cell is occupied

                for entity in entities:

                    if not(entity.walkable): # non walkable = non reachable so nooo
                        
                        return None
    
    collided_with_entity = False # these 3 variables are used in case we have an entity as target

    collision_node = None 
    while searching:
        _, best_node = heapq.heappop(searching)

        # these conditions are have only sense when the target is an entity 
        # not a normal position path finding, but it doesnt affect 
        # the algo in the case of normal pathfinding



        ##found path !!###
        if collided_with_entity: # in case optional target

            path = {}
            while collision_node: # this maybe is not the best one to the center but the closest one to collide
                if (collision_node.Y, collision_node.X) in path:
                    break
                path[(collision_node.Y, collision_node.X)] = None # the keys are the node we did this so we can pop easliy later
                collision_node = collision_node.previus
            reversed_path = dict(reversed(list(path.items())))
            
            return reversed_path
        
        elif best_node == target_node:
            # Reconstruct path
            path = {}
            while best_node:
                path[(best_node.Y, best_node.X)] = None 
                best_node = best_node.previus

            reversed_path = dict(reversed(list(path.items())))
            
            return reversed_path
        ## end ##

        searched.add((best_node.X, best_node.Y))

        for offsetY in [-1, 0, 1]:
            for offsetX in [-1, 0, 1]: # neighbors are the cells around
                if not(collided_with_entity):
                    neighbor_X = best_node.X + offsetX
                    neighbor_Y = best_node.Y + offsetY

                    if (offsetY == 0 and offsetX == 0) or neighbor_X < 0 or neighbor_Y < 0 or neighbor_X >= _map.nb_CellX or neighbor_Y >= _map.nb_CellY: # not in bound
                        continue

                    cell_walkable = True 
                    C_cost = 0
                    #check if the current cellX and cellY contains entities 
                    region = _map.entity_matrix.get((neighbor_Y//_map.region_division, neighbor_X//_map.region_division), None)

                    if (region != None):
                        for team_region in region.values():
                            entities = team_region.get((neighbor_Y, neighbor_X), None)
                            if(entities): # entities exists so the cell is occupied
                    
                                for entity in entities:
                                    if (entity.id == the_moving_unit._entity_optional_target_id):

                                        cell_walkable = True 
                                        collided_with_entity = True 
                                        break

                                    elif not(entity.walkable):
                                        if not(neighbor_X == end_X and neighbor_Y == end_Y and pass_flags):
                                            cell_walkable = False
                                            break

                                    elif entity.representation not in ["F"]:
                                        C_cost += 1

                    if cell_walkable:
                        neighbor_node = discoverd.get((neighbor_Y, neighbor_X),None) 

                        if neighbor_node is None: # we didnt discover this cell in the grid, so we create the node 
                            neighbor_node = Node(neighbor_X, neighbor_Y)
                            neighbor_node.G_cost = neighbor_node.dist_to(start_node) + C_cost
                            neighbor_node.H_cost = neighbor_node.dist_to(target_node)
                            neighbor_node.update_F_cost()
                            neighbor_node.previus = best_node

                            discoverd[(neighbor_Y, neighbor_X)] = neighbor_node # now it is discoverd and we need to explore it, push to the heap
                            heapq.heappush(searching, (neighbor_node.F_cost, neighbor_node)) # we push with respect to the F_cost, priority to the lowest F cost
                        else:
                            current_G_cost = best_node.G_cost + best_node.dist_to(neighbor_node) + C_cost
                            if current_G_cost < neighbor_node.G_cost: # if it smaller, we found a path connected to this node, better than a previous one
                                neighbor_node.G_cost = current_G_cost # update its G cost
                                neighbor_node.update_F_cost()
                                neighbor_node.previus = best_node # connect the path

                    if collided_with_entity:
                        collision_node = neighbor_node
    return None  # No path found
"""
def arrounding_cells(start_X, start_Y, _map, the_moving_unit, the_moving_unit._entity_optional_target_id):
    def process_cell(currentY, currentX, ite_list):
        
        matrix_Y = currentY // CELL_DIVISION
        matrix_X = currentX // CELL_DIVISION

        region_Y, region_X = matrix_Y//_map.region_division, matrix_X//_map.region_division
        
        
        current_position = PVector2(currentX * (_map.tile_size_2d / CELL_DIVISION) + (_map.tile_size_2d / CELL_DIVISION) / 2,
                                    currentY * (_map.tile_size_2d / CELL_DIVISION) + (_map.tile_size_2d / CELL_DIVISION) / 2)
        
        current_shape = Square(current_position.x, current_position.y, _map.tile_size_2d / CELL_DIVISION / 2)
        current_C_cost = 0 # crowd cost

        cell_walkable = True

        current_region = _map.entity_matrix.get((region_Y, region_X), None)

        if current_region:
            current_set = current_region.get((matrix_Y, matrix_X), None)

            if current_set:
                for entity in current_set:
                        
                    if entity.collide_with_shape(current_shape):
                        if not(entity != the_moving_unit and entity != the_moving_unit._entity_optional_target_id):
                            
                            if (isinstance(entity,Building) and not(entity.walkable)) or isinstance(entity, Resources):
                                cell_walkable = False
                                break
                            else:
                                current_C_cost += 1

        if cell_walkable:
            ite_list.append(((currentY, currentX), current_C_cost))
        
    ite_list = []
    closest_available_cell = None


    if the_moving_unit._entity_optional_target_id:
        top_Y = (the_moving_unit._entity_optional_target_id.cell_Y + 1) * CELL_DIVISION
        top_X = (the_moving_unit._entity_optional_target_id.cell_X + 1) * CELL_DIVISION
        sq_size = the_moving_unit._entity_optional_target_id.sq_size

        bottom_Y = top_Y - sq_size * CELL_DIVISION - 1
        bottom_X = top_X - sq_size * CELL_DIVISION - 1

        # Top Boundary
        for current_Y in range(top_Y - 1, bottom_Y, -1):
            if not(0<=current_Y<_map.nb_CellY * CELL_DIVISION and 0<=top_X<_map.nb_CellX * CELL_DIVISION):
                continue
            process_cell(current_Y, top_X, ite_list)

        # Right Boundary
        for current_X in range(top_X - 1, bottom_X, -1):
            if not(0<=current_Y<_map.nb_CellY * CELL_DIVISION and 0<=top_X<_map.nb_CellX * CELL_DIVISION):
                continue
            process_cell(top_Y, current_X, ite_list)

        # Bottom Boundary
        for current_Y in range(bottom_Y + 1, top_Y):
            if not(0<=current_Y<_map.nb_CellY * CELL_DIVISION and 0<=top_X<_map.nb_CellX * CELL_DIVISION):
                continue
            process_cell(current_Y, bottom_X, ite_list)

        # Left Boundary
        for current_X in range(bottom_X + 1, top_X):
            if not(0<=current_Y<_map.nb_CellY * CELL_DIVISION and 0<=top_X<_map.nb_CellX * CELL_DIVISION):
                continue
            process_cell(bottom_Y, current_X, ite_list)

        if ite_list:
            closest_available_cell = sorted(
                ite_list,
                key=lambda item: (
                    item[1],  # Primary: crowd cost
                    math.sqrt((start_X - item[0][1])**2 + (start_Y - item[0][0])**2)  # Secondary: distance
                )
            )[0][0]
    print("eyyey")
    print(closest_available_cell)
    return closest_available_cell



def A_STAR(start_X, start_Y, end_X, end_Y, _map, the_moving_unit, the_moving_unit._entity_optional_target_id = None):
    if not (0 <= start_X < _map.nb_CellX * CELL_DIVISION and 0 <= start_Y < _map.nb_CellY* CELL_DIVISION and 
            0 <= end_X < _map.nb_CellX* CELL_DIVISION and 0 <= end_Y < _map.nb_CellY* CELL_DIVISION):
        return None # Invalid start or end



    # check if it is possible to reach the target, check the surrounding cells with the less crowded area a set it as target 
   
        
    start_node = Node(start_X, start_Y)
    
    if the_moving_unit._entity_optional_target_id:
        closest_availalbe_cell = arrounding_cells(start_X, start_Y, _map, the_moving_unit, the_moving_unit._entity_optional_target_id)

        if closest_availalbe_cell == None: # not avaible cells
            return None
        target_node = Node(closest_availalbe_cell[1],closest_availalbe_cell[0])
    else:

        target_node = Node(end_X, end_Y)

    start_node.H_cost = start_node.dist_to(target_node)
    start_node.update_F_cost()

    searching = []
    heapq.heappush(searching, (start_node.F_cost, start_node))

    discoverd = {}
    searched = set()

    
    

    current_searching = 0
    while searching:
        print(current_searching)
        current_searching += 1
        _, best_node = heapq.heappop(searching)
        
        # these conditions are have only sense when the target is an entity 
        # not a normal position path finding, but it doesnt affect 
        # the algo in the case of normal pathfinding



        ##found path !!###
        if best_node == target_node:
            # Reconstruct path

            path = []

            
            if the_moving_unit._entity_optional_target_id:
                ent = []

                for offsetY in range(-1, 2):
                    for offsetX in range(-1,2):
                        currentY = target_node.Y + offsetY
                        currentX = target_node.X + offsetX
                        
                        matrix_Y = currentY // CELL_DIVISION
                        matrix_X = currentX // CELL_DIVISION

                        region_Y = matrix_Y // _map.region_division
                        region_X = matrix_X // _map.region_division

                        current_region = _map.entity_matrix.get((region_Y, region_X), None)

                        if current_region:

                            current_set = current_region.get((matrix_Y, matrix_X), None)

                            if current_set:

                                for entity in current_set:
                                    if entity == the_moving_unit._entity_optional_target_id:
                                        print("marra")
                                        ent.append((currentX, currentY))
                    
                    print(ent)
                    closest_index = 0
                    smallest = 10000

                    for index in range(len(ent)):
                        current_dist =math.sqrt((target_node.X - ent[index][0])**2 + (target_node.Y - ent[index][1])**2)
                        if current_dist < smallest:
                            smallest = current_dist
                            closest_index = index
                    
                    path.append((ent[closest_index][0], ent[closest_index][1]))
          
            while best_node:
                path.append((best_node.X, best_node.Y))
                best_node = best_node.previus
            path.reverse()
            return path
        ## end ##
        
        searched.add((best_node.X, best_node.Y))


        
        for offsetY, offsetX in [(1,0), (-1, 0), (0, -1), (0, 1)]:
            neighbor_X = best_node.X + offsetX
            neighbor_Y = best_node.Y + offsetY

            neighbor_position = PVector2(neighbor_X * _map.tile_size_2d/CELL_DIVISION + _map.tile_size_2d/2/CELL_DIVISION, neighbor_Y * _map.tile_size_2d/CELL_DIVISION+ _map.tile_size_2d/2/CELL_DIVISION)
            neighbor_shape = Square(neighbor_position.x, neighbor_position.y, _map.tile_size_2d/CELL_DIVISION/2)

            if (neighbor_X == best_node.X and neighbor_Y == best_node.Y ) or neighbor_X < 0 or neighbor_Y < 0 or neighbor_X >= _map.nb_CellX * CELL_DIVISION or neighbor_Y >= _map.nb_CellY * CELL_DIVISION: # not in bound
                continue

            cell_walkable = True 
            current_C_cost = 0 # crowd cost 
            #check if the current cellX and cellY contains entities 
            region = _map.entity_matrix.get(((neighbor_Y // CELL_DIVISION) //_map.region_division, (neighbor_X // CELL_DIVISION) //_map.region_division), None)

            if (region != None):
                
                entities = region.get((neighbor_Y // CELL_DIVISION, neighbor_X //CELL_DIVISION), None)
                if(entities): # entities exists so the cell is occupied
                    
                    for entity in entities:
                        if entity != the_moving_unit:

                            if entity.collide_with_shape(neighbor_shape):
                                        
                                if (isinstance(entity, Building) and not(entity.walkable)) or isinstance(entity, Resources): # some building can be walkable
                                    cell_walkable = False
                                    break
                                else:
                                    current_C_cost += 1
                    
            if not(cell_walkable):
                continue

            neighbor_node = discoverd.get((neighbor_Y, neighbor_X),None) 

            if neighbor_node is None: # we didnt discover this cell in the grid, so we create the node 
                neighbor_node = Node(neighbor_X, neighbor_Y)
                neighbor_node.G_cost = neighbor_node.dist_to(start_node) + current_C_cost
                neighbor_node.H_cost = neighbor_node.dist_to(target_node)
                neighbor_node.update_F_cost()
                neighbor_node.previus = best_node

                discoverd[(neighbor_Y, neighbor_X)] = neighbor_node # now it is discoverd and we need to explore it, push to the heap
                heapq.heappush(searching, (neighbor_node.F_cost, neighbor_node)) # we push with respect to the F_cost, priority to the lowest F cost
            else:
                current_G_cost = best_node.G_cost + best_node.dist_to(neighbor_node) + current_C_cost
                if current_G_cost < neighbor_node.G_cost: # if it smaller, we found a path connected to this node, better than a previous one
                    neighbor_node.G_cost = current_G_cost # update its G cost
                    neighbor_node.update_F_cost()
                    neighbor_node.previus = best_node # connect the path

    return None # No path found

"""




























































"""
def A_STAR(start_X, start_Y, end_X, end_Y, _map, the_moving_unit, the_moving_unit._entity_optional_target_id = None):
    if not (0 <= start_X < _map.nb_CellX and 0 <= start_Y < _map.nb_CellY and 
            0 <= end_X < _map.nb_CellX and 0 <= end_Y < _map.nb_CellY):
        return None # Invalid start or end

    start_node = Node(start_X, start_Y)
    
    target_node = Node(end_X, end_Y)

    start_node.H_cost = start_node.dist_to(target_node)
    start_node.update_F_cost()

    searching = []
    heapq.heappush(searching, (start_node.F_cost, start_node))

    discoverd = {}
    searched = set()

    
    collided_with_entity = False # these 3 variables are used in case we have an entity as target

    

    while searching:
        _, best_node = heapq.heappop(searching)
        
        # these conditions are have only sense when the target is an entity 
        # not a normal position path finding, but it doesnt affect 
        # the algo in the case of normal pathfinding



        ##found path !!###
        if best_node == target_node or collided_with_entity:
            # Reconstruct path
            path = []
            while best_node:
                path.append((best_node.X, best_node.Y))
                best_node = best_node.previus
            path.reverse()
            return path
        ## end ##
        
        searched.add((best_node.X, best_node.Y))

        region = _map.entity_matrix.get((best_node.Y//_map.region_division, best_node.X//_map.region_division), None)

        

        for offsetY in [-1, 0, 1]:
            for offsetX in [-1, 0, 1]: # neighbors are the cells around
                neighbor_X = best_node.X + offsetX
                neighbor_Y = best_node.Y + offsetY

                if neighbor_X < 0 or neighbor_Y < 0 or neighbor_X >= _map.nb_CellX or neighbor_Y >= _map.nb_CellY: # not in bound
                    continue

                cell_walkable = True 

                #check if the current cellX and cellY contains entities 
                region = _map.entity_matrix.get((neighbor_Y//_map.region_division, neighbor_X//_map.region_division), None)

                if (region != None):
                    
                    entities = region.get((neighbor_Y, neighbor_X), None)
                    if(entities): # entities exists so the cell is occupied
                        
                        for entity in entities:
                            #if entity != the_moving_unit:
                            if (entity == the_moving_unit._entity_optional_target_id):
                                cell_walkable = True 
                                collided_with_entity = True
                                print("collided")
                                break

                            if isinstance(entity, Building): # some building can be walkable
                                if not(entity.walkable):    # if it is not , False and break
                                    cell_walkable = False
                                    break

                            elif isinstance(entity, Resources):
                                cell_walkable = False
                                break

                        
                if not(cell_walkable):
                    continue

                neighbor_node = discoverd.get((neighbor_Y, neighbor_X),None) 

                if neighbor_node is None: # we didnt discover this cell in the grid, so we create the node 
                    neighbor_node = Node(neighbor_X, neighbor_Y)
                    neighbor_node.G_cost = neighbor_node.dist_to(start_node) 
                    neighbor_node.H_cost = neighbor_node.dist_to(target_node)
                    neighbor_node.update_F_cost()
                    neighbor_node.previus = best_node

                    discoverd[(neighbor_Y, neighbor_X)] = neighbor_node # now it is discoverd and we need to explore it, push to the heap
                    heapq.heappush(searching, (neighbor_node.F_cost, neighbor_node)) # we push with respect to the F_cost, priority to the lowest F cost
                else:
                    current_G_cost = best_node.G_cost + best_node.dist_to(neighbor_node) 
                    if current_G_cost < neighbor_node.G_cost: # if it smaller, we found a path connected to this node, better than a previous one
                        neighbor_node.G_cost = current_G_cost # update its G cost
                        neighbor_node.update_F_cost()
                        neighbor_node.previus = best_node # connect the path

    return None  # No path found"""