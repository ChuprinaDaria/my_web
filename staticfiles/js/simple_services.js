// ===============================================
// 🔥 ПРОСТИЙ JS ДЛЯ СЕРВІСІВ - БЕЗ КАРУСЕЛІ
// ===============================================

document.addEventListener('DOMContentLoaded', function() {
  
  if (typeof lucide !== 'undefined') {
    lucide.createIcons();
  }
  
  const serviceItems = document.querySelectorAll('.service-horizontal-item');
  
  serviceItems.forEach(function(item) {
    const accordion = item.querySelector('.service-description-accordion');
    const serviceSlug = item.getAttribute('data-service-id');
    const titleElement = item.querySelector('.service-title');
    const arrowElement = item.querySelector('.accordion-arrow');
    const serviceUrl = item.getAttribute('data-service-url');
    
    if (!accordion) return;
    
    if (titleElement) {
      titleElement.addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        
        if (serviceUrl) {
          window.location.href = serviceUrl;
        }
      });
    }
    
    if (arrowElement) {
      arrowElement.addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        
        toggleAccordion(accordion);
      });
    } else {
      
    }
    
    item.addEventListener('click', function(e) {
      
      
      if (e.target === titleElement || titleElement.contains(e.target) || 
          e.target === arrowElement || arrowElement.contains(e.target)) {
        
        return;
      }
      
      e.preventDefault();
      e.stopPropagation();
      
      
      
      setTimeout(() => {
        if (!item.dataset.doubleClick) {
          
          toggleAccordion(accordion);
        }
        delete item.dataset.doubleClick;
      }, 200);
    });
    
    item.addEventListener('dblclick', function(e) {
      e.preventDefault();
      e.stopPropagation();
      item.dataset.doubleClick = 'true';
      
      if (serviceUrl) {
        window.location.href = serviceUrl;
      } else if (serviceSlug) {
        
        const currentPath = window.location.pathname;
        const basePath = currentPath.replace(/\/$/, '');
        window.location.href = `${basePath}/${serviceSlug}/`;
      }
    });
    
    item.addEventListener('keydown', function(e) {
      if (e.key === 'Enter') {
        e.preventDefault();
        toggleAccordion(accordion);
      }
      
      if (e.key === ' ') {
        e.preventDefault();
        toggleAccordion(accordion);
      }
    });
    
    item.setAttribute('tabindex', '0');
    item.setAttribute('role', 'button');
    item.setAttribute('aria-expanded', 'false');
  });
  
  function toggleAccordion(accordion) {
    const isOpen = accordion.classList.contains('open');
    const serviceItem = accordion.closest('.service-horizontal-item');
    
    
    
    if (isOpen) {
      
      accordion.style.display = 'none';
      accordion.classList.remove('open');
      serviceItem.setAttribute('aria-expanded', 'false');
    } else {
      
      accordion.style.display = 'block';
      accordion.classList.add('open');
      serviceItem.setAttribute('aria-expanded', 'true');
    }
  }
  
  document.addEventListener('click', function(e) {
    if (!e.target.closest('.service-horizontal-item')) {
      closeAllAccordions();
    }
  });
  
  function closeAllAccordions() {
    const openAccordions = document.querySelectorAll('.service-description-accordion.open');
    openAccordions.forEach(function(accordion) {
      accordion.style.display = 'none';
      accordion.classList.remove('open');
      const serviceItem = accordion.closest('.service-horizontal-item');
      serviceItem.setAttribute('aria-expanded', 'false');
    });
  }
  
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
      closeAllAccordions();
    }
  });
  
  
  
});
