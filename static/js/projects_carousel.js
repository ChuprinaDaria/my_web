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
      track.style.transform = `translate3d(${x}px,0,0)`;
      updateButtons();
      updateDots();
    }

    function updateButtons() {
      if (prev) prev.disabled = index <= 0;
      if (next) next.disabled = index >= items.length - visibleCount();
    }

    function buildDots() {
      if (!dotsWrap) return;
      dotsWrap.innerHTML = '';
      const pages = Math.max(1, items.length - visibleCount() + 1);
      for (let i = 0; i < pages; i++) {
        const b = document.createElement('button');
        b.className = 'indicator' + (i === 0 ? ' active' : '');
        b.type = 'button';
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

    // controls
    prev && prev.addEventListener('click', () => { index = clamp(index - 1); update(); });
    next && next.addEventListener('click', () => { index = clamp(index + 1); update(); });

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
    document.querySelectorAll('.projects-carousel-container').forEach(initCarousel);
  });
})();