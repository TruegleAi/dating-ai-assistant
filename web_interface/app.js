const API_URL = ''; // Use relative URLs for tunnel compatibility

// Check API health on load
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

// Tab switching
function showTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelectorAll('.tab').forEach(tab => {
        tab.classList.remove('active');
    });

    // Show selected tab
    document.getElementById(`${tabName}-tab`).classList.add('active');
    event.target.classList.add('active');
}

// Get Dating Advice
async function getAdvice() {
    const query = document.getElementById('advice-query').value.trim();
    const resultDiv = document.getElementById('advice-result');

    if (!query) {
        alert('Please enter a question');
        return;
    }

    resultDiv.innerHTML = '<div class="loading">Getting advice</div>';
    resultDiv.classList.add('show');

    try {
        const response = await fetch(`${API_URL}/advice`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                text: query,
                context: ['Push-Pull Dynamics', 'Qualification techniques'],
                user_type: 'premium'
            })
        });

        const data = await response.json();

        if (data.success) {
            resultDiv.innerHTML = `
                <h3>Dating Advice</h3>
                <div class="advice-text">${data.data.response}</div>
            `;
        } else {
            throw new Error('Failed to get advice');
        }
    } catch (error) {
        resultDiv.innerHTML = `<p style="color: var(--pink);">Error: ${error.message}</p>`;
    }
}

// Message management for interest analysis
function addMessage() {
    const container = document.getElementById('messages-container');
    const messageInput = document.createElement('div');
    messageInput.className = 'message-input';
    messageInput.innerHTML = `
        <select class="sender-select">
            <option value="user">You</option>
            <option value="woman">Her</option>
        </select>
        <input type="text" class="message-text" placeholder="Message text...">
        <button onclick="removeMessage(this)" class="btn-remove">×</button>
    `;
    container.appendChild(messageInput);
}

function removeMessage(button) {
    const container = document.getElementById('messages-container');
    if (container.children.length > 1) {
        button.parentElement.remove();
    }
}

// Analyze Interest
async function analyzeInterest() {
    const messageInputs = document.querySelectorAll('.message-input');
    const messages = [];

    messageInputs.forEach(input => {
        const sender = input.querySelector('.sender-select').value;
        const text = input.querySelector('.message-text').value.trim();
        if (text) {
            messages.push({ sender, text });
        }
    });

    const resultDiv = document.getElementById('analyze-result');

    if (messages.length === 0) {
        alert('Please add at least one message');
        return;
    }

    resultDiv.innerHTML = '<div class="loading">Analyzing messages</div>';
    resultDiv.classList.add('show');

    try {
        const response = await fetch(`${API_URL}/analyze`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ messages })
        });

        const data = await response.json();

        if (data.success) {
            const analysis = data.analysis;
            const scoreClass = `interest-${analysis.level}`;

            resultDiv.innerHTML = `
                <h3>Interest Analysis</h3>
                <div class="interest-score ${scoreClass}">${analysis.score}/100 - ${analysis.level.toUpperCase()} INTEREST</div>
                <p><strong>Advice:</strong> ${analysis.advice}</p>
                <p><strong>Suggested Reply Time:</strong> ${analysis.reply_time}</p>
                <p><strong>Messages Analyzed:</strong> ${analysis.analyzed_messages}</p>
            `;
        } else {
            throw new Error('Failed to analyze interest');
        }
    } catch (error) {
        resultDiv.innerHTML = `<p style="color: var(--pink);">Error: ${error.message}</p>`;
    }
}

// Generate Opener
async function generateOpener() {
    const profileContext = document.getElementById('profile-context').value.trim();
    const platform = document.getElementById('platform').value;
    const resultDiv = document.getElementById('opener-result');

    resultDiv.innerHTML = '<div class="loading">Generating opener</div>';
    resultDiv.classList.add('show');

    try {
        const response = await fetch(`${API_URL}/opener`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                profile_context: profileContext,
                platform: platform
            })
        });

        const data = await response.json();

        if (data.success) {
            const opener = data.opener;

            resultDiv.innerHTML = `
                <h3>Your Opening Line</h3>
                <div class="opener-line">"${opener.opener}"</div>
                <p><strong>Technique:</strong> ${opener.technique}</p>
                <p><strong>Platform:</strong> ${opener.platform}</p>
                <p><strong>Expected Success:</strong> ${opener.success_rate}</p>
            `;
        } else {
            throw new Error('Failed to generate opener');
        }
    } catch (error) {
        resultDiv.innerHTML = `<p style="color: var(--pink);">Error: ${error.message}</p>`;
    }
}

// Initialize on page load
window.addEventListener('DOMContentLoaded', () => {
    checkHealth();
    // Add initial message inputs
    addMessage();
});
