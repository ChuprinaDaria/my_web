/* ===============================================
   🎠 PROJECTS ACCORDION JAVASCRIPT
   =============================================== */

class ProjectsAccordion {
  constructor(containerSelector = '.projects-accordion-container') {
    this.container = document.querySelector(containerSelector);
    if (!this.container) return;
    
    this.track = this.container.querySelector('.projects-accordion-track');
    this.prevBtn = this.container.querySelector('.nav-prev');
    this.nextBtn = this.container.querySelector('.nav-next');
    this.items = this.track ? this.track.querySelectorAll('.project-accordion-item') : [];
    
    // Налаштування
    this.currentIndex = 0;
    this.itemHeight = this.getItemHeight();
    this.visibleItems = this.getVisibleItems();
    this.totalItems = this.items.length;
    this.maxIndex = Math.max(0, this.totalItems - this.visibleItems);
    
    // Автопрокрутка
    this.autoPlay = true;
    this.autoPlayInterval = 4000;
    this.autoPlayTimer = null;
    
    this.init();
  }
  
  getItemHeight() {
    if (window.innerWidth <= 480) return 120;
    if (window.innerWidth <= 768) return 140;
    return 200;
  }
  
  getVisibleItems() {
    if (window.innerWidth <= 480) return 2;
    if (window.innerWidth <= 768) return 2;
    return 3;
  }
  
  init() {
    if (!this.track || !this.prevBtn || !this.nextBtn) return;
    
    // Події кнопок
    this.prevBtn.addEventListener('click', () => this.prev());
    this.nextBtn.addEventListener('click', () => this.next());
    
    // Responsive
    window.addEventListener('resize', () => this.handleResize());
    
    // Touch events для мобілки
    this.addTouchEvents();
    
    // Hover events для автопрокрутки
    this.container.addEventListener('mouseenter', () => this.stopAutoPlay());
    this.container.addEventListener('mouseleave', () => this.startAutoPlay());
    
    // Ініціалізація
    this.updateAccordion();
    this.startAutoPlay();
    
    console.log('🎠 Projects Accordion ініціалізовано:', {
      totalItems: this.totalItems,
      visibleItems: this.visibleItems,
      itemHeight: this.itemHeight
    });
  }
  
  prev() {
    if (this.currentIndex > 0) {
      this.currentIndex--;
      this.updateAccordion();
      this.resetAutoPlay();
    }
  }
  
  next() {
    if (this.currentIndex < this.maxIndex) {
      this.currentIndex++;
      this.updateAccordion();
      this.resetAutoPlay();
    }
  }
  
  goTo(index) {
    this.currentIndex = Math.max(0, Math.min(index, this.maxIndex));
    this.updateAccordion();
    this.resetAutoPlay();
  }
  
  updateAccordion() {
    if (!this.track) return;
    
    // Анімація переходу
    this.track.style.transform = `translateY(-${this.currentIndex * this.itemHeight}px)`;
    
    // Оновлення кнопок
    this.prevBtn.disabled = this.currentIndex === 0;
    this.nextBtn.disabled = this.currentIndex >= this.maxIndex;
    
    // Додавання активного класу
    this.items.forEach((item, index) => {
      const isVisible = index >= this.currentIndex && index < this.currentIndex + this.visibleItems;
      item.classList.toggle('visible', isVisible);
    });
  }
  
  handleResize() {
    // Оновлюємо налаштування при зміні розміру
    const newItemHeight = this.getItemHeight();
    const newVisibleItems = this.getVisibleItems();
    
    if (newItemHeight !== this.itemHeight || newVisibleItems !== this.visibleItems) {
      this.itemHeight = newItemHeight;
      this.visibleItems = newVisibleItems;
      this.maxIndex = Math.max(0, this.totalItems - this.visibleItems);
      
      // Корегуємо поточний індекс якщо потрібно
      if (this.currentIndex > this.maxIndex) {
        this.currentIndex = this.maxIndex;
      }
      
      this.updateAccordion();
    }
  }
  
  addTouchEvents() {
    let startY = 0;
    let startTime = 0;
    
    this.track.addEventListener('touchstart', (e) => {
      startY = e.touches[0].clientY;
      startTime = Date.now();
      this.stopAutoPlay();
    });
    
    this.track.addEventListener('touchend', (e) => {
      const endY = e.changedTouches[0].clientY;
      const endTime = Date.now();
      const deltaY = startY - endY;
      const deltaTime = endTime - startTime;
      
      // Swipe detection
      if (Math.abs(deltaY) > 50 && deltaTime < 300) {
        if (deltaY > 0) {
          this.next();
        } else {
          this.prev();
        }
      }
      
      this.startAutoPlay();
    });
  }
  
  startAutoPlay() {
    if (!this.autoPlay) return;
    
    this.stopAutoPlay();
    this.autoPlayTimer = setInterval(() => {
      if (this.currentIndex >= this.maxIndex) {
        this.currentIndex = 0;
      } else {
        this.currentIndex++;
      }
      this.updateAccordion();
    }, this.autoPlayInterval);
  }
  
  stopAutoPlay() {
    if (this.autoPlayTimer) {
      clearInterval(this.autoPlayTimer);
      this.autoPlayTimer = null;
    }
  }
  
  resetAutoPlay() {
    this.stopAutoPlay();
    this.startAutoPlay();
  }
  
  destroy() {
    this.stopAutoPlay();
    // Remove event listeners if needed
  }
}

/* ===============================================
   🚀 PROJECTS PAGE INITIALIZATION
   =============================================== */

document.addEventListener('DOMContentLoaded', function() {
  // Initialize Lucide icons
  if (typeof lucide !== 'undefined') {
    lucide.createIcons();
  }
  
  // Initialize Projects Accordion
  window.projectsAccordion = new ProjectsAccordion();
  
  // Initialize other components if needed
  console.log('🚀 Projects page initialized');
});

/* ===============================================
   📞 CONTACT SCROLL FUNCTION
   =============================================== */

function scrollToContact(projectInfo) {
  const contactSection = document.getElementById('contact');
  if (contactSection) {
    contactSection.scrollIntoView({ 
      behavior: 'smooth',
      block: 'start'
    });
    
    setTimeout(() => {
      const messageField = document.querySelector('#contact textarea, #contact input[name="message"]');
      if (messageField && projectInfo) {
        const currentLang = document.documentElement.lang || 'uk';
        const messages = {
          'uk': `Привіт! Мене зацікавили проєкти з категорії "${projectInfo}". Хочу обговорити можливості співпраці.`,
          'en': `Hi! I'm interested in projects from "${projectInfo}" category. I'd like to discuss collaboration opportunities.`,
          'pl': `Cześć! Interesują mnie projekty z kategorii "${projectInfo}". Chciałbym omówić możliwości współpracy.`
        };
        messageField.value = messages[currentLang] || messages['uk'];
        messageField.focus();
      }
    }, 1000);
  }
}
