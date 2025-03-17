import pygame
import random 
import webbrowser
import os
#from Game.savegame import *
from ImageProcessingDisplay import UserInterface, StartMenu, PauseMenu, Camera, TerminalCamera 
from GameField.map import *
#from GLOBAL_VAR import *
#from Entity import *
from yattag import Doc
import tkinter as tk
from tkinter import filedialog, messagebox
import pickle

class GameState:
    def __init__(self):
        self.states = START
        self.speed = 1
        self.selected_map_type = MAP_NORMAL
        self.selected_mode = LEAN
        self.selected_players = 2
        self.map = Map(MAP_CELLX, MAP_CELLY)
        self.display_mode = ISO2D # Mode d'affichage par défaut
        # Pour gérer le délai de basculement d'affichage
        self.switch_time_acc = 0
        self.switch_cooldown = ONE_SEC*(0.2) # Délai de 200ms (0,2 secondes)
        self.full_screen = False
        self.mouse_held = False
        self.screen_width = SCREEN_WIDTH
        self.screen_height = SCREEN_HEIGHT
        self.camera = Camera()
        self.terminal_camera = TerminalCamera()
        self.music_state = ""

    def change_music(self, state):
        
        if self.music_state != state:  # Ne changer que si l'état est différent
            
            pygame.mixer.music.stop()  # Arrêter la musique actuelle
            pygame.mixer.music.load(MUSIC[state])  # Charger la nouvelle musique
            pygame.mixer.music.play(-1)  # Jouer en boucle (-1 = boucle infinie)
            self.music_state = state
    

    def go_to_main_menu(self):
        self.states = START
        self.speed = 1
        self.selected_map_type = MAP_NORMAL
        self.selected_mode = LEAN
        self.selected_players = 2
        self.map = Map(MAP_CELLX, MAP_CELLY)
        self.display_mode = ISO2D # Mode d'affichage par défaut
        self.camera = Camera()
        self.terminal_camera = TerminalCamera()
        self.display_mode = ISO2D # Mode d'affichage par défaut

    def endgame(self):
        if self.map.state == "end":
            self.states = END

    def start_game(self):
        """Méthode pour démarrer la génération de la carte après que l'utilisateur ait validé ses choix."""
        self.map.generate_map(self.selected_map_type, self.selected_mode, self.selected_players)

    def set_map_size(self, X, Y):
        self.map = Map(X, Y)

    def set_map_type(self, map_type):
        self.selected_map_type = map_type

    def set_difficulty_mode(self, mode):
        self.selected_mode = mode

    def set_display_mode(self, mode):
        self.display_mode = mode

    def set_players(self, players):
        self.selected_players = players

    def toggle_pause(self):
        """Activer/désactiver la pause avec un délai pour éviter le spam."""

        if self.switch_time_acc >= self.switch_cooldown:
            if self.states == PAUSE:
                self.states = PLAY
            elif self.states == PLAY:
                self.states = PAUSE
            self.switch_time_acc = 0

    def set_screen_size(self, width, height):
        self.screen_width = width
        self.screen_height = height

    def toggle_fullscreen(self, gameloop):
        if not(self.full_screen):
            self.full_screen = True
            gameloop.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.FULLSCREEN)
            #self.screen.set_alpha(None)
        else:
            self.full_screen = False
            gameloop.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.RESIZABLE)
            #self.screen.set_alpha(None)
    def set_speed(self, new_speed):
        if self.switch_time_acc >= self.switch_cooldown:
            if new_speed >= 0.3 and new_speed <= 8:
                self.speed = new_speed
            self.switch_time_acc = 0
    def toggle_display_mode(self, gameloop):
        """Bascule entre les modes d'affichage Terminal et 2.5D."""
         
        if self.switch_time_acc>= self.switch_cooldown:
            if self.display_mode == ISO2D:
                self.display_mode = TERMINAL
                
                gameloop.screen = pygame.display.set_mode((20, 20), pygame.HWSURFACE | pygame.DOUBLEBUF )
                gameloop.screen.set_alpha(None)
            elif self.display_mode == TERMINAL:
                self.display_mode = ISO2D
                self.set_screen_size(SCREEN_WIDTH, SCREEN_HEIGHT)
                gameloop.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.RESIZABLE)
                gameloop.screen.set_alpha(None)



    def toggle_resources(self, ui):
        
         
        if self.switch_time_acc>= self.switch_cooldown:
            ui.toggle_resources()
            self.switch_time_acc = 0

    def toggle_units(self, ui):
        
        if self.switch_time_acc >= self.switch_cooldown:
            ui.toggle_units()
            self.switch_time_acc = 0
    def toggle_builds(self, ui):
         
        if self.switch_time_acc >= self.switch_cooldown:
            self.switch_time_acc = 0
            ui.toggle_builds()

    def toggle_all(self, ui):
        if self.switch_time_acc >= self.switch_cooldown:
            self.switch_time_acc = 0
            ui.toggle_all()

    def update(self, dt):
        self.switch_time_acc += dt

    def generate_html_file(self, players_dict):
        doc, tag, text = Doc().tagtext()
        doc.asis('<!DOCTYPE html>')
        with tag('html', lang='en'):
            with tag('head'):
                with tag('meta', charset='UTF-8'):
                    pass
                with tag('meta', name='viewport', content='width=device-width, initial-scale=1.0'):
                    pass
                with tag('title'):
                    text('Age of Empires - Overview')
                with tag('link', rel='stylesheet', href='styles.css'):
                    pass
                with tag('script'):
                    text('''
                    function toggleTeam(teamId) {
                        var teamDiv = document.getElementById("team-" + teamId);
                        var button = document.getElementById("button-" + teamId);
                        if (teamDiv.style.display === "none" || teamDiv.style.display === "") {
                            teamDiv.style.display = "block";
                            button.textContent = "Hide Team " + teamId;
                        } else {
                            teamDiv.style.display = "none";
                            button.textContent = "Show Team " + teamId;
                        }
                    }
                    ''')

            with tag('body'):
                with tag('h1'):
                    text('Age of Empires - Overview')
                for team in players_dict.keys():
                    with tag('button', id=f"button-{team}", onclick=f"toggleTeam('{team}')"):
                        text(f"Show Team {team}")
                for team, player in players_dict.items():
                    with tag('div', id=f"team-{team}", klass="team-section", style="display:none;"):
                        with tag('h2'):
                            text(f"Team {team}")
                        with tag('h3'):
                            text("Resources: ")
                        for resource_type, amount in player.get_current_resources().items():
                            with tag('ul', klass='resource-item'):
                                icons_path = ICONS_HTML.get(resource_type+"i", "default_image.png")
                                doc.stag('img', src=f"{icons_path}", klass="photo", width=50, height=50)
                                text(f"{resource_type} : {amount}")
                        with tag('h3'):
                            text("Entities: ")
                        for entity_repr in player.entities_dict.keys():
                            with tag('h4'):
                                icons_path = ICONS_HTML.get(entity_repr+"i", "default_image.png")
                                doc.stag('img', src=f"{icons_path}", klass="photo", width=50, height=50)
                            for id in player.get_entities_by_class(entity_repr):
                                with tag('ul'):
                                    with tag('li'):
                                        doc.asis(player.entities_dict[entity_repr][id].get_html())
                                        doc.stag(
                                            'progress',
                                            klass="health-bar",
                                            max=player.entities_dict[entity_repr][id].max_hp,
                                            value=player.entities_dict[entity_repr][id].hp
                                        )

        #save HTML 
        html_content = doc.getvalue()

        with open('overview.html', 'w') as f:
            f.write(html_content)

        #CSS
        css_content = """
        @import url('https://fonts.googleapis.com/css2?family=MedievalSharp&display=swap');

        body {
            font-family:'MedievalSharp';
            background-color: #ffebcd;
            margin: 0;
            padding: 0;
        }

        h1 {
            font-family:'MedievalSharp';
            text-align: center;
            color: #333;
            padding: 20px;
            background: #8b0000;
            color: white;
            margin: 0;
        }

        button {
            font-family:'MedievalSharp';
            margin: 10px;
            padding: 10px 20px;
            background: #deb887;
            color: black;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
        }

        button:hover {
            background: #fffafa;
        }

        .team-section {
            margin: 20px auto;
            padding: 15px;
            max-width: 800px;
            background: #deb887;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            display: none;  /* Initially hidden */
        }

        h2, h3 {
            color: #444;
        }

        ul {
            padding: 0;
            list-style: none;
        }

        .resource-item {
            display: flex;
            align-items: center;
            gap: 10px;
            margin: 8px 0;
        }

        ul li {
            padding: 8px 0;
            border-bottom: 1px solid #ddd;
        }

        ul li:last-child {
            border-bottom: none;
        }
        """
        with open('styles.css', 'w') as f:
            f.write(css_content)

        #Open directly the generated file in the browser
        browser = webbrowser.open('overview.html', 1, True)
        if not browser:
            messagebox.showinfo("Erreur", "Impossible d'ouvrir le fichier HTML")



    def save(self):
        # Sauvegarde l'objet dans un fichier
        file_path = filedialog.asksaveasfilename(
            defaultextension=".save",
            filetypes=[("Fichiers de sauvegarde", "*.save"), ("Tous les fichiers", "*.*")]
        )
        if file_path:
            with open(file_path, 'wb') as file:
                pickle.dump(self.__dict__, file)
            messagebox.showinfo("Sauvegarde réussie", f"Jeu sauvegardé dans {file_path}")
        else:
            messagebox.showwarning("Aucune sauvegarde", "Sauvegarde annulée.")

    def load(self):
        # Charge une sauvegarde depuis un fichier
        file_path = filedialog.askopenfilename(
            title="Sélectionner un fichier de sauvegarde",
            filetypes=[("Fichiers de sauvegarde", "*.save"), ("Tous les fichiers", "*.*")]
        )

        if file_path:
            with open(file_path, 'rb') as file:
                self.__dict__ = pickle.load(file)
                self.states = PLAY
                messagebox.showinfo("Chargement réussi", f"Jeu chargé depuis {file_path}")
                  # Retourne l'objet chargé
            return True
        else:
            messagebox.showwarning("Aucun fichier", "Vous n'avez pas sélectionné de fichier.")
            return False  # Retourne None si aucune sauvegarde n'est chargée

    # def draw_pause_text(self, screen):
    #     """Affiche le texte 'Jeu en pause' au centre de l'écran."""
    #     font = pygame.font.SysFont('Arial', 48)
    #     text = font.render("Jeu en pause", True, (255, 0, 0))  # Rouge pour le texte
    #     text_rect = text.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2))
    #     screen.blit(text, text_rect)

    

    # def draw_minimap(self, screen):
    #     minimap_size = (200, 200)  # Dimensions de la minimap
    #     minimap_surface = pygame.Surface(minimap_size)
    #     minimap_surface.fill((50, 50, 50))  # Couleur de fond de la minimap

    #     # Taille de la carte
    #     map_width, map_height = len(self.grid[0]), len(self.grid)
    #     scale_x = minimap_size[0] / map_width
    #     scale_y = minimap_size[1] / map_height

    #     # Dessiner les ressources
    #     for y in range(map_height):
    #         for x in range(map_width):
    #             if self.grid[y][x] != '.':
    #                 color = (34, 139, 34) if isinstance(self.grid[y][x], Wood) else (255, 215, 0)
    #                 pygame.draw.rect(
    #                     minimap_surface,
    #                     color,
    #                     pygame.Rect(x * scale_x, y * scale_y, scale_x, scale_y)
    #                 )

    #     # Calculer les dimensions visibles
    #     screen_width, screen_height = screen.get_size()
    #     visible_tiles_x = screen_width / self.tile_size
    #     visible_tiles_y = screen_height / self.tile_size

    #     # Limiter la caméra aux bords de la carte
    #     self.camera_x = max(0, min(self.camera_x, map_width - visible_tiles_x))
    #     self.camera_y = max(0, min(self.camera_y, map_height - visible_tiles_y))

    #     # Position et taille du rectangle
    #     rect_x = self.camera_x * scale_x
    #     rect_y = self.camera_y * scale_y
    #     rect_width = min(visible_tiles_x * scale_x, minimap_size[0] - rect_x)
    #     rect_height = min(visible_tiles_y * scale_y, minimap_size[1] - rect_y)

    #     # Dessiner le rectangle jaune
    #     pygame.draw.rect(
    #         minimap_surface,
    #         (255, 255, 0),
    #         pygame.Rect(rect_x, rect_y, rect_width, rect_height),
    #         2
    #     )

    #     # Position de la minimap sur l'écran
    #     minimap_position = (screen.get_width() - minimap_size[0] - 10, screen.get_height() - minimap_size[1] - 10)
    #     screen.blit(minimap_surface, minimap_position)
