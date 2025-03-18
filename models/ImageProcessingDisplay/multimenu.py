import pygame
import socket
from GLOBAL_VAR import *

class MultiplayerMenu:
    def __init__(self, screen):
        self.screen = screen

        # États du menu multijoueur
        self.menu_state = "principal" # "principal", "rejoindre", "hebergement", "attente"

        # Pour stocker l'IP à rejoindre
        self.ip_adresse_rejoindre = ""
        self.input_actif = False # Si le champ IP est actif pour la saisie
        
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
        
        # Buttons pour le menu "Hébergement"
        self.hebergement_buttons = {
            "Annuler": pygame.Rect(0, 0, 200, 50)
        }

        # Champ de texte pour l'IP dans le menu "Rejoindre"
        self.champ_ip_rect = pygame.Rect(0, 0, 300, 30)

    def get_local_ip(self):
        """Récupère l'adresse IP locale de la machine."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # Se connecte à une adresse externe pour déterminer quelle interface utiliser
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"  # Fallback sur localhost

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

            self._draw_text("Entrez l'adresse IP:", (center_x, center_y - 110), centered=True, font_size=24)
            self._dessiner_champ_texte(self.ip_adresse_rejoindre, self.champ_ip_rect) # Dessiner le champ IP
            self._draw_button("Rejoindre_ip", "Rejoindre", button_dict=self.rejoindre_buttons) # Bouton "Rejoindre"
            self._draw_button("Retour_rejoindre", "Retour", button_dict=self.rejoindre_buttons) # Bouton "Retour"
            
            # Afficher le statut de connexion si présent
            if self.connection_status:
                color = (255, 0, 0) if "Échec" in self.connection_status else (0, 128, 0)
                self._draw_text(self.connection_status, (center_x, center_y + 110), centered=True, color=color)

        elif self.menu_state == "hebergement":
            # --- Menu "Hébergement d'une partie" ---
            titre_text = "Hébergement d'une partie"
            self._draw_text(titre_text, (center_x, center_y - 150), centered=True, font_size=36)
            
            # Afficher l'adresse IP locale
            ip_text = f"Votre adresse IP: {self.local_ip}"
            self._draw_text(ip_text, (center_x, center_y - 80), centered=True, font_size=24)
            
            # Message d'attente
            self._draw_text("En attente d'une connexion...", (center_x, center_y - 20), centered=True, font_size=24)
            
            # Bouton pour annuler l'hébergement
            self.hebergement_buttons["Annuler"].topleft = (center_x - 100, center_y + 50)
            self._draw_button("Annuler", "Annuler", button_dict=self.hebergement_buttons)
            
            # Afficher le statut de connexion si présent
            if self.connection_status:
                color = (255, 0, 0) if "Échec" in self.connection_status else (0, 128, 0)
                self._draw_text(self.connection_status, (center_x, center_y + 110), centered=True, color=color)
                
        elif self.menu_state == "attente":
            # --- Menu d'attente après connexion réussie ---
            titre_text = "Connexion établie!"
            self._draw_text(titre_text, (center_x, center_y - 150), centered=True, font_size=36)
            
            message = "En attente du lancement de la partie..."
            self._draw_text(message, (center_x, center_y), centered=True, font_size=24)


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
        
        # Ajouter un curseur clignotant si le champ est actif
        if self.input_actif:
            cursor_pos = texte_rect.x + texte_surface.get_width() + 2
            blink_show = pygame.time.get_ticks() % 1000 < 500  # Clignotement chaque 500ms
            if blink_show:
                pygame.draw.line(self.screen, BLACK_COLOR, 
                                (cursor_pos, rect.y + 5), 
                                (cursor_pos, rect.y + rect.height - 5), 2)


    def handle_click(self, pos):
        """Gère les clics sur les boutons en fonction de l'état du menu."""
        if self.menu_state == "principal":
            if self.principal_buttons["Heberger"].collidepoint(pos):
                self.menu_state = "hebergement"
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
                # Vérifier que l'IP est valide avant de tenter la connexion
                if self._verifier_format_ip(self.ip_adresse_rejoindre):
                    return ("rejoindre", self.ip_adresse_rejoindre) # Indiquer "rejoindre" et l'IP
                else:
                    self.connection_status = "Format d'IP invalide"
                    self.connection_status_timer = pygame.time.get_ticks()
            elif self.rejoindre_buttons["Retour_rejoindre"].collidepoint(pos):
                self.menu_state = "principal" # Retour au menu principal multijoueur
                
        elif self.menu_state == "hebergement":
            if self.hebergement_buttons["Annuler"].collidepoint(pos):
                self.menu_state = "principal"
                return "annuler_hebergement"
                
        return None # Si aucun bouton important n'a été cliqué

    def handle_keydown(self, event):
        """Gère la saisie clavier pour le champ IP."""
        if self.menu_state == "rejoindre" and self.input_actif:
            if event.key == pygame.K_RETURN:
                # Essayer de se connecter quand on appuie sur Entrée
                if self._verifier_format_ip(self.ip_adresse_rejoindre):
                    return ("rejoindre", self.ip_adresse_rejoindre)
                else:
                    self.connection_status = "Format d'IP invalide"
                    self.connection_status_timer = pygame.time.get_ticks()
            elif event.key == pygame.K_BACKSPACE:
                self.ip_adresse_rejoindre = self.ip_adresse_rejoindre[:-1] # Supprimer le dernier caractère
            else:
                # N'accepter que des caractères valides pour une IP (chiffres et points)
                if event.unicode in "0123456789." and len(self.ip_adresse_rejoindre) < 15:
                    self.ip_adresse_rejoindre += event.unicode # Ajouter le caractère tapé
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
        # Effacer les messages de statut après un certain temps
        if self.connection_status and pygame.time.get_ticks() - self.connection_status_timer > 5000:
            self.connection_status = ""
    import pygame
import socket
from GLOBAL_VAR import *

class MultiplayerMenu:
    def __init__(self, screen):
        self.screen = screen

        # États du menu multijoueur
        self.menu_state = "principal" # "principal", "rejoindre", "hebergement", "attente"

        # Pour stocker l'IP à rejoindre
        self.ip_adresse_rejoindre = ""
        self.input_actif = False # Si le champ IP est actif pour la saisie
        
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
        
        # Buttons pour le menu "Hébergement"
        self.hebergement_buttons = {
            "Annuler": pygame.Rect(0, 0, 200, 50)
        }

        # Champ de texte pour l'IP dans le menu "Rejoindre"
        self.champ_ip_rect = pygame.Rect(0, 0, 300, 30)

    def get_local_ip(self):
        """Récupère l'adresse IP locale de la machine."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # Se connecte à une adresse externe pour déterminer quelle interface utiliser
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"  # Fallback sur localhost

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

            self._draw_text("Entrez l'adresse IP:", (center_x, center_y - 110), centered=True, font_size=24)
            self._dessiner_champ_texte(self.ip_adresse_rejoindre, self.champ_ip_rect) # Dessiner le champ IP
            self._draw_button("Rejoindre_ip", "Rejoindre", button_dict=self.rejoindre_buttons) # Bouton "Rejoindre"
            self._draw_button("Retour_rejoindre", "Retour", button_dict=self.rejoindre_buttons) # Bouton "Retour"
            
            # Afficher le statut de connexion si présent
            if self.connection_status:
                color = (255, 0, 0) if "Échec" in self.connection_status else (0, 128, 0)
                self._draw_text(self.connection_status, (center_x, center_y + 110), centered=True, color=color)

        elif self.menu_state == "hebergement":
            # --- Menu "Hébergement d'une partie" ---
            titre_text = "Hébergement d'une partie"
            self._draw_text(titre_text, (center_x, center_y - 150), centered=True, font_size=36)
            
            # Afficher l'adresse IP locale
            ip_text = f"Votre adresse IP: {self.local_ip}"
            self._draw_text(ip_text, (center_x, center_y - 80), centered=True, font_size=24)
            
            # Message d'attente
            self._draw_text("En attente d'une connexion...", (center_x, center_y - 20), centered=True, font_size=24)
            
            # Bouton pour annuler l'hébergement
            self.hebergement_buttons["Annuler"].topleft = (center_x - 100, center_y + 50)
            self._draw_button("Annuler", "Annuler", button_dict=self.hebergement_buttons)
            
            # Afficher le statut de connexion si présent
            if self.connection_status:
                color = (255, 0, 0) if "Échec" in self.connection_status else (0, 128, 0)
                self._draw_text(self.connection_status, (center_x, center_y + 110), centered=True, color=color)
                
        elif self.menu_state == "attente":
            # --- Menu d'attente après connexion réussie ---
            titre_text = "Connexion établie!"
            self._draw_text(titre_text, (center_x, center_y - 150), centered=True, font_size=36)
            
            message = "En attente du lancement de la partie..."
            self._draw_text(message, (center_x, center_y), centered=True, font_size=24)


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
        
        # Ajouter un curseur clignotant si le champ est actif
        if self.input_actif:
            cursor_pos = texte_rect.x + texte_surface.get_width() + 2
            blink_show = pygame.time.get_ticks() % 1000 < 500  # Clignotement chaque 500ms
            if blink_show:
                pygame.draw.line(self.screen, BLACK_COLOR, 
                                (cursor_pos, rect.y + 5), 
                                (cursor_pos, rect.y + rect.height - 5), 2)


    def handle_click(self, pos):
        """Gère les clics sur les boutons en fonction de l'état du menu."""
        if self.menu_state == "principal":
            if self.principal_buttons["Heberger"].collidepoint(pos):
                self.menu_state = "hebergement"
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
                # Vérifier que l'IP est valide avant de tenter la connexion
                if self._verifier_format_ip(self.ip_adresse_rejoindre):
                    return ("rejoindre", self.ip_adresse_rejoindre) # Indiquer "rejoindre" et l'IP
                else:
                    self.connection_status = "Format d'IP invalide"
                    self.connection_status_timer = pygame.time.get_ticks()
            elif self.rejoindre_buttons["Retour_rejoindre"].collidepoint(pos):
                self.menu_state = "principal" # Retour au menu principal multijoueur
                
        elif self.menu_state == "hebergement":
            if self.hebergement_buttons["Annuler"].collidepoint(pos):
                self.menu_state = "principal"
                return "annuler_hebergement"
                
        return None # Si aucun bouton important n'a été cliqué

    def handle_keydown(self, event):
        """Gère la saisie clavier pour le champ IP."""
        if self.menu_state == "rejoindre" and self.input_actif:
            if event.key == pygame.K_RETURN:
                # Essayer de se connecter quand on appuie sur Entrée
                if self._verifier_format_ip(self.ip_adresse_rejoindre):
                    return ("rejoindre", self.ip_adresse_rejoindre)
                else:
                    self.connection_status = "Format d'IP invalide"
                    self.connection_status_timer = pygame.time.get_ticks()
            elif event.key == pygame.K_BACKSPACE:
                self.ip_adresse_rejoindre = self.ip_adresse_rejoindre[:-1] # Supprimer le dernier caractère
            else:
                # N'accepter que des caractères valides pour une IP (chiffres et points)
                if event.unicode in "0123456789." and len(self.ip_adresse_rejoindre) < 15:
                    self.ip_adresse_rejoindre += event.unicode # Ajouter le caractère tapé
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
        # Effacer les messages de statut après un certain temps
        if self.connection_status and pygame.time.get_ticks() - self.connection_status_timer > 5000:
            self.connection_status = ""