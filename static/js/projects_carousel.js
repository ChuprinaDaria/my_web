document.addEventListener('DOMContentLoaded', function() {
    console.log('🎠 Ініціалізація каруселей проєктів...');
    
    // Ініціалізація Lucide іконок
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
        console.log('✅ Lucide іконки ініціалізовано');
    } else {
        console.warn('⚠️ Lucide не завантажено');
    }
    
    // Ініціалізація каруселей
    const carousels = document.querySelectorAll('.projects-carousel-wrapper');
    console.log(`📋 Знайдено каруселей: ${carousels.length}`);
    
    carousels.forEach((carousel, index) => {
        const track = carousel.querySelector('.projects-carousel-track');
        const items = carousel.querySelectorAll('.carousel-project-item');
        const carouselId = carousel.id;
        
        console.log(`🎯 Карусель ${index + 1}: ID=${carouselId}, елементів=${items.length}`);
        
        if (!track || items.length === 0) return;
        
        let currentIndex = 0;
        const totalItems = items.length;
        
        // Отримуємо навігацію
        const prevBtn = document.querySelector(`.carousel-nav-btn[data-carousel="${carouselId}"][data-direction="prev"]`);
        const nextBtn = document.querySelector(`.carousel-nav-btn[data-carousel="${carouselId}"][data-direction="next"]`);
        const indicators = document.querySelectorAll(`.indicator[data-carousel="${carouselId}"]`);
        
        console.log(`🔘 Кнопки: prev=${!!prevBtn}, next=${!!nextBtn}, indicators=${indicators.length}`);
        
        // Функція розрахунку ширини
        function getItemWidth() {
            if (items.length === 0) return 340;
            const itemStyle = window.getComputedStyle(items[0]);
            const itemWidth = items[0].offsetWidth;
            const gap = parseFloat(itemStyle.marginRight) || 24;
            return itemWidth + gap;
        }
        
        // Функція видимих елементів
        function getVisibleItems() {
            const containerWidth = carousel.offsetWidth;
            const itemWidth = getItemWidth();
            return Math.max(1, Math.floor(containerWidth / itemWidth));
        }
        
        // Оновлення каруселі
        function updateCarousel() {
            const itemWidth = getItemWidth();
            const translateX = -(currentIndex * itemWidth);
            track.style.transform = `translateX(${translateX}px)`;
            
            // Оновлення кнопок
            const visibleItems = getVisibleItems();
            const maxIndex = Math.max(0, totalItems - visibleItems);
            
            if (prevBtn) {
                prevBtn.disabled = currentIndex === 0;
            }
            if (nextBtn) {
                nextBtn.disabled = currentIndex >= maxIndex;
            }
            
            // Оновлення індикаторів
            indicators.forEach((indicator, index) => {
                indicator.classList.toggle('active', index === currentIndex);
            });
            
            console.log(`📊 Позиція: ${currentIndex}/${maxIndex}, видимих: ${visibleItems}`);
        }
        
        // Попередня картка
        if (prevBtn) {
            prevBtn.addEventListener('click', () => {
                console.log('👈 Попередня картка');
                if (currentIndex > 0) {
                    currentIndex--;
                    updateCarousel();
                }
            });
        }
        
        // Наступна картка
        if (nextBtn) {
            nextBtn.addEventListener('click', () => {
                console.log('👉 Наступна картка');
                const visibleItems = getVisibleItems();
                const maxIndex = Math.max(0, totalItems - visibleItems);
                if (currentIndex < maxIndex) {
                    currentIndex++;
                    updateCarousel();
                }
            });
        }
        
        // Індикатори
        indicators.forEach((indicator, index) => {
            indicator.addEventListener('click', () => {
                console.log(`🎯 Перехід до індикатора ${index}`);
                currentIndex = index;
                updateCarousel();
            });
        });
        
        // Touch/Swipe події
        let startX = 0;
        let isDragging = false;
        
        track.addEventListener('touchstart', (e) => {
            startX = e.touches[0].clientX;
            isDragging = true;
            console.log('👆 Touch start');
        });
        
        track.addEventListener('touchend', (e) => {
            if (!isDragging) return;
            
            const endX = e.changedTouches[0].clientX;
            const diff = startX - endX;
            const threshold = 50;
            
            console.log(`👆 Touch end: diff=${diff}`);
            
            if (Math.abs(diff) > threshold) {
                if (diff > 0 && nextBtn && !nextBtn.disabled) {
                    nextBtn.click();
                } else if (diff < 0 && prevBtn && !prevBtn.disabled) {
                    prevBtn.click();
                }
            }
            
            isDragging = false;
        });
        
        // Resize обробка
        window.addEventListener('resize', () => {
            console.log('📐 Resize карусель');
            updateCarousel();
        });
        
        // Ініціалізація
        updateCarousel();
        console.log(`✅ Карусель ${index + 1} ініціалізовано`);
    });
});