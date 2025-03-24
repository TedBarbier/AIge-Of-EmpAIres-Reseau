import socket
from Game.reseau import Send

class GameEventHandler:
    def __init__(self, map, players, ai_profiles):
        self.map = map
        self.players = players
        self.ai_profiles = ai_profiles
        self.send = Send()


    def process_ai_decisions(self, tree):
        all_action = []
        context = self.get_context_for_player()
        actions = self.ai_profiles.decide_action(tree, context)
        dict_actions={"update":actions, "get_context_to_send" : self.get_context_to_send()}
        self.send.send_action_via_udp(dict_actions)
        all_action.append(actions)
        # self.send.send_action_via_udp(context)

        # Envoi des actions via UDP
        # for action in all_action:
        #     self.send.send_action_via_udp(action)
            # Vous pouvez également envoyer via IPC si nécessaire
            # self.send_action_via_ipc(action)
    
    def process_ai_decisions(self, tree):
        all_action = []
        context = self.get_context_for_player()
        actions = self.ai_profiles.decide_action(tree, context)
        dict_actions={"update":actions, "get_context_to_send" : self.get_context_to_send()}
        dict_actions['get_context_to_send']["build_repr"]=self.ai_profiles.repr
        self.send.send_action_via_udp(dict_actions)
        dict_actions['get_context_to_send']["build_repr"]=None
        all_action.append(actions)

 
    def receive_context(self):
        host = '127.0.0.1'
        port = 12345
        buffer_size = 1024
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s: # SOCK_DGRAM pour UDP
                s.bind((host, port))
                data, addr = s.recvfrom(buffer_size)
                if data:
                    received_message = data.decode('utf-8')
                    print("Message reçu : ", received_message)
                    return received_message
        except Exception as e:
            print(f"Erreur lors de la reception du message : {e}")
            return None

    def get_context_for_player(self):
        context = {
            'desired_villager_count': len(self.players.get_entities_by_class(['T','H','C','F','B','S','A','K']))+2,
            'resources': self.players.get_current_resources(),
            'ratio_military': len(self.players.get_entities_by_class(['h', 'a', 's', 'x', 'm', 'c'])) / len(self.players.get_entities_by_class(['h', 'a', 's', 'v', 'x', 'm', 'c'])) if len(self.players.get_entities_by_class(['h', 'a', 's', 'v', 'x', 'm', 'c'])) != 0 else 0,
            'buildings': {
                'storage': self.players.get_entities_by_class(['T','C']),
                'training': self.players.get_entities_by_class(['B','S','A']),
                'ratio': {
                    'T': len(self.players.entities_dict['T']) / sum(len(self.players.entities_dict[k]) for k in self.players.entities_dict.keys()) if 'T' in self.players.entities_dict.keys() else 0,
                    'H': len(self.players.entities_dict['H']) / sum(len(self.players.entities_dict[k]) for k in self.players.entities_dict.keys()) if 'H' in self.players.entities_dict.keys() else 0,
                    'C': len(self.players.entities_dict['C']) / sum(len(self.players.entities_dict[k]) for k in self.players.entities_dict.keys()) if 'C' in self.players.entities_dict.keys() else 0,
                    'F': len(self.players.entities_dict['F']) / sum(len(self.players.entities_dict[k]) for k in self.players.entities_dict.keys()) if 'F' in self.players.entities_dict.keys() else 0,
                    'B': len(self.players.entities_dict['B']) / sum(len(self.players.entities_dict[k]) for k in self.players.entities_dict.keys()) if 'B' in self.players.entities_dict.keys() else 0,
                    'S': len(self.players.entities_dict['S']) / sum(len(self.players.entities_dict[k]) for k in self.players.entities_dict.keys()) if 'S' in self.players.entities_dict.keys() else 0,
                    'A': len(self.players.entities_dict['A']) / sum(len(self.players.entities_dict[k]) for k in self.players.entities_dict.keys()) if 'A' in self.players.entities_dict.keys() else 0,
                    'K': len(self.players.entities_dict['K']) / sum(len(self.players.entities_dict[k]) for k in self.players.entities_dict.keys()) if 'K' in self.players.entities_dict.keys() else 0,
                }
            },
            'units': {
                'military_free': [self.players.linked_map.get_entity_by_id(m_id) for m_id in self.players.get_entities_by_class(['h', 'a', 's', 'm', 'c', 'x'], is_free=True)],
                'villager': [self.players.linked_map.get_entity_by_id(v_id) for v_id in self.players.get_entities_by_class(['v'])],
                'villager_free': [self.players.linked_map.get_entity_by_id(v_id) for v_id in self.players.get_entities_by_class(['v'], is_free=True)],
            },
            'enemy_id': None,
            'drop_off_id': self.players.ect(['T', 'C'], self.players.cell_Y, self.players.cell_X)[0] if self.players.ect(['T', 'C'], self.players.cell_Y, self.players.cell_X) else None,
            'player': self.players,
            'housing_crisis': (self.players.current_population >= self.players.get_current_population_capacity())
        }
        return context

    def get_context_to_send(self):
        context ={
            'resources': self.players.get_current_resources(),
            'buildings': {
                'storage': self.players.get_entities_by_class(['T','C']),
                'training': self.players.get_entities_by_class(['B','S','A']),
                'ratio': {
                    'T': len(self.players.entities_dict['T']) / sum(len(self.players.entities_dict[k]) for k in self.players.entities_dict.keys()) if 'T' in self.players.entities_dict.keys() else 0,
                    'H': len(self.players.entities_dict['H']) / sum(len(self.players.entities_dict[k]) for k in self.players.entities_dict.keys()) if 'H' in self.players.entities_dict.keys() else 0,
                    'C': len(self.players.entities_dict['C']) / sum(len(self.players.entities_dict[k]) for k in self.players.entities_dict.keys()) if 'C' in self.players.entities_dict.keys() else 0,
                    'F': len(self.players.entities_dict['F']) / sum(len(self.players.entities_dict[k]) for k in self.players.entities_dict.keys()) if 'F' in self.players.entities_dict.keys() else 0,
                    'B': len(self.players.entities_dict['B']) / sum(len(self.players.entities_dict[k]) for k in self.players.entities_dict.keys()) if 'B' in self.players.entities_dict.keys() else 0,
                    'S': len(self.players.entities_dict['S']) / sum(len(self.players.entities_dict[k]) for k in self.players.entities_dict.keys()) if 'S' in self.players.entities_dict.keys() else 0,
                    'A': len(self.players.entities_dict['A']) / sum(len(self.players.entities_dict[k]) for k in self.players.entities_dict.keys()) if 'A' in self.players.entities_dict.keys() else 0,
                    'K': len(self.players.entities_dict['K']) / sum(len(self.players.entities_dict[k]) for k in self.players.entities_dict.keys()) if 'K' in self.players.entities_dict.keys() else 0,
                }
            },
            'units': {
                'military_free': [self.players.get_entities_by_class(['h', 'a', 's', 'm', 'c', 'x'], is_free=True)],
                'villager': [self.players.get_entities_by_class(['v'])],
                'villager_free': [self.players.get_entities_by_class(['v'], is_free=True)],
            },
            'enemy_id': None,
            'drop_off_id': self.players.ect(['T', 'C'], self.players.cell_Y, self.players.cell_X)[0] if self.players.ect(['T', 'C'], self.players.cell_Y, self.players.cell_X) else None,
            'player': self.players.team,
            'strategy': self.players.ai_profile.strategy,
            'build_repr' : None
        }
        return context
    
    def get_all_context(self):
        return self.players.all_context

    def update_all_context(self, send):
        all_context=self.players.all_context
        all_context[send['player']]=send
        