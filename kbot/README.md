# Tantra Bot v2.0.0

Advanced automation bot for Tantra Online with modular architecture.

## Features

- **Intelligent Combat System**: Advanced targeting and skill rotation
- **OCR Target Recognition**: Smart mob detection and validation
- **Configurable Skills**: Flexible skill management with priorities and conditions
- **Auto-Potion System**: Smart health and mana management
- **Window Management**: Easy game window selection and management
- **Real-time Monitoring**: Live vitals and statistics tracking

## Installation

1. Install Python 3.7 or higher
2. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Install Tesseract OCR and update path in core/pixel_analyzer.py if needed
4. Run the bot:
   ```bash
   python main.py
   ```

## Quick Start

1. **Select Game Window**: Use "Select Game Window" to attach to your game
2. **Configure Regions**: Set up HP/MP bar detection areas
3. **Set Whitelist**: Define which mobs to attack
4. **Configure Skills**: Set up skill rotations and priorities
5. **Start Bot**: Click "Start Bot" to begin automation

## Project Structure

```
tantra_bot_v2/
├── config/          # Configuration management
├── core/            # Core functionality
├── combat/          # Combat logic and skills
├── ui/              # User interface
├── utils/           # Utilities and helpers
└── main.py          # Entry point
```

## Safety Features

- Emergency stop functionality
- Input validation and error handling
- Comprehensive logging
- Configurable timing to avoid detection

Created by cursebox. For educational purposes.
