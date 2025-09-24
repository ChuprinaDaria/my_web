document.addEventListener('DOMContentLoaded', function() {
  if (typeof lucide !== 'undefined') {
    lucide.createIcons();
  }
  const ctaButtons = document.querySelectorAll('.sidebar-cta-button:not([onclick])');
  ctaButtons.forEach(button => {
    button.addEventListener('click', function(e) {
      e.preventDefault();
      const projectTitle = this.dataset.projectTitle || 'Custom Project Development';
      scrollToContact(projectTitle);
    });
  });
  const projectItems = document.querySelectorAll('.project-item');
  projectItems.forEach(item => {
    item.addEventListener('click', function(e) {});
  });
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

function scrollToContact(projectTitle) {
  const contactSection = document.querySelector('#contact') || document.querySelector('.contact-form') || document.querySelector('[id*="contact"]');
  if (contactSection) {
    contactSection.scrollIntoView({
      behavior: 'smooth',
      block: 'start'
    });
    setTimeout(() => {
      const messageField = document.querySelector('textarea[name="message"]');
      if (messageField && projectTitle) {
        const currentLang = document.documentElement.lang || 'uk';
        const messages = {
          'uk': `Привіт!Мене цікавить проєкт "${projectTitle}". Хочу обговорити можливості співпраці.`,
          'en': `Hi!I'm interested in the "${projectTitle}" project. I'd like to discuss collaboration opportunities.`,
          'pl': `Cześć!Interesuje mnie projekt "${projectTitle}". Chciałbym omówić możliwości współpracy.`
        };
        messageField.value = messages[currentLang] || messages['uk'];
        messageField.focus();
      }
    }, 1000);
  } else {
    const currentLang = document.documentElement.lang || 'uk';
    window.location.href = `/${currentLang}/contacts/`;
  }
}

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
    rootMargin: '0px 0px-50px 0px'
  });
  sidebarElements.forEach((element, index) => {
    element.style.opacity = '0';
    element.style.transform = 'translateY(20px)';
    element.style.transition = `opacity 0.6s ease ${index*0.1}s,transform 0.6s ease ${index*0.1}s`;
    observer.observe(element);
  });
}

document.addEventListener('DOMContentLoaded', animateSidebarElements);