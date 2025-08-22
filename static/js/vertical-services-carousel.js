// 🎠 VERTICAL SERVICES CAROUSEL - Standalone version
(function() {
  'use strict';

  function initVerticalCarousel() {
    const carousels = document.querySelectorAll('.services-carousel-vertical');

    carousels.forEach(carousel => {
      const track = carousel.querySelector('.services-track');
      const items = Array.from(carousel.querySelectorAll('.service-item'));
      const upBtn = carousel.closest('.services-preview')?.querySelector('.control-up');
      const downBtn = carousel.closest('.services-preview')?.querySelector('.control-down');
      const indicators = Array.from(carousel.closest('.services-preview')?.querySelectorAll('.indicator') || []);

      if (!track || items.length === 0) return;

      let currentIndex = 0;
      const visibleItems = 3;
      const maxIndex = Math.max(0, items.length - visibleItems);

      function getItemHeight() {
        if (items.length === 0) return 0;
        
        const firstItem = items[0];
        const computedStyle = getComputedStyle(track);
        const gap = parseInt(computedStyle.gap || 0);
        
        return firstItem.offsetHeight + gap;
      }

      function updateCarousel() {
        const itemHeight = getItemHeight();
        const offset = currentIndex * itemHeight;
        
        track.style.transform = 'translateY(-' + offset + 'px)';

        indicators.forEach(function(indicator, index) {
          const isActive = index === currentIndex;
          indicator.classList.toggle('active', isActive);
          indicator.setAttribute('aria-selected', isActive ? 'true' : 'false');
        });

        if (upBtn) {
          upBtn.disabled = currentIndex === 0;
          upBtn.classList.toggle('disabled', currentIndex === 0);
        }
        
        if (downBtn) {
          downBtn.disabled = currentIndex >= maxIndex;
          downBtn.classList.toggle('disabled', currentIndex >= maxIndex);
        }

        carousel.setAttribute('aria-live', 'polite');
      }

      // UP button
      if (upBtn) {
        upBtn.addEventListener('click', function() {
          if (currentIndex > 0) {
            currentIndex--;
            updateCarousel();
          }
        });
      }

      // DOWN button  
      if (downBtn) {
        downBtn.addEventListener('click', function() {
          if (currentIndex < maxIndex) {
            currentIndex++;
            updateCarousel();
          }
        });
      }

      // Indicators
      indicators.forEach(function(indicator, index) {
        indicator.addEventListener('click', function() {
          const targetIndex = Math.min(index, maxIndex);
          currentIndex = targetIndex;
          updateCarousel();
        });
      });

      // Keyboard navigation
      carousel.addEventListener('keydown', function(e) {
        switch(e.key) {
          case 'ArrowUp':
            e.preventDefault();
            if (currentIndex > 0) {
              currentIndex--;
              updateCarousel();
            }
            break;
          case 'ArrowDown':
            e.preventDefault();
            if (currentIndex < maxIndex) {
              currentIndex++;
              updateCarousel();
            }
            break;
          case 'Home':
            e.preventDefault();
            currentIndex = 0;
            updateCarousel();
            break;
          case 'End':
            e.preventDefault();
            currentIndex = maxIndex;
            updateCarousel();
            break;
        }
      });

      // Touch support
      let startY = 0;
      let currentY = 0;
      let isDragging = false;

      track.addEventListener('touchstart', function(e) {
        startY = e.touches[0].clientY;
        isDragging = true;
      });

      track.addEventListener('touchmove', function(e) {
        if (!isDragging) return;
        currentY = e.touches[0].clientY;
        e.preventDefault();
      });

      track.addEventListener('touchend', function() {
        if (!isDragging) return;
        isDragging = false;
        
        const diff = startY - currentY;
        const threshold = 50;
        
        if (Math.abs(diff) > threshold) {
          if (diff > 0 && currentIndex < maxIndex) {
            currentIndex++;
          } else if (diff < 0 && currentIndex > 0) {
            currentIndex--;
          }
          updateCarousel();
        }
      });

      // Resize handler
      let resizeTimeout;
      window.addEventListener('resize', function() {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(updateCarousel, 150);
      });

      // Initial setup
      updateCarousel();

      console.log('🎠 Vertical carousel initialized with ' + items.length + ' items');
    });
  }

  // Global function
  window.initVerticalServicesCarousel = function(carouselId, config) {
    config = config || {};
    console.log('🎠 Global init called for: ' + carouselId, config);
    initVerticalCarousel();
  };

  // Auto-init on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initVerticalCarousel);
  } else {
    initVerticalCarousel();
  }

})();