/**
 * Loan Eligibility Agent - Chat Interface
 * Handles the conversational UI and API integration
 */

// Configuration
const API_BASE_URL = window.location.origin;
let sessionId = null;
let isTyping = false;

// Initialize chat on page load
document.addEventListener('DOMContentLoaded', () => {
    // Check for existing session
    sessionId = localStorage.getItem('loan_agent_session');
});

/**
 * Open the chat widget
 */
function openChat() {
    const widget = document.getElementById('chat-widget');
    widget.classList.remove('hidden');

    // Start new conversation if no session
    if (!sessionId) {
        startConversation();
    }
}

/**
 * Close the chat widget
 */
function closeChat() {
    const widget = document.getElementById('chat-widget');
    widget.classList.add('hidden');
}

/**
 * Toggle chat widget visibility
 */
function toggleChat() {
    const widget = document.getElementById('chat-widget');
    if (widget.classList.contains('hidden')) {
        openChat();
    } else {
        closeChat();
    }
}

/**
 * Start a new conversation session
 */
async function startConversation() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/conversation/start`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            throw new Error('Failed to start conversation');
        }

        const data = await response.json();
        sessionId = data.session_id;
        localStorage.setItem('loan_agent_session', sessionId);

        // Display the initial greeting
        addMessage(data.message, 'bot');

    } catch (error) {
        console.error('Error starting conversation:', error);
        addMessage('Sorry, I\'m having trouble connecting. Please try again later.', 'bot');
    }
}

/**
 * Send a message to the API
 */
async function sendMessage() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();

    if (!message || isTyping) return;

    // Clear input
    input.value = '';

    // Add user message to chat
    addMessage(message, 'user');

    // Show typing indicator
    showTypingIndicator();

    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/conversation/message`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                session_id: sessionId,
                message: message
            })
        });

        // Remove typing indicator
        hideTypingIndicator();

        if (!response.ok) {
            if (response.status === 404) {
                // Session expired, start new one
                sessionId = null;
                localStorage.removeItem('loan_agent_session');
                await startConversation();
                return;
            }
            throw new Error('Failed to send message');
        }

        const data = await response.json();

        // Add bot response
        addMessage(data.response, 'bot');

        // Check if conversation is complete
        if (data.conversation_complete) {
            showConversationComplete();
        }

    } catch (error) {
        hideTypingIndicator();
        console.error('Error sending message:', error);
        addMessage('Sorry, I encountered an error. Please try again.', 'bot');
    }
}

/**
 * Add a message to the chat
 */
function addMessage(text, sender) {
    const messagesContainer = document.getElementById('chat-messages');

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;

    // Parse markdown-like formatting
    const formattedText = formatMessage(text);
    messageDiv.innerHTML = formattedText;

    messagesContainer.appendChild(messageDiv);

    // Scroll to bottom
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

/**
 * Format message with basic markdown support
 */
function formatMessage(text) {
    // Convert **bold** to <strong>
    text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

    // Convert bullet points
    text = text.replace(/^• (.*)/gm, '<li>$1</li>');
    text = text.replace(/(<li>.*<\/li>)+/gs, '<ul>$&</ul>');

    // Convert numbered lists
    text = text.replace(/^\d+\. (.*)/gm, '<li>$1</li>');

    // Convert line breaks
    text = text.replace(/\n/g, '<br>');

    return text;
}

/**
 * Show typing indicator
 */
function showTypingIndicator() {
    isTyping = true;
    const messagesContainer = document.getElementById('chat-messages');

    const typingDiv = document.createElement('div');
    typingDiv.className = 'message bot typing';
    typingDiv.id = 'typing-indicator';
    typingDiv.innerHTML = '<span></span><span></span><span></span>';

    messagesContainer.appendChild(typingDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

/**
 * Hide typing indicator
 */
function hideTypingIndicator() {
    isTyping = false;
    const typingIndicator = document.getElementById('typing-indicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
}

/**
 * Show conversation complete options
 */
function showConversationComplete() {
    const messagesContainer = document.getElementById('chat-messages');

    const actionsDiv = document.createElement('div');
    actionsDiv.className = 'chat-actions';
    actionsDiv.innerHTML = `
        <button onclick="requestCallback()" class="action-btn">Request Callback</button>
        <button onclick="startNewConversation()" class="action-btn secondary">Start New Inquiry</button>
    `;

    messagesContainer.appendChild(actionsDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

/**
 * Handle Enter key press
 */
function handleKeyPress(event) {
    if (event.key === 'Enter') {
        sendMessage();
    }
}

/**
 * Start a new conversation (reset)
 */
async function startNewConversation() {
    // Clear messages
    const messagesContainer = document.getElementById('chat-messages');
    messagesContainer.innerHTML = '';

    // Clear session
    sessionId = null;
    localStorage.removeItem('loan_agent_session');

    // Start fresh
    await startConversation();
}

/**
 * Request callback from human agent
 */
async function requestCallback() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/conversation/handoff/${sessionId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const data = await response.json();

        addMessage('Thank you! A loan specialist will contact you within 24 hours. Is there anything else I can help you with?', 'bot');

    } catch (error) {
        console.error('Error requesting callback:', error);
        addMessage('I\'ll have a specialist contact you. Please ensure your contact information is up to date.', 'bot');
    }
}

/**
 * Quick eligibility check (API demo)
 */
async function quickCheck(loanType, amount, income, creditScore) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/eligibility/quick-check`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                loan_type: loanType,
                requested_amount: amount,
                annual_income: income,
                credit_score: creditScore,
                existing_debt: 0
            })
        });

        return await response.json();

    } catch (error) {
        console.error('Error in quick check:', error);
        return null;
    }
}

// Add styles for action buttons
const style = document.createElement('style');
style.textContent = `
    .chat-actions {
        display: flex;
        gap: 8px;
        margin-top: 12px;
    }

    .action-btn {
        padding: 10px 16px;
        border-radius: 8px;
        border: none;
        font-size: 0.85rem;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s;
    }

    .action-btn:not(.secondary) {
        background: var(--primary-color);
        color: white;
    }

    .action-btn:not(.secondary):hover {
        background: var(--primary-dark);
    }

    .action-btn.secondary {
        background: var(--surface-light);
        color: var(--text-primary);
    }

    .action-btn.secondary:hover {
        background: var(--border-color);
    }

    .message ul {
        margin: 8px 0;
        padding-left: 20px;
    }

    .message li {
        margin: 4px 0;
    }
`;
document.head.appendChild(style);
