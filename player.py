import pygame
import math
from settings import *

class Player(pygame.sprite.Sprite):
    def __init__(self, x, y, character_config):
        super().__init__()
        
        # Store character configuration
        self.character_config = character_config
        self.theme = THEMES[character_config['theme']]
        
        # Create player surface and rect
        self.base_image = self.create_character_sprite()
        self.image = self.base_image.copy()
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        
        # Physics variables
        self.vel_x = 0
        self.vel_y = 0
        self.on_ground = False
        self.jump_count = 0
        self.max_jumps = 2  # Allow double jump
        
        # Input state
        self.moving_left = False
        self.moving_right = False
        
        # Visual effects
        self.particle_timer = 0
        self.particles = []
        self.shadow_offset = 3
        
        # Animation state
        self.animation_timer = 0
        self.is_moving = False
        self.facing_right = True
    
    def create_character_sprite(self):
        """Create the character sprite based on customization options"""
        sprite = pygame.Surface((PLAYER_WIDTH, PLAYER_HEIGHT), pygame.SRCALPHA)
        
        # Draw character based on pattern
        pattern = self.character_config['pattern']
        theme = self.theme
        
        if pattern == "solid":
            sprite.fill(theme['player_color'])
        elif pattern == "stripes":
            sprite.fill(theme['player_color'])
            for i in range(0, PLAYER_HEIGHT, 6):
                pygame.draw.rect(sprite, theme['player_accent'], (0, i, PLAYER_WIDTH, 3))
        elif pattern == "dots":
            sprite.fill(theme['player_color'])
            for x in range(6, PLAYER_WIDTH-6, 8):
                for y in range(6, PLAYER_HEIGHT-6, 8):
                    pygame.draw.circle(sprite, theme['player_accent'], (x, y), 2)
        elif pattern == "gradient":
            for y in range(PLAYER_HEIGHT):
                color_ratio = y / PLAYER_HEIGHT
                r = int(theme['player_color'][0] * (1-color_ratio) + theme['player_accent'][0] * color_ratio)
                g = int(theme['player_color'][1] * (1-color_ratio) + theme['player_accent'][1] * color_ratio)
                b = int(theme['player_color'][2] * (1-color_ratio) + theme['player_accent'][2] * color_ratio)
                pygame.draw.line(sprite, (r, g, b), (0, y), (PLAYER_WIDTH, y))
        
        # Add accessories
        accessory = self.character_config['accessory']
        if accessory == "cape":
            # Simple cape behind character (drawn first so it's behind)
            cape_sprite = pygame.Surface((PLAYER_WIDTH + 10, PLAYER_HEIGHT + 5), pygame.SRCALPHA)
            cape_points = [
                (PLAYER_WIDTH//4 - 5, PLAYER_HEIGHT//3),
                (PLAYER_WIDTH//4 - 15, PLAYER_HEIGHT + 5),
                (PLAYER_WIDTH//4 + 10, PLAYER_HEIGHT + 5),
                (PLAYER_WIDTH//2 - 5, PLAYER_HEIGHT//3)
            ]
            pygame.draw.polygon(cape_sprite, theme['player_accent'], cape_points)
            cape_sprite.blit(sprite, (5, 0))
            return cape_sprite
            
        elif accessory == "hat":
            # Simple hat on top
            pygame.draw.rect(sprite, theme['player_accent'], (PLAYER_WIDTH//4, -2, PLAYER_WIDTH//2, 6))
            
        elif accessory == "belt":
            # Belt around middle
            pygame.draw.rect(sprite, theme['player_accent'], (0, PLAYER_HEIGHT//2-1, PLAYER_WIDTH, 3))
        
        return sprite
    
    def handle_input(self, keys):
        """Handle player input for movement and jumping"""
        # Reset movement flags
        self.moving_left = False
        self.moving_right = False
        self.is_moving = False
        
        # Horizontal movement
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.moving_left = True
            self.is_moving = True
            self.facing_right = False
            self.vel_x = -PLAYER_SPEED
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.moving_right = True
            self.is_moving = True
            self.facing_right = True
            self.vel_x = PLAYER_SPEED
        else:
            # Apply friction when not moving
            self.vel_x *= (1 - FRICTION)
            if abs(self.vel_x) < 0.1:
                self.vel_x = 0
        
        # Jumping
        if keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]:
            self.jump()
    
    def jump(self):
        """Handle jumping logic including double jump"""
        if self.on_ground or self.jump_count < self.max_jumps:
            self.vel_y = PLAYER_JUMP_SPEED
            self.on_ground = False
            if not self.on_ground:
                self.jump_count += 1
            
            # Add jump particles
            self.add_jump_particles()
    
    def add_jump_particles(self):
        """Add particle effects when jumping"""
        for i in range(5):
            particle = {
                'x': self.rect.centerx + (i - 2) * 5,
                'y': self.rect.bottom,
                'vel_x': (i - 2) * 20,
                'vel_y': -30 - i * 10,
                'life': 0.5 + i * 0.1,
                'max_life': 0.5 + i * 0.1,
                'color': self.theme['particle_color']
            }
            self.particles.append(particle)
    
    def add_landing_particles(self):
        """Add particle effects when landing"""
        for i in range(8):
            angle = (i / 8) * 360
            speed = 30 + i * 5
            vel_x = math.cos(math.radians(angle)) * speed
            vel_y = math.sin(math.radians(angle)) * speed - 20
            
            particle = {
                'x': self.rect.centerx,
                'y': self.rect.bottom,
                'vel_x': vel_x,
                'vel_y': vel_y,
                'life': 0.3 + i * 0.05,
                'max_life': 0.3 + i * 0.05,
                'color': self.theme['particle_color']
            }
            self.particles.append(particle)
    
    def update_particles(self, dt):
        """Update particle effects"""
        for particle in self.particles[:]:
            particle['life'] -= dt
            particle['x'] += particle['vel_x'] * dt
            particle['y'] += particle['vel_y'] * dt
            particle['vel_y'] += 100 * dt  # Gravity on particles
            
            if particle['life'] <= 0:
                self.particles.remove(particle)
    
    def update_animation(self, dt):
        """Update character animations"""
        self.animation_timer += dt * 5  # Animation speed
        
        # Create animated version of the sprite
        self.image = self.base_image.copy()
        
        # Apply walking animation (slight bobbing)
        if self.is_moving and self.on_ground:
            offset_y = int(math.sin(self.animation_timer) * 1)
            if offset_y != 0:
                new_image = pygame.Surface((PLAYER_WIDTH, PLAYER_HEIGHT), pygame.SRCALPHA)
                new_image.blit(self.base_image, (0, offset_y))
                self.image = new_image
        
        # Flip sprite based on direction
        if not self.facing_right:
            self.image = pygame.transform.flip(self.image, True, False)
    
    def update(self, platforms):
        """Update player position and handle physics"""
        dt = 1/60  # Assuming 60 FPS for particle effects
        
        # Store previous on_ground state for landing detection
        was_on_ground = self.on_ground
        
        # Apply gravity
        self.vel_y += PLAYER_GRAVITY
        
        # Limit falling speed
        if self.vel_y > PLAYER_MAX_FALL_SPEED:
            self.vel_y = PLAYER_MAX_FALL_SPEED
        
        # Update horizontal position
        self.rect.x += self.vel_x
        
        # Check horizontal collisions with platforms
        self.check_horizontal_collisions(platforms)
        
        # Update vertical position
        self.rect.y += self.vel_y
        
        # Check vertical collisions with platforms
        self.check_vertical_collisions(platforms)
        
        # Add landing particles if just landed
        if not was_on_ground and self.on_ground:
            self.add_landing_particles()
        
        # Keep player on screen horizontally
        if self.rect.left < 0:
            self.rect.left = 0
        elif self.rect.right > SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH
        
        # Update visual effects
        self.update_particles(dt)
        self.update_animation(dt)
    
    def check_horizontal_collisions(self, platforms):
        """Check and handle horizontal collisions with platforms"""
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                if self.vel_x > 0:  # Moving right
                    self.rect.right = platform.rect.left
                elif self.vel_x < 0:  # Moving left
                    self.rect.left = platform.rect.right
                self.vel_x = 0
    
    def check_vertical_collisions(self, platforms):
        """Check and handle vertical collisions with platforms"""
        self.on_ground = False
        
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                if self.vel_y > 0:  # Falling down
                    self.rect.bottom = platform.rect.top
                    self.vel_y = 0
                    self.on_ground = True
                    self.jump_count = 0  # Reset jump count when landing
                elif self.vel_y < 0:  # Jumping up
                    self.rect.top = platform.rect.bottom
                    self.vel_y = 0
    
    def draw(self, screen):
        """Draw the player and effects on the screen"""
        # Draw shadow
        shadow_rect = self.rect.copy()
        shadow_rect.x += self.shadow_offset
        shadow_rect.y += self.shadow_offset
        shadow_surf = pygame.Surface((shadow_rect.width, shadow_rect.height), pygame.SRCALPHA)
        shadow_surf.fill((*BLACK, 50))  # Semi-transparent black
        screen.blit(shadow_surf, shadow_rect)
        
        # Draw particles behind player
        for particle in self.particles:
            if particle['life'] > 0:
                alpha = int((particle['life'] / particle['max_life']) * 255)
                size = max(1, int((particle['life'] / particle['max_life']) * 4))
                
                particle_surf = pygame.Surface((size*2, size*2), pygame.SRCALPHA)
                color_with_alpha = (*particle['color'], alpha)
                pygame.draw.circle(particle_surf, color_with_alpha, (size, size), size)
                screen.blit(particle_surf, (int(particle['x']) - size, int(particle['y']) - size))
        
        # Draw the player
        screen.blit(self.image, self.rect)