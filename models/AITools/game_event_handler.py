# from GameField.map import Map
# from ai_profiles import AIProfile
from Entity.entity import Entity
from GLOBAL_VAR import *


class GameEventHandler:
    def __init__(self, map, players, ai_profiles):
        self.map = map
        self.players = players
        self.ai_profiles = ai_profiles

    def process_ai_decisions(self, tree):
        all_action = []
        context = self.get_context_for_player()
        actions = self.ai_profiles.decide_action(tree, context)
        all_action.append(actions)

    def get_context_for_player(self):
        context = {
            'desired_villager_count': len(self.players.get_entities_by_class(['T','H','C','F','B','S','A','K']))+2,
            'resources': self.players.get_current_resources(),
            'ratio_military':len(self.players.get_entities_by_class(['h', 'a', 's','x','m','c']))/len(self.players.get_entities_by_class(['h', 'a', 's','v','x','m','c'])) if len(self.players.get_entities_by_class(['h','a','s','v','x','m','c'])) != 0 else 0,
            'buildings': {
                'storage': self.players.get_entities_by_class(['T','C']),
                'training': self.players.get_entities_by_class(['B','S','A']),
                'ratio':{
                    'T' : len(self.players.entities_dict['T'])/sum(len(self.players.entities_dict[k]) for k in self.players.entities_dict.keys()) if 'T' in self.players.entities_dict.keys() else 0,
                    'H' : len(self.players.entities_dict['H'])/sum(len(self.players.entities_dict[k]) for k in self.players.entities_dict.keys()) if 'H' in self.players.entities_dict.keys() else 0,
                    'C' : len(self.players.entities_dict['C'])/sum(len(self.players.entities_dict[k]) for k in self.players.entities_dict.keys()) if 'C' in self.players.entities_dict.keys() else 0,
                    'F' : len(self.players.entities_dict['F'])/sum(len(self.players.entities_dict[k]) for k in self.players.entities_dict.keys()) if 'F' in self.players.entities_dict.keys() else 0,
                    'B' : len(self.players.entities_dict['B'])/sum(len(self.players.entities_dict[k]) for k in self.players.entities_dict.keys()) if 'B' in self.players.entities_dict.keys() else 0,
                    'S' : len(self.players.entities_dict['S'])/sum(len(self.players.entities_dict[k]) for k in self.players.entities_dict.keys()) if 'S' in self.players.entities_dict.keys() else 0,
                    'A' : len(self.players.entities_dict['A'])/sum(len(self.players.entities_dict[k]) for k in self.players.entities_dict.keys()) if 'A' in self.players.entities_dict.keys() else 0,
                    'K' : len(self.players.entities_dict['K'])/sum(len(self.players.entities_dict[k]) for k in self.players.entities_dict.keys()) if 'K' in self.players.entities_dict.keys() else 0,
                }
            },
            'units' : {
                'military_free': [self.players.linked_map.get_entity_by_id(m_id) for m_id in self.players.get_entities_by_class(['h', 'a', 's','m','c','x'], is_free=True)],
                'villager': [self.players.linked_map.get_entity_by_id(v_id) for v_id in self.players.get_entities_by_class(['v'])],
                'villager_free': [self.players.linked_map.get_entity_by_id(v_id) for v_id in self.players.get_entities_by_class(['v'],is_free=True)],

            },
            'enemy_id': None,
            'drop_off_id': self.players.ect(['T', 'C'], self.players.cell_Y, self.players.cell_X)[0] if self.players.ect(['T', 'C'], self.players.cell_Y, self.players.cell_X) else None,
            'player': self.players,
            'housing_crisis':(self.players.current_population >= self.players.get_current_population_capacity())
        }
        return context




