document.addEventListener("DOMContentLoaded", function() {
  document.querySelectorAll(".star-rating").forEach(star => {
    const ratingElem = star.querySelector("strong.rating");
    const span = star.querySelector("span");
    if(ratingElem && span) {
      const ratingValue = parseFloat(ratingElem.textContent);
      if(!isNaN(ratingValue)) {
        span.style.width = ((ratingValue / 5) * 100).toFixed(2) + "%";
      }
    }
  });
});
