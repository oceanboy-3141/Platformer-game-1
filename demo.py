import pygame
import math
import random
from settings import *
from player import Player

class DemoAI:
    """AI controller that demonstrates the game by playing it intelligently"""
    
    def __init__(self, player, platforms, powerups, victory_zone):
        self.player = player
        self.platforms = platforms
        self.powerups = powerups
        self.victory_zone = victory_zone
        
        # AI state management
        self.current_target = None
        self.path_finding_timer = 0.0
        self.stuck_timer = 0.0
        self.last_position = (0, 0)
        self.retry_jump_timer = 0.0
        
        # AI decision making
        self.decision_timer = 0.0
        self.current_action = "explore"  # explore, jump, wait, collect
        self.action_duration = 0.0
        
        # Platform analysis
        self.analyzed_platforms = []
        self.safe_platforms = []
        self.goal_direction = (1, -1)  # Generally move right and up
        
        # AI personality settings
        self.aggressiveness = 0.7  # How willing to take risks (0-1)
        self.exploration_tendency = 0.8  # How much to explore vs beeline to goal
        
        # Analyze the level once
        self.analyze_level()
    
    def analyze_level(self):
        """Analyze the level layout to understand platform relationships"""
        self.analyzed_platforms = []
        self.safe_platforms = []
        
        for platform in self.platforms:
            platform_info = {
                'platform': platform,
                'rect': platform.rect,
                'type': self.identify_platform_type(platform),
                'safety': self.calculate_platform_safety(platform),
                'connections': []
            }
            
            # Mark safe platforms
            if platform_info['safety'] > 0.5:
                self.safe_platforms.append(platform_info)
            
            self.analyzed_platforms.append(platform_info)
        
        # Find connections between platforms
        for platform_info in self.analyzed_platforms:
            platform_info['connections'] = self.find_platform_connections(platform_info)
    
    def identify_platform_type(self, platform):
        """Identify what type of platform this is"""
        if hasattr(platform, 'one_way'):
            return "oneway"
        elif hasattr(platform, 'bounce_strength'):
            return "bouncy"
        elif hasattr(platform, 'ice_friction'):
            return "ice"
        elif hasattr(platform, 'is_solid') and not platform.is_solid:
            return "disappeared"
        elif hasattr(platform, 'activated'):
            return "disappearing"
        elif hasattr(platform, 'get_movement_delta'):
            return "moving"
        elif hasattr(platform, 'get_movement_delta_y'):
            return "elevator"
        elif hasattr(platform, 'angle'):
            return "rotating"
        elif hasattr(platform, 'rider'):
            return "teleporter"
        else:
            return "normal"
    
    def calculate_platform_safety(self, platform):
        """Calculate how safe a platform is (0-1)"""
        safety = 0.8  # Base safety
        
        # Check platform type dangers
        platform_type = self.identify_platform_type(platform)
        if platform_type == "disappearing":
            safety -= 0.3
        elif platform_type == "moving":
            safety -= 0.1
        elif platform_type == "ice":
            safety -= 0.2
        elif platform_type == "rotating":
            safety -= 0.4
        elif platform_type == "bouncy":
            safety += 0.1  # Actually helpful
        elif platform_type == "teleporter":
            safety += 0.2  # Very helpful
        
        # Check proximity to death zone
        death_zone_y = WORLD_HEIGHT - GROUND_HEIGHT
        distance_to_death = death_zone_y - platform.rect.bottom
        if distance_to_death < 200:
            safety -= 0.3
        
        # Check platform size (bigger = safer)
        if platform.rect.width > 150:
            safety += 0.1
        elif platform.rect.width < 80:
            safety -= 0.1
        
        return max(0.0, min(1.0, safety))
    
    def find_platform_connections(self, platform_info):
        """Find platforms that can be reached from this platform"""
        connections = []
        current_rect = platform_info['rect']
        
        for other_info in self.analyzed_platforms:
            if other_info == platform_info:
                continue
                
            other_rect = other_info['rect']
            
            # Check if platform is reachable
            horizontal_distance = abs(other_rect.centerx - current_rect.centerx)
            vertical_distance = other_rect.centery - current_rect.centery
            
            # Can reach if within jump range
            max_jump_distance = 150  # Player can jump about this far
            max_jump_height = -200   # Player can jump about this high
            
            if (horizontal_distance <= max_jump_distance and 
                vertical_distance >= max_jump_height and
                vertical_distance <= 100):  # Don't jump down too far
                
                connection_info = {
                    'platform': other_info,
                    'distance': horizontal_distance,
                    'height_diff': vertical_distance,
                    'difficulty': self.calculate_jump_difficulty(horizontal_distance, vertical_distance)
                }
                connections.append(connection_info)
        
        return sorted(connections, key=lambda x: x['difficulty'])
    
    def calculate_jump_difficulty(self, distance, height_diff):
        """Calculate how difficult a jump is (0-1)"""
        difficulty = 0.0
        
        # Distance difficulty
        difficulty += (distance / 150) * 0.4
        
        # Height difficulty (upward jumps are harder)
        if height_diff < 0:  # Going up
            difficulty += abs(height_diff / 200) * 0.6
        else:  # Going down (easier)
            difficulty += (height_diff / 100) * 0.2
        
        return min(1.0, difficulty)
    
    def update(self, dt):
        """Update AI decision making and control player"""
        self.decision_timer += dt
        self.action_duration += dt
        
        # Check if stuck
        current_pos = (self.player.rect.centerx, self.player.rect.centery)
        if abs(current_pos[0] - self.last_position[0]) < 5 and abs(current_pos[1] - self.last_position[1]) < 5:
            self.stuck_timer += dt
        else:
            self.stuck_timer = 0.0
            self.last_position = current_pos
        
        # Make decisions every 0.1 seconds
        if self.decision_timer >= 0.1:
            self.make_decision()
            self.decision_timer = 0.0
        
        # Execute current action
        self.execute_action()
    
    def make_decision(self):
        """AI decision making brain"""
        # Check for immediate dangers
        if self.is_in_immediate_danger():
            self.current_action = "escape"
            self.action_duration = 0.0
            return
        
        # Check for power-ups nearby
        nearby_powerup = self.find_nearby_powerup()
        if nearby_powerup and random.random() < 0.7:
            self.current_target = nearby_powerup
            self.current_action = "collect"
            self.action_duration = 0.0
            return
        
        # Check if stuck and need to try something different
        if self.stuck_timer > 2.0:
            self.current_action = "unstuck"
            self.action_duration = 0.0
            self.stuck_timer = 0.0
            return
        
        # Normal pathfinding toward goal
        if self.current_action == "explore" or self.action_duration > 3.0:
            self.find_next_target()
            self.current_action = "navigate"
            self.action_duration = 0.0
    
    def is_in_immediate_danger(self):
        """Check if player is in immediate danger"""
        # Check if falling toward death zone
        if self.player.vel_y > 10 and self.player.rect.bottom > WORLD_HEIGHT - GROUND_HEIGHT - 200:
            return True
        
        # Check if on disappearing platform
        for platform in self.platforms:
            if (hasattr(platform, 'activated') and platform.activated and 
                self.player.rect.colliderect(platform.rect)):
                return True
        
        return False
    
    def find_nearby_powerup(self):
        """Find power-ups within reasonable distance"""
        for powerup in self.powerups:
            distance = math.sqrt((powerup.rect.centerx - self.player.rect.centerx)**2 + 
                               (powerup.rect.centery - self.player.rect.centery)**2)
            if distance < 200 and not powerup.collected:
                return powerup
        return None
    
    def find_next_target(self):
        """Find the next platform to move toward"""
        current_platform = self.find_current_platform()
        
        if not current_platform:
            # If not on platform, find nearest safe platform
            self.current_target = self.find_nearest_safe_platform()
            return
        
        # Find platform connections
        current_info = None
        for info in self.analyzed_platforms:
            if info['platform'] == current_platform:
                current_info = info
                break
        
        if not current_info or not current_info['connections']:
            # No connections, find best platform to jump to
            self.current_target = self.find_best_next_platform()
            return
        
        # Choose best connection based on goal direction
        best_connection = self.choose_best_connection(current_info['connections'])
        if best_connection:
            self.current_target = best_connection['platform']['platform']
        else:
            self.current_target = self.find_best_next_platform()
    
    def find_current_platform(self):
        """Find which platform the player is currently on"""
        for platform in self.platforms:
            if (self.player.rect.colliderect(platform.rect) and 
                self.player.rect.bottom <= platform.rect.top + 10):
                return platform
        return None
    
    def find_nearest_safe_platform(self):
        """Find the nearest safe platform to land on"""
        best_platform = None
        best_distance = float('inf')
        
        for info in self.safe_platforms:
            platform = info['platform']
            distance = math.sqrt((platform.rect.centerx - self.player.rect.centerx)**2 + 
                               (platform.rect.centery - self.player.rect.centery)**2)
            
            if distance < best_distance:
                best_distance = distance
                best_platform = platform
        
        return best_platform
    
    def find_best_next_platform(self):
        """Find the best platform to move toward the goal"""
        goal_x = self.victory_zone.centerx
        goal_y = self.victory_zone.centery
        
        best_platform = None
        best_score = -1
        
        for info in self.analyzed_platforms:
            platform = info['platform']
            
            # Skip if too dangerous or disappeared
            if info['safety'] < 0.3 or info['type'] == "disappeared":
                continue
            
            # Calculate score based on progress toward goal and safety
            progress_x = (platform.rect.centerx - self.player.rect.centerx) * self.goal_direction[0]
            progress_y = (platform.rect.centery - self.player.rect.centery) * self.goal_direction[1]
            
            distance_to_goal = math.sqrt((platform.rect.centerx - goal_x)**2 + 
                                       (platform.rect.centery - goal_y)**2)
            
            score = (progress_x * 0.4 + progress_y * 0.3 + info['safety'] * 0.3 - 
                    distance_to_goal * 0.0001)
            
            if score > best_score:
                best_score = score
                best_platform = platform
        
        return best_platform
    
    def choose_best_connection(self, connections):
        """Choose the best platform connection to use"""
        goal_x = self.victory_zone.centerx
        
        best_connection = None
        best_score = -1
        
        for connection in connections:
            platform_info = connection['platform']
            platform = platform_info['platform']
            
            # Skip dangerous platforms
            if platform_info['safety'] < 0.4:
                continue
            
            # Prefer platforms that move us toward the goal
            progress_score = (platform.rect.centerx - self.player.rect.centerx) / 200.0
            safety_score = platform_info['safety']
            difficulty_penalty = connection['difficulty']
            
            score = progress_score * 0.5 + safety_score * 0.4 - difficulty_penalty * 0.3
            
            if score > best_score:
                best_score = score
                best_connection = connection
        
        return best_connection
    
    def execute_action(self):
        """Execute the current AI action"""
        if self.current_action == "escape":
            self.execute_escape()
        elif self.current_action == "collect":
            self.execute_collect()
        elif self.current_action == "navigate":
            self.execute_navigate()
        elif self.current_action == "unstuck":
            self.execute_unstuck()
        else:
            # Default exploration
            self.execute_navigate()
    
    def execute_escape(self):
        """Execute escape from danger"""
        # Try to get to nearest safe platform quickly
        safe_platform = self.find_nearest_safe_platform()
        if safe_platform:
            self.move_toward_target(safe_platform.rect.centerx, safe_platform.rect.centery, urgent=True)
        else:
            # Just try to move away from danger
            if self.player.rect.centerx < WORLD_WIDTH / 2:
                self.move_toward_target(self.player.rect.centerx + 200, self.player.rect.centery - 100)
            else:
                self.move_toward_target(self.player.rect.centerx - 200, self.player.rect.centery - 100)
    
    def execute_collect(self):
        """Execute power-up collection"""
        if self.current_target and hasattr(self.current_target, 'rect'):
            self.move_toward_target(self.current_target.rect.centerx, self.current_target.rect.centery)
        else:
            self.current_action = "navigate"
    
    def execute_navigate(self):
        """Execute navigation toward target"""
        if self.current_target and hasattr(self.current_target, 'rect'):
            self.move_toward_target(self.current_target.rect.centerx, self.current_target.rect.centery)
        else:
            # No target, just move toward goal
            self.move_toward_target(self.victory_zone.centerx, self.victory_zone.centery)
    
    def execute_unstuck(self):
        """Execute unstuck behavior"""
        # Try random direction
        if random.random() < 0.5:
            self.move_toward_target(self.player.rect.centerx + random.randint(-200, 200),
                                  self.player.rect.centery - 100, force_jump=True)
        else:
            self.move_toward_target(self.player.rect.centerx - 100, self.player.rect.centery - 50, force_jump=True)
    
    def move_toward_target(self, target_x, target_y, urgent=False, force_jump=False):
        """Move the player toward a target position"""
        # Create simulated key presses - include ALL keys that player.handle_input expects
        keys = {
            pygame.K_LEFT: False, 
            pygame.K_RIGHT: False, 
            pygame.K_a: False,
            pygame.K_d: False,
            pygame.K_SPACE: False,
            pygame.K_UP: False,
            pygame.K_w: False
        }
        
        dx = target_x - self.player.rect.centerx
        dy = target_y - self.player.rect.centery
        
        # Horizontal movement
        if abs(dx) > 20:  # Dead zone to prevent jittering
            if dx > 0:
                keys[pygame.K_RIGHT] = True
                keys[pygame.K_d] = True  # Also set WASD equivalent
            else:
                keys[pygame.K_LEFT] = True
                keys[pygame.K_a] = True  # Also set WASD equivalent
        
        # Jumping logic
        should_jump = False
        
        if force_jump:
            should_jump = True
        elif urgent and dy < -50:
            should_jump = True
        elif dy < -100:  # Target is significantly above
            should_jump = True
        elif abs(dx) > 100 and dy < 50:  # Need to jump gap
            should_jump = True
        elif self.player.vel_y > 0 and not self.player.on_ground:  # Falling, try to save with double jump
            should_jump = True
        
        # Smart jumping timing
        if should_jump:
            self.retry_jump_timer += 0.016  # Assume 60 FPS
            if self.retry_jump_timer > 0.2:  # Don't spam jump
                keys[pygame.K_SPACE] = True
                keys[pygame.K_UP] = True  # Also set arrow key equivalent
                keys[pygame.K_w] = True   # Also set WASD equivalent
                self.retry_jump_timer = 0.0
        
        # Apply the controls
        self.player.handle_input(keys)
    
    def get_ai_status(self):
        """Get current AI status for display"""
        return {
            'action': self.current_action,
            'target': f"({self.current_target.rect.centerx}, {self.current_target.rect.centery})" if self.current_target and hasattr(self.current_target, 'rect') else "None",
            'stuck_time': f"{self.stuck_timer:.1f}s" if self.stuck_timer > 0 else "Not stuck",
            'on_platform': self.identify_platform_type(self.find_current_platform()) if self.find_current_platform() else "Airborne"
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