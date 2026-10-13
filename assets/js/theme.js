(function () {
  var STORAGE_KEY = "site-theme";

  function getTheme() {
    var stored = localStorage.getItem(STORAGE_KEY);
    return stored === "light" || stored === "dark" ? stored : "auto";
  }

  function isDark(theme) {
    if (theme === "dark") return true;
    if (theme === "light") return false;
    return window.matchMedia("(prefers-color-scheme: dark)").matches;
  }

  function applyTheme(theme) {
    var root = document.documentElement;
    root.setAttribute("data-theme", theme);
    root.classList.toggle("theme-is-dark", isDark(theme));

    var meta = document.querySelector('meta[name="theme-color"]');
    if (meta) {
      meta.setAttribute("content", isDark(theme) ? "#1a1a1a" : "#f5f2ea");
    }
  }

  function toggleTheme(event) {
    if (event) event.preventDefault();
    var current = getTheme();
    var next = isDark(current) ? "light" : "dark";
    localStorage.setItem(STORAGE_KEY, next);
    applyTheme(next);
  }

  applyTheme(getTheme());

  document.addEventListener("DOMContentLoaded", function () {
    var toggle = document.getElementById("theme-toggle");
    if (toggle) {
      toggle.addEventListener("click", toggleTheme);
    }

    // The visitor map can increase the sticky footer's height after page load.
    var footer = document.querySelector(".page__footer");
    if (footer && window.ResizeObserver) {
      new ResizeObserver(function () {
        var style = window.getComputedStyle(footer);
        var height = footer.getBoundingClientRect().height;
        height += parseFloat(style.marginTop) || 0;
        height += parseFloat(style.marginBottom) || 0;
        document.body.style.marginBottom = height + "px";
      }).observe(footer);
    }
  });

  window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", function () {
    if (getTheme() === "auto") {
      applyTheme("auto");
    }
  });
})();
