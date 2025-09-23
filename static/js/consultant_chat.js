window.openConsultantModal = function() {
    const modal = document.getElementById('consultantModal');
    if (modal) {
        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';
        
        if (!window.consultantChat) {
            window.consultantChat = new ConsultantChat();
        }
    } else {
        console.error('Modal element not found!');
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
        this.currentQuoteData = null;
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadSession();
        this.updateWelcomeTime();
        this.startSessionTimer();
        this.addWelcomeMessage();
        this.initializeSession();
    }

    async initializeSession() {
        
        try {
            const response = await fetch(window.consultantApiUrls.startSession, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    session_id: this.sessionId
                })
            });

            if (response.ok) {
                const data = await response.json();
                console.log('✅ Сесія ініціалізована:', data.session_id);
            }
        } catch (error) {
            console.error('❌ Помилка ініціалізації сесії:', error);
        }
    }

    bindEvents() {
        const sendButton = document.getElementById('sendButton');
        const messageInput = document.getElementById('messageInput');
        const chatForm = document.getElementById('chatForm');

        if (chatForm) {
            chatForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.sendMessage();
            });
        }

        if (sendButton) {
            sendButton.addEventListener('click', (e) => {
                e.preventDefault();
                this.sendMessage();
            });
        }

        if (messageInput) {
            messageInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendMessage();
                }
            });
        }

        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('quick-question')) {
                const text = e.target.textContent.trim();
                this.sendQuickQuestion(text);
            }
            
            if (e.target.classList.contains('rag-action-btn')) {
                const action = e.target.dataset.action;
                this.handleRagAction(action, e.target.dataset);
            }
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
            this.addMessage('assistant', '👋 Привіт! Я ваш RAG консультант з ШІ. Готовий допомогти з будь-якими питаннями!');
        }
    }

    addMessage(sender, content, timestamp = null, ragData = null) {
        const message = {
            id: Date.now() + Math.random(),
            sender,
            content,
            timestamp: timestamp || new Date().toISOString(),
            ragData
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
        
        let messageHTML = `
            <div class="message-content">
                <div class="message-text">${this.escapeHtml(message.content)}</div>
                <div class="message-time">${this.formatTime(message.timestamp)}</div>
            </div>
        `;

        if (message.sender === 'assistant' && message.ragData) {
            messageHTML += this.renderRagInterface(message.ragData);
        }

        messageElement.innerHTML = messageHTML;
        messagesContainer.appendChild(messageElement);
    }

    renderRagInterface(ragData) {
        let ragHTML = '';

        if (ragData.sources && ragData.sources.length > 0) {
            ragHTML += '<div class="rag-sources"><div class="rag-sources-title">📚 Джерела:</div>';
            ragData.sources.forEach((source, index) => {
                ragHTML += `
                    <div class="rag-source-item">
                        <span class="source-title">${this.escapeHtml(source.content_title || 'Джерело')}</span>
                        <span class="source-similarity">${Math.round(source.similarity * 100)}% збіг</span>
                    </div>
                `;
            });
            ragHTML += '</div>';
        }

        if (ragData.suggestions && ragData.suggestions.length > 0) {
            ragHTML += '<div class="rag-suggestions"><div class="rag-suggestions-title">💡 Пропозиції:</div>';
            ragData.suggestions.forEach((suggestion) => {
                ragHTML += `
                    <button class="suggestion-btn quick-question">${this.escapeHtml(suggestion)}</button>
                `;
            });
            ragHTML += '</div>';
        }

        if (ragData.actions && ragData.actions.length > 0) {
            ragHTML += '<div class="rag-actions"><div class="rag-actions-title">⚡ Дії:</div>';
            ragData.actions.forEach((action) => {
                const btnClass = `rag-action-btn btn-${action.style || 'primary'}`;
                if (action.type === 'button') {
                    ragHTML += `
                        <button class="${btnClass}" data-action="${action.action}" data-text="${this.escapeHtml(action.text)}">
                            ${this.escapeHtml(action.text)}
                        </button>
                    `;
                } else if (action.type === 'link') {
                    ragHTML += `
                        <a href="${action.url}" class="${btnClass}" target="_blank">
                            ${this.escapeHtml(action.text)}
                        </a>
                    `;
                }
            });
            ragHTML += '</div>';
        }

        if (ragData.method && window.location.hostname === 'localhost') {
            ragHTML += `<div class="rag-debug">🔍 Метод: ${ragData.method} | Намір: ${ragData.intent}</div>`;
        }

        return ragHTML ? `<div class="rag-interface">${ragHTML}</div>` : '';
    }

    handleRagAction(action, dataset) {
        
        switch (action) {
            case 'request_quote':
                this.showQuoteModal(dataset.text);
                break;
                
            case 'schedule_consultation':
                this.showConsultationModal();
                break;
                
            case 'contact_manager':
                this.contactManager();
                break;
                
            default:
                console.log('Невідома дія:', action);
        }
    }

    showQuoteModal(context = '') {
        
        if (!document.getElementById('quoteModal')) {
            this.createQuoteModal();
        }

        const modal = document.getElementById('quoteModal');
        const messageField = document.getElementById('quoteMessage');
        
        if (messageField && context) {
            messageField.value = `Контекст з чату: ${context}\n\nДодаткова інформація про проєкт:`;
        }
        
        modal.style.display = 'flex';
    }

    createQuoteModal() {
        
        const modalHTML = `
            <div id="quoteModal" class="quote-modal" style="display: none;">
                <div class="modal-content">
                    <div class="modal-header">
                        <h3>🧮 Отримати прорахунок</h3>
                        <button class="modal-close" onclick="closeQuoteModal()">×</button>
                    </div>
                    <form id="quoteForm" class="quote-form">
                        <div class="form-group">
                            <label for="quoteName">Ваше ім'я *</label>
                            <input type="text" id="quoteName" name="client_name" required>
                        </div>
                        <div class="form-group">
                            <label for="quoteEmail">Email *</label>
                            <input type="email" id="quoteEmail" name="client_email" required>
                        </div>
                        <div class="form-group">
                            <label for="quotePhone">Телефон</label>
                            <input type="tel" id="quotePhone" name="client_phone">
                        </div>
                        <div class="form-group">
                            <label for="quoteCompany">Компанія</label>
                            <input type="text" id="quoteCompany" name="client_company">
                        </div>
                        <div class="form-group">
                            <label for="quoteMessage">Опишіть ваш проєкт *</label>
                            <textarea id="quoteMessage" name="message" rows="4" required></textarea>
                        </div>
                        <div class="modal-actions">
                            <button type="button" onclick="closeQuoteModal()" class="btn-secondary">
                                Скасувати
                            </button>
                            <button type="submit" class="btn-primary">
                                📧 Отримати прорахунок
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        
        document.getElementById('quoteForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.submitQuoteRequest();
        });
    }

    async submitQuoteRequest() {
        
        const form = document.getElementById('quoteForm');
        const formData = new FormData(form);
        
        const data = {
            client_name: formData.get('client_name'),
            client_email: formData.get('client_email'),
            client_phone: formData.get('client_phone'),
            client_company: formData.get('client_company'),
            message: formData.get('message'),
            session_id: this.sessionId
        };

        try {
            const response = await fetch(window.consultantApiUrls.requestQuote, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify(data)
            });

            if (response.ok) {
                const result = await response.json();
                
                closeQuoteModal();
                
                this.addMessage('assistant', `✅ ${result.message}`);
                
                form.reset();
                
            } else {
                const error = await response.json();
                alert(`Помилка: ${error.error || 'Невідома помилка'}`);
            }
            
        } catch (error) {
            console.error('Помилка відправки запиту:', error);
            alert('Помилка з\'єднання. Спробуйте пізніше.');
        }
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

        this.addMessage('user', message);
        messageInput.value = '';

        this.showTypingIndicator();

        try {
            const response = await fetch(window.consultantApiUrls.sendMessage, {
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
            
            this.hideTypingIndicator();
            
            this.addMessage('assistant', data.message.content, null, data.rag_data);

            if (data.show_quote_form) {
                setTimeout(() => {
                    this.showQuoteModal('Автоматично визначений запит на прорахунок');
                }, 1000);
            }

        } catch (error) {
            console.error('Error sending message:', error);
            this.hideTypingIndicator();
            this.addMessage('assistant', 'Вибачте, виникла помилка з\'єднання. Спробуйте ще раз.');
        }
    }

    sendQuickQuestion(text) {
        const messageInput = document.getElementById('messageInput');
        if (messageInput) {
            messageInput.value = text;
            this.sendMessage();
        }
    }

    showTypingIndicator() {
        if (this.isTyping) return;
        this.isTyping = true;

        const messagesContainer = document.getElementById('messages');
        const typingElement = document.createElement('div');
        typingElement.className = 'message assistant typing-indicator';
        typingElement.id = 'typingIndicator';
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
        const typingIndicator = document.getElementById('typingIndicator');
        if (typingIndicator) {
            typingIndicator.remove();
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
        return new Date(timestamp).toLocaleTimeString('uk-UA', {
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    updateWelcomeTime() {
        const welcomeTimeElement = document.getElementById('welcomeTime');
        if (welcomeTimeElement) {
            welcomeTimeElement.textContent = new Date().toLocaleTimeString('uk-UA', {
                hour: '2-digit',
                minute: '2-digit'
            });
        }
    }

    startSessionTimer() {
        const sessionTimeElement = document.getElementById('sessionTime');
        if (!sessionTimeElement) return;

        setInterval(() => {
            const elapsed = Math.floor((Date.now() - this.sessionStartTime) / 1000);
            const minutes = Math.floor(elapsed / 60);
            const seconds = elapsed % 60;
            sessionTimeElement.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        }, 1000);
    }

    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
               document.querySelector('meta[name="csrf-token"]')?.content ||
               '';
    }
}

window.closeQuoteModal = function() {
    const modal = document.getElementById('quoteModal');
    if (modal) {
        modal.style.display = 'none';
    }
};

document.addEventListener('DOMContentLoaded', function() {
    console.log('🤖 RAG Consultant готовий!');
});
