/**
 * Universal CTA Modal - Спрощена версія
 * Одразу відкриває контактну форму замість показу власної модалки
 */

class UniversalCTAModal {
    constructor() {
        this.ctaSource = 'unknown';
        this.ctaTitle = '';
        this.translations = {
            title: 'Безкоштовна консультація',
            description: 'Отримайте експертну консультацію від наших спеціалістів',
            primaryBtn: 'Зв\'язатися зараз',
            secondaryBtn: 'Пізніше',
            footer: '100% безкоштовно • Без зобов\'язань • Швидка відповідь'
        };
        
        // Завантажуємо переклади
        this.loadTranslations();
    }
    
    loadTranslations() {
        // Завантажуємо переклади з Django контексту
        if (window.DJANGO_CONTEXT) {
            this.translations = {
                title: window.DJANGO_CONTEXT.modalTitle || this.translations.title,
                description: window.DJANGO_CONTEXT.modalDetails || this.translations.description,
                primaryBtn: window.DJANGO_CONTEXT.ctaPrimaryBtn || this.translations.primaryBtn,
                secondaryBtn: window.DJANGO_CONTEXT.ctaSecondaryBtn || this.translations.secondaryBtn,
                footer: window.DJANGO_CONTEXT.ctaFooter || this.translations.footer
            };
        }
    }
    
    show(ctaSource = 'unknown', ctaTitle = '') {
        // Зберігаємо дані трекінгу
        this.ctaSource = ctaSource;
        this.ctaTitle = ctaTitle;
        
        // Зберігаємо в localStorage для contact_forms.js
        if (typeof(Storage) !== "undefined") {
            localStorage.setItem('last_cta_source', ctaSource);
            localStorage.setItem('last_cta_title', ctaTitle);
        }
        
        // Відкриваємо універсальну модалку
        showConsultationModal();
        
        // Трекінг
        this.trackCTA('cta_clicked', ctaSource);
    }
    
    
    trackCTA(eventName, ctaSource) {
        // Google Analytics 4 трекінг
        if (typeof gtag !== 'undefined') {
            gtag('event', eventName, {
                'event_category': 'CTA',
                'event_label': ctaSource,
                'cta_source': ctaSource,
                'page_title': document.title,
                'page_path': window.location.pathname
            });
        }
    }
}

// Створюємо глобальний екземпляр
window.UniversalCTAModal = UniversalCTAModal;

// Ініціалізуємо при завантаженні сторінки
document.addEventListener('DOMContentLoaded', function() {
    window.ctaModal = new UniversalCTAModal();
    console.log('🎯 Universal CTA Modal initialized');
});