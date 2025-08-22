// 🚀 LAZYSOFT - Main JavaScript File

document.addEventListener("DOMContentLoaded", () => {
  // 🎨 Добавляем CSS правила прямо через JavaScript
  const style = document.createElement('style');
  style.textContent = `
    [data-lang]:not(.js-active) {
      display: none !important;
      visibility: hidden !important;
      opacity: 0 !important;
    }
    
    [data-lang].js-active {
      display: block !important;
      visibility: visible !important;
      opacity: 1 !important;
    }

    .about-card[data-lang].js-active {
      display: flex !important;
    }
    
    span[data-lang].js-active {
      display: inline !important;
    }
    
    /* Плавный переход для переключения языков */
    [data-lang] {
      transition: opacity 0.2s ease-in-out;
    }
    
    /* Предотвращаем прыжки страницы */
    .hero-content {
      min-height: 80px;
    }
  `;
  document.head.appendChild(style);
  
  // 🌐 Определение текущего языка из URL
  const urlPath = window.location.pathname;
  let currentLang = 'en'; // по умолчанию
  
  if (urlPath.startsWith('/uk/') || urlPath === '/uk') {
    currentLang = 'uk';
  } else if (urlPath.startsWith('/pl/') || urlPath === '/pl') {
    currentLang = 'pl';
  } else if (urlPath === '/' || urlPath.startsWith('/en/')) {
    currentLang = 'en';
  }
  
  // 🔄 Переключение языковых элементов
  switchLanguage(currentLang);
  
  // 🎯 Обработчики для языковых ссылок
  document.querySelectorAll('.lang-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const href = btn.getAttribute('href');
      let newLang = 'en';
      
      if (href === '/uk/' || href.includes('/uk/')) {
        newLang = 'uk';
      } else if (href === '/pl/' || href.includes('/pl/')) {
        newLang = 'pl';
      } else if (href === '/' || href.includes('/en/')) {
        newLang = 'en';
      }
      
      // Предварительное переключение для плавности
      switchLanguage(newLang);
    });
  });

  // 🍔 Инициализация мобильного меню
  initMobileMenu();
  
  // 🖱️ Инициализация кликабельных карточек
  initClickableCards();
});

// 🌐 Функция переключения языка
function switchLanguage(currentLang) {
  // Плавное переключение элементов
  document.querySelectorAll("[data-lang]").forEach(el => {
    if (el.dataset.lang === currentLang) {
      // Показываем элемент
      el.style.opacity = '0';
      
      setTimeout(() => {
        if (el.tagName.toLowerCase() === 'span') {
          el.style.display = 'inline';
        } else if (el.classList.contains('about-card')) {
          el.style.display = 'flex';
        } else {
          el.style.display = 'block';
        }
        el.style.visibility = 'visible';
        el.classList.remove('active', 'js-active');
        if (el.dataset.lang === currentLang) {
          el.classList.add('active', 'js-active');
        }
        
        // Плавное появление
        setTimeout(() => {
          el.style.opacity = '1';
        }, 10);
      }, 50);
      
    } else {
      // Плавно скрываем элемент
      el.style.opacity = '0';
      
      setTimeout(() => {
        el.style.display = 'none';
        el.style.visibility = 'hidden';
        el.classList.remove('active', 'js-active');
      }, 100);
    }
  });
  
  // Обновляем активную кнопку языка
  document.querySelectorAll('.lang-btn').forEach(btn => {
    const href = btn.getAttribute('href');
    let btnLang = 'en';
    
    if (href === '/uk/' || href.includes('/uk/')) {
      btnLang = 'uk';
    } else if (href === '/pl/' || href.includes('/pl/')) {
      btnLang = 'pl';
    } else if (href === '/' || href.includes('/en/')) {
      btnLang = 'en';
    }
    
    if (btnLang === currentLang) {
      btn.classList.add('active');
    } else {
      btn.classList.remove('active');
    }
  });
}

// 🍔 Функция для мобильного меню
function toggleMenu() {
  const burger = document.querySelector('.burger');
  const navLinks = document.querySelector('.nav-links');
  
  if (burger && navLinks) {
    burger.classList.toggle('active');
    navLinks.classList.toggle('active');
  }
}

// 🍔 Инициализация мобильного меню
function initMobileMenu() {
  const burger = document.querySelector('.burger');
  const navLinks = document.querySelector('.nav-links');
  const navbar = document.querySelector('.navbar');
  
  if (!burger || !navLinks || !navbar) return;
  
  // Закриваємо при кліку поза навігацією
  document.addEventListener('click', function(event) {
    if (!navbar.contains(event.target)) {
      burger.classList.remove('active');
      navLinks.classList.remove('active');
    }
  });
  
  // Закриваємо при кліку на посилання в мобільному меню
  navLinks.querySelectorAll('a').forEach(link => {
    link.addEventListener('click', function() {
      burger.classList.remove('active');
      navLinks.classList.remove('active');
    });
  });
  
  // Закриваємо при зміні розміру екрана
  window.addEventListener('resize', function() {
    if (window.innerWidth > 768) {
      burger.classList.remove('active');
      navLinks.classList.remove('active');
    }
  });
}

// 🖱️ Инициализация кликабельных карточек
function initClickableCards() {
  // Кликабельные карточки с data-href
  document.querySelectorAll('.clickable[data-href]').forEach(card => {
    card.style.cursor = 'pointer';
    card.addEventListener('click', () => {
      const href = card.getAttribute('data-href');
      if (href) {
        window.location.href = href;
      }
    });
  });

  // About карточки
  document.querySelectorAll('.about-card[data-href]').forEach(card => {
    card.style.cursor = 'pointer';
    card.addEventListener('click', () => {
      const link = card.getAttribute('data-href');
      if (link) {
        window.location.href = link;
      }
    });
  });
}

// 📞 Функция прокрутки к контакт форме
function scrollToContact(projectTitle) {
  if (event) {
    event.stopPropagation();
  }
  
  const contactSection = document.getElementById('contact');
  if (contactSection) {
    contactSection.scrollIntoView({ 
      behavior: 'smooth',
      block: 'start'
    });
    
    // Заполняем форму если есть название проекта
    setTimeout(() => {
      const messageField = document.querySelector('#contact textarea, #contact input[name="message"]');
      if (messageField && projectTitle) {
        const currentLang = document.documentElement.lang || 'uk';
        const messages = {
          'uk': `Привіт! Мене зацікавив проєкт "${projectTitle}". Хочу замовити щось подібне для свого бізнесу. Розкажіть більше про можливості та вартість.`,
          'en': `Hi! I'm interested in the "${projectTitle}" project. I'd like to order something similar for my business. Please tell me more about possibilities and pricing.`,
          'pl': `Cześć! Interesuje mnie projekt "${projectTitle}". Chciałbym zamówić coś podobnego dla mojego biznesu. Proszę opowiedzieć więcej o możliwościach i cenach.`
        };
        messageField.value = messages[currentLang] || messages['uk'];
        messageField.focus();
      }
    }, 1000);
  }
}

// 🎯 Плавное появление элементов при скроле
function initScrollAnimations() {
  const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
  };

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('fade-in-up');
      }
    });
  }, observerOptions);

  // Наблюдаем за секциями
  document.querySelectorAll('.section, .project-card, .news-card').forEach(el => {
    observer.observe(el);
  });
}

// 🖱️ Smooth scroll для внутренних ссылок
function initSmoothScroll() {
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
      e.preventDefault();
      const target = document.querySelector(this.getAttribute('href'));
      if (target) {
        target.scrollIntoView({
          behavior: 'smooth',
          block: 'start'
        });
      }
    });
  });
}

// 🎨 Parallax эффект для фоновых элементов
function initParallax() {
  const shapes = document.querySelectorAll('.bg-shape');
  
  window.addEventListener('scroll', () => {
    const scrolled = window.pageYOffset;
    const rate = scrolled * -0.5;
    
    shapes.forEach((shape, index) => {
      const speed = (index + 1) * 0.1;
      shape.style.transform = `translateY(${rate * speed}px)`;
    });
  });
}

// 📱 Определение устройства
function isMobileDevice() {
  return window.innerWidth <= 768;
}

// 🎯 Lazy loading для изображений
function initLazyLoading() {
  const images = document.querySelectorAll('img[data-src]');
  
  const imageObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const img = entry.target;
        img.src = img.dataset.src;
        img.classList.remove('lazy');
        imageObserver.unobserve(img);
      }
    });
  });

  images.forEach(img => imageObserver.observe(img));
}

// 🔄 Инициализация всех функций
function initAll() {
  if ('IntersectionObserver' in window) {
    initScrollAnimations();
    initLazyLoading();
  }
  
  initSmoothScroll();
  
  // Parallax только для десктопа
  if (!isMobileDevice()) {
    initParallax();
  }
}

// 🚀 Запуск всех функций после загрузки
window.addEventListener('load', initAll);

// 📱 Перезапуск при изменении размера окна
let resizeTimer;
window.addEventListener('resize', () => {
  clearTimeout(resizeTimer);
  resizeTimer = setTimeout(() => {
    // Перезапускаем только необходимые функции
    if (isMobileDevice()) {
      // Отключаем параллакс на мобильном
      document.querySelectorAll('.bg-shape').forEach(shape => {
        shape.style.transform = '';
      });
    } else {
      // Включаем параллакс на десктопе
      initParallax();
    }
  }, 250);
});

// 🎯 Экспорт функций для глобального использования
window.toggleMenu = toggleMenu;
window.scrollToContact = scrollToContact;
window.switchLanguage = switchLanguage;