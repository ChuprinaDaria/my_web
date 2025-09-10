(function () {
  function initCarousel(root) {
    const track = root.querySelector('.projects-carousel-track');
    const items = [...root.querySelectorAll('.carousel-project-item')];
    const wrapper = root.querySelector('.projects-carousel-wrapper') || root;
    const prev = root.querySelector('.carousel-nav-btn.prev');
    const next = root.querySelector('.carousel-nav-btn.next');
    const dotsWrap = root.querySelector('.carousel-indicators');

    if (!track || items.length === 0) return;

    const getGap = () => parseFloat(getComputedStyle(track).gap || '24');
    let index = 0;

    const slideW = () => items[0].getBoundingClientRect().width + getGap();
    const visibleCount = () => {
      const w = wrapper.getBoundingClientRect().width;
      return Math.max(1, Math.floor((w + getGap()) / (items[0].getBoundingClientRect().width + getGap())));
    };
    const clamp = (i) => Math.max(0, Math.min(i, items.length - visibleCount()));

    function update() {
      const x = -(index * slideW());
      
      track.style.transition = 'transform 0.5s cubic-bezier(0.25, 0.46, 0.45, 0.94)';
      track.style.transform = `translate3d(${x}px,0,0)`;
      
      updateButtons();
      updateDots();
      
      const currentSlide = index + 1;
      const totalSlides = items.length;
      
      if (track.getAttribute('aria-live')) {
        track.setAttribute('aria-label', `Showing slide ${currentSlide} of ${totalSlides}`);
      }
    }

    function updateButtons() {
      const canScrollLeft = index > 0;
      const maxIndex = Math.max(0, items.length - visibleCount());
      const canScrollRight = index < maxIndex;
      
      const prevBtns = root.querySelectorAll('.carousel-nav-btn.prev');
      prevBtns.forEach(btn => {
        btn.disabled = !canScrollLeft;
        if (window.innerWidth > 768) {
          btn.style.opacity = canScrollLeft ? '1' : '0';
        } else {
          btn.style.opacity = canScrollLeft ? '1' : '0.3';
        }
      });
      
      const nextBtns = root.querySelectorAll('.carousel-nav-btn.next');
      nextBtns.forEach(btn => {
        btn.disabled = !canScrollRight;
        if (window.innerWidth > 768) {
          btn.style.opacity = canScrollRight ? '1' : '0';
        } else {
          btn.style.opacity = canScrollRight ? '1' : '0.3';
        }
      });
    }

    function buildDots() {
      if (!dotsWrap) return;
      dotsWrap.innerHTML = '';
      
      const pages = Math.max(1, items.length - visibleCount() + 1);
      
      if (pages <= 1) {
        dotsWrap.style.display = 'none';
        return;
      }
      
      dotsWrap.style.display = 'flex';
      
      for (let i = 0; i < pages; i++) {
        const b = document.createElement('button');
        b.className = 'indicator' + (i === 0 ? ' active' : '');
        b.type = 'button';
        b.setAttribute('aria-label', `Go to slide ${i + 1} of ${pages}`);
        b.addEventListener('click', () => { index = i; update(); });
        dotsWrap.appendChild(b);
      }
    }

    function updateDots() {
      if (!dotsWrap) return;
      [...dotsWrap.querySelectorAll('.indicator')].forEach((d, i) =>
        d.classList.toggle('active', i === index)
      );
    }

    root.querySelectorAll('.carousel-nav-btn.prev').forEach(btn => {
      btn.addEventListener('click', () => { 
        index = clamp(index - 1); 
        update(); 
      });
    });

    root.querySelectorAll('.carousel-nav-btn.next').forEach(btn => {
      btn.addEventListener('click', () => { 
        index = clamp(index + 1); 
        update(); 
      });
    });

    // touch/drag
    let startX = 0, dragging = false, pid = null;
    track.addEventListener('pointerdown', (e) => {
      dragging = true; startX = e.clientX; pid = e.pointerId;
      track.setPointerCapture(pid);
    });
    track.addEventListener('pointerup', (e) => {
      if (!dragging) return;
      const dx = e.clientX - startX;
      if (Math.abs(dx) > 30) index = clamp(index + (dx < 0 ? 1 : -1));
      dragging = false; track.releasePointerCapture(pid); update();
    });

    // wheel (горизонтальний)
    root.addEventListener('wheel', (e) => {
      if (Math.abs(e.deltaX) < Math.abs(e.deltaY)) return;
      e.preventDefault();
      index = clamp(index + (e.deltaX > 0 ? 1 : -1));
      update();
    }, { passive: false });

    // resize
    window.addEventListener('resize', () => { buildDots(); index = clamp(index); update(); });

    // init
    buildDots();
    update();
  }

  document.addEventListener('DOMContentLoaded', () => {
    // Ініціалізація каруселей
    document.querySelectorAll('.projects-carousel-container').forEach(initCarousel);
  });
})();