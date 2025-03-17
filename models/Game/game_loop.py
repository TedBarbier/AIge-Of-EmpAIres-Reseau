import pygame
import tkinter as tk
from tkinter import messagebox, Button, Tk

from ImageProcessingDisplay import UserInterface, EndMenu, StartMenu, PauseMenu, IAMenu, MultiplayerMenu # Import MultiplayerMenu
from GLOBAL_VAR import *
from Game.game_state import *
import socket
import json


class GameLoop:
    def __init__(self, multiplayer_mode=None, server_ip=None):
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
        self.multimenu = MultiplayerMenu(self.screen) # Instantiate MultiplayerMenu here
        self.ui = UserInterface(self.screen)
        self.action_in_progress = False

        self.multiplayer_mode = multiplayer_mode
        self.server_ip = server_ip
        self.ipc_connexion = None
        self.ipc_socket = None
        self.num_players = 1

        if self.multiplayer_mode:
            self.initialiser_ipc()

    def add_new_player(self, mode=MARINES):
        self.num_players += 1
        self.state.map._place_player_starting_areas_multi(mode, self.num_players)
    
    def handle_new_players(self):
        if self.num_players <2:     # test à remplacer par la connexion d'un nouveau joueur mais c'est pour tester la méthode
            self.add_new_player(self)

    def initialiser_ipc(self):
        IPC_SOCKET_PATH = "/tmp/aoe_ipc.sock"

        if self.multiplayer_mode == "heberger":
            self.ipc_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            try:
                self.ipc_socket.bind(IPC_SOCKET_PATH)
                self.ipc_socket.listen(1)
                print(f"Serveur IPC en écoute sur: {IPC_SOCKET_PATH}")
                self.ipc_connexion, addr = self.ipc_socket.accept()
                print(f"Connexion IPC établie avec: {addr}")
            except socket.error as e:
                print(f"Erreur IPC (hébergement): {e}")
                self.multiplayer_mode = None

            self.generer_et_envoyer_carte_initiale()

        elif self.multiplayer_mode == "rejoindre":
            self.ipc_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            try:
                self.ipc_socket.connect(IPC_SOCKET_PATH)
                self.ipc_connexion = self.ipc_socket
                print(f"Connecté au serveur IPC sur: {IPC_SOCKET_PATH}")
            except socket.error as e:
                print(f"Erreur IPC (rejoindre): {e}")
                self.multiplayer_mode = None

            self.recevoir_carte_initiale()

    def generer_et_envoyer_carte_initiale(self):
        self.state.start_game()
        carte_data = self.state.map.to_dict()
        carte_json = json.dumps({"type": "initial_map", "map_data": carte_data})

        try:
            self.ipc_connexion.sendall(carte_json.encode())
            print("Carte initiale envoyée via IPC.")
        except (ConnectionResetError, BrokenPipeError, Exception) as e:
            print(f"Erreur d'envoi de la carte initiale via IPC: {e}")
            self.multiplayer_mode = None

    def recevoir_carte_initiale(self):
        try:
            carte_initiale_bytes = self.ipc_connexion.recv(4096 * 10)
            if not carte_initiale_bytes:
                print("Erreur: Aucune donnée reçue pour la carte initiale via IPC.")
                self.multiplayer_mode = None
                return
            carte_initiale_json = carte_initiale_bytes.decode()
            carte_initiale_data = json.loads(carte_initiale_json)
            carte_data = carte_initiale_data["map_data"]
            self.state.map.from_dict(carte_data)
            print("Carte initiale reçue via IPC.")

            self.state.reset_game_state_from_map()

            self.state.states = PLAY

        except (ConnectionResetError, BrokenPipeError, json.JSONDecodeError, Exception) as e:
            print(f"Erreur de réception/décodage de la carte initiale via IPC: {e}")
            self.multiplayer_mode = None

    def handle_start_events(self, event):
        if pygame.key.get_pressed()[pygame.K_F12]:
            loaded = self.state.load()
            if loaded:
                pygame.display.set_mode(
                    (self.state.screen_width, self.state.screen_height),
                    pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.RESIZABLE,
                )
                if self.state.states == PAUSE:
                    self.state.states = PLAY

        elif event.type == pygame.MOUSEBUTTONDOWN:
            menu_result_start = self.startmenu.handle_click(event.pos) # Get result from start menu
            if menu_result_start == "jeu_solo":
                # --- Lancement du jeu SOLO ---
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
            elif menu_result_start == "multijoueur": # If "Multijoueur" button is clicked
                self.state.states = MULTIMENU # Change game state to MULTIMENU
            else:
                # ... (Gestion des clics pour l'édition du menu START - inchangé) ...
                center_x, center_y = self.state.screen_width // 2, self.state.screen_height // 2
                player_count_rect = pygame.Rect(center_x - 75, center_y - 20, 150, 50)
                map_cell_rect_x = pygame.Rect(center_x - 75, center_y - 280, 150, 50)
                map_cell_rect_y = pygame.Rect(center_x - 75, center_y - 185, 150, 50)

                if player_count_rect.collidepoint(event.pos):
                    self.startmenu.start_editing_player_count()
                elif map_cell_rect_x.collidepoint(event.pos):
                    self.startmenu.start_editing_map_cell_count_x()
                elif map_cell_rect_y.collidepoint(event.pos):
                    self.startmenu.start_editing_map_cell_count_y()

        elif event.type == pygame.KEYDOWN:
            self.startmenu.handle_keydown(event)

    def handle_multimenu_events(self, event): # New event handler for MULTIMENU state
        if event.type == pygame.MOUSEBUTTONDOWN:
            menu_result_multi = self.multimenu.handle_click(event.pos) # Handle clicks in MultiplayerMenu
            if menu_result_multi == "heberger":
                print("Héberger partie")
                # Lancer le jeu en mode hébergement ici
                game = GameLoop(multiplayer_mode="heberger") # Create new GameLoop instance in heberger mode
                game.run() # Run the new game instance. Consider how to manage this flow better if needed.
                self.state.states = START # Return to start menu after game ends (adjust as needed)

            elif isinstance(menu_result_multi, tuple) and menu_result_multi[0] == "rejoindre":
                ip_rejoindre = menu_result_multi[1]
                print(f"Rejoindre partie à l'IP: {ip_rejoindre}")
                # Lancer le jeu en mode rejoindre ici
                game = GameLoop(multiplayer_mode="rejoindre", server_ip=ip_rejoindre) # Create new GameLoop instance in rejoindre mode
                game.run() # Run the new game instance. Consider how to manage this flow better.
                self.state.states = START # Return to start menu after game ends (adjust as needed)

            elif menu_result_multi == "principal_solo":
                self.state.states = START # Return to start menu
        elif event.type == pygame.KEYDOWN:
            self.multimenu.handle_keydown(event) # Handle keydown events in MultiplayerMenu

    def handle_config_events(self,dt, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.iamenu.handle_click(event.pos, self.state)

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

        if keys[pygame.K_KP_PLUS] or keys[pygame.K_k]:
            self.state.camera.adjust_zoom(dt, 0.1, SCREEN_WIDTH, SCREEN_HEIGHT)
        elif keys[pygame.K_KP_MINUS] or keys[pygame.K_j]:
            self.state.camera.adjust_zoom(dt, -0.1, SCREEN_WIDTH, SCREEN_HEIGHT)
        if keys[pygame.K_1]:
            self.state.set_speed(self.state.speed + 0.1)
        if keys[pygame.K_2]:
            self.state.set_speed(self.state.speed - 0.1)
        if keys[pygame.K_3]:
            self.state.set_speed(0.3)
        if keys[pygame.K_4]:
            self.state.set_speed(1)
        if keys[pygame.K_5]:
            self.state.set_speed(2)
        if keys[pygame.K_6]:
            self.state.set_speed(8)
        if keys[pygame.K_F10]:
            self.state.toggle_display_mode(self)
        if keys[pygame.K_F11]:
            self.state.set_screen_size(self.screen.get_width(), self.screen.get_height())
            self.state.save()
        if keys[pygame.K_F12]:
            loaded = self.state.load()
            if loaded:
                pygame.display.set_mode(self.state.screen_width, self.state.screen_height,
                                     pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.RESIZABLE)
                if self.state.states == PAUSE:
                    self.state.toggle_pause()
        if keys[pygame.K_TAB]:
            self.state.generate_html_file(self.state.map.players_dict)
            self.state.toggle_pause()
        if keys[pygame.K_p] or keys[pygame.K_ESCAPE]:
            self.state.toggle_pause()
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
        if not (self.state.states == PAUSE):
            if self.multiplayer_mode:
                self.update_game_state_multiplayer(dt)
            else:
                self.update_game_state_solo(dt)
            self.state.endgame()

    def update_game_state_solo(self, dt):
        self.state.map.update_all_events(dt * self.state.speed, self.state.camera, self.screen)

    def update_game_state_multiplayer(self, dt):
        try:
            updates_bytes = self.ipc_connexion.recv(4096)
            if updates_bytes:
                updates_json = updates_bytes.decode()
                updates_data = json.loads(updates_json)
                if updates_data["type"] == "map_updates":
                    for update in updates_data["updates"]:
                        self.state.map.apply_map_update(update)
        except socket.timeout:
            pass
        except (ConnectionResetError, BrokenPipeError, EOFError, json.JSONDecodeError, Exception) as e:
            print(f"Erreur IPC (réception mises à jour): {e}")
            self.multiplayer_mode = None

        actions_ia = self.state.map.get_ia_actions(dt * self.state.speed)

        for action in actions_ia:
            if action["type"] == "map_update":
                self.state.map.apply_map_update(action)
                try:
                    action_json = json.dumps(action)
                    self.ipc_connexion.sendall(action_json.encode())
                except (ConnectionResetError, BrokenPipeError, Exception) as e:
                    print(f"Erreur IPC (envoi modification locale): {e}")
                    self.multiplayer_mode = None
                    break

    def render_display(self, dt, mouse_x, mouse_y):
        if self.state.states == START:
            self.startmenu.draw()
        elif self.state.states == MULTIMENU: # Render MultiplayerMenu if state is MULTIMENU
            self.multimenu.draw()
        elif self.state.states == CONFIG:
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
        self.state.states = START # Start at the START menu state
        while running:
            dt = self.clock.tick(FPS)
            self.screen_width, self.screen_height = self.screen.get_width(), self.screen.get_height()
            move_flags = 0
            mouse_x, mouse_y = pygame.mouse.get_pos()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if self.state.states == START:
                    self.state.change_music("start")
                    self.handle_start_events(event)
                elif self.state.states == MULTIMENU: # Handle events for MULTIMENU state
                    self.handle_multimenu_events(event)
                elif self.state.states == PAUSE:
                    self.handle_pause_events(dt, event)
                elif self.state.states == PLAY:
                    self.state.change_music(self.state.map.state)
                    self.handle_play_events(event, mouse_x, mouse_y, dt)
                elif self.state.states == END:
                    self.handle_end_events(event)

            if self.state.mouse_held:
                self.state.map.minimap.update_camera(self.state.camera, mouse_x, mouse_y)

            if not (self.state.states == START or self.state.states == MULTIMENU): # Disable keyboard inputs in menus
                self.handle_keyboard_inputs(move_flags, dt)

            self.state.update(dt)
            if self.state.states == PLAY:
                self.update_game_state(dt)
                if self.state.get_is_multiplayer():
                    self.handle_new_players()
            self.render_display(dt, mouse_x, mouse_y)

            if self.multiplayer_mode is None and self.ipc_connexion:
                print("Fermeture de la connexion IPC (retour en mode solo).")
                self.multiplayer_mode = None
                if self.ipc_connexion:
                    self.ipc_connexion.close()
                    self.ipc_connexion = None
                if self.ipc_socket:
                    self.ipc_socket.close()
                    self.ipc_socket = None
            # --- Reset GameState when returning to the start menu ---
            if self.state.states == START: # Check for state START to reset for new solo game
                self.state.reset_for_new_game() # Call reset_for_new_game() to reset GameState

        if self.ipc_connexion:
            self.ipc_connexion.close()
            print("Connexion IPC fermée à la sortie du jeu.")
        if self.ipc_socket:
            self.ipc_socket.close()
            print("Socket IPC fermé à la sortie du jeu.")
        pygame.quit()


if __name__ == "__main__":
    game = GameLoop()
    game.run()