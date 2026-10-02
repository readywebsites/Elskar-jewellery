/* ==========================================================================
   AZURE JEWELS - PREMIUM NAVIGATION & HEADER JAVASCRIPT
   Features:
   - Auto-rotating announcement bar (pause on hover, manual controls)
   - 60fps sticky header scroll transitions (Deep Navy compact state)
   - Expandable luxury search overlay with quick tags & auto-focus
   - Fully responsive mobile drawer with smooth accordion menus
   - Safe element guarding (zero missing-element errors)
   - Database-backed source of truth (zero localStorage interference)
   ========================================================================== */

(function () {
  'use strict';

  // ------------------------------------------------------------------------
  // 1. Top Rotating Announcement Bar
  // ------------------------------------------------------------------------
  function initAnnouncementBar() {
    const slider = document.getElementById('azureAnnounceSlider');
    if (!slider) return;

    const items = slider.querySelectorAll('.azure-announcement-item');
    if (!items.length) return;

    let currentIndex = 0;
    let timer = null;
    const intervalTime = 4000;

    function showSlide(index) {
      items.forEach(function (item, idx) {
        if (idx === index) {
          item.classList.add('active');
        } else {
          item.classList.remove('active');
        }
      });
      currentIndex = index;
    }

    function nextSlide() {
      const nextIndex = (currentIndex + 1) % items.length;
      showSlide(nextIndex);
    }

    function prevSlide() {
      const prevIndex = (currentIndex - 1 + items.length) % items.length;
      showSlide(prevIndex);
    }

    function startAutoplay() {
      stopAutoplay();
      timer = setInterval(nextSlide, intervalTime);
    }

    function stopAutoplay() {
      if (timer) {
        clearInterval(timer);
        timer = null;
      }
    }

    const nextBtn = document.getElementById('azureAnnounceNext');
    const prevBtn = document.getElementById('azureAnnouncePrev');

    if (nextBtn) {
      nextBtn.addEventListener('click', function () {
        nextSlide();
        startAutoplay();
      });
    }

    if (prevBtn) {
      prevBtn.addEventListener('click', function () {
        prevSlide();
        startAutoplay();
      });
    }

    const barEl = document.getElementById('azureAnnouncementBar');
    if (barEl) {
      barEl.addEventListener('mouseenter', stopAutoplay);
      barEl.addEventListener('mouseleave', startAutoplay);
    }

    startAutoplay();
  }

  // ------------------------------------------------------------------------
  // 2. Sticky Header with Scroll Optimization
  // ------------------------------------------------------------------------
  function initStickyHeader() {
    const headerWrapper = document.getElementById('azureHeaderWrapper');
    if (!headerWrapper) return;

    let lastKnownScrollPosition = 0;
    let ticking = false;

    function onScroll() {
      lastKnownScrollPosition = window.scrollY || window.pageYOffset || 0;
      if (!ticking) {
        window.requestAnimationFrame(function () {
          if (lastKnownScrollPosition > 35) {
            headerWrapper.classList.add('is-scrolled');
          } else {
            headerWrapper.classList.remove('is-scrolled');
          }
          ticking = false;
        });
        ticking = true;
      }
    }

    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
  }

  // ------------------------------------------------------------------------
  // 3. Expandable Search Overlay
  // ------------------------------------------------------------------------
  function initSearchOverlay() {
    const searchToggle = document.getElementById('azureSearchToggle');
    const searchOverlay = document.getElementById('azureSearchOverlay');
    const searchClose = document.getElementById('azureSearchClose');
    const searchInput = document.getElementById('azureSearchInput');
    const searchForm = document.getElementById('azureSearchForm');

    if (!searchToggle || !searchOverlay) return;

    function openSearch() {
      searchOverlay.classList.add('is-active');
      searchOverlay.setAttribute('aria-hidden', 'false');
      searchToggle.setAttribute('aria-expanded', 'true');
      if (searchInput) {
        setTimeout(function () {
          searchInput.focus();
        }, 120);
      }
    }

    function closeSearch() {
      searchOverlay.classList.remove('is-active');
      searchOverlay.setAttribute('aria-hidden', 'true');
      searchToggle.setAttribute('aria-expanded', 'false');
    }

    searchToggle.addEventListener('click', function (e) {
      e.preventDefault();
      if (searchOverlay.classList.contains('is-active')) {
        closeSearch();
      } else {
        openSearch();
      }
    });

    if (searchClose) {
      searchClose.addEventListener('click', function (e) {
        e.preventDefault();
        closeSearch();
      });
    }

    // Close on Escape key
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && searchOverlay.classList.contains('is-active')) {
        closeSearch();
      }
    });

    // Handle search form validation
    if (searchForm) {
      searchForm.addEventListener('submit', function (e) {
        if (searchInput && !searchInput.value.trim()) {
          e.preventDefault();
          searchInput.focus();
        }
      });
    }
  }

  // ------------------------------------------------------------------------
  // 4. Mobile Drawer & Accordion Navigation
  // ------------------------------------------------------------------------
  function initMobileMenu() {
    const mobileToggle = document.getElementById('azureMobileToggle');
    const mobileDrawer = document.getElementById('azureMobileDrawer');
    const mobileBackdrop = document.getElementById('azureMobileBackdrop');
    const mobileClose = document.getElementById('azureMobileClose');

    if (!mobileDrawer) return;

    function openDrawer() {
      mobileDrawer.classList.add('is-active');
      mobileDrawer.setAttribute('aria-hidden', 'false');
      if (mobileBackdrop) {
        mobileBackdrop.classList.add('is-active');
      }
      if (mobileToggle) {
        mobileToggle.setAttribute('aria-expanded', 'true');
      }
      document.body.style.overflow = 'hidden';
    }

    function closeDrawer() {
      mobileDrawer.classList.remove('is-active');
      mobileDrawer.setAttribute('aria-hidden', 'true');
      if (mobileBackdrop) {
        mobileBackdrop.classList.remove('is-active');
      }
      if (mobileToggle) {
        mobileToggle.setAttribute('aria-expanded', 'false');
      }
      document.body.style.overflow = '';
    }

    if (mobileToggle) {
      mobileToggle.addEventListener('click', function (e) {
        e.preventDefault();
        openDrawer();
      });
    }

    if (mobileClose) {
      mobileClose.addEventListener('click', function (e) {
        e.preventDefault();
        closeDrawer();
      });
    }

    if (mobileBackdrop) {
      mobileBackdrop.addEventListener('click', function () {
        closeDrawer();
      });
    }

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && mobileDrawer.classList.contains('is-active')) {
        closeDrawer();
      }
    });

    // Mobile Accordion Items (+ / - toggle)
    const accordionItems = mobileDrawer.querySelectorAll('.azure-mobile-accordion');
    accordionItems.forEach(function (item) {
      const toggleBtn = item.querySelector('.azure-accordion-toggle');
      if (toggleBtn) {
        toggleBtn.addEventListener('click', function (e) {
          e.preventDefault();
          e.stopPropagation();
          const isOpen = item.classList.contains('is-open');

          accordionItems.forEach(function (other) {
            if (other !== item) {
              other.classList.remove('is-open');
              const otherBtn = other.querySelector('.azure-accordion-toggle');
              if (otherBtn) {
                otherBtn.setAttribute('aria-expanded', 'false');
                otherBtn.textContent = '+';
              }
            }
          });

          if (isOpen) {
            item.classList.remove('is-open');
            toggleBtn.setAttribute('aria-expanded', 'false');
            toggleBtn.textContent = '+';
          } else {
            item.classList.add('is-open');
            toggleBtn.setAttribute('aria-expanded', 'true');
            toggleBtn.textContent = '−';
          }
        });
      }
    });
  }

  // ------------------------------------------------------------------------
  // 5. Desktop Mega Menu & MORE Dropdown Interaction
  // ------------------------------------------------------------------------
  function initMegaMenu() {
    const navbar = document.getElementById('azureNavbar');
    if (!navbar) return;

    const navItems = navbar.querySelectorAll('.azure-has-mega, .azure-nav-more-item');
    let closeTimer = null;
    let activeItem = null;

    function openItem(item) {
      if (closeTimer) {
        clearTimeout(closeTimer);
        closeTimer = null;
      }
      if (activeItem && activeItem !== item) {
        activeItem.classList.remove('is-open');
        const prevLink = activeItem.querySelector('.azure-nav-link');
        if (prevLink) prevLink.setAttribute('aria-expanded', 'false');
      }
      activeItem = item;
      item.classList.add('is-open');
      const link = item.querySelector('.azure-nav-link');
      if (link) link.setAttribute('aria-expanded', 'true');
    }

    function scheduleClose(item) {
      if (closeTimer) clearTimeout(closeTimer);
      closeTimer = setTimeout(function () {
        if (item) {
          item.classList.remove('is-open');
          const link = item.querySelector('.azure-nav-link');
          if (link) link.setAttribute('aria-expanded', 'false');
          if (activeItem === item) activeItem = null;
        }
      }, 180);
    }

    function closeAllImmediate() {
      if (closeTimer) {
        clearTimeout(closeTimer);
        closeTimer = null;
      }
      navItems.forEach(function (item) {
        item.classList.remove('is-open');
        const link = item.querySelector('.azure-nav-link');
        if (link) link.setAttribute('aria-expanded', 'false');
      });
      activeItem = null;
    }

    navItems.forEach(function (item) {
      const link = item.querySelector('.azure-nav-link');
      const dropdown = item.querySelector('.azure-mega-dropdown, .azure-more-menu');

      // Open immediately on mouse hover
      item.addEventListener('mouseenter', function () {
        openItem(item);
      });

      // Small delay on mouseleave prevents flickering
      item.addEventListener('mouseleave', function () {
        scheduleClose(item);
      });

      // Moving mouse into dropdown cancels closing
      if (dropdown) {
        dropdown.addEventListener('mouseenter', function () {
          if (closeTimer) {
            clearTimeout(closeTimer);
            closeTimer = null;
          }
          item.classList.add('is-open');
        });

        dropdown.addEventListener('mouseleave', function () {
          scheduleClose(item);
        });
      }

      // Click support
      if (link) {
        link.addEventListener('click', function (e) {
          if (item.classList.contains('azure-nav-more-item') || link.tagName === 'BUTTON') {
            e.preventDefault();
            if (item.classList.contains('is-open')) {
              closeAllImmediate();
            } else {
              openItem(item);
            }
          }
        });
      }
    });

    // Close when mouse leaves navbar area
    navbar.addEventListener('mouseleave', function () {
      if (activeItem) scheduleClose(activeItem);
    });

    // Close on outside click
    document.addEventListener('click', function (e) {
      if (!navbar.contains(e.target)) {
        closeAllImmediate();
      }
    });

    // Close on Escape key
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') {
        closeAllImmediate();
      }
    });
  }

  // ------------------------------------------------------------------------
  // Initialize When DOM Is Ready
  // ------------------------------------------------------------------------
  function init() {
    initAnnouncementBar();
    initStickyHeader();
    initSearchOverlay();
    initMobileMenu();
    initMegaMenu();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
