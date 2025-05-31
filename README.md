# Pygame Platformer - Basic Movement

A simple 2D platformer game built with Pygame featuring basic player movement and jumping mechanics.

## Setup Instructions

1. Install Python (3.7 or higher)
2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## How to Run

Execute the main game file:
```
python main.py
```

## Controls

- **Movement**: Arrow Keys or WASD
  - Left Arrow / A: Move left
  - Right Arrow / D: Move right
- **Jumping**: Spacebar, Up Arrow, or W
  - Single tap: Regular jump
  - Double tap while in air: Double jump
- **Quit**: ESC key or close the window

## Features Implemented

### ✅ Basic Player Movement
- Smooth left and right movement
- Friction when not pressing movement keys
- Horizontal collision detection with platforms

### ✅ Jumping Mechanics
- Variable jump height based on key press duration
- Double jump capability
- Gravity simulation with realistic physics
- Maximum fall speed limit

### ✅ Platform System
- Ground platform spanning the screen width
- Multiple floating platforms at different heights
- Solid collision detection (can't pass through platforms)

### ✅ Physics System
- Gravity affecting the player
- Velocity-based movement
- Collision detection and response
- Screen boundary detection

### ✅ Debug Information
Real-time display of:
- Player position coordinates
- Player velocity (X and Y components)
- Ground contact status
- Jump counter

## Game Architecture

The game is structured with the following key components:

- **`main.py`**: Main game loop and game state management
- **`player.py`**: Player character class with movement and physics
- **`platforms.py`**: Platform classes for collision surfaces
- **`settings.py`**: Game constants and configuration values

## Current Game Features

- **Player Character**: Blue rectangle (32x48 pixels)
- **Platforms**: Green platforms for jumping on
- **Ground**: Dark gray ground platform
- **Physics**: Realistic gravity, jumping, and collision
- **Movement**: Smooth horizontal movement with friction
- **Debug Display**: Real-time game state information

## Next Development Steps

According to the game outline, the next features to implement would be:
1. Simple enemies with basic AI
2. Collectible items (coins, power-ups)
3. Multiple levels
4. Basic UI improvements
5. Sound effects and music

## Technical Details

- **Resolution**: 1024x768 pixels
- **Frame Rate**: 60 FPS
- **Physics**: Custom gravity and collision system
- **Rendering**: Pygame sprite system with double buffering 