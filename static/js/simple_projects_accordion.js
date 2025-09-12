/* ===============================================
   🎯 SIMPLE PROJECTS ACCORDION JAVASCRIPT
   =============================================== */

class SimpleProjectsAccordion {
  constructor(containerSelector = '.featured-projects-section') {
    this.container = document.querySelector(containerSelector);
    if (!this.container) return;
    
    this.items = this.container.querySelectorAll('.project-simple-item');
    this.triggers = this.container.querySelectorAll('.project-trigger');
    this.descriptions = this.container.querySelectorAll('.project-description-accordion');
    this.arrows = this.container.querySelectorAll('.accordion-arrow');
    
    this.init();
  }
  
  init() {
    // Додаємо обробники подій для кожного тригера
    this.triggers.forEach((trigger, index) => {
      trigger.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        this.toggleItem(index);
      });
      
      // Keyboard support
      trigger.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          e.stopPropagation();
          this.toggleItem(index);
        }
      });
    });
    
    // Ініціалізація ARIA атрибутів
    this.updateAriaAttributes();
    
    console.log(`Simple projects accordion initialized with ${this.items.length} items`);
  }
  
  toggleItem(index) {
    const item = this.items[index];
    const description = this.descriptions[index];
    const arrow = this.arrows[index];
    const trigger = this.triggers[index];
    
    if (!item || !description || !arrow || !trigger) return;
    
    const isExpanded = item.getAttribute('aria-expanded') === 'true';
    
    if (isExpanded) {
      this.closeItem(item, description, arrow, trigger);
    } else {
      // Закриваємо всі інші елементи (accordion behavior)
      this.closeAllItems();
      this.openItem(item, description, arrow, trigger);
    }
  }
  
  openItem(item, description, arrow, trigger) {
    // Показуємо опис
    description.hidden = false;
    description.style.height = 'auto';
    
    // Оновлюємо ARIA
    item.setAttribute('aria-expanded', 'true');
    trigger.setAttribute('aria-expanded', 'true');
    
    // Анімація стрілки
    arrow.style.transform = 'rotate(180deg)';
    
    // Плавна анімація висоти
    const height = description.offsetHeight;
    description.style.height = '0px';
    description.style.overflow = 'hidden';
    
    requestAnimationFrame(() => {
      description.style.transition = 'height 0.3s ease';
      description.style.height = height + 'px';
      
      // Після завершення анімації
      setTimeout(() => {
        description.style.height = 'auto';
        description.style.overflow = 'visible';
        description.style.transition = '';
      }, 300);
    });
    
    // Фокус на тригер для accessibility
    trigger.focus();
  }
  
  closeItem(item, description, arrow, trigger) {
    // Анімація закриття
    const height = description.offsetHeight;
    description.style.height = height + 'px';
    description.style.overflow = 'hidden';
    description.style.transition = 'height 0.3s ease';
    
    requestAnimationFrame(() => {
      description.style.height = '0px';
      
      setTimeout(() => {
        description.hidden = true;
        description.style.height = 'auto';
        description.style.overflow = 'visible';
        description.style.transition = '';
      }, 300);
    });
    
    // Оновлюємо ARIA
    item.setAttribute('aria-expanded', 'false');
    trigger.setAttribute('aria-expanded', 'false');
    
    // Анімація стрілки
    arrow.style.transform = 'rotate(0deg)';
  }
  
  closeAllItems() {
    this.items.forEach((item, index) => {
      const description = this.descriptions[index];
      const arrow = this.arrows[index];
      const trigger = this.triggers[index];
      
      if (item.getAttribute('aria-expanded') === 'true') {
        this.closeItem(item, description, arrow, trigger);
      }
    });
  }
  
  updateAriaAttributes() {
    this.items.forEach((item, index) => {
      const trigger = this.triggers[index];
      const description = this.descriptions[index];
      
      // Встановлюємо початкові ARIA атрибути
      item.setAttribute('aria-expanded', 'false');
      trigger.setAttribute('aria-expanded', 'false');
      trigger.setAttribute('aria-controls', `pdesc-${index + 1}`);
      
      // Приховуємо всі описи за замовчуванням
      if (description) {
        description.hidden = true;
      }
    });
  }
  
  // Публічні методи для зовнішнього використання
  openItemByIndex(index) {
    if (index >= 0 && index < this.items.length) {
      this.toggleItem(index);
    }
  }
  
  closeAll() {
    this.closeAllItems();
  }
  
  getOpenItemIndex() {
    for (let i = 0; i < this.items.length; i++) {
      if (this.items[i].getAttribute('aria-expanded') === 'true') {
        return i;
      }
    }
    return -1;
  }
}

// Автоматична ініціалізація при завантаженні DOM
document.addEventListener('DOMContentLoaded', function() {
  // Ініціалізуємо тільки якщо є контейнер проєктів
  if (document.querySelector('.featured-projects-section')) {
    window.simpleProjectsAccordion = new SimpleProjectsAccordion();
  }
});

// Експорт для використання в модульних системах
if (typeof module !== 'undefined' && module.exports) {
  module.exports = SimpleProjectsAccordion;
}
