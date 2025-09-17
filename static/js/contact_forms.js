/**
 * Contact Forms Handler
 * Обробляє відправку форм контактів та показує модалки
 */

// Глобальні змінні
let isSubmitting = false;

// Ініціалізація при завантаженні сторінки
document.addEventListener('DOMContentLoaded', function() {
    console.log('📋 Contact forms initialized');
    
    // Ініціалізуємо обробники форм
    initializeFormHandlers();
});

function initializeFormHandlers() {
    // Обробник для основної форми контактів
    const contactForm = document.getElementById('contactForm');
    if (contactForm) {
        contactForm.addEventListener('submit', handleFormSubmit);
        console.log('✅ Main contact form handler attached');
    }
    
    // Обробник для модальної форми консультації
    const consultationForm = document.getElementById('quickConsultationForm');
    if (consultationForm) {
        consultationForm.addEventListener('submit', handleFormSubmit);
        console.log('✅ Consultation modal form handler attached');
    }
}

async function handleFormSubmit(event) {
    event.preventDefault();
    
    if (isSubmitting) {
        console.log('⚠️ Form is already being submitted');
        return;
    }
    
    const form = event.target;
    const submitButton = form.querySelector('button[type="submit"]');
    
    console.log('📤 Form submission started:', form.id);
    console.log('📱 User agent:', navigator.userAgent);
    console.log('📱 Is mobile:', /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent));
    
    // Показуємо стан завантаження
    setLoadingState(submitButton, true);
    isSubmitting = true;
    
    try {
        // Збираємо дані форми
        const formData = new FormData(form);
        
        // Перевіряємо CSRF token
        const csrfToken = formData.get('csrfmiddlewaretoken');
        console.log('🔐 CSRF token:', csrfToken ? 'Present' : 'Missing');
        
        // Додаємо дані трекінгу CTA
        const ctaData = getCTATrackingData();
        if (ctaData.cta_source) {
            formData.append('cta_source', ctaData.cta_source);
        }
        if (ctaData.page_url) {
            formData.append('page_url', ctaData.page_url);
        }
        if (ctaData.session_id) {
            formData.append('session_id', ctaData.session_id);
        }
        
        console.log('📋 Form data keys:', Array.from(formData.keys()));
        
        const response = await fetch(form.action, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': formData.get('csrfmiddlewaretoken')
            },
            // Додаткові налаштування для мобільних пристроїв
            cache: 'no-cache',
            credentials: 'same-origin'
        });
        
        const result = await response.json();
        console.log('📦 Response data:', result);
        
        if (result.success) {
            console.log('✅ Success response received:', result);
            // Показуємо success модалку
            showSuccessModal(result.message);
            form.reset();
            
            // Закриваємо швидку модалку якщо вона відкрита
            if (form.id === 'quickConsultationForm') {
                closeConsultationModal();
            }
            
        } else {
            console.log('❌ Error response received:', result);
            showErrorMessage(form, result.error || 'Виникла помилка при відправленні форми');
        }
        
    } catch (error) {
        console.error('❌ Form submission error:', error);
        console.error('❌ Error details:', {
            name: error.name,
            message: error.message,
            stack: error.stack
        });
        
        // Різні повідомлення для різних типів помилок
        let errorMessage = 'Помилка з\'єднання. Спробуйте ще раз.';
        if (error.name === 'TypeError' && error.message.includes('fetch')) {
            errorMessage = 'Проблема з мережею. Перевірте підключення до інтернету.';
        } else if (error.name === 'AbortError') {
            errorMessage = 'Запит було скасовано. Спробуйте ще раз.';
        }
        
        showErrorMessage(form, errorMessage);
    } finally {
        // Прибираємо стан завантаження
        setLoadingState(submitButton, false);
        isSubmitting = false;
    }
}

function setLoadingState(button, isLoading) {
    if (!button) return;
    
    const btnText = button.querySelector('.btn-text');
    const btnLoading = button.querySelector('.btn-loading');
    
    if (isLoading) {
        button.disabled = true;
        if (btnText) btnText.style.display = 'none';
        if (btnLoading) btnLoading.style.display = 'inline';
    } else {
        button.disabled = false;
        if (btnText) btnText.style.display = 'inline';
        if (btnLoading) btnLoading.style.display = 'none';
    }
}

function showErrorMessage(form, message) {
    // Видаляємо попередні повідомлення про помилки
    const existingError = form.querySelector('.error-message');
    if (existingError) {
        existingError.remove();
    }
    
    // Створюємо нове повідомлення про помилку
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.style.cssText = `
        background: rgba(255, 68, 68, 0.1);
        color: #ff4444;
        border: 1px solid rgba(255, 68, 68, 0.3);
        padding: 1rem;
        border-radius: 10px;
        margin-top: 1rem;
        text-align: center;
        font-weight: 600;
    `;
    errorDiv.textContent = message;
    
    // Додаємо повідомлення до форми
    form.appendChild(errorDiv);
    
    // Автоматично прибираємо через 5 секунд
    setTimeout(() => {
        if (errorDiv.parentNode) {
            errorDiv.remove();
        }
    }, 5000);
}

function showSuccessModal(message) {
    // Видаляємо попередні модалки
    const existingModal = document.querySelector('.success-notification-modal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Отримуємо переклади з Django контексту
    const translations = {
        thankYou: window.DJANGO_CONTEXT?.thankYou || 'Дякуємо!',
        successMessage: window.DJANGO_CONTEXT?.successMessage || 'Ваше повідомлення надіслано. Ми зв\'яжемося з вами найближчим часом.',
        understood: window.DJANGO_CONTEXT?.understood || 'Зрозуміло'
    };
    
    // Створюємо модалку успіху
    const modal = document.createElement('div');
    modal.className = 'success-notification-modal';
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        z-index: 10002;
        display: flex;
        align-items: center;
        justify-content: center;
        background: rgba(0, 0, 0, 0.8);
        backdrop-filter: blur(10px);
        opacity: 0;
        transition: opacity 0.3s ease;
    `;
    
    modal.innerHTML = `
        <div class="success-modal-content" style="
            background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
            border: 2px solid #66ff00;
            border-radius: 20px;
            padding: 2rem;
            max-width: 500px;
            width: 90%;
            text-align: center;
            position: relative;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.5);
            transform: scale(0.9);
            transition: transform 0.3s ease;
        ">
            <div style="
                width: 80px;
                height: 80px;
                margin: 0 auto 1.5rem;
                background: rgba(102, 255, 0, 0.2);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                color: #66ff00;
            ">
                <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
                    <polyline points="22,4 12,14.01 9,11.01"></polyline>
                </svg>
            </div>
            
            <h2 style="
                color: #66ff00;
                font-size: 1.8rem;
                font-weight: 700;
                margin-bottom: 1rem;
                text-shadow: 0 2px 10px rgba(102, 255, 0, 0.3);
            ">${translations.thankYou}</h2>
            
            <p style="
                color: #ffffff;
                font-size: 1.1rem;
                line-height: 1.6;
                margin-bottom: 2rem;
                opacity: 0.9;
            ">${message || translations.successMessage}</p>
            
            <button onclick="closeSuccessModal()" style="
                background: linear-gradient(135deg, #66ff00 0%, #4ddb00 100%);
                color: #000;
                border: none;
                padding: 1rem 2rem;
                border-radius: 50px;
                font-size: 1.1rem;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s ease;
                box-shadow: 0 4px 15px rgba(102, 255, 0, 0.3);
            ">${translations.understood}</button>
        </div>
    `;
    
    // Додаємо до DOM
    document.body.appendChild(modal);
    
    // Анімація появи
    setTimeout(() => {
        modal.style.opacity = '1';
        modal.querySelector('.success-modal-content').style.transform = 'scale(1)';
    }, 10);
    
    // Автоматично закриваємо через 5 секунд
    setTimeout(() => {
        closeSuccessModal();
    }, 5000);
}

function closeSuccessModal() {
    const modal = document.querySelector('.success-notification-modal');
    if (modal) {
        modal.style.opacity = '0';
        modal.querySelector('.success-modal-content').style.transform = 'scale(0.9)';
        
        setTimeout(() => {
            modal.remove();
        }, 300);
    }
}

// Функції для модалки консультації
function showConsultationModal() {
    const modal = document.getElementById('consultationModal');
    
    if (modal) {
        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';
        
        // Перевіряємо чи прив'язаний обробник до форми в модалці
        const consultationForm = document.getElementById('quickConsultationForm');
        if (consultationForm && !consultationForm.hasAttribute('data-handler-attached')) {
            consultationForm.addEventListener('submit', handleFormSubmit);
            consultationForm.setAttribute('data-handler-attached', 'true');
            console.log('✅ Consultation modal form handler attached dynamically');
        }
        
        // Анімація появи
        setTimeout(() => {
            modal.classList.add('show');
        }, 10);
    }
}

function closeConsultationModal() {
    const modal = document.getElementById('consultationModal');
    if (modal) {
        // Анімація зникнення
        modal.classList.remove('show');
        
        setTimeout(() => {
            modal.style.display = 'none';
            document.body.style.overflow = '';
        }, 300);
    }
}

// Функції для трекінгу CTA
function getCTATrackingData() {
    return {
        cta_source: localStorage.getItem('last_cta_source') || '',
        page_url: window.location.href,
        session_id: getSessionId()
    };
}

function getSessionId() {
    let sessionId = sessionStorage.getItem('cta_session_id');
    if (!sessionId) {
        sessionId = 'cta_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        sessionStorage.setItem('cta_session_id', sessionId);
    }
    return sessionId;
}

// Глобальні функції для виклику з HTML
window.showConsultationModal = showConsultationModal;
window.closeConsultationModal = closeConsultationModal;
window.closeSuccessModal = closeSuccessModal;