class SimpleProjectsAccordion {
  constructor(containerSelector = '.featured-projects-section') {
    this.container = document.querySelector(containerSelector);
    if (!this.container) return;
    this.items = this.container.querySelectorAll('.project-simple-item');
    this.triggers = this.container.querySelectorAll('.project-trigger');
    this.descriptions = this.container.querySelectorAll('.project-description-accordion');
    this.arrows = this.container.querySelectorAll('.accordion-arrow');
    this.animationDuration = 300;
    this.currentlyOpen = null;
    this.init();
  }
  init() {
    this.initializeAriaAttributes();
    this.addEventListeners();
    this.initializeLucideIcons();
    
  }
  initializeAriaAttributes() {
    this.triggers.forEach((trigger, index) => {
      const description = this.descriptions[index];
      const item = this.items[index];
      if (!description || !item) return;
      if (!description.id) {
        description.id = `project-desc-${index+1}`;
      }
      trigger.setAttribute('aria-expanded', 'false');
      trigger.setAttribute('aria-controls', description.id);
      description.hidden = true;
      description.style.height = '0px';
      description.style.overflow = 'hidden';
    });
  }
  addEventListeners() {
    this.triggers.forEach((trigger, index) => {
      trigger.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        this.toggleItem(index);
      });
      trigger.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          e.stopPropagation();
          this.toggleItem(index);
        }
        if (e.key === 'ArrowDown') {
          e.preventDefault();
          this.focusNextTrigger(index);
        } else if (e.key === 'ArrowUp') {
          e.preventDefault();
          this.focusPreviousTrigger(index);
        }
      });
    });
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && this.currentlyOpen !== null) {
        this.closeItem(this.currentlyOpen);
      }
    });
  }
  toggleItem(index) {
    const trigger = this.triggers[index];
    const description = this.descriptions[index];
    const arrow = this.arrows[index];
    if (!trigger || !description || !arrow) return;
    const isExpanded = trigger.getAttribute('aria-expanded') === 'true';
    if (isExpanded) {
      this.closeItem(index);
    } else {
      if (this.currentlyOpen !== null && this.currentlyOpen !== index) {
        this.closeItem(this.currentlyOpen);
      }
      this.openItem(index);
    }
  }
  async openItem(index) {
    const trigger = this.triggers[index];
    const description = this.descriptions[index];
    const arrow = this.arrows[index];
    if (!trigger || !description || !arrow) return;
    this.currentlyOpen = index;
    trigger.setAttribute('aria-expanded', 'true');
    description.hidden = false;
    description.style.height = 'auto';
    description.style.overflow = 'hidden';
    const targetHeight = description.scrollHeight;
    description.style.height = '0px';
    description.style.transition = `height ${this.animationDuration}ms cubic-bezier(0.4,0,0.2,1)`;
    arrow.style.transition = `transform ${this.animationDuration}ms cubic-bezier(0.4,0,0.2,1)`;
    arrow.style.transform = 'rotate(180deg)';
    requestAnimationFrame(() => {
      description.style.height = `${targetHeight}px`;
    });
    setTimeout(() => {
      description.style.height = 'auto';
      description.style.overflow = 'visible';
      description.style.transition = '';
      arrow.style.transition = '';
    }, this.animationDuration);
    setTimeout(() => {
      this.scrollToItem(index);
    }, this.animationDuration / 2);
  }
  async closeItem(index) {
    const trigger = this.triggers[index];
    const description = this.descriptions[index];
    const arrow = this.arrows[index];
    if (!trigger || !description || !arrow) return;
    this.currentlyOpen = null;
    trigger.setAttribute('aria-expanded', 'false');
    const currentHeight = description.scrollHeight;
    description.style.height = `${currentHeight}px`;
    description.style.overflow = 'hidden';
    description.style.transition = `height ${this.animationDuration}ms cubic-bezier(0.4,0,0.2,1)`;
    arrow.style.transition = `transform ${this.animationDuration}ms cubic-bezier(0.4,0,0.2,1)`;
    arrow.style.transform = 'rotate(0deg)';
    requestAnimationFrame(() => {
      description.style.height = '0px';
    });
    setTimeout(() => {
      description.hidden = true;
      description.style.height = 'auto';
      description.style.overflow = 'visible';
      description.style.transition = '';
      arrow.style.transition = '';
    }, this.animationDuration);
  }
  scrollToItem(index) {
    const item = this.items[index];
    if (!item) return;
    const itemRect = item.getBoundingClientRect();
    const windowHeight = window.innerHeight;
    if (itemRect.top < 100 || itemRect.bottom > windowHeight - 100) {
      item.scrollIntoView({
        behavior: 'smooth',
        block: 'start',
        inline: 'nearest'
      });
    }
  }
  focusNextTrigger(currentIndex) {
    const nextIndex = currentIndex + 1;
    if (nextIndex < this.triggers.length) {
      this.triggers[nextIndex].focus();
    }
  }
  focusPreviousTrigger(currentIndex) {
    const prevIndex = currentIndex - 1;
    if (prevIndex >= 0) {
      this.triggers[prevIndex].focus();
    }
  }
  initializeLucideIcons() {
    if (typeof lucide !== 'undefined' && lucide.createIcons) {
      setTimeout(() => {
        lucide.createIcons();
      }, 100);
    }
  }
  openItemByIndex(index) {
    if (index >= 0 && index < this.items.length) {
      this.openItem(index);
    }
  }
  closeItemByIndex(index) {
    if (index >= 0 && index < this.items.length) {
      this.closeItem(index);
    }
  }
  closeAll() {
    if (this.currentlyOpen !== null) {
      this.closeItem(this.currentlyOpen);
    }
  }
  getOpenItemIndex() {
    return this.currentlyOpen;
  }
  isItemOpen(index) {
    return this.currentlyOpen === index;
  }
  refresh() {
    this.items = this.container.querySelectorAll('.project-simple-item');
    this.triggers = this.container.querySelectorAll('.project-trigger');
    this.descriptions = this.container.querySelectorAll('.project-description-accordion');
    this.arrows = this.container.querySelectorAll('.accordion-arrow');
    this.currentlyOpen = null;
    this.initializeAriaAttributes();
    this.addEventListeners();
    this.initializeLucideIcons();
    
  }
  destroy() {
    this.triggers.forEach((trigger) => {
      trigger.removeEventListener('click', this.toggleItem);
      trigger.removeEventListener('keydown', this.toggleItem);
    });
    this.descriptions.forEach((description) => {
      description.hidden = false;
      description.style.height = 'auto';
      description.style.overflow = 'visible';
      description.style.transition = '';
    });
    this.arrows.forEach((arrow) => {
      arrow.style.transform = '';
      arrow.style.transition = '';
    });
    
  }
}
document.addEventListener('DOMContentLoaded', function() {
  if (document.querySelector('.featured-projects-section')) {
    window.simpleProjectsAccordion = new SimpleProjectsAccordion();
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
      window.debugAccordion = {
        open: (index) => window.simpleProjectsAccordion.openItemByIndex(index),
        close: (index) => window.simpleProjectsAccordion.closeItemByIndex(index),
        closeAll: () => window.simpleProjectsAccordion.closeAll(),
        refresh: () => window.simpleProjectsAccordion.refresh(),
        destroy: () => window.simpleProjectsAccordion.destroy()
      };
      
    }
  }
});
window.addEventListener('popstate', function() {
  if (window.simpleProjectsAccordion && document.querySelector('.featured-projects-section')) {
    window.simpleProjectsAccordion.refresh();
  }
});
if (typeof module !== 'undefined' && module.exports) {
  module.exports = SimpleProjectsAccordion;
}
if (typeof define === 'function' && define.amd) {
  define([], function() {
    return SimpleProjectsAccordion;
  });
}