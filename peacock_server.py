#!/usr/bin/env python3
"""
Peacock Server - Interactive Audio Library with Editing Capabilities
Runs a local web server to enable editing audio file metadata
"""

import os
import json
import re
from pathlib import Path
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from mutagen import File as MutagenFile
from mutagen.mp4 import MP4

# Import the main peacock module
import peacock

app = Flask(__name__)
CORS(app)

# Store the metadata in memory
audio_metadata = []
config = {}


def update_file_metadata(file_path, new_title):
    """Update the title metadata in the actual audio file"""
    try:
        audio = MutagenFile(file_path)
        
        if audio is None:
            return False, "Could not open audio file"
        
        # Update title based on file type
        if isinstance(audio, MP4):
            audio['\xa9nam'] = [new_title]
        else:
            audio['title'] = new_title
        
        audio.save()
        return True, "Title updated successfully"
    
    except Exception as e:
        return False, str(e)


def generate_smart_title(filename, metadata):
    """Generate a smart title suggestion based on filename and metadata"""
    # Remove extension
    base_name = os.path.splitext(filename)[0]
    
    # Pattern 1: Date timestamp (YYYYMMDD HHMMSS)
    date_pattern = r'(\d{4})(\d{2})(\d{2})\s*(\d{2})(\d{2})(\d{2})'
    match = re.match(date_pattern, base_name)
    if match:
        year, month, day, hour, minute, second = match.groups()
        # Create a descriptive title
        return f"Recording {year}-{month}-{day} at {hour}:{minute}"
    
    # Pattern 2: Already has a good title
    if metadata.get('title') and metadata['title'] != base_name:
        return metadata['title']
    
    # Pattern 3: Clean up the filename
    # Replace underscores and dashes with spaces
    clean_name = base_name.replace('_', ' ').replace('-', ' ')
    # Capitalize words
    clean_name = ' '.join(word.capitalize() for word in clean_name.split())
    
    return clean_name


@app.route('/')
def index():
    """Serve the main HTML page"""
    html_file = Path(__file__).parent / 'audio_library_interactive.html'
    if html_file.exists():
        return send_from_directory(Path(__file__).parent, 'audio_library_interactive.html')
    return "Please generate the report first by running: python peacock_server.py --generate", 404


@app.route('/api/metadata')
def get_metadata():
    """Get all audio metadata"""
    return jsonify(audio_metadata)


@app.route('/api/update_title', methods=['POST'])
def update_title():
    """Update the title of an audio file"""
    data = request.json
    file_path = data.get('file_path')
    new_title = data.get('new_title')
    
    if not file_path or not new_title:
        return jsonify({'success': False, 'error': 'Missing file_path or new_title'}), 400
    
    # Security check: ensure file is within the configured directory
    file_path = os.path.abspath(file_path)
    base_path = os.path.abspath(config.get('default_path', ''))
    
    if not file_path.startswith(base_path):
        return jsonify({'success': False, 'error': 'Invalid file path'}), 403
    
    # Update the file
    success, message = update_file_metadata(file_path, new_title)
    
    if success:
        # Update our in-memory metadata
        for item in audio_metadata:
            if item['file_path'] == file_path:
                item['title'] = new_title
                break
        
        return jsonify({'success': True, 'message': message, 'new_title': new_title})
    else:
        return jsonify({'success': False, 'error': message}), 500


@app.route('/api/suggest_titles', methods=['POST'])
def suggest_titles():
    """Generate smart title suggestions for all files"""
    suggestions = []
    
    for item in audio_metadata:
        original_title = item.get('title') or item['filename']
        suggested_title = generate_smart_title(item['filename'], item)
        
        # Only suggest if it's different
        if suggested_title != original_title:
            suggestions.append({
                'file_path': item['file_path'],
                'filename': item['filename'],
                'current_title': original_title,
                'suggested_title': suggested_title
            })
    
    return jsonify(suggestions)


@app.route('/api/apply_title_suggestions', methods=['POST'])
def apply_title_suggestions():
    """Apply selected title suggestions"""
    data = request.json
    selected_updates = data.get('updates', [])
    
    results = []
    success_count = 0
    error_count = 0
    
    for update in selected_updates:
        file_path = update.get('file_path')
        new_title = update.get('new_title')
        
        if not file_path or not new_title:
            continue
        
        # Security check
        file_path = os.path.abspath(file_path)
        base_path = os.path.abspath(config.get('default_path', ''))
        
        if not file_path.startswith(base_path):
            results.append({
                'file_path': file_path,
                'success': False,
                'error': 'Invalid file path'
            })
            error_count += 1
            continue
        
        # Update the file
        success, message = update_file_metadata(file_path, new_title)
        
        if success:
            # Update in-memory metadata
            for item in audio_metadata:
                if item['file_path'] == file_path:
                    item['title'] = new_title
                    break
            success_count += 1
        else:
            error_count += 1
        
        results.append({
            'file_path': file_path,
            'success': success,
            'message': message if success else f'Error: {message}'
        })
    
    return jsonify({
        'success': True,
        'results': results,
        'success_count': success_count,
        'error_count': error_count
    })


@app.route('/api/audio/<path:filename>')
def serve_audio(filename):
    """Serve audio files securely"""
    from urllib.parse import unquote
    from flask import Response, make_response
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
        # Fallback for common audio formats
        ext = os.path.splitext(file_path)[1].lower()
        mime_types = {
            '.m4a': 'audio/x-m4a',  # Changed to x-m4a for better Firefox compatibility
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
    
    # Create response with proper headers for Firefox
    response = make_response(send_from_directory(directory, basename, mimetype=mime_type))
    response.headers['Accept-Ranges'] = 'bytes'
    response.headers['Cache-Control'] = 'no-cache'
    return response


@app.route('/api/open/<path:filename>')
def open_audio(filename):
    """Reveal audio file in Finder"""
    from urllib.parse import unquote
    import subprocess
    
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


def generate_interactive_html(metadata_list, config_data):
    """Generate the interactive HTML with editing capabilities"""
    global audio_metadata, config
    audio_metadata = metadata_list
    config = config_data
    
    json_data = json.dumps(metadata_list, default=str, indent=2)
    
    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{config.get("report_title", "Peacock - Audio Library")}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        
        .stats {{
            display: flex;
            justify-content: center;
            gap: 30px;
            margin-top: 20px;
            flex-wrap: wrap;
        }}
        
        .stat-item {{
            background: rgba(255,255,255,0.2);
            padding: 15px 25px;
            border-radius: 8px;
        }}
        
        .stat-value {{
            font-size: 2em;
            font-weight: bold;
        }}
        
        .stat-label {{
            font-size: 0.9em;
            opacity: 0.9;
            margin-top: 5px;
        }}
        
        .controls {{
            padding: 20px 30px;
            background: #f8f9fa;
            border-bottom: 1px solid #dee2e6;
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
            align-items: center;
        }}
        
        .search-box {{
            flex: 1;
            min-width: 250px;
        }}
        
        .search-box input {{
            width: 100%;
            padding: 12px 20px;
            border: 2px solid #dee2e6;
            border-radius: 8px;
            font-size: 16px;
            transition: border-color 0.3s;
        }}
        
        .search-box input:focus {{
            outline: none;
            border-color: #667eea;
        }}
        
        .filter-group {{
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }}
        
        .filter-btn, .action-btn {{
            padding: 10px 20px;
            border: 2px solid #dee2e6;
            background: white;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s;
            font-size: 14px;
        }}
        
        .filter-btn:hover, .action-btn:hover {{
            border-color: #667eea;
            background: #f8f9ff;
        }}
        
        .filter-btn.active {{
            background: #667eea;
            color: white;
            border-color: #667eea;
        }}
        
        .action-btn.organize {{
            background: #28a745;
            color: white;
            border-color: #28a745;
        }}
        
        .action-btn.organize:hover {{
            background: #218838;
            border-color: #1e7e34;
        }}
        
        .table-container {{
            overflow-x: auto;
            padding: 30px;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        
        thead {{
            background: #f8f9fa;
            position: sticky;
            top: 0;
        }}
        
        th {{
            padding: 15px;
            text-align: left;
            font-weight: 600;
            color: #495057;
            border-bottom: 2px solid #dee2e6;
            cursor: pointer;
            user-select: none;
        }}
        
        th:hover {{
            background: #e9ecef;
        }}
        
        td {{
            padding: 15px;
            border-bottom: 1px solid #dee2e6;
            vertical-align: middle;
        }}
        
        tbody tr {{
            transition: background 0.2s;
        }}
        
        tbody tr:hover {{
            background: #f8f9ff;
        }}
        
        .play-btn {{
            background: #667eea;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
        }}
        
        .open-btn {{
            background: #48bb78;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            margin-left: 5px;
            transition: all 0.3s;
        }}
        
        .play-btn:hover {{
            background: #5568d3;
            transform: scale(1.05);
        }}
        
        .title-cell {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .title-text {{
            font-weight: 500;
            color: #667eea;
            flex: 1;
        }}
        
        .edit-btn {{
            background: none;
            border: none;
            cursor: pointer;
            opacity: 0.5;
            transition: opacity 0.3s;
            font-size: 16px;
            padding: 4px;
        }}
        
        .edit-btn:hover {{
            opacity: 1;
        }}
        
        .title-input {{
            flex: 1;
            padding: 6px 12px;
            border: 2px solid #667eea;
            border-radius: 4px;
            font-size: 14px;
        }}
        
        .title-actions {{
            display: flex;
            gap: 5px;
        }}
        
        .save-btn, .cancel-btn {{
            padding: 4px 12px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 13px;
        }}
        
        .save-btn {{
            background: #28a745;
            color: white;
        }}
        
        .cancel-btn {{
            background: #6c757d;
            color: white;
        }}
        
        /* Modal Styles */
        .modal {{
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
        }}
        
        .modal.active {{
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        
        .modal-content {{
            background: white;
            border-radius: 12px;
            max-width: 800px;
            max-height: 80vh;
            overflow-y: auto;
            padding: 30px;
            position: relative;
        }}
        
        .modal-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }}
        
        .modal-header h2 {{
            color: #667eea;
        }}
        
        .close-modal {{
            background: none;
            border: none;
            font-size: 28px;
            cursor: pointer;
            color: #6c757d;
        }}
        
        .suggestion-item {{
            padding: 15px;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            margin-bottom: 10px;
            display: flex;
            gap: 15px;
            align-items: center;
        }}
        
        .suggestion-checkbox {{
            width: 20px;
            height: 20px;
            cursor: pointer;
        }}
        
        .suggestion-details {{
            flex: 1;
        }}
        
        .suggestion-current {{
            color: #6c757d;
            text-decoration: line-through;
        }}
        
        .suggestion-new {{
            color: #28a745;
            font-weight: 600;
            margin-top: 5px;
        }}
        
        .modal-actions {{
            display: flex;
            gap: 10px;
            justify-content: flex-end;
            margin-top: 20px;
        }}
        
        .btn-primary {{
            background: #667eea;
            color: white;
            padding: 10px 24px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 16px;
        }}
        
        .btn-secondary {{
            background: #6c757d;
            color: white;
            padding: 10px 24px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 16px;
        }}
        
        .loading {{
            text-align: center;
            padding: 20px;
            color: #6c757d;
        }}
        
        .notification {{
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 20px;
            border-radius: 8px;
            background: white;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 2000;
            animation: slideIn 0.3s ease-out;
        }}
        
        .notification.success {{
            border-left: 4px solid #28a745;
        }}
        
        .notification.error {{
            border-left: 4px solid #dc3545;
        }}
        
        @keyframes slideIn {{
            from {{
                transform: translateX(400px);
                opacity: 0;
            }}
            to {{
                transform: translateX(0);
                opacity: 1;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🦚 {config.get("report_title", "Peacock - Audio Library")}</h1>
            <div class="stats">
                <div class="stat-item">
                    <div class="stat-value" id="totalCount">0</div>
                    <div class="stat-label">Total Files</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value" id="totalDuration">0:00</div>
                    <div class="stat-label">Total Duration</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value" id="totalSize">0 MB</div>
                    <div class="stat-label">Total Size</div>
                </div>
            </div>
        </div>
        
        <div class="controls">
            <div class="search-box">
                <input type="text" id="searchInput" placeholder="🔍 Search by title, filename, artist, album, comment...">
            </div>
            <button class="action-btn organize" onclick="showTitleOrganizer()">✨ Organize Titles</button>
            <div class="filter-group">
                <button class="filter-btn active" data-sort="default">Default Order</button>
                <button class="filter-btn" data-sort="duration">By Duration</button>
                <button class="filter-btn" data-sort="date">By Date</button>
                <button class="filter-btn" data-sort="title">By Title</button>
            </div>
        </div>
        
        <div class="table-container">
            <table id="recordingsTable">
                <thead>
                    <tr>
                        <th style="width: 30%;">Title</th>
                        <th style="width: 20%;">Filename</th>
                        <th>Duration</th>
                        <th>Size</th>
                        <th>Created</th>
                        <th>Artist</th>
                        <th>Play</th>
                    </tr>
                </thead>
                <tbody id="tableBody">
                </tbody>
            </table>
        </div>
    </div>
    
    <!-- Title Organizer Modal -->
    <div class="modal" id="organizerModal">
        <div class="modal-content">
            <div class="modal-header">
                <h2>✨ Title Organizer</h2>
                <button class="close-modal" onclick="closeOrganizer()">×</button>
            </div>
            <div id="organizerContent">
                <div class="loading">Loading suggestions...</div>
            </div>
            <div class="modal-actions">
                <button class="btn-secondary" onclick="closeOrganizer()">Cancel</button>
                <button class="btn-primary" onclick="applySelectedSuggestions()">Apply Selected</button>
            </div>
        </div>
    </div>
    
    <script>
        const API_BASE = 'http://localhost:5000/api';
        let recordings = {json_data};
        let filteredRecordings = [...recordings];
        let editingIndex = null;
        let suggestions = [];
        
        document.addEventListener('DOMContentLoaded', () => {{
            updateStats();
            renderTable();
            setupEventListeners();
        }});
        
        function updateStats() {{
            const totalCount = recordings.length;
            const totalDuration = recordings.reduce((sum, r) => sum + (r.duration || 0), 0);
            const totalSize = recordings.reduce((sum, r) => sum + (r.file_size || 0), 0);
            
            document.getElementById('totalCount').textContent = totalCount;
            document.getElementById('totalDuration').textContent = formatDuration(totalDuration);
            document.getElementById('totalSize').textContent = formatSize(totalSize);
        }}
        
        function formatDuration(seconds) {{
            if (!seconds) return '0:00';
            const hours = Math.floor(seconds / 3600);
            const minutes = Math.floor((seconds % 3600) / 60);
            const secs = Math.floor(seconds % 60);
            if (hours > 0) {{
                return `${{hours}}:${{minutes.toString().padStart(2, '0')}}:${{secs.toString().padStart(2, '0')}}`;
            }}
            return `${{minutes}}:${{secs.toString().padStart(2, '0')}}`;
        }}
        
        function formatSize(bytes) {{
            const units = ['B', 'KB', 'MB', 'GB'];
            let size = bytes;
            let unitIndex = 0;
            while (size >= 1024 && unitIndex < units.length - 1) {{
                size /= 1024;
                unitIndex++;
            }}
            return `${{size.toFixed(2)}} ${{units[unitIndex]}}`;
        }}
        
        function renderTable() {{
            const tbody = document.getElementById('tableBody');
            
            tbody.innerHTML = filteredRecordings.map((recording, index) => `
                <tr id="row-${{index}}">
                    <td>
                        <div class="title-cell">
                            <span class="title-text">${{recording.title || '<em>No title</em>'}}</span>
                            <button class="edit-btn" onclick="startEdit(${{index}})" title="Edit title">✏️</button>
                        </div>
                    </td>
                    <td>${{recording.filename}}</td>
                    <td>${{recording.duration_formatted}}</td>
                    <td>${{recording.file_size_formatted}}</td>
                    <td>${{new Date(recording.created_date).toLocaleDateString()}}</td>
                    <td>${{recording.artist || '-'}}</td>
                    <td>
                        <button class="play-btn" onclick="playRecording(${{index}})">▶ Play</button>
                        <button class="open-btn" onclick="openInPlayer(${{index}})">📂 Show</button>
                    </td>
                </tr>
            `).join('');
        }}
        
        function startEdit(index) {{
            if (editingIndex !== null) {{
                cancelEdit();
            }}
            
            editingIndex = index;
            const recording = filteredRecordings[index];
            const row = document.getElementById(`row-${{index}}`);
            const titleCell = row.querySelector('.title-cell');
            
            const currentTitle = recording.title || recording.filename;
            
            titleCell.innerHTML = `
                <input type="text" class="title-input" id="title-input-${{index}}" value="${{currentTitle}}" autofocus>
                <div class="title-actions">
                    <button class="save-btn" onclick="saveEdit(${{index}})">✓</button>
                    <button class="cancel-btn" onclick="cancelEdit()">✕</button>
                </div>
            `;
            
            document.getElementById(`title-input-${{index}}`).focus();
            document.getElementById(`title-input-${{index}}`).select();
        }}
        
        async function saveEdit(index) {{
            const newTitle = document.getElementById(`title-input-${{index}}`).value.trim();
            const recording = filteredRecordings[index];
            
            if (!newTitle) {{
                showNotification('Title cannot be empty', 'error');
                return;
            }}
            
            if (newTitle === recording.title) {{
                cancelEdit();
                return;
            }}
            
            // Confirm before saving
            if (!confirm(`Update title to "${{newTitle}}"?\\n\\nThis will modify the actual audio file metadata.`)) {{
                cancelEdit();
                return;
            }}
            
            try {{
                const response = await fetch(`${{API_BASE}}/update_title`, {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{
                        file_path: recording.file_path,
                        new_title: newTitle
                    }})
                }});
                
                const result = await response.json();
                
                if (result.success) {{
                    recording.title = newTitle;
                    // Update the original recordings array too
                    const origIndex = recordings.findIndex(r => r.file_path === recording.file_path);
                    if (origIndex !== -1) {{
                        recordings[origIndex].title = newTitle;
                    }}
                    editingIndex = null;
                    renderTable();
                    showNotification('Title updated successfully!', 'success');
                }} else {{
                    showNotification('Failed to update title: ' + result.error, 'error');
                }}
            }} catch (error) {{
                showNotification('Error updating title: ' + error.message, 'error');
            }}
        }}
        
        function cancelEdit() {{
            editingIndex = null;
            renderTable();
        }}
        
        async function showTitleOrganizer() {{
            const modal = document.getElementById('organizerModal');
            const content = document.getElementById('organizerContent');
            
            modal.classList.add('active');
            content.innerHTML = '<div class="loading">Analyzing titles and generating suggestions...</div>';
            
            try {{
                const response = await fetch(`${{API_BASE}}/suggest_titles`, {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }}
                }});
                
                suggestions = await response.json();
                
                if (suggestions.length === 0) {{
                    content.innerHTML = '<p style="text-align: center; padding: 40px; color: #6c757d;">All titles look good! No suggestions at this time.</p>';
                    return;
                }}
                
                content.innerHTML = `
                    <p style="margin-bottom: 20px; color: #6c757d;">
                        Found <strong>${{suggestions.length}}</strong> files that could have better titles. 
                        Select which changes you want to apply:
                    </p>
                    <div>
                        <label style="margin-bottom: 15px; display: block;">
                            <input type="checkbox" id="selectAll" onchange="toggleSelectAll()"> 
                            <strong>Select All</strong>
                        </label>
                    </div>
                    ${{suggestions.map((s, i) => `
                        <div class="suggestion-item">
                            <input type="checkbox" class="suggestion-checkbox" id="check-${{i}}" checked>
                            <div class="suggestion-details">
                                <div style="font-size: 12px; color: #6c757d;">${{s.filename}}</div>
                                <div class="suggestion-current">${{s.current_title}}</div>
                                <div class="suggestion-new">→ ${{s.suggested_title}}</div>
                            </div>
                        </div>
                    `).join('')}}
                `;
                
                document.getElementById('selectAll').checked = true;
            }} catch (error) {{
                content.innerHTML = `<p style="color: #dc3545; text-align: center;">Error loading suggestions: ${{error.message}}</p>`;
            }}
        }}
        
        function toggleSelectAll() {{
            const selectAll = document.getElementById('selectAll').checked;
            suggestions.forEach((_, i) => {{
                document.getElementById(`check-${{i}}`).checked = selectAll;
            }});
        }}
        
        function closeOrganizer() {{
            document.getElementById('organizerModal').classList.remove('active');
        }}
        
        async function applySelectedSuggestions() {{
            const selected = suggestions
                .map((s, i) => {{
                    if (document.getElementById(`check-${{i}}`).checked) {{
                        return {{
                            file_path: s.file_path,
                            new_title: s.suggested_title
                        }};
                    }}
                    return null;
                }})
                .filter(s => s !== null);
            
            if (selected.length === 0) {{
                showNotification('No changes selected', 'error');
                return;
            }}
            
            if (!confirm(`Apply ${{selected.length}} title changes?\\n\\nThis will modify the actual audio file metadata.`)) {{
                return;
            }}
            
            const content = document.getElementById('organizerContent');
            content.innerHTML = '<div class="loading">Applying changes...</div>';
            
            try {{
                const response = await fetch(`${{API_BASE}}/apply_title_suggestions`, {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ updates: selected }})
                }});
                
                const result = await response.json();
                
                closeOrganizer();
                
                if (result.success) {{
                    // Update local data
                    selected.forEach(update => {{
                        const recording = recordings.find(r => r.file_path === update.file_path);
                        if (recording) {{
                            recording.title = update.new_title;
                        }}
                    }});
                    
                    filteredRecordings = [...recordings];
                    renderTable();
                    showNotification(`Successfully updated ${{result.success_count}} titles!`, 'success');
                }} else {{
                    showNotification('Some updates failed. Check console for details.', 'error');
                }}
            }} catch (error) {{
                closeOrganizer();
                showNotification('Error applying changes: ' + error.message, 'error');
            }}
        }}
        
        function showNotification(message, type = 'success') {{
            const notification = document.createElement('div');
            notification.className = `notification ${{type}}`;
            notification.textContent = message;
            document.body.appendChild(notification);
            
            setTimeout(() => {{
                notification.remove();
            }}, 4000);
        }}
        
        function playRecording(index) {{
            const recording = filteredRecordings[index];
            const filename = encodeURIComponent(recording.filename);
            const audioUrl = `${{API_BASE}}/audio/${{filename}}`;
            
            // Create or get audio player
            let audioPlayer = document.getElementById('audioPlayer');
            if (!audioPlayer) {{
                audioPlayer = document.createElement('audio');
                audioPlayer.id = 'audioPlayer';
                audioPlayer.controls = true;
                audioPlayer.style.cssText = 'position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%); z-index: 2000; background: white; padding: 10px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.2);';
                document.body.appendChild(audioPlayer);
            }}
            
            audioPlayer.src = audioUrl;
            audioPlayer.load();
            audioPlayer.play().catch(err => {{
                console.error('Playback error:', err);
                showNotification('Error playing audio: ' + err.message, 'error');
            }});
            
            // Show now playing notification
            showNotification(`Playing: ${{recording.title || recording.filename}}`, 'success');
        }}
        
        function openInPlayer(index) {{
            const recording = filteredRecordings[index];
            const filename = encodeURIComponent(recording.filename);
            const openUrl = `${{API_BASE}}/open/${{filename}}`;
            
            // Call API to reveal file in Finder
            fetch(openUrl)
                .then(response => response.json())
                .then(data => {{
                    if (data.success) {{
                        showNotification(`Revealed in Finder: ${{recording.title || recording.filename}}`, 'success');
                    }} else {{
                        showNotification('Error: ' + data.error, 'error');
                    }}
                }})
                .catch(err => {{
                    console.error('Error:', err);
                    showNotification('Error revealing file', 'error');
                }});
        }}
        
        function setupEventListeners() {{
            document.getElementById('searchInput').addEventListener('input', (e) => {{
                const query = e.target.value.toLowerCase();
                filteredRecordings = recordings.filter(r => 
                    (r.title && r.title.toLowerCase().includes(query)) ||
                    (r.filename && r.filename.toLowerCase().includes(query)) ||
                    (r.artist && r.artist.toLowerCase().includes(query)) ||
                    (r.comment && r.comment.toLowerCase().includes(query))
                );
                renderTable();
            }});
            
            document.querySelectorAll('.filter-btn').forEach(btn => {{
                btn.addEventListener('click', () => {{
                    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
                    btn.classList.add('active');
                    
                    const sortType = btn.dataset.sort;
                    sortRecordings(sortType);
                }});
            }});
        }}
        
        function sortRecordings(type) {{
            switch(type) {{
                case 'duration':
                    filteredRecordings.sort((a, b) => (b.duration || 0) - (a.duration || 0));
                    break;
                case 'date':
                    filteredRecordings.sort((a, b) => new Date(b.created_date) - new Date(a.created_date));
                    break;
                case 'title':
                    filteredRecordings.sort((a, b) => (a.title || a.filename).localeCompare(b.title || b.filename));
                    break;
                default:
                    filteredRecordings = [...recordings];
            }}
            renderTable();
        }}
    </script>
</body>
</html>'''
    
    output_path = Path(__file__).parent / 'audio_library_interactive.html'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"\n✓ Interactive HTML generated: {output_path}")
    return str(output_path)


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Peacock Server - Interactive Audio Library')
    parser.add_argument('--generate', action='store_true', help='Generate the interactive HTML report')
    parser.add_argument('--port', type=int, default=5000, help='Port to run server on (default: 5000)')
    
    args = parser.parse_args()
    
    if args.generate:
        # Generate the interactive HTML
        print("Generating interactive report...")
        cfg = peacock.check_and_setup_config()
        
        extractor = peacock.PeacockkMetadataExtractor(cfg)
        metadata_list = extractor.scan_directory(cfg['default_path'])
        
        if not metadata_list:
            print("No audio files found.")
            return
        
        html_path = generate_interactive_html(metadata_list, cfg)
        
        print(f"\n✓ Successfully processed {len(metadata_list)} audio files")
        print(f"\nTo use the interactive features:")
        print(f"  1. Start the server: python peacock_server.py")
        print(f"  2. Open your browser to: http://localhost:{args.port}")
    else:
        # Start the Flask server
        global audio_metadata, config
        
        html_file = Path(__file__).parent / 'audio_library_interactive.html'
        if not html_file.exists():
            print("Please generate the interactive report first:")
            print("  python peacock_server.py --generate")
            return
        
        # Load config for security checks
        config = peacock.check_and_setup_config()
        
        # Load metadata
        print("Loading audio metadata...")
        extractor = peacock.PeacockkMetadataExtractor(config)
        audio_metadata = extractor.scan_directory(config['default_path'])
        print(f"Loaded {len(audio_metadata)} audio files")
        
        print("=" * 80)
        print("🦚 Peacock Interactive Server")
        print("=" * 80)
        print(f"\n✓ Server starting on http://localhost:{args.port}")
        print(f"✓ Open your browser to: http://localhost:{args.port}")
        print(f"\n  Features:")
        print(f"  • Edit titles with ✏️ icon")
        print(f"  • Organize titles with ✨ button")
        print(f"  • All changes update actual file metadata")
        print(f"\n  Press Ctrl+C to stop the server\n")
        
        app.run(debug=False, port=args.port)


if __name__ == '__main__':
    main()
