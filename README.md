# 🦚 Peacock - Audio Library Organizer

**Peacock** is an elegant, cross-platform tool that extracts metadata from your audio files (music, voice memos, podcasts, recordings) and generates a beautiful, interactive HTML report. Search, filter, sort, and play your audio files directly in your browser!

Perfect for organizing voice memos, music collections, podcast libraries, or any audio recordings on **Windows, macOS, and Linux**.

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.7+-green)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)
![License](https://img.shields.io/badge/license-MIT-orange)

## ✨ Features

- 🎵 **Interactive HTML Report** - Beautiful, responsive interface that works offline
- 🔍 **Powerful Search** - Search by title, filename, artist, album, comment, or any metadata
- 📊 **Smart Filtering** - Sort by duration, date, title, or any column
- ▶️ **Built-in Audio Player** - Play audio files directly in the browser
- 📈 **Statistics Dashboard** - Total files, duration, and file size at a glance
- 🔒 **Read-Only** - Never modifies your original files
- ⚙️ **Customizable** - Configure via JSON file
- 🌐 **Shareable** - Easy to share with friends and colleagues
- 💻 **Cross-Platform** - Works on Windows, macOS, and Linux

## 🎯 Supported Audio Formats

- **M4A** (Apple Voice Memos, iTunes)
- **MP3** (Universal format)
- **WAV** (Uncompressed audio)
- **AAC** (Advanced Audio Coding)
- **FLAC** (Lossless audio)
- **OGG** (Ogg Vorbis)
- **OPUS** (High quality, low latency)

## 🚀 Quick Start

### Prerequisites

- Python 3.7 or higher
- pip (Python package installer)

### Installation

1. **Clone or download this repository:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/Peacock.git
   cd Peacock
   ```

2. **Create a virtual environment (recommended):**
   
   **On macOS/Linux:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
   
   **On Windows:**
   ```cmd
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

### Configuration

**First-time users:** Don't worry about creating a config file manually! Peacock will guide you through an interactive setup wizard on your first run.

#### Automatic Setup (Recommended)

1. **Run Peacock for the first time:**
   ```bash
   python peacock.py
   ```

2. **Follow the setup wizard:**
   - Enter the path to your audio files
   - Enter a title for your library
   - Configuration will be saved automatically!

#### Manual Configuration (Optional)

If you prefer to configure manually:

1. **Copy the example config file:**
   ```bash
   cp config.example.json config.json
   ```

2. **Edit config.json with your settings:**
   ```json
   {
     "default_path": "C:/Users/YourName/Music",  // Windows
     "default_path": "/Users/YourName/Music",    // macOS
     "default_path": "/home/yourname/Music",     // Linux
     "report_title": "My Audio Library",
     "output_filename": "audio_library_report.html"
   }
   ```

#### Reconfigure Anytime

To change your configuration:
```bash
python peacock.py --setup
```

### Usage

#### Basic Usage
```bash
python peacock.py
```

On first run, you'll be guided through a setup wizard. After that, it will use your saved configuration.

#### Reconfigure Settings
```bash
python peacock.py --setup
```

#### Specify Path Directly
```bash
python peacock.py "/path/to/audio/files"

# Windows example:
python peacock.py "C:\Users\YourName\Music"

# macOS/Linux example:
python peacock.py "/Users/YourName/Music"
```

#### Custom Output File
```bash
python peacock.py "/path/to/audio/files" -o my_report.html
```

#### Using Custom Config File
```bash
python peacock.py -c my_config.json
```

### View the Report

After running Peacock, open the generated HTML file in your browser:

**macOS:**
```bash
open audio_library_report.html
```

**Linux:**
```bash
xdg-open audio_library_report.html
```

**Windows:**
```cmd
start audio_library_report.html
```

Or simply **double-click** the HTML file to open it in your default browser!

## 📦 Distribution Options

### Option 1: Standalone Executable (Easiest for Non-Technical Users)

Create a single executable file that doesn't require Python installation:

1. **Install PyInstaller:**
   ```bash
   pip install pyinstaller
   ```

2. **Create executable:**
   ```bash
   pyinstaller --onefile --name Peacock peacock.py
   ```

3. **Find your executable in the `dist/` folder:**
   - Windows: `dist/Peacock.exe`
   - macOS/Linux: `dist/Peacock`

4. **Share the executable** - Users can run it without installing Python!

**Note:** Include `config.example.json` with the executable so users can reference it if needed. The executable will run the setup wizard automatically on first use.

### Option 2: Python Script (For Python Users)

Share the repository as-is. Users need Python 3.7+ and will run:
```bash
pip install -r requirements.txt
python peacock.py
```

### Option 3: ZIP Package

Create a package with everything:
```bash
# 1. Create executable
pyinstaller --onefile --name Peacock peacock.py

# 2. Create distribution folder
mkdir Peacock-Distribution
cp dist/Peacock* Peacock-Distribution/
cp config.example.json Peacock-Distribution/
cp README.md Peacock-Distribution/

# 3. Zip it
zip -r Peacock.zip Peacock-Distribution/
```

Users just unzip, create `config.json`, and run the executable!

## 📖 How It Works

1. **Scan** - Peacock recursively scans your directory for audio files
2. **Extract** - Reads metadata including title, artist, album, duration, dates, and more
3. **Generate** - Creates a beautiful, interactive HTML report
4. **Enjoy** - Open in your browser to search, filter, and play audio files

## 🎨 Customization

### Configuration Options

Edit `config.json` to customize:

- `default_path`: Default directory to scan for audio files (use forward slashes or escaped backslashes)
- `report_title`: Title displayed in the HTML report
- `audio_extensions`: List of audio file extensions to process
- `output_filename`: Default name for generated HTML file

**Path Examples:**
- Windows: `"C:/Users/YourName/Music"` or `"C:\\Users\\YourName\\Music"`
- macOS: `"/Users/YourName/Music"`
- Linux: `"/home/yourname/Music"`

### For Sharing with Others

When sharing Peacock with others:

1. Share the executable (from PyInstaller) or the Python script
2. Include `config.example.json` as a reference (optional)
3. On first run, Peacock will automatically guide them through setup:
   - They'll enter their audio directory path
   - They'll choose a report title
   - Configuration is saved automatically
4. They can reconfigure anytime with `--setup` flag

## 📁 Project Structure

```
Peacock/
├── peacock.py              # Main application
├── config.json             # Your personal config (not in git)
├── config.example.json     # Example config for sharing
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── .gitignore             # Git ignore rules
└── LICENSE                # MIT License
```

## 🛠️ Command Line Options

```bash
python peacock.py [path] [-o OUTPUT] [-c CONFIG] [--setup]

Arguments:
  path                  Path to audio files directory (optional if configured)
  
Options:
  -o, --output OUTPUT   Output HTML file path (default: audio_library_report.html)
  -c, --config CONFIG   Path to custom config.json file
  --setup              Run setup wizard to configure or reconfigure settings
  -h, --help           Show help message

Examples:
  python peacock.py                           # Use saved configuration
  python peacock.py --setup                   # Run setup wizard
  python peacock.py "C:/Users/Me/Music"       # Specify path directly
  python peacock.py "/home/user/audio" -o my_collection.html
  python peacock.py -c custom_config.json
```

## 🔒 Privacy & Security

- **Read-Only**: Peacock only reads metadata, never modifies files
- **Local Processing**: All processing happens on your machine
- **No Network**: No data is sent to external servers
- **Your Data**: Generated reports stay on your computer

## 🐛 Troubleshooting

### "mutagen library not installed"
```bash
pip install -r requirements.txt
```

### "Directory does not exist"
- Check that the path in `config.json` is correct
- Use forward slashes `/` or double backslashes `\\` in paths
- Use absolute paths (e.g., `C:/Users/username/Music` or `/Users/username/Music`)

### Audio won't play in browser
- Some browsers may have security restrictions with `file://` URLs
- Try opening the HTML file from a local web server or use a different browser

## 🤝 Contributing

Contributions are welcome! Feel free to:
- Report bugs
- Suggest new features
- Submit pull requests

## 📝 License

MIT License - feel free to use this project for personal or commercial purposes.

## 👨‍💻 Author

Created with ❤️ for organizing voice memos

## 🙏 Acknowledgments

- Built with [Mutagen](https://mutagen.readthedocs.io/) for audio metadata reading
- Inspired by the need to organize audio collections across all platforms

---

**Enjoy organizing your audio library with Peacock! 🦚**

*Works on Windows, macOS, and Linux - organize any audio collection!*
