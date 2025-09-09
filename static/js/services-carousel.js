(function () {
  function initVerticalServicesCarousel(containerId, opts = {}) {
    const container = document.getElementById(`services-vertical-${containerId}`) 
                   || document.querySelector('.services-carousel-vertical');
    if (!container) return;

    const track = container.querySelector('.services-track');
    const items = [...track.querySelectorAll('.service-item')];
    if (!items.length) return;

    const visible = opts.visibleItems || 3;

    function cardStep() {
      const first = items[0];
      const style = window.getComputedStyle(first);
      const mb = parseFloat(style.marginBottom) || 0;
      return Math.ceil(first.getBoundingClientRect().height + mb);
    }

    function scrollByStep(dir = 1) {
      const step = cardStep();
      container.scrollBy({ top: dir * step, left: 0, behavior: 'smooth' });
    }

    document.querySelectorAll('.control-up').forEach(btn => {
      btn.addEventListener('click', () => scrollByStep(-1), { passive: true });
    });
    document.querySelectorAll('.control-down').forEach(btn => {
      btn.addEventListener('click', () => scrollByStep(1), { passive: true });
    });

    let startY = null;
    container.addEventListener('touchstart', e => { startY = e.touches[0].clientY; }, { passive: true });
    container.addEventListener('touchmove', () => {}, { passive: true });
    container.addEventListener('touchend', e => { startY = null; }, { passive: true });
  }

  window.initVerticalServicesCarousel = initVerticalServicesCarousel;
})();
