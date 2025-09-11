class ModernProjectsCarousel {
  constructor(element, options = {}) {
    this.element = element;
    this.track = element.querySelector('.projects-carousel-track');
    this.slides = Array.from(element.querySelectorAll('.carousel-project-item'));
    
    this.prevBtns = Array.from(element.querySelectorAll('.carousel-nav-btn.prev'));
    this.nextBtns = Array.from(element.querySelectorAll('.carousel-nav-btn.next'));
    
    this.options = {
      slidesToShow: 3,
      slidesToScroll: 1,
      infinite: false,
      autoPlay: false,
      autoPlayDelay: 5000,
      ...options
    };
    
    this.currentIndex = 0;
    this.isTransitioning = false;
    this.touchStartX = 0;
    this.touchEndX = 0;
    this.touchStartY = 0;
    this.touchEndY = 0;
    this.dragging = false;
    
    this.init();
  }
  
  init() {
    if (this.slides.length === 0) return;
    
    this.bindEvents();
    this.updateUI();
    this.observeSlides();
    this.setupAccessibility();
    this.addClickHandlers();
  }
  
  bindEvents() {
    this.prevBtns.forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        this.previousSlide();
      });
    });
    
    this.nextBtns.forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        this.nextSlide();
      });
    });
    
    this.track.addEventListener('touchstart', this.handleTouchStart.bind(this), { passive: true });
    this.track.addEventListener('touchend', this.handleTouchEnd.bind(this), { passive: true });
    
    this.track.addEventListener('keydown', this.handleKeyDown.bind(this));
    
    this.resizeObserver = new ResizeObserver(() => {
      this.updateSlidesToShow();
      this.updateUI();
    });
    this.resizeObserver.observe(this.element);
    
    this.track.addEventListener('scroll', this.handleScroll.bind(this), { passive: true });
  }
  
  addClickHandlers() {
    this.slides.forEach(slide => {
      const projectCard = slide.querySelector('.project-card-home');
      if (!projectCard) return;
      
      if (projectCard.onclick) return;
      
      const href = projectCard.getAttribute('data-href');
      if (href) {
        projectCard.style.cursor = 'pointer';
        projectCard.addEventListener('click', (e) => {
          if (e.target.closest('button, a, .cta-primary, .details-link, .demo-link')) {
            return;
          }
          
          e.preventDefault();
          window.location.href = href;
        });
      }
    });
  }
  
  handleTouchStart(e) {
    const touch = e.changedTouches[0];
    this.touchStartX = touch.clientX;
    this.touchStartY = touch.clientY;
    this.dragging = false;
  }
  
  handleTouchEnd(e) {
    const touch = e.changedTouches[0];
    this.touchEndX = touch.clientX;
    this.touchEndY = touch.clientY;
    this.handleSwipe();
  }
  
  handleSwipe() {
    const swipeThreshold = 50;
    const diffX = this.touchStartX - this.touchEndX;
    const diffY = this.touchStartY - this.touchEndY;
    
    if (Math.abs(diffX) > Math.abs(diffY) + 5 && Math.abs(diffX) > swipeThreshold) {
      if (diffX > 0) {
        this.nextSlide();
      } else {
        this.previousSlide();
      }
    }
  }
  
  handleKeyDown(e) {
    switch (e.key) {
      case 'ArrowLeft':
        e.preventDefault();
        this.previousSlide();
        break;
      case 'ArrowRight':
        e.preventDefault();
        this.nextSlide();
        break;
      case 'Home':
        e.preventDefault();
        this.goToSlide(0);
        break;
      case 'End':
        e.preventDefault();
        this.goToSlide(this.slides.length - 1);
        break;
    }
  }
  
  handleScroll() {
    if (this.isTransitioning) return;
    
    const slideWidth = this.getSlideWidth();
    const newIndex = Math.round(this.track.scrollLeft / slideWidth);
    
    if (newIndex !== this.currentIndex) {
      this.currentIndex = newIndex;
      this.updateUI();
    }
  }
  
  previousSlide() {
    if (this.isTransitioning) return;
    
    const slideWidth = this.getSlideWidth();
    const currentScroll = this.track.scrollLeft;
    const newScrollPosition = Math.max(0, currentScroll - slideWidth);
    
    this.isTransitioning = true;
    
    this.track.scrollTo({
      left: newScrollPosition,
      behavior: 'smooth'
    });
    
    setTimeout(() => {
      this.isTransitioning = false;
      this.updateUI();
    }, 500);
  }
  
  nextSlide() {
    if (this.isTransitioning) return;
    
    const slideWidth = this.getSlideWidth();
    const currentScroll = this.track.scrollLeft;
    const maxScroll = this.track.scrollWidth - this.track.clientWidth;
    const newScrollPosition = Math.min(maxScroll, currentScroll + slideWidth);
    
    this.isTransitioning = true;
    
    this.track.scrollTo({
      left: newScrollPosition,
      behavior: 'smooth'
    });
    
    setTimeout(() => {
      this.isTransitioning = false;
      this.updateUI();
    }, 500);
  }
  
  getSlideWidth() {
    if (this.slides.length === 0) return 340;
    
    const slide = this.slides[0];
    const slideWidth = slide.offsetWidth;
    const gap = parseInt(window.getComputedStyle(this.track).gap) || 24;
    
    return slideWidth + gap;
  }
  
  goToSlide(index) {
    if (this.isTransitioning) return;
    
    this.currentIndex = Math.max(0, Math.min(index, this.slides.length - 1));
    
    const slideWidth = this.getSlideWidth();
    const scrollPosition = this.currentIndex * slideWidth;
    
    this.isTransitioning = true;
    
    this.track.scrollTo({
      left: scrollPosition,
      behavior: 'smooth'
    });
    
    setTimeout(() => {
      this.isTransitioning = false;
      this.updateUI();
    }, 500);
  }
  
  updateSlidesToShow() {
    const containerWidth = this.element.offsetWidth;
    
    if (containerWidth < 600) {
      this.options.slidesToShow = 1;
    } else if (containerWidth < 900) {
      this.options.slidesToShow = 2;
    } else if (containerWidth < 1200) {
      this.options.slidesToShow = 3;
    } else {
      this.options.slidesToShow = 3;
    }
  }
  
  updateUI() {
    this.updateButtons();
    this.updateAriaAttributes();
  }
  
  updateButtons() {
    const canScrollLeft = this.track.scrollLeft > 0;
    
    const canScrollRight = 
      this.track.scrollLeft < (this.track.scrollWidth - this.track.clientWidth - 10);
    
    this.prevBtns.forEach(btn => {
      btn.disabled = !canScrollLeft;
      if (window.innerWidth > 768) {
        btn.style.opacity = canScrollLeft ? '1' : '0';
      } else {
        btn.style.opacity = canScrollLeft ? '1' : '0.3';
      }
    });
    
    this.nextBtns.forEach(btn => {
      btn.disabled = !canScrollRight;
      if (window.innerWidth > 768) {
        btn.style.opacity = canScrollRight ? '1' : '0';
      } else {
        btn.style.opacity = canScrollRight ? '1' : '0.3';
      }
    });
  }
  
  updateAriaAttributes() {
    this.slides.forEach((slide, index) => {
      const isVisible = index >= this.currentIndex && 
                       index < this.currentIndex + this.options.slidesToShow;
      
      slide.setAttribute('aria-hidden', !isVisible ? 'true' : 'false');
    });
    
    this.track.setAttribute('aria-live', 'polite');
  }
  
  setupAccessibility() {
    this.element.setAttribute('role', 'region');
    this.track.setAttribute('role', 'group');
    this.track.setAttribute('tabindex', '0');
    
    this.slides.forEach((slide, index) => {
      slide.setAttribute('role', 'group');
      slide.setAttribute('aria-roledescription', 'slide');
      slide.setAttribute('aria-label', `Project ${index + 1} of ${this.slides.length}`);
    });
  }
  
  observeSlides() {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('slide-visible');
          
          const img = entry.target.querySelector('img[data-src]');
          if (img) {
            img.src = img.dataset.src;
            img.removeAttribute('data-src');
          }
        }
      });
    }, { 
      root: this.track, 
      rootMargin: '50px',
      threshold: 0.1 
    });
    
    this.slides.forEach(slide => observer.observe(slide));
  }
  
  destroy() {
    if (this.resizeObserver) {
      this.resizeObserver.disconnect();
    }
    
    this.prevBtns.forEach(btn => {
      btn.removeEventListener('click', this.previousSlide);
    });
    
    this.nextBtns.forEach(btn => {
      btn.removeEventListener('click', this.nextSlide);
    });
    
    this.track.removeEventListener('touchstart', this.handleTouchStart);
    this.track.removeEventListener('touchend', this.handleTouchEnd);
    this.track.removeEventListener('keydown', this.handleKeyDown);
    this.track.removeEventListener('scroll', this.handleScroll);
  }
}

document.addEventListener('DOMContentLoaded', function() {
  const carousels = document.querySelectorAll('.projects-carousel-container, .projects-carousel-wrapper');
  
  carousels.forEach(carousel => {
    new ModernProjectsCarousel(carousel, {
      slidesToShow: 3,
      slidesToScroll: 1,
      infinite: false,
      autoPlay: false
    });
  });
  
  if (typeof lucide !== 'undefined') {
    lucide.createIcons();
  }
});

(function () {
  function initCarouselNav(container){
    const track = container.querySelector('.projects-carousel-track');
    const prev = container.querySelector('.projects-carousel-nav .prev');
    const next = container.querySelector('.projects-carousel-nav .next');
    if (!track || !prev || !next) return;

    const getStep = () => {
      const item = track.querySelector('.carousel-project-item');
      if (!item) return track.clientWidth * 0.9;
      const rect = item.getBoundingClientRect();
      const gap = parseFloat(getComputedStyle(track).columnGap || getComputedStyle(track).gap || 0) || 0;
      return rect.width + gap;
    };

    const updateButtons = () => {
      const maxScroll = track.scrollWidth - track.clientWidth - 1;
      prev.disabled = track.scrollLeft <= 0;
      next.disabled = track.scrollLeft >= maxScroll;
    };

    prev.addEventListener('click', () => {
      track.scrollBy({ left: -getStep(), behavior: 'smooth' });
      setTimeout(updateButtons, 200);
    });
    next.addEventListener('click', () => {
      track.scrollBy({ left:  getStep(), behavior: 'smooth' });
      setTimeout(updateButtons, 200);
    });

    track.addEventListener('scroll', updateButtons, { passive: true });
    window.addEventListener('resize', () => { updateButtons(); }, { passive: true });

    updateButtons();
  }

  document.addEventListener('DOMContentLoaded', function(){
    document
      .querySelectorAll('.projects-carousel-container, .projects-carousel-wrapper')
      .forEach(initCarouselNav);
  });
})();

(function attachMobileSwipeIntent() {
  const carousels = document.querySelectorAll('.projects-carousel-container, .projects-carousel-wrapper');
  carousels.forEach(c => {
    const track = c.querySelector('.projects-carousel-track');
    if (!track) return;

    let startX = 0, startY = 0, lastX = 0;
    let dragging = false, isHorizontal = false;

    track.addEventListener('touchstart', (e) => {
      if (e.target.closest('a,button')) return;
      const t = e.touches[0];
      startX = lastX = t.clientX;
      startY = t.clientY;
      dragging = true;
      isHorizontal = false;
    }, { passive: true });

    track.addEventListener('touchmove', (e) => {
      if (!dragging) return;
      const t = e.touches[0];
      const dx = t.clientX - startX;
      const dy = t.clientY - startY;

      if (!isHorizontal) {
        if (Math.abs(dx) > Math.abs(dy) + 6) {
          isHorizontal = true;
        } else if (Math.abs(dy) > Math.abs(dx) + 6) {
          dragging = false;
          return;
        } else {
          return;
        }
      }

      e.preventDefault();
      const shift = t.clientX - lastX;
      track.scrollLeft -= shift;
      lastX = t.clientX;
    }, { passive: false });

    ['touchend', 'touchcancel'].forEach(evt =>
      track.addEventListener(evt, () => { dragging = false; }, { passive: true })
    );
  });
})();

window.ModernProjectsCarousel = ModernProjectsCarousel;
