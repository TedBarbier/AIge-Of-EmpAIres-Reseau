import pygame
from GLOBAL_VAR import *

class MultiplayerMenu:
    def __init__(self, screen):
        self.screen = screen

        # États du menu multijoueur
        self.menu_state = "principal" # "principal", "rejoindre"

        # Pour stocker l'IP à rejoindre
        self.ip_adresse_rejoindre = ""
        self.input_actif = False # Si le champ IP est actif pour la saisie

        # Buttons pour le menu principal multijoueur
        self.principal_buttons = {
            "Heberger": pygame.Rect(0, 0, 200, 50),
            "Rejoindre": pygame.Rect(0, 0, 200, 50),
            "Retour": pygame.Rect(0, 0, 200, 50)
        }

        # Buttons pour le menu "Rejoindre"
        self.rejoindre_buttons = {
            "Rejoindre_ip": pygame.Rect(0, 0, 200, 50), # Bouton "Rejoindre" après saisie IP
            "Retour_rejoindre": pygame.Rect(0, 0, 200, 50) # Bouton "Retour" dans le menu "Rejoindre"
        }

        # Champ de texte pour l'IP dans le menu "Rejoindre"
        self.champ_ip_rect = pygame.Rect(0, 0, 300, 30)


    def draw(self):
        """Dessine le menu multijoueur en fonction de l'état."""
        self.screen.fill((255, 255, 255)) # Fond blanc (vous pouvez changer)
        screen_width, screen_height = self.screen.get_size()
        # Vous pouvez mettre une image de fond spécifique au menu multijoueur ici si vous voulez
        # self.screen.blit(adjust_sprite(MULTIJOUER_MENU_IMG, screen_width, screen_height), (0, 0))

        center_x = screen_width // 2
        center_y = screen_height // 2

        if self.menu_state == "principal":
            # --- Menu Principal Multijoueur ---
            titre_text = "Menu Multijoueur"
            self._draw_text(titre_text, (center_x, center_y - 100), centered=True, font_size=36)

            self.principal_buttons["Heberger"].topleft = (center_x - 100, center_y - 30)
            self.principal_buttons["Rejoindre"].topleft = (center_x - 100, center_y + 40)
            self.principal_buttons["Retour"].topleft = (center_x - 100, center_y + 110)

            self._draw_button("Heberger", "Héberger", button_dict=self.principal_buttons)
            self._draw_button("Rejoindre", "Rejoindre", button_dict=self.principal_buttons)
            self._draw_button("Retour", "Retour", button_dict=self.principal_buttons)

        elif self.menu_state == "rejoindre":
            # --- Menu "Rejoindre une Partie" ---
            titre_text = "Rejoindre une Partie"
            self._draw_text(titre_text, (center_x, center_y - 150), centered=True, font_size=36)

            self.champ_ip_rect.topleft = (center_x - 150, center_y - 80)
            self.rejoindre_buttons["Rejoindre_ip"].topleft = (center_x - 100, center_y - 20)
            self.rejoindre_buttons["Retour_rejoindre"].topleft = (center_x - 100, center_y + 50)

            self._dessiner_champ_texte(self.ip_adresse_rejoindre, self.champ_ip_rect) # Dessiner le champ IP
            self._draw_button("Rejoindre_ip", "Rejoindre", button_dict=self.rejoindre_buttons) # Bouton "Rejoindre"
            self._draw_button("Retour_rejoindre", "Retour", button_dict=self.rejoindre_buttons) # Bouton "Retour"


    def _draw_button(self, key, text, selected=False, button_dict=None):
        """Dessine un bouton avec texte, en utilisant un dictionnaire de boutons spécifié."""
        if button_dict is None:
            button_dict = self.principal_buttons # Par défaut, utilise les boutons principaux si non spécifié
        rect = button_dict[key]
        color = (0, 128, 0) if selected else (128, 128, 128)
        pygame.draw.rect(self.screen, color, rect)
        font = pygame.font.Font(MEDIEVALSHARP, 28)
        button_text = font.render(text, True, (255, 255, 255))
        text_rect = button_text.get_rect(center=rect.center)
        self.screen.blit(button_text, text_rect)

    def _draw_text(self, text, pos, centered=False, font_size=28, color=WHITE_COLOR):
        """Dessine du texte à une position spécifique avec une taille de police ajustable."""
        font = pygame.font.Font(MEDIEVALSHARP, font_size)
        rendered_text = font.render(text, True, color)
        text_rect = rendered_text.get_rect(center=pos if centered else None)
        self.screen.blit(rendered_text, text_rect if centered else pos)

    def _dessiner_champ_texte(self, texte, rect):
        """Dessine le champ de texte pour la saisie IP."""
        pygame.draw.rect(self.screen, BLACK_COLOR, rect, 2) # Bordure
        font = pygame.font.Font(None, 24) # Police plus petite pour le champ IP
        texte_surface = font.render(texte, True, BLACK_COLOR)
        texte_rect = texte_surface.get_rect(midleft=rect.midleft) # Aligné à gauche
        texte_rect.x += 5 # Petite marge
        self.screen.blit(texte_surface, texte_rect)


    def handle_click(self, pos):
        """Gère les clics sur les boutons en fonction de l'état du menu."""
        if self.menu_state == "principal":
            if self.principal_buttons["Heberger"].collidepoint(pos):
                return "heberger" # Indiquer qu'on veut héberger
            elif self.principal_buttons["Rejoindre"].collidepoint(pos):
                self.menu_state = "rejoindre" # Aller à l'écran "Rejoindre"
            elif self.principal_buttons["Retour"].collidepoint(pos):
                return "principal_solo" # Retour au menu principal solo (start_menu)

        elif self.menu_state == "rejoindre":
            if self.champ_ip_rect.collidepoint(pos):
                self.input_actif = True # Activer la saisie dans le champ IP
            else:
                self.input_actif = False # Désactiver si clic ailleurs
            if self.rejoindre_buttons["Rejoindre_ip"].collidepoint(pos):
                return ("rejoindre", self.ip_adresse_rejoindre) # Indiquer "rejoindre" et l'IP
            elif self.rejoindre_buttons["Retour_rejoindre"].collidepoint(pos):
                self.menu_state = "principal" # Retour au menu principal multijoueur

        return None # Si aucun bouton important n'a été cliqué

    def handle_keydown(self, event):
        """Gère la saisie clavier pour le champ IP."""
        if self.menu_state == "rejoindre" and self.input_actif:
            if event.key == pygame.K_RETURN:
                self.input_actif = False # Valider l'IP (peut-être)
            elif event.key == pygame.K_BACKSPACE:
                self.ip_adresse_rejoindre = self.ip_adresse_rejoindre[:-1] # Supprimer le dernier caractère
            else:
                self.ip_adresse_rejoindre += event.unicode # Ajouter le caractère tapé