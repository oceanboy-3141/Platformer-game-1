import pygame
import math
import random
import json
import os
from settings import *
from player import Player

class LearningAI:
    """Learning AI that gets smarter over time by remembering what works"""
    
    def __init__(self, player, platforms, powerups, victory_zone):
        self.player = player
        self.platforms = platforms
        self.powerups = powerups
        self.victory_zone = victory_zone
        
        # Learning memory
        self.success_memory = {}  # position -> successful action
        self.failure_memory = {}  # position -> list of failed actions
        self.action_history = []  # For tracking action sequences
        
        # Emotional memory system
        self.positive_reinforcement = {}  # action -> positive feeling strength (0-10)
        self.negative_reinforcement = {}  # action -> negative feeling strength (0-10)
        self.recent_progress_feeling = 0  # -10 to +10, how AI feels about recent progress
        
        # Personal Best (PB) System
        self.personal_best_distance = 200  # Starting position as initial PB
        self.pb_route = []  # List of (position_key, action) that led to PB
        self.pb_recovery_mode = False  # Whether AI is trying to get back to PB
        self.pb_route_index = 0  # Current step in PB recovery route
        
        # Performance tracking
        self.attempt_count = 0
        self.victories = 0
        self.current_distance = 200  # Track furthest rightward progress
        self.best_distance = 200
        self.consecutive_failures = 0
        
        # State tracking
        self.stuck_timer = 0.0
        self.last_x = self.player.rect.x
        self.learning_active = True
        self.jump_cooldown = 0.0
        
        # Auto-save counter
        self.actions_since_save = 0
        
        # Game knowledge
        self.game_knowledge = {
            "goal": "Reach the victory zone at (6400, WORLD_HEIGHT - 3300)",
            "death_condition": "Touching the bottom ground platform",
            "victory_condition": "Player rect collides with victory zone",
            "movement": "Arrow keys or WASD for left/right movement",
            "double_jump": "Spacebar for jumping, can double-jump in air",
            "platform_types": {
                "normal": "Standard platforms (brown/themed)",
                "moving": "Blue platforms that slide horizontally",
                "bouncy": "Orange platforms that boost jump height",
                "disappearing": "Flash red and fade when stepped on",
                "oneway": "Yellow platforms - jump through from below",
                "ice": "Light blue slippery platforms with low friction",
                "rotating": "Purple circular platforms that spin",
                "elevator": "Green platforms that move vertically and teleport rider"
            },
            "powerups": {
                "jump_boost": "Green crystals - 50% higher jumps for 10 seconds"
            }
        }
        
        # Load previous learning data
        self.load_learning_data()
        
        # Print tutorial for the AI
        self.print_game_tutorial()
    
    def print_game_tutorial(self):
        """Print the game rules and mechanics for the AI to understand"""
        print("\n" + "="*60)
        print("🎓 GAME TUTORIAL FOR AI")
        print("="*60)
        print(f"🎯 GOAL: {self.game_knowledge['goal']}")
        print("🔑 KEY STRATEGY: MOVE RIGHT AND UP TO WIN!")
        print("   Victory zone is at the TOP-RIGHT of the world")
        print("   Moving RIGHT = Horizontal progress toward victory")
        print("   Moving UP = Vertical progress toward victory") 
        print("   You need BOTH rightward AND upward movement!")
        print("   Moving LEFT or DOWN = Away from victory = SADNESS!")
        print(f"💀 DEATH: {self.game_knowledge['death_condition']}")
        print(f"🏆 VICTORY: {self.game_knowledge['victory_condition']}")
        print(f"🎮 MOVEMENT: {self.game_knowledge['movement']}")
        print(f"⬆️ JUMPING: {self.game_knowledge['double_jump']}")
        
        print("\n📋 PLATFORM TYPES:")
        for platform_type, description in self.game_knowledge['platform_types'].items():
            print(f"  • {platform_type.upper()}: {description}")
        
        print("\n💎 POWER-UPS:")
        for powerup_type, description in self.game_knowledge['powerups'].items():
            print(f"  • {powerup_type.upper()}: {description}")
        
        print("\n🧠 LEARNING STRATEGY:")
        print("  • PRIORITY #1: Move RIGHT and UP toward victory!")
        print("  • Start with HIGH EXPLORATION, solidify knowledge over time")
        print("  • Try different actions at each position")
        print("  • Remember what works and what fails")
        print("  • Feel EXTRA good about rightward AND upward progress")
        print("  • Strongly prefer actions that felt good before")
        print("  • Build emotional associations with actions")
        print("="*60 + "\n")
    
    def feel_emotion(self, emotion_type, intensity, action=None):
        """AI experiences emotions about actions and outcomes"""
        if emotion_type == "success":
            self.recent_progress_feeling = min(10, self.recent_progress_feeling + intensity)
            if action:
                current_positive = self.positive_reinforcement.get(action, 0)
                # BOOST positive feelings for rightward actions!
                if "right" in action:
                    intensity = min(10, intensity * 1.5)  # 50% bonus for rightward actions
                    print(f"😄 AI feels EXTRA GOOD about {action} (rightward bonus!)")
                self.positive_reinforcement[action] = min(10, current_positive + intensity)
                if "right" not in action:
                    print(f"😊 AI feels GOOD about {action} (intensity: {intensity})")
        
        elif emotion_type == "failure":
            self.recent_progress_feeling = max(-10, self.recent_progress_feeling - intensity)
            if action:
                current_negative = self.negative_reinforcement.get(action, 0)
                # EXTRA punishment for leftward actions that fail
                if "left" in action:
                    intensity = min(10, intensity * 1.5)  # 50% more negative for leftward fails
                    print(f"😡 AI feels EXTRA BAD about {action} (leftward penalty!)")
                self.negative_reinforcement[action] = min(10, current_negative + intensity)
                if "left" not in action:
                    print(f"😢 AI feels BAD about {action} (intensity: {intensity})")
        
        elif emotion_type == "stuck":
            self.recent_progress_feeling = max(-10, self.recent_progress_feeling - 1)
            print(f"😤 AI feels FRUSTRATED from being stuck")
        
        elif emotion_type == "rightward_progress":
            # Special emotion for making rightward progress
            self.recent_progress_feeling = min(10, self.recent_progress_feeling + intensity)
            print(f"🚀 AI feels AMAZING about moving RIGHT! (intensity: {intensity})")
    
    def get_position_key(self):
        """Convert current position to a discrete key for memory storage"""
        # Use smaller grid for more precise learning
        grid_x = int(self.player.rect.centerx // 30)  # Smaller grid = more precision
        grid_y = int(self.player.rect.centery // 30)
        
        # Include more context for better learning
        on_ground = self.player.on_ground
        moving_right = self.player.vel_x > 0
        
        return (grid_x, grid_y, on_ground, moving_right)
    
    def remember_success(self, position_key, action):
        """Remember that this action worked at this position"""
        self.success_memory[str(position_key)] = action
        print(f"✅ Learned: {action} works at position {position_key}")
    
    def remember_failure(self, position_key, action):
        """Remember that this action failed at this position"""
        pos_str = str(position_key)
        if pos_str not in self.failure_memory:
            self.failure_memory[pos_str] = []
        if action not in self.failure_memory[pos_str]:
            self.failure_memory[pos_str].append(action)
            print(f"❌ Learned: {action} fails at position {position_key}")
    
    def get_learned_action(self, position_key):
        """Get the learned successful action for this position, if any"""
        pos_str = str(position_key)
        return self.success_memory.get(pos_str)
    
    def is_action_known_failure(self, position_key, action):
        """Check if this action is known to fail at this position"""
        pos_str = str(position_key)
        failed_actions = self.failure_memory.get(pos_str, [])
        return action in failed_actions
    
    def update(self, dt):
        """Update learning AI logic with emotional processing"""
        if not self.learning_active:
            return
            
        self.jump_cooldown = max(0, self.jump_cooldown - dt)
        
        # Track progress and emotional state
        old_distance = self.current_distance
        self.current_distance = max(self.current_distance, self.player.rect.centerx)
        
        # Feel EXTRA good about rightward progress!
        if self.current_distance > old_distance:
            progress_amount = self.current_distance - old_distance
            if progress_amount > 20:  # Significant progress
                # Double happiness for rightward progress!
                happiness_intensity = min(5, progress_amount / 20)
                self.feel_emotion("rightward_progress", happiness_intensity)
                self.consecutive_failures = 0
                
                # Remember the last action that led to this progress as EXTRA good
                if len(self.action_history) > 0:
                    last_pos, last_action, _ = self.action_history[-1]
                    if "right" in last_action:
                        self.feel_emotion("success", 2, last_action)  # Extra boost for rightward success
        
        # Check if stuck and feel bad about it
        if abs(self.player.rect.x - self.last_x) < 3:
            self.stuck_timer += dt
            if self.stuck_timer > 3.0:  # Feel frustrated when stuck
                self.feel_emotion("stuck", 1)
        else:
            self.stuck_timer = 0.0
            self.last_x = self.player.rect.x
        
        # Make intelligent movement decision
        self.make_smart_decision()
        
        # Decay emotions over time (don't hold grudges forever)
        self.recent_progress_feeling *= 0.999
    
    def update_personal_best(self):
        """Update personal best distance and remember the route to get there"""
        current_x = self.player.rect.centerx
        
        if current_x > self.personal_best_distance:
            old_pb = self.personal_best_distance
            self.personal_best_distance = current_x
            
            # Save the successful route to this new PB!
            self.pb_route = self.action_history.copy()
            
            print(f"🏆 NEW PERSONAL BEST! Distance: {current_x:.0f} (was {old_pb:.0f})")
            print(f"📝 Remembered route with {len(self.pb_route)} actions to reach PB!")
            
            # Feel AMAZING about setting a new PB
            self.feel_emotion("success", 5)
            
            # Turn off recovery mode since we're now at a new PB
            self.pb_recovery_mode = False
            self.pb_route_index = 0
            
            return True
        
        return False
    
    def should_use_pb_recovery(self):
        """Determine if AI should try to recover to its PB using memory"""
        current_x = self.player.rect.centerx
        
        # Use PB recovery ONLY in more extreme situations - not as primary strategy!
        # 1. We're VERY far behind our PB (more than 200 pixels)
        # 2. We have a route to remember
        # 3. We're REALLY struggling (many failures AND bad feelings AND stuck)
        
        very_far_behind = current_x < (self.personal_best_distance - 200)  # Increased threshold
        has_route = len(self.pb_route) > 0
        really_struggling = (self.consecutive_failures > 5 and  # More failures required
                           self.recent_progress_feeling < -4 and  # More negative feelings required
                           self.stuck_timer > 4.0)  # Longer stuck time required
        
        # Add some randomness - don't always use PB recovery even when conditions are met
        random_exploration = random.random() < 0.3  # 30% chance to explore instead
        
        should_recover = very_far_behind and has_route and really_struggling and not random_exploration
        
        if should_recover:
            print(f"🆘 AI is REALLY struggling (far behind: {very_far_behind}, failures: {self.consecutive_failures}, feeling: {self.recent_progress_feeling:.1f}) - considering PB recovery")
        
        return should_recover
    
    def try_pb_recovery(self):
        """Try to follow the remembered route back to Personal Best with exploration mixed in"""
        if not self.pb_route or self.pb_route_index >= len(self.pb_route):
            # No route or finished route - exit recovery mode
            self.pb_recovery_mode = False
            self.pb_route_index = 0
            print("📍 PB recovery route completed - resuming exploration")
            return None
        
        # Add exploration even during PB recovery - don't follow route blindly!
        if random.random() < 0.25:  # 25% chance to explore instead of following route
            print("🎲 PB Recovery: Choosing to explore instead of following route")
            return None  # Return None to fall back to normal exploration
        
        # Get current position
        current_pos = self.get_position_key()
        
        # Try to find where we are in the PB route
        route_action = None
        found_position = False
        
        # Look for current position in the route (starting from current index)
        for i in range(self.pb_route_index, len(self.pb_route)):
            route_pos, route_action_for_pos, _ = self.pb_route[i]
            
            # Check if we're close to this route position
            route_grid_x, route_grid_y, _, _ = route_pos
            current_grid_x, current_grid_y, _, _ = current_pos
            
            # Allow some flexibility in position matching
            if (abs(route_grid_x - current_grid_x) <= 3 and  # More flexibility
                abs(route_grid_y - current_grid_y) <= 3):
                route_action = route_action_for_pos
                self.pb_route_index = i + 1
                found_position = True
                print(f"📍 PB Recovery: Found position in route, using action: {route_action}")
                break
        
        if not found_position:
            # Instead of trying to get back on track, just exit recovery and explore
            print("📍 PB Recovery: Position not found in route - switching to exploration")
            self.pb_recovery_mode = False
            self.pb_route_index = 0
            return None
        
        return route_action
    
    def is_at_pb_location(self):
        """Check if we're at or past our Personal Best location"""
        return self.player.rect.centerx >= (self.personal_best_distance - 50)
    
    def get_dynamic_exploration_rate(self):
        """Calculate exploration rate that starts high and decreases as AI learns"""
        # Start with high exploration (80%) and gradually decrease
        base_exploration = 80  # Start at 80% exploration
        
        # Reduce exploration based on knowledge gained
        knowledge_factor = len(self.success_memory) * 2  # Each success reduces exploration
        attempt_factor = self.attempt_count * 0.5  # Each attempt reduces exploration slightly
        
        # Calculate current exploration rate
        current_exploration = max(15, base_exploration - knowledge_factor - attempt_factor)
        
        # If AI is struggling (low success rate), increase exploration temporarily
        if self.attempt_count > 5:
            success_rate = (self.victories / self.attempt_count) * 100
            if success_rate < 10:  # If very low success rate, boost exploration
                current_exploration = min(60, current_exploration + 20)
        
        return current_exploration
    
    def is_making_good_progress(self):
        """Check if AI is making good vertical AND horizontal progress toward victory"""
        victory_x = self.victory_zone.centerx
        victory_y = self.victory_zone.centery
        
        current_x = self.player.rect.centerx
        current_y = self.player.rect.centery
        
        # Calculate progress toward victory (both horizontal and vertical)
        horizontal_progress = (current_x - 200) / (victory_x - 200)  # 0 to 1
        vertical_progress = (WORLD_HEIGHT - current_y) / (WORLD_HEIGHT - victory_y)  # 0 to 1
        
        # Good progress means making decent progress in BOTH dimensions
        return horizontal_progress > 0.1 and vertical_progress > 0.1
    
    def get_position_progress_score(self):
        """Get a score (0-100) for how close current position is to victory"""
        victory_x = self.victory_zone.centerx
        victory_y = self.victory_zone.centery
        
        current_x = self.player.rect.centerx
        current_y = self.player.rect.centery
        
        # Calculate progress in both dimensions
        horizontal_progress = max(0, min(1, (current_x - 200) / (victory_x - 200)))
        vertical_progress = max(0, min(1, (WORLD_HEIGHT - current_y) / (WORLD_HEIGHT - victory_y)))
        
        # Combined progress score (both dimensions are important!)
        combined_progress = (horizontal_progress + vertical_progress) / 2
        return combined_progress * 100
    
    def make_smart_decision(self):
        """Enhanced decision making with dynamic exploration and UP+RIGHT awareness"""
        # Update Personal Best if we've gone further
        new_pb = self.update_personal_best()
        
        # If we just set a new PB, feel extra good about exploration!
        if new_pb:
            self.feel_emotion("success", 3)
            print("🎉 New PB set - AI feels GREAT about exploring!")
        
        # Check if we should enter PB recovery mode (more restrictive now)
        if not self.pb_recovery_mode and self.should_use_pb_recovery():
            self.pb_recovery_mode = True
            self.pb_route_index = 0
            print(f"🔄 ENTERING PB RECOVERY MODE - trying to get back to {self.personal_best_distance:.0f}")
            self.feel_emotion("success", 1)  # Feel good about having a plan
        
        # Exit PB recovery mode if we've reached our PB area OR if we're making good progress exploring
        if self.pb_recovery_mode:
            if self.is_at_pb_location():
                self.pb_recovery_mode = False
                self.pb_route_index = 0
                print(f"🎯 REACHED PB AREA - resuming exploration from {self.player.rect.centerx:.0f}")
                self.feel_emotion("success", 3)  # Feel great about getting back to PB
            elif self.recent_progress_feeling > 0:  # If feeling good, exit recovery and explore
                self.pb_recovery_mode = False
                self.pb_route_index = 0
                print(f"😊 AI feeling good - exiting PB recovery to explore!")
                self.feel_emotion("success", 1)
        
        # Get current position for learning
        position_key = self.get_position_key()
        
        # Calculate dynamic exploration rate
        exploration_rate = self.get_dynamic_exploration_rate()
        
        # Decide on action with DYNAMIC EXPLORATION PRIORITY
        chosen_action = None
        
        # PRIORITY 1: Dynamic exploration (starts high, decreases with learning)
        exploration_chance = exploration_rate / 100
        if random.random() < exploration_chance:
            chosen_action = self.choose_exploration_action(position_key)
            print(f"🎲 Dynamic exploration ({exploration_rate:.1f}%): {chosen_action}")
        
        # PRIORITY 2: Use learned successful action for this position (increasing chance as we learn)
        exploitation_chance = min(0.8, 0.3 + (len(self.success_memory) * 0.01))  # Starts at 30%, increases with knowledge
        if not chosen_action and random.random() < exploitation_chance:
            learned_action = self.get_learned_action(position_key)
            if learned_action:
                chosen_action = learned_action
                print(f"🧠 Using learned action ({exploitation_chance*100:.1f}% chance): {chosen_action}")
        
        # PRIORITY 3: PB Recovery (only as fallback when really struggling)
        if not chosen_action and self.pb_recovery_mode:
            pb_action = self.try_pb_recovery()
            if pb_action:
                chosen_action = pb_action
                print(f"🔄 PB Recovery: Using {chosen_action}")
        
        # PRIORITY 4: Smart exploration (UP+RIGHT bias + emotions)
        if not chosen_action:
            chosen_action = self.choose_exploration_action(position_key)
        
        # Create keys dictionary and apply the chosen action
        keys = {
            pygame.K_LEFT: False, 
            pygame.K_RIGHT: False, 
            pygame.K_a: False,
            pygame.K_d: False,
            pygame.K_SPACE: False,
            pygame.K_UP: False,
            pygame.K_w: False
        }
        
        self.apply_action(keys, chosen_action)
        
        # CRITICAL FIX: Actually apply the keys to the player!
        self.player.handle_input(keys)
        
        # Remember this action in our history
        timestamp = self.attempt_count * 1000 + len(self.action_history)
        self.action_history.append((position_key, chosen_action, timestamp))
        
        # Limit action history size to prevent memory bloat
        if len(self.action_history) > 500:  # Keep last 500 actions
            self.action_history = self.action_history[-400:]  # Trim to 400
        
        # Auto-save every 10 actions
        self.actions_since_save += 1
        if self.actions_since_save >= 10:
            self.save_learning_data()
            self.actions_since_save = 0
    
    def choose_exploration_action(self, position_key):
        """Choose an action using logic and emotional learning with UP+RIGHT bias"""
        possible_actions = ["move_right", "move_left", "jump_right", "jump_left", "jump_only", "wait"]
        
        # Filter out known failures
        safe_actions = [action for action in possible_actions 
                       if not self.is_action_known_failure(position_key, action)]
        
        if not safe_actions:
            safe_actions = ["jump_right", "jump_only"]  # Always try jumping if everything else failed
        
        # PRIORITY SYSTEM: UP+RIGHT actions get massive preference!
        upward_rightward_actions = [a for a in safe_actions if "jump" in a and "right" in a]  # Best: up AND right
        rightward_actions = [a for a in safe_actions if "right" in a]  # Good: rightward
        upward_actions = [a for a in safe_actions if "jump" in a]  # OK: upward
        leftward_actions = [a for a in safe_actions if "left" in a]  # Bad: leftward  
        neutral_actions = [a for a in safe_actions if a in ["wait"]]  # Neutral
        
        # EMOTIONAL ACTION SELECTION - STRONGLY prefer actions that felt good!
        def get_emotional_score(action):
            positive_feeling = self.positive_reinforcement.get(action, 0)
            negative_feeling = self.negative_reinforcement.get(action, 0)
            emotional_score = positive_feeling - negative_feeling
            
            # MASSIVE bonuses for UP+RIGHT movement!
            if "jump" in action and "right" in action:
                emotional_score += 5  # +5 bonus for UP+RIGHT actions!
            elif "right" in action:
                emotional_score += 3  # +3 bonus for rightward actions
            elif "jump" in action:
                emotional_score += 2  # +2 bonus for upward actions
            elif "left" in action:
                emotional_score -= 2  # -2 penalty for leftward actions
                
            return emotional_score
        
        # Sort all actions by emotional preference
        all_actions_with_scores = [(action, get_emotional_score(action)) for action in safe_actions]
        all_actions_with_scores.sort(key=lambda x: x[1], reverse=True)  # Sort by score descending
        
        # Use the action with highest emotional score if it's positive
        best_action, best_score = all_actions_with_scores[0]
        if best_score > 2:  # If we have a strongly positive emotional association
            print(f"💭 AI chooses {best_action} based on STRONG POSITIVE FEELINGS (score: {best_score})")
            return best_action
        
        # LOGICAL ACTION SELECTION with UP+RIGHT PRIORITY and DYNAMIC EXPLORATION
        
        # Get progress toward victory to inform decisions
        progress_score = self.get_position_progress_score()
        victory_x = self.victory_zone.centerx
        victory_y = self.victory_zone.centery
        
        # ALWAYS prefer UP+RIGHT movement when possible!
        if upward_rightward_actions:
            if random.random() < 0.8:  # 80% chance to choose UP+RIGHT when available
                chosen = random.choice(upward_rightward_actions)
                print(f"🚀 AI chooses {chosen} - UP AND RIGHT toward victory!")
                return chosen
        
        # If not near victory zone, prioritize getting closer (UP+RIGHT)
        if self.player.rect.centerx < victory_x * 0.8 or self.player.rect.centery > victory_y * 1.2:
            # Prefer rightward movement if far horizontally
            if self.player.rect.centerx < victory_x * 0.8 and rightward_actions:
                if self.player.on_ground and "move_right" in rightward_actions and random.random() < 0.6:
                    print(f"🎯 AI chooses move_right - GOING TOWARD VICTORY!")
                    return "move_right"
                elif "jump_right" in rightward_actions:
                    print(f"🎯 AI chooses jump_right - UP AND RIGHT!")
                    return "jump_right"
            
            # Prefer upward movement if low vertically
            if self.player.rect.centery > victory_y * 1.2 and upward_actions:
                upward_action = random.choice(upward_actions)
                print(f"⬆️ AI chooses {upward_action} - GOING UP toward victory!")
                return upward_action
        
        # EXPLORATION BOOST: Sometimes try random UP+RIGHT actions
        exploration_rate = self.get_dynamic_exploration_rate()
        if random.random() < (exploration_rate / 100) * 0.5:  # Scale with exploration rate
            if upward_rightward_actions:
                chosen = random.choice(upward_rightward_actions)
                print(f"🔍 EXPLORATION: Trying {chosen} to discover UP+RIGHT paths!")
                return chosen
            elif rightward_actions:
                chosen = random.choice(rightward_actions)
                print(f"🔍 EXPLORATION: Trying {chosen} to discover rightward paths!")
                return chosen
        
        # If feeling frustrated, try aggressive UP+RIGHT actions
        if self.recent_progress_feeling < -3 or self.stuck_timer > 2.0:
            if upward_rightward_actions:
                aggressive_action = random.choice(upward_rightward_actions)
                print(f"😡 AI frustrated, trying aggressive UP+RIGHT: {aggressive_action}")
                return aggressive_action
            elif upward_actions:
                aggressive_action = random.choice(upward_actions)
                print(f"😡 AI frustrated, trying aggressive UPWARD: {aggressive_action}")
                return aggressive_action
        
        # If we're in the air, still prefer rightward movement when falling
        if not self.player.on_ground:
            if "move_right" in safe_actions and self.player.vel_y > 0:  # Falling
                print(f"🪂 AI chooses move_right while falling - TOWARD VICTORY!")
                return "move_right"
            elif "wait" in safe_actions:
                return "wait"  # Don't interfere with landing
        
        # If we haven't made much progress, encourage UP+RIGHT exploration
        if progress_score < 20:  # Still early in the game
            if upward_rightward_actions:
                chosen = random.choice(upward_rightward_actions)
                print(f"🚀 AI early game - {chosen} toward victory!")
                return chosen
            elif rightward_actions:
                chosen = random.choice(rightward_actions)
                print(f"🚀 AI early game - {chosen} toward victory!")
                return chosen
        
        # Priority order: UP+RIGHT > RIGHT > UP > NEUTRAL > LEFT
        if upward_rightward_actions:
            chosen = random.choice(upward_rightward_actions)
            print(f"🎯 AI defaults to UP+RIGHT: {chosen}")
            return chosen
        elif rightward_actions:
            chosen = random.choice(rightward_actions)
            print(f"🎯 AI defaults to rightward: {chosen}")
            return chosen
        elif upward_actions:
            chosen = random.choice(upward_actions)
            print(f"⬆️ AI defaults to upward: {chosen}")
            return chosen
        elif neutral_actions:
            return random.choice(neutral_actions)
        else:
            # Only use leftward as absolute last resort
            chosen = random.choice(leftward_actions) if leftward_actions else random.choice(safe_actions)
            print(f"😞 AI reluctantly chooses: {chosen} (no UP+RIGHT options)")
            return chosen
    
    def apply_action(self, keys, action):
        """Apply the chosen action to the key inputs"""
        if action == "move_right":
            keys[pygame.K_RIGHT] = True
            keys[pygame.K_d] = True
        elif action == "move_left":
            keys[pygame.K_LEFT] = True
            keys[pygame.K_a] = True
        elif action == "jump_right" and self.jump_cooldown <= 0:
            keys[pygame.K_RIGHT] = True
            keys[pygame.K_d] = True
            keys[pygame.K_SPACE] = True
            keys[pygame.K_UP] = True
            keys[pygame.K_w] = True
            self.jump_cooldown = 0.8
        elif action == "jump_left" and self.jump_cooldown <= 0:
            keys[pygame.K_LEFT] = True
            keys[pygame.K_a] = True
            keys[pygame.K_SPACE] = True
            keys[pygame.K_UP] = True
            keys[pygame.K_w] = True
            self.jump_cooldown = 0.8
        elif action == "jump_only" and self.jump_cooldown <= 0:
            keys[pygame.K_SPACE] = True
            keys[pygame.K_UP] = True
            keys[pygame.K_w] = True
            self.jump_cooldown = 0.8
        # "wait" does nothing - no keys pressed
    
    def on_death(self):
        """Called when AI dies - strong negative emotional learning"""
        self.attempt_count += 1
        self.consecutive_failures += 1
        
        # Feel REALLY bad about dying
        death_feeling_intensity = min(8, 3 + self.consecutive_failures)
        self.feel_emotion("failure", death_feeling_intensity)
        
        # Update best distance if improved
        if self.current_distance > self.best_distance:
            self.best_distance = self.current_distance
            print(f"🚀 NEW RECORD! Reached distance: {self.current_distance}")
            
            # Feel GREAT about making progress!
            progress_feeling = min(8, (self.current_distance - self.best_distance) / 100)
            self.feel_emotion("success", progress_feeling)
            
            # When we make progress, reinforce more of the successful sequence
            success_count = min(5, len(self.action_history) // 2)
            for i in range(success_count):
                if len(self.action_history) > i:
                    pos, action, _ = self.action_history[-(i+1)]
                    self.remember_success(pos, action)
                    self.feel_emotion("success", 1, action)  # Feel good about this action
        
        # Learn from failure - last few actions probably caused death
        failure_count = min(3, len(self.action_history))
        for i in range(failure_count):
            if len(self.action_history) > i:
                pos, action, _ = self.action_history[-(i+1)]
                self.remember_failure(pos, action)
                # Feel BAD about actions that led to death
                bad_feeling_intensity = 3 - i  # Earlier actions feel less bad
                self.feel_emotion("failure", bad_feeling_intensity, action)
        
        print(f"💀 Attempt #{self.attempt_count} ended. Distance: {self.current_distance}")
        print(f"🧠 Knowledge: {len(self.success_memory)} successes, {len(self.failure_memory)} failures")
        print(f"😊 Current mood: {self.recent_progress_feeling:.1f}/10")
        
        # Auto-save learning every 10 attempts
        if self.attempt_count % 10 == 0:
            self.save_learning_data()
            print(f"💾 Auto-saved after {self.attempt_count} attempts")
        
        # Reset for next attempt
        self.current_distance = 0
        self.action_history = []
        self.stuck_timer = 0.0
    
    def on_victory(self):
        """Called when AI reaches victory - MASSIVE positive emotional boost!"""
        self.victories += 1
        self.attempt_count += 1
        self.consecutive_failures = 0
        
        print(f"🏆 VICTORY #{self.victories}! Attempt #{self.attempt_count}")
        
        # Feel AMAZING about winning!
        self.feel_emotion("success", 10)  # Maximum positive feeling!
        
        # Learn from ALL actions in this successful attempt
        for pos, action, _ in self.action_history:
            self.remember_success(pos, action)
            self.feel_emotion("success", 2, action)  # All actions in winning run feel good
        
        # Reset for next attempt
        self.current_distance = 0
        self.action_history = []
        self.stuck_timer = 0.0
    
    def save_learning_data(self):
        """Save learning data and PB information to file"""
        try:
            data = {
                'success_memory': self.success_memory,
                'failure_memory': self.failure_memory,
                'positive_reinforcement': self.positive_reinforcement,
                'negative_reinforcement': self.negative_reinforcement,
                'attempt_count': self.attempt_count,
                'victories': self.victories,
                'best_distance': self.best_distance,
                'personal_best_distance': self.personal_best_distance,
                'pb_route': self.pb_route,  # Save the PB route!
                'recent_progress_feeling': self.recent_progress_feeling
            }
            
            with open('ai_learning_data.json', 'w') as f:
                json.dump(data, f, indent=2)
            print(f"💾 Learning data saved! PB: {self.personal_best_distance:.0f}, Route steps: {len(self.pb_route)}")
        except Exception as e:
            print(f"❌ Failed to save learning data: {e}")
    
    def load_learning_data(self):
        """Load learning data and PB information from file"""
        try:
            with open('ai_learning_data.json', 'r') as f:
                data = json.load(f)
            
            self.success_memory = data.get('success_memory', {})
            self.failure_memory = data.get('failure_memory', {})
            self.positive_reinforcement = data.get('positive_reinforcement', {})
            self.negative_reinforcement = data.get('negative_reinforcement', {})
            self.attempt_count = data.get('attempt_count', 0)
            self.victories = data.get('victories', 0)
            self.best_distance = data.get('best_distance', 200)
            self.personal_best_distance = data.get('personal_best_distance', 200)
            self.pb_route = data.get('pb_route', [])  # Load the PB route!
            self.recent_progress_feeling = data.get('recent_progress_feeling', 0)
            
            print(f"📖 Learning data loaded! PB: {self.personal_best_distance:.0f}, Route steps: {len(self.pb_route)}")
        except FileNotFoundError:
            print("📖 No previous learning data found - starting fresh")
        except Exception as e:
            print(f"❌ Failed to load learning data: {e}")
    
    def erase_learning_data(self):
        """Erase all learning data including PB information"""
        self.success_memory.clear()
        self.failure_memory.clear()
        self.positive_reinforcement.clear()
        self.negative_reinforcement.clear()
        self.action_history.clear()
        self.attempt_count = 0
        self.victories = 0
        self.best_distance = 200
        self.personal_best_distance = 200  # Reset PB
        self.pb_route.clear()  # Clear PB route
        self.pb_recovery_mode = False
        self.pb_route_index = 0
        self.recent_progress_feeling = 0
        self.consecutive_failures = 0
        
        # Delete the save file
        try:
            if os.path.exists('ai_learning_data.json'):
                os.remove('ai_learning_data.json')
        except:
            pass
        
        print("🧹 All learning data erased! PB reset to starting position.")
    
    def toggle_learning(self):
        """Start/stop the learning process"""
        self.learning_active = not self.learning_active
        status = "STARTED" if self.learning_active else "STOPPED"
        print(f"⏯️ Learning {status}")
        return self.learning_active
    
    def get_learning_stats(self):
        """Get learning statistics including PB information"""
        if self.attempt_count > 0:
            success_rate = (self.victories / self.attempt_count) * 100
        else:
            success_rate = 0.0
        
        total_emotions = len(self.positive_reinforcement) + len(self.negative_reinforcement)
        if total_emotions > 0:
            positive_ratio = len(self.positive_reinforcement) / total_emotions
        else:
            positive_ratio = 0.5
        
        emotional_score = self.recent_progress_feeling
        
        # Calculate dynamic exploration rate
        exploration_rate = self.get_dynamic_exploration_rate()
        
        return {
            'attempts': self.attempt_count,
            'victories': self.victories,
            'success_rate': success_rate,
            'best_distance': self.best_distance,
            'personal_best': self.personal_best_distance,  # Include PB
            'pb_route_length': len(self.pb_route),  # Include route info
            'exploration_rate': exploration_rate,  # Now dynamic!
            'emotional_score': emotional_score,
            'recovery_mode': self.pb_recovery_mode,  # Include recovery status
            'known_positions': len(self.success_memory),
            'failed_actions': sum(len(failures) for failures in self.failure_memory.values()),
            'positive_associations': len(self.positive_reinforcement),
            'negative_associations': len(self.negative_reinforcement)
        }

class DemoLevel:
    """Learning AI Demo that shows AI getting smarter over time"""
    
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
        
        # Create Learning AI controller
        self.ai = LearningAI(self.player, self.platforms, self.powerups, self.victory_zone)
        
        # Demo state
        self.demo_complete = False
        self.demo_timer = 0.0
        self.attempt_timer = 0.0
        
        # UI elements
        self.font_large = pygame.font.Font(None, 36)
        self.font_medium = pygame.font.Font(None, 28)
        self.font_small = pygame.font.Font(None, 22)
        
        # Control buttons state
        self.button_cooldown = 0.0
    
    def update(self, dt):
        """Update learning demo logic"""
        self.demo_timer += dt
        self.attempt_timer += dt
        self.button_cooldown = max(0, self.button_cooldown - dt)
        
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
            self.ai.on_victory()
            self.restart_attempt()
        
        # Check for death (restart learning attempt)
        elif self.player.rect.bottom >= WORLD_HEIGHT - GROUND_HEIGHT:
            self.ai.on_death()
            self.restart_attempt()
    
    def restart_attempt(self):
        """Restart the AI for a new learning attempt"""
        # Reset player position
        self.player.rect.x = 200
        self.player.rect.y = WORLD_HEIGHT - 200
        self.player.vel_x = 0
        self.player.vel_y = 0
        self.player.on_ground = False
        self.attempt_timer = 0.0
        
        # Reset platforms to initial state
        for platform in self.platforms:
            if hasattr(platform, 'is_solid'):
                platform.is_solid = True
            if hasattr(platform, 'activated'):
                platform.activated = False
    
    def handle_controls(self, keys_just_pressed):
        """Handle learning control inputs"""
        if self.button_cooldown > 0:
            return
        
        # S key: Save learning data
        if keys_just_pressed.get(pygame.K_s, False):
            self.ai.save_learning_data()
            self.button_cooldown = 0.5
        
        # P key: Pause/Continue learning
        elif keys_just_pressed.get(pygame.K_p, False):
            self.ai.toggle_learning()
            self.button_cooldown = 0.5
        
        # E key: Erase all learning data
        elif keys_just_pressed.get(pygame.K_e, False):
            self.ai.erase_learning_data()
            self.restart_attempt()
            self.button_cooldown = 0.5
        
        # R key: Restart current attempt
        elif keys_just_pressed.get(pygame.K_r, False):
            self.restart_attempt()
            self.button_cooldown = 0.5
    
    def draw_learning_ui(self):
        """Draw the learning AI status and controls"""
        if not self.ai:
            return
        
        # Get current stats
        stats = self.ai.get_learning_stats()
        
        # Learning status indicator - PROMINENT
        status_color = GREEN if self.ai.learning_active else RED
        status_text = "LEARNING: ACTIVE" if self.ai.learning_active else "LEARNING: PAUSED"
        status_surface = self.font_large.render(status_text, True, status_color)
        self.screen.blit(status_surface, (20, 20))
        
        # PB Recovery Mode indicator - NEW!
        if stats['recovery_mode']:
            recovery_text = f"🔄 PB RECOVERY MODE - Target: {stats['personal_best']:.0f}"
            recovery_surface = self.font_medium.render(recovery_text, True, YELLOW)
            self.screen.blit(recovery_surface, (20, 50))
            y_offset = 80
        else:
            y_offset = 50
        
        # Left column - Performance stats
        left_x = 20
        left_y = y_offset + 5
        progress_texts = [
            f"Attempt: #{stats['attempts'] + 1}",
            f"Victories: {stats['victories']}",
            f"Success Rate: {stats['success_rate']:.1f}%",
            f"Best Distance: {stats['best_distance']:.0f}",
            f"Personal Best: {stats['personal_best']:.0f} (Route: {stats['pb_route_length']} steps)"  # NEW!
        ]
        
        for i, text in enumerate(progress_texts):
            color = WHITE
            # Highlight PB if it's higher than best distance
            if "Personal Best" in text and stats['personal_best'] > stats['best_distance']:
                color = YELLOW
            
            rendered = self.font_small.render(text, True, color)
            self.screen.blit(rendered, (left_x, left_y + i * 25))
        
        # Right column - Current state
        right_x = SCREEN_WIDTH // 2 + 20
        right_y = y_offset + 5
        current_texts = [
            f"Current Distance: {self.ai.current_distance:.0f}",
            f"Known Positions: {stats['known_positions']}",
            f"Exploration: {stats['exploration_rate']:.1f}%",
            f"Positive Emotions: {stats['positive_associations']}",
            f"Recovery Mode: {'ON' if stats['recovery_mode'] else 'OFF'}"  # NEW!
        ]
        
        for i, text in enumerate(current_texts):
            color = WHITE
            # Highlight recovery mode status
            if "Recovery Mode: ON" in text:
                color = YELLOW
            elif "Recovery Mode: OFF" in text:
                color = GREEN
            
            rendered = self.font_small.render(text, True, color)
            self.screen.blit(rendered, (right_x, right_y + i * 25))
        
        # Emotional state display - more prominent
        emotion_text = f"Feeling: {stats['emotional_score']:.1f}/10"
        emotion_color = WHITE
        emotional_score = stats['emotional_score']
        
        if emotional_score > 3:
            emotion_color = GREEN
            mood_emoji = "😄"
        elif emotional_score > 0:
            emotion_color = LIGHT_GRAY  
            mood_emoji = "😊"
        elif emotional_score > -3:
            emotion_color = GRAY
            mood_emoji = "😐"
        elif emotional_score > -6:
            emotion_color = ORANGE
            mood_emoji = "😞"
        else:
            emotion_color = RED
            mood_emoji = "😡"
            
        full_emotion_text = f"{mood_emoji} {emotion_text}"
        emotion_surface = self.font_medium.render(full_emotion_text, True, emotion_color)
        self.screen.blit(emotion_surface, (SCREEN_WIDTH // 2 + 20, y_offset + 130))
        
        # Learning progress bar
        if stats['attempts'] > 0:
            progress_width = 300
            progress_height = 20
            progress_x = 20
            progress_y = y_offset + 160
            
            # Background
            pygame.draw.rect(self.screen, DARK_GRAY, (progress_x, progress_y, progress_width, progress_height))
            
            # Progress fill based on success rate
            success_rate = stats['success_rate']
            fill_width = int((success_rate / 100) * progress_width)
            
            # Color based on emotional state
            if emotional_score > 3:
                fill_color = GREEN
            elif emotional_score > 0:
                fill_color = LIGHT_GRAY
            elif emotional_score > -3:
                fill_color = YELLOW
            else:
                fill_color = RED
            
            if fill_width > 0:
                pygame.draw.rect(self.screen, fill_color, (progress_x, progress_y, fill_width, progress_height))
            
            # Border
            pygame.draw.rect(self.screen, WHITE, (progress_x, progress_y, progress_width, progress_height), 2)
            
            # Progress text with emotional context and PB info
            if stats['recovery_mode']:
                progress_text = f"PB Recovery: Returning to {stats['personal_best']:.0f}"
                progress_color = YELLOW
            elif emotional_score > 3:
                progress_text = f"Learning Progress: {stats['success_rate']:.1f}% (AI is happy!)"
                progress_color = GREEN
            elif emotional_score < -3:
                progress_text = f"Learning Progress: {stats['success_rate']:.1f}% (AI is struggling)"
                progress_color = RED
            else:
                progress_text = f"Learning Progress: {stats['success_rate']:.1f}%"
                progress_color = WHITE
            
            rendered = self.font_small.render(progress_text, True, progress_color)
            self.screen.blit(rendered, (progress_x, progress_y + progress_height + 5))
        
        # Controls - bottom of screen
        controls_y = SCREEN_HEIGHT - 120
        controls = [
            "Controls:",
            "P: Toggle Learning ON/OFF",
            "S: Save Learning Data", 
            "E: Erase All Learning Data",
            "R: Restart Current Attempt",
            "ESC: Exit Demo"
        ]
        
        for i, control in enumerate(controls):
            color = YELLOW if i == 0 else WHITE
            if i == 0:
                font = self.font_medium
            else:
                font = self.font_small
            rendered = font.render(control, True, color)
            self.screen.blit(rendered, (20, controls_y + i * 20))
    
    def draw_background(self):
        """Draw themed background"""
        self.screen.fill(self.theme['bg_color'])
    
    def draw(self, camera):
        """Draw the learning demo level"""
        # Draw background
        self.draw_background()
        
        # Draw all sprites with camera offset
        for sprite in self.all_sprites:
            sprite_rect = camera.apply(sprite.rect)
            self.screen.blit(sprite.image, sprite_rect)
        
        # Draw learning UI on top
        self.draw_learning_ui()
    
    def is_complete(self):
        """Check if demo should end"""
        return self.demo_complete
    
    def should_restart(self, keys_just_pressed):
        """Check if demo should restart"""
        # Handle learning controls instead
        self.handle_controls(keys_just_pressed)
        return False  # Let learning AI handle its own restarts
    
    def should_exit(self, keys_just_pressed):
        """Check if should exit demo"""
        return keys_just_pressed.get(pygame.K_ESCAPE, False) 

    def is_near_platform_edge(self):
        """Check if player is near the edge of a platform"""
        for platform in self.platforms:
            if (self.player.rect.bottom <= platform.rect.top + 10 and
                self.player.rect.bottom >= platform.rect.top - 10):
                # Check if near right edge
                if (self.player.rect.right >= platform.rect.right - 20 and
                    self.player.rect.right <= platform.rect.right + 10):
                    return True
        return False 