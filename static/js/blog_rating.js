document.addEventListener("DOMContentLoaded", function () {
  var forms = document.querySelectorAll(".rating-form");
  forms.forEach(function (form) {
    var buttons = form.querySelectorAll(".star-button");
    buttons.forEach(function (btn) {
      btn.addEventListener("click", function () {
        btn.classList.add("active");
      });
    });
  });
});


