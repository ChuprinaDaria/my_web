document.addEventListener('DOMContentLoaded', function() {
    const clickableElements = document.querySelectorAll('.clickable[data-href]');
    
    clickableElements.forEach(element => {
        element.addEventListener('click', function(e) {
            if (e.target.closest('button, a, input, select, textarea')) {
                return; 
            }
            
            const href = this.getAttribute('data-href');
            if (href) {
                if (href.startsWith('http://') || href.startsWith('https://')) {
                    window.open(href, '_blank', 'noopener,noreferrer');
                } else {
                    window.location.href = href;
                }
            }
        });
        
        element.style.cursor = 'pointer';
    });
    
});
