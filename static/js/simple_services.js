// ===============================================
// 🔥 ПРОСТИЙ JS ДЛЯ СЕРВІСІВ - БЕЗ КАРУСЕЛІ
// ===============================================

console.log('🔥 Simple Services JS file loaded');

document.addEventListener('DOMContentLoaded', function() {
  
  // Ініціалізація Lucide іконок
  if (typeof lucide !== 'undefined') {
    lucide.createIcons();
  }
  
  // Отримуємо всі елементи сервісів
  const serviceItems = document.querySelectorAll('.service-horizontal-item');
  
  serviceItems.forEach(function(item) {
    const accordion = item.querySelector('.service-description-accordion');
    const serviceSlug = item.getAttribute('data-service-id');
    const titleElement = item.querySelector('.service-title');
    const arrowElement = item.querySelector('.accordion-arrow');
    const serviceUrl = item.getAttribute('data-service-url');
    
    if (!accordion) return;
    
    // КЛІК НА ЗАГОЛОВОК - переходить на сторінку сервісу
    if (titleElement) {
      titleElement.addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        
        if (serviceUrl) {
          window.location.href = serviceUrl;
        }
      });
    }
    
    // КЛІК НА СТРІЛОЧКУ - відкриває/закриває акордеон
    if (arrowElement) {
      arrowElement.addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        console.log('Arrow clicked');
        toggleAccordion(accordion);
      });
    } else {
      console.log('Arrow element not found');
    }
    
    // КЛІК НА КАРТКУ - відкриває/закриває акордеон (тільки якщо не клікнули на заголовок або стрілочку)
    item.addEventListener('click', function(e) {
      console.log('Card clicked, target:', e.target);
      
      // Якщо клікнули на заголовок або стрілочку, не обробляємо
      if (e.target === titleElement || titleElement.contains(e.target) || 
          e.target === arrowElement || arrowElement.contains(e.target)) {
        console.log('Clicked on title or arrow, ignoring');
        return;
      }
      
      e.preventDefault();
      e.stopPropagation();
      
      console.log('Processing card click');
      
      // Невелика затримка для розрізнення одинарного та подвійного кліку
      setTimeout(() => {
        if (!item.dataset.doubleClick) {
          console.log('Single click - toggling accordion');
          toggleAccordion(accordion);
        }
        delete item.dataset.doubleClick;
      }, 200);
    });
    
    // ПОДВІЙНИЙ КЛІК - переходить на сторінку сервісу
    item.addEventListener('dblclick', function(e) {
      e.preventDefault();
      e.stopPropagation();
      item.dataset.doubleClick = 'true';
      
      if (serviceUrl) {
        window.location.href = serviceUrl;
      } else if (serviceSlug) {
        // Fallback - використовуємо поточний URL з додаванням slug
        const currentPath = window.location.pathname;
        const basePath = currentPath.replace(/\/$/, '');
        window.location.href = `${basePath}/${serviceSlug}/`;
      }
    });
    
    // ENTER на клавіатурі
    item.addEventListener('keydown', function(e) {
      if (e.key === 'Enter') {
        e.preventDefault();
        toggleAccordion(accordion);
      }
      
      // SPACE - теж відкриває акордеон
      if (e.key === ' ') {
        e.preventDefault();
        toggleAccordion(accordion);
      }
    });
    
    // Робимо елемент фокусованим
    item.setAttribute('tabindex', '0');
    item.setAttribute('role', 'button');
    item.setAttribute('aria-expanded', 'false');
  });
  
  // Функція для відкриття/закриття акордеону
  function toggleAccordion(accordion) {
    const isOpen = accordion.classList.contains('open');
    const serviceItem = accordion.closest('.service-horizontal-item');
    
    console.log('Toggle accordion:', isOpen ? 'closing' : 'opening');
    
    if (isOpen) {
      // Закриваємо
      accordion.style.display = 'none';
      accordion.classList.remove('open');
      serviceItem.setAttribute('aria-expanded', 'false');
    } else {
      // Відкриваємо
      accordion.style.display = 'block';
      accordion.classList.add('open');
      serviceItem.setAttribute('aria-expanded', 'true');
    }
  }
  
  // Закриваємо всі акордеони при кліку поза ними
  document.addEventListener('click', function(e) {
    if (!e.target.closest('.service-horizontal-item')) {
      closeAllAccordions();
    }
  });
  
  // Функція для закриття всіх акордеонів
  function closeAllAccordions() {
    const openAccordions = document.querySelectorAll('.service-description-accordion.open');
    openAccordions.forEach(function(accordion) {
      accordion.style.display = 'none';
      accordion.classList.remove('open');
      const serviceItem = accordion.closest('.service-horizontal-item');
      serviceItem.setAttribute('aria-expanded', 'false');
    });
  }
  
  // ESC закриває всі акордеони
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
      closeAllAccordions();
    }
  });
  
  console.log('🔥 Simple Services JS initialized');
  console.log('Found service items:', serviceItems.length);
});
