import pygame
import sys
from settings import *
from player import Player
from platforms import Platform, Ground, MovingPlatform, DisappearingPlatform
from powerups import PowerUp
from character_select import CharacterSelectScreen

class Camera:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.target_x = 0
        self.target_y = 0
    
    def update(self, target_rect):
        """Update camera position to follow target with smoothing"""
        # Calculate target camera position (center target on screen)
        self.target_x = target_rect.centerx - SCREEN_WIDTH // 2
        self.target_y = target_rect.centery - SCREEN_HEIGHT // 2
        
        # Apply camera bounds (don't go outside world)
        self.target_x = max(0, min(self.target_x, WORLD_WIDTH - SCREEN_WIDTH))
        self.target_y = max(0, min(self.target_y, WORLD_HEIGHT - SCREEN_HEIGHT))
        
        # Smooth camera movement
        self.x += (self.target_x - self.x) * CAMERA_SMOOTHING
        self.y += (self.target_y - self.y) * CAMERA_SMOOTHING
    
    def apply(self, rect):
        """Apply camera offset to a rect for drawing"""
        return pygame.Rect(rect.x - self.x, rect.y - self.y, rect.width, rect.height)
    
    def apply_pos(self, x, y):
        """Apply camera offset to a position"""
        return (x - self.x, y - self.y)

class Game:
    def __init__(self):
        # Initialize Pygame
        pygame.init()
        
        # Set up the display
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Pygame Platformer - Character Selection")
        
        # Set up the clock for consistent framerate
        self.clock = pygame.time.Clock()
        
        # Load background image
        self.load_background()
        
        # Game state management
        self.state = GAME_STATE_CHARACTER_SELECT
        self.character_config = None
        
        # Initialize character selection screen
        self.character_select = CharacterSelectScreen(self.screen)
        
        # Track key states for proper input handling
        self.keys_pressed = pygame.key.get_pressed()
        self.previous_keys = pygame.key.get_pressed()
        
        # Game objects (initialized after character selection)
        self.all_sprites = None
        self.platforms = None
        self.player = None
        
        # Game state
        self.running = True
        
        # Initialize camera
        self.camera = Camera()
    
    def load_background(self):
        """Load and prepare the background image"""
        # We'll load theme-specific backgrounds later when theme is selected
        self.background_images = {}
        
        # Background file mapping for each theme
        background_files = {
            'crystal': 'Back round Crystal.png',
            'forest': 'Background forest gardioun.png', 
            'metal': 'Background Cyber runner.png',
            'stone': 'Background anchiant explorer.png'
        }
        
        # Load all theme backgrounds
        for theme_name, filename in background_files.items():
            try:
                bg_image = pygame.image.load(f"Assets/{filename}").convert()
                # Scale background to fit screen
                bg_image = pygame.transform.scale(bg_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
                self.background_images[theme_name] = bg_image
                print(f"Loaded background for {theme_name}: {filename}")
            except Exception as e:
                print(f"Warning: Could not load background for {theme_name}: {e}")
                self.background_images[theme_name] = None
    
    def init_game_world(self):
        """Initialize the game world after character selection"""
        # Create sprite groups
        self.all_sprites = pygame.sprite.Group()
        self.platforms = pygame.sprite.Group()
        self.powerups = pygame.sprite.Group()
        
        # Create larger level with platforms leading to top-right
        self.create_large_level()
        
        # Create player on the first safe platform (not near deadly ground!)
        start_x = 200  # On the first platform at (150, WORLD_HEIGHT - 180, 250, 25)
        start_y = WORLD_HEIGHT - 180 - PLAYER_HEIGHT - 5  # Just above first platform
        self.player = Player(start_x, start_y, self.character_config)
        self.all_sprites.add(self.player)
        
        # Initialize camera to follow player
        self.camera.update(self.player.rect)
    
    def create_large_level(self):
        """Create a large level with multiple paths and easier jumps"""
        theme = THEMES[self.character_config['theme']]
        
        # Ground platform spans the entire bottom (this is deadly!)
        ground = Ground(0, WORLD_HEIGHT - GROUND_HEIGHT, WORLD_WIDTH, theme)
        self.platforms.add(ground)
        self.all_sprites.add(ground)
        
        # Create multiple paths with easier jumps (max 120 pixel gaps, 80-100 pixel height differences)
        platforms_data = [
            # Starting area - multiple ways up
            (150, WORLD_HEIGHT - 180, 250, 25),   # First safe platform
            (500, WORLD_HEIGHT - 180, 200, 25),   # Alternative first platform
            
            # Path A (Left route - easier)
            (200, WORLD_HEIGHT - 280, 180, 25),   # Small jump up
            (450, WORLD_HEIGHT - 380, 200, 25),   # Manageable gap
            (750, WORLD_HEIGHT - 480, 150, 25),   # Continue up
            (1000, WORLD_HEIGHT - 580, 180, 25),  # Path A continues
            
            # Path B (Right route - medium difficulty)
            (700, WORLD_HEIGHT - 300, 160, 25),   # Alternative route
            (950, WORLD_HEIGHT - 420, 140, 25),   # Slightly harder jumps
            (1200, WORLD_HEIGHT - 540, 160, 25),  # Path B continues
            (1500, WORLD_HEIGHT - 660, 150, 25),  # Keep going up
            
            # Convergence point - paths meet
            (1250, WORLD_HEIGHT - 780, 250, 25),  # Big platform where paths meet
            
            # Mid-section - choose your difficulty again
            # Easy path (left)
            (1100, WORLD_HEIGHT - 900, 180, 25),
            (1350, WORLD_HEIGHT - 1020, 160, 25),
            (1600, WORLD_HEIGHT - 1140, 170, 25),
            (1900, WORLD_HEIGHT - 1260, 160, 25),
            
            # Medium path (middle)
            (1550, WORLD_HEIGHT - 950, 140, 25),
            (1800, WORLD_HEIGHT - 1080, 130, 25),
            (2100, WORLD_HEIGHT - 1210, 140, 25),
            (2400, WORLD_HEIGHT - 1340, 150, 25),
            
            # Hard path (right) - for advanced players
            (1750, WORLD_HEIGHT - 900, 120, 25),
            (2000, WORLD_HEIGHT - 1050, 110, 25),
            (2300, WORLD_HEIGHT - 1200, 120, 25),
            (2600, WORLD_HEIGHT - 1350, 130, 25),
            
            # Upper convergence
            (2200, WORLD_HEIGHT - 1500, 300, 25),  # Another meeting point
            
            # Some moving/interesting platforms
            (2600, WORLD_HEIGHT - 1650, 150, 25),
            (2950, WORLD_HEIGHT - 1800, 140, 25),
            (3300, WORLD_HEIGHT - 1950, 160, 25),
            
            # Final approaches - multiple ways to victory
            (3600, WORLD_HEIGHT - 2100, 180, 25),
            (3950, WORLD_HEIGHT - 2250, 170, 25),
            (4300, WORLD_HEIGHT - 2400, 160, 25),
            (4650, WORLD_HEIGHT - 2550, 150, 25),
            
            # Near victory - branching final paths
            (5000, WORLD_HEIGHT - 2700, 200, 25),  # Safe route
            (5350, WORLD_HEIGHT - 2850, 180, 25),  # Medium route
            (5700, WORLD_HEIGHT - 3000, 160, 25),  # Harder route
            
            # Final platforms
            (6000, WORLD_HEIGHT - 3150, 250, 25),  # Pre-victory platform
            (6400, WORLD_HEIGHT - 3300, 300, 30),  # Victory platform (bigger!)
        ]
        
        # Create all platforms
        for x, y, width, height in platforms_data:
            platform = Platform(x, y, width, height, theme)
            self.platforms.add(platform)
            self.all_sprites.add(platform)
        
        # Add some "checkpoint" platforms (extra wide for safety)
        checkpoint_platforms = [
            (1250, WORLD_HEIGHT - 780, 250, 25),   # First checkpoint
            (2200, WORLD_HEIGHT - 1500, 300, 25),  # Second checkpoint
            (4000, WORLD_HEIGHT - 2400, 280, 25),  # Third checkpoint
        ]
        
        for x, y, width, height in checkpoint_platforms:
            checkpoint = Platform(x, y, width, height, theme)
            self.platforms.add(checkpoint)
            self.all_sprites.add(checkpoint)
        
        # Create victory zone at top-right (bigger and more forgiving)
        self.victory_zone = pygame.Rect(6350, WORLD_HEIGHT - 3400, 400, 150)
        
        # Add PHASE 3: Moving Platforms (Horizontal)
        moving_platforms_data = [
            # VERY early test platform - should be visible right away
            (300, WORLD_HEIGHT - 300, 100, 25, 450, 200),   # Super fast for testing
            
            # Another early platform that goes across the starting area
            (100, WORLD_HEIGHT - 250, 80, 25, 350, 300),    # Even faster for testing
            
            # Start area moving platform
            (800, WORLD_HEIGHT - 350, 120, 25, 1000, 250),  # Fast for testing
            
            # Mid-section moving bridges
            (1700, WORLD_HEIGHT - 800, 100, 25, 1900, 30),
            (2800, WORLD_HEIGHT - 1100, 120, 25, 3100, 35),
            (3500, WORLD_HEIGHT - 1700, 100, 25, 3800, 25),
            
            # Upper area challenging moving platforms
            (4800, WORLD_HEIGHT - 2200, 90, 25, 5100, 50),  # Faster one
            (5500, WORLD_HEIGHT - 2800, 110, 25, 5900, 30),
        ]
        
        for start_x, y, width, height, end_x, speed in moving_platforms_data:
            moving_platform = MovingPlatform(start_x, y, width, height, end_x, speed, theme)
            self.platforms.add(moving_platform)
            self.all_sprites.add(moving_platform)
        
        # Add PHASE 3: Disappearing Platforms (creates timing challenges)
        disappearing_platforms_data = [
            # VERY early test platform - right after the moving platforms
            (550, WORLD_HEIGHT - 300, 80, 25, 4.0),   # Close to start area for testing
            
            # Early game - safe disappearing platforms (longer times)
            (1400, WORLD_HEIGHT - 600, 100, 25, 4.0),  # x, y, width, height, disappear_time
            (1800, WORLD_HEIGHT - 1000, 90, 25, 3.5),
            
            # Mid game - moderate challenge
            (2500, WORLD_HEIGHT - 1400, 80, 25, 3.0),
            (3200, WORLD_HEIGHT - 1900, 100, 25, 3.5),
            
            # Late game - quick disappearing (advanced players only)
            (4200, WORLD_HEIGHT - 2100, 70, 25, 2.5),
            (5800, WORLD_HEIGHT - 2900, 80, 25, 2.0),
        ]
        
        for x, y, width, height, disappear_time in disappearing_platforms_data:
            disappearing_platform = DisappearingPlatform(x, y, width, height, theme, disappear_time)
            self.platforms.add(disappearing_platform)
            self.all_sprites.add(disappearing_platform)
        
        # Add PHASE 3: Jump Boost Power-ups (strategic placement)
        jump_boost_locations = [
            # Early game - teach players about power-ups
            (600, WORLD_HEIGHT - 400),   # Near first moving platform
            
            # Mid game - help with difficult sections
            (1600, WORLD_HEIGHT - 1200), # Before disappearing platform section
            (2800, WORLD_HEIGHT - 1600), # Mid-level boost
            
            # Late game - for challenging final areas
            (4500, WORLD_HEIGHT - 2500), # Before final moving platforms
            (6000, WORLD_HEIGHT - 3200), # Near victory area
        ]
        
        for x, y in jump_boost_locations:
            jump_boost = PowerUp(x, y, "jump_boost", theme)
            self.powerups.add(jump_boost)
            self.all_sprites.add(jump_boost)
    
    def handle_input(self):
        """Handle input based on current game state"""
        # Update key states
        self.previous_keys = self.keys_pressed
        self.keys_pressed = pygame.key.get_pressed()
    
    def get_keys_just_pressed(self):
        """Get keys that were just pressed this frame"""
        keys_just_pressed = {}
        for i in range(len(self.keys_pressed)):
            keys_just_pressed[i] = self.keys_pressed[i] and not self.previous_keys[i]
        return keys_just_pressed
    
    def handle_events(self):
        """Handle all game events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.state == GAME_STATE_PLAYING:
                        self.state = GAME_STATE_CHARACTER_SELECT
                    elif self.state in [GAME_STATE_GAME_OVER, GAME_STATE_VICTORY]:
                        self.state = GAME_STATE_CHARACTER_SELECT
                    else:
                        self.running = False
                elif event.key == pygame.K_SPACE:
                    if self.state in [GAME_STATE_GAME_OVER, GAME_STATE_VICTORY]:
                        # Restart the game with same character
                        self.init_game_world()
                        self.state = GAME_STATE_PLAYING
    
    def update(self):
        """Update game based on current state"""
        dt = self.clock.get_time() / 1000.0  # Delta time in seconds
        
        if self.state == GAME_STATE_CHARACTER_SELECT:
            self.character_select.update(dt)
            
            # Check if character selection is complete
            keys_just_pressed = self.get_keys_just_pressed()
            if self.character_select.handle_input(self.keys_pressed, keys_just_pressed):
                self.character_config = self.character_select.get_character_config()
                self.init_game_world()
                self.state = GAME_STATE_PLAYING
                
        elif self.state == GAME_STATE_PLAYING:
            # Handle player input
            self.player.handle_input(self.keys_pressed)
            
            # Update player with platform collision
            self.player.update(self.platforms)
            
            # Update all platforms (for moving/disappearing behavior) - use the same dt!
            for platform in self.platforms:
                platform.update(dt)
            
            # Update power-ups
            for powerup in self.powerups:
                powerup.update(dt)
            
            # Check power-up collection
            collected_powerups = pygame.sprite.spritecollide(self.player, self.powerups, False)
            for powerup in collected_powerups:
                if not powerup.collected:
                    powerup.collect()
                    if powerup.powerup_type == "jump_boost":
                        self.player.add_powerup("jump_boost", 10.0)  # 10-second jump boost
                    self.powerups.remove(powerup)
                    self.all_sprites.remove(powerup)
            
            # Update camera
            self.camera.update(self.player.rect)
            
            # Check for death and victory
            self.check_death_and_victory()
    
    def draw_background(self, theme):
        """Draw the background with theme coloring"""
        # Get the theme key from the character config
        theme_key = self.character_config['theme']
        
        if theme_key in self.background_images and self.background_images[theme_key]:
            # Use the theme-specific background
            bg_image = self.background_images[theme_key]
            
            # Calculate how many background tiles we need based on camera position
            bg_x = int(-(self.camera.x % SCREEN_WIDTH))
            bg_y = int(-(self.camera.y % SCREEN_HEIGHT))
            
            # Draw background tiles to cover the screen
            for x in range(bg_x - SCREEN_WIDTH, SCREEN_WIDTH + SCREEN_WIDTH, SCREEN_WIDTH):
                for y in range(bg_y - SCREEN_HEIGHT, SCREEN_HEIGHT + SCREEN_HEIGHT, SCREEN_HEIGHT):
                    self.screen.blit(bg_image, (x, y))
        else:
            # Fallback to solid color background
            self.screen.fill(theme['bg_color'])
    
    def draw_powerup_ui(self):
        """Draw active power-up indicators on screen"""
        if not self.player.active_powerups:
            return
        
        # Set up fonts
        font = pygame.font.Font(None, 28)
        small_font = pygame.font.Font(None, 20)
        
        y_offset = 20
        for powerup_type, time_left in self.player.active_powerups.items():
            if powerup_type == "jump_boost":
                # Draw jump boost indicator
                icon_color = (100, 255, 100)
                bg_color = (0, 0, 0, 100)
                
                # Create background box
                box_width = 160
                box_height = 40
                box_surface = pygame.Surface((box_width, box_height), pygame.SRCALPHA)
                box_surface.fill(bg_color)
                
                # Draw power-up icon (simple up arrow)
                pygame.draw.polygon(box_surface, icon_color, [(15, 25), (10, 15), (20, 15)])
                pygame.draw.rect(box_surface, icon_color, (12, 15, 6, 15))
                
                # Draw text
                text = font.render("Jump Boost", True, WHITE)
                box_surface.blit(text, (30, 8))
                
                # Draw timer
                timer_text = small_font.render(f"{time_left:.1f}s", True, icon_color)
                box_surface.blit(timer_text, (30, 24))
                
                # Draw border
                pygame.draw.rect(box_surface, icon_color, (0, 0, box_width, box_height), 2)
                
                # Blit to screen
                self.screen.blit(box_surface, (SCREEN_WIDTH - box_width - 20, y_offset))
                y_offset += box_height + 10
    
    def draw(self):
        """Draw everything based on current state"""
        if self.state == GAME_STATE_CHARACTER_SELECT:
            self.character_select.draw()
            
        elif self.state == GAME_STATE_PLAYING:
            # Get theme for background
            theme = THEMES[self.character_config['theme']]
            
            # Draw themed background
            self.draw_background(theme)
            
            # Draw all sprites with camera offset
            for sprite in self.all_sprites:
                sprite_rect = self.camera.apply(sprite.rect)
                self.screen.blit(sprite.image, sprite_rect)
            
            # Draw power-up UI
            self.draw_powerup_ui()
                
        elif self.state == GAME_STATE_GAME_OVER:
            self.draw_game_over_screen()
            
        elif self.state == GAME_STATE_VICTORY:
            self.draw_victory_screen()
        
        # Update display
        pygame.display.flip()
    
    def draw_game_over_screen(self):
        """Draw the game over screen"""
        # Dark overlay
        self.screen.fill((20, 20, 20))
        
        font_large = pygame.font.Font(None, 72)
        font_medium = pygame.font.Font(None, 48)
        
        # Game Over text
        game_over_text = font_large.render("GAME OVER", True, RED)
        game_over_rect = game_over_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 100))
        self.screen.blit(game_over_text, game_over_rect)
        
        # Retry instructions
        retry_text = font_medium.render("Press SPACE to try again", True, WHITE)
        retry_rect = retry_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
        self.screen.blit(retry_text, retry_rect)
        
        # Return to character select
        menu_text = font_medium.render("Press ESC for character select", True, WHITE)
        menu_rect = menu_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 60))
        self.screen.blit(menu_text, menu_rect)
    
    def draw_victory_screen(self):
        """Draw the victory screen"""
        theme = THEMES[self.character_config['theme']]
        
        # Victory background with theme colors
        self.screen.fill(theme['bg_color'])
        
        font_large = pygame.font.Font(None, 72)
        font_medium = pygame.font.Font(None, 48)
        
        # Victory text
        victory_text = font_large.render("VICTORY!", True, theme['glow_color'])
        victory_rect = victory_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 100))
        self.screen.blit(victory_text, victory_rect)
        
        # Congratulations
        congrats_text = font_medium.render("You reached the top!", True, WHITE)
        congrats_rect = congrats_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
        self.screen.blit(congrats_text, congrats_rect)
        
        # Play again instructions
        again_text = font_medium.render("Press SPACE to play again", True, WHITE)
        again_rect = again_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 60))
        self.screen.blit(again_text, again_rect)
        
        # Return to character select
        menu_text = font_medium.render("Press ESC for character select", True, WHITE)
        menu_rect = menu_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 120))
        self.screen.blit(menu_text, menu_rect)
    
    def check_death_and_victory(self):
        """Check if player has died or won"""
        # Death condition: touched the ground platform (bottom of world)
        if self.player.rect.bottom >= WORLD_HEIGHT - GROUND_HEIGHT:
            self.state = GAME_STATE_GAME_OVER
            return
        
        # Victory condition: reached top-right corner
        if self.victory_zone.colliderect(self.player.rect):
            self.state = GAME_STATE_VICTORY
            return
    
    def run(self):
        """Main game loop"""
        while self.running:
            # Handle events
            self.handle_events()
            
            # Handle input
            self.handle_input()
            
            # Update game state
            self.update()
            
            # Draw everything
            self.draw()
            
            # Control framerate
            self.clock.tick(FPS)
        
        # Clean up
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run() 