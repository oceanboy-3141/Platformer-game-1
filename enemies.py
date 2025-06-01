import pygame
import math
from settings import *

class Enemy(pygame.sprite.Sprite):
    """Base enemy class - to be expanded in future phases"""
    def __init__(self, x, y, theme=None):
        super().__init__()
        
        # Basic enemy properties
        self.theme = theme if theme else THEMES['crystal']
        self.health = 1
        self.speed = 30  # pixels per second
        self.direction = 1  # 1 for right, -1 for left
        
        # Create basic enemy sprite (red square for now)
        self.image = pygame.Surface((24, 24))
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        
        # Physics
        self.vel_x = 0
        self.vel_y = 0
        self.on_ground = False
    
    def update(self, dt, platforms):
        """Update enemy behavior - to be expanded"""
        pass
    
    def take_damage(self):
        """Handle taking damage"""
        self.health -= 1
        if self.health <= 0:
            self.kill()

class Walker(Enemy):
    """Basic walking enemy - moves back and forth"""
    def __init__(self, x, y, patrol_start, patrol_end, theme=None):
        super().__init__(x, y, theme)
        self.patrol_start = patrol_start
        self.patrol_end = patrol_end
        self.speed = 40
    
    def update(self, dt, platforms):
        """Simple patrol behavior"""
        # Move horizontally
        self.rect.x += self.direction * self.speed * dt
        
        # Turn around at patrol boundaries
        if self.direction > 0 and self.rect.x >= self.patrol_end:
            self.direction = -1
        elif self.direction < 0 and self.rect.x <= self.patrol_start:
            self.direction = 1

class Jumper(Enemy):
    """Enemy that hops around"""
    def __init__(self, x, y, theme=None):
        super().__init__(x, y, theme)
        self.jump_timer = 0
        self.jump_interval = 2.0  # Jump every 2 seconds
    
    def update(self, dt, platforms):
        """Hopping behavior"""
        self.jump_timer += dt
        
        # Apply gravity
        self.vel_y += PLAYER_GRAVITY
        if self.vel_y > PLAYER_MAX_FALL_SPEED:
            self.vel_y = PLAYER_MAX_FALL_SPEED
        
        # Jump periodically
        if self.jump_timer >= self.jump_interval and self.on_ground:
            self.vel_y = PLAYER_JUMP_SPEED * 0.7  # Smaller jumps than player
            self.jump_timer = 0
            self.on_ground = False
        
        # Update position
        self.rect.y += self.vel_y

class Flyer(Enemy):
    """Enemy that flies in patterns"""
    def __init__(self, x, y, pattern_width=200, pattern_height=100, theme=None):
        super().__init__(x, y, theme)
        self.start_x = x
        self.start_y = y
        self.pattern_width = pattern_width
        self.pattern_height = pattern_height
        self.angle = 0
        self.speed = 60
    
    def update(self, dt, platforms):
        """Figure-8 or circular flying pattern"""
        self.angle += self.speed * dt
        if self.angle >= 360:
            self.angle -= 360
        
        # Circular pattern
        offset_x = math.cos(math.radians(self.angle)) * self.pattern_width
        offset_y = math.sin(math.radians(self.angle * 2)) * self.pattern_height
        
        self.rect.centerx = self.start_x + offset_x
        self.rect.centery = self.start_y + offset_y

class Guard(Enemy):
    """Stationary enemy that activates when player is near"""
    def __init__(self, x, y, detection_range=150, theme=None):
        super().__init__(x, y, theme)
        self.detection_range = detection_range
        self.alert = False
        
        # Make guards look different (darker red)
        self.image.fill((150, 0, 0))
    
    def update(self, dt, platforms, player_pos=None):
        """Alert when player is nearby"""
        if player_pos:
            distance = math.sqrt((self.rect.centerx - player_pos[0])**2 + 
                               (self.rect.centery - player_pos[1])**2)
            
            if distance <= self.detection_range:
                self.alert = True
                # Could add alert behavior here (sound, color change, etc.)
            else:
                self.alert = False

# TODO: Future enemy types to implement:
# - Shooter: Fires projectiles at player
# - Chaser: Follows player when detected
# - Bouncer: Bounces off walls and platforms
# - Boss: Large enemy with multiple attacks
# - Spawner: Creates other enemies periodically 