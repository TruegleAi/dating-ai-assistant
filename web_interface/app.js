// Munch AI Dating Assistant - Frontend App
const API_URL = '';

// State
let currentUser = null;
let currentConversation = null;
let selectedResponseType = 'Dating App';
let conversations = [];

// ==================== INITIALIZATION ====================
document.addEventListener('DOMContentLoaded', () => {
    checkHealth();
    setupResponseTypeButtons();
    loadOrCreateUser();

    // Add SVG gradient definition for progress ring
    addProgressGradient();
});

function addProgressGradient() {
    const svg = document.querySelector('.progress-ring');
    if (svg) {
        const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
        defs.innerHTML = `
            <linearGradient id="progressGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" style="stop-color:#00D4FF;stop-opacity:1" />
                <stop offset="50%" style="stop-color:#FFB800;stop-opacity:1" />
                <stop offset="100%" style="stop-color:#FF8C00;stop-opacity:1" />
            </linearGradient>
        `;
        svg.insertBefore(defs, svg.firstChild);
    }
}

// ==================== HEALTH CHECK ====================
async function checkHealth() {
    try {
        const response = await fetch(`${API_URL}/health`);
        if (response.ok) {
            document.getElementById('status-indicator').classList.add('online');
            document.getElementById('status-text').textContent = 'Connected';
        } else {
            throw new Error('API not responding');
        }
    } catch (error) {
        document.getElementById('status-indicator').classList.add('offline');
        document.getElementById('status-text').textContent = 'Disconnected';
        console.error('Health check failed:', error);
    }
}

// ==================== USER MANAGEMENT ====================
async function loadOrCreateUser() {
    // Try to get user from localStorage
    const storedUserId = localStorage.getItem('munch_user_id');
    const storedEmail = localStorage.getItem('munch_user_email');

    if (storedUserId && storedEmail) {
        try {
            const response = await fetch(`${API_URL}/api/users/${storedEmail}`);
            if (response.ok) {
                const data = await response.json();
                currentUser = data.user;
                loadConversations();
                loadUserStats();
                return;
            }
        } catch (e) {
            console.log('Could not load stored user');
        }
    }

    // Create a new anonymous user
    const email = `user_${Date.now()}@munch.local`;
    try {
        const response = await fetch(`${API_URL}/api/users`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, subscription_tier: 'free' })
        });

        if (response.ok) {
            const data = await response.json();
            currentUser = data.user;
            localStorage.setItem('munch_user_id', currentUser.id);
            localStorage.setItem('munch_user_email', currentUser.email);
            loadConversations();
        }
    } catch (e) {
        console.error('Could not create user:', e);
    }
}

async function loadUserStats() {
    if (!currentUser) return;

    try {
        const response = await fetch(`${API_URL}/api/users/${currentUser.id}/stats`);
        if (response.ok) {
            const data = await response.json();
            updateSidebarStats(data.stats);
        }
    } catch (e) {
        console.error('Could not load stats:', e);
    }
}

function updateSidebarStats(stats) {
    const total = stats.total_conversations || 1;
    const successRate = Math.round((stats.success / total) * 100) || 0;
    const failureRate = Math.round((stats.ghosted / total) * 100) || 0;
    const chemistryScore = stats.avg_chemistry_score || 0;

    // Update progress ring
    updateProgressRing(chemistryScore);

    // Update text values
    document.getElementById('chemistry-score').textContent = `${chemistryScore}%`;
    document.getElementById('success-rate').textContent = `${successRate}%`;
    document.getElementById('failure-rate').textContent = `${failureRate}%`;
}

function updateProgressRing(percentage) {
    const circle = document.getElementById('progress-circle');
    if (circle) {
        const circumference = 2 * Math.PI * 52; // r = 52
        const offset = circumference - (percentage / 100) * circumference;
        circle.style.strokeDasharray = `${circumference}`;
        circle.style.strokeDashoffset = offset;
    }
}

// ==================== SIDEBAR ====================
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebar-overlay');

    sidebar.classList.toggle('active');
    overlay.classList.toggle('active');
}

function closeSidebar() {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebar-overlay');

    sidebar.classList.remove('active');
    overlay.classList.remove('active');
}

// ==================== CONVERSATIONS ====================
async function loadConversations() {
    if (!currentUser) return;

    try {
        const response = await fetch(`${API_URL}/api/conversations?user_id=${currentUser.id}`);
        if (response.ok) {
            const data = await response.json();
            conversations = data.conversations || [];
            renderConversationList();
        }
    } catch (e) {
        console.error('Could not load conversations:', e);
    }
}

function renderConversationList() {
    const container = document.getElementById('conversation-list');

    if (conversations.length === 0) {
        container.innerHTML = `
            <div class="empty-state">No conversations yet</div>
            <button class="btn-new-conv" onclick="showNewConversationModal()">+ New Conversation</button>
        `;
        return;
    }

    let html = conversations.map(conv => {
        const statusClass = conv.status.toLowerCase();
        const statusIcon = getStatusIcon(conv.status);
        const isActive = currentConversation && currentConversation.id === conv.id;

        return `
            <div class="conversation-item ${isActive ? 'active' : ''}" onclick="selectConversation(${conv.id})">
                <span class="conv-name">${conv.name}</span>
                <div class="conv-status ${statusClass}">
                    ${conv.chemistry_score}% ${statusIcon}
                    <span class="conv-arrow">›</span>
                </div>
            </div>
        `;
    }).join('');

    html += `<button class="btn-new-conv" onclick="showNewConversationModal()" style="margin-top: 12px; width: 100%; padding: 12px; background: transparent; border: 1px dashed var(--border); border-radius: 12px; color: var(--text-secondary); cursor: pointer;">+ New Conversation</button>`;

    container.innerHTML = html;
}

function getStatusIcon(status) {
    switch (status.toLowerCase()) {
        case 'success': return '✓';
        case 'stalled': return '⏳';
        case 'ghosted': return '👻';
        default: return '';
    }
}

async function selectConversation(convId) {
    try {
        const response = await fetch(`${API_URL}/api/conversations/${convId}`);
        if (response.ok) {
            const data = await response.json();
            currentConversation = data.conversation;

            // Update AI tip with latest analysis
            if (data.conversation.chemistry_score > 0) {
                updateAITip(`Chemistry score: ${data.conversation.chemistry_score}%. Keep building rapport!`);
            }

            renderConversationList();
            closeSidebar();
        }
    } catch (e) {
        console.error('Could not load conversation:', e);
    }
}

function updateAITip(tip) {
    document.getElementById('ai-tip-text').textContent = tip;
}

// ==================== NEW CONVERSATION MODAL ====================
function showNewConversationModal() {
    document.getElementById('new-conv-modal').classList.remove('hidden');
}

function closeModal() {
    document.getElementById('new-conv-modal').classList.add('hidden');
    document.getElementById('conv-name').value = '';
}

async function createConversation() {
    const name = document.getElementById('conv-name').value.trim();
    const type = document.getElementById('conv-type').value;

    if (!name) {
        alert('Please enter a name for this conversation');
        return;
    }

    if (!currentUser) {
        alert('Please wait for user initialization');
        return;
    }

    try {
        const response = await fetch(`${API_URL}/api/conversations`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: currentUser.id,
                name: name,
                response_type: type
            })
        });

        if (response.ok) {
            const data = await response.json();
            currentConversation = data.conversation;
            closeModal();
            loadConversations();
        } else {
            throw new Error('Failed to create conversation');
        }
    } catch (e) {
        console.error('Error creating conversation:', e);
        alert('Could not create conversation');
    }
}

// ==================== RESPONSE TYPE SELECTOR ====================
function setupResponseTypeButtons() {
    const buttons = document.querySelectorAll('.type-btn');
    buttons.forEach(btn => {
        btn.addEventListener('click', () => {
            buttons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            selectedResponseType = btn.dataset.type;
        });
    });
}

// ==================== FILE UPLOAD ====================
function triggerUpload() {
    document.getElementById('file-upload').click();
}

async function handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    // Show loading
    const input = document.getElementById('message-input');
    input.value = 'Analyzing screenshot...';
    input.disabled = true;

    try {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(`${API_URL}/api/image/upload`, {
            method: 'POST',
            body: formData
        });

        if (response.ok) {
            const data = await response.json();

            // Format extracted messages
            if (data.messages && data.messages.length > 0) {
                const formatted = data.messages.map(m =>
                    `${m.sender === 'user' ? 'Me' : 'Her'}: ${m.content}`
                ).join('\n');
                input.value = formatted;
            } else {
                input.value = 'Could not extract messages from image. Try pasting them manually.';
            }
        } else {
            input.value = 'Failed to analyze image. Please paste messages manually.';
        }
    } catch (e) {
        console.error('Upload error:', e);
        input.value = 'Error analyzing image. Please paste messages manually.';
    } finally {
        input.disabled = false;
        event.target.value = ''; // Reset file input
    }
}

// ==================== MAIN ANALYSIS ====================
async function analyzeConversation() {
    const input = document.getElementById('message-input');
    const text = input.value.trim();

    if (!text) {
        alert('Please enter or paste conversation messages');
        return;
    }

    // Show loading
    const btn = document.querySelector('.btn-analyze');
    const originalText = btn.textContent;
    btn.textContent = 'Analyzing...';
    btn.disabled = true;

    const resultsSection = document.getElementById('results-section');
    const suggestionText = document.getElementById('suggestion-text');

    resultsSection.classList.remove('hidden');
    suggestionText.innerHTML = '<div class="loading">Getting AI suggestion</div>';

    try {
        // If we have a current conversation, add messages and analyze
        if (currentConversation) {
            // Parse and add messages
            const messages = parseMessages(text);
            for (const msg of messages) {
                await fetch(`${API_URL}/api/conversations/${currentConversation.id}/messages`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(msg)
                });
            }

            // Analyze conversation
            const analysisResponse = await fetch(`${API_URL}/api/conversations/${currentConversation.id}/analyze`, {
                method: 'POST'
            });

            if (analysisResponse.ok) {
                const analysisData = await analysisResponse.json();
                updateSidebarWithAnalysis(analysisData.analysis);
            }

            // Get AI suggestion
            const suggestionResponse = await fetch(`${API_URL}/api/ai/suggest`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ conversation_id: currentConversation.id })
            });

            if (suggestionResponse.ok) {
                const suggestionData = await suggestionResponse.json();
                suggestionText.textContent = suggestionData.suggestion;
            }
        } else {
            // Quick analysis without conversation
            const response = await fetch(`${API_URL}/advice`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    text: `Based on this conversation, suggest what I should reply:\n\n${text}`,
                    context: [selectedResponseType],
                    user_type: 'premium'
                })
            });

            if (response.ok) {
                const data = await response.json();
                suggestionText.textContent = data.data.response;
            } else {
                throw new Error('Failed to get advice');
            }
        }

        // Refresh stats
        loadUserStats();

    } catch (e) {
        console.error('Analysis error:', e);
        suggestionText.textContent = 'Could not analyze conversation. Please try again.';
    } finally {
        btn.textContent = originalText;
        btn.disabled = false;
    }
}

function parseMessages(text) {
    const messages = [];
    const lines = text.split('\n').filter(l => l.trim());

    for (const line of lines) {
        // Try to detect sender
        const lowerLine = line.toLowerCase();
        let role = 'user'; // Default to user (her messages)

        if (lowerLine.startsWith('me:') || lowerLine.startsWith('you:') || lowerLine.startsWith('i:')) {
            role = 'assistant'; // Your messages
        } else if (lowerLine.startsWith('her:') || lowerLine.startsWith('she:')) {
            role = 'user'; // Her messages
        }

        // Clean content
        let content = line.replace(/^(me|you|i|her|she):\s*/i, '').trim();

        if (content) {
            messages.push({ role, content });
        }
    }

    return messages;
}

function updateSidebarWithAnalysis(analysis) {
    // Update progress ring
    updateProgressRing(analysis.chemistry_score);
    document.getElementById('chemistry-score').textContent = `${analysis.chemistry_score}%`;

    // Update success/failure rates
    document.getElementById('success-rate').textContent = `${Math.round(analysis.success_rate)}%`;
    document.getElementById('failure-rate').textContent = `${Math.round(analysis.failure_rate)}%`;

    // Update AI tip
    if (analysis.ai_tip) {
        updateAITip(analysis.ai_tip);
    }
}

// ==================== UTILITY ====================
function showTab(tabName) {
    // Legacy function for compatibility
    console.log('Tab:', tabName);
}
