# gameloop.py
import subprocess
import pygame
import tkinter as tk
import socket
import select
from tkinter import messagebox, Button, Tk
import socket # Import socket for networking

from ImageProcessingDisplay import UserInterface, EndMenu, StartMenu, PauseMenu, IAMenu, MultiplayerMenu
from GLOBAL_VAR import *
from Game.game_state import *
from Game.reseau import *

executable_path = '../Reseau/boucle/serv'


class GameLoop:
    def __init__(self):
        pygame.init()

        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.RESIZABLE)
        self.screen.set_alpha(None)
        pygame.display.set_caption("Age Of Empaire II")

        pygame.mouse.set_visible(False)

        self.font = pygame.font.Font(None, 24)

        self.clock = pygame.time.Clock()

        self.state = GameState()
        self.state.set_screen_size(self.screen.get_width(), self.screen.get_height())
        self.startmenu = StartMenu(self.screen)
        self.pausemenu = PauseMenu(self.screen)
        self.endmenu = EndMenu(self.screen)
        self.ui = UserInterface(self.screen)
        #self.iamenu = IAMenu(self.screen, self.state.selected_players) # Assuming IAMenu is used somewhere
        self.multiplayer_menu = MultiplayerMenu(self.screen) # Instantiate MultiplayerMenu
        self.action_in_progress = False
        self.num_players = 1
        self.udp_socket_to_receive = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket_to_receive.bind(("127.0.0.1", 1234))
        self.polygon = None
        self.reseau=Send()
    
    def string_to_dict(self, string_data):
        """
        Transforme une chaîne de caractères en dictionnaire Python.

        Cette fonction tente d'interpréter la chaîne de caractères comme du JSON.
        Si la chaîne est au format JSON valide, elle sera convertie en dictionnaire.
        Sinon, une erreur sera levée.

        Args:
            string_data: La chaîne de caractères à transformer.

        Returns:
            Un dictionnaire Python si la chaîne est au format JSON valide.
            None si la chaîne n'est pas au format JSON valide (et une erreur est affichée).
        """
        try:
            # Utilise json.loads() pour parser la chaîne JSON et la convertir en dictionnaire
            dictionnaire = json.loads(string_data)
            return dictionnaire
        except json.JSONDecodeError as e:
            print(f"Erreur de décodage JSON : La chaîne n'est pas un JSON valide.\nErreur : {e}")
            return None # Ou vous pouvez choisir de lever l'exception à nouveau, ou retourner une valeur par défaut


    def handle_message(self):
        buffersize = 1024
        readable, _ , _ = select.select([self.udp_socket_to_receive], [], [], 0.1) 
        for s in readable:
            data, addr = s.recvfrom(buffersize)
            if data:
                received_message = data.decode('utf-8')
                
                if "Map" in received_message:
                    print("on reçoit la map")
                    dict = self.string_to_dict(received_message)
                    self.state.selected_mode = dict["Map"]["mode"]
                    self.state.selected_map_type = dict["Map"]["map_type"]
                    self.state.speed = dict["Map"]["speed"]
                    self.state.map.nb_CellX = dict["Map"]["nb_cellX"]
                    self.state.map.nb_CellY = dict["Map"]["nb_cellY"]
                    self.state.map.tile_size_2d = dict["Map"]["tile_size_2d"]
                    self.state.map.region_division = dict["Map"]["region_division"]
                    self.state.map.seed = dict["Map"]["seed"]
                    self.state.map.score_players = dict["Map"]["score_players"]
                    self.num_players += 1
                    self.state.start_game(self.num_players)
                elif received_message == "\"Rejoindre la partie\"" and self.num_players < self.state.selected_players:
                        self.add_new_player()
                        self.reseau.send_action_via_udp("Vous avez rejoint la partie")
                else:
                    return(received_message)
            
    def create_info_entity(self):
        representation_list_letter=['v','h', 'a', 's', 'x', 'm', 'c', 'T', 'H', 'C', 'F', 'B', 'S', 'A', 'K', 'W', 'G']
        map_dict={}
        for representation in representation_list_letter:
            map_send=self.state.map.players_dict[1].entities_dict.get(representation, None)
            if map_send is not None:
                for key in map_send.keys():
                    map_dict[key]=map_send[key].to_network_dict()
        return map_dict

    def handle_start_events(self, event):
        if pygame.key.get_pressed()[pygame.K_F12]:
            loaded = self.state.load()
            if loaded:
                pygame.display.set_mode(
                    (self.state.screen_width, self.state.screen_height),
                    pygame.HWSURFACpygame.HWSURFACE | pygame.DOUBLEBUF | pygame.RESIZABLE,
                )
                if self.state.states == PAUSE:
                    self.state.states = PLAY

        elif event.type == pygame.MOUSEBUTTONDOWN:

            start_menu_action = self.startmenu.handle_click(event.pos) # Get action from start menu
            if start_menu_action == "play":
                self.state.set_map_size(self.startmenu.map_cell_count_x, self.startmenu.map_cell_count_y)
                self.state.set_map_type(self.startmenu.map_options[self.startmenu.selected_map_index])
                self.state.set_difficulty_mode(self.startmenu.selected_mode_index)
                self.state.set_display_mode(self.startmenu.display_mode)
                self.state.set_players(self.startmenu.selected_player_count)
                self.state.start_game()
                self.state.states = PLAY

                if self.state.display_mode == TERMINAL:
                    self.state.set_screen_size(20, 20)
                    pygame.display.set_mode(
                        (self.state.screen_width, self.state.screen_height),
                        pygame.HWSURFACE | pygame.DOUBLEBUF,
                    )
            elif start_menu_action == "multiplayer": # If multiplayer is clicked
                self.state.is_multiplayer = True
                self.state.set_map_size(self.startmenu.map_cell_count_x, self.startmenu.map_cell_count_y)
                self.state.set_map_type(self.startmenu.map_options[self.startmenu.selected_map_index])
                self.state.set_difficulty_mode(self.startmenu.selected_mode_index)
                self.state.set_display_mode(self.startmenu.display_mode)
                self.state.set_players(self.startmenu.selected_player_count)
                self.state.start_game()
                self.state.states = PLAY

                print(self.state.map.entity_id_dict.values())
                map_send = {"Map" :{
                    "nb_cellX" : self.state.map.nb_CellX,
                    "nb_cellY" : self.state.map.nb_CellY,
                    "tile_size_2d" : self.state.map.tile_size_2d,
                    "region_division" : self.state.map.region_division,
                    "seed" : self.state.map.seed,
                    "map_type" : self.state.selected_map_type,
                    "mode" : self.state.selected_mode,
                    "speed" : self.state.speed,
                    # "entity_matrix" : self.state.map.entity_matrix,
                    # "entity_id_dict" : self.state.map.entity_id_dict,
                    # "resource_id_dict" : self.state.map.resource_id_dict,
                    # "dead_entities" : self.state.map.dead_entities,
                    "score_players" : self.state.map.score_players,
                    # "player_dict" : self.state.map.players_dict
                }}

                print("create",self.create_info_entity())
                map_send=self.create_info_entity()
                self.reseau.send_action_via_udp(map_send)
                print("envoie de la map")
                print(map_send)

                if self.state.display_mode == TERMINAL:
                    self.state.set_screen_size(20, 20)
                    pygame.display.set_mode(
                        (self.state.screen_width, self.state.screen_height),
                        pygame.HWSURFACE | pygame.DOUBLEBUF,
                    )
            else:
                # Check if clicking on player count or cell count enables editing
                center_x, center_y = self.state.screen_width // 2, self.state.screen_height // 2
                player_count_rect = pygame.Rect(center_x - 75, center_y - 20, 150, 50)  # Rect for player count
                map_cell_rect_x = pygame.Rect(center_x - 75, center_y - 280, 150, 50)  # Rect for X cell count
                map_cell_rect_y = pygame.Rect(center_x - 75, center_y - 185, 150, 50)  # Rect for Y cell count

                if player_count_rect.collidepoint(event.pos):
                    self.startmenu.start_editing_player_count()
                elif map_cell_rect_x.collidepoint(event.pos):
                    self.startmenu.start_editing_map_cell_count_x()
                elif map_cell_rect_y.collidepoint(event.pos):
                    self.startmenu.start_editing_map_cell_count_y()

        elif event.type == pygame.KEYDOWN:
            # Handle keyboard events for editing
            self.startmenu.handle_keydown(event)

    # def handle_multiplayer_menu_events(self, event): # New event handler for multiplayer menu
    #     if event.type == pygame.MOUSEBUTTONDOWN:
    #         multiplayer_menu_action = self.multiplayer_menu.handle_click(event.pos)
    #         if multiplayer_menu_action == "principal_solo":
    #             self.state.states = START # Retour à l'état START
    #         elif multiplayer_menu_action == "heberger":
    #             print("Hosting game (placeholder)") # Placeholder for hosting logic
    #             self.state.is_multiplayer = True # Set multiplayer flag
    #             #self.state.states = START # Retour à l'état START pour le moment, ou peut-être un état d'attente
    #         elif isinstance(multiplayer_menu_action, tuple) and multiplayer_menu_action[0] == "rejoindre":
    #             ip_to_join = multiplayer_menu_action[1]
    #             print([executable_path, ip_to_join])
    #             run_process = subprocess.run([executable_path, ip_to_join], capture_output=True, text=True)
    #             self.state.is_multiplayer = True # Set multiplayer flag
    #             # Afficher la sortie du programme
    #             print("Sortie du programme :")
    #             print(run_process.stdout)

    #             # Afficher les erreurs, le cas échéant
    #             if run_process.stderr:
    #                 print("Erreurs :")
    #                 print(run_process.stderr)
    #             self.reseau.send_action_via_udp("Rejoindre la partie")
    #             #self.state.states = START # Retour à l'état START pour le moment, ou peut-être un état d'attente
    #         elif multiplayer_menu_action == "annuler_hebergement":
    #             self.multiplayer_menu.menu_state = "principal" # Reset multiplayer menu state
    #         elif multiplayer_menu_action == "start_hosting": # Handle "Heberger_config" click
    #             self.state.is_multiplayer = True
    #             map_type = self.multiplayer_menu.map_options[self.multiplayer_menu.selected_map_index]
    #             mode = self.multiplayer_menu.selected_mode_index
    #             player_count = self.multiplayer_menu.selected_player_count
    #             map_cell_count_x = self.multiplayer_menu.map_cell_count_x
    #             map_cell_count_y = self.multiplayer_menu.map_cell_count_y

    #             self.state.set_map_size(map_cell_count_x, map_cell_count_y) # Set map size from multiplayer menu
    #             self.state.set_players(player_count) # Set player count
    #             self.state.set_difficulty_mode(mode) # Set mode based on string
    #             self.state.set_map_type(map_type) # set map type based on string
    #             self.polygon = self.state.map.generate_map_multi(map_type, mode, player_count) # Call generate_map_multi

    #             self.state.states = PLAY # Change state to PLAY


        # elif event.type == pygame.KEYDOWN:
        #     keydown_action = self.multiplayer_menu.handle_keydown(event)
        #     if keydown_action is not None and isinstance(keydown_action, tuple) and keydown_action[0] == "rejoindre":
        #         ip_to_join = keydown_action[1]
        #         print(f"Joining game at IP: {ip_to_join} (from keydown) (placeholder)") # Placeholder for joining logic
        #         self.state.is_multiplayer = True
        #         self.state.states = START # Retour à l'état START pour le moment, ou peut-être un état d'attente

        # self.multiplayer_menu.update()


    # def handle_config_events(self,dt, event):
    #     if event.type == pygame.MOUSEBUTTONDOWN:
    #         self.iamenu.handle_click(event.pos, self.state)

    def handle_pause_events(self,dt, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.pausemenu.handle_click(event.pos, self.state)

    def handle_end_events(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.endmenu.handle_click(event.pos, self.state)

    def handle_play_events(self, event, mouse_x, mouse_y, dt):
        if event.type == pygame.MOUSEBUTTONDOWN:

            if event.button == LEFT_CLICK:
                entity_id = self.state.map.mouse_get_entity(self.state.camera, mouse_x, mouse_y)

                self.state.mouse_held = True
        elif event.type == pygame.MOUSEBUTTONUP:
            self.state.mouse_held = False
        elif event.type == pygame.MOUSEWHEEL:
            if event.y == 1:
                self.state.camera.adjust_zoom(dt, 0.1, SCREEN_WIDTH, SCREEN_HEIGHT)
            elif event.y == -1:
                self.state.camera.adjust_zoom(dt, -0.1, SCREEN_WIDTH, SCREEN_HEIGHT)


    def handle_keyboard_inputs(self, move_flags, dt):
        keys = pygame.key.get_pressed()
        scale = 2 if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT] else 1

        # Zoom de la caméra
        if keys[pygame.K_KP_PLUS] or keys[pygame.K_k]:
            self.state.camera.adjust_zoom(dt, 0.1, SCREEN_WIDTH, SCREEN_HEIGHT)
        elif keys[pygame.K_KP_MINUS] or keys[pygame.K_j]:
            self.state.camera.adjust_zoom(dt, -0.1, SCREEN_WIDTH, SCREEN_HEIGHT)

        # Changer la vitesse de Jeu
        if keys[pygame.K_1]:
            self.state.set_speed(self.state.speed+0.1)
        if keys[pygame.K_2]:
            self.state.set_speed(self.state.speed-0.1)

        if keys[pygame.K_3]:
            self.state.set_speed(0.3)
        if keys[pygame.K_4]:
            self.state.set_speed(1)
        if keys[pygame.K_5]:
            self.state.set_speed(2)
        if keys[pygame.K_6]:
            self.state.set_speed(8)

        # Basculer le mode d'affichage
        if keys[pygame.K_F10]:
            self.state.toggle_display_mode(self)

        # Sauvegarder et charger
        if keys[pygame.K_F11]:
            self.state.set_screen_size(self.screen.get_width(), self.state.screen_height())
            self.state.save()

        if keys[pygame.K_F12]:
            loaded = self.state.load()
            if loaded:
                pygame.display.set_mode((self.state.screen_width, self.state.screen_height), pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.RESIZABLE)
                if self.state.states == PAUSE:
                    self.state.toggle_pause()

        # Générer fichier HTML
        if keys[pygame.K_TAB]:
            self.state.generate_html_file(self.state.map.players_dict)
            self.state.toggle_pause()

        # Pause
        if keys[pygame.K_p] or keys[pygame.K_ESCAPE] :
            self.state.toggle_pause()

        # Mouvement de la caméra
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            move_flags |= 0b0010
        if keys[pygame.K_LEFT] or keys[pygame.K_q]:
            move_flags |= 0b0001
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            move_flags |= 0b0100
        if keys[pygame.K_UP] or keys[pygame.K_z]:
            move_flags |= 0b1000

        if keys[pygame.K_f]:
            self.state.toggle_fullscreen(self)

        # Overlays
        if keys[pygame.K_F1]:
            self.state.toggle_resources(self.ui)
        if keys[pygame.K_F2]:
            self.state.toggle_units(self.ui)
        if keys[pygame.K_F3]:
            self.state.toggle_builds(self.ui)
        if keys[pygame.K_F4]:
            self.state.toggle_all(self.ui)

        self.state.camera.move_flags = move_flags
        self.state.terminal_camera.move_flags = move_flags
        self.state.terminal_camera.move(dt)
        self.state.camera.move(dt, 5 * scale)

    def update_game_state(self, dt):
        if not (self.state.states == PAUSE): # Ne pas mettre à jour l'état du jeu dans le menu multijoueur ou pause
            self.state.map.update_all_events(dt*self.state.speed, self.state.camera, self.screen)
            self.state.endgame()

    def render_display(self, dt, mouse_x, mouse_y):
        if self.state.states == START: # Utiliser START ici
            self.startmenu.draw()
        # elif self.state.states == MULTIMENU: # Utiliser MULTIMENU ici
        #     self.multiplayer_menu.draw()
        # elif self.state.states == CONFIG:
        #     self.iamenu.draw()
        elif self.state.states == PAUSE:
            self.pausemenu.draw()
        elif self.state.states == END:
            self.endmenu.draw(self.state.map.score_players)
        elif self.state.states == PLAY:
            pygame.mouse.set_visible(False)
            if self.state.display_mode == ISO2D:
                self.state.map.display(dt, self.screen, self.state.camera, self.screen_width, self.screen_height)
                fps = int(self.clock.get_fps())
                fps_text = self.font.render(f"FPS: {fps}", True, (255, 255, 255))
                speed_text = self.font.render(f"speed: {self.state.speed:.1f}", True, (255, 255, 255))
                self.screen.blit(fps_text, (10, 10))
                self.screen.blit(speed_text, (100, 10))

                self.ui.draw_resources(self.state.map.players_dict)
            elif self.state.display_mode == TERMINAL:
                self.state.map.terminal_display(dt, self.state.terminal_camera)
        self.screen.blit(CURSOR_IMG, (mouse_x, mouse_y))
        pygame.display.flip()


    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS)
            self.screen_width, self.screen_height = self.screen.get_width(), self.screen.get_height()
            move_flags = 0
            mouse_x, mouse_y = pygame.mouse.get_pos()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if self.state.states == START: # Utiliser START ici
                    self.state.change_music("start")
                    self.handle_start_events(event)
                # elif self.state.states == MULTIMENU: # Utiliser MULTIMENU ici
                #     self.handle_multiplayer_menu_events(event)
                elif self.state.states == PAUSE:
                    self.handle_pause_events(dt, event)
                elif self.state.states == PLAY:
                    self.state.change_music(self.state.map.state)
                    self.handle_play_events(event, mouse_x, mouse_y, dt)
                elif self.state.states == END:
                    self.handle_end_events(event)

            if self.state.mouse_held:
                self.state.map.minimap.update_camera(self.state.camera, mouse_x, mouse_y)

            if not (self.state.states == START): # Pas d'input clavier dans le menu start et multijoueur
                self.handle_keyboard_inputs(move_flags, dt)

            self.state.update(dt)

            if self.state.states == PLAY:
                self.update_game_state(dt)
                self.reseau.send_action_via_udp(self.create_info_entity())
                if self.state.is_multiplayer:
                    self.handle_message()
            self.render_display(dt, mouse_x, mouse_y)


        pygame.quit()


if __name__ == "__main__":
    game = GameLoop()
    game.run()