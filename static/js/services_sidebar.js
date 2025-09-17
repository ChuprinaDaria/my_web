// ===============================================
// 🚀 SERVICES SIDEBAR INTERACTIONS
// ===============================================

document.addEventListener('DOMContentLoaded', function() {
  // Initialize Lucide icons
  if (typeof lucide !== 'undefined') {
    lucide.createIcons();
  }
  
  // Handle CTA button clicks (тільки для кнопок без onclick обробника)
  const ctaButtons = document.querySelectorAll('.sidebar-cta-button:not([onclick])');
  ctaButtons.forEach(button => {
    button.addEventListener('click', function(e) {
      e.preventDefault();
      const projectTitle = this.dataset.projectTitle || 'Custom Project Development';
      scrollToContact(projectTitle);
    });
  });
  
  // Handle project item clicks
  const projectItems = document.querySelectorAll('.project-item');
  projectItems.forEach(item => {
    item.addEventListener('click', function(e) {
      // Let the link work normally, no preventDefault needed
      // The href will handle navigation
    });
  });
  
  // Handle FAQ link clicks
  const faqLinks = document.querySelectorAll('a[href="#faq"]');
  faqLinks.forEach(link => {
    link.addEventListener('click', function(e) {
      e.preventDefault();
      const faqSection = document.querySelector('#faq');
      if (faqSection) {
        faqSection.scrollIntoView({ 
          behavior: 'smooth',
          block: 'start'
        });
      }
    });
  });
});

// Scroll to contact function
function scrollToContact(projectTitle) {
  // Try to find contact section on current page
  const contactSection = document.querySelector('#contact') || 
                        document.querySelector('.contact-form') ||
                        document.querySelector('[id*="contact"]');
  
  if (contactSection) {
    contactSection.scrollIntoView({ 
      behavior: 'smooth',
      block: 'start'
    });
    
    // Fill form with project info
    setTimeout(() => {
      const messageField = document.querySelector('textarea[name="message"]');
      if (messageField && projectTitle) {
        const currentLang = document.documentElement.lang || 'uk';
        const messages = {
          'uk': `Привіт! Мене цікавить проєкт "${projectTitle}". Хочу обговорити можливості співпраці.`,
          'en': `Hi! I'm interested in the "${projectTitle}" project. I'd like to discuss collaboration opportunities.`,
          'pl': `Cześć! Interesuje mnie projekt "${projectTitle}". Chciałbym omówić możliwości współpracy.`
        };
        messageField.value = messages[currentLang] || messages['uk'];
        messageField.focus();
      }
    }, 1000);
  } else {
    // Fallback - redirect to contact page
    const currentLang = document.documentElement.lang || 'uk';
    window.location.href = `/${currentLang}/contacts/`;
  }
}

// Smooth animations for sidebar elements
function animateSidebarElements() {
  const sidebarElements = document.querySelectorAll('.sidebar-section');
  
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.style.opacity = '1';
        entry.target.style.transform = 'translateY(0)';
      }
    });
  }, {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
  });
  
  sidebarElements.forEach((element, index) => {
    element.style.opacity = '0';
    element.style.transform = 'translateY(20px)';
    element.style.transition = `opacity 0.6s ease ${index * 0.1}s, transform 0.6s ease ${index * 0.1}s`;
    observer.observe(element);
  });
}

// Initialize animations when DOM is ready
document.addEventListener('DOMContentLoaded', animateSidebarElements);
