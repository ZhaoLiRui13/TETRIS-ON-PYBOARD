# TETRIS-ON-PYBOARD

A fully functional Tetris game implemented on the **Pyboard V1.1** using a **ST7735S 1.8" TFT LCD** display and three physical buttons.

## Features

- Classic Tetris gameplay
- Smooth real-time controls (Left, Right, Rotate)
- Line clearing with score tracking
- Simple wall-kick rotation system
- Anti-glitch rendering system
- Optimized performance for MicroPython

## Hardware Requirements

- **Pyboard V1.1**
- **ST7735S 1.8" TFT LCD** (128x160)
- 3 Push Buttons (with pull-up resistors)
- Jumper wires

### Pin Connections

| Component     | Pyboard Pin     |
| ------------- | --------------- |
| Left Button   | Y12             |
| Right Button  | Y9              |
| Rotate Button | Y11             |
| LCD RST       | X3              |
| LCD DC        | X4              |
| LCD CS        | X5              |
| LCD SPI       | SPI1 (Y6/Y7/Y8) |

## Installation & Running

1. Copy the `main.py` file to your Pyboard root directory.
2. Ensure the board is running **MicroPython**.
3. Reset the Pyboard.

The game will start automatically.

## Controls

- **Left Button** → Move piece left
- **Right Button** → Move piece right
- **Rotate Button** → Rotate piece clockwise

## Project Structure

```
Pyboard-Tetris/
├── main.py                 # Main game code
├── README.md               # This file
└── (optional) screenshots/
```

## Code Architecture

- `ST7735_Manual` class: Low-level optimized LCD driver
- `Piece` class: Tetromino representation and rotation logic
- `game_loop()`: Main game loop with input, physics, and rendering
- Optimized rectangle filling with chunked SPI transmission

## Technical Details

- **Display:** 128x160 RGB565 (ST7735S)
- **Playfield:** 10×18 blocks
- **Block Size:** 8×8 pixels
- **Drop Interval:** 700ms (adjustable)
- **Scoring:** 100 points per cleared line

## Notes

- The code includes hardware offset correction (`HARDWARE_OFFSET_X/Y`) for easy calibration.
- Anti-glitch measures are implemented via full grid redraw after locking pieces.
- Designed for educational purposes and embedded systems demonstration.

## Customization

You can easily modify:

- `BLOCK_SIZE`, `FIELD_WIDTH`, `FIELD_HEIGHT`
- Drop speed (`700` in gravity section)
- Button debounce timing
- Colors

## License

This project is open for educational and personal use.

---

**Made for Pyboard V1.1 + ST7735S**

---
