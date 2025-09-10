class ModernServicesCarousel {
  constructor(element, options = {}) {
    this.element = element;
    this.track = element.querySelector('.carousel-track');
    this.slides = Array.from(element.querySelectorAll('.carousel-slide'));
    
    this.prevBtns = Array.from(element.querySelectorAll('.nav-prev'));
    this.nextBtns = Array.from(element.querySelectorAll('.nav-next'));
    
    
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
    
    this.init();
  }
  
  init() {
    if (this.slides.length === 0) return;
    
    this.bindEvents();
    this.updateUI();
    this.observeSlides();
    
    this.setupAccessibility();
  }
  
  
  bindEvents() {
    this.prevBtns.forEach(btn => {
      btn.addEventListener('click', () => this.previousSlide());
    });
    
    this.nextBtns.forEach(btn => {
      btn.addEventListener('click', () => this.nextSlide());
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
  
  handleTouchStart(e) {
    this.touchStartX = e.changedTouches[0].screenX;
  }
  
  handleTouchEnd(e) {
    this.touchEndX = e.changedTouches[0].screenX;
    this.handleSwipe();
  }
  
  handleSwipe() {
    const swipeThreshold = 50;
    const diff = this.touchStartX - this.touchEndX;
    
    if (Math.abs(diff) > swipeThreshold) {
      if (diff > 0) {
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
    
    const slideWidth = this.slides[0]?.offsetWidth + 32;
    const newIndex = Math.round(this.track.scrollLeft / slideWidth);
    
    if (newIndex !== this.currentIndex) {
      this.currentIndex = newIndex;
    }
  }
  
  previousSlide() {
    const slideWidth = this.getSlideWidth();
    const currentScroll = this.track.scrollLeft;
    const newScrollPosition = Math.max(0, currentScroll - slideWidth);
    
    this.track.scrollTo({
      left: newScrollPosition,
      behavior: 'smooth'
    });
  }
  
  nextSlide() {
    const slideWidth = this.getSlideWidth();
    const currentScroll = this.track.scrollLeft;
    const maxScroll = this.track.scrollWidth - this.track.clientWidth;
    const newScrollPosition = Math.min(maxScroll, currentScroll + slideWidth);
    
    this.track.scrollTo({
      left: newScrollPosition,
      behavior: 'smooth'
    });
  }
  
  getSlideWidth() {
    if (this.slides.length === 0) return 300;
    
    const slide = this.slides[0];
    const computedStyle = window.getComputedStyle(slide);
    const slideWidth = slide.offsetWidth;
    const gap = parseInt(window.getComputedStyle(this.track).gap) || 32;
    
    return slideWidth + gap;
  }
  
  goToSlide(index) {
    if (this.isTransitioning) return;
    
    this.currentIndex = Math.max(0, Math.min(index, this.slides.length - 1));
    
    const slideWidth = this.slides[0]?.offsetWidth + 32;
    const scrollPosition = this.currentIndex * slideWidth;
    
    this.isTransitioning = true;
    
    this.track.scrollTo({
      left: scrollPosition,
      behavior: 'smooth'
    });
    
    setTimeout(() => {
      this.isTransitioning = false;
      this.updateUI();
    }, 300);
  }
  
  updateSlidesToShow() {
    const containerWidth = this.element.offsetWidth;
    
    if (containerWidth < 600) {
      this.options.slidesToShow = 1;
    } else if (containerWidth < 900) {
      this.options.slidesToShow = 2;
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
      btn.style.opacity = canScrollLeft ? '1' : '0';
    });
    
    this.nextBtns.forEach(btn => {
      btn.disabled = !canScrollRight;
      btn.style.opacity = canScrollRight ? '1' : '0';
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
      slide.setAttribute('aria-label', `Slide ${index + 1} of ${this.slides.length}`);
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
  const carousels = document.querySelectorAll('.services-carousel');
  
  carousels.forEach(carousel => {
    new ModernServicesCarousel(carousel, {
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

window.ModernServicesCarousel = ModernServicesCarousel;
