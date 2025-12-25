"""
Title Suggester - Generate smart title suggestions for audio files
"""

import re
from datetime import datetime
from typing import Dict, List


class TitleSuggester:
    """Generate intelligent title suggestions for audio files"""
    
    def __init__(self):
        # Common patterns for voice memo filenames
        self.date_pattern = re.compile(r'(\d{4})(\d{2})(\d{2})')
    
    def generate_suggestion(self, metadata: Dict) -> str:
        """
        Generate a suggested title for an audio file
        
        Args:
            metadata: File metadata dictionary
            
        Returns:
            Suggested title string
        """
        filename = metadata.get('filename', '')
        current_title = metadata.get('title', '')
        
        # If there's already a good title, keep it
        if current_title and not self._is_generic_title(current_title, filename):
            return current_title
        
        # Try to extract date from filename
        suggested = self._extract_date_based_title(filename)
        if suggested:
            return suggested
        
        # Clean up filename as fallback
        return self._clean_filename(filename)
    
    def get_suggestions_for_library(self, metadata_list: List[Dict]) -> List[Dict]:
        """
        Get title suggestions for multiple files
        
        Args:
            metadata_list: List of metadata dictionaries
            
        Returns:
            List of suggestion dictionaries with current and suggested titles
        """
        suggestions = []
        
        for metadata in metadata_list:
            current_title = metadata.get('title') or metadata.get('filename', '')
            suggested_title = self.generate_suggestion(metadata)
            
            # Only suggest if different from current
            if suggested_title != current_title:
                suggestions.append({
                    'file_path': metadata['file_path'],
                    'filename': metadata['filename'],
                    'current_title': current_title,
                    'suggested_title': suggested_title
                })
        
        return suggestions
    
    def _is_generic_title(self, title: str, filename: str) -> bool:
        """Check if title is generic/unhelpful"""
        # Title is same as filename (without extension)
        if title == filename.rsplit('.', 1)[0]:
            return True
        
        # Title looks like a timestamp
        if re.match(r'^\d{8}[\s_-]?\d{6}', title):
            return True
        
        # Very short titles (likely not descriptive)
        if len(title) < 3:
            return True
        
        return False
    
    def _extract_date_based_title(self, filename: str) -> str:
        """Extract and format date from filename"""
        match = self.date_pattern.search(filename)
        if match:
            year, month, day = match.groups()
            try:
                date_obj = datetime(int(year), int(month), int(day))
                return f"Recording {date_obj.strftime('%B %d, %Y')}"
            except ValueError:
                pass
        
        return ""
    
    def _clean_filename(self, filename: str) -> str:
        """Clean up filename to make a reasonable title"""
        # Remove extension
        title = filename.rsplit('.', 1)[0]
        
        # Replace underscores and hyphens with spaces
        title = title.replace('_', ' ').replace('-', ' ')
        
        # Remove common noise patterns
        title = re.sub(r'\d{8}\s*\d{6}', '', title)  # Remove timestamps
        title = re.sub(r'\s+', ' ', title)  # Normalize whitespace
        title = title.strip()
        
        # Capitalize first letter
        if title:
            title = title[0].upper() + title[1:]
        
        return title or filename
