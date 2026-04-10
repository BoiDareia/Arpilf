/**
 * Menu móvel — toggle, acessibilidade e fecho automático.
 * Requisitos: 2.5 (ARIA), 2.6 (sem focus traps), 2.7 (hamburger <768px)
 */
(function () {
  'use strict';

  var toggle = document.getElementById('menu-toggle');
  var menu   = document.getElementById('mobile-menu');
  var iconOpen  = document.getElementById('icon-open');
  var iconClose = document.getElementById('icon-close');

  if (!toggle || !menu) return;

  function isOpen() {
    return toggle.getAttribute('aria-expanded') === 'true';
  }

  function openMenu() {
    toggle.setAttribute('aria-expanded', 'true');
    menu.classList.remove('hidden');
    if (iconOpen)  iconOpen.classList.add('hidden');
    if (iconClose) iconClose.classList.remove('hidden');
  }

  function closeMenu() {
    toggle.setAttribute('aria-expanded', 'false');
    menu.classList.add('hidden');
    if (iconOpen)  iconOpen.classList.remove('hidden');
    if (iconClose) iconClose.classList.add('hidden');
  }

  // Toggle on button click
  toggle.addEventListener('click', function () {
    if (isOpen()) {
      closeMenu();
    } else {
      openMenu();
    }
  });

  // Close on click outside the nav
  document.addEventListener('click', function (e) {
    if (isOpen() && !toggle.contains(e.target) && !menu.contains(e.target)) {
      closeMenu();
    }
  });

  // Close on Escape key — no focus trap (req 2.6)
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && isOpen()) {
      closeMenu();
      toggle.focus();
    }
  });
})();
