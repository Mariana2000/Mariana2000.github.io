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
    document.documentElement.setAttribute("data-theme", theme);
    var meta = document.querySelector('meta[name="theme-color"]');
    if (meta) {
      meta.setAttribute("content", isDark(theme) ? "#1a1a1a" : "#ffffff");
    }
  }

  function toggleTheme() {
    var current = getTheme();
    var next = isDark(current) ? "light" : "dark";
    localStorage.setItem(STORAGE_KEY, next);
    applyTheme(next);
  }

  applyTheme(getTheme());

  document.addEventListener("DOMContentLoaded", function () {
    var button = document.getElementById("theme-toggle");
    if (button) {
      button.addEventListener("click", toggleTheme);
    }
  });

  window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", function () {
    if (getTheme() === "auto") {
      applyTheme("auto");
    }
  });
})();
