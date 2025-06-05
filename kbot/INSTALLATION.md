# Installation Guide

## Prerequisites

1. **Python 3.7+**: Download from https://python.org
2. **Tesseract OCR**: Required for text recognition
   - Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki
   - Linux: `sudo apt-get install tesseract-ocr`
   - macOS: `brew install tesseract`

## Installation Steps

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Tesseract path** (Windows):
   - Edit `core/pixel_analyzer.py`
   - Update the `tesseract_cmd` path to match your installation

3. **Run the bot**:
   ```bash
   python main.py
   ```

## First Time Setup

1. Select your game window using "Select Game Window"
2. Configure screen regions for HP/MP bars using "Configure Regions"
3. Set up your mob whitelist in the Control tab
4. Configure skill slots and timing in the Skills tab
5. Test pixel accuracy and OCR using the test buttons
6. Start the bot!

## Troubleshooting

- **Import errors**: Ensure all dependencies are installed with `pip install -r requirements.txt`
- **OCR not working**: Check Tesseract installation and path configuration
- **Window not detected**: Try running as administrator
- **Permission errors**: Check antivirus settings for PyAutoGUI

For more help, check the application logs.
