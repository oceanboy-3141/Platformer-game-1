import pygame
import math
from settings import *

class CharacterSelectScreen:
    def __init__(self, screen):
        self.screen = screen
        self.font_large = pygame.font.Font(None, 48)
        self.font_medium = pygame.font.Font(None, 36)
        self.font_small = pygame.font.Font(None, 24)
        
        self.selected_theme = "crystal"
        self.selected_pattern = "solid"
        self.selected_accessory = "none"
        
        self.theme_keys = list(THEMES.keys())
        self.pattern_keys = list(CHARACTER_PATTERNS.keys())
        self.accessory_keys = list(CHARACTER_ACCESSORIES.keys())
        
        self.current_selection = 0  # 0=theme, 1=pattern, 2=accessory
        self.selection_indices = [0, 0, 0]  # Current index for each category
        
        # Animation variables
        self.glow_timer = 0
        self.preview_scale = 1.0
        self.particle_timer = 0
        self.particles = []
        
    def handle_input(self, keys_pressed, keys_just_pressed):
        """Handle input for character selection"""
        # Helper function to safely check if key was just pressed
        def is_key_just_pressed(key):
            return keys_just_pressed.get(key, False)
        
        if is_key_just_pressed(pygame.K_UP) or is_key_just_pressed(pygame.K_w):
            self.current_selection = (self.current_selection - 1) % 3
            
        elif is_key_just_pressed(pygame.K_DOWN) or is_key_just_pressed(pygame.K_s):
            self.current_selection = (self.current_selection + 1) % 3
            
        elif is_key_just_pressed(pygame.K_LEFT) or is_key_just_pressed(pygame.K_a):
            if self.current_selection == 0:  # Theme
                self.selection_indices[0] = (self.selection_indices[0] - 1) % len(self.theme_keys)
                self.selected_theme = self.theme_keys[self.selection_indices[0]]
            elif self.current_selection == 1:  # Pattern
                self.selection_indices[1] = (self.selection_indices[1] - 1) % len(self.pattern_keys)
                self.selected_pattern = self.pattern_keys[self.selection_indices[1]]
            elif self.current_selection == 2:  # Accessory
                self.selection_indices[2] = (self.selection_indices[2] - 1) % len(self.accessory_keys)
                self.selected_accessory = self.accessory_keys[self.selection_indices[2]]
                
        elif is_key_just_pressed(pygame.K_RIGHT) or is_key_just_pressed(pygame.K_d):
            if self.current_selection == 0:  # Theme
                self.selection_indices[0] = (self.selection_indices[0] + 1) % len(self.theme_keys)
                self.selected_theme = self.theme_keys[self.selection_indices[0]]
            elif self.current_selection == 1:  # Pattern
                self.selection_indices[1] = (self.selection_indices[1] + 1) % len(self.pattern_keys)
                self.selected_pattern = self.pattern_keys[self.selection_indices[1]]
            elif self.current_selection == 2:  # Accessory
                self.selection_indices[2] = (self.selection_indices[2] + 1) % len(self.accessory_keys)
                self.selected_accessory = self.accessory_keys[self.selection_indices[2]]
                
        return is_key_just_pressed(pygame.K_RETURN) or is_key_just_pressed(pygame.K_SPACE)
    
    def update(self, dt):
        """Update animations and effects"""
        self.glow_timer += dt * 3
        self.particle_timer += dt
        
        # Update preview scale animation
        self.preview_scale = 1.0 + 0.1 * math.sin(self.glow_timer)
        
        # Add particles around the character preview
        if self.particle_timer > 0.1:
            self.add_particle()
            self.particle_timer = 0
            
        # Update existing particles
        for particle in self.particles[:]:
            particle['life'] -= dt
            particle['y'] -= particle['speed'] * dt
            particle['x'] += math.sin(particle['life'] * 5) * 20 * dt
            
            if particle['life'] <= 0:
                self.particles.remove(particle)
    
    def add_particle(self):
        """Add a magical particle effect"""
        theme = THEMES[self.selected_theme]
        center_x = SCREEN_WIDTH // 2
        center_y = SCREEN_HEIGHT // 2 - 50
        
        particle = {
            'x': center_x + (pygame.math.Vector2(1, 0).rotate(len(self.particles) * 30).x * 60),
            'y': center_y + 100,
            'speed': 50 + len(self.particles) * 5,
            'life': 2.0,
            'color': theme['particle_color']
        }
        self.particles.append(particle)
        
        # Limit particle count
        if len(self.particles) > 20:
            self.particles.pop(0)
    
    def draw_character_preview(self):
        """Draw the character preview with current selections"""
        theme = THEMES[self.selected_theme]
        center_x = SCREEN_WIDTH // 2
        center_y = SCREEN_HEIGHT // 2 - 50
        
        # Draw glow effect
        glow_radius = 50 + 10 * math.sin(self.glow_timer)
        glow_surf = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (*theme['glow_color'], 30), (glow_radius, glow_radius), glow_radius)
        self.screen.blit(glow_surf, (center_x - glow_radius, center_y - glow_radius))
        
        # Calculate scaled dimensions
        width = int(PLAYER_WIDTH * 3 * self.preview_scale)
        height = int(PLAYER_HEIGHT * 3 * self.preview_scale)
        
        # Create character surface
        char_surf = pygame.Surface((width, height), pygame.SRCALPHA)
        
        # Draw character based on pattern
        if self.selected_pattern == "solid":
            char_surf.fill(theme['player_color'])
        elif self.selected_pattern == "stripes":
            char_surf.fill(theme['player_color'])
            for i in range(0, height, 8):
                pygame.draw.rect(char_surf, theme['player_accent'], (0, i, width, 4))
        elif self.selected_pattern == "dots":
            char_surf.fill(theme['player_color'])
            for x in range(8, width-8, 12):
                for y in range(8, height-8, 12):
                    pygame.draw.circle(char_surf, theme['player_accent'], (x, y), 3)
        elif self.selected_pattern == "gradient":
            for y in range(height):
                color_ratio = y / height
                r = int(theme['player_color'][0] * (1-color_ratio) + theme['player_accent'][0] * color_ratio)
                g = int(theme['player_color'][1] * (1-color_ratio) + theme['player_accent'][1] * color_ratio)
                b = int(theme['player_color'][2] * (1-color_ratio) + theme['player_accent'][2] * color_ratio)
                pygame.draw.line(char_surf, (r, g, b), (0, y), (width, y))
        
        # Draw accessories
        if self.selected_accessory == "cape":
            # Simple cape behind character
            cape_points = [
                (width//4, height//3),
                (width//4 - 10, height + 5),
                (width//4 + 15, height + 5),
                (width//2, height//3)
            ]
            pygame.draw.polygon(char_surf, theme['player_accent'], cape_points)
            
        elif self.selected_accessory == "hat":
            # Simple hat on top
            pygame.draw.rect(char_surf, theme['player_accent'], (width//4, -5, width//2, 10))
            
        elif self.selected_accessory == "belt":
            # Belt around middle
            pygame.draw.rect(char_surf, theme['player_accent'], (0, height//2-2, width, 4))
        
        # Draw character
        char_rect = char_surf.get_rect(center=(center_x, center_y))
        self.screen.blit(char_surf, char_rect)
        
        # Draw particles
        for particle in self.particles:
            pygame.draw.circle(self.screen, particle['color'], 
                             (int(particle['x']), int(particle['y'])), 
                             max(1, int(particle['life'] * 3)))
    
    def draw(self):
        """Draw the character selection screen"""
        theme = THEMES[self.selected_theme]
        
        # Background
        self.screen.fill(theme['bg_color'])
        
        # Title
        title_text = self.font_large.render("Choose Your Character", True, WHITE)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH//2, 80))
        self.screen.blit(title_text, title_rect)
        
        # Character preview
        self.draw_character_preview()
        
        # Selection categories
        categories = [
            ("Theme", self.selected_theme, THEMES[self.selected_theme]['name']),
            ("Pattern", self.selected_pattern, CHARACTER_PATTERNS[self.selected_pattern]),
            ("Accessory", self.selected_accessory, CHARACTER_ACCESSORIES[self.selected_accessory])
        ]
        
        y_start = SCREEN_HEIGHT - 250
        for i, (category, key, display_name) in enumerate(categories):
            y_pos = y_start + i * 60
            
            # Highlight current selection
            if i == self.current_selection:
                highlight_rect = pygame.Rect(50, y_pos - 20, SCREEN_WIDTH - 100, 50)
                pygame.draw.rect(self.screen, theme['glow_color'], highlight_rect, 3)
            
            # Category label
            cat_text = self.font_medium.render(f"{category}:", True, WHITE)
            self.screen.blit(cat_text, (100, y_pos))
            
            # Current selection
            sel_text = self.font_medium.render(display_name, True, theme['particle_color'])
            self.screen.blit(sel_text, (250, y_pos))
            
            # Navigation arrows
            if i == self.current_selection:
                arrow_left = self.font_medium.render("◄", True, WHITE)
                arrow_right = self.font_medium.render("►", True, WHITE)
                self.screen.blit(arrow_left, (200, y_pos))
                self.screen.blit(arrow_right, (SCREEN_WIDTH - 150, y_pos))
        
        # Theme description
        desc_text = self.font_small.render(THEMES[self.selected_theme]['description'], True, LIGHT_GRAY)
        desc_rect = desc_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 120))
        self.screen.blit(desc_text, desc_rect)
        
        # Instructions
        instructions = [
            "↑↓ / WS: Select Category",
            "←→ / AD: Change Selection", 
            "ENTER / SPACE: Start Game"
        ]
        
        for i, instruction in enumerate(instructions):
            inst_text = self.font_small.render(instruction, True, WHITE)
            inst_rect = inst_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT - 80 + i * 25))
            self.screen.blit(inst_text, inst_rect)
    
    def get_character_config(self):
        """Return the selected character configuration"""
        return {
            'theme': self.selected_theme,
            'pattern': self.selected_pattern,
            'accessory': self.selected_accessory
        } 