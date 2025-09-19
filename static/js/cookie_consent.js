/**
 * 🍪 Cookie Consent Manager
 * Простий, надійний, без зайвих наворотів
 */

class CookieConsent {
  constructor() {
    this.cookieName = 'cookie_consent';
    this.cookieExpiry = 365; // днів
    this.overlay = null;
    this.init();
  }

  /**
   * Ініціалізація
   */
  init() {
    // Чекаємо коли DOM завантажиться
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => this.setup());
    } else {
      this.setup();
    }
  }

  /**
   * Налаштування після завантаження DOM
   */
  setup() {
    this.overlay = document.getElementById('cookieConsentOverlay');
    
    if (!this.overlay) {
      console.warn('Cookie consent overlay not found');
      return;
    }

    // Показуємо модалку якщо згода ще не дана
    if (!this.hasConsent()) {
      this.showModal();
    }

    // Додаємо обробники подій
    this.bindEvents();
  }

  /**
   * Прив'язуємо події до кнопок
   */
  bindEvents() {
    const acceptBtn = document.getElementById('acceptCookies');
    const declineBtn = document.getElementById('declineCookies');

    if (acceptBtn) {
      acceptBtn.addEventListener('click', () => this.acceptCookies());
    }

    if (declineBtn) {
      declineBtn.addEventListener('click', () => this.declineCookies());
    }

    // Закриття при кліку на overlay (опціонально)
    this.overlay.addEventListener('click', (e) => {
      if (e.target === this.overlay) {
        // Не закриваємо автоматично - юзер має явно обрати
      }
    });
  }

  /**
   * Показати модалку
   */
  showModal() {
    if (this.overlay) {
      // Невелика затримка для плавної анімації
      setTimeout(() => {
        this.overlay.classList.add('show');
      }, 100);
    }
  }

  /**
   * Сховати модалку
   */
  hideModal() {
    if (this.overlay) {
      this.overlay.classList.remove('show');
      
      // Видаляємо з DOM після анімації
      setTimeout(() => {
        this.overlay.style.display = 'none';
      }, 300);
    }
  }

  /**
   * Прийняти cookies
   */
  acceptCookies() {
    this.setCookie(this.cookieName, 'accepted', this.cookieExpiry);
    this.hideModal();
    
    // Можна додати додаткову логіку для аналітики
    this.enableAnalytics();
  }

  /**
   * Відхилити cookies
   */
  declineCookies() {
    this.setCookie(this.cookieName, 'declined', this.cookieExpiry);
    this.hideModal();
    
    // Вимикаємо всі необов'язкові cookies
    this.disableAnalytics();
  }

  /**
   * Перевірити чи є згода
   */
  hasConsent() {
    const consent = this.getCookie(this.cookieName);
    return consent === 'accepted' || consent === 'declined';
  }

  /**
   * Перевірити чи прийняті cookies
   */
  isAccepted() {
    return this.getCookie(this.cookieName) === 'accepted';
  }

  /**
   * Встановити cookie
   */
  setCookie(name, value, days) {
    const expires = new Date();
    expires.setTime(expires.getTime() + (days * 24 * 60 * 60 * 1000));
    document.cookie = `${name}=${value};expires=${expires.toUTCString()};path=/;SameSite=Lax`;
  }

  /**
   * Отримати cookie
   */
  getCookie(name) {
    const nameEQ = name + "=";
    const ca = document.cookie.split(';');
    
    for (let i = 0; i < ca.length; i++) {
      let c = ca[i];
      while (c.charAt(0) === ' ') c = c.substring(1, c.length);
      if (c.indexOf(nameEQ) === 0) return c.substring(nameEQ.length, c.length);
    }
    
    return null;
  }

  /**
   * Увімкнути аналітику (Google Analytics, тощо)
   */
  enableAnalytics() {
    // Тут можна додати Google Analytics, Meta Pixel, тощо
    console.log('Analytics enabled');
    
    // Приклад для Google Analytics
    /*
    if (typeof gtag !== 'undefined') {
      gtag('consent', 'update', {
        'analytics_storage': 'granted'
      });
    }
    */
  }

  /**
   * Вимкнути аналітику
   */
  disableAnalytics() {
    console.log('Analytics disabled');
    
    // Очищуємо аналітичні cookies якщо потрібно
    this.deleteCookie('_ga');
    this.deleteCookie('_gid');
    this.deleteCookie('_gat');
  }

  /**
   * Видалити cookie
   */
  deleteCookie(name) {
    document.cookie = `${name}=;expires=Thu, 01 Jan 1970 00:00:00 GMT;path=/`;
  }
}

// Ініціалізуємо при завантаженні сторінки
const cookieConsent = new CookieConsent();


