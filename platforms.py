import pygame
from settings import *

class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, theme=None):
        super().__init__()
        
        # Use theme colors if provided, otherwise use fallback
        if theme:
            color = theme['platform_color']
        else:
            color = PLATFORM_COLOR  # Fallback color
        
        # Create platform surface and rect
        self.image = pygame.Surface((width, height))
        self.image.fill(color)
        
        # Add a simple border for visual appeal
        border_color = (max(0, color[0]-30), max(0, color[1]-30), max(0, color[2]-30))
        pygame.draw.rect(self.image, border_color, (0, 0, width, height), 2)
        
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
    
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
        
        # Override with ground-specific appearance
        self.image.fill(color)
        
        # Add texture lines for ground
        texture_color = (min(255, color[0]+20), min(255, color[1]+20), min(255, color[2]+20))
        for i in range(0, width, 20):
            pygame.draw.line(self.image, texture_color, (i, 5), (i, GROUND_HEIGHT-5))