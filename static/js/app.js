/**
 * FASHION. — Main Application Entry & Coordinator
 * Bootstraps modules, binds mobile navigation, search, and initial content
 */

// Ensure smooth page transition resets on back/forward history navigation
window.addEventListener('pageshow', () => {
  document.body.classList.remove('page-transitioning');
});

document.addEventListener('DOMContentLoaded', async () => {
  document.body.classList.remove('page-transitioning');
  // 1. Initialize UI Effects & Scroll Listeners
  UI.initHeaderScroll();
  UI.initScrollAutoplayVideos();
  UI.initHeroSlider();
  Chat.init();
  Products.updateWishlistBadge();

  // 2. References
  const liveGrid = document.getElementById('liveRecommendationsGrid');
  const trendingGrid = document.getElementById('trendingGrid');
  const headerSearchInput = document.getElementById('headerSearchInput');
  const btnViewSaved = document.getElementById('btnViewSaved');

  // 3. Show Initial Skeletons while loading catalog
  if (liveGrid) UI.renderProductSkeletons(liveGrid, 3);
  if (trendingGrid) UI.renderProductSkeletons(trendingGrid, 4);

  // 4. Load Catalog from Backend
  const catalog = await Products.loadCatalog();

  if (catalog && catalog.length > 0) {
    // Populate Live Board with initial recommended picks
    if (liveGrid) {
      Products.renderGrid(liveGrid, catalog.slice(0, 4));
      const sectionMeta = document.getElementById('liveRecommendationsMeta');
      if (sectionMeta) sectionMeta.textContent = 'Gợi ý nổi bật hôm nay';
    }

    // Populate Trending section with remaining items
    if (trendingGrid) {
      Products.renderGrid(trendingGrid, catalog.slice(2, 6));
    }
  } else {
    if (liveGrid) UI.renderEmptyState(liveGrid);
    if (trendingGrid) UI.renderEmptyState(trendingGrid);
  }

  // 5. Header Search Handling
  if (headerSearchInput) {
    headerSearchInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        const query = headerSearchInput.value.trim();
        if (query) {
          Chat.sendPrompt(`Tìm ${query}`);
          headerSearchInput.value = '';
          // Smooth scroll to Stylist section
          const stylistCard = document.querySelector('.stylist-session-card');
          if (stylistCard) {
            stylistCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
          }
        }
      }
    });
  }

  // 6. View Wishlist / Saved Items (Slide-over Drawer)
  window.showSavedItemsView = () => {
    if (typeof Wishlist !== 'undefined' && Wishlist.open) {
      Wishlist.open();
    }
  };

  if (btnViewSaved) {
    btnViewSaved.addEventListener('click', (e) => {
      e.preventDefault();
      if (typeof Wishlist !== 'undefined' && Wishlist.open) {
        Wishlist.open();
      }
    });
  }

  // Robust global User Dropdown controller
  window.toggleUserDropdown = (e) => {
    if (e) {
      e.preventDefault();
      e.stopPropagation();
    }
    const menu = document.getElementById('userDropdownMenu');
    const btn = document.getElementById('userMenuBtn');
    if (!menu) return;
    const isShown = menu.classList.contains('show');
    if (isShown) {
      menu.classList.remove('show');
      if (btn) btn.setAttribute('aria-expanded', 'false');
    } else {
      menu.classList.add('show');
      if (btn) btn.setAttribute('aria-expanded', 'true');
    }
  };

  window.closeUserDropdown = () => {
    const menu = document.getElementById('userDropdownMenu');
    const btn = document.getElementById('userMenuBtn');
    if (menu) {
      menu.classList.remove('show');
    }
    if (btn) btn.setAttribute('aria-expanded', 'false');
  };

  const userMenuBtn = document.getElementById('userMenuBtn');
  if (userMenuBtn) {
    userMenuBtn.addEventListener('click', (e) => {
      window.toggleUserDropdown(e);
    });
  }

  document.addEventListener('click', (e) => {
    const wrapper = document.getElementById('userDropdownWrapper') || document.querySelector('.user-dropdown-wrapper');
    if (wrapper && !wrapper.contains(e.target)) {
      window.closeUserDropdown();
    }
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      window.closeUserDropdown();
    }
  });

  // 7. Mobile Bottom Navigation Handling
  const bottomNavButtons = document.querySelectorAll('.bottom-nav-btn');
  bottomNavButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      bottomNavButtons.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      const target = btn.dataset.nav;
      if (target === 'home') {
        window.scrollTo({ top: 0, behavior: 'smooth' });
      } else if (target === 'style') {
        Chat.openChat();
      } else if (target === 'explore') {
        const trendingSection = document.querySelector('.trending-social-box');
        if (trendingSection) {
          trendingSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
      } else if (target === 'saved') {
        window.showSavedItemsView();
      } else if (target === 'profile') {
        window.location.href = '/login';
      }
    });
  });

  // 8. Close Modal when clicking outside
  const modal = document.getElementById('productModal');
  if (modal) {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        UI.closeProductModal();
      }
    });
  }

  console.log('[Evern] Editorial Fashion × Gen Z Frontend initialized.');
});
