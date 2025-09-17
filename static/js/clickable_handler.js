// ===============================================
// 🖱️ УНІВЕРСАЛЬНИЙ ОБРОБНИК КЛІКІВ
// ===============================================

document.addEventListener('DOMContentLoaded', function() {
    // Обробник для всіх елементів з класом clickable
    const clickableElements = document.querySelectorAll('.clickable[data-href]');
    
    clickableElements.forEach(element => {
        element.addEventListener('click', function(e) {
            // Перевіряємо, чи клік не на кнопці або посиланні
            if (e.target.closest('button, a, input, select, textarea')) {
                return; // Дозволяємо стандартну поведінку
            }
            
            const href = this.getAttribute('data-href');
            if (href) {
                // Перевіряємо, чи це зовнішнє посилання
                if (href.startsWith('http://') || href.startsWith('https://')) {
                    window.open(href, '_blank', 'noopener,noreferrer');
                } else {
                    // Внутрішнє посилання
                    window.location.href = href;
                }
            }
        });
        
        // Додаємо курсор pointer
        element.style.cursor = 'pointer';
    });
    
    console.log(`✅ Clickable handler initialized for ${clickableElements.length} elements`);
});
