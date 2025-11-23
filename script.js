window.addEventListener('scroll', () => {
    const navbar = document.getElementById('navbar');
    if (window.scrollY > 100) {
        navbar.classList.add('scrolled');
    } else {
        navbar.classList.remove('scrolled');
    }
});

// Typing effect
const texts = ['AIML Engineer', 'Data Scientist', 'Problem Solver', 'Creative Thinker'];
let count = 0;
let index = 0;
let currentText = '';
let letter = '';

function type() {
    if (count === texts.length) {
        count = 0;
    }
    currentText = texts[count];
    letter = currentText.slice(0, ++index);

    document.querySelector('.typing-effect').textContent = letter;
    if (letter.length === currentText.length) {
        count++;
        index = 0;
        setTimeout(type, 2000);
    } else {
        setTimeout(type, 100);
    }
}

type();

// Smooth scroll
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// Chat Assistant logic
const chatToggle = document.getElementById('chat-toggle');
const chatWidget = document.getElementById('chat-widget');
const chatClose = document.getElementById('chat-close');
const chatForm = document.getElementById('chat-form');
const chatInput = document.getElementById('chat-input');
const chatMessages = document.getElementById('chat-messages');

function appendMessage(text, role) {
    const div = document.createElement('div');
    div.className = `message ${role}`;
    // Convert Markdown → HTML instead of plain text
    div.innerHTML = marked.parse(text);
    chatMessages.appendChild(div);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}


// assistantReply removed: chat now calls server-side assistant API

// Manage chat visibility with persistence so it survives tab switches / navigations
function setChatVisibility(visible) {
    if (!chatWidget) return;
    if (visible) {
        chatWidget.classList.remove('hidden');
        try { chatInput.focus(); } catch (e) {}
        localStorage.setItem('chatVisible', '1');
    } else {
        chatWidget.classList.add('hidden');
        localStorage.setItem('chatVisible', '0');
    }
}

function toggleChat() {
    const isHidden = chatWidget?.classList.contains('hidden');
    setChatVisibility(!!isHidden);
}

// Restore visibility from previous session (if any)
(function restoreChatState() {
    try {
        const saved = localStorage.getItem('chatVisible');
        if (saved === '1') setChatVisibility(true);
        // if '0' or null, keep default (hidden)
    } catch (e) {
        // localStorage might be disabled; ignore
    }
})();

chatToggle?.addEventListener('click', () => setChatVisibility(true));
chatClose?.addEventListener('click', () => setChatVisibility(false));

chatForm?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const value = chatInput.value.trim();
    if (!value) return;
    appendMessage(value, 'user');
    chatInput.value = '';
    try {
        const res = await fetch('http://localhost:7860/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: value })
        });
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            appendMessage('Assistant error: ' + (err.error || res.statusText), 'bot');
            return;
        }
        const data = await res.json();
        appendMessage(data.reply || 'No reply from assistant', 'bot');
    } catch (err) {
        appendMessage('Unable to reach assistant server. Start `assistant_server.py`.', 'bot');
    }
});