# Chealth (Chess Stealth) 🎮♟️

A stealthy chess analysis overlay that works with Chess.com and remains invisible during screen sharing. Perfect for analyzing positions without detection!

## Features 🌟

- **Invisible Overlay**: Completely undetectable during screen sharing or recording
- **Real-time Analysis**: Get instant position evaluation using Stockfish
- **Hotkey Controls**: Easy-to-use keyboard shortcuts
- **Clean Interface**: Modern, gaming-style overlay design
- **Direct Browser Integration**: Works directly with Chess.com

## How It Works 🔍

Chealth creates a transparent overlay window that:
1. Reads the chess position directly from your Chess.com browser window
2. Analyzes the position using the Stockfish chess engine
3. Displays the analysis in a sleek, modern overlay
4. Remains completely invisible during screen sharing

## Requirements 📋

- Windows 10/11
- Python 3.8 or higher
- Google Chrome browser
- Active internet connection

## Installation 🚀

1. Clone this repository:
```bash
git clone https://github.com/efebolukbasi/Chealth.git
cd Chealth
```

2. Install the required packages:
```bash
pip install -r requirements.txt
```

## Usage 💻

1. Start Chrome with remote debugging enabled:
```bash
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222
```

2. Navigate to Chess.com in the Chrome window

3. Run the program:
```bash
python overlay_app.py
```

### Hotkeys ⌨️

- `Ctrl + Alt + S`: Analyze current position
- `Ctrl + Alt + H`: Toggle overlay visibility
- `Ctrl + Alt + Q`: Quit the program

## Important Notes ⚠️

- Always start Chrome with remote debugging before running the program
- Keep the Chess.com tab active when analyzing positions
- The overlay will automatically hide during screen sharing

## Technical Details 🔧

Chealth uses:
- Win32 API for creating an undetectable overlay
- Selenium WebDriver for chess position detection
- Stockfish API for position analysis
- Modern Python async programming

## Disclaimer ⚖️

This tool is for educational and practice purposes only. Please respect Chess.com's terms of service and fair play policies during actual games or tournaments.

## Contributing 🤝

Feel free to submit issues, fork the repository, and create pull requests for any improvements.

## License 📄

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE) file for details. 