import machine
import time
import random

# ================= HARDWARE PIN CONFIGURATION (PYBOARD V1.1) =================
# Input Controls
PIN_LEFT   = 'Y12'   # Left movement button
PIN_RIGHT  = 'Y9'    # Right movement button
PIN_ROTATE = 'Y11'   # Rotation button

# LCD ST7735S SPI Interface
SPI_BUS_ID = 1
PIN_RST    = 'X3'    # Reset pin
PIN_DC     = 'X4'    # Data/Command control pin
PIN_CS     = 'X5'    # Chip Select pin

# ================= DISPLAY CONFIGURATION =================
SCREEN_WIDTH  = 128
SCREEN_HEIGHT = 160

# Color definitions in RGB565 format
BLACK  = 0x0000
WHITE  = 0xFFFF
BLUE   = 0x001F
RED    = 0xF800
GREEN  = 0x07E0
CYAN   = 0x07FF
YELLOW = 0xFFE0

# ================= TETRIS GAME CONFIGURATION =================
BLOCK_SIZE   = 8                     # Size of each tetromino block in pixels
FIELD_WIDTH  = 10                    # Playfield width (in blocks)
FIELD_HEIGHT = 18                    # Playfield height (in blocks)

# Centering the playfield on the screen
OFFSET_X = int((SCREEN_WIDTH - (FIELD_WIDTH * BLOCK_SIZE)) / 2)
OFFSET_Y = 5

# Hardware offset correction (adjust if display is misaligned)
HARDWARE_OFFSET_X = 0
HARDWARE_OFFSET_Y = 0


# ================= ST7735S LCD DRIVER (Manual Implementation) =================
class ST7735_Manual:
    """
    Custom low-level driver for the ST7735S TFT LCD display.
    Implements direct SPI communication for optimal performance on Pyboard.
    """
    def __init__(self, spi, cs, dc, rst):
        self.spi = spi
        self.cs = machine.Pin(cs, machine.Pin.OUT)
        self.dc = machine.Pin(dc, machine.Pin.OUT)
        self.rst = machine.Pin(rst, machine.Pin.OUT)
        
        self.cs.value(1)
        self.dc.value(0)
        self.rst.value(1)
        self.init_display()

    def write_cmd(self, cmd):
        """Send a command byte to the display controller."""
        self.dc.value(0)
        self.cs.value(0)
        self.spi.write(bytearray([cmd]))
        self.cs.value(1)

    def write_data(self, data):
        """Send a data byte to the display controller."""
        self.dc.value(1)
        self.cs.value(0)
        self.spi.write(bytearray([data]))
        self.cs.value(1)

    def init_display(self):
        """Initialize the ST7735S display with appropriate configuration."""
        self.rst.value(0)
        time.sleep_ms(50)
        self.rst.value(1)
        time.sleep_ms(50)

        self.write_cmd(0x01)                    # Software Reset
        time.sleep_ms(150)
        self.write_cmd(0x11)                    # Sleep Out
        time.sleep_ms(255)

        self.write_cmd(0x3A); self.write_data(0x05)   # 16-bit RGB565 color mode
        self.write_cmd(0x36); self.write_data(0xC8)   # Memory Data Access Control (orientation)
        self.write_cmd(0x21)                          # Display Inversion ON

        # Gamma and Power Settings
        self.write_cmd(0xB1); self.write_data(0x01); self.write_data(0x2C); self.write_data(0x2D)
        self.write_cmd(0xB2); self.write_data(0x01); self.write_data(0x2C); self.write_data(0x2D)
        self.write_cmd(0xB3); self.write_data(0x01); self.write_data(0x2C); self.write_data(0x2D)
        self.write_cmd(0xB3); self.write_data(0x01); self.write_data(0x2C); self.write_data(0x2D)
        
        self.write_cmd(0xC0); self.write_data(0xA2); self.write_data(0x02); self.write_data(0x84)
        
        self.write_cmd(0x29)                    # Display ON
        time.sleep_ms(100)

    def fill_rect(self, x, y, w, h, color):
        """
        Optimized function to fill a rectangle with a specified color.
        Uses chunked transmission to improve performance with large areas.
        """
        if x >= SCREEN_WIDTH or y >= SCREEN_HEIGHT:
            return
        if x + w > SCREEN_WIDTH:  w = SCREEN_WIDTH - x
        if y + h > SCREEN_HEIGHT: h = SCREEN_HEIGHT - y

        x_start = x + HARDWARE_OFFSET_X
        y_start = y + HARDWARE_OFFSET_Y

        self.write_cmd(0x2A)
        self.write_data(0x00); self.write_data(x_start)
        self.write_data(0x00); self.write_data(x_start + w - 1)

        self.write_cmd(0x2B)
        self.write_data(0x00); self.write_data(y_start)
        self.write_data(0x00); self.write_data(y_start + h - 1)

        self.write_cmd(0x2C)

        self.dc.value(1)
        self.cs.value(0)

        # Prepare color buffer for efficient transmission
        color_hi = (color >> 8) & 0xFF
        color_lo = color & 0xFF
        chunk_size = 512
        buffer = bytearray(chunk_size * 2)

        for i in range(0, chunk_size * 2, 2):
            buffer[i] = color_hi
            buffer[i + 1] = color_lo

        remaining = w * h
        while remaining > 0:
            to_send = min(remaining, chunk_size)
            if to_send == chunk_size:
                self.spi.write(buffer)
            else:
                self.spi.write(buffer[:to_send * 2])
            remaining -= to_send

        self.cs.value(1)

    def fill_screen(self, color):
        """Fill the entire screen with a single color."""
        self.fill_rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, color)

    def draw_digit(self, x, y, num, color, size=2):
        """Draw a single digit using a 5x4 pixel font."""
        patterns = [
            [0xE, 0xA, 0xA, 0xA, 0xE], [0x4, 0xC, 0x4, 0x4, 0xE],
            [0xE, 0x2, 0xE, 0x8, 0xE], [0xE, 0x2, 0xE, 0x2, 0xE],
            [0xA, 0xA, 0xE, 0x2, 0x2], [0xE, 0x8, 0xE, 0x2, 0xE],
            [0xE, 0x8, 0xE, 0xA, 0xE], [0xE, 0x2, 0x2, 0x2, 0x2],
            [0xE, 0xA, 0xE, 0xA, 0xE], [0xE, 0xA, 0xE, 0x2, 0xE]
        ]
        if 0 <= num <= 9:
            pat = patterns[num]
            for r in range(5):
                for c in range(4):
                    if (pat[r] >> (3 - c)) & 0x01:
                        self.fill_rect(x + c * size, y + r * size, size, size, color)


# ================= TETROMINO DATA =================
SHAPES = [
    [],  # Index 0 unused
    [[[1,1,1,1]], [[1],[1],[1],[1]]],           # I
    [[[1,0,0],[1,1,1]], [[1,1],[1,0],[1,0]], [[1,1,1],[0,0,1]], [[0,1],[0,1],[1,1]]],  # J
    [[[0,0,1],[1,1,1]], [[1,0],[1,0],[1,1]], [[1,1,1],[1,0,0]], [[1,1],[0,1],[0,1]]],  # L
    [[[1,1],[1,1]]],                            # O
    [[[0,1,1],[1,1,0]], [[1,0],[1,1],[0,1]]],  # S
    [[[0,1,0],[1,1,1]], [[1,0],[1,1],[1,0]], [[1,1,1],[0,1,0]], [[0,1],[1,1],[0,1]]],  # T
    [[[1,1,0],[0,1,1]], [[0,1],[1,1],[1,0]]]   # Z
]

# Global game variables
screen_grid = []
current_piece = None
next_piece_type = 0
score = 0
game_over = False


class Piece:
    """Represents a single Tetromino piece with rotation support."""
    def __init__(self, t):
        self.type = t
        self.rot_idx = 0
        self.rotations = SHAPES[t]
        self.matrix = self.rotations[0]
        self.x = int(FIELD_WIDTH / 2) - int(len(self.matrix[0]) / 2)
        self.y = 0

    def rotate(self):
        """Rotate the piece clockwise."""
        self.rot_idx = (self.rot_idx + 1) % len(self.rotations)
        self.matrix = self.rotations[self.rot_idx]

    def undo_rotate(self):
        """Revert to previous rotation (used in wall kick failure)."""
        self.rot_idx = (self.rot_idx - 1) % len(self.rotations)
        self.matrix = self.rotations[self.rot_idx]


# ================= HARDWARE INITIALIZATION =================
spi = machine.SPI(SPI_BUS_ID, baudrate=20000000, polarity=0, phase=0)
tft = ST7735_Manual(spi, cs=PIN_CS, dc=PIN_DC, rst=PIN_RST)

btn_left   = machine.Pin(PIN_LEFT,   machine.Pin.IN, machine.Pin.PULL_UP)
btn_right  = machine.Pin(PIN_RIGHT,  machine.Pin.IN, machine.Pin.PULL_UP)
btn_rotate = machine.Pin(PIN_ROTATE, machine.Pin.IN, machine.Pin.PULL_UP)


# ================= GAME LOGIC FUNCTIONS =================
def reset_game():
    """Reset all game variables and initialize a new game."""
    global screen_grid, score, game_over
    screen_grid = [[0] * FIELD_HEIGHT for _ in range(FIELD_WIDTH)]
    score = 0
    game_over = False
    tft.fill_screen(BLACK)
    draw_layout()


def draw_block(gx, gy, color):
    """Draw a single block on the playfield with padding for visual separation."""
    tft.fill_rect(
        OFFSET_X + gx * BLOCK_SIZE + 1,
        OFFSET_Y + gy * BLOCK_SIZE + 1,
        BLOCK_SIZE - 2,
        BLOCK_SIZE - 2,
        color
    )


def draw_layout():
    """Draw the static playfield borders and UI elements."""
    # Vertical borders
    tft.fill_rect(OFFSET_X - 2, OFFSET_Y, 2, FIELD_HEIGHT * BLOCK_SIZE, WHITE)
    tft.fill_rect(OFFSET_X + FIELD_WIDTH * BLOCK_SIZE, OFFSET_Y, 2, FIELD_HEIGHT * BLOCK_SIZE, WHITE)
    # Bottom border
    tft.fill_rect(OFFSET_X - 2, OFFSET_Y + FIELD_HEIGHT * BLOCK_SIZE, 
                  FIELD_WIDTH * BLOCK_SIZE + 4, 2, WHITE)
    update_score_display()


def update_score_display():
    """Update the score display on the screen."""
    score_y = 152
    score_x_start = 80
    tft.fill_rect(score_x_start, score_y, 48, 8, BLACK)
    
    s_str = str(score)
    curr_x = SCREEN_WIDTH - (len(s_str) * 8) - 5
    for ch in s_str:
        tft.draw_digit(curr_x, score_y, int(ch), YELLOW, 2)
        curr_x += 8


def draw_grid_static():
    """Redraw the entire static grid (used to prevent graphical glitches)."""
    for x in range(FIELD_WIDTH):
        for y in range(FIELD_HEIGHT):
            color = WHITE if screen_grid[x][y] > 0 else BLACK
            draw_block(x, y, color)


def draw_piece(piece, clear=False):
    """Draw or clear a tetromino piece on the screen."""
    color = BLACK if clear else WHITE
    for r in range(len(piece.matrix)):
        for c in range(len(piece.matrix[0])):
            if piece.matrix[r][c]:
                if 0 <= piece.y + r < FIELD_HEIGHT and 0 <= piece.x + c < FIELD_WIDTH:
                    draw_block(piece.x + c, piece.y + r, color)


def check_collision(piece, off_x=0, off_y=0):
    """Check if the piece would collide with walls or locked blocks."""
    for r in range(len(piece.matrix)):
        for c in range(len(piece.matrix[0])):
            if piece.matrix[r][c]:
                nx = piece.x + c + off_x
                ny = piece.y + r + off_y
                if nx < 0 or nx >= FIELD_WIDTH or ny >= FIELD_HEIGHT:
                    return True
                if ny >= 0 and screen_grid[nx][ny]:
                    return True
    return False


def lock_piece(piece):
    """Lock the current piece into the grid and process line clears."""
    global score
    for r in range(len(piece.matrix)):
        for c in range(len(piece.matrix[0])):
            if piece.matrix[r][c]:
                if 0 <= piece.y + r < FIELD_HEIGHT:
                    screen_grid[piece.x + c][piece.y + r] = 1

    # Line clearing logic
    cleared = 0
    y = FIELD_HEIGHT - 1
    while y >= 0:
        if all(screen_grid[x][y] for x in range(FIELD_WIDTH)):
            cleared += 1
            for row in range(y, 0, -1):
                for col in range(FIELD_WIDTH):
                    screen_grid[col][row] = screen_grid[col][row - 1]
            for col in range(FIELD_WIDTH):
                screen_grid[col][0] = 0
        else:
            y -= 1

    if cleared:
        score += cleared * 100

    # Refresh static grid to prevent visual artifacts
    draw_grid_static()
    update_score_display()


def game_loop():
    """Main game loop handling input, gravity, collision, and rendering."""
    global current_piece, next_piece_type, game_over

    reset_game()
    next_piece_type = random.randint(1, 7)
    current_piece = Piece(next_piece_type)
    next_piece_type = random.randint(1, 7)

    last_drop = time.ticks_ms()

    while not game_over:
        current_ms = time.ticks_ms()

        # ================= INPUT HANDLING =================
        # Move Left
        if btn_left.value() == 0:
            draw_piece(current_piece, clear=True)
            if not check_collision(current_piece, off_x=-1):
                current_piece.x -= 1
            draw_piece(current_piece)
            time.sleep_ms(80)

        # Move Right
        elif btn_right.value() == 0:
            draw_piece(current_piece, clear=True)
            if not check_collision(current_piece, off_x=1):
                current_piece.x += 1
            draw_piece(current_piece)
            time.sleep_ms(80)

        # Rotate
        elif btn_rotate.value() == 0:
            draw_piece(current_piece, clear=True)
            current_piece.rotate()

            # Simple wall kick
            if check_collision(current_piece):
                if not check_collision(current_piece, off_x=-1):
                    current_piece.x -= 1
                elif not check_collision(current_piece, off_x=1):
                    current_piece.x += 1
                else:
                    current_piece.undo_rotate()

            draw_piece(current_piece)
            time.sleep_ms(200)

        # ================= GRAVITY =================
        if time.ticks_diff(current_ms, last_drop) > 700:
            draw_piece(current_piece, clear=True)
            if not check_collision(current_piece, off_y=1):
                current_piece.y += 1
                draw_piece(current_piece)
            else:
                draw_piece(current_piece)
                lock_piece(current_piece)
                
                current_piece = Piece(next_piece_type)
                next_piece_type = random.randint(1, 7)

                if check_collision(current_piece):
                    game_over = True
                    tft.fill_screen(RED)
                    time.sleep(0.5)
                    tft.fill_screen(BLACK)
                    time.sleep(0.5)

            last_drop = current_ms

        time.sleep_ms(10)  # CPU relief


# ================= MAIN PROGRAM =================
try:
    while True:
        game_loop()
        time.sleep(1)
except KeyboardInterrupt:
    print("Game terminated by user.")