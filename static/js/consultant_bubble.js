class ConsultantBubble {
  constructor() {
    this.bubble = null;
    this.isVisible = true;
    this.init();
  }

  init() {
    
    if (document.readyState === 'loading') {
      
      document.addEventListener('DOMContentLoaded', () => this.setupBubble());
    } else {
      
      this.setupBubble();
    }
  }

  setupBubble() {
    
    this.createBubbleHTML();
    
    
    this.addEventListeners();
    
    
    this.initAnimations();
    
  }

  createBubbleHTML() {
    
    const bubbleHTML = `
      <div class="consultant-bubble-container" id="consultant-bubble">
        <div class="pulse-ring"></div>
        <div class="bubble-stage">
          <div class="consultant-bubble">
            <div class="sphere"></div>
            <div class="iridescence"></div>
            <div class="highlight"></div>
            <div class="secondary-highlight"></div>
            <div class="tiny-spark"></div>
            <div class="shadow"></div>
            <div class="bubble-text">RAG<br>CHAT</div>
          </div>
        </div>
      </div>
    `;
    
    
    document.body.insertAdjacentHTML('beforeend', bubbleHTML);
    this.bubble = document.getElementById('consultant-bubble');
    
  }

  addEventListeners() {
    if (!this.bubble) {
      
      return;
    }

    const bubbleElement = this.bubble.querySelector('.consultant-bubble');
    
    if (!bubbleElement) {
      
      return;
    }
    
    
    
    bubbleElement.addEventListener('click', (e) => {
      e.preventDefault();
      
      this.openConsultant();
    });

    
    bubbleElement.addEventListener('mouseenter', () => {
      this.onHoverEnter();
    });

    bubbleElement.addEventListener('mouseleave', () => {
      this.onHoverLeave();
    });

    
    let lastScrollTop = 0;
    window.addEventListener('scroll', () => {
      const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
      
      if (scrollTop > lastScrollTop && scrollTop > 100) {
        
        this.hideBubble();
      } else {
        
        this.showBubble();
      }
      
      lastScrollTop = scrollTop;
    });
  }

  initAnimations() {
    
    if (this.bubble) {
      this.bubble.style.opacity = '0';
      this.bubble.style.transform = 'scale(0.5)';
      
      setTimeout(() => {
        this.bubble.style.transition = 'all 0.5s ease-out';
        this.bubble.style.opacity = '1';
        this.bubble.style.transform = 'scale(1)';
      }, 1000);
    }
  }

  onHoverEnter() {
    const bubbleElement = this.bubble.querySelector('.consultant-bubble');
    if (bubbleElement) {
      bubbleElement.style.transform = 'scale(1.15)';
      bubbleElement.style.filter = 'brightness(1.1) saturate(1.2)';
    }
  }

  onHoverLeave() {
    const bubbleElement = this.bubble.querySelector('.consultant-bubble');
    if (bubbleElement) {
      bubbleElement.style.transform = 'scale(1)';
      bubbleElement.style.filter = 'brightness(1) saturate(1)';
    }
  }

  showBubble() {
    if (this.bubble && !this.isVisible) {
      this.bubble.style.opacity = '1';
      this.bubble.style.transform = 'scale(1)';
      this.bubble.style.pointerEvents = 'auto';
      this.isVisible = true;
    }
  }

  hideBubble() {
    if (this.bubble && this.isVisible) {
      this.bubble.style.opacity = '0.3';
      this.bubble.style.transform = 'scale(0.8)';
      this.bubble.style.pointerEvents = 'none';
      this.isVisible = false;
    }
  }

  openConsultant() {
    
    
    
    if (window.openConsultantModal) {
      
      window.openConsultantModal();
    } else {
      
      
    }
  }

  showConsultantModal() {
    
    const modal = document.createElement('div');
    modal.className = 'consultant-modal';
    modal.style.cssText = `
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: rgba(0, 0, 0, 0.9);
      display: flex;
      justify-content: center;
      align-items: center;
      z-index: 10000;
      backdrop-filter: blur(20px);
      overflow-y: auto;
      padding: 20px;
    `;

    const modalContent = document.createElement('div');
    modalContent.className = 'consultant-modal-content';
    modalContent.style.cssText = `
      background: linear-gradient(135deg, #1a1a1a, #0a0a0a);
      border: 1px solid rgba(158, 255, 0, 0.3);
      border-radius: 20px;
      max-width: 800px;
      width: 100%;
      max-height: 90vh;
      overflow-y: auto;
      box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
      position: relative;
    `;

    modalContent.innerHTML = `
      
      <div class="consultant-modal-header" style="
        padding: 40px 40px 20px 40px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        position: relative;
      ">
        <button class="consultant-modal-close" id="close-modal" style="
          position: absolute;
          top: 20px;
          right: 20px;
          background: rgba(255, 255, 255, 0.1);
          border: none;
          color: #b3adad;
          width: 40px;
          height: 40px;
          border-radius: 50%;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          transition: all 0.3s ease;
          font-size: 18px;
        ">×</button>
        
        <div class="consultant-hero" style="text-align: center;">
          <div class="consultant-avatar" style="
            width: 120px;
            height: 120px;
            margin: 0 auto 20px;
            border-radius: 50%;
            background: linear-gradient(135deg, #9eff00, #66ff00);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 48px;
            box-shadow: 0 0 30px rgba(158, 255, 0, 0.5);
          ">🫧</div>
          
          <h1 style="
            color: antiquewhite;
            margin: 0 0 10px 0;
            font-size: 2.5rem;
            font-weight: 700;
            background: linear-gradient(135deg, #9eff00, #66ff00);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
          ">RAG Консультант</h1>
          
          <p style="
            color: #b3adad;
            font-size: 1.2rem;
            margin: 0 0 30px 0;
            line-height: 1.6;
          ">Штучний інтелект для консультацій та допомоги</p>
          
          
          <div class="consultant-tags" style="
            display: flex;
            justify-content: center;
            flex-wrap: wrap;
            gap: 12px;
            margin-bottom: 30px;
          ">
            <span style="
              padding: 8px 16px;
              background: rgba(158, 255, 0, 0.1);
              border: 1px solid rgba(158, 255, 0, 0.3);
              border-radius: 20px;
              color: #9eff00;
              font-size: 14px;
              font-weight: 600;
            ">AI Консультант</span>
            <span style="
              padding: 8px 16px;
              background: rgba(255, 0, 107, 0.1);
              border: 1px solid rgba(255, 0, 107, 0.3);
              border-radius: 20px;
              color: #ff006b;
              font-size: 14px;
              font-weight: 600;
            ">RAG Система</span>
            <span style="
              padding: 8px 16px;
              background: rgba(147, 51, 234, 0.1);
              border: 1px solid rgba(147, 51, 234, 0.3);
              border-radius: 20px;
              color: #9333ea;
              font-size: 14px;
              font-weight: 600;
            ">24/7 Доступ</span>
          </div>
        </div>
      </div>

      
      <div class="consultant-modal-body" style="padding: 40px;">
        <div class="consultant-bio" style="
          background: rgba(255, 255, 255, 0.05);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 16px;
          padding: 30px;
          margin-bottom: 30px;
        ">
          <h3 style="
            color: antiquewhite;
            margin: 0 0 20px 0;
            font-size: 1.5rem;
            display: flex;
            align-items: center;
            gap: 12px;
          ">
            <span style="
              background: #9eff00;
              color: #000;
              width: 40px;
              height: 40px;
              border-radius: 8px;
              display: flex;
              align-items: center;
              justify-content: center;
              font-size: 18px;
            ">🤖</span>
            Про мене
          </h3>
          <p style="
            color: #b3adad;
            line-height: 1.7;
            margin: 0 0 20px 0;
            font-size: 1.1rem;
          ">
            Привіт! Я RAG (Retrieval-Augmented Generation) консультант - це означає, що я поєдную 
            можливості генеративного ШІ з доступом до актуальної бази знань. Я можу допомогти вам 
            з різними питаннями, надати консультації та відповісти на складні запити.
          </p>
          <p style="
            color: #b3adad;
            line-height: 1.7;
            margin: 0;
            font-size: 1.1rem;
          ">
            Моя особливість - це здатність поєднувати творчість з точністю, використовуючи 
            найсучасніші технології машинного навчання для надання якісних консультацій.
          </p>
        </div>

        <div class="consultant-features" style="
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
          gap: 20px;
          margin-bottom: 30px;
        ">
          <div class="feature-card" style="
            background: rgba(158, 255, 0, 0.05);
            border: 1px solid rgba(158, 255, 0, 0.2);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
          ">
            <div style="
              font-size: 2rem;
              margin-bottom: 12px;
            ">💬</div>
            <h4 style="
              color: #9eff00;
              margin: 0 0 8px 0;
              font-size: 1.1rem;
            ">Інтерактивний чат</h4>
            <p style="
              color: #b3adad;
              font-size: 0.9rem;
              margin: 0;
              line-height: 1.5;
            ">Живе спілкування з ШІ консультантом</p>
          </div>
          
          <div class="feature-card" style="
            background: rgba(255, 0, 107, 0.05);
            border: 1px solid rgba(255, 0, 107, 0.2);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
          ">
            <div style="
              font-size: 2rem;
              margin-bottom: 12px;
            ">🧠</div>
            <h4 style="
              color: #ff006b;
              margin: 0 0 8px 0;
              font-size: 1.1rem;
            ">Розумні відповіді</h4>
            <p style="
              color: #b3adad;
              font-size: 0.9rem;
              margin: 0;
              line-height: 1.5;
            ">Точні та релевантні консультації</p>
          </div>
          
          <div class="feature-card" style="
            background: rgba(147, 51, 234, 0.05);
            border: 1px solid rgba(147, 51, 234, 0.2);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
          ">
            <div style="
              font-size: 2rem;
              margin-bottom: 12px;
            ">⚡</div>
            <h4 style="
              color: #9333ea;
              margin: 0 0 8px 0;
              font-size: 1.1rem;
            ">Швидкість</h4>
            <p style="
              color: #b3adad;
              font-size: 0.9rem;
              margin: 0;
              line-height: 1.5;
            ">Миттєві відповіді на ваші запити</p>
          </div>
        </div>

        
        <div class="consultant-actions" style="
          display: flex;
          gap: 20px;
          justify-content: center;
          flex-wrap: wrap;
        ">
          <button id="start-chat" style="
            background: linear-gradient(135deg, #9eff00, #66ff00);
            color: #000;
            border: none;
            padding: 16px 32px;
            border-radius: 50px;
            font-weight: 700;
            font-size: 16px;
            cursor: pointer;
            transition: all 0.3s ease;
            min-width: 200px;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
          ">🚀 Почати чат</button>
          
          <button id="learn-more" style="
            background: rgba(255, 255, 255, 0.1);
            color: #b3adad;
            border: 1px solid rgba(255, 255, 255, 0.2);
            padding: 16px 32px;
            border-radius: 50px;
            font-weight: 600;
            font-size: 16px;
            cursor: pointer;
            transition: all 0.3s ease;
            min-width: 200px;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
          ">📚 Дізнатися більше</button>
        </div>
      </div>
    `;

    modal.appendChild(modalContent);
    document.body.appendChild(modal);

    
    modal.querySelector('#start-chat').addEventListener('click', () => {
      this.startChat();
      document.body.removeChild(modal);
    });

    modal.querySelector('#learn-more').addEventListener('click', () => {
      this.showLearnMore();
    });

    modal.querySelector('#close-modal').addEventListener('click', () => {
      document.body.removeChild(modal);
    });

    
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        document.body.removeChild(modal);
      }
    });

    
    const startChatBtn = modal.querySelector('#start-chat');
    const learnMoreBtn = modal.querySelector('#learn-more');
    const closeBtn = modal.querySelector('#close-modal');

    startChatBtn.addEventListener('mouseenter', () => {
      startChatBtn.style.transform = 'translateY(-2px) scale(1.05)';
      startChatBtn.style.boxShadow = '0 8px 32px rgba(158, 255, 0, 0.5)';
    });

    startChatBtn.addEventListener('mouseleave', () => {
      startChatBtn.style.transform = 'translateY(0) scale(1)';
      startChatBtn.style.boxShadow = 'none';
    });

    learnMoreBtn.addEventListener('mouseenter', () => {
      learnMoreBtn.style.background = 'rgba(255, 255, 255, 0.15)';
      learnMoreBtn.style.borderColor = '#9eff00';
      learnMoreBtn.style.color = '#9eff00';
      learnMoreBtn.style.transform = 'translateY(-2px)';
    });

    learnMoreBtn.addEventListener('mouseleave', () => {
      learnMoreBtn.style.background = 'rgba(255, 255, 255, 0.1)';
      learnMoreBtn.style.borderColor = 'rgba(255, 255, 255, 0.2)';
      learnMoreBtn.style.color = '#b3adad';
      learnMoreBtn.style.transform = 'translateY(0)';
    });

    closeBtn.addEventListener('mouseenter', () => {
      closeBtn.style.background = 'rgba(255, 255, 255, 0.2)';
      closeBtn.style.transform = 'scale(1.1)';
    });

    closeBtn.addEventListener('mouseleave', () => {
      closeBtn.style.background = 'rgba(255, 255, 255, 0.1)';
      closeBtn.style.transform = 'scale(1)';
    });

    
    modal.style.opacity = '0';
    modalContent.style.transform = 'scale(0.8) translateY(50px)';
    
    setTimeout(() => {
      modal.style.transition = 'opacity 0.4s ease';
      modalContent.style.transition = 'transform 0.4s ease';
      modal.style.opacity = '1';
      modalContent.style.transform = 'scale(1) translateY(0)';
    }, 10);
  }

  showLearnMore() {
    alert('📚 Дізнайтеся більше про RAG консультанта!\n\n' +
          'RAG (Retrieval-Augmented Generation) - це технологія, яка поєднує:\n' +
          '• Генеративні можливості ШІ\n' +
          '• Доступ до актуальної бази знань\n' +
          '• Точність та релевантність відповідей\n\n' +
          'Скоро тут буде детальна інформація!');
  }

  startChat() {
    
    if (typeof openConsultantModal === 'function') {
      openConsultantModal();
    } else {
      
      window.open('/consultant/', '_blank');
    }
  }

  
  toggle() {
    if (this.isVisible) {
      this.hideBubble();
    } else {
      this.showBubble();
    }
  }

  destroy() {
    if (this.bubble) {
      this.bubble.remove();
      this.bubble = null;
    }
  }
}

document.addEventListener('DOMContentLoaded', function() {
  
  const consultantBubble = new ConsultantBubble();
  
  
  window.ConsultantBubble = ConsultantBubble;
  window.consultantBubble = consultantBubble;
  
  
  const bubbleElement = document.getElementById('consultant-bubble');
  
});
