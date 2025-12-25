#!/usr/bin/env python3
"""
Peacock Interactive Server
Web-based audio library manager with editing capabilities
"""

import os
import json
import sys
import subprocess
import argparse
from pathlib import Path
from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_cors import CORS

# Import our library modules
from lib.metadata_manager import MetadataManager
from lib.title_suggester import TitleSuggester

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Global state
audio_metadata = []
config = {}
current_directory = None
metadata_manager = MetadataManager()
title_suggester = TitleSuggester()


def run_setup_wizard():
    """Interactive setup wizard for configuration"""
    print("=" * 80)
    print("🦚 Peacock Interactive Server - Setup")
    print("=" * 80)
    print("\nLet's configure your audio library\n")
    
    # Get default path
    while True:
        print("Enter the path to your audio files directory:")
        print("Examples:")
        print("  Windows: C:/Users/YourName/Music")
        print("  macOS:   /Users/YourName/Music")
        print("  Linux:   /home/yourname/Music")
        default_path = input("\n> ").strip().strip('"').strip("'")
        
        if os.path.exists(default_path):
            break
        else:
            print(f"\n❌ Directory '{default_path}' does not exist. Please try again.\n")
    
    # Get report title
    print("\nEnter a title for your audio library:")
    print("(Press Enter for default: 'My Audio Library')")
    report_title = input("> ").strip()
    if not report_title:
        report_title = "My Audio Library"
    
    # Create config
    config = {
        "default_path": default_path,
        "report_title": report_title,
        "audio_extensions": [".m4a", ".mp3", ".wav", ".aac", ".flac", ".ogg", ".m4v", ".opus"],
        "output_filename": "audio_library_report.html"
    }
    
    # Save config
    config_path = Path(__file__).parent / 'config.json'
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"\n✅ Configuration saved to {config_path}")
    print(f"✅ Audio directory: {default_path}")
    print(f"✅ Library title: {report_title}\n")
    
    return config


def load_config(path_override=None):
    """Load configuration from config.json or create new config"""
    config_path = Path(__file__).parent / 'config.json'
    
    if not config_path.exists():
        print("\n⚠️  No configuration file found.")
        print("Running setup wizard...\n")
        return run_setup_wizard()
    
    with open(config_path, 'r') as f:
        cfg = json.load(f)
    
    # Override default_path if provided
    if path_override:
        cfg['default_path'] = path_override
        print(f"✓ Using path override: {path_override}")
    
    return cfg


def save_config(cfg):
    """Save configuration to config.json"""
    config_path = Path(__file__).parent / 'config.json'
    with open(config_path, 'w') as f:
        json.dump(cfg, f, indent=2)


def load_audio_metadata(path=None):
    """Load audio metadata from specified or configured directory"""
    global audio_metadata, config, current_directory
    
    audio_path = path or config.get('default_path', '')
    current_directory = audio_path
    
    print(f"Loading audio metadata from: {audio_path}")
    
    if not os.path.exists(audio_path):
        print(f"Error: Audio path '{audio_path}' does not exist")
        return []
    
    audio_metadata = metadata_manager.scan_directory(audio_path)
    print(f"Loaded {len(audio_metadata)} audio files")
    return audio_metadata


# Routes

@app.route('/')
def index():
    """Serve the main page"""
    return render_template(
        'index.html',
        title=config.get('report_title', 'Peacock - Audio Library'),
        audio_data=audio_metadata,
        current_path=current_directory
    )


@app.route('/api/config', methods=['GET'])
def get_config():
    """Get current configuration"""
    return jsonify({
        'default_path': current_directory,
        'report_title': config.get('report_title', 'My Audio Library'),
        'file_count': len(audio_metadata)
    })


@app.route('/api/change_directory', methods=['POST'])
def change_directory():
    """Change audio library directory and reload"""
    data = request.json
    new_path = data.get('path', '').strip()
    
    if not new_path:
        return jsonify({'success': False, 'error': 'No path provided'}), 400
    
    if not os.path.exists(new_path):
        return jsonify({'success': False, 'error': 'Directory does not exist'}), 404
    
    if not os.path.isdir(new_path):
        return jsonify({'success': False, 'error': 'Path is not a directory'}), 400
    
    try:
        # Update config
        config['default_path'] = new_path
        save_config(config)
        
        # Reload metadata
        new_metadata = load_audio_metadata(new_path)
        
        return jsonify({
            'success': True,
            'path': current_directory,
            'file_count': len(new_metadata),
            'audio_data': new_metadata
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/update_title', methods=['POST'])
def update_title():
    """Update a single file's title"""
    data = request.json
    file_path = data.get('file_path')
    new_title = data.get('new_title')
    
    if not file_path or not new_title:
        return jsonify({'success': False, 'error': 'Missing parameters'}), 400
    
    success = metadata_manager.update_title(file_path, new_title)
    
    if success:
        # Update in-memory metadata
        for item in audio_metadata:
            if item['file_path'] == file_path:
                item['title'] = new_title
                break
        
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Failed to update file'}), 500


@app.route('/api/suggest_titles', methods=['POST'])
def suggest_titles():
    """Generate title suggestions for all files"""
    suggestions = title_suggester.get_suggestions_for_library(audio_metadata)
    return jsonify(suggestions)


@app.route('/api/apply_title_suggestions', methods=['POST'])
def apply_title_suggestions():
    """Apply multiple title updates"""
    data = request.json
    updates = data.get('updates', [])
    
    if not updates:
        return jsonify({'success': False, 'error': 'No updates provided'}), 400
    
    results = metadata_manager.update_multiple_titles(updates)
    
    # Update in-memory metadata
    for update in updates:
        for item in audio_metadata:
            if item['file_path'] == update['file_path']:
                item['title'] = update['new_title']
                break
    
    return jsonify({
        'success': True,
        'success_count': results['success_count'],
        'failed_count': results['failed_count'],
        'errors': results['errors']
    })


@app.route('/api/audio/<path:filename>')
def serve_audio(filename):
    """Serve audio files for streaming"""
    from urllib.parse import unquote
    from flask import make_response
    import mimetypes
    
    filename = unquote(filename)
    
    # Security: ensure file is within configured directory
    base_path = os.path.abspath(current_directory or config.get('default_path', ''))
    
    # Find the file in our metadata
    file_path = None
    for item in audio_metadata:
        if item['filename'] == filename:
            file_path = item['file_path']
            break
    
    if not file_path or not os.path.exists(file_path):
        return f"File not found: {filename}", 404
    
    file_path = os.path.abspath(file_path)
    
    # Security check
    if not file_path.startswith(base_path):
        return "Access denied", 403
    
    # Get correct MIME type
    mime_type = mimetypes.guess_type(file_path)[0]
    if not mime_type:
        ext = os.path.splitext(file_path)[1].lower()
        mime_types = {
            '.m4a': 'audio/x-m4a',
            '.mp3': 'audio/mpeg',
            '.wav': 'audio/wav',
            '.aac': 'audio/aac',
            '.flac': 'audio/flac',
            '.ogg': 'audio/ogg',
            '.opus': 'audio/opus'
        }
        mime_type = mime_types.get(ext, 'application/octet-stream')
    
    directory = os.path.dirname(file_path)
    basename = os.path.basename(file_path)
    
    response = make_response(send_from_directory(directory, basename, mimetype=mime_type))
    response.headers['Accept-Ranges'] = 'bytes'
    response.headers['Cache-Control'] = 'no-cache'
    return response


@app.route('/api/open/<path:filename>')
def open_audio(filename):
    """Reveal audio file in Finder/Explorer"""
    from urllib.parse import unquote
    import platform
    
    filename = unquote(filename)
    
    # Security: ensure file is within configured directory
    base_path = os.path.abspath(current_directory or config.get('default_path', ''))
    
    # Find the file in our metadata
    file_path = None
    for item in audio_metadata:
        if item['filename'] == filename:
            file_path = item['file_path']
            break
    
    if not file_path or not os.path.exists(file_path):
        return jsonify({'success': False, 'error': 'File not found'}), 404
    
    file_path = os.path.abspath(file_path)
    
    # Security check
    if not file_path.startswith(base_path):
        return jsonify({'success': False, 'error': 'Access denied'}), 403
    
    try:
        system = platform.system()
        if system == 'Darwin':  # macOS
            subprocess.run(['open', '-R', file_path], check=True)
        elif system == 'Windows':
            subprocess.run(['explorer', '/select,', file_path], check=True)
        else:  # Linux
            # Open containing directory
            directory = os.path.dirname(file_path)
            subprocess.run(['xdg-open', directory], check=True)
        
        return jsonify({'success': True, 'path': file_path})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


def main():
    """Main entry point"""
    global config
    
    parser = argparse.ArgumentParser(
        description='Peacock Interactive Server',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python peacock_server.py                          # Use saved config
  python peacock_server.py --setup                  # Run setup wizard
  python peacock_server.py /path/to/audio           # Use specific path
  python peacock_server.py --port 8080              # Custom port
        """
    )
    parser.add_argument('path', nargs='?', help='Path to audio files directory')
    parser.add_argument('--setup', action='store_true', help='Run setup wizard')
    parser.add_argument('--port', type=int, default=5000, help='Port to run server on')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to')
    args = parser.parse_args()
    
    # Run setup if requested
    if args.setup:
        config = run_setup_wizard()
    else:
        # Load configuration (with optional path override)
        config = load_config(args.path)
    
    # Load audio metadata
    load_audio_metadata(args.path)
    
    # Print startup message
    print("=" * 80)
    print("�� Peacock Interactive Server")
    print("=" * 80)
    print()
    print(f"✓ Server starting on http://localhost:{args.port}")
    print(f"✓ Open your browser to: http://localhost:{args.port}")
    print(f"✓ Audio directory: {current_directory}")
    print(f"✓ Loaded {len(audio_metadata)} files")
    print()
    print("  Features:")
    print("  • Edit titles with ✏️ icon")
    print("  • Organize titles with ✨ button")
    print("  • Change directory with 📂 button")
    print("  • All changes update actual file metadata")
    print()
    print("  Press Ctrl+C to stop the server")
    print()
    
    # Run Flask app
    app.run(host=args.host, port=args.port, debug=False)


if __name__ == '__main__':
    main()
