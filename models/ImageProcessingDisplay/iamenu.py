import pygame
from GLOBAL_VAR import *  # Assurez-vous que GLOBAL_VAR est correctement défini si nécessaire
from random import uniform

class IAMenu:
    def __init__(self, screen, selected_players, num_player=1, is_multiplayer=False):
        """
        Initialise le menu de l'IA.

        Args:
            screen: L'écran Pygame sur lequel dessiner le menu.
            selected_players: Le nombre total de joueurs sélectionnés (IA inclus).
            num_player: Le numéro du joueur à configurer en mode multijoueur (par défaut: 1).
            is_multiplayer: Un booléen indiquant si le jeu est en mode multijoueur (par défaut: False).
        """
        self.screen = screen
        self.selected_players = selected_players
        self.num_player = num_player
        self.is_multiplayer = is_multiplayer
        self.sliders = []
        self.confirm_button = pygame.Rect(0, 0, 200, 50)

        self.slider_spacing = 100

        for i in range(selected_players): # On crée toujours les sliders pour tous les joueurs, mais on les affiche conditionnellement
            aggressive_slider = pygame.Rect(100, 100 + i * self.slider_spacing, 300, 10)
            defensive_slider = pygame.Rect(100, 130 + i * self.slider_spacing, 300, 10)
            self.sliders.append({
                "aggressive": aggressive_slider,
                "defensive": defensive_slider,
                "aggressive_value": round(uniform(1, 3), 1),
                "defensive_value": round(uniform(1, 3), 1)
            })

    def draw(self):
        self.screen.fill((255, 255, 255))
        screen_width, screen_height = self.screen.get_size()

        if self.is_multiplayer:
            # Mode multijoueur: afficher seulement le joueur spécifié par num_player
            player_index = self.num_player # Ajuster l'index car num_player est 1-indexé
            if 0 <= player_index < len(self.sliders): # Vérification pour éviter les erreurs d'index
                slider_set = self.sliders[player_index]
                player_label = f"Player {self.num_player} (IA)" # Indiquer que c'est l'IA en multijoueur
                self._draw_text(player_label, (slider_set["aggressive"].x, slider_set["aggressive"].y - 40))
                self._draw_slider(slider_set["aggressive"], slider_set["aggressive_value"], "Agressive")
                self._draw_slider(slider_set["defensive"], slider_set["defensive_value"], "Defense")
        else:
            # Mode solo: afficher tous les joueurs jusqu'à selected_players
            for i, slider_set in enumerate(self.sliders):
                player_label = f"Player {i + 1} (IA)" # Indiquer que c'est l'IA en solo aussi
                self._draw_text(player_label, (slider_set["aggressive"].x, slider_set["aggressive"].y - 40))
                self._draw_slider(slider_set["aggressive"], slider_set["aggressive_value"], "Agressive")
                self._draw_slider(slider_set["defensive"], slider_set["defensive_value"], "Defense")

        self.confirm_button.topleft = (screen_width // 2 - 100, screen_height - 80)
        pygame.draw.rect(self.screen, (0, 255, 0), self.confirm_button)
        self._draw_text("Confirmer", (self.confirm_button.centerx, self.confirm_button.centery), centered=True)

    def _draw_slider(self, slider_rect, value, label):
        pygame.draw.rect(self.screen, (200, 200, 200), slider_rect)
        thumb_x = slider_rect.x + int((value - 1) / 2 * slider_rect.width)
        pygame.draw.rect(self.screen, (0, 0, 255), (thumb_x, slider_rect.y - 5, 10, 20))
        self._draw_text(f"{label}: {value}", (slider_rect.x, slider_rect.y - 20))

    def _draw_text(self, text, pos, centered=False):
        font = pygame.font.Font(None, 28)
        rendered_text = font.render(text, True, (0, 0, 0))
        text_rect = rendered_text.get_rect()

        if centered:
            text_rect.center = pos
        else:
            text_rect.topleft = pos

        self.screen.blit(rendered_text, text_rect)

    def handle_click(self, pos):
        # Gestion des clics pour seulement les sliders affichés (important en multijoueur)
        sliders_to_check = []
        if self.is_multiplayer:
            player_index = self.num_player
            if 0 <= player_index < len(self.sliders):
                sliders_to_check.append(self.sliders[player_index])
        else:
            sliders_to_check = self.sliders

        for slider_set in sliders_to_check:
            if slider_set["aggressive"].collidepoint(pos):
                slider_set["aggressive_value"] = min(3, max(1, round(slider_set["aggressive_value"] + 0.1, 1)))
            elif slider_set["defensive"].collidepoint(pos):
                slider_set["defensive_value"] = min(3, max(1, round(slider_set["defensive_value"] + 0.1, 1)))

        if self.confirm_button.collidepoint(pos):
            return self.get_ai_values()
        return None

    def get_ai_values(self):
        result = []
        if self.is_multiplayer:
            s = self.sliders[self.num_player]
            if s["defensive_value"] >= s["aggressive_value"]-0.5 and s["defensive_value"] <= s["aggressive_value"]+0.5 :
                result.append("balanced")
                result.append(s["aggressive_value"])
                result.append(s["defensive_value"])
            elif s["defensive_value"] > s["aggressive_value"]:
                result.append("defensive")
                result.append(s["aggressive_value"])
                result.append(s["defensive_value"])
            else:
                result.append("aggressive")
                result.append(s["aggressive_value"])
                result.append(s["defensive_value"])
            return result
        else:
            for s in self.sliders:
                if s["defensive_value"] >= s["aggressive_value"]-0.5 and s["defensive_value"] <= s["aggressive_value"]+0.5 :
                    result.append("balanced")
                    result.append(s["aggressive_value"])
                    result.append(s["defensive_value"])
                elif s["defensive_value"] > s["aggressive_value"]:
                    result.append("defensive")
                    result.append(s["aggressive_value"])
                    result.append(s["defensive_value"])
                else:
                    result.append("aggressive")
                    result.append(s["aggressive_value"])
                    result.append(s["defensive_value"])
            return result


if __name__ == '__main__':
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("IA Menu Test")

    # Exemple d'utilisation en mode solo (comme avant)
    ia_menu_solo = IAMenu(screen, selected_players=3)

    # Exemple d'utilisation en mode multijoueur pour le joueur 2
    ia_menu_multi_player2 = IAMenu(screen, selected_players=3, num_player=2, is_multiplayer=True)

    running_solo = False # False par défaut pour tester le mode multijoueur
    running_multi = True # True pour tester le mode multijoueur

    if running_solo:
        ia_menu = ia_menu_solo
    elif running_multi:
        ia_menu = ia_menu_multi_player2
    else: # Par défaut, mode solo
        ia_menu = ia_menu_solo


    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Bouton gauche de la souris
                    ai_values = ia_menu.handle_click(event.pos)
                    if ai_values:
                        print("Valeurs de l'IA confirmées:", ai_values)
                        running = False # Pour cet exemple, on quitte après confirmation

        ia_menu.draw()
        pygame.display.flip()

    pygame.quit()