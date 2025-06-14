import pygame
import math
from settings import *

class Player(pygame.sprite.Sprite):
    def __init__(self, x, y, character_config):
        super().__init__()
        
        # Store character configuration
        self.character_config = character_config
        self.theme = THEMES[character_config['theme']]
        
        # Load base humanoid sprite
        self.base_humanoid_image = self.load_base_sprite()
        
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
        
        # Power-up system
        self.active_powerups = {}  # {effect_type: time_remaining}
        
        # Moving platform interaction
        self.on_moving_platform = None
        self.platform_velocity_x = 0
    
    def load_base_sprite(self):
        """Load and prepare the base humanoid sprite"""
        try:
            # Load the humanoid sprite
            sprite = pygame.image.load("Assets/Player.png").convert_alpha()
            
            # Scale to our player size if needed
            sprite = pygame.transform.scale(sprite, (PLAYER_WIDTH, PLAYER_HEIGHT))
            
            return sprite
        except Exception as e:
            print(f"Warning: Could not load player sprite: {e}")
            # Fallback to simple humanoid shape if image fails to load
            return self.create_fallback_humanoid()
    
    def create_fallback_humanoid(self):
        """Create a simple humanoid shape as fallback"""
        sprite = pygame.Surface((PLAYER_WIDTH, PLAYER_HEIGHT), pygame.SRCALPHA)
        
        # Head (circle)
        head_radius = PLAYER_WIDTH // 4
        pygame.draw.circle(sprite, (255, 220, 177), 
                         (PLAYER_WIDTH // 2, head_radius + 2), head_radius)
        
        # Body (rectangle)
        body_width = PLAYER_WIDTH // 2
        body_height = PLAYER_HEIGHT // 2
        pygame.draw.rect(sprite, (100, 100, 100), 
                        (PLAYER_WIDTH // 2 - body_width // 2, head_radius * 2, 
                         body_width, body_height))
        
        # Arms (rectangles)
        arm_width = 4
        arm_height = body_height // 2
        # Left arm
        pygame.draw.rect(sprite, (255, 220, 177), 
                        (PLAYER_WIDTH // 2 - body_width // 2 - arm_width, 
                         head_radius * 2 + 5, arm_width, arm_height))
        # Right arm
        pygame.draw.rect(sprite, (255, 220, 177), 
                        (PLAYER_WIDTH // 2 + body_width // 2, 
                         head_radius * 2 + 5, arm_width, arm_height))
        
        # Legs (rectangles)
        leg_width = 6
        leg_height = PLAYER_HEIGHT - (head_radius * 2 + body_height)
        # Left leg
        pygame.draw.rect(sprite, (50, 50, 200), 
                        (PLAYER_WIDTH // 2 - leg_width - 2, 
                         head_radius * 2 + body_height, leg_width, leg_height))
        # Right leg
        pygame.draw.rect(sprite, (50, 50, 200), 
                        (PLAYER_WIDTH // 2 + 2, 
                         head_radius * 2 + body_height, leg_width, leg_height))
        
        return sprite
    
    def apply_color_theme(self, sprite):
        """Apply theme-based color transformations to the sprite"""
        try:
            themed_sprite = sprite.copy()
            theme = self.theme
            
            # Get all pixels
            width, height = themed_sprite.get_size()
            
            # Color mapping based on theme
            color_mappings = {
                'crystal': {
                    'primary': theme['player_color'],    # Main body color
                    'secondary': theme['player_accent'], # Accent color
                    'skin': (150, 200, 255),            # Cool blue skin tone
                },
                'forest': {
                    'primary': theme['player_color'],    # Forest green
                    'secondary': theme['player_accent'], # Brown
                    'skin': (255, 220, 177),            # Natural skin tone
                },
                'metal': {
                    'primary': theme['player_color'],    # Silver
                    'secondary': theme['player_accent'], # Blue
                    'skin': (200, 200, 220),            # Metallic skin tone
                },
                'stone': {
                    'primary': theme['player_color'],    # Stone gray
                    'secondary': theme['player_accent'], # Orange
                    'skin': (220, 190, 150),            # Earthy skin tone
                }
            }
            
            theme_colors = color_mappings.get(self.character_config['theme'], color_mappings['crystal'])
            
            # Apply color transformations pixel by pixel
            for x in range(width):
                for y in range(height):
                    try:
                        pixel_color = themed_sprite.get_at((x, y))
                        if pixel_color[3] > 0:  # If pixel is not transparent
                            # Determine what type of pixel this is based on its original color
                            brightness = sum(pixel_color[:3]) / 3
                            
                            if brightness > 200:  # Light colors (skin, highlights)
                                new_color = theme_colors['skin']
                            elif brightness > 100:  # Medium colors (main body)
                                new_color = theme_colors['primary']
                            else:  # Dark colors (details, shadows)
                                new_color = theme_colors['secondary']
                            
                            themed_sprite.set_at((x, y), (*new_color, pixel_color[3]))
                    except Exception:
                        # Skip problematic pixels
                        continue
            
            return themed_sprite
        except Exception as e:
            print(f"Warning: Could not apply color theme: {e}")
            return sprite
    
    def apply_pattern_effect(self, sprite):
        """Apply subtle pattern effects to the themed sprite"""
        try:
            pattern = self.character_config['pattern']
            theme = self.theme
            
            if pattern == "solid":
                return sprite  # No additional pattern needed
            
            # Create a copy to modify
            patterned_sprite = sprite.copy()
            width, height = patterned_sprite.get_size()
            
            # Create subtle pattern overlay
            pattern_overlay = pygame.Surface((width, height), pygame.SRCALPHA)
            
            if pattern == "stripes":
                # Subtle horizontal stripes
                for i in range(0, height, 8):
                    pygame.draw.rect(pattern_overlay, (*theme['player_accent'], 40), 
                                   (0, i, width, 2))
            
            elif pattern == "dots":
                # Small decorative dots
                for x in range(6, width-6, 10):
                    for y in range(6, height-6, 10):
                        pygame.draw.circle(pattern_overlay, (*theme['player_accent'], 60), 
                                         (x, y), 1)
            
            elif pattern == "gradient":
                # Subtle gradient overlay
                for y in range(height):
                    alpha = int((y / height) * 30)
                    pygame.draw.line(pattern_overlay, (*theme['player_accent'], alpha), 
                                   (0, y), (width, y))
            
            # Blend the pattern overlay very subtly - remove problematic blend mode
            patterned_sprite.blit(pattern_overlay, (0, 0))
            
            return patterned_sprite
        except Exception as e:
            print(f"Warning: Could not apply pattern effect: {e}")
            return sprite
    
    def add_accessories(self, sprite):
        """Add accessories to the character sprite without covering the humanoid"""
        try:
            accessory = self.character_config['accessory']
            theme = self.theme
            
            if accessory == "none":
                return sprite
            
            # Create a copy to modify
            accessorized_sprite = sprite.copy()
            width, height = accessorized_sprite.get_size()
            
            if accessory == "cape":
                # Draw a flowing cape behind the character (more realistic)
                cape_points = [
                    (width//4 + 2, height//3),
                    (width//4 - 6, height - 2),
                    (width//4 + 10, height - 2),
                    (width//2 - 2, height//3)
                ]
                pygame.draw.polygon(accessorized_sprite, theme['player_accent'], cape_points)
                
                # Add cape highlight for depth
                highlight_points = [
                    (width//4 + 3, height//3),
                    (width//4 - 4, height - 2),
                    (width//4 + 2, height - 2)
                ]
                lighter_color = (min(255, theme['player_accent'][0] + 40),
                               min(255, theme['player_accent'][1] + 40),
                               min(255, theme['player_accent'][2] + 40))
                pygame.draw.polygon(accessorized_sprite, lighter_color, highlight_points)
                
            elif accessory == "hat":
                # Draw a hat on top without covering the face
                hat_rect = pygame.Rect(width//4, 1, width//2, 6)
                pygame.draw.rect(accessorized_sprite, theme['player_accent'], hat_rect)
                
                # Hat brim
                brim_rect = pygame.Rect(width//4 - 2, 6, width//2 + 4, 2)
                pygame.draw.rect(accessorized_sprite, theme['player_accent'], brim_rect)
                
            elif accessory == "belt":
                # Draw a belt around the waist area
                belt_y = int(height * 0.6)  # Around waist area
                belt_rect = pygame.Rect(width//6, belt_y, width - width//3, 3)
                pygame.draw.rect(accessorized_sprite, theme['player_accent'], belt_rect)
                
                # Belt buckle
                buckle_rect = pygame.Rect(width//2 - 2, belt_y, 4, 3)
                buckle_color = (min(255, theme['player_accent'][0] + 60),
                              min(255, theme['player_accent'][1] + 60),
                              min(255, theme['player_accent'][2] + 60))
                pygame.draw.rect(accessorized_sprite, buckle_color, buckle_rect)
            
            return accessorized_sprite
        except Exception as e:
            print(f"Warning: Could not add accessories: {e}")
            return sprite
    
    def create_character_sprite(self):
        """Create the complete character sprite with theme, pattern, and accessories"""
        try:
            # Start with the base humanoid sprite
            sprite = self.base_humanoid_image.copy()
            
            # Apply theme colors
            sprite = self.apply_color_theme(sprite)
            
            # Apply subtle pattern effects
            sprite = self.apply_pattern_effect(sprite)
            
            # Add accessories without covering the character
            sprite = self.add_accessories(sprite)
            
            return sprite
        except Exception as e:
            print(f"Warning: Could not create character sprite: {e}")
            # Return a basic fallback sprite
            return self.create_fallback_humanoid()
    
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
        """Handle jumping logic including double jump and power-ups"""
        if self.on_ground or self.jump_count < self.max_jumps:
            # Calculate jump strength (enhanced by power-ups)
            jump_strength = PLAYER_JUMP_SPEED
            if self.has_powerup("jump_boost"):
                jump_strength *= 1.5  # 50% higher jumps
            
            self.vel_y = jump_strength
            self.on_ground = False
            if not self.on_ground:
                self.jump_count += 1
            
            # Add jump particles (enhanced for power-ups)
            self.add_jump_particles()
    
    def add_jump_particles(self):
        """Add particle effects when jumping"""
        # Enhanced particles for jump boost
        particle_count = 8 if self.has_powerup("jump_boost") else 5
        particle_color = (100, 255, 100) if self.has_powerup("jump_boost") else self.theme['particle_color']
        
        for i in range(particle_count):
            particle = {
                'x': self.rect.centerx + (i - particle_count//2) * 5,
                'y': self.rect.bottom,
                'vel_x': (i - particle_count//2) * 20,
                'vel_y': -30 - i * 10,
                'life': 0.5 + i * 0.1,
                'max_life': 0.5 + i * 0.1,
                'color': particle_color
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
            offset_y = int(math.sin(self.animation_timer) * 2)
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
        
        # Update power-ups
        self.update_powerups(dt)
        
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
        
        # Check vertical collisions with platforms (including moving platforms)
        self.check_vertical_collisions(platforms)
        
        # Handle moving platform interaction
        if self.on_moving_platform:
            # Move with the platform (horizontal)
            if hasattr(self.on_moving_platform, 'get_movement_delta'):
                platform_delta = self.on_moving_platform.get_movement_delta()
                self.rect.x += platform_delta
            
            # Move with the platform (vertical)
            if hasattr(self.on_moving_platform, 'get_movement_delta_y'):
                platform_delta_y = self.on_moving_platform.get_movement_delta_y()
                self.rect.y += platform_delta_y
        
        # Apply ice friction if on ice platform, otherwise normal friction
        if not self.apply_ice_friction(platforms):
            # Apply normal friction when not moving
            if not (self.moving_left or self.moving_right):
                self.vel_x *= (1 - FRICTION)
                if abs(self.vel_x) < 0.1:
                    self.vel_x = 0
        
        # Add landing particles if just landed
        if not was_on_ground and self.on_ground:
            self.add_landing_particles()
        
        # Keep player within world bounds (not just screen bounds!)
        if self.rect.left < 0:
            self.rect.left = 0
        elif self.rect.right > WORLD_WIDTH:
            self.rect.right = WORLD_WIDTH
        
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
        """Check and handle vertical collisions with platforms (including special platform types)"""
        self.on_ground = False
        self.on_moving_platform = None
        
        for platform in platforms:
            # Skip non-solid platforms (like disappeared platforms)
            if hasattr(platform, 'is_solid') and not platform.is_solid:
                continue
            
            # Special handling for one-way platforms
            if hasattr(platform, 'one_way') and platform.one_way:
                # Only collide if falling down and player is above the platform
                if self.vel_y > 0 and self.rect.bottom <= platform.rect.top + 10:
                    if self.rect.colliderect(platform.rect):
                        self.rect.bottom = platform.rect.top
                        self.vel_y = 0
                        self.on_ground = True
                        self.jump_count = 0
                continue
                
            if self.rect.colliderect(platform.rect):
                if self.vel_y > 0:  # Falling down
                    self.rect.bottom = platform.rect.top
                    self.vel_y = 0
                    self.on_ground = True
                    self.jump_count = 0  # Reset jump count when landing
                    
                    # Handle special platform effects
                    if hasattr(platform, 'bounce_strength'):  # Bouncy platform
                        self.vel_y = PLAYER_JUMP_SPEED * platform.bounce_strength
                        self.on_ground = False
                        platform.trigger_bounce()  # Trigger bounce animation
                        self.add_bounce_particles()
                    
                    # Check if this is a moving platform
                    if hasattr(platform, 'get_movement_delta'):
                        self.on_moving_platform = platform
                    
                    # Check if this is a teleporter elevator
                    if hasattr(platform, 'set_rider'):
                        platform.set_rider(self)  # Register as rider for teleporter
                        self.on_moving_platform = platform  # Also treat as moving platform
                    
                    # Activate disappearing platforms
                    if hasattr(platform, 'activate'):
                        platform.activate()
                        
                elif self.vel_y < 0:  # Jumping up
                    self.rect.top = platform.rect.bottom
                    self.vel_y = 0
    
    def add_bounce_particles(self):
        """Add special particle effects for bouncy platforms"""
        for i in range(12):
            angle = (i / 12) * 360
            speed = 40 + i * 3
            vel_x = math.cos(math.radians(angle)) * speed
            vel_y = math.sin(math.radians(angle)) * speed - 40
            
            particle = {
                'x': self.rect.centerx,
                'y': self.rect.bottom,
                'vel_x': vel_x,
                'vel_y': vel_y,
                'life': 0.6 + i * 0.03,
                'max_life': 0.6 + i * 0.03,
                'color': (255, 150, 0)  # Orange bounce particles
            }
            self.particles.append(particle)
    
    def apply_ice_friction(self, platforms):
        """Apply special ice friction when on ice platforms"""
        if self.on_ground:
            for platform in platforms:
                if (hasattr(platform, 'ice_friction') and 
                    self.rect.colliderect(platform.rect) and 
                    self.rect.bottom <= platform.rect.top + 5):
                    # Apply ice friction instead of normal friction
                    self.vel_x *= (1 - platform.ice_friction)
                    return True
        return False
    
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
    
    def add_powerup(self, powerup_type, duration):
        """Add a power-up effect"""
        self.active_powerups[powerup_type] = duration
    
    def has_powerup(self, powerup_type):
        """Check if player has an active power-up"""
        return powerup_type in self.active_powerups
    
    def update_powerups(self, dt):
        """Update power-up timers"""
        expired = []
        for powerup_type, time_left in self.active_powerups.items():
            self.active_powerups[powerup_type] = time_left - dt
            if self.active_powerups[powerup_type] <= 0:
                expired.append(powerup_type)
        
        for powerup_type in expired:
            del self.active_powerups[powerup_type]