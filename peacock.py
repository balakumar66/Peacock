#!/usr/bin/env python3
"""
Peacock - Audio Library Organizer
Generate interactive HTML reports from audio file metadata
Supports all audio formats: MP3, M4A, WAV, FLAC, AAC, and more
"""

import os
import json
import sys
from pathlib import Path
from datetime import datetime
from urllib.parse import quote
import argparse

try:
    from mutagen import File
    from mutagen.mp4 import MP4
except ImportError:
    print("Error: mutagen library not installed.")
    print("Please install it using: pip install -r requirements.txt")
    exit(1)


def run_setup_wizard():
    """Interactive setup wizard for first-time configuration"""
    print("=" * 80)
    print("🦚 Welcome to Peacock - Audio Library Organizer")
    print("=" * 80)
    print("\nFirst-time setup - Let's configure your settings\n")
    
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
    print("\nEnter a title for your audio library report:")
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
        json.dump(config, indent=2, fp=f)
    
    print("\n✓ Configuration saved!")
    print(f"✓ Config file: {config_path}")
    print(f"✓ Default path: {default_path}")
    print(f"✓ Report title: {report_title}\n")
    
    return config


def check_and_setup_config():
    """Check if config exists, if not run setup wizard"""
    config_path = Path(__file__).parent / 'config.json'
    
    if not config_path.exists():
        print("\n⚠️  No configuration file found.\n")
        return run_setup_wizard()
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        return config
    except json.JSONDecodeError:
        print("\n⚠️  Configuration file is corrupted.\n")
        return run_setup_wizard()


class PeacockkMetadataExtractor:
    """Extract metadata from audio files (READ-ONLY operations)"""
    
    def __init__(self, config=None):
        self.config = config or self.load_config()
        self.audio_extensions = {'.m4a', '.mp3', '.wav', '.aac', '.flac', '.ogg', '.m4v', '.opus'}
    
    @staticmethod
    def load_config():
        """Load configuration from config.json if exists"""
        config_path = Path(__file__).parent / 'config.json'
        if config_path.exists():
            with open(config_path, 'r') as f:
                return json.load(f)
        return {}
    
    @staticmethod
    def format_duration(seconds):
        """Convert seconds to HH:MM:SS format"""
        if seconds is None:
            return "Unknown"
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"
    
    @staticmethod
    def format_size(bytes_size):
        """Convert bytes to human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_size < 1024.0:
                return f"{bytes_size:.2f} {unit}"
            bytes_size /= 1024.0
        return f"{bytes_size:.2f} TB"
    
    def extract_metadata(self, file_path):
        """Extract metadata from an audio file (READ-ONLY)"""
        try:
            audio = File(file_path)
            
            if audio is None:
                return None
            
            metadata = {
                'filename': os.path.basename(file_path),
                'file_path': file_path,
                'file_size': os.path.getsize(file_path),
                'file_size_formatted': self.format_size(os.path.getsize(file_path)),
                'duration': getattr(audio.info, 'length', None),
                'duration_formatted': self.format_duration(getattr(audio.info, 'length', None)),
                'bitrate': getattr(audio.info, 'bitrate', None),
                'sample_rate': getattr(audio.info, 'sample_rate', None),
                'title': None,
                'artist': None,
                'album': None,
                'date': None,
                'comment': None,
                'genre': None,
            }
            
            # Extract tags based on file type
            if isinstance(audio, MP4):
                metadata['title'] = audio.get('\xa9nam', [None])[0]
                metadata['artist'] = audio.get('\xa9ART', [None])[0]
                metadata['album'] = audio.get('\xa9alb', [None])[0]
                metadata['date'] = audio.get('\xa9day', [None])[0]
                metadata['comment'] = audio.get('\xa9cmt', [None])[0]
                metadata['genre'] = audio.get('\xa9gen', [None])[0]
            else:
                metadata['title'] = audio.get('title', [None])[0] if audio.get('title') else None
                metadata['artist'] = audio.get('artist', [None])[0] if audio.get('artist') else None
                metadata['album'] = audio.get('album', [None])[0] if audio.get('album') else None
                metadata['date'] = audio.get('date', [None])[0] if audio.get('date') else None
                metadata['comment'] = audio.get('comment', [None])[0] if audio.get('comment') else None
            
            # File timestamps
            metadata['modified_date'] = datetime.fromtimestamp(os.path.getmtime(file_path))
            metadata['created_date'] = datetime.fromtimestamp(os.path.getctime(file_path))
            
            return metadata
        
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return None
    
    def scan_directory(self, directory_path):
        """Scan directory for audio files and extract all metadata"""
        if not os.path.exists(directory_path):
            print(f"Error: Directory '{directory_path}' does not exist.")
            return []
        
        audio_files = []
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                if Path(file).suffix.lower() in self.audio_extensions:
                    audio_files.append(os.path.join(root, file))
        
        print(f"Found {len(audio_files)} audio file(s)")
        
        metadata_list = []
        for i, file_path in enumerate(sorted(audio_files), 1):
            print(f"Processing {i}/{len(audio_files)}: {os.path.basename(file_path)}")
            metadata = self.extract_metadata(file_path)
            if metadata:
                metadata_list.append(metadata)
        
        return metadata_list


class HTMLReportGenerator:
    """Generate interactive HTML reports with search and playback"""
    
    def __init__(self, config=None):
        self.config = config or {}
        self.title = self.config.get('report_title', 'Peacock - Audio Library')
    
    def generate_html(self, metadata_list, output_path):
        """Generate interactive HTML report"""
        html_content = self._generate_html_template(metadata_list)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"\n✓ HTML report generated: {output_path}")
        print(f"✓ Open it in your browser to view and play recordings")
    
    def _generate_html_template(self, metadata_list):
        """Generate the complete HTML template"""
        # Convert metadata to JSON for JavaScript
        json_data = json.dumps(metadata_list, default=str, indent=2)
        
        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.title}</title>
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
        
        .filter-btn {{
            padding: 10px 20px;
            border: 2px solid #dee2e6;
            background: white;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s;
            font-size: 14px;
        }}
        
        .filter-btn:hover {{
            border-color: #667eea;
            background: #f8f9ff;
        }}
        
        .filter-btn.active {{
            background: #667eea;
            color: white;
            border-color: #667eea;
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
        
        th.sortable::after {{
            content: ' ⇅';
            opacity: 0.3;
        }}
        
        th.sorted-asc::after {{
            content: ' ↑';
            opacity: 1;
        }}
        
        th.sorted-desc::after {{
            content: ' ↓';
            opacity: 1;
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
            transition: all 0.3s;
        }}
        
        .play-btn:hover {{
            background: #5568d3;
            transform: scale(1.05);
        }}
        
        .title-cell {{
            font-weight: 500;
            color: #667eea;
        }}
        
        .no-results {{
            text-align: center;
            padding: 50px;
            color: #6c757d;
            font-size: 18px;
        }}
        
        .audio-player {{
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background: white;
            padding: 15px 30px;
            box-shadow: 0 -5px 20px rgba(0,0,0,0.1);
            display: none;
            z-index: 1000;
        }}
        
        .audio-player.active {{
            display: block;
        }}
        
        .audio-info {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }}
        
        .audio-title {{
            font-weight: 600;
            color: #667eea;
        }}
        
        .close-player {{
            background: none;
            border: none;
            font-size: 24px;
            cursor: pointer;
            color: #6c757d;
        }}
        
        audio {{
            width: 100%;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🦚 {self.title}</h1>
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
                        <th class="sortable" data-column="title">Title</th>
                        <th class="sortable" data-column="filename">Filename</th>
                        <th class="sortable" data-column="duration">Duration</th>
                        <th class="sortable" data-column="file_size">Size</th>
                        <th class="sortable" data-column="created_date">Created</th>
                        <th class="sortable" data-column="artist">Artist</th>
                        <th class="sortable" data-column="comment">Comment</th>
                        <th>Play</th>
                    </tr>
                </thead>
                <tbody id="tableBody">
                </tbody>
            </table>
            <div id="noResults" class="no-results" style="display: none;">
                No audio files found matching your search.
            </div>
        </div>
    </div>
    
    <div class="audio-player" id="audioPlayer">
        <div class="audio-info">
            <span class="audio-title" id="nowPlaying">Now Playing</span>
            <button class="close-player" onclick="closePlayer()">×</button>
        </div>
        <audio id="audioElement" controls></audio>
    </div>
    
    <script>
        // Data
        const recordings = {json_data};
        let filteredRecordings = [...recordings];
        let currentSort = null;
        let sortDirection = 'asc';
        
        // Initialize
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
            const noResults = document.getElementById('noResults');
            
            if (filteredRecordings.length === 0) {{
                tbody.innerHTML = '';
                noResults.style.display = 'block';
                return;
            }}
            
            noResults.style.display = 'none';
            
            tbody.innerHTML = filteredRecordings.map((recording, index) => `
                <tr>
                    <td class="title-cell">${{recording.title || '<em>No title</em>'}}</td>
                    <td>${{recording.filename}}</td>
                    <td>${{recording.duration_formatted}}</td>
                    <td>${{recording.file_size_formatted}}</td>
                    <td>${{new Date(recording.created_date).toLocaleDateString()}}</td>
                    <td>${{recording.artist || '-'}}</td>
                    <td>${{recording.comment || '-'}}</td>
                    <td>
                        <button class="play-btn" onclick="playRecording(${{index}})">▶ Play</button>
                    </td>
                </tr>
            `).join('');
        }}
        
        function playRecording(index) {{
            const recording = filteredRecordings[index];
            const player = document.getElementById('audioPlayer');
            const audio = document.getElementById('audioElement');
            const nowPlaying = document.getElementById('nowPlaying');
            
            audio.src = 'file://' + recording.file_path;
            nowPlaying.textContent = `Now Playing: ${{recording.title || recording.filename}}`;
            player.classList.add('active');
            audio.play();
        }}
        
        function closePlayer() {{
            const player = document.getElementById('audioPlayer');
            const audio = document.getElementById('audioElement');
            audio.pause();
            player.classList.remove('active');
        }}
        
        function setupEventListeners() {{
            // Search
            document.getElementById('searchInput').addEventListener('input', (e) => {{
                const query = e.target.value.toLowerCase();
                filteredRecordings = recordings.filter(r => 
                    (r.title && r.title.toLowerCase().includes(query)) ||
                    (r.filename && r.filename.toLowerCase().includes(query)) ||
                    (r.artist && r.artist.toLowerCase().includes(query)) ||
                    (r.comment && r.comment.toLowerCase().includes(query)) ||
                    (r.album && r.album.toLowerCase().includes(query))
                );
                renderTable();
            }});
            
            // Filter buttons
            document.querySelectorAll('.filter-btn').forEach(btn => {{
                btn.addEventListener('click', () => {{
                    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
                    btn.classList.add('active');
                    
                    const sortType = btn.dataset.sort;
                    sortRecordings(sortType);
                }});
            }});
            
            // Column sorting
            document.querySelectorAll('th.sortable').forEach(th => {{
                th.addEventListener('click', () => {{
                    const column = th.dataset.column;
                    sortByColumn(column, th);
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
        
        function sortByColumn(column, headerElement) {{
            // Toggle sort direction
            if (currentSort === column) {{
                sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
            }} else {{
                sortDirection = 'asc';
                currentSort = column;
            }}
            
            // Update header classes
            document.querySelectorAll('th.sortable').forEach(th => {{
                th.classList.remove('sorted-asc', 'sorted-desc');
            }});
            headerElement.classList.add(sortDirection === 'asc' ? 'sorted-asc' : 'sorted-desc');
            
            // Sort data
            filteredRecordings.sort((a, b) => {{
                let aVal = a[column] || '';
                let bVal = b[column] || '';
                
                // Handle different data types
                if (column === 'duration' || column === 'file_size') {{
                    aVal = parseFloat(aVal) || 0;
                    bVal = parseFloat(bVal) || 0;
                }} else if (column === 'created_date') {{
                    aVal = new Date(aVal);
                    bVal = new Date(bVal);
                }}
                
                if (aVal < bVal) return sortDirection === 'asc' ? -1 : 1;
                if (aVal > bVal) return sortDirection === 'asc' ? 1 : -1;
                return 0;
            }});
            
            renderTable();
        }}
    </script>
</body>
</html>'''
        
        return html


def main():
    parser = argparse.ArgumentParser(
        description='Peacock - Generate interactive HTML reports from audio file metadata'
    )
    parser.add_argument(
        'path',
        nargs='?',
        help='Path to audio files directory'
    )
    parser.add_argument(
        '-o', '--output',
        default='audio_library_report.html',
        help='Output HTML file path (default: audio_library_report.html)'
    )
    parser.add_argument(
        '-c', '--config',
        help='Path to config.json file'
    )
    parser.add_argument(
        '--setup',
        action='store_true',
        help='Run setup wizard to configure or reconfigure settings'
    )
    
    args = parser.parse_args()
    
    # Run setup if requested
    if args.setup:
        run_setup_wizard()
        print("\nSetup complete! Run peacock.py again to generate your report.\n")
        return
    
    # Load config
    if args.config and os.path.exists(args.config):
        with open(args.config, 'r') as f:
            config = json.load(f)
    else:
        config = check_and_setup_config()
    
    # Get recordings path
    if args.path:
        recordings_path = args.path
    elif 'default_path' in config:
        recordings_path = config['default_path']
    else:
        recordings_path = input("Enter path to audio files directory: ").strip()
    
    print("=" * 80)
    print("🦚 Peacock - Audio Library Organizer")
    print("=" * 80)
    print(f"\nScanning: {recordings_path}\n")
    
    # Extract metadata
    extractor = PeacockkMetadataExtractor(config)
    metadata_list = extractor.scan_directory(recordings_path)
    
    if not metadata_list:
        print("\nNo audio files found or processed.")
        return
    
    # Generate HTML report
    generator = HTMLReportGenerator(config)
    generator.generate_html(metadata_list, args.output)
    
    print(f"\n✓ Successfully processed {len(metadata_list)} audio files")
    print(f"✓ Report saved to: {os.path.abspath(args.output)}")
    print(f"\nOpen the HTML file in your browser to view and play your audio files!")
    print(f"\n💡 Tip: Run 'python peacock.py --setup' to change your configuration anytime.")


if __name__ == "__main__":
    main()
