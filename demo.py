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
        self.success_memory = {}  # {(position_key, action): success_count}
        self.failure_memory = {}  # {(position_key, action): failure_count}
        
        # NEW: Enhanced learning with confidence tracking
        self.action_attempts = {}  # {(position_key, action): attempt_count}
        self.state_visit_count = {}  # {position_key: visit_count}
        
        # Enhanced memory for progress efficiency
        self.progress_memory = {}  # {(position_key, action): [progress_amounts]}
        self.average_progress = {}  # {(position_key, action): average_progress}
        
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
        
        # PB route failure tracking
        self.pb_step_failure_count = {}  # Track failures for specific PB route steps
        self.last_pb_step_attempted = None  # Track which PB step was last attempted
        
        # Statistics and state tracking
        self.attempts = 0
        self.total_deaths = 0
        self.victories = 0
        self.last_distance = 0
        self.last_action = None
        self.last_position = None
        self.stuck_timer = 0.0
        
        # Path efficiency tracking
        self.inefficient_action_streak = 0  # Counter for actions that don't make meaningful progress
        self.last_meaningful_progress_distance = 0  # Track distance at last meaningful progress
        
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
            # Special case: Victory can exceed normal emotional caps (up to 15)
            max_feeling = 15 if intensity > 10 else 10  # Allow victory to go to 15
            self.recent_progress_feeling = min(max_feeling, self.recent_progress_feeling + intensity)
            if action:
                current_positive = self.positive_reinforcement.get(action, 0)
                # BOOST positive feelings for rightward actions!
                if "right" in action:
                    intensity = min(10, intensity * 1.5)  # 50% bonus for rightward actions
                    # print(f"😄 AI feels EXTRA GOOD about {action} (rightward bonus!)")
                self.positive_reinforcement[action] = min(10, current_positive + intensity)
                # if "right" not in action:
                #     print(f"😊 AI feels GOOD about {action} (intensity: {intensity})")
        
        elif emotion_type == "failure":
            self.recent_progress_feeling = max(-10, self.recent_progress_feeling - intensity)
            if action:
                current_negative = self.negative_reinforcement.get(action, 0)
                # EXTRA punishment for leftward actions that fail
                if "left" in action:
                    intensity = min(10, intensity * 1.5)  # 50% more negative for leftward fails
                    # print(f"😡 AI feels EXTRA BAD about {action} (leftward penalty!)")
                self.negative_reinforcement[action] = min(10, current_negative + intensity)
                # if "left" not in action:
                #     print(f"😢 AI feels BAD about {action} (intensity: {intensity})")
        
        elif emotion_type == "stuck":
            self.recent_progress_feeling = max(-10, self.recent_progress_feeling - 1)
            # print(f"😤 AI feels FRUSTRATED from being stuck")
        
        elif emotion_type == "rightward_progress":
            # Special emotion for making rightward progress
            # Enhanced: Amplify if progress was made efficiently
            if hasattr(self, 'inefficient_action_streak') and self.inefficient_action_streak <= 3:
                intensity = min(10, intensity * 1.3)  # 30% bonus for efficient progress
                print(f"🚀 EFFICIENT rightward progress! (intensity: {intensity:.1f})")
            else:
                print(f"🚀 Rightward progress (intensity: {intensity:.1f})")
            self.recent_progress_feeling = min(10, self.recent_progress_feeling + intensity)
    
    def get_position_key(self):
        """Simplified position key for basic platform learning"""
        # Grid position (30px resolution)
        grid_x = int(self.player.rect.centerx // 30)
        grid_y = int(self.player.rect.centery // 30)
        
        # Velocity context (quantized for manageable state space)
        vel_x_quantized = "still"
        if self.player.vel_x > 1:
            vel_x_quantized = "moving_right"
        elif self.player.vel_x < -1:
            vel_x_quantized = "moving_left"
        
        # Enhanced vertical motion representation
        vertical_motion = 0  # -1 for falling, 1 for rising, 0 for near-zero
        if self.player.vel_y > 5:  # Falling threshold
            vertical_motion = -1
        elif self.player.vel_y < -5:  # Rising threshold
            vertical_motion = 1
        
        # Ground state
        ground_state = "on_ground" if self.player.on_ground else "in_air"
        
        # TEMPORARILY COMMENTED OUT: Power-up status and platform context for simplified learning
        # # Power-up status (boolean flag for jump boost)
        # has_jump_boost = self.player.has_powerup("jump_boost")
        # 
        # # Nearby platform context (simplified)
        # platform_context = self.get_nearby_platform_context()
        
        # Relative position to victory (simplified)
        victory_distance = abs(self.player.rect.centerx - self.victory_zone.centerx) // 100
        victory_distance = min(victory_distance, 50)  # Cap at 50 to limit state space
        
        return f"{grid_x}_{grid_y}_{ground_state}_{vel_x_quantized}_{vertical_motion}_{victory_distance}"
        # FULL VERSION: return f"{grid_x}_{grid_y}_{ground_state}_{vel_x_quantized}_{vertical_motion}_{has_jump_boost}_{platform_context}_{victory_distance}"
    
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
        """Store successful action in memory with progress tracking"""
        key = (position_key, action)
        self.success_memory[key] = self.success_memory.get(key, 0) + 1
        
        # Track this action attempt
        self.track_action_attempt(position_key, action)
        
        # Track progress efficiency
        if hasattr(self, 'last_distance') and hasattr(self, 'last_meaningful_progress_distance'):
            progress_made = self.last_distance - getattr(self, 'action_start_distance', self.last_meaningful_progress_distance)
            if key not in self.progress_memory:
                self.progress_memory[key] = []
            self.progress_memory[key].append(max(0, progress_made))  # Only positive progress
            
            # Update average progress (keep last 10 measurements)
            if len(self.progress_memory[key]) > 10:
                self.progress_memory[key] = self.progress_memory[key][-10:]
            
            self.average_progress[key] = sum(self.progress_memory[key]) / len(self.progress_memory[key])
    
    def remember_failure(self, position_key, action):
        """Store failed action in memory"""
        key = (position_key, action)
        self.failure_memory[key] = self.failure_memory.get(key, 0) + 1
        
        # Enhanced tracking for UCB1
        self.track_action_attempt(position_key, action)
    
    def track_action_attempt(self, position_key, action):
        """Track that an action was attempted at a position"""
        key = (position_key, action)
        self.action_attempts[key] = self.action_attempts.get(key, 0) + 1
        
        # Track state visits
        self.state_visit_count[position_key] = self.state_visit_count.get(position_key, 0) + 1
    
    def get_action_confidence(self, position_key, action):
        """Calculate confidence for an action at a position"""
        key = (position_key, action)
        
        # Get success and failure counts
        successes = self.success_memory.get(key, 0)
        failures = self.failure_memory.get(key, 0)
        total_attempts = self.action_attempts.get(key, 0)
        
        if total_attempts == 0:
            return 0.0  # No data, no confidence
        
        # Calculate success rate
        success_rate = successes / total_attempts if total_attempts > 0 else 0
        
        # Confidence increases with more attempts (but caps out)
        attempt_confidence = min(1.0, total_attempts / 10)  # Full confidence at 10+ attempts
        
        # Combined confidence: success rate weighted by how much data we have
        confidence = success_rate * attempt_confidence
        
        return confidence
    
    def get_ucb1_score(self, position_key, action):
        """Calculate UCB1 score for exploration/exploitation balance"""
        key = (position_key, action)
        
        # Get action statistics
        successes = self.success_memory.get(key, 0)
        attempts = self.action_attempts.get(key, 0)
        total_state_visits = self.state_visit_count.get(position_key, 0)
        
        if attempts == 0:
            return float('inf')  # Unvisited actions get highest priority
        
        if total_state_visits == 0:
            return float('inf')  # Avoid division by zero
        
        # Calculate average reward (success rate)
        average_reward = successes / attempts
        
        # Calculate exploration bonus
        exploration_bonus = self.ucb1_c * math.sqrt(math.log(total_state_visits) / attempts)
        
        # Add progress efficiency bonus if available
        progress_bonus = 0.0
        if key in self.average_progress:
            # Normalize progress bonus (assuming max progress ~100 pixels)
            progress_bonus = min(0.5, self.average_progress[key] / 200)
        
        return average_reward + exploration_bonus + progress_bonus
    
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
        """Get the best known action for this position"""
        safe_actions = ["move_right", "jump_only", "up_right", "wait"]
        
        best_action = None
        best_confidence = 0.0
        
        for action in safe_actions:
            key = (position_key, action)
            if key in self.success_memory and self.success_memory[key] > 0:
                confidence = self.get_action_confidence(position_key, action)
                if confidence > best_confidence and confidence > 0.3:  # Require reasonable confidence
                    best_confidence = confidence
                    best_action = action
        
        return best_action
    
    def is_action_known_failure(self, position_key, action):
        """Check if an action is known to consistently fail"""
        key = (position_key, action)
        successes = self.success_memory.get(key, 0)
        failures = self.failure_memory.get(key, 0)
        total = successes + failures
        
        # Consider it a known failure if tried 3+ times with <20% success rate
        return total >= 3 and (successes / total) < 0.2
    
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
            
            # Track action start distance for progress efficiency calculation
            self.action_start_distance = self.player.rect.centerx
        
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
                
                # Reset inefficient action streak on meaningful progress
                if progress_amount > 15:  # Meaningful progress threshold
                    self.inefficient_action_streak = 0
                    self.last_meaningful_progress_distance = self.last_distance
                
                # Use temporal learning to reward recent actions
                self.propagate_temporal_reward("success", happiness_intensity * 0.5)
                
                # Remember the last action that led to this progress as EXTRA good
                if self.last_action:
                    self.feel_emotion("success", 2, self.last_action)  # Extra boost for rightward success
        else:
            # No meaningful progress made - increment inefficiency streak
            if self.last_action and self.last_action != "wait":
                self.inefficient_action_streak += 1
                
                # Provide feedback when streak gets concerning
                if self.inefficient_action_streak == 6:
                    print(f"🔄 AI making inefficient moves (streak: {self.inefficient_action_streak})")
                elif self.inefficient_action_streak >= 10:
                    print(f"⚠️ AI very inefficient (streak: {self.inefficient_action_streak})")
        
        # Enhanced stuck detection and timer management
        old_x = self.last_position[0] if self.last_position else self.player.rect.centerx
        old_y = self.last_position[1] if self.last_position else self.player.rect.centery
        old_on_ground = getattr(self, 'last_on_ground', self.player.on_ground)
        
        # Reset stuck timer on various types of progress
        horizontal_progress = abs(self.player.rect.centerx - old_x) > 5  # Moved horizontally
        significant_vertical_progress = (old_y - self.player.rect.centery) > 15  # Moved up significantly
        ground_state_changed = old_on_ground != self.player.on_ground  # Ground state changed
        
        if horizontal_progress or significant_vertical_progress or ground_state_changed:
            self.stuck_timer = 0.0
            if significant_vertical_progress:
                print(f"📈 Vertical progress detected: {old_y - self.player.rect.centery:.1f} pixels up")
        else:
            self.stuck_timer += dt
        
        # Store current state for next comparison
        self.last_position = (self.player.rect.centerx, self.player.rect.centery)
        self.last_on_ground = self.player.on_ground
        
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
        """Update Personal Best with intelligent route filtering for efficiency"""
        current_x = self.player.rect.centerx
        
        if current_x > self.personal_best_distance:
            # We've made a new personal best!
            old_pb = self.personal_best_distance
            self.personal_best_distance = current_x
            
            # ENHANCED: Only append actions that significantly contribute to progress
            if self.last_action:
                current_pos = self.get_position_key()
                
                # Check if this action was truly beneficial for reaching new PB
                should_add_to_route = False
                
                if len(self.pb_route) == 0:
                    # First action in route - always add
                    should_add_to_route = True
                else:
                    # Get the last recorded distance from pb_route
                    last_recorded_pos, last_recorded_action, last_recorded_distance = self.pb_route[-1]
                    
                    # Calculate net progress since last recorded action
                    net_progress = current_x - last_recorded_distance
                    
                    # Only add if this action contributed meaningfully to progress
                    if net_progress >= 15:  # Meaningful progress threshold
                        # Check if this is an efficient action (not corrective)
                        is_efficient = True
                        
                        # Filter out back-and-forth movements
                        if "left" in self.last_action and net_progress > 0:
                            # Moving left while making overall rightward progress - might be corrective
                            if net_progress < 30:  # Small net progress suggests correction
                                is_efficient = False
                        
                        # Filter out very small jumps that don't help much
                        elif self.last_action == "jump_only" and net_progress < 5:
                            is_efficient = False
                        
                        # Check for repeated similar actions from similar positions
                        if len(self.pb_route) >= 2:
                            prev_pos, prev_action, prev_distance = self.pb_route[-2]
                            if prev_action == self.last_action and abs(last_recorded_distance - prev_distance) < 20:
                                # Similar action from similar position - might be inefficient repetition
                                is_efficient = False
                        
                        if is_efficient:
                            should_add_to_route = True
                        else:
                            # Replace the last entry if this new action is more efficient
                            if net_progress > (current_x - last_recorded_distance):
                                self.pb_route.pop()  # Remove less efficient last entry
                                should_add_to_route = True
                
                if should_add_to_route:
                    self.pb_route.append((current_pos, self.last_action, current_x))
                    # Limit route length to prevent it from becoming too long
                    if len(self.pb_route) > 50:  # Keep only most recent 50 efficient actions
                        self.pb_route = self.pb_route[-40:]  # Trim to 40, keeping most recent
            
            print(f"🏆 NEW PB: {current_x:.0f} (+{current_x - old_pb:.0f}) | Route: {len(self.pb_route)} efficient actions")
            
            # Feel AMAZING about setting a new PB
            self.feel_emotion("success", 5)
            
            # Turn off recovery mode since we're now at a new PB
            self.pb_recovery_mode = False
            self.pb_route_index = 0
            
            return True
        
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
            self.pb_recovery_mode = False
            self.pb_route_index = 0
            print("📍 PB recovery route completed - resuming exploration")
            return None
        
        # Increase exploration chance if stuck during PB recovery
        base_exploration_chance = 0.25  # Original 25% chance
        stuck_induced_exploration_bonus = 0.0
        if self.stuck_timer > 3.5:  # If stuck for a notable duration
            stuck_induced_exploration_bonus = 0.40  # Add 40% chance, making it 65% total
            print(f"🎲 PB Recovery: AI is stuck (timer: {self.stuck_timer:.1f}s), increasing exploration likelihood.")

        if random.random() < (base_exploration_chance + stuck_induced_exploration_bonus):
            print("🎲 PB Recovery: Choosing to explore (possibly due to being stuck) instead of following route step.")
            # Optionally, slightly reduce frustration here too, as it's trying something new
            self.recent_progress_feeling = max(-10, self.recent_progress_feeling + 0.5)
            return None  # Fall back to exploration logic in make_smart_decision
        
        # Get current position for comparison with PB route
        current_pos = self.get_position_key()
        
        # Find the closest matching position in our PB route from current index
        best_match_index = None
        best_match_distance = float('inf')
        
        # Look ahead in the route to find a good match
        search_range = min(3, len(self.pb_route) - self.pb_route_index)
        for i in range(search_range):
            route_index = self.pb_route_index + i
            if route_index < len(self.pb_route):
                route_pos, route_action, route_distance = self.pb_route[route_index]
                
                # Calculate "distance" between current position and route position
                # This is a simplified comparison - in a more advanced system, 
                # you'd compare individual components of the position key
                if route_pos == current_pos:
                    best_match_index = route_index
                    break
                else:
                    # Simple heuristic: if positions don't match exactly, continue
                    continue
        
        if best_match_index is not None:
            # Found a good match, execute that action
            self.pb_route_index = best_match_index
            route_pos, route_action_for_pos, route_distance = self.pb_route[self.pb_route_index]
            
            print(f"📍 PB Recovery: Found matching position at step {self.pb_route_index}, action: {route_action_for_pos}")
            
            # Track this PB step attempt for failure analysis
            self.last_pb_step_attempted = self.pb_route_index
            
            # Check if this step has failed multiple times
            failure_count = self.pb_step_failure_count.get(self.pb_route_index, 0)
            if failure_count >= 3:  # Step has failed 3+ times
                print(f"⚠️ PB Recovery: Step {self.pb_route_index} has failed {failure_count} times - forcing exploration instead")
                self.last_pb_step_attempted = None  # Don't track this as a PB attempt
                return None  # Force exploration instead
            
            # Move to next step for next time
            self.pb_route_index += 1
            
            return route_action_for_pos
        else:
            # No good match found, try next action in sequence anyway
            if self.pb_route_index < len(self.pb_route):
                route_pos, route_action_for_pos, route_distance = self.pb_route[self.pb_route_index]
                print(f"📍 PB Recovery: No exact match, trying sequential action at step {self.pb_route_index}: {route_action_for_pos}")
                
                # Track this PB step attempt for failure analysis
                self.last_pb_step_attempted = self.pb_route_index
                
                # Check if this step has failed multiple times
                failure_count = self.pb_step_failure_count.get(self.pb_route_index, 0)
                if failure_count >= 3:  # Step has failed 3+ times
                    print(f"⚠️ PB Recovery: Step {self.pb_route_index} has failed {failure_count} times - forcing exploration instead")
                    self.last_pb_step_attempted = None  # Don't track this as a PB attempt
                    return None  # Force exploration instead
                
                self.pb_route_index += 1
                return route_action_for_pos
            else:
                # Somehow got past the end
                self.pb_recovery_mode = False
                self.pb_route_index = 0
                print("📍 PB recovery exceeded route length - resuming exploration")
                return None
    
    def is_at_pb_location(self):
        """Check if we're at or past our Personal Best location"""
        return self.player.rect.centerx >= (self.personal_best_distance - 50)
    
    def get_dynamic_exploration_rate(self):
        """Calculate dynamic exploration rate based on progress and distance from PB"""
        base_rate = 10  # Even lower base rate for more consistent learned behavior
        
        # Distance-based exploration - get MORE exploratory as we approach PB
        current_distance = self.player.rect.centerx
        distance_from_pb = abs(current_distance - self.personal_best_distance)
        
        # Adjusted for ultra-simple level - even smaller distance thresholds
        if distance_from_pb < 15:  # Very close to PB (was 25)
            distance_bonus = 50  # Very jittery near PB
        elif distance_from_pb < 40:  # Near PB (was 75)
            distance_bonus = 30  # Moderately jittery approaching PB
        elif distance_from_pb < 80:  # Somewhat close to PB (was 150)
            distance_bonus = 15  # Some exploration
        else:  # Far from PB
            distance_bonus = 5   # Minimal exploration - focus on learning efficient path
        
        # Time-based reduction - but much less aggressive
        time_factor = max(0.8, 1.0 - (self.attempts * 0.01))  # Even slower reduction
        
        final_rate = min(75, (base_rate + distance_bonus) * time_factor)  # Lower cap at 75%
        return final_rate
    
    def is_making_good_progress(self):
        """Check if AI is making good progress toward the goal"""
        current_x = self.player.rect.centerx
        current_y = self.player.rect.centery
        
        # For ultra-simplified level, much smaller progress thresholds
        # Good progress = moving right AND up in smaller amounts
        progress_threshold = 50  # Even smaller threshold for ultra-simple level
        height_progress_threshold = 30  # Moving up is important but smaller steps
        
        # Check if we've moved significantly right from starting position (100)
        horizontal_progress = current_x > (100 + progress_threshold)
        
        # Check if we've gained height (smaller world, so smaller height gains count)
        # Starting Y is around WORLD_HEIGHT - 180, so going up means smaller Y values
        starting_y = WORLD_HEIGHT - 180
        height_progress = current_y < (starting_y - height_progress_threshold)
        
        return horizontal_progress and height_progress
    
    def get_position_progress_score(self):
        """Get a score (0-100) representing how close we are to victory"""
        current_x = self.player.rect.centerx
        current_y = self.player.rect.centery
        
        # For ultra-simplified level: victory zone is at (1200, WORLD_HEIGHT - 720)
        victory_x = 1200  # Much closer victory zone
        victory_y = WORLD_HEIGHT - 720
        
        starting_x = 100  # New starting position
        starting_y = WORLD_HEIGHT - 180
        
        # Calculate progress (0 to 1) for both dimensions
        horizontal_progress = max(0, min(1, (current_x - starting_x) / (victory_x - starting_x)))
        vertical_progress = max(0, min(1, (starting_y - current_y) / (starting_y - victory_y)))
        
        # Combined score (slightly favor horizontal progress as it's the main direction)
        combined_score = (horizontal_progress * 0.6 + vertical_progress * 0.4) * 100
        
        return int(combined_score)
    
    def make_smart_decision(self):
        """Make AI decision based on learning and emotions with enhanced logging"""
        position_key = self.get_position_key()
        current_distance = self.player.rect.centerx
        far_from_pb = current_distance < (self.personal_best_distance - 100)
        at_pb_location = current_distance >= (self.personal_best_distance - 100)
        
        happiness_level = max(0, self.recent_progress_feeling)
        anger_level = max(0, -self.recent_progress_feeling)
        
        # Reduced logging - only show important decisions
        # print(f"\n🤖 AI Decision Making:")
        # print(f"   Position: {position_key}")
        # print(f"   Current distance: {current_distance}, PB distance: {self.personal_best_distance}")
        # print(f"   Emotions - Happiness: {happiness_level:.1f}, Anger: {anger_level:.1f}")
        # print(f"   Far from PB: {far_from_pb}, At PB: {at_pb_location}, Stuck timer: {self.stuck_timer:.1f}s")
        # print(f"   PB recovery mode: {self.pb_recovery_mode}, Manual override: {self.manual_pb_override}")
        
        # Only log when in recovery mode
        if self.pb_recovery_mode:
            print(f"📍 PB Recovery: Step {self.pb_route_index}/{len(self.pb_route)}")
            # if self.pb_route_index < len(self.pb_route):
            #     route_pos, route_action, route_dist = self.pb_route[self.pb_route_index]
            #     print(f"   Next PB step: {route_action} at {route_pos} (dist: {route_dist})")
        
        # Check if learning is active
        if not self.learning_active:
            return "wait"
        
        # EXPERIMENT: COMMENTING OUT MANUAL PB OVERRIDE SYSTEM FOR TESTING
        # =================================================================
        # # MANUAL OVERRIDE SYSTEM - Force PB recovery when requested
        # if self.manual_pb_override:
        #     if len(self.pb_route) > 0:
        #         if not self.pb_recovery_mode:
        #             self.pb_recovery_mode = True
        #             self.pb_route_index = 0
        #             print(f"🎯 MANUAL OVERRIDE: Starting PB recovery to {self.personal_best_distance:.0f}")
        #         
        #         recovery_action = self.try_pb_recovery()
        #         if recovery_action:
        #             print(f"🎯 MANUAL OVERRIDE: Following PB route - {recovery_action}")
        #             return recovery_action
        #         else:
        #             # Reached end of PB route or got stuck
        #             self.manual_pb_override = False
        #             self.pb_recovery_mode = False
        #             print("🎯 MANUAL OVERRIDE COMPLETE: Now at PB location")
        #     else:
        #         # No PB route available, disable override
        #         self.manual_pb_override = False
        #         print("❌ Manual override disabled - no PB route to follow")
        
        # NEW LOGIC: MAD = stick to PB route, HAPPY = explore
        
        # EXPERIMENT: COMMENTING OUT ANGRY AI LOGIC TO TEST EXPLORATION-ONLY BEHAVIOR
        # =======================================================================
        # # ANGRY/FRUSTRATED AI - Stick to what worked before, unless catastrophically stuck!
        # if anger_level > 4:  # Moderately frustrated or worse
        #     # DESPERATION / STUCK OVERRIDE for extreme anger
        #     if self.stuck_timer > 5.0 and anger_level >= 9.0:  # Thresholds for being very stuck and very angry
        #         print(f"😡 DESPERATION MODE: anger {anger_level:.1f}, stuck {self.stuck_timer:.1f}s")
        #         self.pb_recovery_mode = False  # Ensure we are not in PB recovery mode
        #         self.manual_pb_override = False  # Turn off manual override too, if it was active
        #         self.recent_progress_feeling = max(-10, self.recent_progress_feeling + 2)  # Slightly reduce anger to allow trying something new
        #         self.stuck_timer = 0.0  # Reset stuck timer as we are taking a new approach
        #         # Aggressively explore, trying to break the pattern.
        #         chosen_action = self.choose_exploration_action(position_key, exploration_boost=0.95)  # Very high exploration
        #         self.last_action = chosen_action  # Record this desperation action
        #         # print(f"😡 Desperation action: {chosen_action}")
        #         return chosen_action
        #     
        #     # If not in desperation mode, proceed with normal angry logic
        #     if len(self.pb_route) > 0 and far_from_pb:
        #         if not self.pb_recovery_mode:
        #             self.pb_recovery_mode = True
        #             self.pb_route_index = 0
        #             print(f"😤 FRUSTRATED - Starting PB recovery (anger: {anger_level:.1f})")
        #         
        #         recovery_action = self.try_pb_recovery()
        #         if recovery_action:
        #             # print(f"😤 FRUSTRATED: Following proven route - {recovery_action}")
        #             return recovery_action
        #         else:
        #             # Finished PB route, now explore carefully
        #             self.pb_recovery_mode = False
        #             # print(f"😤 Reached PB via route, now exploring carefully (anger: {anger_level:.1f})")
        #     # else:
        #     #     print(f"😤 AI frustrated (anger: {anger_level:.1f}) but no good route to follow")
        
        # HAPPY/SUCCESSFUL AI - Explore new possibilities!
        elif happiness_level > 3 or at_pb_location:
            # Disable any PB recovery mode - we're feeling good!
            if self.pb_recovery_mode:
                self.pb_recovery_mode = False
                print(f"😊 HAPPY - Disabling PB recovery to explore!")
            
            # At PB location or feeling happy = maximum exploration!
            if at_pb_location:
                # MAXIMUM JITTERY EXPLORATION at PB - this creates the jittery behavior
                print(f"🎯 AT PB: MAXIMUM UP+RIGHT EXPLORATION!")
                return self.choose_exploration_action(position_key, exploration_boost=0.95)  # 95% exploration (was 80%)
            else:
                # Happy but not at PB = confident exploration
                return self.choose_exploration_action(position_key, exploration_boost=0.7)  # 70% exploration (was 40%)
        
        # NORMAL AI - Balanced approach when not strongly emotional
        else:
            # Boost exploration if AI is being inefficient
            inefficiency_boost = 0.0
            if self.inefficient_action_streak > 5:
                inefficiency_boost = min(0.3, (self.inefficient_action_streak - 5) * 0.05)
                if inefficiency_boost > 0.1:
                    print(f"🔄 Boosting exploration due to inefficiency (streak: {self.inefficient_action_streak})")
            
            # Get dynamic exploration rate based on distance from PB
            exploration_rate = self.get_dynamic_exploration_rate()
            
            # Try learned behavior first, but skip it if exploration rate is very high
            learned_action = self.get_learned_action(position_key)
            if learned_action and inefficiency_boost < 0.2 and exploration_rate < 50:  # Only use learned when exploration is low
                print(f"📚 Using learned action: {learned_action}")
                return learned_action
            
            # Otherwise explore with dynamic rate + inefficiency boost
            total_boost = (exploration_rate / 100) + inefficiency_boost
            print(f"🎲 EXPLORING: Dynamic rate {exploration_rate:.0f}% (distance-based)")
            chosen_action = self.choose_exploration_action(position_key, exploration_boost=total_boost)
            return chosen_action
    
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
            # EXPLORATION: Prioritize UP movement first (survival), then UP+RIGHT
            jump_actions = [a for a in safe_actions if "jump" in a]
            upright_actions = [a for a in safe_actions if "right" in a or "jump" in a]
            
            if jump_actions and random.random() < 0.85:  # 85% chance to prioritize ANY jumping
                # Further bias toward JUMP+RIGHT within jumping actions
                jump_right_actions = [a for a in jump_actions if "right" in a]
                if jump_right_actions and random.random() < 0.7:  # 70% chance for JUMP+RIGHT within jumps
                    chosen_action = random.choice(jump_right_actions)
                    print(f"🎲 EXPLORING: UP+RIGHT priority: {chosen_action}")
                else:
                    chosen_action = random.choice(jump_actions)
                    print(f"🎲 EXPLORING: UP priority (safety): {chosen_action}")
            elif upright_actions and random.random() < 0.95:  # 95% chance for remaining UP+RIGHT actions
                chosen_action = random.choice(upright_actions)
                print(f"🎲 EXPLORING: UP/RIGHT action: {chosen_action}")
            else:
                # Only 5% chance for other actions (and avoid LEFT when possible)
                non_left_actions = [a for a in safe_actions if "left" not in a]
                if non_left_actions:
                    chosen_action = random.choice(non_left_actions)
                    print(f"🎲 EXPLORING: Non-left fallback: {chosen_action}")
                else:
                    chosen_action = random.choice(safe_actions)
                    print(f"🎲 EXPLORING: Last resort: {chosen_action}")
            
            return chosen_action
        
        # INTELLIGENT EXPLOITATION: Use UCB1 for learned behavior
        if position_key in self.success_memory or position_key in self.action_attempts:
            # Calculate UCB1 scores for all safe actions
            action_scores = []
            
            for action in safe_actions:
                ucb1_score = self.get_ucb1_score(position_key, action)
                confidence = self.get_action_confidence(position_key, action)
                
                # Add directional bias to UCB1 scores - UP is MORE important than RIGHT!
                direction_bonus = 0
                if "right" in action and "jump" in action:
                    direction_bonus = 1.2  # UP+RIGHT = MASSIVE bonus! (increased from 1.0)
                elif "jump" in action:
                    direction_bonus = 1.0  # UP = HUGE bonus! (increased from 0.4) - UP is critical!
                elif "right" in action:
                    direction_bonus = 0.3  # RIGHT = moderate bonus (decreased from 0.6) - less important than UP
                elif "left" in action:
                    direction_bonus = -0.8  # LEFT = major penalty
                elif action == "wait":
                    direction_bonus = -0.5  # WAIT = bigger penalty to encourage movement (increased from -0.3)
                
                # Simplified scoring for basic platform learning
                powerup_bonus = 0  # No power-ups in simplified mode
                platform_bonus = 0  # No special platforms in simplified mode
                
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
        
        # FALLBACK: Prioritize UP movement for survival, then UP+RIGHT
        jump_actions = [a for a in safe_actions if "jump" in a]
        upright_actions = [a for a in safe_actions if "right" in a or "jump" in a]
        
        if jump_actions:
            # First priority: any jumping action for survival
            jump_right_actions = [a for a in jump_actions if "right" in a]
            if jump_right_actions and random.random() < 0.7:  # 70% prefer jump+right within jumps
                chosen_action = random.choice(jump_right_actions)
                print(f"⬆️➡️ FALLBACK: UP+RIGHT priority: {chosen_action}")
            else:
                chosen_action = random.choice(jump_actions)
                print(f"⬆️ FALLBACK: UP priority (safety): {chosen_action}")
        elif upright_actions:
            chosen_action = random.choice(upright_actions)
            print(f"⬆️➡️ FALLBACK: UP/RIGHT action: {chosen_action}")
        else:
            # Avoid LEFT if possible, prefer jumping over waiting
            non_left_actions = [a for a in safe_actions if "left" not in a]
            if non_left_actions:
                chosen_action = random.choice(non_left_actions)
                print(f"🤷 FALLBACK: Non-left action: {chosen_action}")
            else:
                chosen_action = random.choice(safe_actions)
                print(f"🤷 FALLBACK: Last resort: {chosen_action}")
        
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
        
        # Enhanced PB route failure tracking
        if self.pb_recovery_mode and self.last_pb_step_attempted is not None:
            # We were following PB route and died - this step failed
            if self.last_pb_step_attempted not in self.pb_step_failure_count:
                self.pb_step_failure_count[self.last_pb_step_attempted] = 0
            self.pb_step_failure_count[self.last_pb_step_attempted] += 1
            failure_count = self.pb_step_failure_count[self.last_pb_step_attempted]
            
            print(f"📉 PB Route Step {self.last_pb_step_attempted} failed (total failures: {failure_count})")
            
            # More strongly penalize the specific action from the pb_route that was last attempted
            if self.last_pb_step_attempted < len(self.pb_route):
                failed_pos, failed_action, failed_distance = self.pb_route[self.last_pb_step_attempted]
                self.remember_failure(failed_pos, failed_action)
                self.feel_emotion("failure", death_feeling_intensity * 1.5, failed_action)  # Extra penalty
                print(f"💥 Extra penalty for PB route failure: {failed_action} at {failed_pos}")
            
            self.last_pb_step_attempted = None  # Reset for next attempt
        
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
        
        # Feel AMAZING about winning! VICTORY IS THE ULTIMATE HIGH!
        self.feel_emotion("success", 15)  # SUPER-maximum positive feeling! (higher than normal 10 cap)
        
        # Learn from ALL actions in this successful attempt
        for pos, action, distance in self.pb_route:
            self.remember_success(pos, action)
            self.feel_emotion("success", 2, action)  # All actions in winning run feel good
        
        # Reset for next attempt
        self.last_distance = 0
        self.pb_route = []
        self.stuck_timer = 0.0
    
    def save_learning_data(self):
        """Save AI learning data to JSON file"""
        try:
            # Convert tuple keys to strings for JSON serialization
            save_data = {
                "success_memory": {f"{pos}|{action}": count for (pos, action), count in self.success_memory.items()},
                "failure_memory": {f"{pos}|{action}": count for (pos, action), count in self.failure_memory.items()},
                "action_attempts": {f"{pos}|{action}": count for (pos, action), count in self.action_attempts.items()},
                "state_visit_count": self.state_visit_count,
                "average_progress": {f"{pos}|{action}": progress for (pos, action), progress in self.average_progress.items()},
                "positive_reinforcement": self.positive_reinforcement,
                "negative_reinforcement": self.negative_reinforcement,
                "personal_best_distance": self.personal_best_distance,
                "pb_route": self.pb_route,
                "total_deaths": self.total_deaths,
                "victories": self.victories,
                "recent_progress_feeling": self.recent_progress_feeling,
                "inefficient_action_streak": getattr(self, 'inefficient_action_streak', 0)
            }
            
            with open("ai_learning_data.json", "w") as f:
                json.dump(save_data, f, indent=2)
                
        except Exception as e:
            print(f"Failed to save learning data: {e}")
    
    def load_learning_data(self):
        """Load AI learning data from JSON file"""
        try:
            with open("ai_learning_data.json", "r") as f:
                data = json.load(f)
            
            # Handle new format with tuple keys
            if "success_memory" in data and isinstance(next(iter(data["success_memory"].keys()), ""), str):
                # New format: convert string keys back to tuples
                self.success_memory = {}
                for pos_action_str, count in data["success_memory"].items():
                    if "|" in pos_action_str:
                        parts = pos_action_str.split("|", 1)  # Split only on first |
                        pos_str, action = parts[0], parts[1]
                        self.success_memory[(pos_str, action)] = count
                
                self.failure_memory = {}
                for pos_action_str, count in data["failure_memory"].items():
                    if "|" in pos_action_str:
                        parts = pos_action_str.split("|", 1)
                        pos_str, action = parts[0], parts[1]
                        self.failure_memory[(pos_str, action)] = count
                
                self.action_attempts = {}
                for pos_action_str, count in data.get("action_attempts", {}).items():
                    if "|" in pos_action_str:
                        parts = pos_action_str.split("|", 1)
                        pos_str, action = parts[0], parts[1]
                        self.action_attempts[(pos_str, action)] = count
                
                self.average_progress = {}
                for pos_action_str, progress in data.get("average_progress", {}).items():
                    if "|" in pos_action_str:
                        parts = pos_action_str.split("|", 1)
                        pos_str, action = parts[0], parts[1]
                        self.average_progress[(pos_str, action)] = progress
                
                self.state_visit_count = data.get("state_visit_count", {})
            else:
                # Legacy format or empty data
                self.success_memory = {}
                self.failure_memory = {}
                self.action_attempts = {}
                self.average_progress = {}
                self.state_visit_count = {}
            
            # Load other data with fallbacks
            self.positive_reinforcement = data.get("positive_reinforcement", {})
            self.negative_reinforcement = data.get("negative_reinforcement", {})
            self.personal_best_distance = data.get("personal_best_distance", 0)
            self.pb_route = data.get("pb_route", [])
            self.total_deaths = data.get("total_deaths", 0)
            self.victories = data.get("victories", 0)
            self.recent_progress_feeling = data.get("recent_progress_feeling", 0.0)
            self.inefficient_action_streak = data.get("inefficient_action_streak", 0)
            
            print(f"📖 Loaded AI learning data: {len(self.success_memory)} learned actions")
                
        except FileNotFoundError:
            print("📖 No previous learning data found - starting fresh!")
        except Exception as e:
            print(f"⚠️ Error loading learning data: {e}")
            print("📖 Starting with fresh learning data...")
    
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
        for (position_key, action) in self.action_attempts:
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
            
        # EXPERIMENT: COMMENTING OUT B KEY - MANUAL PB OVERRIDE FOR TESTING
        # elif keys_just_pressed.get(pygame.K_b, False):
        #     # Manual override - force AI to go to Personal Best
        #     if self.ai.personal_best_distance > 0:
        #         self.ai.manual_pb_override = True
        #         self.ai.pb_recovery_mode = True
        #         self.ai.pb_route_index = 0
        #         print(f"🎯 MANUAL OVERRIDE: Forcing AI to go to Personal Best ({self.ai.personal_best_distance:.0f})")
        #     else:
        #         print("❌ No Personal Best recorded yet!")
    
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
        
        # EXPERIMENT: COMMENTING OUT EMOTIONAL MODE INDICATOR FOR CLEANER UI
        # ====================================================================
        # # NEW: Emotional mode indicator
        # anger_level = max(0, -self.ai.recent_progress_feeling)
        # happiness_level = max(0, self.ai.recent_progress_feeling)
        # current_x = self.ai.player.rect.centerx
        # at_pb_location = current_x >= (self.ai.personal_best_distance - 100)
        # 
        # # Determine AI mode based on emotional state
        # if self.ai.manual_pb_override:
        #     mode_status = "🎯 MANUAL OVERRIDE: Following PB Route"
        #     mode_color = YELLOW
        # elif anger_level > 4:
        #     mode_status = f"😤 FRUSTRATED: Following reliable PB route (anger: {anger_level:.1f})"
        #     mode_color = (255, 100, 100)  # Light red
        # elif happiness_level > 3 or at_pb_location:
        #     if at_pb_location:
        #         mode_status = f"🎉 AT PB: Maximum exploration for new paths!"
        #         mode_color = (100, 255, 100)  # Bright green
        #     else:
        #         mode_status = f"😊 HAPPY: Confident exploration (happiness: {happiness_level:.1f})"
        #         mode_color = (150, 255, 150)  # Light green
        # else:
        #     mode_status = f"😐 NEUTRAL: Balanced approach"
        #     mode_color = WHITE
        # 
        # # Display the mode
        # mode_surface = self.font_medium.render(mode_status, True, mode_color)
        # self.screen.blit(mode_surface, (20, 50))
        
        # Simple AI mode indicator (no emotional state)
        current_x = self.ai.player.rect.centerx
        at_pb_location = current_x >= (self.ai.personal_best_distance - 100)
        
        if at_pb_location:
            mode_status = "🎯 AT PERSONAL BEST: Exploring for new paths"
            mode_color = GREEN
        else:
            mode_status = "🤖 LEARNING MODE: Exploration + Experience"
            mode_color = WHITE
        
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
        
        # Learning progress bar (simplified without emotional coloring)
        if stats['attempts'] > 0:
            progress_width = 300
            progress_height = 20
            progress_x = 20
            progress_y = y_offset + 130  # Moved up since no emotion display
            
            # Background
            pygame.draw.rect(self.screen, DARK_GRAY, (progress_x, progress_y, progress_width, progress_height))
            
            # Progress fill based on success rate
            success_rate = stats['success_rate']
            fill_width = int((success_rate / 100) * progress_width)
            
            # Simple color based on success rate (no emotion)
            if success_rate > 75:
                fill_color = GREEN
            elif success_rate > 50:
                fill_color = YELLOW
            elif success_rate > 25:
                fill_color = ORANGE
            else:
                fill_color = RED
            
            if fill_width > 0:
                pygame.draw.rect(self.screen, fill_color, (progress_x, progress_y, fill_width, progress_height))
            
            # Border
            pygame.draw.rect(self.screen, WHITE, (progress_x, progress_y, progress_width, progress_height), 2)
            
            # Simplified progress text without emotional context
            if stats['recovery_mode']:
                progress_text = f"PB Recovery: Returning to {stats['personal_best']:.0f}"
                progress_color = YELLOW
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
            "🧪 EXPERIMENT: No Anger Mode",
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