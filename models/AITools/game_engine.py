from GameField.map import Map
from Player.player import Player

class GameEngine:
    def __init__(self, map_width, map_height, num_players):
        self.map = Map(map_width, map_height)
        self.players = {i + 1: Player(team=i + 1) for i in range(num_players)}

    def add_entity(self, entity):
        player = self.players.get(entity.team)
        if player:
            player.add_entity(entity)
            self.map.add_entity(entity)

    def update(self, current_time):
        self.map.update_all_entities(current_time)
