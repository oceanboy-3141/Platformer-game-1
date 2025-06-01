import pygame
import sys
from settings import *
from player import Player
from platforms import Platform, Ground
from character_select import CharacterSelectScreen

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
    
    def load_background(self):
        """Load and prepare the background image"""
        try:
            self.background_image = pygame.image.load("Assets/Back round.png").convert()
            # Scale background to fit screen
            self.background_image = pygame.transform.scale(self.background_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
        except:
            # Fallback to None if image fails to load
            self.background_image = None
            print("Warning: Could not load background image, using solid color")
    
    def init_game_world(self):
        """Initialize the game world after character selection"""
        # Create sprite groups
        self.all_sprites = pygame.sprite.Group()
        self.platforms = pygame.sprite.Group()
        
        # Create player with selected character config
        self.player = Player(100, 100, self.character_config)
        self.all_sprites.add(self.player)
        
        # Create platforms with theme
        self.create_platforms()
    
    def create_platforms(self):
        """Create the initial platforms for the level"""
        theme = THEMES[self.character_config['theme']]
        
        # Ground platform
        ground = Ground(0, SCREEN_HEIGHT - GROUND_HEIGHT, SCREEN_WIDTH, theme)
        self.platforms.add(ground)
        self.all_sprites.add(ground)
        
        # Some floating platforms with theme colors
        platform1 = Platform(300, SCREEN_HEIGHT - 200, 200, 20, theme)
        self.platforms.add(platform1)
        self.all_sprites.add(platform1)
        
        platform2 = Platform(600, SCREEN_HEIGHT - 300, 150, 20, theme)
        self.platforms.add(platform2)
        self.all_sprites.add(platform2)
        
        platform3 = Platform(100, SCREEN_HEIGHT - 400, 100, 20, theme)
        self.platforms.add(platform3)
        self.all_sprites.add(platform3)
        
        platform4 = Platform(800, SCREEN_HEIGHT - 250, 180, 20, theme)
        self.platforms.add(platform4)
        self.all_sprites.add(platform4)
    
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
                    else:
                        self.running = False
    
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
    
    def draw_background(self, theme):
        """Draw the background with theme coloring"""
        if self.background_image:
            # Apply theme-based color tinting to background
            tinted_bg = self.background_image.copy()
            
            # Create color overlay based on theme
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((*theme['bg_color'], 50))  # Light theme tint
            
            # Blend overlay with background using simple blit
            tinted_bg.blit(overlay, (0, 0))
            
            self.screen.blit(tinted_bg, (0, 0))
        else:
            # Fallback to solid color background
            self.screen.fill(theme['bg_color'])
    
    def draw(self):
        """Draw everything based on current state"""
        if self.state == GAME_STATE_CHARACTER_SELECT:
            self.character_select.draw()
            
        elif self.state == GAME_STATE_PLAYING:
            # Get theme for background
            theme = THEMES[self.character_config['theme']]
            
            # Draw themed background
            self.draw_background(theme)
            
            # Draw all sprites
            self.all_sprites.draw(self.screen)
            
            # Draw player info (debug)
            self.draw_debug_info()
        
        # Update display
        pygame.display.flip()
    
    def draw_debug_info(self):
        """Draw debug information on screen"""
        font = pygame.font.Font(None, 36)
        
        # Player position
        pos_text = font.render(f"Position: ({self.player.rect.x}, {self.player.rect.y})", True, WHITE)
        self.screen.blit(pos_text, (10, 10))
        
        # Player velocity
        vel_text = font.render(f"Velocity: ({self.player.vel_x:.1f}, {self.player.vel_y:.1f})", True, WHITE)
        self.screen.blit(vel_text, (10, 50))
        
        # On ground status
        ground_text = font.render(f"On Ground: {self.player.on_ground}", True, WHITE)
        self.screen.blit(ground_text, (10, 90))
        
        # Jump count
        jump_text = font.render(f"Jumps Used: {self.player.jump_count}/{self.player.max_jumps}", True, WHITE)
        self.screen.blit(jump_text, (10, 130))
        
        # Character info
        char_text = font.render(f"Theme: {THEMES[self.character_config['theme']]['name']}", True, WHITE)
        self.screen.blit(char_text, (10, 170))
        
        # Controls
        controls_text = font.render("Controls: Arrow Keys/WASD to move, Space/Up to jump", True, WHITE)
        self.screen.blit(controls_text, (10, SCREEN_HEIGHT - 40))
        
        esc_text = font.render("Press ESC to return to character select", True, WHITE)
        self.screen.blit(esc_text, (10, SCREEN_HEIGHT - 80))
    
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