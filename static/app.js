const API_BASE = 'http://localhost:5000/api';
let recordings = [];
let filteredRecordings = [];
let editingIndex = null;
let suggestions = [];

// Initialize app when data is loaded
function initializeApp(audioData) {
    recordings = audioData;
    filteredRecordings = [...recordings];
    
    // Check if DOM is already ready (since script is at bottom of HTML)
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initUI);
    } else {
        initUI();
    }
}

function initUI() {
    updateStats();
    renderTable();
    setupEventListeners();
}

function updateStats() {
    const totalCount = recordings.length;
    const totalDuration = recordings.reduce((sum, r) => sum + (r.duration || 0), 0);
    const totalSize = recordings.reduce((sum, r) => sum + (r.file_size || 0), 0);
    
    document.getElementById('totalCount').textContent = totalCount;
    document.getElementById('totalDuration').textContent = formatDuration(totalDuration);
    document.getElementById('totalSize').textContent = formatSize(totalSize);
}

function formatDuration(seconds) {
    if (!seconds) return '0:00';
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    if (hours > 0) {
        return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
}

function formatSize(bytes) {
    const units = ['B', 'KB', 'MB', 'GB'];
    let size = bytes;
    let unitIndex = 0;
    while (size >= 1024 && unitIndex < units.length - 1) {
        size /= 1024;
        unitIndex++;
    }
    return `${size.toFixed(2)} ${units[unitIndex]}`;
}

function renderTable() {
    const tbody = document.getElementById('tableBody');
    
    tbody.innerHTML = filteredRecordings.map((recording, index) => `
        <tr id="row-${index}">
            <td>
                <div class="title-cell">
                    <span class="title-text">${recording.title || '<em>No title</em>'}</span>
                    <button class="edit-btn" onclick="startEdit(${index})" title="Edit title">✏️</button>
                </div>
            </td>
            <td>${recording.filename}</td>
            <td>${recording.duration_formatted}</td>
            <td>${recording.file_size_formatted}</td>
            <td>${new Date(recording.created_date).toLocaleDateString()}</td>
            <td>${new Date(recording.created_date).toLocaleDateString()}</td>
            <td>${recording.comment || '-'}</td>
            <td>${recording.artist || '-'}</td>
            <td>${recording.album || '-'}</td>
            <td>
                <div class="action-cell">
                    <button class="play-btn" onclick="playRecording(${index})">▶ Play</button>
                    <button class="open-btn" onclick="openInPlayer(${index})">📂 Show</button>
                </div>
            </td>
        </tr>
    `).join('');
}

function startEdit(index) {
    if (editingIndex !== null) {
        cancelEdit();
    }
    
    editingIndex = index;
    const recording = filteredRecordings[index];
    const row = document.getElementById(`row-${index}`);
    const titleCell = row.querySelector('.title-cell');
    
    const currentTitle = recording.title || recording.filename;
    
    titleCell.innerHTML = `
        <input type="text" class="title-input" id="title-input-${index}" value="${currentTitle}" autofocus>
        <div class="title-actions">
            <button class="save-btn" onclick="saveEdit(${index})">✓</button>
            <button class="cancel-btn" onclick="cancelEdit()">✕</button>
        </div>
    `;
    
    document.getElementById(`title-input-${index}`).focus();
    document.getElementById(`title-input-${index}`).select();
}

async function saveEdit(index) {
    const newTitle = document.getElementById(`title-input-${index}`).value.trim();
    const recording = filteredRecordings[index];
    
    if (!newTitle) {
        showNotification('Title cannot be empty', 'error');
        return;
    }
    
    if (newTitle === recording.title) {
        cancelEdit();
        return;
    }
    
    // Confirm before saving
    if (!confirm(`Update title to "${newTitle}"?\n\nThis will modify the actual audio file metadata.`)) {
        cancelEdit();
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/update_title`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                file_path: recording.file_path,
                new_title: newTitle
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            recording.title = newTitle;
            // Update the original recordings array too
            const origIndex = recordings.findIndex(r => r.file_path === recording.file_path);
            if (origIndex !== -1) {
                recordings[origIndex].title = newTitle;
            }
            editingIndex = null;
            renderTable();
            showNotification('Title updated successfully!', 'success');
        } else {
            showNotification('Failed to update title: ' + result.error, 'error');
        }
    } catch (error) {
        showNotification('Error updating title: ' + error.message, 'error');
    }
}

function cancelEdit() {
    editingIndex = null;
    renderTable();
}

async function showTitleOrganizer() {
    const modal = document.getElementById('organizerModal');
    const content = document.getElementById('organizerContent');
    
    modal.classList.add('active');
    content.innerHTML = '<div class="loading">Analyzing titles and generating suggestions...</div>';
    
    try {
        const response = await fetch(`${API_BASE}/suggest_titles`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        suggestions = await response.json();
        
        if (suggestions.length === 0) {
            content.innerHTML = '<p style="text-align: center; padding: 40px; color: #6c757d;">All titles look good! No suggestions at this time.</p>';
            return;
        }
        
        content.innerHTML = `
            <p style="margin-bottom: 20px; color: #6c757d;">
                Found <strong>${suggestions.length}</strong> files that could have better titles. 
                Select which changes you want to apply:
            </p>
            <div>
                <label style="margin-bottom: 15px; display: block;">
                    <input type="checkbox" id="selectAll" onchange="toggleSelectAll()"> 
                    <strong>Select All</strong>
                </label>
            </div>
            ${suggestions.map((s, i) => `
                <div class="suggestion-item">
                    <input type="checkbox" class="suggestion-checkbox" id="check-${i}" checked>
                    <div class="suggestion-details">
                        <div style="font-size: 12px; color: #6c757d;">${s.filename}</div>
                        <div class="suggestion-current">${s.current_title}</div>
                        <div class="suggestion-new">→ ${s.suggested_title}</div>
                    </div>
                </div>
            `).join('')}
        `;
        
        document.getElementById('selectAll').checked = true;
    } catch (error) {
        content.innerHTML = `<p style="color: #dc3545; text-align: center;">Error loading suggestions: ${error.message}</p>`;
    }
}

function toggleSelectAll() {
    const selectAll = document.getElementById('selectAll').checked;
    suggestions.forEach((_, i) => {
        document.getElementById(`check-${i}`).checked = selectAll;
    });
}

function closeOrganizer() {
    document.getElementById('organizerModal').classList.remove('active');
}

async function applySelectedSuggestions() {
    const selected = suggestions
        .map((s, i) => {
            if (document.getElementById(`check-${i}`).checked) {
                return {
                    file_path: s.file_path,
                    new_title: s.suggested_title
                };
            }
            return null;
        })
        .filter(s => s !== null);
    
    if (selected.length === 0) {
        showNotification('No changes selected', 'error');
        return;
    }
    
    if (!confirm(`Apply ${selected.length} title changes?\n\nThis will modify the actual audio file metadata.`)) {
        return;
    }
    
    const content = document.getElementById('organizerContent');
    content.innerHTML = '<div class="loading">Applying changes...</div>';
    
    try {
        const response = await fetch(`${API_BASE}/apply_title_suggestions`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ updates: selected })
        });
        
        const result = await response.json();
        
        closeOrganizer();
        
        if (result.success) {
            // Update local data
            selected.forEach(update => {
                const recording = recordings.find(r => r.file_path === update.file_path);
                if (recording) {
                    recording.title = update.new_title;
                }
            });
            
            filteredRecordings = [...recordings];
            renderTable();
            showNotification(`Successfully updated ${result.success_count} titles!`, 'success');
        } else {
            showNotification('Some updates failed. Check console for details.', 'error');
        }
    } catch (error) {
        closeOrganizer();
        showNotification('Error applying changes: ' + error.message, 'error');
    }
}

function showNotification(message, type = 'success') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 4000);
}

function playRecording(index) {
    const recording = filteredRecordings[index];
    const filename = encodeURIComponent(recording.filename);
    const audioUrl = `${API_BASE}/audio/${filename}`;
    
    // Create or get audio player
    let audioPlayer = document.getElementById('audioPlayer');
    if (!audioPlayer) {
        audioPlayer = document.createElement('audio');
        audioPlayer.id = 'audioPlayer';
        audioPlayer.controls = true;
        audioPlayer.style.cssText = 'position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%); z-index: 2000; background: white; padding: 10px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.2);';
        document.body.appendChild(audioPlayer);
    }
    
    audioPlayer.src = audioUrl;
    audioPlayer.load();
    audioPlayer.play().catch(err => {
        console.error('Playback error:', err);
        showNotification('Error playing audio: ' + err.message, 'error');
    });
    
    // Show now playing notification
    showNotification(`Playing: ${recording.title || recording.filename}`, 'success');
}

function openInPlayer(index) {
    const recording = filteredRecordings[index];
    const filename = encodeURIComponent(recording.filename);
    const openUrl = `${API_BASE}/open/${filename}`;
    
    // Call API to reveal file in Finder
    fetch(openUrl)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification(`Revealed in Finder: ${recording.title || recording.filename}`, 'success');
            } else {
                showNotification('Error: ' + data.error, 'error');
            }
        })
        .catch(err => {
            console.error('Error:', err);
            showNotification('Error revealing file', 'error');
        });
}

function setupEventListeners() {
    document.getElementById('searchInput').addEventListener('input', (e) => {
        const query = e.target.value.toLowerCase();
        filteredRecordings = recordings.filter(r => 
            (r.title && r.title.toLowerCase().includes(query)) ||
            (r.filename && r.filename.toLowerCase().includes(query)) ||
            (r.artist && r.artist.toLowerCase().includes(query)) ||
            (r.comment && r.comment.toLowerCase().includes(query))
        );
        renderTable();
    });
    
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            const sortType = btn.dataset.sort;
            sortRecordings(sortType);
        });
    });
    
    // Dark mode toggle
    const darkModeToggle = document.getElementById('darkModeToggle');
    if (darkModeToggle) {
        // Load saved preference
        const isDarkMode = localStorage.getItem('darkMode') === 'true';
        if (isDarkMode) {
            document.body.classList.add('dark-mode');
            darkModeToggle.textContent = '☀️ Light Mode';
        }
        
        darkModeToggle.addEventListener('click', () => {
            document.body.classList.toggle('dark-mode');
            const isNowDark = document.body.classList.contains('dark-mode');
            localStorage.setItem('darkMode', isNowDark);
            darkModeToggle.textContent = isNowDark ? '☀️ Light Mode' : '🌙 Dark Mode';
        });
    }
}

function sortRecordings(type) {
    switch(type) {
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
    }
    renderTable();
}
