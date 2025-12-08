document.addEventListener("DOMContentLoaded", function () {
  var forms = document.querySelectorAll(".rating-form");
  forms.forEach(function (form) {
    var starsContainer = form.querySelector(".stars");
    var buttons = form.querySelectorAll(".star-button");
    
    buttons.forEach(function (btn, index) {
      btn.addEventListener("mouseenter", function () {
        highlightStars(starsContainer, index + 1);
      });
      
      btn.addEventListener("click", function (e) {
        e.preventDefault();
        var score = index + 1;
        setActiveStars(starsContainer, score);
        
        var formData = new FormData(form);
        formData.set("score", score);
        
        fetch(form.action, {
          method: "POST",
          body: formData,
          headers: {
            "X-CSRFToken": formData.get("csrfmiddlewaretoken")
          }
        })
        .then(function(response) {
          if (response.ok) {
            return response.json();
          }
          throw new Error("Network response was not ok");
        })
        .then(function(data) {
          if (data.average !== undefined) {
            updateRatingSummary(data.average, data.count);
          }
        })
        .catch(function(error) {
          console.error("Error:", error);
          form.submit();
        });
      });
    });
    
    starsContainer.addEventListener("mouseleave", function () {
      var activeButtons = starsContainer.querySelectorAll(".star-button.active");
      if (activeButtons.length > 0) {
        var lastActive = activeButtons[activeButtons.length - 1];
        var activeIndex = Array.from(buttons).indexOf(lastActive);
        highlightStars(starsContainer, activeIndex + 1);
      } else {
        clearHighlights(starsContainer);
      }
    });
  });
  
  function highlightStars(container, count) {
    var buttons = container.querySelectorAll(".star-button");
    buttons.forEach(function (btn, index) {
      btn.classList.remove("hover-active");
      if (index < count) {
        btn.classList.add("hover-active");
      }
    });
  }
  
  function setActiveStars(container, count) {
    var buttons = container.querySelectorAll(".star-button");
    buttons.forEach(function (btn, index) {
      btn.classList.remove("active", "hover-active");
      if (index < count) {
        btn.classList.add("active");
      }
    });
  }
  
  function clearHighlights(container) {
    var buttons = container.querySelectorAll(".star-button");
    buttons.forEach(function (btn) {
      btn.classList.remove("hover-active");
    });
  }
  
  function updateRatingSummary(average, count) {
    var summary = document.querySelector(".rating-summary");
    if (summary) {
      summary.innerHTML = "★ " + average.toFixed(1) + " (" + count + ")";
    }
  }
});

