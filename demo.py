import pygame
import math
import random
from settings import *
from player import Player

class DemoAI:
    """Ultra-simple, reliable AI that actually works"""
    
    def __init__(self, player, platforms, powerups, victory_zone):
        self.player = player
        self.platforms = platforms
        self.powerups = powerups
        self.victory_zone = victory_zone
        
        # Simple state tracking
        self.stuck_timer = 0.0
        self.last_x = player.rect.x
        self.jump_cooldown = 0.0
        self.direction = 1  # 1 = right, -1 = left
        self.panic_timer = 0.0
    
    def update(self, dt):
        """Update ultra-simple AI logic"""
        self.jump_cooldown = max(0, self.jump_cooldown - dt)
        self.panic_timer += dt
        
        # Check if stuck (not moving horizontally)
        if abs(self.player.rect.x - self.last_x) < 3:
            self.stuck_timer += dt
        else:
            self.stuck_timer = 0.0
            self.panic_timer = 0.0
            self.last_x = self.player.rect.x
        
        # Very simple movement
        self.simple_reliable_movement()
    
    def simple_reliable_movement(self):
        """Ultra-simple but reliable movement that actually works"""
        keys = {
            pygame.K_LEFT: False, 
            pygame.K_RIGHT: False, 
            pygame.K_a: False,
            pygame.K_d: False,
            pygame.K_SPACE: False,
            pygame.K_UP: False,
            pygame.K_w: False
        }
        
        # SUPER SIMPLE: Just move right and jump when needed
        goal_direction = 1 if self.player.rect.x < self.victory_zone.centerx else -1
        
        # Always try to move toward goal (unless in air)
        if self.player.on_ground:
            if goal_direction > 0:
                keys[pygame.K_RIGHT] = True
                keys[pygame.K_d] = True
            else:
                keys[pygame.K_LEFT] = True
                keys[pygame.K_a] = True
        
        # MUCH MORE CONSERVATIVE JUMPING: Only jump when on ground and stuck
        should_jump = False
        
        # ONLY jump if we're on solid ground AND stuck for a while
        if (self.player.on_ground and 
            self.stuck_timer > 2.0 and 
            self.jump_cooldown <= 0):
            should_jump = True
            print(f"AI JUMPING! Stuck for {self.stuck_timer:.1f} seconds")
        
        # EMERGENCY jump if we haven't moved in a very long time
        elif (self.player.on_ground and 
              self.panic_timer > 4.0 and 
              self.jump_cooldown <= 0):
            should_jump = True
            self.panic_timer = 0.0
            print(f"AI PANIC JUMP! Been {self.panic_timer:.1f} seconds")
        
        # Apply jump ONLY if on ground
        if should_jump:
            keys[pygame.K_SPACE] = True
            keys[pygame.K_UP] = True
            keys[pygame.K_w] = True
            self.jump_cooldown = 1.0  # Longer cooldown to prevent spam
        
        # Apply controls
        self.player.handle_input(keys)
    
    def check_edge_simple(self):
        """Super simple edge detection - just check if we're near world edge"""
        # Simple check: if player is near the right edge of the world, we're at edge
        if self.player.rect.right > WORLD_WIDTH - 100:
            return True
        
        # Check if player is falling (might have walked off edge)
        if not self.player.on_ground and self.player.vel_y > 0:
            return True
        
        return False
    
    def find_closest_platform_ahead(self):
        """Find any platform ahead of us"""
        for platform in self.platforms:
            # Skip death ground
            if platform.rect.bottom >= WORLD_HEIGHT - GROUND_HEIGHT:
                continue
            
            # Any platform to the right of us
            if platform.rect.centerx > self.player.rect.centerx:
                return platform
        
        return None
    
    def can_probably_reach(self, platform):
        """Very simple reachability check"""
        if not platform:
            return False
        
        # Just check if it's not too far
        dx = abs(platform.rect.centerx - self.player.rect.centerx)
        return dx < 500  # Very generous range
    
    def get_ai_status(self):
        """Get current AI status for display"""
        if not self.player.on_ground:
            status = "In Air"
        elif self.check_edge_simple():
            status = "At Edge - Looking for Platform"
        elif self.stuck_timer > 2.0:
            status = "Stuck - Will Jump Soon"
        else:
            status = "Moving Safely"
        
        next_platform = self.find_closest_platform_ahead()
        if next_platform:
            target_info = f"Platform at ({next_platform.rect.centerx}, {next_platform.rect.centery})"
        else:
            target_info = f"Victory Zone ({self.victory_zone.centerx}, {self.victory_zone.centery})"
        
        return {
            'action': status,
            'target': target_info,
            'stuck_time': f"{self.stuck_timer:.1f}s" if self.stuck_timer > 0 else "Not stuck",
            'on_platform': "Ground" if self.player.on_ground else "Airborne"
        }


class DemoLevel:
    """Demo mode that shows AI playing the game"""
    
    def __init__(self, screen, character_config, main_game):
        self.screen = screen
        self.character_config = character_config
        self.theme = THEMES[character_config['theme']]
        
        # Copy game world from main game
        self.all_sprites = main_game.all_sprites.copy()
        self.platforms = main_game.platforms.copy()
        self.powerups = main_game.powerups.copy()
        self.victory_zone = main_game.victory_zone
        
        # Create AI player
        self.player = Player(200, WORLD_HEIGHT - 200, character_config)
        self.all_sprites.add(self.player)
        
        # Create AI controller
        self.ai = DemoAI(self.player, self.platforms, self.powerups, self.victory_zone)
        
        # Demo state
        self.demo_complete = False
        self.demo_timer = 0.0
        
        # UI elements
        self.font_large = pygame.font.Font(None, 36)
        self.font_medium = pygame.font.Font(None, 28)
        self.font_small = pygame.font.Font(None, 22)
    
    def update(self, dt):
        """Update demo logic"""
        self.demo_timer += dt
        
        # Update AI
        self.ai.update(dt)
        
        # Update player
        self.player.update(self.platforms)
        
        # Update platforms
        for platform in self.platforms:
            platform.update(dt)
            
            # Special handling for teleporter elevator
            if hasattr(platform, 'rider') and platform.rider:
                if not self.player.rect.colliderect(platform.rect):
                    platform.remove_rider()
        
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
        
        # Check for victory
        if self.victory_zone.colliderect(self.player.rect):
            self.demo_complete = True
        
        # Check for death (restart demo)
        if self.player.rect.bottom >= WORLD_HEIGHT - GROUND_HEIGHT:
            # Restart demo
            self.player.rect.x = 200
            self.player.rect.y = WORLD_HEIGHT - 200
            self.player.vel_x = 0
            self.player.vel_y = 0
            self.demo_timer = 0.0
    
    def draw_demo_ui(self):
        """Draw demo UI overlay"""
        # Semi-transparent background for UI
        ui_bg = pygame.Surface((SCREEN_WIDTH, 120), pygame.SRCALPHA)
        ui_bg.fill((0, 0, 0, 180))
        self.screen.blit(ui_bg, (0, 0))
        
        # Demo title
        title_text = self.font_large.render("🤖 AI DEMO MODE", True, self.theme['glow_color'])
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH//2, 25))
        self.screen.blit(title_text, title_rect)
        
        # AI status
        ai_status = self.ai.get_ai_status()
        status_text = f"AI Action: {ai_status['action'].upper()}"
        status = self.font_medium.render(status_text, True, WHITE)
        self.screen.blit(status, (20, 50))
        
        target_text = f"Target: {ai_status['target']}"
        target = self.font_small.render(target_text, True, LIGHT_GRAY)
        self.screen.blit(target, (20, 75))
        
        platform_text = f"Platform: {ai_status['on_platform']}"
        platform = self.font_small.render(platform_text, True, LIGHT_GRAY)
        self.screen.blit(platform, (20, 95))
        
        # Demo instructions
        instructions = [
            "Watch the AI navigate through the level!",
            "Press ESC to return to character select",
            "Press SPACE to restart demo"
        ]
        
        for i, instruction in enumerate(instructions):
            inst_text = self.font_small.render(instruction, True, WHITE)
            self.screen.blit(inst_text, (SCREEN_WIDTH - 300, 50 + i * 20))
        
        # Demo timer
        timer_text = f"Demo Time: {self.demo_timer:.1f}s"
        timer = self.font_small.render(timer_text, True, LIGHT_GRAY)
        self.screen.blit(timer, (SCREEN_WIDTH//2 - 50, SCREEN_HEIGHT - 30))
    
    def draw_background(self):
        """Draw themed background"""
        self.screen.fill(self.theme['bg_color'])
    
    def draw(self, camera):
        """Draw the demo level"""
        # Draw background
        self.draw_background()
        
        # Draw all sprites with camera offset
        for sprite in self.all_sprites:
            sprite_rect = camera.apply(sprite.rect)
            self.screen.blit(sprite.image, sprite_rect)
        
        # Draw demo UI on top
        self.draw_demo_ui()
    
    def is_complete(self):
        """Check if demo should end"""
        return self.demo_complete
    
    def should_restart(self, keys_just_pressed):
        """Check if demo should restart"""
        return keys_just_pressed.get(pygame.K_SPACE, False)
    
    def should_exit(self, keys_just_pressed):
        """Check if should exit demo"""
        return keys_just_pressed.get(pygame.K_ESCAPE, False) 