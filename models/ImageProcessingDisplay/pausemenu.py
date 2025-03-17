import pygame
from GLOBAL_VAR import *

class PauseMenu:
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.Font(MEDIEVALSHARP, 28)

        # Button dimensions
        self.button_width = 200
        self.button_height = 50

        # Initialize button positions (updated dynamically)
        self.buttons = {}
        self._update_buttons()

        self.volume = 0.5

        # Slider for volume
        self.slider_rect = pygame.Rect(screen.get_width() - 320, screen.get_height() - 50, 300, 10)
        self.slider_thumb_rect = pygame.Rect(self.slider_rect.x + int(self.volume * 300), self.slider_rect.y - 5, 10, 20)

    def _update_buttons(self):
        """Recalculate button positions based on screen size."""
        screen_width, screen_height = self.screen.get_size()
        center_x = screen_width // 2
        center_y = screen_height // 2

        self.buttons = {
            'resume': pygame.Rect(center_x - self.button_width // 2, center_y - 90, self.button_width, self.button_height),
            'main_menu': pygame.Rect(center_x - self.button_width // 2, center_y - 30, self.button_width, self.button_height),
            'save': pygame.Rect(center_x - self.button_width // 2, center_y + 30, self.button_width, self.button_height),
            'quit': pygame.Rect(center_x - self.button_width // 2, center_y + 90, self.button_width, self.button_height),
        }

    def draw(self):
        """Draw the pause menu overlay and buttons."""
        # Update button positions in case of screen resize
        self._update_buttons()

        # Draw semi-transparent overlay
        overlay = pygame.Surface(self.screen.get_size())
        overlay.set_alpha(220)  # Transparency level (0-255)
        overlay.fill((0, 0, 0))  # Black background
        self.screen.blit(overlay, (0, 0))
        screen_width, screen_height = self.screen.get_size()

        self.screen.blit(adjust_sprite(START_IMG, screen_width, screen_height), (0, 0))

                # Update slider position dynamically to always be at the bottom right
        self.slider_rect.topleft = (screen_width - 320, screen_height - 50)
        self.slider_thumb_rect.topleft = (self.slider_rect.x + int(self.volume * 300), self.slider_rect.y - 5)

        # Draw pause menu title
        title_text = self.font.render("Pause Menu", True, WHITE_COLOR)
        title_rect = title_text.get_rect(center=(self.screen.get_width() // 2, self.screen.get_height() // 2 - 150))
        self.screen.blit(title_text, title_rect)

        # Draw buttons
        for button_text, button_rect in self.buttons.items():
            pygame.draw.rect(self.screen, (50, 50, 50), button_rect)  # Button background
            text = self.font.render(button_text.replace('_', ' ').capitalize(), True, WHITE_COLOR)
            text_rect = text.get_rect(center=button_rect.center)
            self.screen.blit(text, text_rect)
        # Draw volume control slider
        self._draw_slider()

    def _draw_slider(self):
        """Draw the volume slider and its thumb."""
        pygame.draw.rect(self.screen, (200, 200, 200), self.slider_rect)  # Slider track
        pygame.draw.rect(self.screen, (0, 0, 255), self.slider_thumb_rect)  # Slider thumb

        # Draw volume text
        volume_text = f"Volume: {int(self.volume * 100)}%"
        self._draw_text(volume_text, (self.slider_rect.centerx, self.slider_rect.bottom + 10), centered=True)

    def _draw_text(self, text, pos, centered=False):
        """Draw text at a specific position."""
        font = pygame.font.Font(MEDIEVALSHARP, 28)
        rendered_text = font.render(text, True, WHITE_COLOR)
        text_rect = rendered_text.get_rect(center=pos if centered else None)
        self.screen.blit(rendered_text, text_rect if centered else pos)

    def handle_click(self, pos, game_state):
        """Handle button clicks based on mouse position."""
        if self.buttons['resume'].collidepoint(pos):
            game_state.toggle_pause()
        elif self.buttons['main_menu'].collidepoint(pos):
            game_state.go_to_main_menu()
        elif self.buttons['save'].collidepoint(pos):
            game_state.save()
        elif self.buttons['quit'].collidepoint(pos):
            pygame.quit()
            exit()
        # Handle volume slider interaction
        if self.slider_rect.collidepoint(pos):
            # Update volume based on the mouse x position
            self.volume = max(0.0, min(1.0, (pos[0] - self.slider_rect.x) / self.slider_rect.width))
            self.slider_thumb_rect.x = self.slider_rect.x + int(self.volume * self.slider_rect.width)
            pygame.mixer.music.set_volume(self.volume)  # Update volume of the music