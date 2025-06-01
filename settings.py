# Game Settings and Constants

# Screen dimensions
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
FPS = 60

# World dimensions (8 times larger than screen)
WORLD_WIDTH = SCREEN_WIDTH * 8  # 8192 pixels
WORLD_HEIGHT = SCREEN_HEIGHT * 8  # 6144 pixels

# Camera settings
CAMERA_SMOOTHING = 0.3  # More responsive camera (was 0.1)
CAMERA_MARGIN_X = SCREEN_WIDTH // 4  # Dead zone for horizontal camera movement
CAMERA_MARGIN_Y = SCREEN_HEIGHT // 4  # Dead zone for vertical camera movement

# Colors (RGB)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)
LIGHT_GRAY = (192, 192, 192)
PURPLE = (128, 0, 128)
ORANGE = (255, 165, 0)
PINK = (255, 192, 203)
BROWN = (139, 69, 19)
FOREST_GREEN = (34, 139, 34)
STONE_GRAY = (105, 105, 105)
CRYSTAL_BLUE = (70, 130, 180)
METAL_SILVER = (192, 192, 192)

# Player settings
PLAYER_WIDTH = 32
PLAYER_HEIGHT = 48
PLAYER_SPEED = 6
PLAYER_JUMP_SPEED = -18
PLAYER_GRAVITY = 0.7
PLAYER_MAX_FALL_SPEED = 15

# Platform settings (fallback colors)
PLATFORM_COLOR = GREEN
GROUND_HEIGHT = 100

# Game physics
FRICTION = 0.1

# Theme System
THEMES = {
    "crystal": {
        "name": "Crystal Mystic",
        "player_color": CRYSTAL_BLUE,
        "player_accent": CYAN,
        "platform_color": (100, 150, 200),
        "ground_color": (60, 90, 140),
        "particle_color": CYAN,
        "glow_color": (150, 200, 255),
        "bg_color": (20, 30, 60),
        "description": "Magical crystal realm"
    },
    "forest": {
        "name": "Forest Guardian",
        "player_color": FOREST_GREEN,
        "player_accent": BROWN,
        "platform_color": BROWN,
        "ground_color": (101, 67, 33),
        "particle_color": GREEN,
        "glow_color": (144, 238, 144),
        "bg_color": (34, 50, 34),
        "description": "Natural woodland adventure"
    },
    "metal": {
        "name": "Cyber Runner",
        "player_color": METAL_SILVER,
        "player_accent": BLUE,
        "platform_color": GRAY,
        "ground_color": DARK_GRAY,
        "particle_color": WHITE,
        "glow_color": (200, 200, 255),
        "bg_color": (40, 40, 60),
        "description": "Industrial tech world"
    },
    "stone": {
        "name": "Ancient Explorer",
        "player_color": STONE_GRAY,
        "player_accent": ORANGE,
        "platform_color": (139, 129, 76),
        "ground_color": (101, 84, 67),
        "particle_color": ORANGE,
        "glow_color": (255, 215, 0),
        "bg_color": (50, 40, 30),
        "description": "Mysterious ancient ruins"
    }
}

# Character customization options
CHARACTER_PATTERNS = {
    "solid": "Solid Color",
    "stripes": "Horizontal Stripes", 
    "dots": "Polka Dots",
    "gradient": "Gradient Effect"
}

CHARACTER_ACCESSORIES = {
    "none": "No Accessories",
    "cape": "Flowing Cape",
    "hat": "Adventure Hat",
    "belt": "Utility Belt"
}

# Game states
GAME_STATE_MENU = "menu"
GAME_STATE_CHARACTER_SELECT = "character_select"
GAME_STATE_TUTORIAL = "tutorial"
GAME_STATE_PLAYING = "playing"
GAME_STATE_PAUSED = "paused"
GAME_STATE_GAME_OVER = "game_over"
GAME_STATE_VICTORY = "victory"