import pygame
import math
from settings import *
from player import Player
from platforms import (Platform, Ground, MovingPlatform, DisappearingPlatform, 
                      VerticalMovingPlatform, RotatingPlatform, OneWayPlatform, 
                      BouncyPlatform, IcePlatform, TeleporterElevator)
from powerups import PowerUp

class TutorialLevel:
    def __init__(self, screen, character_config):
        self.screen = screen
        self.character_config = character_config
        self.theme = THEMES[character_config['theme']]
        
        # Tutorial state
        self.current_section = 0
        self.sections_completed = [False] * 10  # Track completion of each section
        self.tutorial_complete = False
        
        # Create sprite groups
        self.all_sprites = pygame.sprite.Group()
        self.platforms = pygame.sprite.Group()
        self.powerups = pygame.sprite.Group()
        
        # Create tutorial world
        self.create_tutorial_world()
        
        # Create player
        self.player = Player(100, WORLD_HEIGHT - 200, character_config)
        self.all_sprites.add(self.player)
        
        # UI elements
        self.font_large = pygame.font.Font(None, 36)
        self.font_medium = pygame.font.Font(None, 28)
        self.font_small = pygame.font.Font(None, 22)
        
        # Tutorial sections with explanations - UPDATED CHECKPOINTS
        self.sections = [
            {
                "title": "Welcome to the Tutorial!",
                "text": ["Use ARROW KEYS or WASD to move", "SPACEBAR to jump", "ESC to skip tutorial"],
                "checkpoint": (150, WORLD_HEIGHT - 200)  # Starting area
            },
            {
                "title": "Basic Movement",
                "text": ["Practice moving left and right", "Try jumping with SPACEBAR", "You can double-jump in the air!"],
                "checkpoint": (350, WORLD_HEIGHT - 220)  # Second platform
            },
            {
                "title": "Moving Platforms",
                "text": ["Blue platforms move back and forth", "Stand on them to ride along", "Time your jumps carefully!"],
                "checkpoint": (750, WORLD_HEIGHT - 290)  # Moving platform area
            },
            {
                "title": "Bouncy Platforms",
                "text": ["Orange platforms give you extra jump height", "Use them to reach higher areas", "Great for accessing tough spots!"],
                "checkpoint": (1200, WORLD_HEIGHT - 370)  # Bouncy platform area
            },
            {
                "title": "One-Way Platforms",
                "text": ["Yellow platforms can be jumped through from below", "But you can land on them from above", "Perfect for alternate routes!"],
                "checkpoint": (1650, WORLD_HEIGHT - 490)  # One-way area
            },
            {
                "title": "Disappearing Platforms",
                "text": ["Platforms flash red when stepped on", "They disappear after a few seconds", "Move quickly across them!"],
                "checkpoint": (1970, WORLD_HEIGHT - 570)  # Disappearing area
            },
            {
                "title": "Teleporter Elevators",
                "text": ["Green platforms move you up and down", "Stand on them to teleport along", "Much easier than regular elevators!"],
                "checkpoint": (2280, WORLD_HEIGHT - 660)  # Elevator area
            },
            {
                "title": "Ice Platforms",
                "text": ["Light blue platforms are slippery", "You slide more on ice", "Be careful with your movement!"],
                "checkpoint": (2480, WORLD_HEIGHT - 900)  # Ice area
            },
            {
                "title": "Power-ups",
                "text": ["Green crystals give jump boost", "Lasts for 10 seconds", "Great for reaching difficult areas!"],
                "checkpoint": (2830, WORLD_HEIGHT - 960)  # Power-up area
            },
            {
                "title": "Tutorial Complete!",
                "text": ["You've learned all the mechanics!", "Ready for the main adventure?", "Press ENTER to start the real game!"],
                "checkpoint": (3150, WORLD_HEIGHT - 1090)  # Final area
            }
        ]
    
    def create_tutorial_world(self):
        """Create a guided tutorial world with each mechanic introduced separately"""
        theme = self.theme
        
        # Ground platform
        ground = Ground(0, WORLD_HEIGHT - 50, WORLD_WIDTH, theme)
        self.platforms.add(ground)
        self.all_sprites.add(ground)
        
        # Section 0-1: Basic platforms for movement practice - MUCH EASIER JUMPS
        basic_platforms = [
            (50, WORLD_HEIGHT - 150, 200, 25),    # Starting platform
            (280, WORLD_HEIGHT - 180, 150, 25),   # Very close jump
            (450, WORLD_HEIGHT - 210, 120, 25),   # Very close jump
        ]
        
        for x, y, width, height in basic_platforms:
            platform = Platform(x, y, width, height, theme)
            self.platforms.add(platform)
            self.all_sprites.add(platform)
        
        # Section 2: Moving platform introduction - MUCH FASTER & EASIER REACH
        moving_platform = MovingPlatform(600, WORLD_HEIGHT - 250, 140, 25, 900, 60, theme)  # Faster speed, bigger platform, easier reach
        self.platforms.add(moving_platform)
        self.all_sprites.add(moving_platform)
        
        # Landing platform after moving platform - VERY CLOSE
        platform = Platform(950, WORLD_HEIGHT - 280, 160, 25, theme)  # Much closer and bigger
        self.platforms.add(platform)
        self.all_sprites.add(platform)
        
        # Section 3: Bouncy platform demonstration - CLOSER & EASIER
        bouncy_platform = BouncyPlatform(1130, WORLD_HEIGHT - 320, 120, 25, 1.8, theme)  # Much closer, bigger
        self.platforms.add(bouncy_platform)
        self.all_sprites.add(bouncy_platform)
        
        # High platform to reach with bouncy - MUCH EASIER HEIGHT
        platform = Platform(1300, WORLD_HEIGHT - 420, 140, 25, theme)  # Much closer, lower height
        self.platforms.add(platform)
        self.all_sprites.add(platform)
        
        # Section 4: One-way platform - EASIER POSITIONING + SUPPORTING PLATFORMS
        # First, add a platform to get TO the one-way area
        platform = Platform(1480, WORLD_HEIGHT - 450, 100, 25, theme)  # Lead-up platform
        self.platforms.add(platform)
        self.all_sprites.add(platform)
        
        # The one-way platform itself
        oneway_platform = OneWayPlatform(1600, WORLD_HEIGHT - 480, 120, 20, theme)  # Easier positioning
        self.platforms.add(oneway_platform)
        self.all_sprites.add(oneway_platform)
        
        # Platform above for demonstration - EASIER
        platform = Platform(1550, WORLD_HEIGHT - 550, 120, 25, theme)  # Above, easier reach
        self.platforms.add(platform)
        self.all_sprites.add(platform)
        
        # CRITICAL: Platform BELOW the one-way for demonstration (was missing!)
        platform = Platform(1620, WORLD_HEIGHT - 400, 100, 25, theme)  # Below the one-way
        self.platforms.add(platform)
        self.all_sprites.add(platform)
        
        # Continue path after one-way
        platform = Platform(1750, WORLD_HEIGHT - 520, 120, 25, theme)  # Continue
        self.platforms.add(platform)
        self.all_sprites.add(platform)
        
        # Section 5: Disappearing platform - MUCH EASIER
        disappearing_platform = DisappearingPlatform(1900, WORLD_HEIGHT - 560, 120, 25, theme, 8.0)  # Longer time, bigger platform
        self.platforms.add(disappearing_platform)
        self.all_sprites.add(disappearing_platform)
        
        # Safe platform to land on - MUCH CLOSER
        platform = Platform(2050, WORLD_HEIGHT - 600, 140, 25, theme)  # Much closer and bigger
        self.platforms.add(platform)
        self.all_sprites.add(platform)
        
        # Section 6: Teleporter elevator - EASIER REACH
        teleporter = TeleporterElevator(2220, WORLD_HEIGHT - 650, 120, 25, WORLD_HEIGHT - 800, 40, 2.0, theme)  # Bigger platform
        self.platforms.add(teleporter)
        self.all_sprites.add(teleporter)
        
        # Platform at elevator top - MUCH EASIER
        platform = Platform(2170, WORLD_HEIGHT - 850, 160, 25, theme)  # Bigger, easier positioning
        self.platforms.add(platform)
        self.all_sprites.add(platform)
        
        # Section 7: Ice platform - EASIER REACH AND EXIT
        ice_platform = IcePlatform(2400, WORLD_HEIGHT - 890, 160, 25, theme)  # Bigger, easier reach
        self.platforms.add(ice_platform)
        self.all_sprites.add(ice_platform)
        
        # CRITICAL: Make jump after ice MUCH easier
        platform = Platform(2600, WORLD_HEIGHT - 920, 140, 25, theme)  # Much closer and slightly higher for easier jump
        self.platforms.add(platform)
        self.all_sprites.add(platform)
        
        # Section 8: Power-up demonstration - EASIER REACH
        jump_boost = PowerUp(2780, WORLD_HEIGHT - 950, "jump_boost", theme)  # Much closer
        self.powerups.add(jump_boost)
        self.all_sprites.add(jump_boost)
        
        # High platform to reach with power-up - EASIER
        platform = Platform(2900, WORLD_HEIGHT - 1050, 140, 25, theme)  # Much closer, not as high
        self.platforms.add(platform)
        self.all_sprites.add(platform)
        
        # Final platform - EASIER REACH
        platform = Platform(3080, WORLD_HEIGHT - 1080, 220, 25, theme)  # Much closer, bigger
        self.platforms.add(platform)
        self.all_sprites.add(platform)
    
    def update_tutorial_progress(self):
        """Check if player has reached the next section"""
        if self.current_section < len(self.sections):
            checkpoint_x, checkpoint_y = self.sections[self.current_section]["checkpoint"]
            
            # Check if player reached this checkpoint
            if (self.player.rect.centerx >= checkpoint_x - 50 and 
                self.player.rect.centery <= checkpoint_y + 50):
                if not self.sections_completed[self.current_section]:
                    self.sections_completed[self.current_section] = True
                    self.current_section += 1
    
    def update(self, dt):
        """Update tutorial logic"""
        # Handle player input
        keys = pygame.key.get_pressed()
        self.player.handle_input(keys)
        
        # Update player
        self.player.update(self.platforms)
        
        # Update platforms
        for platform in self.platforms:
            platform.update(dt)
            
            # Special handling for teleporter elevator
            if hasattr(platform, 'rider') and platform.rider:
                # Check if rider is still on the platform
                if not self.player.rect.colliderect(platform.rect):
                    platform.remove_rider()  # Remove rider if no longer touching
        
        # Update power-ups
        for powerup in self.powerups:
            powerup.update(dt)
        
        # Check power-up collection
        collected_powerups = pygame.sprite.spritecollide(self.player, self.powerups, False)
        for powerup in collected_powerups:
            if not powerup.collected:
                powerup.collect()
                if powerup.powerup_type == "jump_boost":
                    self.player.add_powerup("jump_boost", 10.0)
                self.powerups.remove(powerup)
                self.all_sprites.remove(powerup)
        
        # Update tutorial progress
        self.update_tutorial_progress()
        
        # Check if tutorial is complete
        if self.current_section >= len(self.sections):
            self.tutorial_complete = True
    
    def draw_tutorial_ui(self):
        """Draw tutorial instructions and progress"""
        # Semi-transparent background for text
        ui_bg = pygame.Surface((SCREEN_WIDTH, 150), pygame.SRCALPHA)
        ui_bg.fill((0, 0, 0, 150))
        self.screen.blit(ui_bg, (0, 0))
        
        if self.current_section < len(self.sections):
            section = self.sections[self.current_section]
            
            # Section title
            title_text = self.font_large.render(section["title"], True, self.theme['glow_color'])
            title_rect = title_text.get_rect(center=(SCREEN_WIDTH//2, 30))
            self.screen.blit(title_text, title_rect)
            
            # Instructions
            y_offset = 60
            for line in section["text"]:
                text = self.font_medium.render(line, True, WHITE)
                text_rect = text.get_rect(center=(SCREEN_WIDTH//2, y_offset))
                self.screen.blit(text, text_rect)
                y_offset += 30
        
        # Progress indicator
        progress_text = f"Section {min(self.current_section + 1, len(self.sections))} of {len(self.sections)}"
        progress = self.font_small.render(progress_text, True, LIGHT_GRAY)
        self.screen.blit(progress, (20, SCREEN_HEIGHT - 40))
        
        # Skip instruction
        skip_text = self.font_small.render("Press ESC to skip tutorial", True, LIGHT_GRAY)
        self.screen.blit(skip_text, (SCREEN_WIDTH - 200, SCREEN_HEIGHT - 40))
    
    def draw_background(self):
        """Draw themed background"""
        self.screen.fill(self.theme['bg_color'])
    
    def draw(self, camera):
        """Draw the tutorial level"""
        # Draw background
        self.draw_background()
        
        # Draw all sprites with camera offset
        for sprite in self.all_sprites:
            sprite_rect = camera.apply(sprite.rect)
            self.screen.blit(sprite.image, sprite_rect)
        
        # Draw tutorial UI on top
        self.draw_tutorial_ui()
    
    def is_complete(self):
        """Check if tutorial is complete"""
        return self.tutorial_complete
    
    def should_skip(self, keys_just_pressed):
        """Check if player wants to skip tutorial"""
        return keys_just_pressed.get(pygame.K_ESCAPE, False) 