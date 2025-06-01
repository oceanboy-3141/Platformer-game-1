# Pygame Platformer - Phase 3.5: Tutorial System & Decluttered Gameplay

A comprehensive 2D platformer game built with Pygame featuring dynamic platforms, character customization, and an optional tutorial system.

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
- **Menu Navigation**: Arrow Keys or WASD, ENTER/SPACE to confirm
- **Quit**: ESC key or close the window

## 🎯 **Phase 3.5 Features - NEW!**

### ✅ **Tutorial System**
- **Optional Tutorial**: Choose "Yes" during character selection
- **Step-by-Step Learning**: Each mechanic introduced gradually
- **Skip Anytime**: Press ESC to skip tutorial and jump to main game
- **Progressive Checkpoints**: 10 sections covering all game mechanics

### ✅ **Decluttered Main Game**
- **Reduced Platform Density**: ~60% fewer special platforms
- **Strategic Placement**: Each platform type appears 2-6 times max
- **Better Spacing**: More breathing room between challenges
- **Cleaner Experience**: Less overwhelming, more focused gameplay

## Features Implemented

### ✅ **Phase 1: Core Gameplay Foundation**
- **Large Game World**: 8x screen size with camera system
- **Smooth Player Movement**: Physics-based with friction
- **Double Jump Mechanics**: Variable jump height
- **Death/Victory System**: Fall to bottom = death, reach top-right = victory

### ✅ **Phase 2: Character Customization**
- **4 Unique Themes**: Crystal, Forest, Metal, Stone
- **Character Patterns**: Solid, Stripes, Dots, Gradient
- **Accessories**: Cape, Hat, Belt, or None
- **Themed Backgrounds**: Each theme has unique visual style

### ✅ **Phase 3: Dynamic Platform Mechanics**
- **Moving Platforms**: Horizontal sliding with blue borders
- **Vertical Elevators**: Green platforms that wait at endpoints
- **Rotating Platforms**: Purple circular platforms with rotation indicators
- **Disappearing Platforms**: Flash red and fade away when stepped on
- **One-Way Platforms**: Yellow, can jump through from below
- **Bouncy Platforms**: Orange, provide extra jump height
- **Ice Platforms**: Light blue, slippery with reduced friction
- **Jump Boost Power-ups**: Green crystals, 10-second effect

### ✅ **Phase 3.5: Tutorial & Polish**
- **Optional Tutorial System**: Learn each mechanic step-by-step
- **Decluttered Design**: Reduced platform density for better experience
- **Progressive Learning**: 10 tutorial sections with clear explanations
- **Modular Code Structure**: Separate tutorial.py and enemies.py modules

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