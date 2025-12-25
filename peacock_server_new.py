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
metadata_manager = MetadataManager()
title_suggester = TitleSuggester()


def load_config():
    """Load configuration from config.json"""
    config_path = Path(__file__).parent / 'config.json'
    
    if not config_path.exists():
        print("\n⚠️  No configuration file found.")
        print("Please run 'python peacock.py' first to set up configuration.\n")
        sys.exit(1)
    
    with open(config_path, 'r') as f:
        return json.load(f)


def load_audio_metadata():
    """Load audio metadata from configured directory"""
    global audio_metadata, config
    
    print("Loading audio metadata...")
    audio_path = config.get('default_path', '')
    
    if not os.path.exists(audio_path):
        print(f"Error: Audio path '{audio_path}' does not exist")
        sys.exit(1)
    
    audio_metadata = metadata_manager.scan_directory(audio_path)
    print(f"Loaded {len(audio_metadata)} audio files")


# Routes

@app.route('/')
def index():
    """Serve the main page"""
    return render_template(
        'index.html',
        title=config.get('report_title', 'Peacock - Audio Library'),
        audio_data=audio_metadata
    )


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
    base_path = os.path.abspath(config.get('default_path', ''))
    
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
    """Reveal audio file in Finder"""
    from urllib.parse import unquote
    
    filename = unquote(filename)
    
    # Security: ensure file is within configured directory
    base_path = os.path.abspath(config.get('default_path', ''))
    
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
        # Reveal file in Finder (macOS)
        subprocess.run(['open', '-R', file_path], check=True)
        return jsonify({'success': True, 'path': file_path})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


def main():
    """Main entry point"""
    global config
    
    parser = argparse.ArgumentParser(description='Peacock Interactive Server')
    parser.add_argument('--port', type=int, default=5000, help='Port to run server on')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to')
    args = parser.parse_args()
    
    # Load configuration
    config = load_config()
    
    # Load audio metadata
    load_audio_metadata()
    
    # Print startup message
    print("=" * 80)
    print("🦚 Peacock Interactive Server")
    print("=" * 80)
    print()
    print(f"✓ Server starting on http://localhost:{args.port}")
    print(f"✓ Open your browser to: http://localhost:{args.port}")
    print()
    print("  Features:")
    print("  • Edit titles with ✏️ icon")
    print("  • Organize titles with ✨ button")
    print("  • All changes update actual file metadata")
    print()
    print("  Press Ctrl+C to stop the server")
    print()
    
    # Run Flask app
    app.run(host=args.host, port=args.port, debug=False)


if __name__ == '__main__':
    main()
