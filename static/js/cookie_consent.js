class CookieConsent {
  constructor() {
    this.cookieName = 'cookie_consent';
    this.cookieExpiry = 365; 
    this.overlay = null;
    this.init();
  }

  init() {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => this.setup());
    } else {
      this.setup();
    }
  }

  setup() {
    this.overlay = document.getElementById('cookieConsentOverlay');
    
    if (!this.overlay) {
      
      return;
    }

    
    if (!this.hasConsent()) {
      this.showModal();
    }

    
    this.bindEvents();
  }

  bindEvents() {
    const acceptBtn = document.getElementById('acceptCookies');
    const declineBtn = document.getElementById('declineCookies');

    if (acceptBtn) {
      acceptBtn.addEventListener('click', () => this.acceptCookies());
    }

    if (declineBtn) {
      declineBtn.addEventListener('click', () => this.declineCookies());
    }

    
    this.overlay.addEventListener('click', (e) => {
      if (e.target === this.overlay) {
        
      }
    });
  }

  showModal() {
    if (this.overlay) {
      
      setTimeout(() => {
        this.overlay.classList.add('show');
      }, 100);
    }
  }

  hideModal() {
    if (this.overlay) {
      this.overlay.classList.remove('show');
      
      
      setTimeout(() => {
        this.overlay.style.display = 'none';
      }, 300);
    }
  }

  acceptCookies() {
    this.setCookie(this.cookieName, 'accepted', this.cookieExpiry);
    this.hideModal();
    
    
    this.enableAnalytics();
  }

  declineCookies() {
    this.setCookie(this.cookieName, 'declined', this.cookieExpiry);
    this.hideModal();
    
    
    this.disableAnalytics();
  }

  hasConsent() {
    const consent = this.getCookie(this.cookieName);
    return consent === 'accepted' || consent === 'declined';
  }

  isAccepted() {
    return this.getCookie(this.cookieName) === 'accepted';
  }

  setCookie(name, value, days) {
    const expires = new Date();
    expires.setTime(expires.getTime() + (days * 24 * 60 * 60 * 1000));
    document.cookie = `${name}=${value};expires=${expires.toUTCString()};path=/;SameSite=Lax`;
  }

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

  enableAnalytics() {
    
    
    
    
  }

  disableAnalytics() {
    
    
    this.deleteCookie('_ga');
    this.deleteCookie('_gid');
    this.deleteCookie('_gat');
  }

  deleteCookie(name) {
    document.cookie = `${name}=;expires=Thu, 01 Jan 1970 00:00:00 GMT;path=/`;
  }
}

const cookieConsent = new CookieConsent();


