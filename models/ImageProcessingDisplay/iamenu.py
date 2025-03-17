import pygame
from GLOBAL_VAR import *
from random import uniform

class IAMenu:
    def __init__(self, screen, num_players):
        self.screen = screen
        self.num_players = num_players
        self.sliders = []
        self.confirm_button = pygame.Rect(0, 0, 200, 50)  # Position updated in draw()
        
        # Ajuster l'espacement entre les joueurs
        self.slider_spacing = 100  # Plus d'espace entre les joueurs
        
        for i in range(num_players):
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
        
        for i, slider_set in enumerate(self.sliders):
            player_label = f"Player {i + 1}"  # Display Player 1, Player 2, etc.
            # Afficher l'étiquette du joueur plus haut pour chaque joueur
            self._draw_text(player_label, (slider_set["aggressive"].x, slider_set["aggressive"].y - 40))  
            self._draw_slider(slider_set["aggressive"], slider_set["aggressive_value"], f"Agressive")
            self._draw_slider(slider_set["defensive"], slider_set["defensive_value"], f"Defense")
        
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
        for slider_set in self.sliders:
            if slider_set["aggressive"].collidepoint(pos):
                slider_set["aggressive_value"] = min(3, max(1, round(slider_set["aggressive_value"] + 0.1, 1)))
            elif slider_set["defensive"].collidepoint(pos):
                slider_set["defensive_value"] = min(3, max(1, round(slider_set["defensive_value"] + 0.1, 1)))
        
        if self.confirm_button.collidepoint(pos):
            return self.get_ai_values()
        return None
    
    def get_ai_values(self):
        return [(s["aggressive_value"], s["defensive_value"]) for s in self.sliders]
