/**
 * FASHION. — Products & Social Commerce Module
 * Product cards, Wishlist management (localStorage), Quick View, Cart
 */

const Products = (() => {
  let catalog = [];
  const WISHLIST_KEY = 'fashion_saved_items';

  // Load Saved Items from localStorage
  const getSavedIds = () => {
    try {
      return JSON.parse(localStorage.getItem(WISHLIST_KEY)) || [];
    } catch {
      return [];
    }
  };

  const saveIds = (ids) => {
    localStorage.setItem(WISHLIST_KEY, JSON.stringify(ids));
    updateWishlistBadge();
  };

  const updateWishlistBadge = () => {
    const badge = document.getElementById('wishlistCountBadge');
    if (!badge) return;
    const count = getSavedIds().length;
    badge.textContent = count;
    badge.style.display = count > 0 ? 'flex' : 'none';
  };

  // Toggle Wishlist
  const toggleWishlist = (product, triggerEl) => {
    let saved = getSavedIds();
    const id = product.id;
    const index = saved.indexOf(id);
    const isNowSaved = (index === -1);

    if (index > -1) {
      saved.splice(index, 1);
      UI.showToast(`Đã bỏ lưu "${product.name}"`, '♡');
    } else {
      saved.push(id);
      UI.showToast(`Đã lưu "${product.name}" vào yêu thích!`, '♥');
    }
    saveIds(saved);

    // Sync all wishlist buttons with this product id across the DOM
    document.querySelectorAll(`[data-id="${id}"]`).forEach(el => {
      // Corner floating button
      if (el.classList.contains('btn-wishlist')) {
        el.classList.toggle('active', isNowSaved);
        const svg = el.querySelector('svg');
        if (svg) {
          svg.setAttribute('fill', isNowSaved ? 'currentColor' : 'none');
        }
      }
      // Card action bar favorite button
      if (el.classList.contains('btn-card-action') && el.classList.contains('favorite')) {
        el.classList.toggle('active', isNowSaved);
        const icon = el.querySelector('i');
        if (icon) {
          icon.className = isNowSaved ? 'fa-solid fa-heart' : 'fa-regular fa-heart';
        }
        const textSpan = el.querySelector('span');
        if (textSpan) {
          textSpan.textContent = isNowSaved ? 'Đã lưu' : 'Yêu thích';
        }
      }
      // Product detail page main wishlist button
      if (el.id === 'btnPdpWishlist') {
        el.classList.toggle('active', isNowSaved);
        const txt = document.getElementById('btnWishlistText');
        if (txt) txt.textContent = isNowSaved ? 'ĐÃ LƯU' : 'YÊU THÍCH';
      }
    });

    if (triggerEl) {
      triggerEl.classList.add('animate-bounce');
      setTimeout(() => triggerEl.classList.remove('animate-bounce'), 350);
    }

    if (typeof Wishlist !== 'undefined' && Wishlist.isOpen && Wishlist.isOpen()) {
      Wishlist.renderDrawer();
    }
  };

  // Build Single Product Card DOM Element
  const createCardElement = (product, isCarousel = false) => {
    const card = document.createElement('div');
    card.className = isCarousel ? 'fashion-card carousel-item' : 'fashion-card';

    const isSaved = getSavedIds().includes(product.id);
    const badgeLabel = product.sub_category || product.category || 'New Fit';
    const sizes = Array.isArray(product.sizes) ? product.sizes : (product.sizes ? product.sizes.split(',') : []);

    card.innerHTML = `
      <div class="card-media-wrap">
        <span class="card-badge-style">${badgeLabel}</span>
        <button class="btn-wishlist ${isSaved ? 'active' : ''}" aria-label="Lưu sản phẩm" title="Lưu vào yêu thích">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="${isSaved ? 'currentColor' : 'none'}" stroke="currentColor" stroke-width="2">
            <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
          </svg>
        </button>
        <img src="${product.image_url || '/static/images/placeholder.jpg'}" alt="${product.name}" loading="lazy" onerror="this.onerror=null; this.src='/static/images/placeholder.jpg';">
      </div>
      <div class="card-content-area">
        <h4 class="card-title" title="${product.name}">${product.name}</h4>
        <div class="card-price-row">
          <span class="card-price">${UI.formatVND(product.price)}</span>
          ${product.price > 600000 ? `<span class="card-old-price">${UI.formatVND(Math.round(product.price * 1.25))}</span>` : ''}
        </div>
        <div class="card-pill-row">
          ${sizes.slice(0, 3).map(s => `<span class="size-tag">${s.trim()}</span>`).join('')}
          ${product.color ? `<span class="size-tag" style="background:#FFFFFF; border:1px solid #EAEAEA;">${product.color}</span>` : ''}
        </div>
        <div class="card-action-bar">
          <button class="btn-card-action view" type="button">Chi tiết</button>
          <button class="btn-card-action favorite ${isSaved ? 'active' : ''}" type="button" data-id="${product.id}" title="${isSaved ? 'Bỏ lưu khỏi yêu thích' : 'Thêm vào yêu thích'}">
            <i class="${isSaved ? 'fa-solid' : 'fa-regular'} fa-heart"></i>
            <span>${isSaved ? 'Đã lưu' : 'Yêu thích'}</span>
          </button>
        </div>
      </div>
    `;

    // Wishlist click (corner icon)
    const wishlistBtn = card.querySelector('.btn-wishlist');
    wishlistBtn.setAttribute('data-id', product.id);
    wishlistBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      toggleWishlist(product, wishlistBtn);
    });

    // Favorite button click (action bar)
    const favBtn = card.querySelector('.btn-card-action.favorite');
    if (favBtn) {
      favBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        toggleWishlist(product, favBtn);
      });
    }

    // View detail navigation to dedicated product page with smooth transition
    const goToDetail = (e) => {
      e.stopPropagation();
      e.preventDefault();
      smoothNavigate(`/product/${product.id}`);
    };

    const viewBtn = card.querySelector('.btn-card-action.view');
    if (viewBtn) viewBtn.addEventListener('click', goToDetail);

    const cardImg = card.querySelector('.card-media-wrap img');
    if (cardImg) {
      cardImg.style.cursor = 'pointer';
      cardImg.addEventListener('click', goToDetail);
    }

    const cardTitle = card.querySelector('.card-title');
    if (cardTitle) {
      cardTitle.style.cursor = 'pointer';
      cardTitle.addEventListener('click', goToDetail);
    }

    // Prefetch product detail page on hover / touch for instant zero-lag transition
    card.addEventListener('mouseenter', () => prefetchUrl(`/product/${product.id}`), { once: true, passive: true });
    card.addEventListener('touchstart', () => prefetchUrl(`/product/${product.id}`), { once: true, passive: true });

    // Legacy add button fallback if present
    const addBtn = card.querySelector('.btn-card-action.add');
    if (addBtn) {
      addBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        addToCart(product);
      });
    }

    return card;
  };

  // Preload/prefetch URL in background
  const prefetchUrl = (url) => {
    if (!url || document.querySelector(`link[rel="prefetch"][href="${url}"]`)) return;
    const link = document.createElement('link');
    link.rel = 'prefetch';
    link.href = url;
    document.head.appendChild(link);
  };

  // Silky-smooth cross-page navigation
  const smoothNavigate = (url) => {
    if (!url) return;
    document.body.classList.add('page-transitioning');
    if ('startViewTransition' in document) {
      document.startViewTransition(() => {
        window.location.href = url;
      });
    } else {
      setTimeout(() => {
        window.location.href = url;
      }, 90);
    }
  };

  // Render Array of Products into a Container
  const renderGrid = (container, products = []) => {
    if (!container) return;
    container.innerHTML = '';
    products.forEach(p => {
      container.appendChild(createCardElement(p));
    });
  };

  // Build Compact Horizontal Product Item for Chat Widget
  const createCompactCardElement = (product) => {
    const item = document.createElement('div');
    item.className = 'chat-compact-product';

    const badgeLabel = product.sub_category || product.category || 'Gợi ý';
    const sizes = Array.isArray(product.sizes) ? product.sizes : (product.sizes ? product.sizes.split(',') : []);

    const safeName = (product.name || '').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    const priceStr = typeof UI !== 'undefined' && UI.formatVND ? UI.formatVND(product.price) : `${Number(product.price).toLocaleString()}đ`;
    const oldPriceHtml = product.old_price && product.old_price > product.price
      ? `<span class="compact-old-price">${typeof UI !== 'undefined' && UI.formatVND ? UI.formatVND(product.old_price) : `${Number(product.old_price).toLocaleString()}đ`}</span>`
      : (product.price > 600000 ? `<span class="compact-old-price">${typeof UI !== 'undefined' && UI.formatVND ? UI.formatVND(Math.round(product.price * 1.25)) : ''}</span>` : '');

    item.innerHTML = `
      <div class="compact-thumb-wrap">
        <img src="${product.image_url || '/static/images/placeholder.jpg'}" alt="${safeName}" loading="lazy" onerror="this.onerror=null; this.src='/static/images/placeholder.jpg';">
      </div>
      <div class="compact-info">
        <span class="compact-badge">${badgeLabel}</span>
        <h5 class="compact-title" title="${safeName}">${safeName}</h5>
        <div class="compact-price-row">
          <span class="compact-price">${priceStr}</span>
          ${oldPriceHtml}
        </div>
        <div class="compact-tags-row">
          ${product.color ? `<span class="compact-tag">${product.color}</span>` : ''}
          ${sizes.length > 0 ? `<span class="compact-tag">Size: ${sizes.slice(0, 3).map(s => String(s).trim()).join('/')}</span>` : ''}
        </div>
      </div>
      <div class="compact-actions">
        <button class="compact-action-btn" type="button" title="Xem chi tiết sản phẩm">
          <span>Xem</span>
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <line x1="5" y1="12" x2="19" y2="12"></line>
            <polyline points="12 5 19 12 12 19"></polyline>
          </svg>
        </button>
      </div>
    `;

    // Click anywhere on item or view button opens product detail
    const goToDetail = (e) => {
      e.stopPropagation();
      e.preventDefault();
      smoothNavigate(`/product/${product.id}`);
    };

    item.addEventListener('click', goToDetail);
    const actionBtn = item.querySelector('.compact-action-btn');
    if (actionBtn) actionBtn.addEventListener('click', goToDetail);

    item.addEventListener('mouseenter', () => prefetchUrl(`/product/${product.id}`), { once: true, passive: true });

    return item;
  };

  // Render Vertical List of Compact Products for Chat Container
  const renderVerticalList = (containerOrProducts, maybeProducts = []) => {
    let container;
    let products;

    if (Array.isArray(containerOrProducts)) {
      products = containerOrProducts;
      container = document.createElement('div');
      container.className = 'chat-products-container';
    } else {
      container = containerOrProducts;
      products = maybeProducts;
    }

    if (!container) return null;
    container.innerHTML = '';
    (products || []).forEach(p => {
      container.appendChild(createCompactCardElement(p));
    });
    return container;
  };

  // Render Horizontal Carousel or Vertical List of Products
  const renderCarousel = (containerOrProducts, maybeProducts = []) => {
    return renderVerticalList(containerOrProducts, maybeProducts);
  };

  // Add to Cart
  const addToCart = (product) => {
    if (typeof Cart !== 'undefined') {
      const sizes = Array.isArray(product.sizes) ? product.sizes : (product.sizes ? product.sizes.split(',') : []);
      const defaultSize = sizes.length > 0 
        ? (typeof sizes[0] === 'string' ? sizes[0].trim() : sizes[0]) 
        : 'L';
      const defaultColor = product.color || 'Tiêu chuẩn';
      Cart.addItem(product, defaultSize, defaultColor, 1);
    } else {
      const name = typeof product === 'string' ? product : (product ? product.name : 'Sản phẩm');
      UI.showToast(`Đã thêm "${name}" vào giỏ hàng!`, '🛍️');
    }
  };

  // Fetch Catalog from Flask Backend
  const loadCatalog = async () => {
    try {
      const res = await fetch('/api/products');
      if (res.ok) {
        catalog = await res.json();
        return catalog;
      }
    } catch (err) {
      console.warn('Could not fetch /api/products, using fallback catalog:', err);
    }
    return catalog;
  };

  const getCatalog = () => catalog;

  return {
    loadCatalog,
    getCatalog,
    renderGrid,
    renderCarousel,
    renderVerticalList,
    createCardElement,
    createCompactCardElement,
    addToCart,
    toggleWishlist,
    updateWishlistBadge,
    getSavedIds,
    saveIds,
    prefetch: prefetchUrl,
    navigate: smoothNavigate
  };
})();

/**
 * EVERN. — Wishlist / Favorites Slide-over Drawer Module
 * Slides in from right, matching the Cart Drawer structure & styling
 */
const Wishlist = (() => {
  const formatVND = (num) => {
    return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(num || 0);
  };

  const open = async () => {
    // Ensure catalog is loaded
    if (!Products.getCatalog() || Products.getCatalog().length === 0) {
      await Products.loadCatalog();
    }
    const backdrop = document.getElementById('wishlistDrawerBackdrop');
    if (backdrop) {
      backdrop.classList.add('open');
      renderDrawer();
    }
  };

  const close = () => {
    const backdrop = document.getElementById('wishlistDrawerBackdrop');
    if (backdrop) {
      backdrop.classList.remove('open');
    }
  };

  const isOpen = () => {
    const backdrop = document.getElementById('wishlistDrawerBackdrop');
    return backdrop && backdrop.classList.contains('open');
  };

  const removeItem = (id) => {
    const savedIds = Products.getSavedIds();
    const newIds = savedIds.filter(savedId => savedId !== id);
    const all = Products.getCatalog();
    const item = all.find(p => p.id === id);
    const itemName = item ? item.name : 'Sản phẩm';

    Products.saveIds(newIds);

    // Sync button states in page
    document.querySelectorAll(`[data-id="${id}"]`).forEach(el => {
      if (el.classList.contains('btn-wishlist')) {
        el.classList.remove('active');
        const svg = el.querySelector('svg');
        if (svg) svg.setAttribute('fill', 'none');
      }
      if (el.classList.contains('btn-card-action') && el.classList.contains('favorite')) {
        el.classList.remove('active');
        const icon = el.querySelector('i');
        if (icon) icon.className = 'fa-regular fa-heart';
        const textSpan = el.querySelector('span');
        if (textSpan) textSpan.textContent = 'Yêu thích';
      }
      if (el.id === 'btnPdpWishlist') {
        el.classList.remove('active');
        const txt = document.getElementById('btnWishlistText');
        if (txt) txt.textContent = 'YÊU THÍCH';
      }
    });

    if (typeof UI !== 'undefined' && UI.showToast) {
      UI.showToast(`Đã bỏ "${itemName}" khỏi yêu thích`, '🗑️');
    }

    renderDrawer();
  };

  const addToCart = (id) => {
    const all = Products.getCatalog();
    const product = all.find(p => p.id === id);
    if (!product) return;

    const sizes = Array.isArray(product.sizes) ? product.sizes : (product.sizes ? product.sizes.split(',') : []);
    const defaultSize = sizes.length > 0 ? (typeof sizes[0] === 'string' ? sizes[0].trim() : sizes[0]) : 'L';
    const defaultColor = product.color || 'Tiêu chuẩn';

    if (typeof Cart !== 'undefined') {
      Cart.addItem(product, defaultSize, defaultColor, 1);
    }
  };

  const addAllToCart = () => {
    if (!window.IS_LOGGED_IN) {
      if (typeof UI !== 'undefined' && UI.showToast) {
        UI.showToast('Vui lòng đăng nhập để thêm vào giỏ hàng!', '🔒');
      }
      setTimeout(() => {
        window.location.href = '/login?next=' + encodeURIComponent('/checkout?mode=cart');
      }, 800);
      return;
    }

    const savedIds = Products.getSavedIds();
    const all = Products.getCatalog();
    const savedProducts = all.filter(p => savedIds.includes(p.id));

    if (savedProducts.length === 0) {
      if (typeof UI !== 'undefined' && UI.showToast) {
        UI.showToast('Danh sách yêu thích trống!', '⚠️');
      }
      return;
    }

    savedProducts.forEach(prod => {
      const sizes = Array.isArray(prod.sizes) ? prod.sizes : (prod.sizes ? prod.sizes.split(',') : []);
      const defaultSize = sizes.length > 0 ? (typeof sizes[0] === 'string' ? sizes[0].trim() : sizes[0]) : 'L';
      const defaultColor = prod.color || 'Tiêu chuẩn';
      Cart.addItemSilently(prod, defaultSize, defaultColor, 1);
    });

    close();
    if (typeof UI !== 'undefined' && UI.showToast) {
      UI.showToast(`Đã thêm ${savedProducts.length} món đồ yêu thích vào giỏ hàng!`, '🛍️');
    }
    Cart.open();
  };

  const renderDrawer = () => {
    const container = document.getElementById('wishlistDrawerItems');
    const headerCount = document.getElementById('wishlistDrawerCount');
    const summaryCount = document.getElementById('wishlistSummaryCount');
    if (!container) return;

    const savedIds = Products.getSavedIds();
    const all = Products.getCatalog();
    const savedProducts = all.filter(p => savedIds.includes(p.id));

    if (headerCount) headerCount.textContent = savedProducts.length;
    if (summaryCount) summaryCount.textContent = `${savedProducts.length} sản phẩm`;

    if (savedProducts.length === 0) {
      container.innerHTML = `
        <div class="cart-empty-state">
          <div class="cart-empty-icon" style="color: #FF4D30; font-size: 38px;">♡</div>
          <h4 class="cart-empty-title">Danh sách yêu thích đang trống</h4>
          <p class="cart-empty-sub">Hãy khám phá bộ sưu tập và bấm vào biểu tượng ♡ trên sản phẩm để lưu lại outfit yêu thích nhé!</p>
          <a href="/#liveSection" class="btn-primary" onclick="Wishlist.close()" style="margin-top: 16px; display: inline-flex;">
            Khám phá sản phẩm ngay
          </a>
        </div>
      `;
      return;
    }

    container.innerHTML = savedProducts.map(item => {
      const badge = item.sub_category || item.category || 'Outfit Gu';
      return `
        <div class="cart-item-card" onmouseenter="Products.prefetch('/product/${item.id}')" ontouchstart="Products.prefetch('/product/${item.id}')">
          <a href="/product/${item.id}" class="cart-item-thumb" onclick="Wishlist.goToProduct(event, '/product/${item.id}')">
            <img src="${item.image_url || '/static/images/placeholder.jpg'}" alt="${item.name}" loading="lazy" decoding="async" onerror="this.onerror=null; this.src='/static/images/placeholder.jpg';">
          </a>
          <div class="cart-item-details">
            <a href="/product/${item.id}" class="cart-item-name" onclick="Wishlist.goToProduct(event, '/product/${item.id}')">
              ${item.name}
            </a>
            <div class="cart-item-meta-tags">
              <span class="cart-meta-pill">${badge}</span>
              <span class="cart-meta-pill">${item.category || 'Thời trang'}</span>
            </div>
            <div class="cart-item-price-row">
              <span class="cart-item-price">${formatVND(item.price)}</span>
              <button type="button" class="btn-wishlist-add-cart" onclick="Wishlist.addToCart(${item.id})" title="Thêm vào giỏ hàng">
                <i class="fa-solid fa-cart-plus"></i> Thêm vào giỏ
              </button>
            </div>
          </div>
          <button type="button" class="btn-cart-remove" onclick="Wishlist.removeItem(${item.id})" title="Xóa khỏi yêu thích" aria-label="Xóa">
            <i class="fa-regular fa-trash-can"></i>
          </button>
        </div>
      `;
    }).join('');
  };

  // Silky smooth navigation from Wishlist drawer to product detail
  const goToProduct = (e, url) => {
    if (e) {
      e.preventDefault();
      e.stopPropagation();
    }
    const panel = document.getElementById('wishlistDrawerPanel');
    if (panel) {
      panel.style.transition = 'opacity 120ms ease, transform 120ms ease';
      panel.style.opacity = '0.6';
      panel.style.transform = 'scale(0.985)';
    }
    document.body.classList.add('page-transitioning');
    if ('startViewTransition' in document) {
      document.startViewTransition(() => {
        window.location.href = url;
      });
    } else {
      setTimeout(() => {
        window.location.href = url;
      }, 90);
    }
  };

  const init = () => {
    // Bind close button
    const btnClose = document.getElementById('btnCloseWishlist');
    if (btnClose) {
      btnClose.addEventListener('click', close);
    }

    // Close when clicking outside on backdrop
    const backdrop = document.getElementById('wishlistDrawerBackdrop');
    if (backdrop) {
      backdrop.addEventListener('click', (e) => {
        if (e.target === backdrop) {
          close();
        }
      });
    }

    // Global ESC key listener to close drawer
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && isOpen()) {
        close();
      }
    });
  };

  return {
    init,
    open,
    close,
    isOpen,
    renderDrawer,
    removeItem,
    addToCart,
    addAllToCart,
    goToProduct
  };
})();

// Expose globally
window.Wishlist = Wishlist;
window.showSavedItemsView = () => Wishlist.open();

// Auto-init Wishlist drawer listeners
document.addEventListener('DOMContentLoaded', () => {
  Wishlist.init();
});

/**
 * ==========================================================================
 * OWEN PRODUCTS CATALOG CONTROLLER
 * Filter sidebar, 10-products-per-page pagination, view mode switcher, sort
 * ==========================================================================
 */
const CatalogPage = (() => {
  let catalog = [];
  let filtered = [];
  let currentPage = 1;
  const pageSize = 10; // Exactly 10 products per page as requested

  let activeCategory = 'all';
  let activeCollars = [];
  let activeSleeves = [];
  let activeMaterials = [];
  let activeFits = [];
  let activeSizes = [];
  let activeColors = [];
  let currentSort = 'default';
  let gridColumns = 3;
  let isSidebarCollapsed = false;

  const formatPrice = (num) => {
    if (typeof UI !== 'undefined' && UI.formatVND) {
      return UI.formatVND(num);
    }
    return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(num || 0);
  };

  // Parse URL query params
  const parseQueryParams = () => {
    const params = new URLSearchParams(window.location.search);
    const p = parseInt(params.get('page'), 10);
    if (!isNaN(p) && p > 0) {
      currentPage = p;
    }
    const cat = params.get('cat');
    if (cat) {
      activeCategory = cat.toLowerCase();
    }
  };

  // Sync state to URL without full reload
  const syncUrlParams = () => {
    const params = new URLSearchParams();
    if (currentPage > 1) {
      params.set('page', currentPage);
    }
    if (activeCategory && activeCategory !== 'all') {
      params.set('cat', activeCategory);
    }
    const newQuery = params.toString() ? '?' + params.toString() : window.location.pathname;
    window.history.replaceState(null, '', newQuery);
  };

  // Initialize Catalog Page
  const init = async () => {
    const grid = document.getElementById('owenProductsGrid');
    if (!grid) return; // Not on the catalog page

    parseQueryParams();

    // Fetch products catalog
    catalog = await Products.loadCatalog();
    if (!catalog || catalog.length === 0) {
      catalog = Products.getCatalog();
    }

    // Mark active category pill
    document.querySelectorAll('.category-pill-btn').forEach(btn => {
      const cat = btn.getAttribute('data-category');
      btn.classList.toggle('active', cat === activeCategory);
      btn.addEventListener('click', () => {
        filterByCategory(cat);
      });
    });

    applyFiltersAndSort();
    render();
  };

  // Accordion Expand/Collapse
  const toggleAccordion = (btn) => {
    const group = btn.closest('.filter-accordion-group');
    if (group) {
      group.classList.toggle('open');
      const content = group.querySelector('.accordion-content');
      if (content) {
        content.style.display = group.classList.contains('open') ? 'block' : 'none';
      }
    }
  };

  // Toggle Sidebar
  const toggleSidebar = () => {
    isSidebarCollapsed = !isSidebarCollapsed;
    const layout = document.getElementById('catalogLayoutGrid');
    const icon = document.getElementById('sidebarToggleIcon');
    if (layout) {
      layout.classList.toggle('sidebar-collapsed', isSidebarCollapsed);
    }
    if (icon) {
      icon.className = isSidebarCollapsed ? 'fa-solid fa-angle-right' : 'fa-solid fa-angle-left';
    }
  };

  // Switch between 3-column and 4-column views
  const setGridColumns = (cols) => {
    gridColumns = cols;
    const grid = document.getElementById('owenProductsGrid');
    const btn3 = document.getElementById('btnView3Col');
    const btn4 = document.getElementById('btnView4Col');

    if (grid) {
      grid.classList.toggle('cols-3', cols === 3);
      grid.classList.toggle('cols-4', cols === 4);
    }
    if (btn3) btn3.classList.toggle('active', cols === 3);
    if (btn4) btn4.classList.toggle('active', cols === 4);
  };

  // Category Filter
  const filterByCategory = (cat) => {
    activeCategory = (cat || 'all').toLowerCase();
    currentPage = 1;

    // Update Category Pills UI
    document.querySelectorAll('.category-pill-btn').forEach(btn => {
      btn.classList.toggle('active', btn.getAttribute('data-category') === activeCategory);
    });

    // Update Breadcrumbs
    const bcCat = document.getElementById('bcCategoryLink');
    const bcCurrent = document.getElementById('bcCurrentLabel');
    if (bcCat && bcCurrent) {
      if (activeCategory === 'all') {
        bcCat.textContent = 'BỘ SƯU TẬP';
        bcCurrent.textContent = 'TẤT CẢ SẢN PHẨM';
      } else if (activeCategory === 'áo') {
        bcCat.textContent = 'ÁO';
        bcCurrent.textContent = 'ÁO SƠ MI & ÁO THUN';
      } else if (activeCategory === 'quần') {
        bcCat.textContent = 'QUẦN';
        bcCurrent.textContent = 'QUẦN ÂU & QUẦN JEAN';
      } else if (activeCategory === 'phụ kiện') {
        bcCat.textContent = 'PHỤ KIỆN';
        bcCurrent.textContent = 'THẮT LƯNG & PHỤ KIỆN';
      } else if (activeCategory === 'new') {
        bcCat.textContent = 'HÀNG MỚI VỀ';
        bcCurrent.textContent = 'NEW ARRIVALS 2026';
      } else if (activeCategory === 'sale') {
        bcCat.textContent = 'ƯU ĐÃI';
        bcCurrent.textContent = 'GIÁ TỐT NHẤT';
      } else if (activeCategory === 'bestseller') {
        bcCat.textContent = 'XU HƯỚNG';
        bcCurrent.textContent = 'BÁN CHẠY NHẤT';
      } else {
        bcCat.textContent = 'THỜI TRANG';
        bcCurrent.textContent = activeCategory.toUpperCase();
      }
    }

    applyFiltersAndSort();
    render();
    syncUrlParams();
  };

  // Size Filter Toggle
  const toggleSizeFilter = (size, btnEl) => {
    const idx = activeSizes.indexOf(size);
    if (idx > -1) {
      activeSizes.splice(idx, 1);
      if (btnEl) btnEl.classList.remove('active');
    } else {
      activeSizes.push(size);
      if (btnEl) btnEl.classList.add('active');
    }
    currentPage = 1;
    applyFiltersAndSort();
    render();
  };

  // Color Filter Toggle
  const toggleColorFilter = (color, chipEl) => {
    const colLower = color.toLowerCase();
    const idx = activeColors.indexOf(colLower);
    if (idx > -1) {
      activeColors.splice(idx, 1);
      if (chipEl) chipEl.classList.remove('active');
    } else {
      activeColors.push(colLower);
      if (chipEl) chipEl.classList.add('active');
    }
    currentPage = 1;
    applyFiltersAndSort();
    render();
  };

  // Generic Checkbox change (Collar, Sleeve, Material, Fit)
  const onFilterChange = () => {
    // Kiểu cổ áo
    activeCollars = Array.from(document.querySelectorAll('input[name="collar"]:checked')).map(cb => cb.value);
    // Kiểu tay áo
    activeSleeves = Array.from(document.querySelectorAll('input[name="sleeve"]:checked')).map(cb => cb.value);
    // Chất liệu
    activeMaterials = Array.from(document.querySelectorAll('input[name="material"]:checked')).map(cb => cb.value);
    // Form dáng
    activeFits = Array.from(document.querySelectorAll('input[name="fit"]:checked')).map(cb => cb.value);

    currentPage = 1;
    applyFiltersAndSort();
    render();
  };

  // Sort Dropdown Change
  const onSortChange = (val) => {
    currentSort = val;
    applyFiltersAndSort();
    render();
  };

  // Reset all filters
  const resetFilters = () => {
    activeCategory = 'all';
    activeCollars = [];
    activeSleeves = [];
    activeMaterials = [];
    activeFits = [];
    activeSizes = [];
    activeColors = [];
    currentSort = 'default';
    currentPage = 1;

    // Uncheck all checkboxes
    document.querySelectorAll('.filter-accordion-group input[type="checkbox"]').forEach(cb => {
      cb.checked = false;
    });

    // Reset size buttons
    document.querySelectorAll('.size-matrix-btn').forEach(btn => {
      btn.classList.remove('active');
    });

    // Reset color chips
    document.querySelectorAll('.filter-color-chip').forEach(chip => {
      chip.classList.remove('active');
    });

    // Reset sort select
    const sortSelect = document.getElementById('catalogSortSelect');
    if (sortSelect) sortSelect.value = 'default';

    // Reset category pills
    document.querySelectorAll('.category-pill-btn').forEach(btn => {
      btn.classList.toggle('active', btn.getAttribute('data-category') === 'all');
    });

    // Reset breadcrumb
    const bcCat = document.getElementById('bcCategoryLink');
    const bcCurrent = document.getElementById('bcCurrentLabel');
    if (bcCat && bcCurrent) {
      bcCat.textContent = 'TRANG CHỦ';
      bcCurrent.textContent = 'TẤT CẢ SẢN PHẨM';
    }

    applyFiltersAndSort();
    render();
    syncUrlParams();
    UI.showToast('Đã đặt lại bộ lọc', '🔄');
  };

  // Filter and Sort Engine
  const applyFiltersAndSort = () => {
    filtered = catalog.filter(p => {
      // Category pill check
      if (activeCategory !== 'all') {
        const pCat = (p.category || '').toLowerCase();
        const pSub = (p.sub_category || '').toLowerCase();
        const pTags = (p.tags || '').toLowerCase();

        if (activeCategory === 'new') {
          if (!pTags.includes('new') && p.id < 20) return false;
        } else if (activeCategory === 'sale') {
          if (!p.old_price && !pTags.includes('sale')) return false;
        } else if (activeCategory === 'bestseller') {
          if (!pTags.includes('bestseller') && (p.points || 0) < 20) return false;
        } else if (activeCategory === 'collection') {
          if (!pTags.includes('collection') && !pCat) return false;
        } else if (activeCategory === 'áo') {
          if (!pCat.includes('áo') && !pSub.includes('áo')) return false;
        } else if (activeCategory === 'quần') {
          if (!pCat.includes('quần') && !pSub.includes('quần')) return false;
        } else if (activeCategory === 'phụ kiện') {
          if (!pCat.includes('phụ kiện') && !pSub.includes('phụ kiện')) return false;
        } else {
          if (!pCat.includes(activeCategory) && !pSub.includes(activeCategory)) return false;
        }
      }

      // Collar filter
      if (activeCollars.length > 0) {
        const pCollar = (p.collar || '').toLowerCase();
        const matchesCollar = activeCollars.some(c => pCollar.includes(c.toLowerCase()));
        if (!matchesCollar) return false;
      }

      // Sleeve filter
      if (activeSleeves.length > 0) {
        const pSleeve = (p.sleeve || '').toLowerCase();
        const matchesSleeve = activeSleeves.some(s => pSleeve.includes(s.toLowerCase()));
        if (!matchesSleeve) return false;
      }

      // Material filter
      if (activeMaterials.length > 0) {
        const pMat = (p.material || '').toLowerCase();
        const matchesMat = activeMaterials.some(m => pMat.includes(m.toLowerCase()));
        if (!matchesMat) return false;
      }

      // Fit filter
      if (activeFits.length > 0) {
        const pFit = (p.fit || '').toLowerCase();
        const matchesFit = activeFits.some(f => pFit.includes(f.toLowerCase()));
        if (!matchesFit) return false;
      }

      // Size filter
      if (activeSizes.length > 0) {
        const sizesArr = Array.isArray(p.sizes) ? p.sizes : (p.sizes ? p.sizes.split(',').map(s => s.trim()) : []);
        const matchesSize = activeSizes.some(sz => sizesArr.includes(sz));
        if (!matchesSize) return false;
      }

      // Color filter
      if (activeColors.length > 0) {
        const pColor = (p.color || '').toLowerCase();
        const matchesColor = activeColors.some(col => pColor.includes(col));
        if (!matchesColor) return false;
      }

      return true;
    });

    // Sorting
    if (currentSort === 'newest') {
      filtered.sort((a, b) => b.id - a.id);
    } else if (currentSort === 'price-asc') {
      filtered.sort((a, b) => a.price - b.price);
    } else if (currentSort === 'price-desc') {
      filtered.sort((a, b) => b.price - a.price);
    } else if (currentSort === 'discount') {
      filtered.sort((a, b) => (b.discount_pct || 0) - (a.discount_pct || 0));
    } else {
      // Default: preserve catalog order
    }

    // Update Counter in Toolbar
    const countEl = document.getElementById('catalogCountVal');
    if (countEl) {
      countEl.textContent = filtered.length;
    }
  };

  // Build Single Owen-Style Card DOM Element
  const createOwenCard = (product) => {
    const card = document.createElement('div');
    card.className = 'owen-product-card';

    const savedIds = Products.getSavedIds();
    const isSaved = savedIds.includes(product.id);
    const discountPct = product.discount_pct || (product.old_price && product.old_price > product.price ? Math.round((1 - product.price / product.old_price) * 100) : 0);
    const points = product.points || Math.max(10, Math.round(product.price / 30000));
    const colorHex = product.color_hex || '#8DA4B4';

    card.innerHTML = `
      <div class="owen-card-image-wrap" onclick="Products.navigate('/product/${product.id}')" title="Xem chi tiết ${product.name}">
        ${discountPct > 0 ? `<span class="owen-discount-badge">-${discountPct}%</span>` : ''}
        <button type="button" class="owen-wishlist-btn ${isSaved ? 'active' : ''}" data-id="${product.id}" aria-label="Lưu vào yêu thích" title="${isSaved ? 'Bỏ lưu' : 'Lưu vào yêu thích'}">
          <i class="${isSaved ? 'fa-solid fa-heart' : 'fa-regular fa-heart'}"></i>
        </button>
        <img src="${product.image_url || '/static/images/placeholder.jpg'}" alt="${product.name}" loading="lazy" onerror="this.onerror=null; this.src='/static/images/placeholder.jpg';">
      </div>
      <div class="owen-card-info">
        <div class="owen-color-swatches">
          <span class="owen-color-dot" style="background-color: ${colorHex};" title="${product.color || 'Màu tiêu chuẩn'}"></span>
        </div>
        <h4 class="owen-card-title" onclick="Products.navigate('/product/${product.id}')" title="${product.name}">
          ${product.name}
        </h4>
        <div class="owen-price-row">
          ${product.old_price && product.old_price > product.price ? `<span class="owen-old-price">${formatPrice(product.old_price)}</span>` : ''}
          <span class="owen-sale-price">${formatPrice(product.price)}</span>
        </div>
        <div class="owen-tags-row">
          <span class="owen-online-tag">Chỉ có tại Online</span>
          <span class="owen-points-tag">
            <i class="fa-solid fa-circle-info"></i> Tích lũy ${points} điểm
          </span>
        </div>
      </div>
    `;

    // Bind Wishlist Heart Toggle
    const heartBtn = card.querySelector('.owen-wishlist-btn');
    if (heartBtn) {
      heartBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        Products.toggleWishlist(product, heartBtn);
        // Toggle icon state immediately
        const nowSaved = Products.getSavedIds().includes(product.id);
        heartBtn.classList.toggle('active', nowSaved);
        const icon = heartBtn.querySelector('i');
        if (icon) {
          icon.className = nowSaved ? 'fa-solid fa-heart' : 'fa-regular fa-heart';
        }
      });
    }

    // Prefetch detail page on hover for instant loading
    card.addEventListener('mouseenter', () => {
      Products.prefetch(`/product/${product.id}`);
    }, { once: true });

    return card;
  };

  // Render Product Grid and Pagination
  const render = () => {
    const grid = document.getElementById('owenProductsGrid');
    const pagination = document.getElementById('catalogPagination');
    if (!grid) return;

    grid.innerHTML = '';

    // Handle Empty Search/Filter Result
    if (filtered.length === 0) {
      grid.innerHTML = `
        <div class="catalog-empty-state">
          <div class="catalog-empty-icon">
            <i class="fa-solid fa-box-open"></i>
          </div>
          <h3 class="catalog-empty-title">Không tìm thấy sản phẩm phù hợp</h3>
          <p class="catalog-empty-desc">Vui lòng thử bỏ chọn một số tiêu chí bộ lọc hoặc tìm kiếm danh mục khác.</p>
          <button type="button" class="btn-empty-reset" onclick="CatalogPage.resetFilters()">
            <i class="fa-solid fa-rotate-left"></i> Xóa tất cả bộ lọc
          </button>
        </div>
      `;
      if (pagination) pagination.innerHTML = '';
      return;
    }

    // Calculate Pagination (10 items / page)
    const totalPages = Math.ceil(filtered.length / pageSize) || 1;
    if (currentPage > totalPages) currentPage = totalPages;
    if (currentPage < 1) currentPage = 1;

    const startIndex = (currentPage - 1) * pageSize;
    const pagedProducts = filtered.slice(startIndex, startIndex + pageSize);

    // Append 10 cards to grid
    pagedProducts.forEach(p => {
      grid.appendChild(createOwenCard(p));
    });

    // Render Pagination Bar
    renderPagination(totalPages);
  };

  // Render Pagination Bar (‹ Trước, 1, 2, 3..., Sau ›)
  const renderPagination = (totalPages) => {
    const pagination = document.getElementById('catalogPagination');
    if (!pagination) return;

    pagination.innerHTML = '';

    // If only 1 page, hide pagination bar
    if (totalPages <= 1) {
      pagination.style.display = 'none';
      return;
    }
    pagination.style.display = 'flex';

    // Previous Button (‹)
    const prevBtn = document.createElement('button');
    prevBtn.type = 'button';
    prevBtn.className = `page-btn ${currentPage === 1 ? 'disabled' : ''}`;
    prevBtn.innerHTML = '<i class="fa-solid fa-angle-left"></i> &nbsp;Trước';
    prevBtn.title = 'Trang trước';
    prevBtn.addEventListener('click', () => {
      if (currentPage > 1) goToPage(currentPage - 1);
    });
    pagination.appendChild(prevBtn);

    // Page Number Buttons
    for (let i = 1; i <= totalPages; i++) {
      const pageBtn = document.createElement('button');
      pageBtn.type = 'button';
      pageBtn.className = `page-btn ${i === currentPage ? 'active' : ''}`;
      pageBtn.textContent = i;
      pageBtn.title = `Trang ${i}`;
      pageBtn.addEventListener('click', () => goToPage(i));
      pagination.appendChild(pageBtn);
    }

    // Next Button (›)
    const nextBtn = document.createElement('button');
    nextBtn.type = 'button';
    nextBtn.className = `page-btn ${currentPage === totalPages ? 'disabled' : ''}`;
    nextBtn.innerHTML = 'Sau &nbsp;<i class="fa-solid fa-angle-right"></i>';
    nextBtn.title = 'Trang sau';
    nextBtn.addEventListener('click', () => {
      if (currentPage < totalPages) goToPage(currentPage + 1);
    });
    pagination.appendChild(nextBtn);
  };

  // Navigate to Page X
  const goToPage = (pageNum) => {
    currentPage = pageNum;
    render();
    syncUrlParams();

    // Smooth scroll to top of catalog
    const toolbar = document.querySelector('.catalog-grid-toolbar');
    if (toolbar) {
      toolbar.scrollIntoView({ behavior: 'smooth', block: 'start' });
    } else {
      window.scrollTo({ top: 120, behavior: 'smooth' });
    }
  };

  return {
    init,
    toggleAccordion,
    toggleSidebar,
    setGridColumns,
    filterByCategory,
    toggleSizeFilter,
    toggleColorFilter,
    onFilterChange,
    onSortChange,
    resetFilters,
    goToPage
  };
})();

// Expose globally
window.CatalogPage = CatalogPage;


