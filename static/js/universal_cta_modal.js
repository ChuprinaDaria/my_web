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
        
        this.loadTranslations();
    }
    
    loadTranslations() {
        
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
        
        this.ctaSource = ctaSource;
        this.ctaTitle = ctaTitle;
        
        
        if (typeof(Storage) !== "undefined") {
            localStorage.setItem('last_cta_source', ctaSource);
            localStorage.setItem('last_cta_title', ctaTitle);
        }
        
        
        showConsultationModal();
        
        
        this.trackCTA('cta_clicked', ctaSource);
    }
    
    
    trackCTA(eventName, ctaSource) {
        
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

window.UniversalCTAModal = UniversalCTAModal;

document.addEventListener('DOMContentLoaded', function() {
    window.ctaModal = new UniversalCTAModal();
    
});