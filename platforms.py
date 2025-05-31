import pygame
from settings import *

class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, color=PLATFORM_COLOR):
        super().__init__()
        
        # Create platform surface and rect
        self.image = pygame.Surface((width, height))
        self.image.fill(color)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
    
    def draw(self, screen):
        """Draw the platform on the screen"""
        screen.blit(self.image, self.rect)

class Ground(Platform):
    """Special platform class for the ground"""
    def __init__(self, x, y, width):
        super().__init__(x, y, width, GROUND_HEIGHT, DARK_GRAY) 