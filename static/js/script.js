document.addEventListener("DOMContentLoaded", () => {
  // Добавляем CSS правила прямо через JavaScript
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
      min-height: 400px;
    }
    
    /* Стили для языковых кнопок */
    .language-selector {
      display: flex;
      gap: 5px;
    }
    
    .lang-btn {
      padding: 5px 10px !important;
      font-size: 12px;
      border: 1px solid var(--glass-border, rgba(255,255,255,0.25));
      border-radius: 15px;
      cursor: pointer;
      text-decoration: none !important;
      color: var(--text-primary, #b3adad);
      transition: all 0.3s ease;
    }
    
    .lang-btn.active {
      background: var(--accent-green, #9eff00);
      color: var(--primary-black, #0a0a0a);
    }
    
    .lang-btn:hover {
      background: var(--glass-bg, rgba(255,255,255,0.12));
    }
  `;
  document.head.appendChild(style);
  
  // Определение текущего языка из URL
  const urlPath = window.location.pathname;
  let currentLang = 'en'; // по умолчанию
  
  if (urlPath.startsWith('/uk/') || urlPath === '/uk') {
    currentLang = 'uk';
  } else if (urlPath.startsWith('/pl/') || urlPath === '/pl') {
    currentLang = 'pl';
  } else if (urlPath === '/' || urlPath.startsWith('/en/')) {
    currentLang = 'en'; // для корневого URL и /en/
  }
  
  
  
  // Переключение языковых элементов
  switchLanguage(currentLang);
  
  // Обработчики для языковых ссылок (если они есть)
  document.querySelectorAll('.lang-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const href = btn.getAttribute('href');
      let newLang = 'en';
      
      if (href === '/uk/') {
        newLang = 'uk';
      } else if (href === '/pl/') {
        newLang = 'pl';
      } else if (href === '/') {
        newLang = 'en';
      }
      
      
      
      // Предварительное переключение для плавности
      switchLanguage(newLang);
    });
  });
});

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
        el.classList.add('active', 'js-active');
        
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
    
    if (href === '/uk/') {
      btnLang = 'uk';
    } else if (href === '/pl/') {
      btnLang = 'pl';
    } else if (href === '/') {
      btnLang = 'en';
    }
    
    if (btnLang === currentLang) {
      btn.classList.add('active');
    } else {
      btn.classList.remove('active');
    }
  });
  
  // Финальная проверка
  setTimeout(() => {
    const finalVisible = document.querySelectorAll('[data-lang].js-active');
    
  }, 200);
}

// Функция для burger menu
function toggleMenu() {
  const menu = document.getElementById('mobileMenu');
  if (menu) {
    menu.classList.toggle('active');
  }
}

document.querySelectorAll('.about-card[data-href]').forEach(card => {
  card.style.cursor = 'pointer';
  card.addEventListener('click', () => {
    const link = card.getAttribute('data-href');
    if (link) {
      window.location.href = link;
    }
  });
});
