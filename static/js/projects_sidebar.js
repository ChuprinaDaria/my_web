document.addEventListener('DOMContentLoaded', function() {
  const tagChips = document.querySelectorAll('.tag-chip[data-color]');
  tagChips.forEach(chip => {
    const color = chip.getAttribute('data-color');
    if (color) {
      chip.style.setProperty('--tag-color', color);
      chip.style.backgroundColor = color + '20';
      chip.style.color = color;
      chip.style.borderColor = color + '40';
    }
  });

  const filterChips = document.querySelectorAll('.filter-chip');
  filterChips.forEach(chip => {
    chip.addEventListener('click', function() {
      const filterType = this.closest('.filter-group');
      
      filterType.querySelectorAll('.filter-chip').forEach(sibling => {
        sibling.classList.remove('active');
      });
      
      this.classList.add('active');
      
      const filterValue = this.getAttribute('data-filter');
      applyProjectFilter(filterValue);
    });
  });

  const ctaButton = document.querySelector('.sidebar-cta-button:not([onclick])');
  if (ctaButton) {
    ctaButton.addEventListener('click', function() {
      const projectTitle = this.getAttribute('data-project-title');
      scrollToContact(projectTitle);
    });
  }
});

function applyProjectFilter(filterValue) {
  const projectCards = document.querySelectorAll('.project-card');
  
  projectCards.forEach(card => {
    if (filterValue === 'all') {
      card.style.display = 'block';
    } else if (filterValue === 'completed') {
      card.style.display = card.classList.contains('status-completed') ? 'block' : 'none';
    } else if (filterValue === 'ongoing') {
      card.style.display = card.classList.contains('status-ongoing') ? 'block' : 'none';
    } else if (filterValue.startsWith('tech-')) {
      const techSlug = filterValue.replace('tech-', '');
      card.style.display = card.dataset.technology === techSlug ? 'block' : 'none';
    }
  });
}

function scrollToContact(projectTitle) {
  const contactSection = document.querySelector('#contact');
  if (contactSection) {
    contactSection.scrollIntoView({ behavior: 'smooth' });
    
    const projectInput = document.querySelector('input[name="project_interest"]');
    if (projectInput) {
      projectInput.value = projectTitle;
    }
  }
}
