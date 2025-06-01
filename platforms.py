import pygame
import math
from settings import *

class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, theme=None):
        super().__init__()
        
        # Load platform image
        try:
            self.base_platform_image = pygame.image.load("Assets/All porpuse platform.png").convert_alpha()
        except Exception as e:
            # Fallback to colored rectangle if image fails
            self.base_platform_image = None
            print(f"Warning: Could not load platform image: {e}")
        
        # Use theme colors if provided, otherwise use fallback
        if theme:
            color = theme['platform_color']
        else:
            color = PLATFORM_COLOR  # Fallback color
        
        # Create platform surface and rect
        if self.base_platform_image:
            # Scale the platform image to fit the desired size
            self.image = pygame.transform.scale(self.base_platform_image, (width, height))
            
            # Apply theme coloring to the platform image
            self.apply_theme_coloring(color)
        else:
            # Fallback to simple colored rectangle
            self.image = pygame.Surface((width, height))
            self.image.fill(color)
            
            # Add a simple border for visual appeal
            border_color = (max(0, color[0]-30), max(0, color[1]-30), max(0, color[2]-30))
            pygame.draw.rect(self.image, border_color, (0, 0, width, height), 2)
        
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
    
    def apply_theme_coloring(self, theme_color):
        """Apply theme-based coloring to the platform image"""
        width, height = self.image.get_size()
        
        # Create a color overlay with theme-specific effects
        color_overlay = pygame.Surface((width, height), pygame.SRCALPHA)
        
        # Add subtle gradient effects based on theme
        for y in range(height):
            alpha = int(80 + (y / height) * 40)  # Gradient from 80 to 120 alpha
            pygame.draw.line(color_overlay, (*theme_color, alpha), (0, y), (width, y))
        
        # Blend the overlay with the original image
        self.image.blit(color_overlay, (0, 0))
        
        # Add a subtle highlight to the top edge for 3D effect
        highlight_color = (min(255, theme_color[0] + 30), 
                          min(255, theme_color[1] + 30), 
                          min(255, theme_color[2] + 30))
        pygame.draw.line(self.image, highlight_color, (0, 0), (width, 0), 2)
        
        # Add a subtle shadow to the bottom edge
        shadow_color = (max(0, theme_color[0] - 30), 
                       max(0, theme_color[1] - 30), 
                       max(0, theme_color[2] - 30))
        pygame.draw.line(self.image, shadow_color, (0, height-1), (width, height-1), 1)
    
    def update(self, dt=0):
        """Update platform (override in subclasses for dynamic behavior)"""
        pass
    
    def draw(self, screen):
        """Draw the platform on the screen"""
        screen.blit(self.image, self.rect)

class MovingPlatform(Platform):
    """Horizontal moving platform that carries the player"""
    def __init__(self, start_x, y, width, height, end_x, speed=30, theme=None):
        super().__init__(start_x, y, width, height, theme)
        
        # Movement properties
        self.start_x = start_x
        self.end_x = end_x
        self.speed = speed  # pixels per second
        self.direction = 1  # 1 for right, -1 for left
        self.last_x = self.rect.x  # For calculating player movement
        
        # Add visual indicator (simple blue border)
        self.add_movement_indicator()
    
    def add_movement_indicator(self):
        """Add a simple visual indicator to show this platform moves"""
        # Just add a bright blue border to indicate movement
        border_color = (0, 150, 255)  # Bright blue
        pygame.draw.rect(self.image, border_color, self.image.get_rect(), 3)
        
        # Add some blue corner dots for extra visibility
        corner_size = 4
        pygame.draw.circle(self.image, border_color, (corner_size, corner_size), corner_size)
        pygame.draw.circle(self.image, border_color, (self.rect.width - corner_size, corner_size), corner_size)
        pygame.draw.circle(self.image, border_color, (corner_size, self.rect.height - corner_size), corner_size)
        pygame.draw.circle(self.image, border_color, (self.rect.width - corner_size, self.rect.height - corner_size), corner_size)
    
    def update(self, dt):
        """Update platform movement"""
        self.last_x = self.rect.x
        
        # Move platform
        self.rect.x += self.direction * self.speed * dt
        
        # Check bounds and reverse direction
        if self.direction > 0 and self.rect.x >= self.end_x:
            self.rect.x = self.end_x
            self.direction = -1
        elif self.direction < 0 and self.rect.x <= self.start_x:
            self.rect.x = self.start_x
            self.direction = 1
    
    def get_movement_delta(self):
        """Get how much the platform moved this frame"""
        return self.rect.x - self.last_x

class DisappearingPlatform(Platform):
    """Platform that disappears after being stepped on"""
    def __init__(self, x, y, width, height, theme=None, disappear_time=3.0):
        super().__init__(x, y, width, height, theme)
        
        # Disappearing properties
        self.disappear_time = disappear_time  # Time before disappearing
        self.fade_time = 1.0  # Time to fade out
        self.activated = False
        self.timer = 0.0
        self.original_image = self.image.copy()
        self.is_solid = True  # Whether player can land on it
    
    def activate(self):
        """Start the disappearing countdown"""
        if not self.activated:
            self.activated = True
            self.timer = 0.0
    
    def update(self, dt):
        """Update disappearing behavior"""
        if self.activated:
            self.timer += dt
            
            # Warning phase (flash)
            if self.timer < self.disappear_time - self.fade_time:
                # Flash faster as time runs out
                flash_speed = 3 + (self.timer / (self.disappear_time - self.fade_time)) * 5
                if int(self.timer * flash_speed) % 2:
                    # Make it flash by mixing with red
                    warning_surface = self.original_image.copy()
                    red_overlay = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
                    red_overlay.fill((255, 0, 0, 100))
                    warning_surface.blit(red_overlay, (0, 0))
                    self.image = warning_surface
                else:
                    self.image = self.original_image.copy()
            
            # Fading phase
            elif self.timer < self.disappear_time:
                fade_progress = (self.timer - (self.disappear_time - self.fade_time)) / self.fade_time
                alpha = int(255 * (1 - fade_progress))
                
                # Create fading image
                fading_image = self.original_image.copy()
                fade_surface = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
                fade_surface.fill((255, 255, 255, alpha))
                fading_image.blit(fade_surface, (0, 0), special_flags=pygame.BLEND_ALPHA_SDL2)
                self.image = fading_image
            
            # Disappeared phase
            else:
                self.is_solid = False
                self.image = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
                # Platform is now invisible and non-solid

class Ground(Platform):
    """Special platform class for the ground"""
    def __init__(self, x, y, width, theme=None):
        # Use theme colors if provided, otherwise use fallback
        if theme:
            color = theme['ground_color']
        else:
            color = DARK_GRAY  # Fallback color
            
        super().__init__(x, y, width, GROUND_HEIGHT, theme)
        
        # Apply additional ground-specific styling if using platform image
        if self.base_platform_image:
            # Make ground platforms slightly darker
            dark_overlay = pygame.Surface((width, GROUND_HEIGHT), pygame.SRCALPHA)
            dark_overlay.fill((*color, 80))
            self.image.blit(dark_overlay, (0, 0))
        
        # Add texture lines for ground
        for i in range(0, width, 20):
            pygame.draw.line(self.image, (min(255, color[0]+20), min(255, color[1]+20), min(255, color[2]+20)), 
                           (i, 5), (i, GROUND_HEIGHT-5))