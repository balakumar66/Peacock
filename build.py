#!/usr/bin/env python3
"""
Build script for creating Peacock executable
Excludes personal files (config.json, metadata cache)
"""
import os
import shutil
import subprocess
import sys

def clean_build():
    """Remove previous build artifacts"""
    dirs_to_remove = ['build', 'dist']
    files_to_remove = ['Peacock.spec']
    
    for d in dirs_to_remove:
        if os.path.exists(d):
            print(f"Cleaning {d}/...")
            shutil.rmtree(d)
    
    for f in files_to_remove:
        if os.path.exists(f):
            print(f"Removing {f}...")
            os.remove(f)

def build_app():
    """Build the application using PyInstaller"""
    print("\n[*] Building Peacock application...")
    
    # Use pyinstaller from venv
    pyinstaller_path = os.path.join(os.path.dirname(sys.executable), 'pyinstaller')
    
    # PyInstaller command
    cmd = [
        pyinstaller_path,
        '--name=Peacock',
        '--windowed',  # No console window (macOS: creates .app)
        '--onefile',  # Single bundle
        '--icon=static/favicon.ico' if os.path.exists('static/favicon.ico') else '--noconfirm',
        # Add data files
        '--add-data=templates:templates',
        '--add-data=static:static',
        '--add-data=lib:lib',
        # Hidden imports
        '--hidden-import=mutagen',
        '--hidden-import=flask',
        '--hidden-import=flask_cors',
        '--hidden-import=lib.metadata_manager',
        # Exclude personal files
        '--exclude-module=config',
        # Main script
        'peacock_server.py'
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print("\n[+] Build successful!")
        print(f"\n[*] Executable location: {os.path.abspath('dist/')}")
        
        # List what was created
        if os.path.exists('dist'):
            print("\nCreated files:")
            for item in os.listdir('dist'):
                size = os.path.getsize(f'dist/{item}')
                print(f"  • {item} ({size / 1024 / 1024:.1f} MB)")
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n[-] Build failed: {e}")
        return False

def create_readme():
    """Create distribution README"""
    readme_content = """# Peacock - Audio Metadata Manager

## Installation

### macOS
1. Open Peacock.app
2. If you see a security warning, go to System Preferences > Security & Privacy
3. Click "Open Anyway"

### Windows
1. Double-click Peacock.exe
2. If Windows Defender shows a warning, click "More info" > "Run anyway"

## First Run

When you first launch Peacock:
1. The setup wizard will appear
2. Select your audio directory (where your recordings are stored)
3. The application will scan and display your audio files

## Usage

- **Edit titles**: Click the ✏️ icon next to any title
- **Organize titles**: Click the ✨ button to auto-format selected titles
- **Play audio**: Click ▶ Play button to preview
- **Show in Finder/Explorer**: Click 📂 Show to reveal file location
- **Search**: Use the search box to filter files
- **Sort**: Click column headers to sort
- **Dark mode**: Toggle with the moon/sun icon

## Adding Directories

Click the "Add Directory" button to scan additional audio locations.

## Support

For issues or questions, visit: https://github.com/balakumar66/Peacock
"""
    
    dist_readme = 'dist/README.txt'
    if os.path.exists('dist'):
        with open(dist_readme, 'w') as f:
            f.write(readme_content)
        print(f"\n[+] Created: {dist_readme}")

def main():
    print("=" * 60)
    print("Peacock Build Script")
    print("=" * 60)
    
    # Clean previous builds
    clean_build()
    
    # Build the application
    if build_app():
        create_readme()
        print("\n" + "=" * 60)
        print("[+] Build complete! Ready for distribution.")
        print("=" * 60)
        print("\nDistribution files are in: dist/")
        print("\n[!] Note: config.json and personal data are NOT included")
    else:
        print("\n[-] Build failed. Check errors above.")
        sys.exit(1)

if __name__ == '__main__':
    main()
