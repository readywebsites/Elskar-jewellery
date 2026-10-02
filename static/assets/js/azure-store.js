/* ==========================================================================
   AZURE JEWELS - E-COMMERCE FRONTEND CONTROLLER
   Integrated with Django Sessions, Database, CSRF, and Dynamic Badges
   ========================================================================== */

(function () {
  'use strict';

  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  const csrftoken = getCookie('csrftoken');

  function showToast(message, type) {
    let container = document.getElementById('azureMessagesContainer');
    if (!container) {
      container = document.createElement('div');
      container.id = 'azureMessagesContainer';
      container.className = 'azure-messages-container';
      document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = 'azure-alert-toast azure-alert-' + (type || 'success');
    toast.innerHTML = `
      <div class="d-flex align-items-center gap-2">
        <i class="bi ${type === 'error' ? 'bi-exclamation-circle' : 'bi-check-circle'} fs-5"></i>
        <span>${message}</span>
      </div>
      <button type="button" class="azure-toast-close" aria-label="Close">&times;</button>
    `;

    container.appendChild(toast);

    toast.querySelector('.azure-toast-close').addEventListener('click', function () {
      toast.remove();
    });

    setTimeout(function () {
      if (toast.parentNode) {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(40px)';
        toast.style.transition = 'all 0.3s ease';
        setTimeout(() => toast.remove(), 300);
      }
    }, 3800);
  }

  window.showAzureToast = showToast;

  function updateBadges(cartCount, wishCount) {
    if (cartCount !== undefined) {
      document.querySelectorAll('.cart-badge, #azureCartCount').forEach(el => {
        el.textContent = cartCount;
        el.style.display = cartCount > 0 ? 'flex' : 'none';
      });
    }
    if (wishCount !== undefined) {
      document.querySelectorAll('.wishlist-count, #azureWishCount, #azureMobileWishCount').forEach(el => {
        el.textContent = wishCount;
        el.style.display = wishCount > 0 ? 'flex' : 'none';
      });
    }
  }

  document.addEventListener('DOMContentLoaded', function () {
    // Initial badge visibility check
    document.querySelectorAll('.cart-badge, #azureCartCount').forEach(el => {
      const count = parseInt(el.textContent.trim(), 10) || 0;
      el.style.display = count > 0 ? 'flex' : 'none';
    });
    document.querySelectorAll('.wishlist-count, #azureWishCount, #azureMobileWishCount').forEach(el => {
      const count = parseInt(el.textContent.trim(), 10) || 0;
      el.style.display = count > 0 ? 'flex' : 'none';
    });

    // Handle AJAX Add to Bag (Quick add buttons on cards and detail page form)
    document.addEventListener('click', function (e) {
      const addBtn = e.target.closest('.azure-quick-add-btn, .btn-ajax-add-cart');
      if (addBtn) {
        e.preventDefault();
        const prodId = addBtn.dataset.productId;
        if (!prodId) return;

        const originalText = addBtn.innerHTML;
        addBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> Adding...';
        addBtn.disabled = true;

        fetch('/cart/add/' + prodId + '/', {
          method: 'POST',
          headers: {
            'X-CSRFToken': csrftoken,
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/x-www-form-urlencoded',
          },
          body: 'quantity=' + (addBtn.dataset.quantity || 1)
        })
          .then(res => res.json())
          .then(data => {
            addBtn.innerHTML = originalText;
            addBtn.disabled = false;
            if (data.success) {
              showToast(data.message || 'Added to your shopping bag!', 'success');
              updateBadges(data.cart_count);
            } else {
              showToast(data.message || 'Could not add item to bag.', 'error');
            }
          })
          .catch(() => {
            addBtn.innerHTML = originalText;
            addBtn.disabled = false;
            // Fallback to normal form submission if needed
            window.location.href = '/cart/add/' + prodId + '/';
          });
      }

      // Handle Wishlist Toggle
      const wishBtn = e.target.closest('.azure-product-wish-btn, .btn-wishlist-toggle');
      if (wishBtn) {
        e.preventDefault();
        const prodId = wishBtn.dataset.productId;
        if (!prodId) return;

        fetch('/wishlist/toggle/' + prodId + '/', {
          method: 'GET',
          headers: {
            'X-Requested-With': 'XMLHttpRequest',
          }
        })
          .then(res => res.json())
          .then(data => {
            if (data.success) {
              if (data.added) {
                wishBtn.classList.add('active');
                const icon = wishBtn.querySelector('i');
                if (icon) {
                  icon.classList.remove('bi-heart');
                  icon.classList.add('bi-heart-fill');
                }
              } else {
                wishBtn.classList.remove('active');
                const icon = wishBtn.querySelector('i');
                if (icon) {
                  icon.classList.remove('bi-heart-fill');
                  icon.classList.add('bi-heart');
                }
              }
              showToast(data.message, 'success');
              updateBadges(undefined, data.wishlist_count);
            }
          })
          .catch(() => {
            window.location.href = '/wishlist/toggle/' + prodId + '/';
          });
      }
    });

    // Auto-dismiss rendered Django messages after 4 seconds
    document.querySelectorAll('.azure-alert-toast').forEach(toast => {
      const closeBtn = toast.querySelector('.azure-toast-close');
      if (closeBtn) {
        closeBtn.addEventListener('click', () => toast.remove());
      }
      setTimeout(() => {
        if (toast.parentNode) {
          toast.style.opacity = '0';
          toast.style.transform = 'translateX(40px)';
          toast.style.transition = 'all 0.3s ease';
          setTimeout(() => toast.remove(), 300);
        }
      }, 4000);
    });
  });
})();
