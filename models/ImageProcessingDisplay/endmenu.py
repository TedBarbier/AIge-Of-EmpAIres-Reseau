import pygame
from GLOBAL_VAR import *

class EndMenu:
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.Font(MEDIEVALSHARP, 28)
        self.title_font = pygame.font.Font(MEDIEVALSHARP, 36)

        # Button dimensions
        self.button_width = 200
        self.button_height = 50

        # Initialize button positions (updated dynamically)
        self.main_menu_button = None
        self.quit_button = None
        self._update_buttons()

    def _update_buttons(self):
        """Recalculate button positions based on screen size."""
        screen_width, screen_height = self.screen.get_size()
        center_x = screen_width // 2
        self.main_menu_button = pygame.Rect(center_x - self.button_width // 2, screen_height - 100, self.button_width, self.button_height)
        self.quit_button = pygame.Rect(center_x - self.button_width // 2, screen_height - 170, self.button_width, self.button_height)

    def draw(self, player_scores):
        """Draw the end menu with the leaderboard and buttons."""
        # Update button positions in case of screen resize
        self._update_buttons()

        # Draw semi-transparent overlay
        overlay = pygame.Surface(self.screen.get_size())
        overlay.set_alpha(220)  # Transparency level (0-255)
        overlay.fill((0, 0, 0))  # Black background
        self.screen.blit(overlay, (0, 0))

        # Draw end menu title
        title_text = self.title_font.render("End Game", True, WHITE_COLOR)
        title_rect = title_text.get_rect(center=(self.screen.get_width() // 2, 50))
        self.screen.blit(title_text, title_rect)

        # Determine the number of players and adjust layout
        num_players = len(player_scores)
        max_players_in_column = num_players // 2 if num_players > 5 else num_players
        column_1_x = self.screen.get_width() // 2 - 200  # Left column x position (more space)
        column_2_x = self.screen.get_width() // 2 + 200  # Right column x position (more space)
        start_y = 150  # Starting Y position for player entries

        # Draw leaderboard with two columns if there are more than 5 players
        for i, (player, score) in enumerate(player_scores):
            if num_players > 5:
                column = 1 if i >= max_players_in_column else 0
                x_pos = column_2_x if column == 1 else column_1_x
                row_index = i if column == 0 else i - max_players_in_column
            else:
                x_pos = self.screen.get_width() // 2
                row_index = i

            # Draw rank (i+1) in white
            rank_text = self.font.render(f"{i + 1}.", True, WHITE_COLOR)
            rank_rect = rank_text.get_rect(center=(x_pos - 100, start_y + row_index * 40))
            self.screen.blit(rank_text, rank_rect)

            # Draw player name in the color of their team (using TEAM_COLORS)
            player_name_text = self.font.render(f"Player {player}", True, TEAM_COLORS[player])
            player_name_rect = player_name_text.get_rect(center=(x_pos, start_y + row_index * 40))
            self.screen.blit(player_name_text, player_name_rect)

            # Draw score in white
            score_text = self.font.render(f"{(int(len(score)))*' '}:{score}", True, WHITE_COLOR)
            score_rect = score_text.get_rect(center=(x_pos + 100, start_y + row_index * 40))
            self.screen.blit(score_text, score_rect)

        # Draw buttons
        pygame.draw.rect(self.screen, (50, 50, 50), self.main_menu_button)  # Button background
        button_text = self.font.render("Menu Principal", True, WHITE_COLOR)
        button_rect = button_text.get_rect(center=self.main_menu_button.center)
        self.screen.blit(button_text, button_rect)

        pygame.draw.rect(self.screen, (50, 50, 50), self.quit_button)  # Button background
        button_text = self.font.render("Quitter", True, WHITE_COLOR)
        button_rect = button_text.get_rect(center=self.quit_button.center)
        self.screen.blit(button_text, button_rect)

    def handle_click(self, pos, game_state):
        """Handle button clicks for going to main menu or quitting the game."""
        if self.main_menu_button.collidepoint(pos):
            game_state.go_to_main_menu()
        elif self.quit_button.collidepoint(pos):
            pygame.quit()
            exit()
