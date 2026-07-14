/* gallery_sidebar.js — sidebar del admin de galería.
 * Patrón basado en Adminator v4 (MIT): vanilla JS, sin dependencias.
 * Mobile drawer con body.has-drawer-open, backdrop inyectado,
 * cierre con Escape, click en nav link o click en overlay.
 */
(function () {
  'use strict';

  var body = document.body;
  var sidebar = document.getElementById('adminSidebar');
  var toggle = document.getElementById('adminMenuToggle');
  var closeBtn = document.getElementById('adminSidebarClose');
  var overlay = document.getElementById('adminSidebarOverlay');

  if (!sidebar || !toggle) return;

  function isMobile() {
    return window.innerWidth <= 860;
  }

  function openDrawer() {
    body.classList.add('has-drawer-open');
    toggle.setAttribute('aria-expanded', 'true');
  }

  function closeDrawer() {
    body.classList.remove('has-drawer-open');
    toggle.setAttribute('aria-expanded', 'false');
  }

  function toggleDrawer() {
    if (body.classList.contains('has-drawer-open')) {
      closeDrawer();
    } else {
      openDrawer();
    }
  }

  toggle.addEventListener('click', function (e) {
    e.preventDefault();
    toggleDrawer();
  });

  if (closeBtn) {
    closeBtn.addEventListener('click', closeDrawer);
  }

  if (overlay) {
    overlay.addEventListener('click', closeDrawer);
  }

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && body.classList.contains('has-drawer-open')) {
      closeDrawer();
    }
  });

  document.addEventListener('click', function (e) {
    var linkInDrawer = e.target.closest('.admin-sidebar a[href]:not([href^="#"]):not([href="javascript:void(0)"])');
    if (body.classList.contains('has-drawer-open') && linkInDrawer) {
      closeDrawer();
    }
  });

  window.addEventListener('resize', function () {
    if (!isMobile()) {
      closeDrawer();
    }
  });
})();
