import pygame
from GLOBAL_VAR import *
from ImageProcessingDisplay.imagemethods import *
from Entity.Unit.unit import Unit
from Entity.Building.building import Building
class UserInterface:
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.Font(MEDIEVALSHARP, 22)
        self.display_resources = False
        self.display_units = False
        self.display_builds = False

    def draw_resources(self, players_dict):
        for player_id, player_object in players_dict.items():
            player_offset = -12
            player_pos = (90*player_id-10, 50)
            # Représentations attendues des unités avec leur offset respectif
            expected_unit_representations = [
                    ('v', 0),
                    ('s', 50),
                    ('h', 100),
                    ('a', 150),
                    ('c', 200),
                    ('m', 250),
                    ('x', 300),
                ]
            # Représentations attendues des constructions avec leur offset respectif
            expected_build_representations = [
                ('T', 0),
                ('H', 50),
                ('C', 100),
                ('F', 150),
                ('B', 200),
                ('S', 250),
                ('K', 300),
                ('A', 350)
            ]
            if self.display_builds or self.display_resources or self.display_units:
                texte = self.font.render("Player "+str(player_id), True, TEAM_COLORS[player_id])  # Crée un rendu de texte
                self.screen.blit(texte, (player_pos[0], player_pos[1]-40))  # Affiche à la position (x=50, y=y_offset)

            if self.display_resources:
                for resource in player_object.get_current_resources().values():
                    texte = self.font.render(str(resource), True, WHITE_COLOR)  # Crée un rendu de texte
                    self.screen.blit(texte, (player_pos[0], player_pos[1]+player_offset))    # Affiche à la position (x=50, y=y_offset)
                    player_offset += 50
            if self.display_units:
                for unit_representation, unit_offset in expected_unit_representations:
                    # Vérifie si la représentation d'unité existe dans entities_dict
                    unit = player_object.entities_dict.get(unit_representation, [])
                    texte = self.font.render(str(len(unit) if unit else 0), True, WHITE_COLOR)
                    self.screen.blit(texte, (player_pos[0], player_pos[1] + player_offset + unit_offset))

                # Mise à jour de l'offset global après les unités
                player_offset += 350  # Ajustez l'offset global si nécessaire
            if self.display_builds:
                for build_representation, build_offset in expected_build_representations:
                    # Vérifie si la représentation de construction existe dans entities_dict
                    build = player_object.entities_dict.get(build_representation, [])
                    texte = self.font.render(str(len(build) if build else 0), True, WHITE_COLOR)
                    self.screen.blit(texte, (player_pos[0], player_pos[1] + player_offset + build_offset))

                # Mise à jour de l'offset global après les constructions
                player_offset += 400  # Ajustez l'offset global si nécessaire
             
        


        # Position des joueurs
        pos = (30,50)

        # Y offsets distincts pour chaque joueur
        y_offset = 0
        
        # Affichage des données des joueurs
        if self.display_resources:
            display_image(ICONS["Gi"], pos[0], pos[1]+y_offset, self.screen, 0x04)
            display_image(ICONS["Wi"], pos[0], pos[1]+y_offset+50, self.screen, 0x04)
            display_image(ICONS["Mi"], pos[0], pos[1]+y_offset+100, self.screen, 0x04)
            y_offset+= 150

        if self.display_units:
            display_image(ICONS["vi"], pos[0], pos[1]+y_offset, self.screen, 0x04)
            display_image(ICONS["si"], pos[0], pos[1]+y_offset+50, self.screen, 0x04)
            display_image(ICONS["hi"], pos[0], pos[1]+y_offset+100, self.screen, 0x04)
            display_image(ICONS["ai"], pos[0], pos[1]+y_offset+150, self.screen, 0x04)
            display_image(ICONS["ci"], pos[0], pos[1]+y_offset+200, self.screen, 0x04)
            display_image(ICONS["mi"], pos[0], pos[1]+y_offset+250, self.screen, 0x04)
            display_image(ICONS["xi"], pos[0], pos[1]+y_offset+300, self.screen, 0x04)
            y_offset += 350

        if self.display_builds:
            display_image(ICONS["Ti"], pos[0], pos[1]+y_offset, self.screen, 0x04)
            display_image(ICONS["Hi"], pos[0], pos[1]+y_offset+50, self.screen, 0x04)
            display_image(ICONS["Ci"], pos[0], pos[1]+y_offset+100, self.screen, 0x04)
            display_image(ICONS["Fi"], pos[0], pos[1]+y_offset+150, self.screen, 0x04)
            display_image(ICONS["Bi"], pos[0], pos[1]+y_offset+200, self.screen, 0x04)
            display_image(ICONS["Si"], pos[0], pos[1]+y_offset+250, self.screen, 0x04)
            display_image(ICONS["Ki"], pos[0], pos[1]+y_offset+300, self.screen, 0x04)
            display_image(ICONS["Ai"], pos[0], pos[1]+y_offset+350, self.screen, 0x04)
            y_offset += 400


    def toggle_resources(self):
        self.display_resources = not self.display_resources

    def toggle_units(self):
        self.display_units = not self.display_units
    def toggle_builds(self):
        self.display_builds = not self.display_builds
    
    def toggle_all(self):
        if (self.display_resources + self.display_units + self.display_builds > 0):
            self.display_resources = False
            self.display_units = False
            self.display_builds = False
        else:
            self.display_resources = True
            self.display_units = True
            self.display_builds = True