from game_engine import GameEngine
from game_event_handler import GameEventHandler  

# Initialisation
engine = GameEngine(map_width=50, map_height=50, num_players=2)
event_handler = GameEventHandler(map=engine.map, players=engine.players)

# Simulation
engine.update(current_time=1000)
event_handler.run_event_cycle()
