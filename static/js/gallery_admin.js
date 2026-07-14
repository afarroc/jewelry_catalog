/* gallery_admin.js — comportamiento del navbar del admin de galería.
 * Vanilla JS, sin dependencias (prohibido Bootstrap).
 * Accesibilidad: aria-expanded sincronizado, cierre con click-outside y Escape.
 */
(function () {
  'use strict';

  var trigger = document.getElementById('adminUserTrigger');
  var menu = document.getElementById('adminUserMenu');
  if (!trigger || !menu) return;

  function open() {
    menu.hidden = false;
    trigger.setAttribute('aria-expanded', 'true');
  }

  function close() {
    menu.hidden = true;
    trigger.setAttribute('aria-expanded', 'false');
  }

  trigger.addEventListener('click', function (e) {
    e.stopPropagation();
    if (menu.hidden) { open(); } else { close(); }
  });

  // Cerrar al hacer click fuera del menú y del trigger
  document.addEventListener('click', function (e) {
    if (!menu.hidden && !menu.contains(e.target) && e.target !== trigger) {
      close();
    }
  });

  // Cerrar con Escape y devolver el foco al trigger
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && !menu.hidden) {
      close();
      trigger.focus();
    }
  });
})();
