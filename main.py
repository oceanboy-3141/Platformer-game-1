import pygame
import sys
from settings import *
from player import Player
from platforms import Platform, Ground

class Game:
    def __init__(self):
        # Initialize Pygame
        pygame.init()
        
        # Set up the display
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Pygame Platformer - Basic Movement")
        
        # Set up the clock for consistent framerate
        self.clock = pygame.time.Clock()
        
        # Create sprite groups
        self.all_sprites = pygame.sprite.Group()
        self.platforms = pygame.sprite.Group()
        
        # Create player
        self.player = Player(100, 100)
        self.all_sprites.add(self.player)
        
        # Create platforms
        self.create_platforms()
        
        # Game state
        self.running = True
    
    def create_platforms(self):
        """Create the initial platforms for the level"""
        # Ground platform
        ground = Ground(0, SCREEN_HEIGHT - GROUND_HEIGHT, SCREEN_WIDTH)
        self.platforms.add(ground)
        self.all_sprites.add(ground)
        
        # Some floating platforms
        platform1 = Platform(300, SCREEN_HEIGHT - 200, 200, 20)
        self.platforms.add(platform1)
        self.all_sprites.add(platform1)
        
        platform2 = Platform(600, SCREEN_HEIGHT - 300, 150, 20)
        self.platforms.add(platform2)
        self.all_sprites.add(platform2)
        
        platform3 = Platform(100, SCREEN_HEIGHT - 400, 100, 20)
        self.platforms.add(platform3)
        self.all_sprites.add(platform3)
        
        platform4 = Platform(800, SCREEN_HEIGHT - 250, 180, 20)
        self.platforms.add(platform4)
        self.all_sprites.add(platform4)
    
    def handle_events(self):
        """Handle all game events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
    
    def update(self):
        """Update all game objects"""
        # Get current key states
        keys = pygame.key.get_pressed()
        
        # Handle player input
        self.player.handle_input(keys)
        
        # Update player with platform collision
        self.player.update(self.platforms)
    
    def draw(self):
        """Draw everything to the screen"""
        # Clear screen with background color
        self.screen.fill(WHITE)
        
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
        pos_text = font.render(f"Position: ({self.player.rect.x}, {self.player.rect.y})", True, BLACK)
        self.screen.blit(pos_text, (10, 10))
        
        # Player velocity
        vel_text = font.render(f"Velocity: ({self.player.vel_x:.1f}, {self.player.vel_y:.1f})", True, BLACK)
        self.screen.blit(vel_text, (10, 50))
        
        # On ground status
        ground_text = font.render(f"On Ground: {self.player.on_ground}", True, BLACK)
        self.screen.blit(ground_text, (10, 90))
        
        # Jump count
        jump_text = font.render(f"Jumps Used: {self.player.jump_count}/{self.player.max_jumps}", True, BLACK)
        self.screen.blit(jump_text, (10, 130))
        
        # Controls
        controls_text = font.render("Controls: Arrow Keys/WASD to move, Space/Up to jump", True, BLACK)
        self.screen.blit(controls_text, (10, SCREEN_HEIGHT - 40))
        
        esc_text = font.render("Press ESC to quit", True, BLACK)
        self.screen.blit(esc_text, (10, SCREEN_HEIGHT - 80))
    
    def run(self):
        """Main game loop"""
        while self.running:
            # Handle events
            self.handle_events()
            
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