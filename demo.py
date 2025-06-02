import pygame
import math
import random
import json
import os
from settings import *
from player import Player
from powerups import PowerUp

class LearningAI:
    """Learning AI that gets smarter over time by remembering what works"""
    
    def __init__(self, player, platforms, powerups, victory_zone):
        self.player = player
        self.platforms = platforms
        self.powerups = powerups
        self.victory_zone = victory_zone
        
        # Learning memory system
        self.success_memory = {}  # position -> {action: success_count}
        self.failure_memory = {}  # position -> {action: failure_count}
        
        # Emotional memory system
        self.positive_reinforcement = {}  # action -> positive feeling score
        self.negative_reinforcement = {}  # action -> negative feeling score
        self.recent_progress_feeling = 0  # -10 (very bad) to +10 (very good)
        
        # Personal Best (PB) System
        self.personal_best_distance = 0  # Furthest distance reached
        self.pb_route = []  # List of actions that led to PB
        self.pb_recovery_mode = False  # Are we trying to get back to PB?
        self.pb_route_index = 0  # Where we are in replaying the PB route
        self.manual_pb_override = False  # Manual override to force PB recovery
        
        # Game knowledge and position tracking
        self.game_knowledge = {
            "goal": "reach victory zone at (6400, WORLD_HEIGHT - 3300)",
            "rule_1": "ALWAYS MOVE RIGHT TO WIN - right = progress toward victory",
            "rule_2": "UP+RIGHT movement is BEST - gets closer to top-right victory zone",
            "rule_3": "avoid falling to ground (WORLD_HEIGHT - GROUND_HEIGHT) = death",
            "rule_4": "victory zone is TOP-RIGHT corner of world",
            "platforms": {
                "normal": "regular platforms for standing/jumping",
                "moving_blue": "blue bordered platforms that slide back and forth",
                "bouncy_orange": "orange platforms give extra jump height", 
                "disappearing": "platforms that fade away after being stepped on",
                "oneway_yellow": "yellow platforms can be jumped through from below",
                "ice_light_blue": "light blue slippery platforms with reduced friction",
                "rotating_purple": "purple circular platforms that slowly rotate",
                "elevator_green": "green platforms that move up and down automatically"
            },
            "powerups": {
                "jump_boost": "green crystals give temporary higher jumps for 10 seconds"
            }
        }
        
        # Statistics
        self.attempts = 0
        self.victories = 0
        self.total_deaths = 0
        self.learning_active = True
        
        # Decision tracking
        self.last_position = None
        self.last_action = None
        self.stuck_timer = 0.0
        self.last_distance = 0
        
        # Try to load existing learning data
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
        print(f"💀 DEATH: {self.game_knowledge['rule_3']}")
        print(f"🏆 VICTORY: {self.game_knowledge['rule_4']}")
        print(f"🎮 MOVEMENT: {self.game_knowledge['rule_1']}")
        print(f"⬆️ JUMPING: {self.game_knowledge['rule_2']}")
        
        print("\n📋 PLATFORM TYPES:")
        for platform_type, description in self.game_knowledge['platforms'].items():
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
        pos_str = str(position_key)
        if pos_str not in self.success_memory:
            self.success_memory[pos_str] = {}
        if action not in self.success_memory[pos_str]:
            self.success_memory[pos_str][action] = 0
        self.success_memory[pos_str][action] += 1
        print(f"✅ Learned: {action} works at position {position_key}")
    
    def remember_failure(self, position_key, action):
        """Remember that this action failed at this position"""
        pos_str = str(position_key)
        if pos_str not in self.failure_memory:
            self.failure_memory[pos_str] = {}
        if action not in self.failure_memory[pos_str]:
            self.failure_memory[pos_str][action] = 0
        self.failure_memory[pos_str][action] += 1
        print(f"❌ Learned: {action} fails at position {position_key}")
    
    def get_learned_action(self, position_key):
        """Get the learned successful action for this position, if any"""
        pos_str = str(position_key)
        return self.success_memory.get(pos_str)
    
    def is_action_known_failure(self, position_key, action):
        """Check if this action is known to fail at this position"""
        pos_str = str(position_key)
        failed_actions = self.failure_memory.get(pos_str, {})
        return action in failed_actions
    
    def update(self, dt):
        """Update AI learning and control"""
        if not self.learning_active:
            return
        
        # Update personal best tracking
        self.update_personal_best()
        
        # Track emotional state for decision making
        anger_level = max(0, -self.recent_progress_feeling)  # 0 to 10, higher = more angry
        happiness_level = max(0, self.recent_progress_feeling)  # 0 to 10, higher = more happy
        
        # Log emotional state periodically
        if self.attempts % 5 == 0 and self.attempts > 0:
            if anger_level > 3:
                print(f"😤 AI Emotional State: ANGRY ({anger_level:.1f}/10)")
            elif happiness_level > 3:
                print(f"😊 AI Emotional State: HAPPY ({happiness_level:.1f}/10)")
            else:
                print(f"😐 AI Emotional State: NEUTRAL (feeling: {self.recent_progress_feeling:.1f})")
        
        # Make smart decision based on new logic
        chosen_action = self.make_smart_decision()
        
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
        
        # CRITICAL: Actually apply the keys to the player
        self.player.handle_input(keys)
        
        # Update player (this handles collision with platforms)
        self.player.update(self.platforms)
        
        # Track progress and emotional state
        old_distance = self.last_distance
        self.last_distance = self.player.rect.centerx
        
        # Feel EXTRA good about rightward progress!
        if self.last_distance > old_distance:
            progress_amount = self.last_distance - old_distance
            if progress_amount > 20:  # Significant progress
                # Double happiness for rightward progress!
                happiness_intensity = min(5, progress_amount / 20)
                self.feel_emotion("rightward_progress", happiness_intensity)
                
                # Remember the last action that led to this progress as EXTRA good
                if self.last_action:
                    self.feel_emotion("success", 2, self.last_action)  # Extra boost for rightward success
        
        # Check if stuck and feel bad about it
        if self.last_position and abs(self.player.rect.x - self.last_position[0]) < 3:
            self.stuck_timer += dt
            if self.stuck_timer > 3.0:  # Feel frustrated when stuck
                self.feel_emotion("stuck", 1)
        else:
            self.stuck_timer = 0.0
            self.last_position = (self.player.rect.x, self.player.rect.y)
        
        # Update moving platforms and other dynamic elements
        for platform in self.platforms:
            platform.update(dt)
        
        # Update power-ups
        for powerup in self.powerups:
            powerup.update(dt)
        
        # Check for power-up collection
        collected = pygame.sprite.spritecollide(self.player, self.powerups, False)
        for powerup in collected:
            if not powerup.collected:
                powerup.collect()
                if powerup.powerup_type == "jump_boost":
                    self.player.add_powerup("jump_boost", 10.0)
                self.powerups.remove(powerup)
        
        # Check for death/victory
        if self.player.rect.bottom >= WORLD_HEIGHT - GROUND_HEIGHT:
            self.on_death()
        elif self.victory_zone.colliderect(self.player.rect):
            self.on_victory()
        
        # Count attempts when we actually make decisions
        if chosen_action != "wait":  # Only count when we actually made a decision
            self.attempts += 1
        
        # Auto-save every 10 attempts
        if self.attempts % 10 == 0 and self.attempts > 0:
            self.save_learning_data()
    
    def update_personal_best(self):
        """Update personal best distance and remember the route to get there"""
        current_x = self.player.rect.centerx
        
        if current_x > self.personal_best_distance:
            old_pb = self.personal_best_distance
            self.personal_best_distance = current_x
            
            # FIXED: pb_route should be a list, not a single action
            # For now, we'll build up the route over time rather than storing just the last action
            if self.last_action:
                # Add current action to the growing route
                current_pos = self.get_position_key()
                self.pb_route.append((current_pos, self.last_action, current_x))
            
            print(f"🏆 NEW PERSONAL BEST! Distance: {current_x:.0f} (was {old_pb:.0f})")
            print(f"📝 Route now has {len(self.pb_route)} steps to reach PB!")
            
            # Feel AMAZING about setting a new PB
            self.feel_emotion("success", 5)
            
            # Turn off recovery mode since we're now at a new PB
            self.pb_recovery_mode = False
            self.pb_route_index = 0
            
            return True
        else:
            # Still building route - add current action to route
            if self.last_action:
                current_pos = self.get_position_key()
                self.pb_route.append((current_pos, self.last_action, current_x))
        
        return False
    
    def should_use_pb_recovery(self):
        """Determine if AI should try to get back to its Personal Best (MORE RESTRICTIVE)"""
        current_x = self.player.rect.centerx
        
        # More restrictive conditions for PB recovery
        very_far_behind = current_x < (self.personal_best_distance - 200)  # Increased threshold
        has_route = len(self.pb_route) > 0
        really_struggling = (self.stuck_timer > 4.0)  # Longer stuck time required
        
        # Add some randomness - don't always use PB recovery even when conditions are met
        random_factor = random.random() < 0.6  # Only 60% chance when conditions are met
        
        should_recover = (very_far_behind and has_route and really_struggling and random_factor)
        
        if should_recover:
            print(f"🆘 AI is REALLY struggling (far behind: {very_far_behind}, feeling: {self.recent_progress_feeling:.1f}) - considering PB recovery")
        
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
            if (abs(route_grid_x - current_grid_x) <= 3 and 
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
        attempt_factor = self.attempts * 0.5  # Each attempt reduces exploration slightly
        
        # Calculate current exploration rate
        current_exploration = max(15, base_exploration - knowledge_factor - attempt_factor)
        
        # If AI is struggling (low success rate), increase exploration temporarily
        if self.attempts > 5:
            success_rate = (self.victories / self.attempts) * 100
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
        """Enhanced decision making: Mad = stick to PB route, Happy = explore new paths"""
        if not self.learning_active:
            return "wait"
        
        position_key = self.get_position_key()
        current_x = self.player.rect.centerx
        
        # Calculate emotional state for decision making
        anger_level = max(0, -self.recent_progress_feeling)  # 0 to 10, higher = more angry
        happiness_level = max(0, self.recent_progress_feeling)  # 0 to 10, higher = more happy
        
        # Are we at or near our Personal Best location?
        at_pb_location = current_x >= (self.personal_best_distance - 100)
        far_from_pb = current_x < (self.personal_best_distance - 300)
        
        # MANUAL OVERRIDE SYSTEM - Force PB recovery when requested
        if self.manual_pb_override:
            if len(self.pb_route) > 0:
                if not self.pb_recovery_mode:
                    self.pb_recovery_mode = True
                    self.pb_route_index = 0
                    print(f"🎯 MANUAL OVERRIDE: Starting PB recovery to {self.personal_best_distance:.0f}")
                
                recovery_action = self.try_pb_recovery()
                if recovery_action:
                    print(f"🎯 MANUAL OVERRIDE: Following PB route - {recovery_action}")
                    return recovery_action
                else:
                    # Reached end of PB route or got stuck
                    self.manual_pb_override = False
                    self.pb_recovery_mode = False
                    print("🎯 MANUAL OVERRIDE COMPLETE: Now at PB location")
            else:
                # No PB route available, disable override
                self.manual_pb_override = False
                print("❌ Manual override disabled - no PB route to follow")
        
        # NEW LOGIC: MAD = stick to PB route, HAPPY = explore
        
        # ANGRY/FRUSTRATED AI - Stick to what worked before!
        if anger_level > 4:  # Moderately frustrated or worse
            if len(self.pb_route) > 0 and far_from_pb:
                if not self.pb_recovery_mode:
                    self.pb_recovery_mode = True
                    self.pb_route_index = 0
                    print(f"😤 AI IS FRUSTRATED (anger: {anger_level:.1f}) - Going back to reliable PB route!")
                
                recovery_action = self.try_pb_recovery()
                if recovery_action:
                    print(f"😤 FRUSTRATED: Following proven route - {recovery_action}")
                    return recovery_action
                else:
                    # Finished PB route, now explore carefully
                    self.pb_recovery_mode = False
                    print(f"😤 Reached PB via route, now exploring carefully (anger: {anger_level:.1f})")
            else:
                print(f"😤 AI frustrated (anger: {anger_level:.1f}) but no good route to follow")
        
        # HAPPY/SUCCESSFUL AI - Explore new possibilities!
        elif happiness_level > 3 or at_pb_location:
            # Disable any PB recovery mode - we're feeling good!
            if self.pb_recovery_mode:
                self.pb_recovery_mode = False
                print(f"😊 AI feeling good (happiness: {happiness_level:.1f}) - disabling PB recovery")
            
            # At PB location or feeling happy = maximum exploration!
            if at_pb_location:
                print(f"🎉 AI at/near PB location - MAXIMUM EXPLORATION to find new paths!")
                return self.choose_exploration_action(position_key, exploration_boost=0.8)  # 80% exploration
            else:
                print(f"😊 AI feeling happy (happiness: {happiness_level:.1f}) - exploring with confidence!")
                return self.choose_exploration_action(position_key, exploration_boost=0.4)  # 40% exploration
        
        # NEUTRAL AI - Balanced approach
        else:
            print(f"😐 AI feeling neutral - balanced exploration")
            return self.choose_exploration_action(position_key, exploration_boost=0.2)  # 20% exploration
    
    def choose_exploration_action(self, position_key, exploration_boost=0.2):
        """Choose an action using logic and emotional learning with UP+RIGHT bias and exploration boost"""
        possible_actions = ["move_right", "move_left", "jump_right", "jump_left", "jump_only", "wait"]
        
        # Filter out known failures
        safe_actions = [action for action in possible_actions 
                       if not self.is_action_known_failure(position_key, action)]
        
        if not safe_actions:
            safe_actions = ["jump_right", "jump_only"]  # Always try jumping if everything else failed
        
        # EXPLORATION MODE - Use the exploration boost to determine randomness level
        exploration_rate = self.get_dynamic_exploration_rate()
        total_exploration_chance = min(0.9, (exploration_rate / 100) + exploration_boost)
        
        if random.random() < total_exploration_chance:
            # EXPLORATION: Try random actions, heavily biased toward UP+RIGHT
            upright_actions = [a for a in safe_actions if "right" in a or "jump" in a]
            
            if upright_actions and random.random() < 0.7:  # 70% chance for UP+RIGHT bias
                chosen_action = random.choice(upright_actions)
                print(f"🎲 EXPLORING (boost: {exploration_boost:.1f}): Trying UP+RIGHT action: {chosen_action}")
            else:
                # Sometimes try other actions for variety
                chosen_action = random.choice(safe_actions)
                print(f"🎲 EXPLORING (boost: {exploration_boost:.1f}): Trying action: {chosen_action}")
            
            return chosen_action
        
        # LEARNED BEHAVIOR: Use emotional intelligence and knowledge
        learned_actions = self.get_learned_action(position_key)
        
        if learned_actions:
            # Use emotional scoring to pick the best learned action
            def get_emotional_score(action):
                positive_score = self.positive_reinforcement.get(action, 0)
                negative_score = self.negative_reinforcement.get(action, 0)
                learned_success_count = learned_actions.get(action, 0)
                
                # Base score from learning
                base_score = learned_success_count * 10
                
                # Emotional modifiers
                emotional_modifier = positive_score - negative_score
                
                # STRONG UP+RIGHT bias - extra points for good directions
                direction_bonus = 0
                if "right" in action and "jump" in action:
                    direction_bonus = 50  # UP+RIGHT = best!
                elif "right" in action:
                    direction_bonus = 30  # RIGHT = good
                elif "jump" in action:
                    direction_bonus = 20  # UP = decent
                elif "left" in action:
                    direction_bonus = -20  # LEFT = bad direction
                
                total_score = base_score + emotional_modifier + direction_bonus
                return total_score
            
            # Find the best action based on emotional learning
            best_action = None
            best_score = float('-inf')
            
            for action in learned_actions:
                if action in safe_actions:  # Only consider safe actions
                    score = get_emotional_score(action)
                    if score > best_score:
                        best_score = score
                        best_action = action
            
            if best_action:
                print(f"🧠 LEARNED BEHAVIOR: Using proven action: {best_action} (score: {best_score:.1f})")
                return best_action
        
        # FALLBACK: No learned behavior, prefer UP+RIGHT actions
        upright_actions = [a for a in safe_actions if "right" in a or "jump" in a]
        if upright_actions:
            chosen_action = random.choice(upright_actions)
            print(f"⬆️➡️ FALLBACK: Choosing UP+RIGHT action: {chosen_action}")
        else:
            chosen_action = random.choice(safe_actions)
            print(f"🤷 FALLBACK: Random safe action: {chosen_action}")
        
        return chosen_action
    
    def apply_action(self, keys, action):
        """Apply an action to the keys dictionary"""
        if action == "move_right":
            keys[pygame.K_RIGHT] = True
            keys[pygame.K_d] = True
        elif action == "move_left":
            keys[pygame.K_LEFT] = True
            keys[pygame.K_a] = True
        elif action == "jump_right":
            keys[pygame.K_RIGHT] = True
            keys[pygame.K_d] = True
            keys[pygame.K_SPACE] = True
            keys[pygame.K_UP] = True
            keys[pygame.K_w] = True
        elif action == "jump_left":
            keys[pygame.K_LEFT] = True
            keys[pygame.K_a] = True
            keys[pygame.K_SPACE] = True
            keys[pygame.K_UP] = True
            keys[pygame.K_w] = True
        elif action == "jump_only":
            keys[pygame.K_SPACE] = True
            keys[pygame.K_UP] = True
            keys[pygame.K_w] = True
        # "wait" does nothing - no keys pressed
    
    def on_death(self):
        """Called when AI dies - strong negative emotional learning"""
        self.attempts += 1
        self.total_deaths += 1
        
        # Feel REALLY bad about dying
        death_feeling_intensity = min(8, 3 + self.total_deaths)
        self.feel_emotion("failure", death_feeling_intensity)
        
        # Check if we made progress (FIXED LOGIC)
        if self.last_distance > self.personal_best_distance:
            old_personal_best = self.personal_best_distance  # Save old value BEFORE updating
            self.personal_best_distance = self.last_distance  # Update to new best
            print(f"🚀 NEW RECORD! Reached distance: {self.last_distance}")
            
            # Feel GREAT about making progress! (Use old value for calculation)
            progress_feeling = min(8, (self.last_distance - old_personal_best) / 100)
            self.feel_emotion("success", progress_feeling)
            
            # When we make progress, reinforce more of the successful sequence
            success_count = min(5, len(self.pb_route) // 2)
            for i in range(success_count):
                if len(self.pb_route) > i:
                    # pb_route contains (position, action, distance) tuples
                    pos, action, distance = self.pb_route[-(i+1)]  # Get from the end (most recent)
                    self.remember_success(pos, action)
                    self.feel_emotion("success", 1, action)  # Feel good about this action
        
        # Learn from failure - last few actions probably caused death
        failure_count = min(3, len(self.pb_route))
        for i in range(failure_count):
            if len(self.pb_route) > i:
                # pb_route contains (position, action, distance) tuples
                pos, action, distance = self.pb_route[-(i+1)]  # Get from the end (most recent)
                self.remember_failure(pos, action)
                # Feel BAD about actions that led to death
                bad_feeling_intensity = 3 - i  # Earlier actions feel less bad
                self.feel_emotion("failure", bad_feeling_intensity, action)
        
        print(f"💀 Attempt #{self.attempts} ended. Distance: {self.last_distance}")
        print(f"🧠 Knowledge: {len(self.success_memory)} successes, {len(self.failure_memory)} failures")
        print(f"😊 Current mood: {self.recent_progress_feeling:.1f}/10")
        
        # Auto-save learning every 10 attempts
        if self.attempts % 10 == 0:
            self.save_learning_data()
            print(f"💾 Auto-saved after {self.attempts} attempts")
        
        # Reset for next attempt
        self.last_distance = 0
        self.pb_route = []
        self.stuck_timer = 0.0
    
    def on_victory(self):
        """Called when AI reaches victory - MASSIVE positive emotional boost!"""
        self.victories += 1
        self.attempts += 1
        self.total_deaths = 0
        
        print(f"🏆 VICTORY #{self.victories}! Attempt #{self.attempts}")
        
        # Feel AMAZING about winning!
        self.feel_emotion("success", 10)  # Maximum positive feeling!
        
        # Learn from ALL actions in this successful attempt
        for pos, action in self.pb_route:
            self.remember_success(pos, action)
            self.feel_emotion("success", 2, action)  # All actions in winning run feel good
        
        # Reset for next attempt
        self.last_distance = 0
        self.pb_route = []
        self.stuck_timer = 0.0
    
    def save_learning_data(self):
        """Save learning data and PB information to file"""
        try:
            data = {
                'success_memory': self.success_memory,
                'failure_memory': self.failure_memory,
                'positive_reinforcement': self.positive_reinforcement,
                'negative_reinforcement': self.negative_reinforcement,
                'attempts': self.attempts,
                'victories': self.victories,
                'total_deaths': self.total_deaths,
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
            self.attempts = data.get('attempts', 0)
            self.victories = data.get('victories', 0)
            self.total_deaths = data.get('total_deaths', 0)
            self.personal_best_distance = data.get('personal_best_distance', 0)
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
        self.pb_route.clear()
        self.personal_best_distance = 0
        self.recent_progress_feeling = 0
        self.attempts = 0
        self.victories = 0
        self.total_deaths = 0
        
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
        if self.attempts > 0:
            success_rate = (self.victories / self.attempts) * 100
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
            'attempts': self.attempts,
            'victories': self.victories,
            'total_deaths': self.total_deaths,
            'success_rate': success_rate,
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
        """Handle manual learning controls"""
        if keys_just_pressed.get(pygame.K_s, False):
            self.ai.save_learning_data()
            print("💾 Learning data saved manually!")
            
        elif keys_just_pressed.get(pygame.K_p, False):
            self.ai.toggle_learning()
            status = "ACTIVE" if self.ai.learning_active else "PAUSED"
            print(f"🧠 Learning {status}")
            
        elif keys_just_pressed.get(pygame.K_e, False):
            self.ai.erase_learning_data()
            print("🗑️ All learning data erased!")
            
        elif keys_just_pressed.get(pygame.K_r, False):
            # Restart current attempt
            self.restart_attempt()
            print("🔄 Attempt restarted!")
            
        elif keys_just_pressed.get(pygame.K_b, False):
            # Manual override - force AI to go to Personal Best
            if self.ai.personal_best_distance > 0:
                self.ai.manual_pb_override = True
                self.ai.pb_recovery_mode = True
                self.ai.pb_route_index = 0
                print(f"🎯 MANUAL OVERRIDE: Forcing AI to go to Personal Best ({self.ai.personal_best_distance:.0f})")
            else:
                print("❌ No Personal Best recorded yet!")
    
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
        
        # NEW: Emotional mode indicator
        anger_level = max(0, -self.ai.recent_progress_feeling)
        happiness_level = max(0, self.ai.recent_progress_feeling)
        current_x = self.ai.player.rect.centerx
        at_pb_location = current_x >= (self.ai.personal_best_distance - 100)
        
        # Determine AI mode based on emotional state
        if self.ai.manual_pb_override:
            mode_status = "🎯 MANUAL OVERRIDE: Following PB Route"
            mode_color = YELLOW
        elif anger_level > 4:
            mode_status = f"😤 FRUSTRATED: Following reliable PB route (anger: {anger_level:.1f})"
            mode_color = (255, 100, 100)  # Light red
        elif happiness_level > 3 or at_pb_location:
            if at_pb_location:
                mode_status = f"🎉 AT PB: Maximum exploration for new paths!"
                mode_color = (100, 255, 100)  # Bright green
            else:
                mode_status = f"😊 HAPPY: Confident exploration (happiness: {happiness_level:.1f})"
                mode_color = (150, 255, 150)  # Light green
        else:
            mode_status = f"😐 NEUTRAL: Balanced approach"
            mode_color = WHITE
        
        # Display the mode
        mode_surface = self.font_medium.render(mode_status, True, mode_color)
        self.screen.blit(mode_surface, (20, 50))
        
        # PB Recovery Mode indicator - UPDATED
        if stats['recovery_mode']:
            recovery_text = f"🔄 PB RECOVERY ACTIVE - Target: {stats['personal_best']:.0f}"
            recovery_surface = self.font_small.render(recovery_text, True, YELLOW)
            self.screen.blit(recovery_surface, (20, 75))
            y_offset = 100
        else:
            y_offset = 80
        
        # Left column - Performance stats
        left_x = 20
        left_y = y_offset + 5
        progress_texts = [
            f"Attempt: #{stats['attempts'] + 1}",
            f"Victories: {stats['victories']}",
            f"Success Rate: {stats['success_rate']:.1f}%",
            f"Best Distance: {stats['personal_best']:.0f}",
            f"Total Deaths: {stats['total_deaths']}"
        ]
        
        for i, text in enumerate(progress_texts):
            color = WHITE
            # Highlight PB if it's improved recently (remove the impossible comparison)
            if "Best Distance" in text and stats['personal_best'] > 0:
                color = YELLOW  # Always highlight if we have a personal best
            
            rendered = self.font_small.render(text, True, color)
            self.screen.blit(rendered, (left_x, left_y + i * 25))
        
        # Right column - Current state
        right_x = SCREEN_WIDTH // 2 + 20
        right_y = y_offset + 5
        current_texts = [
            f"Current Distance: {self.ai.last_distance:.0f}",
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
        
        # Learning controls
        control_instructions = [
            "Learning Controls:",
            "S: Save Learning Data",
            "P: Pause/Resume Learning", 
            "E: Erase All Learning Data",
            "R: Restart Current Attempt",
            "B: Force Go to Personal Best",
            "ESC: Exit Demo"
        ]
        
        for i, instruction in enumerate(control_instructions):
            color = WHITE if i > 0 else self.theme['glow_color']
            if i == 0:  # Title
                text = self.font_medium.render(instruction, True, color)
            else:  # Instructions
                text = self.font_small.render(instruction, True, color)
            y_pos = SCREEN_HEIGHT - 180 + (i * 20)
            self.screen.blit(text, (20, y_pos))
    
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