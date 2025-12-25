"""
Metadata Manager - Handle audio file metadata extraction and updates
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

try:
    from mutagen import File
    from mutagen.mp4 import MP4
except ImportError:
    print("Error: mutagen library not installed.")
    print("Please install it using: pip install -r requirements.txt")
    exit(1)


class MetadataManager:
    """Manages audio file metadata extraction and updates"""
    
    AUDIO_EXTENSIONS = {'.m4a', '.mp3', '.wav', '.aac', '.flac', '.ogg', '.m4v', '.opus'}
    
    def __init__(self):
        pass
    
    def extract_metadata(self, file_path: str) -> Optional[Dict]:
        """
        Extract metadata from an audio file (READ-ONLY)
        
        Args:
            file_path: Path to the audio file
            
        Returns:
            Dictionary containing metadata or None if extraction fails
        """
        try:
            audio = File(file_path, easy=True)
            if audio is None:
                return None
            
            file_stat = os.stat(file_path)
            created_date = datetime.fromtimestamp(file_stat.st_ctime)
            
            metadata = {
                'filename': os.path.basename(file_path),
                'file_path': file_path,
                'title': self._get_tag(audio, 'title'),
                'artist': self._get_tag(audio, 'artist'),
                'album': self._get_tag(audio, 'album'),
                'genre': self._get_tag(audio, 'genre'),
                'date': self._get_tag(audio, 'date'),
                'comment': self._get_tag(audio, 'comment'),
                'duration': getattr(audio.info, 'length', 0),
                'duration_formatted': self._format_duration(getattr(audio.info, 'length', 0)),
                'bitrate': getattr(audio.info, 'bitrate', 0),
                'sample_rate': getattr(audio.info, 'sample_rate', 0),
                'file_size': file_stat.st_size,
                'file_size_formatted': self._format_size(file_stat.st_size),
                'created_date': created_date.isoformat(),
                'format': Path(file_path).suffix.lower()
            }
            
            return metadata
            
        except Exception as e:
            print(f"Error reading {file_path}: {str(e)}")
            return None
    
    def scan_directory(self, directory: str, recursive: bool = True) -> List[Dict]:
        """
        Scan directory for audio files and extract metadata
        
        Args:
            directory: Path to directory to scan
            recursive: Whether to scan subdirectories
            
        Returns:
            List of metadata dictionaries
        """
        audio_files = []
        
        if recursive:
            for root, _, files in os.walk(directory):
                for file in files:
                    if Path(file).suffix.lower() in self.AUDIO_EXTENSIONS:
                        audio_files.append(os.path.join(root, file))
        else:
            for file in os.listdir(directory):
                file_path = os.path.join(directory, file)
                if os.path.isfile(file_path) and Path(file).suffix.lower() in self.AUDIO_EXTENSIONS:
                    audio_files.append(file_path)
        
        print(f"Found {len(audio_files)} audio file(s)")
        
        metadata_list = []
        for i, file_path in enumerate(audio_files, 1):
            print(f"Processing {i}/{len(audio_files)}: {os.path.basename(file_path)}")
            metadata = self.extract_metadata(file_path)
            if metadata:
                metadata_list.append(metadata)
        
        return metadata_list
    
    def update_title(self, file_path: str, new_title: str) -> bool:
        """
        Update the title tag of an audio file (WRITE operation)
        
        Args:
            file_path: Path to the audio file
            new_title: New title to set
            
        Returns:
            True if successful, False otherwise
        """
        try:
            audio = File(file_path, easy=True)
            if audio is None:
                return False
            
            audio['title'] = new_title
            audio.save()
            return True
            
        except Exception as e:
            print(f"Error updating title for {file_path}: {str(e)}")
            return False
    
    def update_multiple_titles(self, updates: List[Dict[str, str]]) -> Dict:
        """
        Update titles for multiple files
        
        Args:
            updates: List of dicts with 'file_path' and 'new_title' keys
            
        Returns:
            Dict with success count and any errors
        """
        results = {
            'success_count': 0,
            'failed_count': 0,
            'errors': []
        }
        
        for update in updates:
            if self.update_title(update['file_path'], update['new_title']):
                results['success_count'] += 1
            else:
                results['failed_count'] += 1
                results['errors'].append({
                    'file': update['file_path'],
                    'error': 'Failed to update'
                })
        
        return results
    
    @staticmethod
    def _get_tag(audio, tag_name: str) -> Optional[str]:
        """Extract a single tag from audio metadata"""
        try:
            value = audio.get(tag_name, [''])[0]
            return value if value else None
        except (IndexError, TypeError):
            return None
    
    @staticmethod
    def _format_duration(seconds: float) -> str:
        """Format duration in seconds to HH:MM:SS or MM:SS"""
        if not seconds:
            return "0:00"
        
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        return f"{minutes}:{secs:02d}"
    
    @staticmethod
    def _format_size(bytes_size: int) -> str:
        """Format file size in bytes to human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_size < 1024.0:
                return f"{bytes_size:.2f} {unit}"
            bytes_size /= 1024.0
        return f"{bytes_size:.2f} PB"
