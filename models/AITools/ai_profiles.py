from Entity.entity import *
from .player import *
from Entity.Building import *
from GLOBAL_VAR import *
import time
from random import *

class AIProfile:
    def __init__(self, strategy, aggressiveness=1.0, defense=1.0):
        """
        Initialize the AI profile with a specific strategy.
        :param strategy: Strategy type ('aggressive', 'defensive', 'balanced')
        :param aggressiveness: Aggressiveness level
        :param defense: Defense level
        """

        self.strategy = strategy
        self.aggressiveness = aggressiveness
        self.defense = defense

    def compare_ratios(self, actual_ratios, target_ratios, context, keys_to_include=None):
        if len(context['player'].get_entities_by_class(['F']))<1:
            if context['player'].get_current_resources()["wood"]>=61:
                result = context['player'].build_entity(context['player'].get_entities_by_class('v',is_free=True), 'F')
                return
            else :
                v_ids = context['player'].get_entities_by_class(['v'],is_free=True)
                c_ids = context['player'].ect(['W'], context['player'].cell_Y, context['player'].cell_X)
                counter = 0
                c_pointer = 0
                for id in v_ids:
                    v = context['player'].linked_map.get_entity_by_id(id)
                    if not v.is_full():
                        if counter == 3:
                            counter = 0
                            if c_pointer<len(c_ids)-1:
                                c_pointer += 1
                        v.collect_entity(c_ids[c_pointer])
                        counter += 1
                    else:
                        if context['drop_off_id'] is None:
                            return
                        v.drop_to_entity(context['player'].entity_closest_to(["T","C"], v.cell_Y, v.cell_X, is_dead = True))
                        #v.drop_to_entity(context['player'].entity_closest_to(["T","C"], v.cell_Y, v.cell_X, is_dead = True))
                        
            return
        if keys_to_include is None:
            keys_to_include = target_ratios.keys()
        differences = {}
        filtered_target_ratios_building = {key: target_ratios[key] for key in keys_to_include if key in target_ratios}
        for key, target in filtered_target_ratios_building.items():
            actual = actual_ratios.get(key, 0)
            diff = abs(target - actual)
            differences[key] = diff
        sorted_differences = sorted(differences.items(), key=lambda x: x[1], reverse=True)
        for building_repr in sorted_differences:
            existing_ids = set(context['player'].get_entities_by_class(['A','B','C','K','T', 'F', 'S']))
            villagers = context['player'].get_entities_by_class(['v'], is_free=True)
            if not villagers:
                return
            result = context['player'].build_entity(context['player'].get_entities_by_class(['v'],is_free=True), building_repr[0])
            new_ids = set(context['player'].get_entities_by_class(['A','B','C','K','T', 'F', 'S']))
            new_building_ids = new_ids - existing_ids
            if result != 0:
                if not new_building_ids:
                    continue
                new_building_id = new_building_ids.pop()
                building = context['player'].linked_map.get_entity_by_id(new_building_id)
                if building.state == BUILDING_ACTIVE:
                    return
            elif result == 0:
                    resources_to_collect=("wood",'W')
                    for temp_resources in [("gold",'G'),("food",'F')]:
                        if context['resources'][temp_resources[0]]<context['resources'][resources_to_collect[0]]:
                            resources_to_collect=temp_resources
                    v_ids = context['player'].get_entities_by_class(['v'],is_free=True)
                    c_ids = context['player'].ect(resources_to_collect[1], context['player'].cell_Y, context['player'].cell_X)
                    counter = 0
                    c_pointer = 0
                    for id in v_ids:
                        v = context['player'].linked_map.get_entity_by_id(id)
                        if not v.is_full():
                            if counter == 3:
                                counter = 0
                                if c_pointer<len(c_ids)-1:
                                    c_pointer += 1
                            v.collect_entity(c_ids[c_pointer])
                            counter += 1
                        if v.is_full():
                            if context['drop_off_id'] is None:
                                return "Gathered resources"
                            v.drop_to_entity(context['player'].entity_closest_to(["T","C"], v.cell_Y, v.cell_X, is_dead = True))
                    return "Gathered resources" 

    STOP_CONDITIONS = {TRAIN_NOT_AFFORDABLE, TRAIN_NOT_FOUND_UNIT, TRAIN_NOT_ACTIVE}

    def choose_units(self, building):
        if isinstance(building, Barracks):
            units_list = ['s','x']
            seed(time.perf_counter())
            n = randint(0, 1)
            return units_list[n]
        elif isinstance(building, Stable):
            units_list = ['h','c']
            seed(time.perf_counter())
            n = randint(0, 1)
            return units_list[n]
        elif isinstance(building, ArcheryRange):
            units_list = ['a','m']
            seed(time.perf_counter())
            n = randint(0, 1)
            return units_list[n]
        
    def closest_player(self,context):
        list_player = context['player'].linked_map.players_dict.values()
        distance = {}
        for player in list_player:
            if player != context['player']:
                dx = context['player'].cell_X - player.cell_X
                dy = context['player'].cell_Y - player.cell_Y
                distance[player] = (dx ** 2 + dy ** 2) ** 0.5
        closest = min(distance.items(), key=lambda x: x[1])
        return closest[0]
    
    def closest_enemy_building(self,context):
        player = self.closest_player(context)
        minus_building = player.ect(BUILDINGS, player.cell_Y, player.cell_X)
        if minus_building:
            closest = minus_building[0]
        else:
            minus_entity = player.ect(UNITS, player.cell_Y, player.cell_X)
            if minus_entity:
                closest = minus_entity[0]
            else:
                return None
        return closest
            
                


    def decide_action(self,tree, context):
        """
        Decide the action to perform based on strategy and decision tree.
        :param context: Dictionary containing the current game state.
        :return: The chosen action as a string.
        """
        # Get the actions from the decision tree
        if context['player'].is_busy:
            return
        actions = tree.decide(context)

        # Call the appropriate strategy
        if self.strategy == "aggressive":
            return self._aggressive_strategy(actions, context)
        elif self.strategy == "defensive":
            return self._defensive_strategy(actions, context)
        elif self.strategy == "balanced":
            return self._balanced_strategy(actions, context)

    def _aggressive_strategy(self, actions, context):
        """
        Implement the aggressive strategy by prioritizing attacks and military training.
        """
        target_ratios_building = {
            'T': 0.13,   
            'C': 0.13,   
            'F': 0.13,    
            'B': 0.18,    
            'S': 0.165,  
            'A': 0.165,   
            'K': 0.1
        }

        try:
            for action in actions:
                if action == "Attacking the enemy!":
                    villager_free=[context['player'].linked_map.get_entity_by_id(v_id) for v_id in context['player'].get_entities_by_class(['v'],is_free=True)]
                    unit_list = context['units']['military_free']+villager_free[:len(villager_free)//2]
                    context['enemy_id'] = self.closest_enemy_building(context)
                    for unit in unit_list:
                        unit.attack_entity(context['enemy_id'])
                    return "Attacking in progress"

                elif action == "Train military units!":
                    # Train military units in training buildings
                    training_buildings = context['buildings']['training']
                    if not training_buildings:
                        keys_to_consider = ['B','S','A']
                        self.compare_ratios(context['buildings']['ratio'], target_ratios_building, context,keys_to_consider)
                    for building in training_buildings:
                        (context['player'].linked_map.get_entity_by_id(building)).train_unit(context['player'], self.choose_units(context['player'].linked_map.get_entity_by_id(building)))
                    # resources_to_collect=("wood",'W')
                    # for temp_resources in [("gold",'G'),("food",'F')]:
                    #     if context['resources'][temp_resources[0]]<context['resources'][resources_to_collect[0]]:
                    #         resources_to_collect=temp_resources
                    # v_ids = context['player'].get_entities_by_class(['v'],is_free=True)
                    # c_ids = context['player'].ect(resources_to_collect[1], context['player'].cell_Y, context['player'].cell_X)
                    # counter = 0
                    # c_pointer = 0
                    # for id in v_ids:
                    #     v = context['player'].linked_map.get_entity_by_id(id)
                    #     if not v.is_full():
                    #         if counter == 3:
                    #             counter = 0
                    #             if c_pointer<len(c_ids)-1:
                    #                 c_pointer += 1
                    #         v.collect_entity(c_ids[c_pointer])
                    #         counter += 1
                    #     if v.is_full():
                    #         v.drop_to_entity(context['player'].entity_closest_to(["T","C"], v.cell_Y, v.cell_X, is_dead = True))
                    self.compare_ratios(context['buildings']['ratio'], target_ratios_building, context)
                    return "Trained military units"
                
                elif action == "Building structure!":
                    self.compare_ratios(context['buildings']['ratio'], target_ratios_building, context)
                    return "Structure are built!"

            # Default to gathering resources if no attack actions are possible
            return "Gather resources for further attacks"
        finally:
            context['player'].is_busy = False

    def _defensive_strategy(self, actions, context):
        """
        Implement the defensive strategy by focusing on repairs and defenses.
        """
        player = context['player']
        target_ratios_building = {
            'T': 0.13,  
            'C': 0.15,   
            'F': 0.15,    
            'B': 0.08,    
            'S': 0.15,  
            'A': 0.15,   
            'K': 0.19
        }

        try:
            for action in actions:                
                if action == "Train military units!":
                    # Train military units in training buildings
                    training_buildings = context['buildings']['training']
                    if not training_buildings:
                        keys_to_consider = ['S','A','T']
                        self.compare_ratios(context['buildings']['ratio'], target_ratios_building, context,keys_to_consider)
                    for building in training_buildings:
                        (context['player'].linked_map.get_entity_by_id(building)).train_unit(player, self.choose_units(context['player'].linked_map.get_entity_by_id(building)))  
                    resources_to_collect=("wood",'W')
                    for temp_resources in [("gold",'G'),("food",'F')]:
                        if context['resources'][temp_resources[0]]<context['resources'][resources_to_collect[0]]:
                            resources_to_collect=temp_resources
                    # v_ids = context['player'].get_entities_by_class(['v'],is_free=True)
                    # c_ids = context['player'].ect(resources_to_collect[1], context['player'].cell_Y, context['player'].cell_X)
                    # counter = 0
                    # c_pointer = 0
                    # for id in v_ids:
                    #     v = context['player'].linked_map.get_entity_by_id(id)
                    #     if not v.is_full():
                    #         if counter == 3:
                    #             counter = 0
                    #             if c_pointer<len(c_ids)-1:
                    #                 c_pointer += 1
                    #         v.collect_entity(c_ids[c_pointer])
                    #         counter += 1
                    #     if v.is_full():
                    #         v.drop_to_entity(context['player'].entity_closest_to(["T","C"], v.cell_Y, v.cell_X, is_dead = True))
                    self.compare_ratios(context['buildings']['ratio'], target_ratios_building, context)
                    return "Trained military units"
                    
                elif action == "Attacking the enemy!":
                    unit_list = context['units']['military_free'][:len(context['units']['military_free'])//2]
                    context['enemy_id'] = self.closest_enemy_building(context)
                    for unit in unit_list:
                        unit.attack_entity(context['enemy_id'])
                    return "Attacking in progress"
                
                elif action == "Building structure!":
                    self.compare_ratios(context['buildings']['ratio'], target_ratios_building, context)
                    return "Structure are built!"
                
        finally:
            context['player'].is_busy = False

    def _balanced_strategy(self, actions, context):
        """
        Implement the balanced strategy by combining gathering, training, and attacks.
        """
        player = context['player']
        target_ratios_building = {
            'T': 0.2,   
            'C': 0.12,   
            'F': 0.2,    
            'B': 0.12,    
            'S': 0.12,  
            'A': 0.12,   
            'K': 0.12
        }

        try:
            for action in actions:
                if action == "Gathering resources!":
                    resources_to_collect=("wood",'W')
                    for temp_resources in [("gold",'G'),("food",'F')]:
                        if context['resources'][temp_resources[0]]<context['resources'][resources_to_collect[0]]:
                            resources_to_collect=temp_resources
                    v_ids = context['player'].get_entities_by_class(['v'],is_free=True)
                    c_ids = context['player'].ect(resources_to_collect[1], context['player'].cell_Y, context['player'].cell_X)
                    counter = 0
                    c_pointer = 0
                    for id in v_ids:
                        v = unit.linked_map.get_entity_by_id(id)
                        if not v.is_full():
                            if counter == 3:
                                counter = 0
                                if c_pointer<len(c_ids)-1:
                                    c_pointer += 1
                            v.collect_entity(c_ids[c_pointer])
                            counter += 1
                        else:
                            if context['drop_off_id'] is None:
                                return "Gathering resources"
                            villager.drop_to_entity(context['player'].entity_closest_to(["T","C"], villager.cell_Y, villager.cell_X, is_dead = True))
                    return "Gathering resources!"

                elif action == "Dropping off resources!":
                    # Drop resources in storage buildings
                    villagers = player.get_entities_by_class(['v'],is_free=True)
                    for villager_id in villagers:
                        if villager.is_full():
                            villager = player.linked_map.get_entity_by_id(villager_id)
                            if context['drop_off_id'] is None:
                                return "Dropped of resources"
                            villager.drop_to_entity(context['player'].entity_closest_to(["T","C"], villager.cell_Y, villager.cell_X, is_dead = True))  # Drop off resources
                    return "Dropped off resources"

                elif action == "Train military units!":
                    # Train military units in training buildings
                    training_buildings = context['buildings']['training']
                    if not training_buildings:
                        keys_to_consider = ['T','B','S']
                        self.compare_ratios(context['buildings']['ratio'], target_ratios_building, context, keys_to_consider)
                    for building in training_buildings:
                        (context['player'].linked_map.get_entity_by_id(building)).train_unit(player,self.choose_units(context['player'].linked_map.get_entity_by_id(building)))
                    resources_to_collect=("wood",'W')
                    for temp_resources in [("gold",'G'),("food",'F')]:
                        if context['resources'][temp_resources[0]]<context['resources'][resources_to_collect[0]]:
                            resources_to_collect=temp_resources
                    
                    # v_ids = context['player'].get_entities_by_class(['v'],is_free=True)
                    # c_ids = context['player'].ect(resources_to_collect[1], context['player'].cell_Y, context['player'].cell_X)
                    # counter = 0
                    # c_pointer = 0
                    # for id in v_ids:
                    #     v = context['player'].linked_map.get_entity_by_id(id)
                    #     if not v.is_full():
                    #         if counter == 3:
                    #             counter = 0
                    #             if c_pointer<len(c_ids)-1:
                    #                 c_pointer += 1
                    #         v.collect_entity(c_ids[c_pointer])
                    #         counter += 1
                    #     if v.is_full():
                    #         v.drop_to_entity(context['player'].entity_closest_to(["T","C"], v.cell_Y, v.cell_X, is_dead = True))
                    self.compare_ratios(context['buildings']['ratio'], target_ratios_building, context)
                    return "Trained military units"

                elif action == "Attacking the enemy!":
                    unit_list = context['units']['military_free']
                    context['enemy_id'] = self.closest_enemy_building(context)
                    for unit in unit_list:
                        unit.attack_entity(context['enemy_id'])
                        
                    return "Attacking in progress"
                
                elif action == "Building structure!":
                    self.compare_ratios(context['buildings']['ratio'], target_ratios_building, context)
                    return "Structure are built!"
        finally:
            context['player'].is_busy = False
        # Default to gathering resources if no actions are possible
        return "Gathered resources for balanced strategy"

