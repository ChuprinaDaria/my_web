// Simple hover animation enhancer for .service-card and .project-card
(function(){
  function addHoverEffects(selector){
    document.querySelectorAll(selector).forEach(function(card){
      card.addEventListener('mouseenter', function(){
        card.classList.add('hover');
      });
      card.addEventListener('mouseleave', function(){
        card.classList.remove('hover');
      });
    });
  }
  document.addEventListener('DOMContentLoaded', function(){
    addHoverEffects('.service-card');
    addHoverEffects('.project-card');
  });
})();


