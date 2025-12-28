/**
 * AI Meeting Assistant - Frontend JavaScript
 */

// Socket.IO connection
const socket = io();

// DOM Elements
const statusIndicator = document.getElementById('status-indicator');
const statusText = statusIndicator.querySelector('.status-text');
const transcriptContainer = document.getElementById('transcript-container');
const currentTopicEl = document.getElementById('current-topic');
const meetingSummaryEl = document.getElementById('meeting-summary');
const answerContainerEl = document.getElementById('answer-container');
const questionInput = document.getElementById('question-input');
const loadingOverlay = document.getElementById('loading-overlay');

// Buttons
const btnToggleDemo = document.getElementById('btn-toggle-demo');
const btnClear = document.getElementById('btn-clear');
const btnRefreshTopic = document.getElementById('btn-refresh-topic');
const btnGenerateSummary = document.getElementById('btn-generate-summary');
const btnAsk = document.getElementById('btn-ask');
const btnDecisions = document.getElementById('btn-decisions');
const btnActions = document.getElementById('btn-actions');
const btnTopics = document.getElementById('btn-topics');

// State
let isRunning = false;

// Helper Functions
function showLoading() {
    loadingOverlay.classList.add('active');
}

function hideLoading() {
    loadingOverlay.classList.remove('active');
}

function updateStatus(connected, running = false) {
    statusIndicator.classList.remove('connected', 'running');
    
    if (running) {
        statusIndicator.classList.add('running');
        statusText.textContent = 'Recording';
        btnToggleDemo.innerHTML = '<span class="btn-icon">⏹️</span><span class="btn-text">Stop Demo</span>';
        btnToggleDemo.classList.add('btn-danger');
        btnToggleDemo.classList.remove('btn-primary');
    } else if (connected) {
        statusIndicator.classList.add('connected');
        statusText.textContent = 'Connected';
        btnToggleDemo.innerHTML = '<span class="btn-icon">▶️</span><span class="btn-text">Start Demo</span>';
        btnToggleDemo.classList.remove('btn-danger');
        btnToggleDemo.classList.add('btn-primary');
    } else {
        statusText.textContent = 'Disconnected';
        btnToggleDemo.innerHTML = '<span class="btn-icon">▶️</span><span class="btn-text">Start Demo</span>';
        btnToggleDemo.classList.remove('btn-danger');
        btnToggleDemo.classList.add('btn-primary');
    }
    
    isRunning = running;
}

function addTranscript(text, speaker) {
    // Remove empty state if present
    const emptyState = transcriptContainer.querySelector('.empty-state');
    if (emptyState) {
        emptyState.remove();
    }
    
    const entry = document.createElement('div');
    entry.className = 'transcript-entry';
    entry.innerHTML = `
        <div class="transcript-speaker">${speaker}</div>
        <div class="transcript-text">${text}</div>
    `;
    
    transcriptContainer.appendChild(entry);
    transcriptContainer.scrollTop = transcriptContainer.scrollHeight;
}

function clearTranscript() {
    transcriptContainer.innerHTML = '<div class="empty-state"><p>Start the demo to see live transcription</p></div>';
}

async function fetchWithLoading(url, options = {}) {
    showLoading();
    try {
        const response = await fetch(url, options);
        return await response.json();
    } catch (error) {
        console.error('Request failed:', error);
        return { error: error.message };
    } finally {
        hideLoading();
    }
}

// Socket Events
socket.on('connect', () => {
    console.log('Connected to server');
    updateStatus(true, isRunning);
});

socket.on('disconnect', () => {
    console.log('Disconnected from server');
    updateStatus(false);
});

socket.on('status', (data) => {
    updateStatus(true, data.running);
    if (data.message) {
        console.log('Status:', data.message);
    }
});

socket.on('transcript', (data) => {
    if (data.is_final) {
        addTranscript(data.text, data.speaker);
    }
});

socket.on('error', (data) => {
    console.error('Error:', data.message);
    alert(data.message);
});

// Button Event Handlers
btnToggleDemo.addEventListener('click', () => {
    if (isRunning) {
        socket.emit('stop_demo');
    } else {
        socket.emit('start_demo');
    }
});

btnClear.addEventListener('click', () => {
    socket.emit('clear_transcript');
    clearTranscript();
    currentTopicEl.innerHTML = '<p class="placeholder">No active discussion</p>';
    meetingSummaryEl.innerHTML = '<p class="placeholder">Click \'Generate\' to create a summary</p>';
    answerContainerEl.innerHTML = '<p class="placeholder">Ask a question about the meeting</p>';
});

btnRefreshTopic.addEventListener('click', async () => {
    const data = await fetchWithLoading('/api/topic');
    if (data.topic) {
        currentTopicEl.innerHTML = `<p>${data.topic}</p>`;
    } else if (data.error) {
        currentTopicEl.innerHTML = `<p class="placeholder">${data.error}</p>`;
    }
});

btnGenerateSummary.addEventListener('click', async () => {
    const data = await fetchWithLoading('/api/summary');
    if (data.summary) {
        meetingSummaryEl.innerHTML = `<p>${data.summary}</p>`;
    } else if (data.error) {
        meetingSummaryEl.innerHTML = `<p class="placeholder">${data.error}</p>`;
    }
});

async function askQuestion(question) {
    const data = await fetchWithLoading('/api/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question })
    });
    
    if (data.answer) {
        answerContainerEl.innerHTML = `<p>${data.answer}</p>`;
    } else if (data.error) {
        answerContainerEl.innerHTML = `<p class="placeholder">${data.error}</p>`;
    }
}

btnAsk.addEventListener('click', () => {
    const question = questionInput.value.trim();
    if (question) {
        askQuestion(question);
    }
});

questionInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        const question = questionInput.value.trim();
        if (question) {
            askQuestion(question);
        }
    }
});

// Quick action buttons
btnDecisions.addEventListener('click', () => {
    questionInput.value = 'What has been decided so far?';
    askQuestion('What has been decided so far?');
});

btnActions.addEventListener('click', () => {
    questionInput.value = 'What are the action items mentioned?';
    askQuestion('What are the action items mentioned?');
});

btnTopics.addEventListener('click', () => {
    questionInput.value = 'What topics have been discussed?';
    askQuestion('What topics have been discussed?');
});

// Initialize
console.log('AI Meeting Assistant initialized');
