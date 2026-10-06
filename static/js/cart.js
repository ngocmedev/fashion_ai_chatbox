/**
 * EVERN. — Shopping Cart Module
 * Persistent LocalStorage Cart, Drawer UI, Badge Counters, Quantity Steppers
 */

const Cart = (() => {
  const CART_KEY = 'evern_shopping_cart';
  const BUY_NOW_KEY = 'evern_buy_now_item';

  // Retrieve cart items from LocalStorage
  const getItems = () => {
    try {
      return JSON.parse(localStorage.getItem(CART_KEY)) || [];
    } catch {
      return [];
    }
  };

  // Retrieve Buy Now item (single-item checkout)
  const getBuyNowItem = () => {
    try {
      const data = localStorage.getItem(BUY_NOW_KEY);
      return data ? JSON.parse(data) : null;
    } catch {
      return null;
    }
  };

  // Set Buy Now item (does not affect normal cart)
  const setBuyNowItem = (product, size = 'L', color = 'Tiêu chuẩn', quantity = 1) => {
    const qty = Math.max(1, parseInt(quantity, 10) || 1);
    const item = {
      id: product.id,
      name: product.name,
      price: product.price,
      image_url: product.image_url,
      category: product.category,
      size: size || 'L',
      color: color || 'Tiêu chuẩn',
      quantity: qty
    };
    localStorage.setItem(BUY_NOW_KEY, JSON.stringify(item));
    return item;
  };

  // Update quantity of Buy Now item
  const updateBuyNowQty = (newQty) => {
    const item = getBuyNowItem();
    if (!item) return null;
    item.quantity = Math.max(1, parseInt(newQty, 10) || 1);
    localStorage.setItem(BUY_NOW_KEY, JSON.stringify(item));
    return item;
  };

  // Clear Buy Now item
  const clearBuyNowItem = () => {
    localStorage.removeItem(BUY_NOW_KEY);
  };

  // Save cart items and update UI
  const saveItems = (items) => {
    localStorage.setItem(CART_KEY, JSON.stringify(items));
    updateBadge();
    renderDrawer();
  };

  // Remove only specific purchased items from cart
  const removePurchasedItems = (purchasedItems = []) => {
    if (!purchasedItems || purchasedItems.length === 0) return;
    const items = getItems();
    const remaining = items.filter(cartItem => {
      return !purchasedItems.some(p => 
        p.id === cartItem.id && 
        (p.size || '').toUpperCase() === (cartItem.size || '').toUpperCase() && 
        (p.color || '').toLowerCase() === (cartItem.color || '').toLowerCase()
      );
    });
    saveItems(remaining);
  };

  // Get total count of all quantities
  const getCount = () => {
    const items = getItems();
    return items.reduce((total, item) => total + (item.quantity || 1), 0);
  };

  // Get total monetary amount
  const getTotal = () => {
    const items = getItems();
    return items.reduce((total, item) => total + (item.price * (item.quantity || 1)), 0);
  };

  // Format currency VND
  const formatVND = (num) => {
    return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(num || 0);
  };

  // Update badge in navbar
  const updateBadge = () => {
    const badge = document.getElementById('cartCountBadge');
    const drawerCount = document.getElementById('cartDrawerCount');
    const count = getCount();

    if (badge) {
      badge.textContent = count;
      badge.style.display = count > 0 ? 'flex' : 'none';
      if (count > 0) {
        badge.classList.add('animate-bounce');
        setTimeout(() => badge.classList.remove('animate-bounce'), 350);
      }
    }

    if (drawerCount) {
      drawerCount.textContent = count;
    }
  };

  // Add Item to Cart
  const addItem = (product, size = 'L', color = 'Kem', quantity = 1) => {
    if (!window.IS_LOGGED_IN) {
      if (typeof UI !== 'undefined' && UI.showToast) {
        UI.showToast('Vui lòng đăng nhập để thêm vào giỏ hàng!', '🔒');
      }
      setTimeout(() => {
        const nextUrl = window.location.pathname.startsWith('/product/') 
          ? window.location.pathname 
          : '/checkout';
        window.location.href = `/login?next=${encodeURIComponent(nextUrl)}`;
      }, 800);
      return;
    }

    const items = getItems();
    const qty = parseInt(quantity, 10) || 1;

    // Check if duplicate item (same product ID, size, and color)
    const existingIdx = items.findIndex(it => 
      it.id === product.id && 
      (it.size || '').toUpperCase() === (size || '').toUpperCase() && 
      (it.color || '').toLowerCase() === (color || '').toLowerCase()
    );

    if (existingIdx > -1) {
      items[existingIdx].quantity = (items[existingIdx].quantity || 1) + qty;
    } else {
      items.push({
        id: product.id,
        name: product.name,
        price: product.price,
        image_url: product.image_url,
        category: product.category,
        size: size || 'L',
        color: color || 'Kem',
        quantity: qty
      });
    }

    saveItems(items);

    if (typeof UI !== 'undefined' && UI.showToast) {
      UI.showToast(`Đã thêm ${qty}x ${product.name} vào giỏ hàng!`, '🛍️');
    }

    // Open Cart drawer after adding
    open();
  };

  // Add Item Silently without drawer/toast (used when guest initiates purchase flow)
  const addItemSilently = (product, size = 'L', color = 'Kem', quantity = 1) => {
    const items = getItems();
    const qty = parseInt(quantity, 10) || 1;
    const existingIdx = items.findIndex(it => 
      it.id === product.id && 
      (it.size || '').toUpperCase() === (size || '').toUpperCase() && 
      (it.color || '').toLowerCase() === (color || '').toLowerCase()
    );
    if (existingIdx > -1) {
      items[existingIdx].quantity = (items[existingIdx].quantity || 1) + qty;
    } else {
      items.push({
        id: product.id,
        name: product.name,
        price: product.price,
        image_url: product.image_url,
        category: product.category,
        size: size || 'L',
        color: color || 'Kem',
        quantity: qty
      });
    }
    saveItems(items);
  };

  // Update Item Quantity
  const updateQty = (idx, newQty) => {
    const items = getItems();
    if (idx < 0 || idx >= items.length) return;

    if (newQty <= 0) {
      removeItem(idx);
    } else {
      items[idx].quantity = newQty;
      saveItems(items);
    }
  };

  // Remove Item from Cart
  const removeItem = (idx) => {
    const items = getItems();
    if (idx < 0 || idx >= items.length) return;

    const removedName = items[idx].name;
    items.splice(idx, 1);
    saveItems(items);

    if (typeof UI !== 'undefined' && UI.showToast) {
      UI.showToast(`Đã bỏ ${removedName} khỏi giỏ hàng`, '🗑️');
    }
  };

  // Open Cart Drawer
  const open = () => {
    const backdrop = document.getElementById('cartDrawerBackdrop');
    if (backdrop) {
      backdrop.classList.add('open');
      renderDrawer();
    }
  };

  // Close Cart Drawer
  const close = () => {
    const backdrop = document.getElementById('cartDrawerBackdrop');
    if (backdrop) {
      backdrop.classList.remove('open');
    }
  };

  // Silky smooth navigation from Cart drawer to product detail
  const goToProduct = (e, url) => {
    if (e) {
      e.preventDefault();
      e.stopPropagation();
    }
    const panel = document.getElementById('cartDrawerPanel');
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

  // Render the Cart Drawer items list & subtotal
  const renderDrawer = () => {
    const container = document.getElementById('cartDrawerItems');
    const subtotalEl = document.getElementById('cartSubtotal');
    if (!container) return;

    const items = getItems();

    if (items.length === 0) {
      container.innerHTML = `
        <div class="cart-empty-state">
          <div class="cart-empty-icon">🛍️</div>
          <h4 class="cart-empty-title">Giỏ hàng của bạn đang trống</h4>
          <p class="cart-empty-sub">Hãy khám phá bộ sưu tập outfit phong cách mới nhất cùng Evern.</p>
          <a href="/#liveSection" class="btn-primary" onclick="Cart.close()" style="margin-top: 16px; display: inline-flex;">
            Khám phá sản phẩm ngay
          </a>
        </div>
      `;
    } else {
      container.innerHTML = items.map((item, idx) => `
        <div class="cart-item-card" onmouseenter="if (typeof Products !== 'undefined') Products.prefetch('/product/${item.id}')">
          <a href="/product/${item.id}" class="cart-item-thumb" onclick="Cart.goToProduct(event, '/product/${item.id}')">
            <img src="${item.image_url || '/static/images/placeholder.jpg'}" alt="${item.name}" loading="lazy" decoding="async" onerror="this.onerror=null; this.src='/static/images/placeholder.jpg';">
          </a>
          <div class="cart-item-details">
            <a href="/product/${item.id}" class="cart-item-name" onclick="Cart.goToProduct(event, '/product/${item.id}')">
              ${item.name}
            </a>
            <div class="cart-item-meta-tags">
              <span class="cart-meta-pill">Size: ${item.size}</span>
              <span class="cart-meta-pill">Màu: ${item.color}</span>
            </div>
            <div class="cart-item-price-row">
              <span class="cart-item-price">${formatVND(item.price * item.quantity)}</span>
              <div class="cart-item-stepper">
                <button type="button" class="btn-cart-step minus" onclick="Cart.updateQty(${idx}, ${item.quantity - 1})" aria-label="Giảm">−</button>
                <span class="cart-step-val">${item.quantity}</span>
                <button type="button" class="btn-cart-step plus" onclick="Cart.updateQty(${idx}, ${item.quantity + 1})" aria-label="Tăng">+</button>
              </div>
            </div>
          </div>
          <button type="button" class="btn-cart-remove" onclick="Cart.removeItem(${idx})" title="Xóa món đồ" aria-label="Xóa">
            <i class="fa-regular fa-trash-can"></i>
          </button>
        </div>
      `).join('');
    }

    if (subtotalEl) {
      subtotalEl.textContent = formatVND(getTotal());
    }
  };

  // Proceed to Checkout for Cart
  const checkout = () => {
    if (!window.IS_LOGGED_IN) {
      if (typeof UI !== 'undefined' && UI.showToast) {
        UI.showToast('Vui lòng đăng nhập để tiến hành mua hàng!', '🔒');
      }
      setTimeout(() => {
        window.location.href = '/login?next=' + encodeURIComponent('/checkout?mode=cart');
      }, 800);
      return;
    }

    const items = getItems();
    if (items.length === 0) {
      if (typeof UI !== 'undefined' && UI.showToast) {
        UI.showToast('Giỏ hàng trống! Vui lòng chọn sản phẩm trước.', '⚠️');
      }
      return;
    }

    window.location.href = '/checkout?mode=cart';
  };

  // Initialize listeners
  const init = () => {
    updateBadge();

    // Bind Cart open button in navbar
    const btnOpen = document.getElementById('btnOpenCart');
    if (btnOpen) {
      btnOpen.addEventListener('click', (e) => {
        e.preventDefault();
        open();
      });
    }

    // Bind Cart close button
    const btnClose = document.getElementById('btnCloseCart');
    if (btnClose) {
      btnClose.addEventListener('click', () => {
        close();
      });
    }

    // Close when clicking outside on backdrop
    const backdrop = document.getElementById('cartDrawerBackdrop');
    if (backdrop) {
      backdrop.addEventListener('click', (e) => {
        if (e.target === backdrop) {
          close();
        }
      });
    }
  };

  // Clear all items from cart
  const clearCart = () => {
    saveItems([]);
  };

  return {
    init,
    getItems,
    addItem,
    addItemSilently,
    updateQty,
    removeItem,
    clearCart,
    getTotal,
    getCount,
    open,
    close,
    renderDrawer,
    checkout,
    updateBadge,
    goToProduct,
    getBuyNowItem,
    setBuyNowItem,
    updateBuyNowQty,
    clearBuyNowItem,
    removePurchasedItems
  };
})();

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  Cart.init();
});
