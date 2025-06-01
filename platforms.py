import pygame
from settings import *

class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, theme=None):
        super().__init__()
        
        # Load platform image
        try:
            self.base_platform_image = pygame.image.load("Assets/Platform.png").convert_alpha()
        except:
            # Fallback to colored rectangle if image fails
            self.base_platform_image = None
            print("Warning: Could not load platform image, using solid color")
        
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
        
        # Create a color overlay
        color_overlay = pygame.Surface((width, height), pygame.SRCALPHA)
        color_overlay.fill((*theme_color, 100))  # Semi-transparent theme color
        
        # Blend the overlay with the original image using correct blend mode
        self.image.blit(color_overlay, (0, 0))
    
    def draw(self, screen):
        """Draw the platform on the screen"""
        screen.blit(self.image, self.rect)

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
        texture_color = (min(255, color[0]+20), min(255, color[1]+20), min(255, color[2]+20))
        for i in range(0, width, 20):
            pygame.draw.line(self.image, texture_color, (i, 5), (i, GROUND_HEIGHT-5))