import pygame
import math
from settings import *

class PowerUp(pygame.sprite.Sprite):
    """Base class for all power-ups"""
    def __init__(self, x, y, powerup_type, theme=None):
        super().__init__()
        
        self.powerup_type = powerup_type
        self.theme = theme if theme else THEMES['crystal']
        
        # Animation properties
        self.float_timer = 0
        self.rotation_timer = 0
        self.pulse_timer = 0
        
        # Create the power-up visual
        self.create_visual()
        
        # Position
        self.rect = self.base_image.get_rect()
        self.rect.centerx = x
        self.rect.centery = y
        
        self.collected = False
    
    def create_visual(self):
        """Create the visual representation of the power-up"""
        size = 24
        self.base_image = pygame.Surface((size, size), pygame.SRCALPHA)
        
        if self.powerup_type == "jump_boost":
            # Create a crystal-like jump boost icon
            color = (100, 255, 100)  # Green for jump
            
            # Draw crystal shape
            points = [
                (size//2, 2),
                (size-4, size//2),
                (size//2, size-2),
                (4, size//2)
            ]
            pygame.draw.polygon(self.base_image, color, points)
            
            # Add inner glow
            inner_points = [
                (size//2, 6),
                (size-8, size//2),
                (size//2, size-6),
                (8, size//2)
            ]
            pygame.draw.polygon(self.base_image, (200, 255, 200), inner_points)
            
            # Add upward arrow
            arrow_points = [
                (size//2, 8),
                (size//2 - 3, 14),
                (size//2 + 3, 14)
            ]
            pygame.draw.polygon(self.base_image, WHITE, arrow_points)
        
        self.image = self.base_image.copy()
    
    def update(self, dt):
        """Update power-up animations"""
        self.float_timer += dt * 2
        self.rotation_timer += dt * 3
        self.pulse_timer += dt * 4
        
        # Create animated version
        self.image = self.base_image.copy()
        
        # Floating animation
        float_offset = int(math.sin(self.float_timer) * 3)
        
        # Pulsing glow effect
        pulse_alpha = int(100 + math.sin(self.pulse_timer) * 50)
        glow_size = 32
        glow_surface = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
        
        if self.powerup_type == "jump_boost":
            glow_color = (100, 255, 100, pulse_alpha)
        
        pygame.draw.circle(glow_surface, glow_color, (glow_size//2, glow_size//2), glow_size//2)
        
        # Composite final image with glow and floating
        final_surface = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
        final_surface.blit(glow_surface, (0, 0))
        final_surface.blit(self.image, (4, 4 + float_offset))
        
        self.image = final_surface
        
        # Update rect for floating animation
        old_center = self.rect.center
        self.rect = self.image.get_rect()
        self.rect.center = (old_center[0], old_center[1] + float_offset)
    
    def collect(self):
        """Mark power-up as collected"""
        self.collected = True
        # Add collection particle effect here if desired

class PowerUpManager:
    """Manages active power-up effects on the player"""
    def __init__(self):
        self.active_effects = {}
    
    def add_effect(self, effect_type, duration):
        """Add a temporary effect"""
        self.active_effects[effect_type] = duration
    
    def update(self, dt):
        """Update all active effects"""
        # Decrease timers
        expired_effects = []
        for effect_type, time_left in self.active_effects.items():
            self.active_effects[effect_type] = time_left - dt
            if self.active_effects[effect_type] <= 0:
                expired_effects.append(effect_type)
        
        # Remove expired effects
        for effect_type in expired_effects:
            del self.active_effects[effect_type]
    
    def has_effect(self, effect_type):
        """Check if an effect is currently active"""
        return effect_type in self.active_effects
    
    def get_time_left(self, effect_type):
        """Get remaining time for an effect"""
        return self.active_effects.get(effect_type, 0) 