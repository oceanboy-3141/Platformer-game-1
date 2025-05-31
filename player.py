import pygame
from settings import *

class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        
        # Create player surface and rect
        self.image = pygame.Surface((PLAYER_WIDTH, PLAYER_HEIGHT))
        self.image.fill(PLAYER_COLOR)
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
    
    def handle_input(self, keys):
        """Handle player input for movement and jumping"""
        # Reset movement flags
        self.moving_left = False
        self.moving_right = False
        
        # Horizontal movement
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.moving_left = True
            self.vel_x = -PLAYER_SPEED
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.moving_right = True
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
    
    def update(self, platforms):
        """Update player position and handle physics"""
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
        
        # Keep player on screen horizontally
        if self.rect.left < 0:
            self.rect.left = 0
        elif self.rect.right > SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH
    
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
        """Draw the player on the screen"""
        screen.blit(self.image, self.rect) 