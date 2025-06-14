import pygame
import math
from settings import *

class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, theme=None):
        super().__init__()
        
        # Load platform image - RESTORED FOR RAINBOW EFFECT
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
            
            # Apply theme coloring to the platform image (can be overridden by subclasses)
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
        
        # Create a MUCH more subtle color overlay to preserve special indicators
        color_overlay = pygame.Surface((width, height), pygame.SRCALPHA)
        
        # Add subtle gradient effects based on theme - REDUCED TO PRESERVE RAINBOW COLORS
        for y in range(height):
            alpha = int(5 + (y / height) * 10)  # MUCH lighter: 5 to 15 alpha to let rainbow show through
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
    """Special platform class for themed animated death zones"""
    def __init__(self, x, y, width, theme=None):
        # Identify theme and set up animation properties
        if theme:
            self.theme_name = None
            # Identify theme by ground colors to determine animation type
            if theme['ground_color'] == (101, 84, 67):  # Ancient/Stone theme
                self.theme_name = "ancient"
            elif theme['ground_color'] == (101, 67, 33):  # Forest theme  
                self.theme_name = "forest"
            elif theme['ground_color'] == (60, 90, 140):  # Crystal theme
                self.theme_name = "crystal" 
            elif theme['ground_color'] == DARK_GRAY:  # Metal/Cyber theme
                self.theme_name = "cyber"
            else:
                self.theme_name = "default"
        else:
            self.theme_name = "default"
            
        super().__init__(x, y, width, GROUND_HEIGHT, theme)
        
        # Animation properties
        self.animation_timer = 0.0
        
        # Create the themed death zone
        self.create_themed_ground()
    
    def create_themed_ground(self):
        """Create animated themed death zone based on theme"""
        width = self.rect.width
        height = self.rect.height
        
        # Create base surface
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        
        if self.theme_name == "ancient":
            self.create_lava_ground(width, height)
        elif self.theme_name == "forest":
            self.create_poison_ground(width, height)
        elif self.theme_name == "crystal":
            self.create_crystal_ground(width, height)
        elif self.theme_name == "cyber":
            self.create_cyber_ground(width, height)
        else:
            # Default ground
            self.image.fill(DARK_GRAY)
    
    def create_lava_ground(self, width, height):
        """Create bubbling lava ground for ancient theme"""
        # Base lava color
        self.image.fill((120, 30, 0))
        
        # Add lava bubbles that change with animation
        bubble_offset = int(self.animation_timer * 50) % 100
        for i in range(0, width, 60):
            bubble_x = i + 30 + (bubble_offset % 20) - 10
            bubble_y = 20 + int(10 * math.sin(self.animation_timer * 3 + i * 0.1))
            
            # Lava bubble
            pygame.draw.circle(self.image, (200, 80, 0), (bubble_x, bubble_y), 8)
            pygame.draw.circle(self.image, (255, 120, 20), (bubble_x, bubble_y), 5)
            
        # Flowing lava streams
        for i in range(0, width, 40):
            stream_y = int(5 * math.sin(self.animation_timer * 2 + i * 0.05))
            pygame.draw.rect(self.image, (180, 60, 0), (i, 40 + stream_y, 30, 15))
            
        # Hot glow at top
        glow_alpha = int(100 + 50 * math.sin(self.animation_timer * 4))
        glow_surface = pygame.Surface((width, 20), pygame.SRCALPHA)
        glow_surface.fill((255, 100, 0, glow_alpha))
        self.image.blit(glow_surface, (0, 0))
    
    def create_poison_ground(self, width, height):
        """Create swirling poison ground for forest theme"""
        # Base poison color
        self.image.fill((60, 80, 30))
        
        # Swirling poison patterns
        for i in range(0, width, 50):
            swirl_offset = self.animation_timer * 100 + i * 0.3
            center_x = i + 25
            
            # Create spiral pattern
            for angle in range(0, 360, 30):
                radius = 15 + 10 * math.sin(swirl_offset * 0.02)
                x = center_x + radius * math.cos(math.radians(angle + swirl_offset))
                y = 30 + radius * math.sin(math.radians(angle + swirl_offset)) * 0.5
                
                if 0 <= x < width and 0 <= y < height:
                    pygame.draw.circle(self.image, (120, 180, 60), (int(x), int(y)), 3)
        
        # Poison bubbles rising
        for i in range(0, width, 80):
            bubble_y = (height - 20) - (self.animation_timer * 20 + i * 2) % height
            pygame.draw.circle(self.image, (100, 200, 80), (i + 40, int(bubble_y)), 4)
            
        # Toxic glow
        toxic_alpha = int(80 + 40 * math.sin(self.animation_timer * 3))
        toxic_surface = pygame.Surface((width, height), pygame.SRCALPHA)
        toxic_surface.fill((80, 255, 100, toxic_alpha))
        self.image.blit(toxic_surface, (0, 0))
    
    def create_crystal_ground(self, width, height):
        """Create sharp crystal spikes for crystal theme"""
        # Base crystal floor
        self.image.fill((50, 100, 150))
        
        # Sharp crystal spikes
        for i in range(0, width, 40):
            spike_height = 30 + int(15 * math.sin(self.animation_timer * 2 + i * 0.1))
            spike_x = i + 20
            
            # Crystal spike points
            crystal_points = [
                (spike_x, height),
                (spike_x - 8, height - spike_height // 2),
                (spike_x, height - spike_height),
                (spike_x + 8, height - spike_height // 2)
            ]
            
            # Draw crystal spike with gradient
            pygame.draw.polygon(self.image, (150, 200, 255), crystal_points)
            pygame.draw.polygon(self.image, (200, 230, 255), [
                (spike_x, height),
                (spike_x - 4, height - spike_height // 2),
                (spike_x, height - spike_height)
            ])
        
        # Crystal glow effect
        glow_intensity = int(60 + 30 * math.sin(self.animation_timer * 4))
        for i in range(0, width, 40):
            glow_x = i + 20
            glow_surface = pygame.Surface((30, 40), pygame.SRCALPHA)
            pygame.draw.circle(glow_surface, (100, 200, 255, glow_intensity), (15, 35), 15)
            self.image.blit(glow_surface, (glow_x - 15, height - 40))
    
    def create_cyber_ground(self, width, height):
        """Create nano bot swarm with lasers for cyber theme"""
        # Base metallic floor
        self.image.fill((80, 80, 100))
        
        # Nano bot swarm
        bot_offset = self.animation_timer * 150
        for i in range(0, width, 30):
            for j in range(0, height, 25):
                bot_x = i + (bot_offset + i * j) % 60 - 30
                bot_y = j + int(5 * math.sin(self.animation_timer * 3 + i * 0.2))
                
                if 0 <= bot_x < width:
                    # Nano bot (small rectangle)
                    pygame.draw.rect(self.image, (150, 150, 180), (int(bot_x), bot_y, 4, 4))
                    # Bot glow
                    pygame.draw.rect(self.image, (200, 200, 255), (int(bot_x) + 1, bot_y + 1, 2, 2))
        
        # Horizontal scanning lasers
        laser_y = int(height / 2 + 20 * math.sin(self.animation_timer * 2))
        laser_alpha = int(150 + 100 * math.sin(self.animation_timer * 6))
        
        # Main laser beam
        laser_surface = pygame.Surface((width, 6), pygame.SRCALPHA)
        laser_surface.fill((255, 100, 100, laser_alpha))
        self.image.blit(laser_surface, (0, laser_y))
        
        # Laser glow
        glow_surface = pygame.Surface((width, 12), pygame.SRCALPHA)
        glow_surface.fill((255, 150, 150, laser_alpha // 3))
        self.image.blit(glow_surface, (0, laser_y - 3))
        
        # Grid pattern overlay
        grid_alpha = int(40 + 20 * math.sin(self.animation_timer * 1.5))
        for i in range(0, width, 20):
            pygame.draw.line(self.image, (120, 120, 150, grid_alpha), (i, 0), (i, height))
        for j in range(0, height, 15):
            pygame.draw.line(self.image, (120, 120, 150, grid_alpha), (0, j), (width, j))
    
    def update(self, dt):
        """Update animation"""
        self.animation_timer += dt
        
        # Recreate the animated ground
        self.create_themed_ground()

class VerticalMovingPlatform(Platform):
    """Vertical moving platform (elevator-style)"""
    def __init__(self, x, start_y, width, height, end_y, speed=40, wait_time=2.0, theme=None):
        super().__init__(x, start_y, width, height, theme)
        
        # Movement properties
        self.start_y = start_y
        self.end_y = end_y
        self.speed = speed  # pixels per second
        self.direction = 1 if end_y > start_y else -1  # 1 for down, -1 for up
        self.wait_time = wait_time  # Time to wait at each end
        self.current_wait = 0.0
        self.is_waiting = False
        self.last_y = self.rect.y
        
        # Add visual indicator (green border for vertical)
        self.add_movement_indicator()
    
    def add_movement_indicator(self):
        """Add a green visual indicator to show this platform moves vertically"""
        border_color = (0, 255, 150)  # Bright green
        pygame.draw.rect(self.image, border_color, self.image.get_rect(), 3)
        
        # Add green up/down arrows
        center_x = self.rect.width // 2
        # Up arrow
        pygame.draw.polygon(self.image, border_color, [
            (center_x, 2), (center_x - 4, 8), (center_x + 4, 8)
        ])
        # Down arrow
        pygame.draw.polygon(self.image, border_color, [
            (center_x, self.rect.height - 2), (center_x - 4, self.rect.height - 8), (center_x + 4, self.rect.height - 8)
        ])
    
    def update(self, dt):
        """Update vertical platform movement"""
        self.last_y = self.rect.y
        
        if self.is_waiting:
            self.current_wait += dt
            if self.current_wait >= self.wait_time:
                self.is_waiting = False
                self.current_wait = 0.0
                self.direction *= -1  # Reverse direction
        else:
            # Move platform
            self.rect.y += self.direction * self.speed * dt
            
            # Check bounds and start waiting
            if self.direction > 0 and self.rect.y >= self.end_y:  # Moving down, hit bottom
                self.rect.y = self.end_y
                self.is_waiting = True
            elif self.direction < 0 and self.rect.y <= self.start_y:  # Moving up, hit top
                self.rect.y = self.start_y
                self.is_waiting = True
    
    def get_movement_delta_y(self):
        """Get how much the platform moved vertically this frame"""
        return self.rect.y - self.last_y

class RotatingPlatform(Platform):
    """Small circular platform that rotates slowly"""
    def __init__(self, x, y, radius=30, rotation_speed=45, theme=None):
        # Create a square surface to contain the circle
        size = radius * 2 + 10
        super().__init__(x - size//2, y - size//2, size, size, theme)
        
        self.radius = radius
        self.rotation_speed = rotation_speed  # degrees per second
        self.angle = 0.0
        self.center_x = x
        self.center_y = y
        
        # Create the rotating platform visual
        self.create_rotating_visual()
    
    def create_rotating_visual(self):
        """Create the circular rotating platform"""
        # Create a fresh transparent surface every time
        self.image = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        self.image.fill((0, 0, 0, 0))  # Transparent
        
        # Draw the circular platform
        center = (self.rect.width // 2, self.rect.height // 2)
        
        # Main circle
        pygame.draw.circle(self.image, (150, 100, 200), center, self.radius)
        
        # Rotating indicator line (so you can see it rotate) - MAKE IT MORE VISIBLE
        line_end_x = center[0] + self.radius * 0.8 * math.cos(math.radians(self.angle))
        line_end_y = center[1] + self.radius * 0.8 * math.sin(math.radians(self.angle))
        pygame.draw.line(self.image, (255, 255, 255), center, (int(line_end_x), int(line_end_y)), 4)
        
        # Add a rotating dot at the end of the line for even better visibility
        pygame.draw.circle(self.image, (255, 255, 0), (int(line_end_x), int(line_end_y)), 4)
        
        # Border
        pygame.draw.circle(self.image, (255, 100, 255), center, self.radius, 3)
    
    def update(self, dt):
        """Update rotation"""
        self.angle += self.rotation_speed * dt
        if self.angle >= 360:
            self.angle -= 360
        
        # Recreate the visual with new rotation
        self.create_rotating_visual()

class OneWayPlatform(Platform):
    """Platform you can jump through from below but land on from above"""
    def __init__(self, x, y, width, height, theme=None):
        super().__init__(x, y, width, height, theme)
        self.one_way = True  # Flag for special collision handling
        
        # Add visual indicator (yellow border with up arrows)
        self.add_movement_indicator()
    
    def add_movement_indicator(self):
        """Add visual indicator for one-way platform"""
        border_color = (255, 255, 0)  # Yellow
        pygame.draw.rect(self.image, border_color, self.image.get_rect(), 2)
        
        # Add up arrows to show you can only land from above
        for i in range(3):
            x = (i + 1) * self.rect.width // 4
            pygame.draw.polygon(self.image, border_color, [
                (x, 2), (x - 3, 8), (x + 3, 8)
            ])

class BouncyPlatform(Platform):
    """Platform that gives extra jump height when landed on"""
    def __init__(self, x, y, width, height, bounce_strength=1.5, theme=None):
        super().__init__(x, y, width, height, theme)
        self.bounce_strength = bounce_strength  # Multiplier for jump height
        self.bounce_animation_timer = 0.0
        
        # Add visual indicator (orange with bounce effect)
        self.add_movement_indicator()
    
    def add_movement_indicator(self):
        """Add visual indicator for bouncy platform"""
        border_color = (255, 80, 0)  # Even brighter orange
        
        # Fill entire platform with orange tint first
        orange_overlay = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        orange_overlay.fill((*border_color, 80))  # Orange tint over whole platform
        self.image.blit(orange_overlay, (0, 0))
        
        # Then add thick border
        pygame.draw.rect(self.image, border_color, self.image.get_rect(), 8)  # Much thicker border
        
        # Add spring coils visual - much more prominent
        for i in range(0, self.rect.width, 12):  # Even more frequent coils
            # Draw spring coil pattern
            pygame.draw.circle(self.image, border_color, (i + 6, self.rect.height // 2), 6, 4)
            # Add bouncy dots above and below
            pygame.draw.circle(self.image, border_color, (i + 6, 3), 3)
            pygame.draw.circle(self.image, border_color, (i + 6, self.rect.height - 3), 3)
    
    def update(self, dt):
        """Update bounce animation"""
        self.bounce_animation_timer += dt * 8
        
        # Create a subtle bouncing visual effect
        if self.bounce_animation_timer < 3.14:  # One bounce cycle
            bounce_offset = int(math.sin(self.bounce_animation_timer) * 2)
            if bounce_offset != 0:
                # Recreate image with bounce offset
                original_image = super().image if hasattr(super(), 'image') else self.image
                self.image = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
                self.image.blit(original_image, (0, bounce_offset))
        
        if self.bounce_animation_timer > 6.28:  # Reset after full cycle
            self.bounce_animation_timer = 0.0
    
    def trigger_bounce(self):
        """Trigger the bounce animation"""
        self.bounce_animation_timer = 0.0

class IcePlatform(Platform):
    """Slippery platform with reduced friction"""
    def __init__(self, x, y, width, height, theme=None):
        super().__init__(x, y, width, height, theme)
        self.ice_friction = 0.02  # Much lower friction than normal
        
        # Add visual indicator (light blue with ice crystals)
        self.add_movement_indicator()
    
    def add_movement_indicator(self):
        """Add visual indicator for ice platform"""
        ice_color = (150, 200, 255)  # Light blue
        pygame.draw.rect(self.image, ice_color, self.image.get_rect(), 2)
        
        # Add ice crystal decorations
        for i in range(0, self.rect.width, 25):
            # Draw simple ice crystal shapes
            x = i + 12
            y = self.rect.height // 2
            crystal_points = [
                (x, y - 4), (x - 3, y), (x, y + 4), (x + 3, y)
            ]
            pygame.draw.polygon(self.image, ice_color, crystal_points)
            
        # Add icy overlay effect
        ice_overlay = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        ice_overlay.fill((*ice_color, 30))  # Semi-transparent ice
        self.image.blit(ice_overlay, (0, 0))

class TeleporterElevator(Platform):
    """Tutorial-friendly elevator that teleports player along with platform"""
    def __init__(self, x, start_y, width, height, end_y, speed=40, wait_time=2.0, theme=None):
        super().__init__(x, start_y, width, height, theme)
        
        # Movement properties
        self.start_y = start_y
        self.end_y = end_y
        self.speed = speed  # pixels per second
        self.direction = 1 if end_y > start_y else -1  # 1 for down, -1 for up
        self.wait_time = wait_time  # Time to wait at each end
        self.current_wait = 0.0
        self.is_waiting = False
        self.last_y = self.rect.y
        
        # Player riding system
        self.rider = None  # Will store reference to player on platform
        
        # Add visual indicator (bright green border for teleporter)
        self.add_movement_indicator()
    
    def add_movement_indicator(self):
        """Add a bright green visual indicator to show this is a teleporter elevator"""
        border_color = (50, 255, 50)  # Bright green
        pygame.draw.rect(self.image, border_color, self.image.get_rect(), 4)
        
        # Add teleporter symbols (up/down arrows with dots)
        center_x = self.rect.width // 2
        # Up arrow with dots
        pygame.draw.polygon(self.image, border_color, [
            (center_x, 3), (center_x - 5, 10), (center_x + 5, 10)
        ])
        # Teleporter dots
        for i in range(3):
            pygame.draw.circle(self.image, border_color, (center_x - 6 + i * 6, 15), 2)
        
        # Down arrow with dots
        pygame.draw.polygon(self.image, border_color, [
            (center_x, self.rect.height - 3), (center_x - 5, self.rect.height - 10), (center_x + 5, self.rect.height - 10)
        ])
        # More teleporter dots
        for i in range(3):
            pygame.draw.circle(self.image, border_color, (center_x - 6 + i * 6, self.rect.height - 18), 2)
    
    def update(self, dt):
        """Update teleporter elevator movement"""
        self.last_y = self.rect.y
        
        if self.is_waiting:
            self.current_wait += dt
            if self.current_wait >= self.wait_time:
                self.is_waiting = False
                self.current_wait = 0.0
                self.direction *= -1  # Reverse direction
        else:
            # Move platform
            old_y = self.rect.y
            self.rect.y += self.direction * self.speed * dt
            movement_delta = self.rect.y - old_y
            
            # Move any rider along with the platform (TELEPORTER STYLE!)
            if self.rider:
                self.rider.rect.y += movement_delta
            
            # Check bounds and start waiting
            if self.direction > 0 and self.rect.y >= self.end_y:  # Moving down, hit bottom
                self.rect.y = self.end_y
                if self.rider:
                    self.rider.rect.y += (self.end_y - old_y - movement_delta)  # Adjust rider position
                self.is_waiting = True
            elif self.direction < 0 and self.rect.y <= self.start_y:  # Moving up, hit top
                self.rect.y = self.start_y
                if self.rider:
                    self.rider.rect.y += (self.start_y - old_y - movement_delta)  # Adjust rider position
                self.is_waiting = True
    
    def set_rider(self, player):
        """Set the player as riding this elevator"""
        self.rider = player
    
    def remove_rider(self):
        """Remove the player from riding this elevator"""
        self.rider = None
    
    def get_movement_delta_y(self):
        """Get how much the platform moved vertically this frame"""
        return self.rect.y - self.last_y