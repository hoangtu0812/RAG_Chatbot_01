// BSR RAG Chatbot Main JS

let selectedModel = 'gemini';
let selectedGeminiModel = '';
let selectedLocalModel = '';
let chatHistory = [];

function toggleTheme() {
    console.log('toggleTheme called');
    const html = document.documentElement;
    const current = html.getAttribute('data-theme');
    const next = current === 'dark' ? 'light' : 'dark';
    html.setAttribute('data-theme', next);
    localStorage.setItem('theme', next);
    document.querySelector('.theme-toggle').textContent = next === 'dark' ? '☀️' : '🌙';
}

function setInitialTheme() {
    const saved = localStorage.getItem('theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const theme = saved || (prefersDark ? 'dark' : 'light');
    document.documentElement.setAttribute('data-theme', theme);
    document.querySelector('.theme-toggle').textContent = theme === 'dark' ? '☀️' : '🌙';
}

async function loadGeminiModels() {
    const select = document.getElementById('geminiModelSelect');
    select.innerHTML = '<option>Loading...</option>';
    try {
        const res = await fetch('/gemini-models');
        const data = await res.json();
        if (data.models && data.models.length > 0) {
            select.innerHTML = data.models.map(m => `<option value="${m}">${m}</option>`).join('');
            selectedGeminiModel = data.models[0];
        } else {
            select.innerHTML = '<option>No models found</option>';
        }
    } catch (e) {
        select.innerHTML = '<option>Error loading models</option>';
    }
}

async function loadLocalModels() {
    const select = document.getElementById('localModelSelect');
    select.innerHTML = '<option>Loading...</option>';
    try {
        const res = await fetch('/local-models');
        const data = await res.json();
        if (data.models && data.models.length > 0) {
            select.innerHTML = data.models.map(m => `<option value="${m}">${m}</option>`).join('');
            selectedLocalModel = data.models[0];
        } else {
            select.innerHTML = '<option>No models found</option>';
        }
    } catch (e) {
        select.innerHTML = '<option>Error loading models</option>';
    }
}

async function sendChatMessage() {
    const messageInput = document.getElementById('messageInput');
    const sendButton = document.getElementById('sendButton');
    const loading = document.getElementById('loading');
    const aiTyping = document.getElementById('aiTyping');
    const chatMessages = document.getElementById('chatMessages');
    
    const message = messageInput.value.trim();
    if (!message) return;
    
    addMessage(message, 'user');
    messageInput.value = '';
    sendButton.disabled = true;
    loading.classList.add('show');
    aiTyping.textContent = 'AI đang trả lời...';
    
    try {
        const payload = {
            message: message,
            model_type: selectedModel
        };
        if (selectedModel === 'gemini') {
            payload.model_name = document.getElementById('geminiModelSelect').value;
        }
        if (selectedModel === 'local') {
            payload.model_name = document.getElementById('localModelSelect').value;
        }
        
        const response = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await response.json();
        
        if (data.error) {
            addMessage(`Error: ${data.error}`, 'ai');
        } else {
            addMessage(data.response, 'ai', data.sources);
        }
    } catch (error) {
        addMessage(`Error: ${error.message}`, 'ai');
    } finally {
        loading.classList.remove('show');
        sendButton.disabled = false;
        messageInput.focus();
    }
}

function addMessage(content, sender, sources = null) {
    const chatMessages = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;
    
    const avatar = document.createElement('div');
    avatar.className = 'avatar';
    if (sender === 'user') {
        avatar.textContent = 'U';
    } else {
        const img = document.createElement('img');
        img.src = '/logoBSR.png';
        img.alt = 'AI Logo';
        avatar.appendChild(img);
    }
    
    const bubble = document.createElement('div');
    bubble.className = 'bubble';
    bubble.innerHTML = content;
    
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(bubble);
    
    if (sources && sources.length > 0) {
        const sourcesDiv = document.createElement('div');
        sourcesDiv.className = 'sources';
        sourcesDiv.innerHTML = `<span class="icon">📄</span> ${sources.map(s => `<span title="${s}">${s}</span>`).join(', ')}`;
        messageDiv.appendChild(sourcesDiv);
    }
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

async function uploadFiles() {
    const fileInput = document.getElementById('fileInput');
    const files = fileInput.files;
    if (files.length === 0) {
        showNotification('Vui lòng chọn file để upload', 'error');
        return;
    }
    const uploadButton = document.querySelector('.upload-button');
    const originalText = uploadButton.textContent;
    const progressContainer = document.getElementById('uploadProgressContainer');
    const progressBar = document.getElementById('uploadProgressBar');
    const progressLabel = document.getElementById('uploadProgressLabel');
    let uploading = true;
    window.onbeforeunload = function(e) {
        if (uploading) {
            e.preventDefault();
            e.returnValue = 'Tải lên đang diễn ra. Bạn có muốn dừng lại không?';
            return e.returnValue;
        }
    };
    progressContainer.style.display = '';
    progressBar.style.width = '0%';
    progressLabel.textContent = '0%';
    uploadButton.textContent = 'Uploading...';
    uploadButton.disabled = true;
    try {
        for (let file of files) {
            const maxSize = 50 * 1024 * 1024; // 50MB
            if (file.size > maxSize) {
                showNotification(`File ${file.name} quá lớn (${(file.size / 1024 / 1024).toFixed(1)}MB). Dung lượng tối đa: 50MB`, 'error');
                continue;
            }
            showNotification(`Uploading ${file.name}...`, 'info');
            const formData = new FormData();
            formData.append('file', file);
            await new Promise((resolve, reject) => {
                const xhr = new XMLHttpRequest();
                xhr.open('POST', '/upload', true);
                xhr.upload.onprogress = function(e) {
                    if (e.lengthComputable) {
                        const percent = Math.round((e.loaded / e.total) * 100);
                        progressBar.style.width = percent + '%';
                        progressLabel.textContent = percent + '%';
                    }
                };
                xhr.onload = function() {
                    if (xhr.status === 200) {
                        try {
                            const data = JSON.parse(xhr.responseText);
                            if (data.success) {
                                showNotification(data.message, 'success');
                                loadDocuments();
                                resolve();
                            } else {
                                showNotification(`Failed to upload ${file.name}: ${data.error}`, 'error');
                                resolve();
                            }
                        } catch (err) {
                            showNotification(`Lỗi upload: ${xhr.responseText}`, 'error');
                            resolve();
                        }
                    } else {
                        showNotification(`Failed to upload ${file.name}: Upload failed: ${xhr.status} ${xhr.statusText}`, 'error');
                        resolve();
                    }
                };
                xhr.onerror = function() {
                    showNotification(`Failed to upload ${file.name}: Network error`, 'error');
                    resolve();
                };
                xhr.send(formData);
            });
        }
    } catch (error) {
        showNotification(`Error uploading files: ${error.message}`, 'error');
    } finally {
        uploading = false;
        window.onbeforeunload = null;
        progressBar.style.width = '100%';
        progressLabel.textContent = '100%';
        setTimeout(() => {
            progressContainer.style.display = 'none';
        }, 800);
        uploadButton.textContent = originalText;
        uploadButton.disabled = false;
        fileInput.value = '';
    }
}

async function loadDocuments() {
    try {
        const response = await fetch('/documents');
        const data = await response.json();
        const documentsList = document.getElementById('documentsList');
        
        if (data.documents && data.documents.length > 0) {
            documentsList.innerHTML = data.documents.map(doc => 
                `<div class="document-item">${doc.source}</div>`
            ).join('');
        } else {
            documentsList.innerHTML = '<div class="document-item">Chưa có tài liệu nào</div>';
        }
    } catch (error) {
        showNotification('Lỗi tải danh sách tài liệu', 'error');
    }
}

function showNotification(message, type) {
    const notification = document.createElement('div');
    notification.className = type;
    notification.textContent = message;
    document.body.appendChild(notification);
    setTimeout(() => {
        notification.remove();
    }, 4000);
}

async function fetchSidebarStatus() {
    try {
        const res = await fetch('/vectorstore-status');
        const data = await res.json();
        
        document.getElementById('dbStatus').className = 'status-indicator ' + (data.db_connected ? 'status-green' : 'status-red');
        document.getElementById('geminiStatus').className = 'status-indicator ' + (data.model_status.gemini ? 'status-green' : 'status-red');
        document.getElementById('localStatus').className = 'status-indicator ' + (data.model_status.local ? 'status-green' : 'status-red');
        document.getElementById('statDocuments').textContent = data.total_documents;
        document.getElementById('statChunks').textContent = data.total_chunks;
    } catch (e) {
        document.getElementById('dbStatus').className = 'status-indicator status-red';
        document.getElementById('geminiStatus').className = 'status-indicator status-red';
        document.getElementById('localStatus').className = 'status-indicator status-red';
        document.getElementById('statDocuments').textContent = '0';
        document.getElementById('statChunks').textContent = '0';
    }
}

document.addEventListener('DOMContentLoaded', function() {
    setInitialTheme();

    // Model selection
    document.querySelectorAll('.model-option').forEach(option => {
        option.addEventListener('click', function() {
            document.querySelectorAll('.model-option').forEach(opt => opt.classList.remove('active'));
            this.classList.add('active');
            selectedModel = this.dataset.model;
            
            if (selectedModel === 'gemini') {
                document.getElementById('geminiModelSelectContainer').style.display = '';
                document.getElementById('localModelSelectContainer').style.display = 'none';
                loadGeminiModels();
            } else {
                document.getElementById('geminiModelSelectContainer').style.display = 'none';
                document.getElementById('localModelSelectContainer').style.display = '';
                loadLocalModels();
            }
        });
    });

    // Model select change events
    document.getElementById('geminiModelSelect').addEventListener('change', function() {
        selectedGeminiModel = this.value;
    });
    
    document.getElementById('localModelSelect').addEventListener('change', function() {
        selectedLocalModel = this.value;
    });

    // Upload button
    document.getElementById('uploadButton').addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        uploadFiles();
    });

    // Chat form
    const chatForm = document.getElementById('chatForm');
    const messageInput = document.getElementById('messageInput');
    const sendButton = document.getElementById('sendButton');
    
    chatForm.addEventListener('submit', function(e) {
        e.preventDefault();
        sendChatMessage();
    });

    // Enter to send
    messageInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendChatMessage();
        }
    });

    // Auto-resize textarea
    messageInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = Math.min(this.scrollHeight, 120) + 'px';
    });

    // File drag & drop
    const fileInputContainer = document.querySelector('.file-input-container');
    if (fileInputContainer) {
        // Click to open file dialog
        fileInputContainer.addEventListener('click', function(e) {
            // Don't trigger if clicking on the upload button
            if (!e.target.classList.contains('upload-button')) {
                document.getElementById('fileInput').click();
            }
        });
        
        // Show selected files info
        document.getElementById('fileInput').addEventListener('change', function(e) {
            const files = e.target.files;
            if (files.length > 0) {
                let fileInfo = '';
                for (let i = 0; i < files.length; i++) {
                    const file = files[i];
                    const sizeMB = (file.size / 1024 / 1024).toFixed(1);
                    fileInfo += `${file.name} (${sizeMB}MB)`;
                    if (i < files.length - 1) fileInfo += ', ';
                }
                showNotification(`Đã chọn: ${fileInfo}`, 'info');
            }
        });
        
        fileInputContainer.addEventListener('dragover', function(e) {
            e.preventDefault();
            fileInputContainer.classList.add('dragover');
        });
        fileInputContainer.addEventListener('dragleave', function(e) {
            e.preventDefault();
            fileInputContainer.classList.remove('dragover');
        });
        fileInputContainer.addEventListener('drop', function(e) {
            e.preventDefault();
            fileInputContainer.classList.remove('dragover');
            const files = e.dataTransfer.files;
            if (files.length) {
                document.getElementById('fileInput').files = files;
                // Trigger change event for drag & drop
                const event = new Event('change');
                document.getElementById('fileInput').dispatchEvent(event);
            }
        });
    }

    // Theme toggle button
    const themeToggle = document.querySelector('.theme-toggle');
    console.log('Theme toggle button found:', themeToggle);
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            console.log('Theme toggle clicked');
            toggleTheme();
        });
    } else {
        // Backup method if button not found immediately
        setTimeout(() => {
            const themeToggleBackup = document.querySelector('.theme-toggle');
            console.log('Theme toggle button backup found:', themeToggleBackup);
            if (themeToggleBackup) {
                themeToggleBackup.addEventListener('click', function() {
                    console.log('Theme toggle clicked (backup)');
                    toggleTheme();
                });
            }
        }, 100);
    }

    // Clear all button
    const clearAllBtn = document.getElementById('clearAllBtn');
    clearAllBtn.addEventListener('click', async function() {
        if (!confirm('Bạn có chắc chắn muốn xóa toàn bộ vectorstore?')) return;
        
        clearAllBtn.disabled = true;
        clearAllBtn.textContent = 'Đang xóa...';
        
        try {
            const res = await fetch('/clear-vectorstore', { method: 'POST' });
            const data = await res.json();
            
            if (data.success) {
                alert('Đã xóa toàn bộ vectorstore!');
                fetchSidebarStatus();
                loadDocuments();
            } else {
                alert('Lỗi: ' + (data.error || 'Không rõ'));
            }
        } catch (e) {
            alert('Lỗi: ' + e.message);
        }
        
        clearAllBtn.disabled = false;
        clearAllBtn.textContent = 'Clear All';
    });

    // Initialize
    loadDocuments();
    fetchSidebarStatus();
    setInterval(fetchSidebarStatus, 4000);
    
    // Additional theme toggle listener for safety
    window.addEventListener('click', function(e) {
        if (e.target.classList.contains('theme-toggle')) {
            console.log('Theme toggle clicked via window listener');
            toggleTheme();
        }
    });
}); 