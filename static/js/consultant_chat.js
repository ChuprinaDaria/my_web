// Глобальна функція - ПЕРШОЮ!
window.openConsultantModal = function() {
    console.log('openConsultantModal called from:', window.location.pathname);
    const modal = document.getElementById('consultantModal');
    console.log('Modal element found:', modal);
    
    if (modal) {
        console.log('Opening modal...');
        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';
        
        // Записуємо сторінку відкриття
        const currentPage = window.location.pathname;
        localStorage.setItem('consultant_opened_from', currentPage);
        console.log('Чат відкрито з:', currentPage);
        
        // Ініціалізуємо чат
        if (!window.consultantChat) {
            console.log('Initializing consultant chat...');
            window.consultantChat = new ConsultantChat();
        }
        console.log('Modal opened successfully!');
    } else {
        console.error('Modal element not found! Available elements with id:', 
            Array.from(document.querySelectorAll('[id]')).map(el => el.id));
    }
};

window.closeConsultantModal = function() {
    const modal = document.getElementById('consultantModal');
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = 'auto';
    }
};

class ConsultantChat {
    constructor() {
        this.messages = [];
        this.isTyping = false;
        this.sessionId = this.getOrCreateSessionId();
        this.sessionStartTime = Date.now();
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadSession();
        this.updateWelcomeTime();
        this.startSessionTimer();
        this.addWelcomeMessage();
    }

    bindEvents() {
        const sendButton = document.getElementById('sendButton');
        const messageInput = document.getElementById('messageInput');
        const quickQuestions = document.querySelectorAll('.quick-question');

        if (sendButton) {
            sendButton.addEventListener('click', () => this.sendMessage());
        }

        if (messageInput) {
            messageInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendMessage();
                }
            });
        }

        quickQuestions.forEach(question => {
            question.addEventListener('click', () => {
                const text = question.textContent.trim();
                this.sendQuickQuestion(text);
            });
        });
    }

    getOrCreateSessionId() {
        let sessionId = localStorage.getItem('consultant_session_id');
        if (!sessionId) {
            sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
            localStorage.setItem('consultant_session_id', sessionId);
        }
        return sessionId;
    }

    loadSession() {
        const savedMessages = localStorage.getItem(`consultant_messages_${this.sessionId}`);
        if (savedMessages) {
            this.messages = JSON.parse(savedMessages);
            this.renderMessages();
        }
    }

    saveSession() {
        localStorage.setItem(`consultant_messages_${this.sessionId}`, JSON.stringify(this.messages));
    }

    addWelcomeMessage() {
        if (this.messages.length === 0) {
            this.addMessage('assistant', 'Привіт! Я ваш RAG консультант. Як можу допомогти?');
        }
    }

    addMessage(sender, content, timestamp = null) {
        const message = {
            id: Date.now() + Math.random(),
            sender,
            content,
            timestamp: timestamp || new Date().toISOString()
        };
        
        this.messages.push(message);
        this.renderMessage(message);
        this.saveSession();
        this.scrollToBottom();
    }

    renderMessage(message) {
        const messagesContainer = document.getElementById('messages');
        if (!messagesContainer) return;

        const messageElement = document.createElement('div');
        messageElement.className = `message ${message.sender}`;
        messageElement.innerHTML = `
            <div class="message-content">
                <div class="message-text">${this.escapeHtml(message.content)}</div>
                <div class="message-time">${this.formatTime(message.timestamp)}</div>
            </div>
        `;

        messagesContainer.appendChild(messageElement);
    }

    renderMessages() {
        const messagesContainer = document.getElementById('messages');
        if (!messagesContainer) return;

        messagesContainer.innerHTML = '';
        this.messages.forEach(message => this.renderMessage(message));
    }

    async sendMessage() {
        const messageInput = document.getElementById('messageInput');
        const message = messageInput.value.trim();
        
        if (!message) return;

        // Додаємо повідомлення користувача
        this.addMessage('user', message);
        messageInput.value = '';

        // Показуємо індикатор набору
        this.showTypingIndicator();

        try {
            const response = await fetch('/consultant/api/send-message/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    message: message,
                    session_id: this.sessionId
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            
            // Приховуємо індикатор набору
            this.hideTypingIndicator();
            
            // Додаємо відповідь консультанта
            this.addMessage('assistant', data.response);

        } catch (error) {
            console.error('Error sending message:', error);
            this.hideTypingIndicator();
            this.addMessage('assistant', 'Вибачте, виникла помилка з\'єднання. Спробуйте ще раз.');
        }
    }

    async sendQuickQuestion(question) {
        const messageInput = document.getElementById('messageInput');
        messageInput.value = question;
        await this.sendMessage();
    }

    showTypingIndicator() {
        if (this.isTyping) return;
        
        this.isTyping = true;
        const messagesContainer = document.getElementById('messages');
        if (!messagesContainer) return;

        const typingElement = document.createElement('div');
        typingElement.className = 'message assistant typing';
        typingElement.id = 'typing-indicator';
        typingElement.innerHTML = `
            <div class="message-content">
                <div class="typing-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        `;

        messagesContainer.appendChild(typingElement);
        this.scrollToBottom();
    }

    hideTypingIndicator() {
        this.isTyping = false;
        const typingElement = document.getElementById('typing-indicator');
        if (typingElement) {
            typingElement.remove();
        }
    }

    scrollToBottom() {
        const messagesContainer = document.getElementById('messages');
        if (messagesContainer) {
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    formatTime(timestamp) {
        const date = new Date(timestamp);
        return date.toLocaleTimeString('uk-UA', { 
            hour: '2-digit', 
            minute: '2-digit' 
        });
    }

    getCSRFToken() {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
        return csrfToken ? csrfToken.value : '';
    }

    clearChat() {
        this.messages = [];
        this.renderMessages();
        this.saveSession();
        this.addWelcomeMessage();
    }

    exportChat() {
        const chatData = {
            sessionId: this.sessionId,
            messages: this.messages,
            exportDate: new Date().toISOString()
        };

        const blob = new Blob([JSON.stringify(chatData, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `consultant_chat_${this.sessionId}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    updateWelcomeTime() {
        const welcomeTime = document.getElementById('welcomeTime');
        if (welcomeTime) {
            welcomeTime.textContent = new Date().toLocaleTimeString('uk-UA', { 
                hour: '2-digit', 
                minute: '2-digit' 
            });
        }
    }

    startSessionTimer() {
        setInterval(() => {
            const elapsed = Math.floor((Date.now() - this.sessionStartTime) / 1000);
            const minutes = Math.floor(elapsed / 60);
            const seconds = elapsed % 60;
            const sessionTimeEl = document.getElementById('sessionTime');
            if (sessionTimeEl) {
                sessionTimeEl.textContent = 
                    minutes.toString().padStart(2, '0') + ':' + seconds.toString().padStart(2, '0');
            }
        }, 1000);
    }

    minimizeChat() {
        const modal = document.getElementById('consultantModal');
        if (modal) {
            modal.classList.add('minimized');
            modal.innerHTML = `
                <div class="minimized-chat" onclick="this.parentElement.classList.remove('minimized'); window.consultantChat.restoreChat()">
                    <span>💬 RAG Chat</span>
                </div>
            `;
        }
    }

    restoreChat() {
        // Відновити повну модалку
        window.location.reload(); // Простий спосіб
    }
}

// Modal functions
function openConsultantModal() {
    const modal = document.getElementById('consultantModal');
    if (modal) {
        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';
        // Initialize chat if not already done
        if (!window.consultantChat) {
            window.consultantChat = new ConsultantChat();
        }
    }
}

function closeConsultantModal() {
    const modal = document.getElementById('consultantModal');
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = 'auto';
    }
}

// Ініціалізація при завантаженні сторінки
document.addEventListener('DOMContentLoaded', function() {
    // Ініціалізуємо чат тільки якщо є відповідні елементи на сторінці
    if (document.getElementById('messages') || document.getElementById('consultantModal')) {
        window.consultantChat = new ConsultantChat();
    }
});

// Функції для кнопок
function clearChat() {
    if (window.consultantChat) {
        window.consultantChat.clearChat();
    }
}

function exportChat() {
    if (window.consultantChat) {
        window.consultantChat.exportChat();
    }
}
