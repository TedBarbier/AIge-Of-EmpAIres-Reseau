import pygame
import socket
from GLOBAL_VAR import *

class MultiplayerMenu:
    def __init__(self, screen):
        self.screen = screen

        # États du menu multijoueur
        self.menu_state = "principal" # "principal", "rejoindre", "hebergement", "attente", "attente_rejoindre" (nouveau)

        # Pour stocker l'IP à rejoindre
        self.ip_adresse_rejoindre = ""
        self.input_actif = False # Si le champ IP est actif pour la saisie

        # Paramètres de la partie pour l'hébergement (ajouté)
        self.map_cell_count_x = 50
        self.map_cell_count_y = 50
        self.selected_map_index = MAP_NORMAL
        self.selected_mode_index = LEAN
        self.selected_player_count = 2

        # Pour l'hébergement
        self.local_ip = self.get_local_ip()
        self.connection_status = "" # Message de statut pour la connexion
        self.connection_status_timer = 0 # Timer pour afficher les messages de statut

        # Statut de la connexion
        self.est_connecte = False

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

        # Buttons pour le menu "Hébergement" et "Attente Rejoindre" (réutilisation)
        self.hebergement_buttons = {
            "Annuler": pygame.Rect(0, 0, 200, 50), # Réutilisé pour "Annuler" dans "attente_rejoindre" et "hebergement"
            "left_map_x": pygame.Rect(0, 0, 30, 30),
            "right_map_x": pygame.Rect(0, 0, 30, 30),
            "left_map_y": pygame.Rect(0, 0, 30, 30),
            "right_map_y": pygame.Rect(0, 0, 30, 30),
            "left_map": pygame.Rect(0, 0, 30, 30),
            "right_map": pygame.Rect(0, 0, 30, 30),
            "left_mode": pygame.Rect(0, 0, 30, 30),
            "right_mode": pygame.Rect(0, 0, 30, 30),
            "left_player_count": pygame.Rect(0, 0, 30, 30),
            "right_player_count": pygame.Rect(0, 0, 30, 30),
            "Heberger_config": pygame.Rect(0, 0, 200, 50)
        }

        # Champ de texte pour l'IP dans le menu "Rejoindre"
        self.champ_ip_rect = pygame.Rect(0, 0, 300, 30)

        # Options
        self.map_options = ["Carte Normal", "Carte Centrée"]
        self.modes_options = ["Lean", "Mean", "Marines"]


    def get_local_ip(self):
        """Récupère l'adresse IP locale de la machine."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"

    def draw(self):
        """Dessine le menu multijoueur en fonction de l'état."""
        self.screen.fill((255, 255, 255))
        screen_width, screen_height = self.screen.get_size()
        self.screen.blit(adjust_sprite(START_IMG, screen_width, screen_height), (0, 0))
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
            self._draw_text("Entrez l'adresse IP:", (center_x, center_y - 110), centered=True, font_size=24)
            self._dessiner_champ_texte(self.ip_adresse_rejoindre, self.champ_ip_rect)
            self._draw_button("Rejoindre_ip", "Rejoindre", button_dict=self.rejoindre_buttons)
            self._draw_button("Retour_rejoindre", "Retour", button_dict=self.rejoindre_buttons)
            if self.connection_status:
                color = RED_COLOR if "Échec" in self.connection_status else WHITE_COLOR
                self._draw_text(self.connection_status, (center_x, center_y + 110), centered=True, color=color)

        elif self.menu_state == "hebergement":
            # --- Menu "Hébergement d'une partie" ---
            titre_text = "Hébergement d'une partie"
            self._draw_text(titre_text, (center_x, center_y - 240), centered=True, font_size=36)
            instruction_text = "Configurez les paramètres de votre partie multijoueur ci-dessous :"
            self._draw_text(instruction_text, (center_x, center_y - 190), centered=True, font_size=20)
            ip_text = f"Votre adresse IP: {self.local_ip}"
            self._draw_text(ip_text, (center_x, center_y - 150), centered=True, font_size=24)
            self._draw_text("Configurez votre partie:", (center_x, center_y - 110), centered=True, font_size=24)
            param_y_start = center_y - 70
            line_height = 40
            self.hebergement_buttons["left_map_x"].topleft = (center_x - 150, param_y_start)
            self._draw_button("left_map_x", "<", button_dict=self.hebergement_buttons)
            map_cell_label_x = f"Map X: {self.map_cell_count_x}"
            self._draw_text(map_cell_label_x, (center_x, param_y_start + 15), centered=True)
            self.hebergement_buttons["right_map_x"].topleft = (center_x + 120, param_y_start)
            self._draw_button("right_map_x", ">", button_dict=self.hebergement_buttons)
            self.hebergement_buttons["left_map_y"].topleft = (center_x - 150, param_y_start + line_height)
            self._draw_button("left_map_y", "<", button_dict=self.hebergement_buttons)
            map_cell_label_y = f"Map Y: {self.map_cell_count_y}"
            self._draw_text(map_cell_label_y, (center_x, param_y_start + line_height + 15), centered=True)
            self.hebergement_buttons["right_map_y"].topleft = (center_x + 120, param_y_start + line_height)
            self._draw_button("right_map_y", ">", button_dict=self.hebergement_buttons)
            self.hebergement_buttons["left_map"].topleft = (center_x - 150, param_y_start + 2 * line_height)
            self._draw_button("left_map", "<", button_dict=self.hebergement_buttons)
            map_label = f"Map Type: {self.map_options[self.selected_map_index]}"
            self._draw_text(map_label, (center_x, param_y_start + 2 * line_height + 15), centered=True)
            self.hebergement_buttons["right_map"].topleft = (center_x + 120, param_y_start + 2 * line_height)
            self._draw_button("right_map", ">", button_dict=self.hebergement_buttons)
            self.hebergement_buttons["left_mode"].topleft = (center_x - 150, param_y_start + 3 * line_height)
            self._draw_button("left_mode", "<", button_dict=self.hebergement_buttons)
            mode_label = f"Mode: {self.modes_options[self.selected_mode_index]}"
            self._draw_text(mode_label, (center_x, param_y_start + 3 * line_height + 15), centered=True)
            self.hebergement_buttons["right_mode"].topleft = (center_x + 120, param_y_start + 3 * line_height)
            self._draw_button("right_mode", ">", button_dict=self.hebergement_buttons)
            self.hebergement_buttons["left_player_count"].topleft = (center_x - 150, param_y_start + 4 * line_height)
            self._draw_button("left_player_count", "<", button_dict=self.hebergement_buttons)
            player_count_label = f"Players: {self.selected_player_count}"
            self._draw_text(player_count_label, (center_x, param_y_start + 4 * line_height + 15), centered=True)
            self.hebergement_buttons["right_player_count"].topleft = (center_x + 120, param_y_start + 4 * line_height)
            self._draw_button("right_player_count", ">", button_dict=self.hebergement_buttons)
            self.hebergement_buttons["Heberger_config"].topleft = (center_x - 100, center_y + 140)
            self._draw_button("Heberger_config", "Heberger", button_dict=self.hebergement_buttons)
            self.hebergement_buttons["Annuler"].topleft = (center_x - 100, center_y + 200)
            self._draw_button("Annuler", "Annuler", button_dict=self.hebergement_buttons)
            if self.connection_status:
                color = (255, 0, 0) if "Échec" in self.connection_status else (0, 128, 0)
                self._draw_text(self.connection_status, (center_x, center_y + 250), centered=True, color=color)

        elif self.menu_state == "attente":
            # --- Menu d'attente après connexion réussie ---
            titre_text = "Connexion établie!"
            self._draw_text(titre_text, (center_x, center_y - 150), centered=True, font_size=36)
            message = "En attente du lancement de la partie..."
            self._draw_text(message, (center_x, center_y), centered=True, font_size=24)

        elif self.menu_state == "attente_rejoindre": # Nouveau menu d'attente pour rejoindre
            # --- Menu d'attente pendant la tentative de connexion pour rejoindre ---
            titre_text = "Tentative de connexion..."
            self._draw_text(titre_text, (center_x, center_y - 100), centered=True, font_size=36)
            message = "Connexion au serveur en cours,\nveuillez patienter..."
            self._draw_text(message, (center_x, center_y - 20), centered=True, font_size=28)

            self.hebergement_buttons["Annuler"].topleft = (center_x - 100, center_y + 50) # Réutilise le bouton "Annuler"
            self._draw_button("Annuler", "Annuler", button_dict=self.hebergement_buttons) # Dessiner le bouton "Annuler"


    def _draw_button(self, key, text, selected=False, button_dict=None):
        """Dessine un bouton avec texte."""
        if button_dict is None:
            button_dict = self.principal_buttons
        rect = button_dict[key]
        color = (0, 128, 0) if selected else (128, 128, 128)
        pygame.draw.rect(self.screen, color, rect)
        font = pygame.font.Font(MEDIEVALSHARP, 28)
        button_text = font.render(text, True, (255, 255, 255))
        text_rect = button_text.get_rect(center=rect.center)
        self.screen.blit(button_text, text_rect)

    def _draw_text(self, text, pos, centered=False, font_size=28, color=WHITE_COLOR):
        """Dessine du texte à une position spécifique."""
        font = pygame.font.Font(MEDIEVALSHARP, font_size)
        rendered_text = font.render(text, True, color)
        text_rect = rendered_text.get_rect(center=pos if centered else None)
        self.screen.blit(rendered_text, text_rect if centered else pos)

    def _dessiner_champ_texte(self, texte, rect):
        """Dessine le champ de texte pour la saisie IP."""
        pygame.draw.rect(self.screen, WHITE_COLOR, rect, 2)
        font = pygame.font.Font(None, 28)
        texte_surface = font.render(texte, True, WHITE_COLOR)
        texte_rect = texte_surface.get_rect(midleft=rect.midleft)
        texte_rect.x += 5
        self.screen.blit(texte_surface, texte_rect)
        if self.input_actif:
            cursor_pos = texte_rect.x + texte_surface.get_width() + 2
            blink_show = pygame.time.get_ticks() % 1000 < 500
            if blink_show:
                pygame.draw.line(self.screen, WHITE_COLOR,
                                (cursor_pos, rect.y + 5),
                                (cursor_pos, rect.y + rect.height - 5), 2)


    def handle_click(self, pos):
        """Gère les clics sur les boutons."""
        if self.menu_state == "principal":
            if self.principal_buttons["Heberger"].collidepoint(pos):
                self.menu_state = "hebergement"
                return "heberger"
            elif self.principal_buttons["Rejoindre"].collidepoint(pos):
                self.menu_state = "rejoindre"
                return "rejoindre_menu" # Indiquer qu'on va au menu "rejoindre"
            elif self.principal_buttons["Retour"].collidepoint(pos):
                return "principal_solo"

        elif self.menu_state == "rejoindre":
            if self.champ_ip_rect.collidepoint(pos):
                self.input_actif = True
            else:
                self.input_actif = False
            if self.rejoindre_buttons["Rejoindre_ip"].collidepoint(pos):
                if self._verifier_format_ip(self.ip_adresse_rejoindre):
                    self.menu_state = "attente_rejoindre" # Aller à l'état "attente_rejoindre" après clic sur "Rejoindre"
                    return ("rejoindre", self.ip_adresse_rejoindre) # Indiquer "rejoindre" et l'IP
                else:
                    self.connection_status = "Format d'IP invalide"
                    self.connection_status_timer = pygame.time.get_ticks()
            elif self.rejoindre_buttons["Retour_rejoindre"].collidepoint(pos):
                self.menu_state = "principal"

        elif self.menu_state == "hebergement":
            if self.hebergement_buttons["Annuler"].collidepoint(pos):
                self.menu_state = "principal"
                return "annuler_hebergement"
            elif self.hebergement_buttons["left_map_x"].collidepoint(pos):
                self.map_cell_count_x = max(10, self.map_cell_count_x - 5)
            elif self.hebergement_buttons["right_map_x"].collidepoint(pos):
                self.map_cell_count_x = min(200, self.map_cell_count_x + 5)
            elif self.hebergement_buttons["left_map_y"].collidepoint(pos):
                self.map_cell_count_y = max(10, self.map_cell_count_y - 5)
            elif self.hebergement_buttons["right_map_y"].collidepoint(pos):
                self.map_cell_count_y = min(200, self.map_cell_count_y + 5)
            elif self.hebergement_buttons["left_map"].collidepoint(pos):
                self.selected_map_index = (self.selected_map_index - 1) % len(self.map_options)
            elif self.hebergement_buttons["right_map"].collidepoint(pos):
                self.selected_map_index = (self.selected_map_index + 1) % len(self.map_options)
            elif self.hebergement_buttons["left_mode"].collidepoint(pos):
                self.selected_mode_index = (self.selected_mode_index - 1) % len(self.modes_options)
            elif self.hebergement_buttons["right_mode"].collidepoint(pos):
                self.selected_mode_index = (self.selected_mode_index + 1) % len(self.modes_options)
            elif self.hebergement_buttons["left_player_count"].collidepoint(pos):
                self.selected_player_count = max(2, self.selected_player_count - 1)
            elif self.hebergement_buttons["right_player_count"].collidepoint(pos):
                self.selected_player_count = min(8, self.selected_player_count + 1)
            elif self.hebergement_buttons["Heberger_config"].collidepoint(pos):
                return "start_hosting"

        elif self.menu_state == "attente_rejoindre": # Gestion des clics dans le menu "attente_rejoindre"
            if self.hebergement_buttons["Annuler"].collidepoint(pos): # Réutiliser le bouton "Annuler"
                self.menu_state = "rejoindre" # Retourner au menu "rejoindre"
                return "annuler_rejoindre" # Optionnel: indiquer à gameloop que l'action de rejoindre est annulée

        return None

    def handle_keydown(self, event):
        """Gère la saisie clavier pour le champ IP."""
        if self.menu_state == "rejoindre" and self.input_actif:
            if event.key == pygame.K_RETURN:
                if self._verifier_format_ip(self.ip_adresse_rejoindre):
                    self.menu_state = "attente_rejoindre" # Aller à l'état "attente_rejoindre" aussi avec Entrée
                    return ("rejoindre", self.ip_adresse_rejoindre)
                else:
                    self.connection_status = "Format d'IP invalide"
                    self.connection_status_timer = pygame.time.get_ticks()
            elif event.key == pygame.K_BACKSPACE:
                self.ip_adresse_rejoindre = self.ip_adresse_rejoindre[:-1]
            else:
                if event.unicode in "0123456789." and len(self.ip_adresse_rejoindre) < 15:
                    self.ip_adresse_rejoindre += event.unicode
        return None

    def _verifier_format_ip(self, ip):
        """Vérifie si l'IP a un format valide."""
        parts = ip.split(".")
        if len(parts) != 4:
            return False
        for part in parts:
            try:
                num = int(part)
                if num < 0 or num > 255:
                    return False
            except ValueError:
                return False
        return True

    def mettre_a_jour_status(self, status, etat_connexion=None):
        """Met à jour le statut de connexion et éventuellement l'état du menu."""
        self.connection_status = status
        self.connection_status_timer = pygame.time.get_ticks()

        if etat_connexion == "connecte":
            self.est_connecte = True
            self.menu_state = "attente"
        elif etat_connexion == "echec":
            self.est_connecte = False

    def update(self):
        """Met à jour les éléments dynamiques du menu."""
        if self.connection_status and pygame.time.get_ticks() - self.connection_status_timer > 5000:
            self.connection_status = ""