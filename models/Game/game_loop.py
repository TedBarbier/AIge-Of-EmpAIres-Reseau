import pygame
import tkinter as tk
from tkinter import messagebox, Button, Tk

from ImageProcessingDisplay import UserInterface, EndMenu, StartMenu, PauseMenu, IAMenu
from GLOBAL_VAR import *
from Game.game_state import * 


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
        self.action_in_progress = False
        

    
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

            if self.startmenu.handle_click(event.pos):
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
            self.state.set_screen_size(self.screen.get_width(), self.screen.get_height())
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
        if not (self.state.states == PAUSE):
            self.state.map.update_all_events(dt*self.state.speed, self.state.camera, self.screen)
            self.state.endgame()

    def render_display(self, dt, mouse_x, mouse_y):
        if self.state.states == START:
            self.startmenu.draw()
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
                elif self.state.states == PAUSE:
                    self.handle_pause_events(dt, event)
                elif self.state.states == PLAY:
                    self.state.change_music(self.state.map.state)
                    self.handle_play_events(event, mouse_x, mouse_y, dt)
                elif self.state.states == END:
                    self.handle_end_events(event)

            if self.state.mouse_held:
                self.state.map.minimap.update_camera(self.state.camera, mouse_x, mouse_y)

            if not (self.state.states == START):
                self.handle_keyboard_inputs(move_flags, dt)

            self.state.update(dt)
            """
            if self.state.states == PLAY:
                for team in self.state.map.players_dict.keys():
                     if not self.action_in_progress:
                        self.action_in_progress = True  # Mark the action as in progress
                        self.state.map.players_dict[team].player_turn(dt)  # Trigger player turn
                        self.action_in_progress = False  # Action finished, ready for the next one
            """
            if self.state.states == PLAY:
                self.update_game_state(dt)
            self.render_display(dt, mouse_x, mouse_y)


        pygame.quit()


if __name__ == "__main__":
    game = GameLoop()
    game.run()