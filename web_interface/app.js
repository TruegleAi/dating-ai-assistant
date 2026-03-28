// Munch AI Dating Assistant - Frontend App
const API_URL = 'https://dating-ai-assistant-production.up.railway.app';

// State
let currentUser = null;
let currentConversation = null;
let selectedResponseType = 'Dating App';
let conversations = [];
let easterEggUnlocked = false;

// ==================== INITIALIZATION ====================
document.addEventListener('DOMContentLoaded', () => {
    checkHealth();
    setupResponseTypeButtons();
    loadOrCreateUser();
    addProgressGradient();

    // Check if easter egg was previously unlocked
    if (localStorage.getItem('munch_easter_egg') === 'unlocked') {
        easterEggUnlocked = true;
        showEasterEggButton();
    }
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
        } else throw new Error('API not responding');
    } catch (error) {
        document.getElementById('status-indicator').classList.add('offline');
        document.getElementById('status-text').textContent = 'Disconnected';
    }
}

// ==================== USER MANAGEMENT ====================
async function loadOrCreateUser() {
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
        } catch (e) {}
    }
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
    } catch (e) { console.error('Could not create user:', e); }
}

async function loadUserStats() {
    if (!currentUser) return;
    try {
        const response = await fetch(`${API_URL}/api/users/${currentUser.id}/stats`);
        if (response.ok) {
            const data = await response.json();
            updateSidebarStats(data.stats);
        }
    } catch (e) {}
}

function updateSidebarStats(stats) {
    const total = stats.total_conversations || 1;
    const successRate = Math.round((stats.success / total) * 100) || 0;
    const failureRate = Math.round((stats.ghosted / total) * 100) || 0;
    const chemistryScore = stats.avg_chemistry_score || 0;
    updateProgressRing(chemistryScore);
    document.getElementById('chemistry-score').textContent = `${chemistryScore}%`;
    document.getElementById('success-rate').textContent = `${successRate}%`;
    document.getElementById('failure-rate').textContent = `${failureRate}%`;
}

function updateProgressRing(percentage) {
    const circle = document.getElementById('progress-circle');
    if (circle) {
        const circumference = 2 * Math.PI * 52;
        const offset = circumference - (percentage / 100) * circumference;
        circle.style.strokeDasharray = `${circumference}`;
        circle.style.strokeDashoffset = offset;
    }
}

// ==================== SIDEBAR ====================
function toggleSidebar() {
    document.getElementById('sidebar').classList.toggle('active');
    document.getElementById('sidebar-overlay').classList.toggle('active');
}
function closeSidebar() {
    document.getElementById('sidebar').classList.remove('active');
    document.getElementById('sidebar-overlay').classList.remove('active');
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
    } catch (e) {}
}

function renderConversationList() {
    const container = document.getElementById('conversation-list');
    if (conversations.length === 0) {
        container.innerHTML = `<div class="empty-state">No conversations yet</div><button class="btn-new-conv" onclick="showNewConversationModal()">+ New Conversation</button>`;
        return;
    }
    let html = conversations.map(conv => {
        const statusClass = conv.status.toLowerCase();
        const statusIcon = getStatusIcon(conv.status);
        const isActive = currentConversation && currentConversation.id === conv.id;
        return `<div class="conversation-item ${isActive ? 'active' : ''}" onclick="selectConversation(${conv.id})">
            <span class="conv-name">${conv.name}</span>
            <div class="conv-status ${statusClass}">${conv.chemistry_score}% ${statusIcon}<span class="conv-arrow">›</span></div>
        </div>`;
    }).join('');
    html += `<button class="btn-new-conv" onclick="showNewConversationModal()" style="margin-top:12px;width:100%;padding:12px;background:transparent;border:1px dashed var(--border);border-radius:12px;color:var(--text-secondary);cursor:pointer;">+ New Conversation</button>`;
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
            if (data.conversation.chemistry_score > 0) {
                updateAITip(`Chemistry score: ${data.conversation.chemistry_score}%. Keep building rapport!`);
            }
            renderConversationList();
            closeSidebar();
        }
    } catch (e) {}
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
    if (!name) { alert('Please enter a name for this conversation'); return; }
    if (!currentUser) { alert('Please wait for user initialization'); return; }
    try {
        const response = await fetch(`${API_URL}/api/conversations`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: currentUser.id, name, response_type: type })
        });
        if (response.ok) {
            const data = await response.json();
            currentConversation = data.conversation;
            closeModal();
            loadConversations();
        }
    } catch (e) { alert('Could not create conversation'); }
}

// ==================== RESPONSE TYPE SELECTOR ====================
function setupResponseTypeButtons() {
    document.querySelectorAll('.type-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.type-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            selectedResponseType = btn.dataset.type;
        });
    });
}

// ==================== FILE UPLOAD ====================
function triggerUpload() { document.getElementById('file-upload').click(); }
async function handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    const input = document.getElementById('message-input');
    input.value = 'Analyzing screenshot...';
    input.disabled = true;
    try {
        const formData = new FormData();
        formData.append('file', file);
        const response = await fetch(`${API_URL}/api/image/upload`, { method: 'POST', body: formData });
        if (response.ok) {
            const data = await response.json();
            if (data.messages && data.messages.length > 0) {
                input.value = data.messages.map(m => `${m.sender === 'user' ? 'Me' : 'Her'}: ${m.content}`).join('\n');
            } else input.value = 'Could not extract messages. Try pasting manually.';
        } else input.value = 'Failed to analyze image. Please paste messages manually.';
    } catch (e) {
        input.value = 'Error analyzing image. Please paste manually.';
    } finally {
        input.disabled = false;
        event.target.value = '';
    }
}

// ==================== MAIN ANALYSIS ====================
async function analyzeConversation() {
    const input = document.getElementById('message-input');
    const text = input.value.trim();
    if (!text) { alert('Please enter or paste conversation messages'); return; }

    const btn = document.querySelector('.btn-analyze');
    const originalText = btn.textContent;
    btn.textContent = 'Analyzing...';
    btn.disabled = true;

    const resultsSection = document.getElementById('results-section');
    const suggestionText = document.getElementById('suggestion-text');
    resultsSection.classList.remove('hidden');
    suggestionText.innerHTML = '<div class="loading">Getting AI suggestion</div>';

    try {
        if (currentConversation) {
            const messages = parseMessages(text);
            for (const msg of messages) {
                await fetch(`${API_URL}/api/conversations/${currentConversation.id}/messages`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(msg)
                });
            }
            const analysisResponse = await fetch(`${API_URL}/api/conversations/${currentConversation.id}/analyze`, { method: 'POST' });
            if (analysisResponse.ok) {
                const analysisData = await analysisResponse.json();
                updateSidebarWithAnalysis(analysisData.analysis);
            }
            const suggestionResponse = await fetch(`${API_URL}/api/ai/suggest`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ conversation_id: currentConversation.id })
            });
            if (suggestionResponse.ok) {
                const suggestionData = await suggestionResponse.json();
                suggestionText.textContent = suggestionData.suggestion;
            }

            // 🎯 Check for date success after analysis
            await checkForDateSuccess();

        } else {
            const response = await fetch(`${API_URL}/advice`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: `Based on this conversation, suggest what I should reply:\n\n${text}`, context: [selectedResponseType], user_type: 'premium' })
            });
            if (response.ok) {
                const data = await response.json();
                suggestionText.textContent = data.data.response;
            } else throw new Error('Failed to get advice');
        }
        loadUserStats();
    } catch (e) {
        suggestionText.textContent = 'Could not analyze conversation. Please try again.';
    } finally {
        btn.textContent = originalText;
        btn.disabled = false;
    }
}

function parseMessages(text) {
    return text.split('\n').filter(l => l.trim()).map(line => {
        const lower = line.toLowerCase();
        let role = 'user';
        if (lower.startsWith('me:') || lower.startsWith('you:') || lower.startsWith('i:')) role = 'assistant';
        else if (lower.startsWith('her:') || lower.startsWith('she:')) role = 'user';
        const content = line.replace(/^(me|you|i|her|she):\s*/i, '').trim();
        return content ? { role, content } : null;
    }).filter(Boolean);
}

function updateSidebarWithAnalysis(analysis) {
    updateProgressRing(analysis.chemistry_score);
    document.getElementById('chemistry-score').textContent = `${analysis.chemistry_score}%`;
    document.getElementById('success-rate').textContent = `${Math.round(analysis.success_rate)}%`;
    document.getElementById('failure-rate').textContent = `${Math.round(analysis.failure_rate)}%`;
    if (analysis.ai_tip) updateAITip(analysis.ai_tip);
}

// ==================== DATE SUCCESS DETECTION ====================
async function checkForDateSuccess() {
    if (!currentConversation || easterEggUnlocked) return;
    try {
        const response = await fetch(`${API_URL}/api/conversations/${currentConversation.id}/check-date`);
        if (response.ok) {
            const data = await response.json();
            if (data.date_detected && data.confidence >= 40) {
                // Small delay so analysis results show first
                setTimeout(() => showDateQuestionnaire(data), 1500);
            }
        }
    } catch (e) { /* non-critical */ }
}

// ==================== DATE QUESTIONNAIRE MODAL ====================
function showDateQuestionnaire(detectionData) {
    // Don't show if already confirmed
    if (localStorage.getItem('munch_date_confirmed')) return;

    const modal = document.getElementById('date-questionnaire-modal');
    if (modal) {
        modal.classList.remove('hidden');
        // Show confidence signals
        if (detectionData.matched_signals && detectionData.matched_signals.length > 0) {
            const signalsEl = document.getElementById('date-signals');
            if (signalsEl) signalsEl.textContent = `Detected: "${detectionData.matched_signals.slice(0, 2).join('", "')}"`;
        }
    }
}

function closeDateModal() {
    document.getElementById('date-questionnaire-modal').classList.add('hidden');
}

async function confirmDate() {
    const where = document.getElementById('date-where').value.trim();
    const when = document.getElementById('date-when').value.trim();
    const vibe = document.getElementById('date-vibe').value;

    if (!where || !when) {
        alert('Fill in where and when at least!');
        return;
    }

    try {
        const response = await fetch(`${API_URL}/api/conversations/${currentConversation.id}/confirm-date`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ where, when, vibe, notes: '' })
        });

        if (response.ok) {
            closeDateModal();
            localStorage.setItem('munch_date_confirmed', '1');
            localStorage.setItem('munch_easter_egg', 'unlocked');
            easterEggUnlocked = true;
            showEasterEggUnlockCelebration();
        }
    } catch (e) {
        alert('Could not confirm date. Try again!');
    }
}

function showEasterEggUnlockCelebration() {
    const cel = document.getElementById('easter-egg-celebration');
    if (cel) {
        cel.classList.remove('hidden');
        setTimeout(() => {
            cel.classList.add('hidden');
            showEasterEggButton();
        }, 3000);
    }
}

function showEasterEggButton() {
    const btn = document.getElementById('easter-egg-btn');
    if (btn) btn.classList.remove('hidden');
}

// ==================== PAC-MAN EASTER EGG GAME ====================
function openEasterEgg() {
    document.getElementById('pacman-modal').classList.remove('hidden');
    initPacMan();
}

function closeEasterEgg() {
    document.getElementById('pacman-modal').classList.add('hidden');
    if (typeof cancelAnimationFrame !== 'undefined' && window._pacmanAnimId) {
        cancelAnimationFrame(window._pacmanAnimId);
    }
}

function initPacMan() {
    const canvas = document.getElementById('pacman-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    // Game state
    let score = 0, lives = 3, level = 1, gameState = 'playing';
    let moveTimer = 0, ghostMoveTimer = 0;
    const MOVE_INTERVAL = 350, GHOST_MOVE_INTERVAL = 450;
    const CELL = 28;

    const layout = [
        "1111111111111111111",
        "1222222222222222221",
        "1311112121211111321",
        "1222222222222222221",
        "1211121112111211121",
        "1222222222222222221",
        "1112112121212112111",
        "0002120000200212000",
        "1112121112111212111",
        "2222222252222222222",
        "1112121112111212111",
        "0002120000200212000",
        "1112121112111212111",
        "1222222222222222221",
        "1211121112111211121",
        "1222222224222222221",
        "1311112121211111321",
        "1222222222222222221",
        "1111111111111111111"
    ];

    const GH = layout.length, GW = layout[0].length;
    let grid = [], dots = [], powerPellets = [], ghosts = [], particles = [];
    let player = { x:9, y:15, dir:{x:0,y:0}, nextDir:{x:0,y:0}, mouth:0, power:false, powerTimer:0 };

    // Build grid
    function buildGrid() {
        grid=[]; dots=[]; powerPellets=[]; ghosts=[];
        for (let y=0;y<GH;y++) {
            grid[y]=[];
            for (let x=0;x<GW;x++) {
                const c=layout[y][x];
                grid[y][x]=c==='1'?1:0;
                if(c==='2') dots.push({x,y,eaten:false});
                if(c==='3') powerPellets.push({x,y,eaten:false});
                if(c==='4'){player.x=x;player.y=y;}
                if(c==='5'){
                    ghosts.push(
                        {x:x-1,y,dir:{x:0,y:-1},color:'#ff6b9d',scared:false},
                        {x:x+1,y,dir:{x:0,y:1},color:'#00d4ff',scared:false},
                        {x:x-1,y:y+1,dir:{x:-1,y:0},color:'#c050ff',scared:false},
                        {x:x+1,y:y+1,dir:{x:1,y:0},color:'#ffcc44',scared:false}
                    );
                }
            }
        }
    }

    function canMove(x,y){ return x>=0&&x<GW&&y>=0&&y<GH&&grid[y][x]!==1; }

    function resize() {
        const cont = document.getElementById('pacman-modal');
        const maxW = Math.min(cont.clientWidth - 20, 540);
        canvas.width = maxW;
        canvas.height = Math.floor(maxW * (GH/GW)) + 60;
    }

    function cellSize() { return Math.floor((canvas.width) / GW); }

    function drawGame() {
        const cs = cellSize();
        const offX = 0, offY = 40;
        ctx.fillStyle = '#04030d';
        ctx.fillRect(0,0,canvas.width,canvas.height);

        // Header
        ctx.fillStyle = '#fff';
        ctx.font = 'bold 14px Orbitron, sans-serif';
        ctx.fillText(`SCORE: ${score}`, 10, 25);
        ctx.fillText(`LIVES: ${'♥'.repeat(lives)}`, canvas.width/2, 25);
        ctx.fillText(`LVL: ${level}`, canvas.width-70, 25);

        ctx.save();
        ctx.translate(offX, offY);

        // Grid
        for(let y=0;y<GH;y++) for(let x=0;x<GW;x++) {
            if(grid[y][x]===1) {
                ctx.fillStyle='#0a0820';
                ctx.fillRect(x*cs+1,y*cs+1,cs-2,cs-2);
                ctx.strokeStyle='#00f2ff';
                ctx.lineWidth=1;
                ctx.strokeRect(x*cs+1,y*cs+1,cs-2,cs-2);
            }
        }

        // Dots
        dots.forEach(d => {
            if(!d.eaten){
                ctx.beginPath();
                ctx.arc(d.x*cs+cs/2,d.y*cs+cs/2,3,0,Math.PI*2);
                ctx.fillStyle='#ffcc44'; ctx.fill();
            }
        });

        // Power pellets
        const pulse = Math.sin(Date.now()/200)*0.3+0.7;
        powerPellets.forEach(p => {
            if(!p.eaten){
                ctx.beginPath();
                ctx.arc(p.x*cs+cs/2,p.y*cs+cs/2,7*pulse,0,Math.PI*2);
                ctx.fillStyle=`rgba(255,107,157,${0.3*pulse})`; ctx.fill();
                ctx.beginPath();
                ctx.arc(p.x*cs+cs/2,p.y*cs+cs/2,5,0,Math.PI*2);
                ctx.fillStyle='#ff6b9d'; ctx.fill();
            }
        });

        // Player
        const px=player.x*cs+cs/2, py=player.y*cs+cs/2, r=cs*0.4;
        ctx.save();
        ctx.translate(px,py);
        let rot=0;
        if(player.dir.x===1)rot=0;
        else if(player.dir.x===-1)rot=Math.PI;
        else if(player.dir.y===-1)rot=-Math.PI/2;
        else if(player.dir.y===1)rot=Math.PI/2;
        ctx.rotate(rot);
        const ma=Math.abs(Math.sin(player.mouth))*0.28+0.05;
        ctx.beginPath();
        ctx.arc(0,0,r,ma,Math.PI*2-ma);
        ctx.lineTo(0,0); ctx.closePath();
        const fg=ctx.createRadialGradient(-3,-3,0,0,0,r);
        fg.addColorStop(0,'#ffe55c'); fg.addColorStop(1,'#ffb800');
        ctx.fillStyle=fg; ctx.fill();
        // Sunglasses
        ctx.fillStyle='#000';
        ctx.fillRect(-r*0.7,-r*0.4,r*1.4,r*0.5);
        ctx.strokeStyle='#ffd700'; ctx.lineWidth=1;
        ctx.strokeRect(-r*0.7,-r*0.4,r*1.4,r*0.5);
        ctx.restore();

        // Ghosts
        ghosts.forEach(g => {
            const gx=g.x*cs+cs/2, gy=g.y*cs+cs/2, gr=cs*0.35;
            ctx.save(); ctx.translate(gx,gy);
            ctx.beginPath();
            ctx.arc(0,-gr*0.3,gr,Math.PI,0);
            ctx.lineTo(gr,gr);
            for(let i=0;i<3;i++){
                ctx.quadraticCurveTo(gr*(1-(i*2+1)/3),gr*0.7,gr*(1-(i+1)*2/3),gr);
            }
            ctx.lineTo(-gr,gr); ctx.closePath();
            ctx.fillStyle=g.scared?'#5b2c6f':g.color; ctx.fill();
            if(!g.scared){
                ctx.fillStyle='white';
                ctx.beginPath(); ctx.arc(-gr*0.3,-gr*0.2,gr*0.22,0,Math.PI*2);
                ctx.arc(gr*0.3,-gr*0.2,gr*0.22,0,Math.PI*2); ctx.fill();
                ctx.fillStyle='#000';
                ctx.beginPath(); ctx.arc(-gr*0.3,-gr*0.2,gr*0.1,0,Math.PI*2);
                ctx.arc(gr*0.3,-gr*0.2,gr*0.1,0,Math.PI*2); ctx.fill();
                // bow
                ctx.fillStyle='#ff6b9d';
                ctx.beginPath(); ctx.ellipse(-8,-gr-5,8,10,-0.3,0,Math.PI*2); ctx.fill();
                ctx.beginPath(); ctx.ellipse(8,-gr-5,8,10,0.3,0,Math.PI*2); ctx.fill();
                ctx.beginPath(); ctx.arc(0,-gr-5,4,0,Math.PI*2); ctx.fill();
            }
            ctx.restore();
        });

        // Particles
        particles=particles.filter(p => {
            p.x+=p.vx; p.y+=p.vy; p.life-=0.03; p.vy+=0.05;
            if(p.life<=0) return false;
            ctx.globalAlpha=p.life;
            ctx.fillStyle=p.color;
            ctx.beginPath(); ctx.arc(p.x,p.y,p.size,0,Math.PI*2); ctx.fill();
            ctx.globalAlpha=1;
            return true;
        });

        ctx.restore();

        // Game Over / Level Complete overlay
        if(gameState==='gameOver'){
            ctx.fillStyle='rgba(0,0,0,0.75)';
            ctx.fillRect(0,0,canvas.width,canvas.height);
            ctx.fillStyle='#ff6b9d';
            ctx.font='bold 28px Orbitron,sans-serif';
            ctx.textAlign='center';
            ctx.fillText('GAME OVER',canvas.width/2,canvas.height/2-20);
            ctx.fillStyle='#fff';
            ctx.font='16px Orbitron,sans-serif';
            ctx.fillText(`Final Score: ${score}`,canvas.width/2,canvas.height/2+15);
            ctx.fillText('Tap to restart',canvas.width/2,canvas.height/2+45);
            ctx.textAlign='left';
        }
        if(gameState==='levelComplete'){
            ctx.fillStyle='rgba(0,0,0,0.75)';
            ctx.fillRect(0,0,canvas.width,canvas.height);
            ctx.fillStyle='#ffcc44';
            ctx.font='bold 24px Orbitron,sans-serif';
            ctx.textAlign='center';
            ctx.fillText('💋 SHE KISSED YOU! 💋',canvas.width/2,canvas.height/2-20);
            ctx.fillStyle='#ff6b9d';
            ctx.font='16px Orbitron,sans-serif';
            ctx.fillText('Tap for next level',canvas.width/2,canvas.height/2+20);
            ctx.textAlign='left';
        }
    }

    let lastTs=0;
    function gameLoop(ts){
        if(!lastTs) lastTs=ts;
        const dt=ts-lastTs; lastTs=ts;

        if(gameState==='playing'){
            moveTimer+=dt; ghostMoveTimer+=dt;
            player.mouth+=0.15;

            if(moveTimer>=MOVE_INTERVAL){
                moveTimer=0;
                if(player.nextDir.x||player.nextDir.y){
                    if(canMove(player.x+player.nextDir.x,player.y+player.nextDir.y))
                        player.dir={...player.nextDir};
                }
                if(player.dir.x||player.dir.y){
                    const nx=player.x+player.dir.x, ny=player.y+player.dir.y;
                    if(canMove(nx,ny)){player.x=nx;player.y=ny;}
                }
                // Collect dots
                dots.forEach(d=>{
                    if(!d.eaten&&d.x===player.x&&d.y===player.y){
                        d.eaten=true; score+=10;
                        for(let i=0;i<5;i++) particles.push({x:player.x*cellSize()+cellSize()/2,y:player.y*cellSize()+cellSize()/2,vx:(Math.random()-0.5)*3,vy:(Math.random()-0.5)*3,life:1,color:'#ffcc44',size:3});
                    }
                });
                // Collect power pellets
                powerPellets.forEach(p=>{
                    if(!p.eaten&&p.x===player.x&&p.y===player.y){
                        p.eaten=true; score+=50; player.power=true; player.powerTimer=400;
                        ghosts.forEach(g=>g.scared=true);
                    }
                });
                if(player.power){
                    player.powerTimer--;
                    if(player.powerTimer<=0){player.power=false;ghosts.forEach(g=>g.scared=false);}
                }
                if(dots.every(d=>d.eaten)&&powerPellets.every(p=>p.eaten)){gameState='levelComplete';}
            }

            if(ghostMoveTimer>=GHOST_MOVE_INTERVAL){
                ghostMoveTimer=0;
                ghosts.forEach(g=>{
                    const dx=player.x-g.x, dy=player.y-g.y;
                    const tx=g.scared?g.x-Math.sign(dx)*2:player.x;
                    const ty=g.scared?g.y-Math.sign(dy)*2:player.y;
                    const dirs=[{x:0,y:-1},{x:0,y:1},{x:-1,y:0},{x:1,y:0}];
                    let best=g.dir, bestS=-Infinity;
                    dirs.forEach(d=>{
                        if(d.x===-g.dir.x&&d.y===-g.dir.y) return;
                        const nx=g.x+d.x, ny=g.y+d.y;
                        if(!canMove(nx,ny)) return;
                        const s=-(Math.abs(nx-tx)+Math.abs(ny-ty));
                        if(s>bestS){bestS=s;best=d;}
                    });
                    g.dir=best;
                    const nx=g.x+g.dir.x, ny=g.y+g.dir.y;
                    if(canMove(nx,ny)){g.x=nx;g.y=ny;}
                    if(g.x===player.x&&g.y===player.y){
                        if(g.scared){g.x=9;g.y=9;g.scared=false;score+=200;}
                        else{
                            lives--;
                            for(let i=0;i<20;i++) particles.push({x:player.x*cellSize()+cellSize()/2,y:player.y*cellSize()+cellSize()/2,vx:(Math.random()-0.5)*4,vy:(Math.random()-0.5)*4,life:1,color:'#ff0000',size:4});
                            if(lives<=0) gameState='gameOver';
                            else{player.x=9;player.y=15;player.dir={x:0,y:0};}
                        }
                    }
                });
            }
        }

        drawGame();
        window._pacmanAnimId = requestAnimationFrame(gameLoop);
    }

    // Controls
    canvas.addEventListener('click', ()=>{
        if(gameState==='gameOver'){score=0;lives=3;level=1;buildGrid();gameState='playing';lastTs=0;}
        if(gameState==='levelComplete'){level++;buildGrid();gameState='playing';lastTs=0;}
    });
    document.addEventListener('keydown', e=>{
        if(!document.getElementById('pacman-modal').classList.contains('hidden')){
            if(e.key==='ArrowUp') player.nextDir={x:0,y:-1};
            if(e.key==='ArrowDown') player.nextDir={x:0,y:1};
            if(e.key==='ArrowLeft') player.nextDir={x:-1,y:0};
            if(e.key==='ArrowRight') player.nextDir={x:1,y:0};
        }
    });

    // D-pad buttons
    ['up','down','left','right'].forEach(dir=>{
        const btn = document.getElementById(`pac-${dir}`);
        if(btn) btn.addEventListener('click',()=>{
            if(dir==='up') player.nextDir={x:0,y:-1};
            if(dir==='down') player.nextDir={x:0,y:1};
            if(dir==='left') player.nextDir={x:-1,y:0};
            if(dir==='right') player.nextDir={x:1,y:0};
        });
    });

    resize();
    buildGrid();
    if(window._pacmanAnimId) cancelAnimationFrame(window._pacmanAnimId);
    lastTs=0;
    window._pacmanAnimId = requestAnimationFrame(gameLoop);
}

function showTab(tabName) { console.log('Tab:', tabName); }
