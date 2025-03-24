# gameloop.py
import pygame
import tkinter as tk
import socket
import select
from tkinter import messagebox, Button, Tk
import socket # Import socket for networking
import json # Import json for networking

from ImageProcessingDisplay import UserInterface, EndMenu, StartMenu, PauseMenu, IAMenu, MultiplayerMenu
from GLOBAL_VAR import *
from Game.game_state import *
from Game.reseau import *


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
        self.iamenu = None # IAMenu will be instantiated when needed
        self.multiplayer_menu = MultiplayerMenu(self.screen) # Instantiate MultiplayerMenu
        self.action_in_progress = False
        self.num_players = 1
        self.udp_socket_to_receive = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket_to_receive.bind(("127.0.0.1", 1234))
        self.reseau=Send()
        self.ai_config_values = None # To store AI config values after IAMenu confirmation


    def string_to_dict(self, string_data):
        """
        Transforme une chaîne de caractères en dictionnaire Python.
        ... (rest of the docstring as before)
        """
        try:
            dictionnaire = json.loads(string_data)
            return dictionnaire
        except json.JSONDecodeError as e:
            print(f"Erreur de décodage JSON : La chaîne n'est pas un JSON valide.\nErreur : {e}")
            return None

    # def handle_message(self, dt, camera, screen):
    #     buffersize = 8192
    #     readable, _, _ = select.select([self.udp_socket_to_receive], [], [], 0)
    #     for s in readable:
    #         data, addr = s.recvfrom(buffersize)
    #         if data:
    #             received_message = data.decode('utf-8')
    #             if "Map" in received_message:
    #                 dict = self.string_to_dict(received_message)
    #                 self.state.map.players_dict[self.num_players].reset(dict["Map"]["nb_cellX"], dict["Map"]["nb_cellY"], self.num_players)
    #                 self.state.selected_mode = dict["Map"]["mode"]
    #                 self.state.selected_map_type = dict["Map"]["map_type"]
    #                 self.state.selected_players = dict["Map"]["nb_max_players"]
    #                 self.state.speed = dict["Map"]["speed"]
    #                 self.state.map = Map(dict["Map"]["nb_cellX"], dict["Map"]["nb_cellY"])
    #                 self.state.map.seed = dict["Map"]["seed"]
    #                 self.state.map.score_players = dict["Map"]["score_players"]
    #                 self.state.polygon = dict["Map"]["polygon"]
    #                 self.num_players += 1
    #                 self.state.start_game(self.num_players)
    #                 self.state.map._place_player_starting_areas_multi(self.state.selected_mode, self.state.selected_players, self.num_players, 1, self.state.polygon)
    #                 self.state.states = PLAY
    #                 self.reseau.send_action_via_udp({"players": self.num_players})
    #             elif "players" in received_message:
    #                 dict = self.string_to_dict(received_message)
    #                 team_joueur_rejoignant = int(dict["players"])
    #                 self.state.map._place_player_starting_areas_multi(self.state.selected_mode, self.state.selected_players, self.num_players, team_joueur_rejoignant, self.state.polygon)
    #             elif "speed" in received_message:
    #                 dict = self.string_to_dict(received_message)
    #                 self.state.set_speed(int(dict["speed"]))
    #             elif "quit" in received_message:
    #                 dict = self.string_to_dict(received_message)
    #                 self.state.map.players_dict.pop(dict["quit"])
    #                 for player in self.state.map.players_dict.keys():
    #                     self.state.map.players_dict[player-1]  = self.state.map.players_dict[player].values()
    #                     self.state.map.players_dict.pop(player)
    #                 self.num_players -= 1
    #             elif "update" in received_message:
    #                 dict = self.string_to_dict(received_message)
    #                 if dict["get_context_to_send"]["player"] != self.num_players and dict["update"] is not None:
    #                     player=self.state.map.players_dict[dict["get_context_to_send"]["player"]]
    #                     if dict["get_context_to_send"]["strategy"] == "aggressive":
    #                         self.state.map.players_dict[self.num_players].ai_profile._aggressive_strategy(dict["update"], dict["get_context_to_send"],player)
    #                     elif dict["get_context_to_send"]["strategy"] == "defensive":
    #                         self.state.map.players_dict[self.num_players].ai_profile._defensive_strategy(dict["update"], dict["get_context_to_send"],player)
    #                     elif dict["get_context_to_send"]["strategy"] == "balanced":
    #                         self.state.map.players_dict[self.num_players].ai_profile._balanced_strategy(dict["update"], dict["get_context_to_send"],player)
    #             else:
    #                 return received_message

    def handle_message(self, dt, camera, screen):
        buffersize = 8192
        readable, _, _ = select.select([self.udp_socket_to_receive], [], [], 0)

        for s in readable:
            data, addr = s.recvfrom(buffersize)
            if data:
                received_message = data.decode('utf-8')
                dict_message = self.string_to_dict(received_message)

                if "Map" in received_message:
                    map_data = dict_message["Map"]
                    self.state.map.players_dict[self.num_players].reset(
                        map_data["nb_cellX"], map_data["nb_cellY"], self.num_players, map_data["ai_profile"]
                    )
                    self.state.selected_mode = map_data["mode"]
                    self.state.selected_map_type = map_data["map_type"]
                    self.state.selected_players = map_data["nb_max_players"]
                    self.state.speed = map_data["speed"]
                    self.state.map = Map(map_data["nb_cellX"], map_data["nb_cellY"])
                    self.state.map.seed = map_data["seed"]
                    self.state.map.score_players = map_data["score_players"]
                    self.state.polygon = map_data["polygon"]
                    self.num_players += 1
                    self.state.start_game(self.num_players, self.ai_config_values)
                    self.state.map._place_player_starting_areas_multi(
                        self.state.selected_mode, self.state.selected_players,
                        self.num_players, 1, self.state.polygon, map_data["ai_profile"]
                    )
                    self.state.states = PLAY
                    self.reseau.send_action_via_udp({"players": self.num_players, "ai_profile": self.ai_config_values})

                elif "players" in received_message:
                    team_joueur_rejoignant = int(dict_message["players"])
                    self.state.map._place_player_starting_areas_multi(
                        self.state.selected_mode, self.state.selected_players,
                        self.num_players,team_joueur_rejoignant, self.state.polygon, dict_message["ai_profile"]
                    )

                elif "speed" in received_message:
                    self.state.set_speed(int(dict_message["speed"]))

                elif "quit" in received_message:
                    player_id = dict_message["quit"]
                    self.state.map.players_dict.pop(player_id)
                    self.num_players -= 1
                    # Re-index players_dict
                    self.state.map.players_dict = {
                        i: self.state.map.players_dict[k]
                        for i, k in enumerate(sorted(self.state.map.players_dict.keys()))
                    }

                elif "update" in received_message:
                    context = dict_message["get_context_to_send"]
                    if context["player"] != self.num_players and dict_message["update"] is not None:
                        if not self.state.map.players_dict[context["player"]]:
                            print("context", context)
                        else:
                            player = self.state.map.players_dict[context["player"]]
                            strategy = context["strategy"]
                            ai_profile = self.state.map.players_dict[self.num_players].ai_profile

                            if strategy == "aggressive":
                                ai_profile._aggressive_strategy(dict_message["update"], context, player)
                            elif strategy == "defensive":
                                ai_profile._defensive_strategy(dict_message["update"], context, player)
                            elif strategy == "balanced":
                                ai_profile._balanced_strategy(dict_message["update"], context, player)
                else:
                    return received_message


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

                # Instantiate IAMenu for solo mode
                self.iamenu = IAMenu(self.screen, self.state.selected_players, is_multiplayer=False) # is_multiplayer=False
                self.state.states = CONFIG_IA # Go to CONFIG_IA state

                if self.state.display_mode == TERMINAL:
                    self.state.set_screen_size(20, 20)
                    pygame.display.set_mode(
                        (self.state.screen_width, self.state.screen_height),
                        pygame.HWSURFACpygame.HWSURFACE | pygame.DOUBLEBUF,
                    )
            elif start_menu_action == "multiplayer": # If multiplayer is clicked
                self.num_players = 1
                self.state.is_multiplayer = True
                self.state.set_map_size(self.startmenu.map_cell_count_x, self.startmenu.map_cell_count_y)
                self.state.set_map_type(self.startmenu.map_options[self.startmenu.selected_map_index])
                self.state.set_difficulty_mode(self.startmenu.selected_mode_index)
                self.state.set_display_mode(self.startmenu.display_mode)
                self.state.set_players(self.startmenu.selected_player_count)

                # Instantiate IAMenu for multiplayer mode - configure for player 1 initially
                self.iamenu = IAMenu(self.screen, self.state.selected_players, num_player=self.num_players, is_multiplayer=True) # is_multiplayer=True, num_player=1
                self.state.states = CONFIG_IA # Go to CONFIG_IA state

                if self.state.display_mode == TERMINAL:
                    self.state.set_screen_size(20, 20)
                    pygame.display.set_mode(
                        (self.state.screen_width, self.state.screen_height),
                        pygame.HWSURFACpygame.HWSURFACE | pygame.DOUBLEBUF,
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



    def handle_config_events(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: # Vérifie que c'est le bouton gauche
                self.iamenu.handle_click(event.pos) # handle_click gère maintenant le début du drag

        elif event.type == pygame.MOUSEMOTION: # Gestion du mouvement de la souris pour le drag
            if self.iamenu and self.iamenu.dragging_slider: # Vérifie que iamenu est instancié et qu'un slider est glissé
                slider_set = self.iamenu.dragging_slider["slider_set"]
                slider_type = self.iamenu.dragging_slider["type"]
                slider_rect = slider_set[slider_type]

                # Calculer la nouvelle valeur du slider en fonction de la position X de la souris
                mouse_x_relative = event.pos[0] - slider_rect.x
                value_ratio = max(0, min(1, mouse_x_relative / slider_rect.width)) # Ratio entre 0 et 1
                new_value = 1 + 2 * value_ratio # Convertir ratio en valeur entre 1 et 3
                new_value = round(max(1, min(3, new_value)), 1) # Assurer valeur entre 1 et 3 et arrondir à 0.1

                if slider_type == "aggressive":
                    slider_set["aggressive_value"] = new_value
                elif slider_type == "defensive":
                    slider_set["defensive_value"] = new_value

        elif event.type == pygame.MOUSEBUTTONUP: # Fin du glissement et confirmation potentielle
            if event.button == 1: # Vérifie que c'est le bouton gauche
                if self.iamenu: # Vérifie que iamenu est instancié avant d'accéder à dragging_slider
                    self.iamenu.dragging_slider = None # Arrêter le glissement quand le bouton de la souris est relâché
                    ai_values = self.iamenu.handle_click(event.pos) # Ré-appelle handle_click pour vérifier si "Confirmer" est cliqué

                    if ai_values: # <--- Déplacer la logique de démarrage du jeu ICI, dans MOUSEBUTTONUP et seulement si ai_values est retourné (bouton "Confirmer" cliqué)
                        self.state.ai_config_values = ai_values # Stocker les valeurs de l'IA
                        if self.state.is_multiplayer:
                            self.state.start_game(ai_config=self.state.ai_config_values)
                            map_send = {"Map" :{
                                "nb_cellX" : self.state.map.nb_CellX,
                                "nb_cellY" : self.state.map.nb_CellY,
                                "seed" : self.state.map.seed,
                                "map_type" : self.state.selected_map_type,
                                "mode" : self.state.selected_mode,
                                "speed" : self.state.speed,
                                "nb_max_players" : self.state.selected_players,
                                "polygon" : self.state.polygon,
                                "team_player": 1,
                                "score_players" : self.state.map.score_players,
                                "ai_profile" : self.state.ai_config_values
                            }}
                            self.reseau.send_action_via_udp(map_send)
                            self.state.states = PLAY
                        else:
                            self.state.start_game()
                            self.state.states = PLAY




    def handle_pause_events(self,dt, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            result = self.pausemenu.handle_click(event.pos, self.state)
            if result == "main_menu" and self.state.is_multiplayer:
                self.reseau.send_action_via_udp({"quit": self.num_players})

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
            self.reseau.send_action_via_udp({"speed": self.state.speed+0.1})
        if keys[pygame.K_2]:
            self.state.set_speed(self.state.speed-0.1)
            self.reseau.send_action_via_udp({"speed": self.state.speed-0.1})

        if keys[pygame.K_3]:
            self.state.set_speed(0.3)
            if self.state.is_multiplayer:
                self.reseau.send_action_via_udp({"speed": 0.3})
        if keys[pygame.K_4]:
            self.state.set_speed(1)
            if self.state.is_multiplayer:
                self.reseau.send_action_via_udp({"speed": 1})
        if keys[pygame.K_5]:
            self.state.set_speed(2)
            if self.state.is_multiplayer:
                self.reseau.send_action_via_udp({"speed": 2})
        if keys[pygame.K_6]:
            self.state.set_speed(8)
            if self.state.is_multiplayer:
                self.reseau.send_action_via_udp({"speed": 8})

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
                pygame.display.set_mode((self.state.screen_width, self.state.screen_height), pygame.HWSURFACpygame.HWSURFACE | pygame.DOUBLEBUF | pygame.RESIZABLE)
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
        if not (self.state.states == PAUSE) or self.state.is_multiplayer: # Ne pas mettre à jour l'état du jeu dans le menu multijoueur ou pause
            self.state.map.update_all_events(dt*self.state.speed, self.state.camera, self.screen)
            self.state.endgame()

    def render_display(self, dt, mouse_x, mouse_y):
        if self.state.states == START: # Utiliser START ici
            self.startmenu.draw()
        elif self.state.states == CONFIG_IA: # Render IAMenu when in CONFIG_IA state
            self.iamenu.draw()
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
                elif self.state.states == CONFIG_IA: # Handle events for CONFIG_IA state
                    self.handle_config_events(event)
                elif self.state.states == PAUSE:
                    self.handle_pause_events(dt, event)
                elif self.state.states == PLAY:
                    self.state.change_music(self.state.map.state)
                    self.handle_play_events(event, mouse_x, mouse_y, dt)
                elif self.state.states == END:
                    self.handle_end_events(event)

            if self.state.mouse_held:
                self.state.map.minimap.update_camera(self.state.camera, mouse_x, mouse_y)

            if not (self.state.states == START or self.state.states == CONFIG_IA): # No keyboard input in START and CONFIG_IA
                self.handle_keyboard_inputs(move_flags, dt)

            self.state.update(dt)

            if self.state.states == PLAY:
                self.update_game_state(dt)
                if self.state.is_multiplayer:
                    self.handle_message(dt, self.state.camera, self.screen)
            elif self.state.states == CONFIG_IA:
                pygame.mouse.set_visible(True) # Show mouse cursor in config menu


            self.render_display(dt, mouse_x, mouse_y)


        pygame.quit()
