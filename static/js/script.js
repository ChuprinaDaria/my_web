document.addEventListener("DOMContentLoaded", () => {
  const currentLang = document.body.dataset.currentLang || "en";

  document.querySelectorAll("[data-lang]").forEach(el => {
    if (el.dataset.lang === currentLang) {
      el.style.display = "block";
    } else {
      el.style.display = "none";
    }
  });
});
