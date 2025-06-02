import pygame
import math
import random
import json
import os
import time
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
        
        # NEW: Enhanced learning with confidence tracking
        self.action_attempts = {}  # position -> {action: attempt_count}
        self.state_visit_count = {}  # position -> total_visits
        
        # Emotional memory system
        self.positive_reinforcement = {}  # action -> positive feeling score
        self.negative_reinforcement = {}  # action -> negative feeling score
        self.recent_progress_feeling = 0  # -10 (very bad) to +10 (very good)
        
        # Personal Best (PB) System
        self.personal_best_distance = 0
        self.pb_route = []  # List of (position, action, distance) tuples
        self.pb_recovery_mode = False
        self.pb_route_index = 0
        
        # Manual override system
        self.manual_pb_override = False
        
        # Enhanced temporal learning - track recent actions for reward propagation
        self.recent_actions = []  # List of (position, action, timestamp) for temporal learning
        self.max_recent_actions = 5  # Number of recent actions to remember
        
        # Statistics and state tracking
        self.attempts = 0
        self.total_deaths = 0
        self.victories = 0
        self.last_distance = 0
        self.last_action = None
        self.last_position = None
        self.stuck_timer = 0.0
        
        # UCB1 exploration parameters
        self.ucb1_c = 1.4  # Exploration parameter (sqrt(2) is theoretical optimum)
        
        # Learning control
        self.learning_active = True
        
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
        
        # Load existing learning data
        self.load_learning_data()
        
        # Print game tutorial for reference
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
        """Enhanced position key with velocity and power-up context"""
        # Grid position (30px resolution)
        grid_x = int(self.player.rect.centerx // 30)
        grid_y = int(self.player.rect.centery // 30)
        
        # Velocity context (quantized for manageable state space)
        vel_x_quantized = "still"
        if self.player.vel_x > 1:
            vel_x_quantized = "moving_right"
        elif self.player.vel_x < -1:
            vel_x_quantized = "moving_left"
        
        vel_y_quantized = "neutral"
        if self.player.vel_y < -5:
            vel_y_quantized = "rising"
        elif self.player.vel_y > 5:
            vel_y_quantized = "falling"
        
        # Ground state
        ground_state = "on_ground" if self.player.on_ground else "in_air"
        
        # Power-up status
        powerup_status = "none"
        if self.player.has_powerup("jump_boost"):
            powerup_status = "jump_boost"
        
        # Nearby platform context (simplified)
        platform_context = self.get_nearby_platform_context()
        
        # Relative position to victory (simplified)
        victory_distance = abs(self.player.rect.centerx - self.victory_zone.centerx) // 100
        victory_distance = min(victory_distance, 50)  # Cap at 50 to limit state space
        
        return f"{grid_x}_{grid_y}_{ground_state}_{vel_x_quantized}_{vel_y_quantized}_{powerup_status}_{platform_context}_{victory_distance}"
    
    def get_nearby_platform_context(self):
        """Get simplified context about nearby platforms"""
        player_x = self.player.rect.centerx
        player_y = self.player.rect.centery
        
        # Look for platforms within reasonable distance
        nearby_types = []
        
        for platform in self.platforms:
            distance_x = abs(platform.rect.centerx - player_x)
            distance_y = abs(platform.rect.centery - player_y)
            
            # Only consider platforms that are close enough to matter
            if distance_x < 200 and distance_y < 150:
                # Determine platform type
                platform_type = "normal"
                if hasattr(platform, 'bounce_strength'):
                    platform_type = "bouncy"
                elif hasattr(platform, 'ice_friction'):
                    platform_type = "ice"
                elif hasattr(platform, 'one_way'):
                    platform_type = "oneway"
                elif hasattr(platform, 'get_movement_delta'):
                    platform_type = "moving"
                elif hasattr(platform, 'activate'):
                    platform_type = "disappearing"
                
                # Determine relative position
                if distance_x < 100:  # Very close
                    if platform.rect.centery < player_y - 50:
                        nearby_types.append(f"{platform_type}_above")
                    elif platform.rect.centery > player_y + 50:
                        nearby_types.append(f"{platform_type}_below")
                    else:
                        nearby_types.append(f"{platform_type}_level")
        
        # Return simplified context (limit to avoid state explosion)
        if not nearby_types:
            return "no_platforms"
        elif len(nearby_types) == 1:
            return nearby_types[0]
        else:
            # Multiple platforms - just return most significant
            if any("bouncy" in p for p in nearby_types):
                return "bouncy_nearby"
            elif any("moving" in p for p in nearby_types):
                return "moving_nearby"
            elif any("ice" in p for p in nearby_types):
                return "ice_nearby"
            else:
                return "multiple_platforms"
    
    def remember_success(self, position_key, action):
        """Remember a successful action at a position with enhanced tracking"""
        if position_key not in self.success_memory:
            self.success_memory[position_key] = {}
        if action not in self.success_memory[position_key]:
            self.success_memory[position_key][action] = 0
        
        self.success_memory[position_key][action] += 1
        
        # Enhanced tracking for UCB1
        self.track_action_attempt(position_key, action)
    
    def remember_failure(self, position_key, action):
        """Remember a failed action at a position with enhanced tracking"""
        if position_key not in self.failure_memory:
            self.failure_memory[position_key] = {}
        if action not in self.failure_memory[position_key]:
            self.failure_memory[position_key][action] = 0
        
        self.failure_memory[position_key][action] += 1
        
        # Enhanced tracking for UCB1
        self.track_action_attempt(position_key, action)
    
    def track_action_attempt(self, position_key, action):
        """Track action attempts for confidence and UCB1 calculations"""
        # Track total attempts for this action at this position
        if position_key not in self.action_attempts:
            self.action_attempts[position_key] = {}
        if action not in self.action_attempts[position_key]:
            self.action_attempts[position_key][action] = 0
        
        self.action_attempts[position_key][action] += 1
        
        # Track total visits to this state
        if position_key not in self.state_visit_count:
            self.state_visit_count[position_key] = 0
        self.state_visit_count[position_key] += 1
    
    def get_action_confidence(self, position_key, action):
        """Calculate confidence score for an action (0-1 range)"""
        if position_key not in self.action_attempts:
            return 0.0
        
        attempts = self.action_attempts[position_key].get(action, 0)
        if attempts == 0:
            return 0.0
        
        successes = self.success_memory.get(position_key, {}).get(action, 0)
        failures = self.failure_memory.get(position_key, {}).get(action, 0)
        
        # Simple confidence: success rate weighted by attempts
        success_rate = successes / max(1, successes + failures)
        
        # Higher confidence with more attempts (up to a point)
        attempt_factor = min(1.0, attempts / 10.0)  # Asymptotic to 1.0
        
        return success_rate * attempt_factor
    
    def get_ucb1_score(self, position_key, action):
        """Calculate UCB1 score for action selection"""
        if position_key not in self.action_attempts:
            return float('inf')  # Unknown actions get highest priority
        
        action_attempts = self.action_attempts[position_key].get(action, 0)
        if action_attempts == 0:
            return float('inf')  # Untried actions get highest priority
        
        total_visits = self.state_visit_count.get(position_key, 1)
        successes = self.success_memory.get(position_key, {}).get(action, 0)
        failures = self.failure_memory.get(position_key, {}).get(action, 0)
        
        # Calculate empirical success rate
        success_rate = successes / max(1, successes + failures)
        
        # UCB1 exploration term
        exploration_term = self.ucb1_c * math.sqrt(math.log(total_visits) / action_attempts)
        
        return success_rate + exploration_term
    
    def add_to_recent_actions(self, position_key, action):
        """Add action to recent actions for temporal learning"""
        import time
        timestamp = time.time()
        self.recent_actions.append((position_key, action, timestamp))
        
        # Keep only recent actions
        if len(self.recent_actions) > self.max_recent_actions:
            self.recent_actions.pop(0)
    
    def propagate_temporal_reward(self, reward_type, intensity):
        """Propagate rewards back to recent actions (Temporal Difference Learning)"""
        if not self.recent_actions:
            return
        
        # Propagate reward back with diminishing strength
        for i, (pos_key, action, timestamp) in enumerate(reversed(self.recent_actions)):
            # More recent actions get more credit
            temporal_discount = 0.8 ** i  # Discount factor
            discounted_intensity = intensity * temporal_discount
            
            if discounted_intensity > 0.1:  # Only propagate significant rewards
                if reward_type == "success":
                    self.remember_success(pos_key, action)
                    self.feel_emotion("success", discounted_intensity, action)
                elif reward_type == "failure":
                    self.remember_failure(pos_key, action)
                    self.feel_emotion("failure", discounted_intensity, action)
    
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
        
        # Add current action to recent actions for temporal learning
        if chosen_action != "wait":  # Don't track wait actions for temporal learning
            current_position = self.get_position_key()
            self.add_to_recent_actions(current_position, chosen_action)
        
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
                
                # Use temporal learning to reward recent actions
                self.propagate_temporal_reward("success", happiness_intensity * 0.5)
                
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
        """Enhanced action selection using UCB1 and confidence scoring"""
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
        
        # INTELLIGENT EXPLOITATION: Use UCB1 for learned behavior
        if position_key in self.success_memory or position_key in self.action_attempts:
            # Calculate UCB1 scores for all safe actions
            action_scores = []
            
            for action in safe_actions:
                ucb1_score = self.get_ucb1_score(position_key, action)
                confidence = self.get_action_confidence(position_key, action)
                
                # Add directional bias to UCB1 scores
                direction_bonus = 0
                if "right" in action and "jump" in action:
                    direction_bonus = 0.3  # UP+RIGHT = best!
                elif "right" in action:
                    direction_bonus = 0.2  # RIGHT = good
                elif "jump" in action:
                    direction_bonus = 0.1  # UP = decent
                elif "left" in action:
                    direction_bonus = -0.1  # LEFT = slight penalty
                
                # Power-up context bonus
                powerup_bonus = 0
                if self.player.has_powerup("jump_boost") and "jump" in action:
                    powerup_bonus = 0.2  # Prefer jumping when boosted
                
                # Platform context bonus
                platform_bonus = 0
                platform_context = self.get_nearby_platform_context()
                if "bouncy" in platform_context and "jump" in action:
                    platform_bonus = 0.15  # Jumping is better near bouncy platforms
                elif "ice" in platform_context and action == "wait":
                    platform_bonus = 0.1  # Sometimes waiting on ice is smart
                
                total_score = ucb1_score + direction_bonus + powerup_bonus + platform_bonus
                action_scores.append((action, total_score, confidence, ucb1_score))
            
            # Sort by total score (highest first)
            action_scores.sort(key=lambda x: x[1], reverse=True)
            
            if action_scores:
                best_action, best_score, confidence, raw_ucb1 = action_scores[0]
                
                # Decide between top options based on confidence
                if len(action_scores) > 1 and confidence < 0.3:  # Low confidence
                    # Consider top 2-3 actions when not confident
                    top_actions = action_scores[:min(3, len(action_scores))]
                    chosen_action = random.choice([a[0] for a in top_actions])
                    print(f"🤔 LOW CONFIDENCE UCB1: Trying {chosen_action} (confidence: {confidence:.2f})")
                else:
                    chosen_action = best_action
                    print(f"🧠 HIGH CONFIDENCE UCB1: Using {chosen_action} (confidence: {confidence:.2f}, UCB1: {raw_ucb1:.2f})")
                
                return chosen_action
        
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
        """Called when AI dies - enhanced with temporal learning"""
        self.attempts += 1
        self.total_deaths += 1
        
        # Feel REALLY bad about dying
        death_feeling_intensity = min(8, 3 + self.total_deaths)
        self.feel_emotion("failure", death_feeling_intensity)
        
        # Use temporal learning to punish recent actions that led to death
        self.propagate_temporal_reward("failure", death_feeling_intensity * 0.3)
        
        # Check if we made progress (FIXED LOGIC)
        if self.last_distance > self.personal_best_distance:
            old_personal_best = self.personal_best_distance  # Save old value BEFORE updating
            self.personal_best_distance = self.last_distance  # Update to new best
            print(f"🚀 NEW RECORD! Reached distance: {self.last_distance}")
            
            # When we make progress, reinforce more of the successful sequence
            success_count = min(5, len(self.pb_route) // 2)
            for i in range(success_count):
                if len(self.pb_route) > i:
                    # pb_route contains (position, action, distance) tuples
                    pos, action, distance = self.pb_route[-(i+1)]  # Get from the end (most recent)
                    self.remember_success(pos, action)
                    self.feel_emotion("success", 1, action)  # Feel good about this action
        else:
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
        
        # Reset position for new attempt
        self.player.rect.x = 200  # Start position
        self.player.rect.y = WORLD_HEIGHT - 180 - PLAYER_HEIGHT - 5
        self.player.vel_x = 0
        self.player.vel_y = 0
        self.player.on_ground = False
        
        # Clear recent actions on death
        self.recent_actions = []
        
        # Update last distance for next attempt
        self.last_distance = self.player.rect.centerx
        
        # Decay emotions slightly over time
        self.recent_progress_feeling *= 0.95
    
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
        """Save enhanced learning data to JSON file"""
        try:
            data = {
                'success_memory': self.success_memory,
                'failure_memory': self.failure_memory,
                'action_attempts': self.action_attempts,  # NEW
                'state_visit_count': self.state_visit_count,  # NEW
                'positive_reinforcement': self.positive_reinforcement,
                'negative_reinforcement': self.negative_reinforcement,
                'recent_progress_feeling': self.recent_progress_feeling,
                'personal_best_distance': self.personal_best_distance,
                'pb_route': self.pb_route,
                'attempts': self.attempts,
                'victories': self.victories,
                'total_deaths': self.total_deaths,
                'ucb1_c': self.ucb1_c  # NEW
            }
            
            with open('ai_learning_data.json', 'w') as f:
                json.dump(data, f, indent=2)
            print(f"💾 Enhanced learning data saved! ({len(self.success_memory)} states learned)")
            
        except Exception as e:
            print(f"❌ Failed to save learning data: {e}")
    
    def load_learning_data(self):
        """Load enhanced learning data from JSON file"""
        try:
            if os.path.exists('ai_learning_data.json'):
                with open('ai_learning_data.json', 'r') as f:
                    data = json.load(f)
                
                self.success_memory = data.get('success_memory', {})
                self.failure_memory = data.get('failure_memory', {})
                self.action_attempts = data.get('action_attempts', {})  # NEW
                self.state_visit_count = data.get('state_visit_count', {})  # NEW
                self.positive_reinforcement = data.get('positive_reinforcement', {})
                self.negative_reinforcement = data.get('negative_reinforcement', {})
                self.recent_progress_feeling = data.get('recent_progress_feeling', 0)
                self.personal_best_distance = data.get('personal_best_distance', 0)
                self.pb_route = data.get('pb_route', [])
                self.attempts = data.get('attempts', 0)
                self.victories = data.get('victories', 0)
                self.total_deaths = data.get('total_deaths', 0)
                self.ucb1_c = data.get('ucb1_c', 1.4)  # NEW
                
                print(f"📖 Enhanced learning data loaded! {len(self.success_memory)} states, {self.attempts} attempts")
                if self.personal_best_distance > 0:
                    print(f"🏆 Personal Best: {self.personal_best_distance:.0f} with {len(self.pb_route)} route actions")
            else:
                print("📝 No existing learning data found - starting fresh!")
                
        except Exception as e:
            print(f"❌ Failed to load learning data: {e}")
            print("📝 Starting with fresh learning data")
    
    def erase_learning_data(self):
        """Erase all enhanced learning data"""
        self.success_memory = {}
        self.failure_memory = {}
        self.action_attempts = {}  # NEW
        self.state_visit_count = {}  # NEW
        self.positive_reinforcement = {}
        self.negative_reinforcement = {}
        self.recent_progress_feeling = 0
        self.personal_best_distance = 0
        self.pb_route = []
        self.attempts = 0
        self.victories = 0
        self.total_deaths = 0
        self.recent_actions = []  # NEW
        
        # Delete the save file
        try:
            if os.path.exists('ai_learning_data.json'):
                os.remove('ai_learning_data.json')
            print("🗑️ All enhanced learning data erased!")
        except Exception as e:
            print(f"❌ Failed to delete save file: {e}")
    
    def toggle_learning(self):
        """Start/stop the learning process"""
        self.learning_active = not self.learning_active
        status = "STARTED" if self.learning_active else "STOPPED"
        print(f"⏯️ Learning {status}")
        return self.learning_active
    
    def get_learning_stats(self):
        """Get enhanced learning statistics for UI display"""
        success_rate = (self.victories / max(1, self.attempts)) * 100
        exploration_rate = self.get_dynamic_exploration_rate()
        
        # Calculate average confidence across all known states
        total_confidence = 0
        confidence_count = 0
        for position_key in self.action_attempts:
            for action in self.action_attempts[position_key]:
                confidence = self.get_action_confidence(position_key, action)
                if confidence > 0:
                    total_confidence += confidence
                    confidence_count += 1
        
        avg_confidence = total_confidence / max(1, confidence_count)
        
        # Calculate state space coverage
        total_states_visited = len(self.state_visit_count)
        well_explored_states = sum(1 for visits in self.state_visit_count.values() if visits >= 3)
        
        return {
            'attempts': self.attempts,
            'victories': self.victories,
            'success_rate': success_rate,
            'total_deaths': self.total_deaths,
            'personal_best': self.personal_best_distance,
            'known_positions': len(self.success_memory),
            'exploration_rate': exploration_rate,
            'emotional_score': self.recent_progress_feeling,
            'positive_associations': len(self.positive_reinforcement),
            'recovery_mode': self.pb_recovery_mode,
            # NEW enhanced metrics
            'avg_confidence': avg_confidence,
            'total_states_visited': total_states_visited,
            'well_explored_states': well_explored_states,
            'state_coverage_ratio': well_explored_states / max(1, total_states_visited),
            'recent_actions_count': len(self.recent_actions),
            'ucb1_exploration_param': self.ucb1_c
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
            f"Avg Confidence: {stats['avg_confidence']:.2f}",
            f"States Explored: {stats['total_states_visited']}",
            f"UCB1 Param: {stats['ucb1_exploration_param']:.1f}",
            f"Recent Actions: {stats['recent_actions_count']}"
        ]
        
        for i, text in enumerate(current_texts):
            color = WHITE
            # Highlight high confidence
            if "Avg Confidence" in text and stats['avg_confidence'] > 0.7:
                color = GREEN
            elif "Avg Confidence" in text and stats['avg_confidence'] < 0.3:
                color = RED
            
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