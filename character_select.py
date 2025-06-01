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
        self.start_tutorial = False  # Whether to start with tutorial
        
        self.theme_keys = list(THEMES.keys())
        self.pattern_keys = list(CHARACTER_PATTERNS.keys())
        self.accessory_keys = list(CHARACTER_ACCESSORIES.keys())
        
        self.current_selection = 0  # 0=theme, 1=pattern, 2=accessory, 3=tutorial
        self.selection_indices = [0, 0, 0, 0]  # Current index for each category
        
        # Animation variables
        self.glow_timer = 0
        self.preview_scale = 1.0
        self.particle_timer = 0
        self.particles = []
        
        # Load base humanoid sprite for preview
        self.base_humanoid = self.load_base_sprite()
        
        # Load background images for preview
        self.load_background_previews()
        
    def load_base_sprite(self):
        """Load the base humanoid sprite for preview"""
        try:
            sprite = pygame.image.load("Assets/Player.png").convert_alpha()
            sprite = pygame.transform.scale(sprite, (PLAYER_WIDTH * 2, PLAYER_HEIGHT * 2))
            return sprite
        except:
            return self.create_fallback_humanoid()
    
    def create_fallback_humanoid(self):
        """Create a simple humanoid shape for preview"""
        width, height = PLAYER_WIDTH * 2, PLAYER_HEIGHT * 2
        sprite = pygame.Surface((width, height), pygame.SRCALPHA)
        
        # Head
        head_radius = width // 4
        pygame.draw.circle(sprite, (255, 220, 177), 
                         (width // 2, head_radius + 4), head_radius)
        
        # Body
        body_width = width // 2
        body_height = height // 2
        pygame.draw.rect(sprite, (100, 100, 100), 
                        (width // 2 - body_width // 2, head_radius * 2, 
                         body_width, body_height))
        
        # Arms
        arm_width = 8
        arm_height = body_height // 2
        pygame.draw.rect(sprite, (255, 220, 177), 
                        (width // 2 - body_width // 2 - arm_width, 
                         head_radius * 2 + 10, arm_width, arm_height))
        pygame.draw.rect(sprite, (255, 220, 177), 
                        (width // 2 + body_width // 2, 
                         head_radius * 2 + 10, arm_width, arm_height))
        
        # Legs
        leg_width = 12
        leg_height = height - (head_radius * 2 + body_height)
        pygame.draw.rect(sprite, (50, 50, 200), 
                        (width // 2 - leg_width - 4, 
                         head_radius * 2 + body_height, leg_width, leg_height))
        pygame.draw.rect(sprite, (50, 50, 200), 
                        (width // 2 + 4, 
                         head_radius * 2 + body_height, leg_width, leg_height))
        
        return sprite
    
    def create_preview_character(self):
        """Create a preview of the character with current selections"""
        # Start with base sprite
        sprite = self.base_humanoid.copy()
        theme = THEMES[self.selected_theme]
        
        # Apply theme-based coloring (similar to player.py but simplified for preview)
        width, height = sprite.get_size()
        
        # Color mappings for preview
        color_mappings = {
            'crystal': {'skin': (150, 200, 255), 'clothes': theme['player_color']},
            'forest': {'skin': (255, 220, 177), 'clothes': theme['player_color']},
            'metal': {'skin': (200, 200, 220), 'clothes': theme['player_color']},
            'stone': {'skin': (220, 190, 150), 'clothes': theme['player_color']}
        }
        
        theme_colors = color_mappings.get(self.selected_theme, color_mappings['crystal'])
        
        # Apply colors (simplified version)
        for x in range(width):
            for y in range(height):
                pixel_color = sprite.get_at((x, y))
                if pixel_color[3] > 0:
                    brightness = sum(pixel_color[:3]) / 3
                    
                    if brightness > 200:  # Skin areas
                        new_color = theme_colors['skin']
                    elif brightness > 100:  # Clothing areas
                        new_color = theme_colors['clothes']
                    else:  # Details
                        new_color = theme['player_accent']
                    
                    sprite.set_at((x, y), (*new_color, pixel_color[3]))
        
        # Apply pattern overlay for preview
        if self.selected_pattern != "solid":
            pattern_overlay = pygame.Surface((width, height), pygame.SRCALPHA)
            
            if self.selected_pattern == "stripes":
                for i in range(0, height, 12):
                    pygame.draw.rect(pattern_overlay, (*theme['player_accent'], 80), 
                                   (0, i, width, 4))
            elif self.selected_pattern == "dots":
                for x in range(12, width-12, 16):
                    for y in range(12, height-12, 16):
                        pygame.draw.circle(pattern_overlay, (*theme['player_accent'], 100), 
                                         (x, y), 3)
            elif self.selected_pattern == "gradient":
                for y in range(height):
                    alpha = int((y / height) * 60)
                    pygame.draw.line(pattern_overlay, (*theme['player_accent'], alpha), 
                                   (0, y), (width, y))
            
            sprite.blit(pattern_overlay, (0, 0))
        
        # Add accessories for preview
        if self.selected_accessory == "cape":
            cape_points = [
                (width//4, height//3),
                (width//4 - 12, height - 4),
                (width//4 + 18, height - 4),
                (width//2, height//3)
            ]
            pygame.draw.polygon(sprite, theme['player_accent'], cape_points)
            
        elif self.selected_accessory == "hat":
            pygame.draw.rect(sprite, theme['player_accent'], (width//4, 4, width//2, 12))
            pygame.draw.rect(sprite, theme['player_accent'], (width//4 - 6, 14, width//2 + 12, 4))
            
        elif self.selected_accessory == "belt":
            pygame.draw.rect(sprite, theme['player_accent'], (0, height//2, width, 6))
            pygame.draw.rect(sprite, (min(255, theme['player_accent'][0] + 50),
                                    min(255, theme['player_accent'][1] + 50),
                                    min(255, theme['player_accent'][2] + 50)), 
                           (width//2 - 6, height//2, 12, 6))
        
        return sprite
    
    def handle_input(self, keys_pressed, keys_just_pressed):
        """Handle input for character selection"""
        # Helper function to safely check if key was just pressed
        def is_key_just_pressed(key):
            return keys_just_pressed.get(key, False)
        
        if is_key_just_pressed(pygame.K_UP) or is_key_just_pressed(pygame.K_w):
            self.current_selection = (self.current_selection - 1) % 4
            
        elif is_key_just_pressed(pygame.K_DOWN) or is_key_just_pressed(pygame.K_s):
            self.current_selection = (self.current_selection + 1) % 4
            
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
            elif self.current_selection == 3:  # Tutorial
                self.selection_indices[3] = (self.selection_indices[3] - 1) % 2
                self.start_tutorial = bool(self.selection_indices[3])
                
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
            elif self.current_selection == 3:  # Tutorial
                self.selection_indices[3] = (self.selection_indices[3] + 1) % 2
                self.start_tutorial = bool(self.selection_indices[3])
                
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
            'x': center_x + (pygame.math.Vector2(1, 0).rotate(len(self.particles) * 30).x * 80),
            'y': center_y + 120,
            'speed': 50 + len(self.particles) * 5,
            'life': 2.0,
            'color': theme['particle_color']
        }
        self.particles.append(particle)
        
        # Limit particle count
        if len(self.particles) > 20:
            self.particles.pop(0)
    
    def draw_character_preview(self):
        """Draw the humanoid character preview with current selections"""
        theme = THEMES[self.selected_theme]
        center_x = SCREEN_WIDTH // 2
        center_y = SCREEN_HEIGHT // 2 - 50
        
        # Draw glow effect
        glow_radius = 70 + 15 * math.sin(self.glow_timer)
        glow_surf = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (*theme['glow_color'], 30), (glow_radius, glow_radius), glow_radius)
        self.screen.blit(glow_surf, (center_x - glow_radius, center_y - glow_radius))
        
        # Create and scale character preview
        char_sprite = self.create_preview_character()
        
        # Apply scaling animation
        scaled_width = int(char_sprite.get_width() * self.preview_scale)
        scaled_height = int(char_sprite.get_height() * self.preview_scale)
        char_sprite = pygame.transform.scale(char_sprite, (scaled_width, scaled_height))
        
        # Draw character
        char_rect = char_sprite.get_rect(center=(center_x, center_y))
        self.screen.blit(char_sprite, char_rect)
        
        # Draw particles
        for particle in self.particles:
            pygame.draw.circle(self.screen, particle['color'], 
                             (int(particle['x']), int(particle['y'])), 
                             max(1, int(particle['life'] * 3)))
    
    def draw(self):
        """Draw the character selection screen"""
        theme = THEMES[self.selected_theme]
        
        # Background - use themed background if available
        if self.selected_theme in self.background_previews and self.background_previews[self.selected_theme]:
            # Draw the themed background
            self.screen.blit(self.background_previews[self.selected_theme], (0, 0))
            
            # Add subtle overlay to make text more readable
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((*BLACK, 80))  # Semi-transparent dark overlay
            self.screen.blit(overlay, (0, 0))
        else:
            # Fallback to solid color background
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
            ("Accessory", self.selected_accessory, CHARACTER_ACCESSORIES[self.selected_accessory]),
            ("Tutorial", self.start_tutorial, "Yes" if self.start_tutorial else "No")
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
        desc_rect = desc_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 140))
        self.screen.blit(desc_text, desc_rect)
        
        # Instructions
        instructions = [
            "↑↓ / WS: Select Category",
            "←→ / AD: Change Selection", 
            "Tutorial: Learn all mechanics step-by-step",
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
            'accessory': self.selected_accessory,
            'start_tutorial': self.start_tutorial
        }
    
    def load_background_previews(self):
        """Load background images for theme previews"""
        self.background_previews = {}
        
        # Background file mapping for each theme
        background_files = {
            'crystal': 'Back round Crystal.png',
            'forest': 'Background forest gardioun.png', 
            'metal': 'Background Cyber runner.png',
            'stone': 'Background anchiant explorer.png'
        }
        
        # Load all theme backgrounds at a smaller size for preview
        for theme_name, filename in background_files.items():
            try:
                bg_image = pygame.image.load(f"Assets/{filename}").convert()
                # Scale to screen size for preview
                bg_image = pygame.transform.scale(bg_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
                self.background_previews[theme_name] = bg_image
            except Exception as e:
                print(f"Warning: Could not load background preview for {theme_name}: {e}")
                self.background_previews[theme_name] = None 