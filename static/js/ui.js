/**
 * FASHION. — UI & Micro-interactions Helper
 * Toast notifications, Skeleton loaders, Empty/Error states, Modals
 */

const UI = (() => {
  // Format VND currency (e.g., 399.000₫)
  const formatVND = (amount) => {
    if (typeof amount !== 'number') {
      amount = parseInt(amount, 10) || 0;
    }
    return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(amount);
  };

  // Toast Notification System
  const showToast = (message, icon = '✦') => {
    let container = document.getElementById('toastContainer');
    if (!container) {
      container = document.createElement('div');
      container.id = 'toastContainer';
      container.className = 'toast-container';
      document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = 'toast-item';
    toast.innerHTML = `<span>${icon}</span><span>${message}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
      toast.classList.add('exit');
      setTimeout(() => toast.remove(), 220);
    }, 2800);
  };

  // Render Skeleton Loading for Products
  const renderProductSkeletons = (container, count = 3) => {
    if (!container) return;
    container.innerHTML = '';
    for (let i = 0; i < count; i++) {
      const card = document.createElement('div');
      card.className = 'skeleton-card';
      card.innerHTML = `
        <div class="skeleton-box skeleton-media"></div>
        <div class="skeleton-content">
          <div class="skeleton-box skeleton-line" style="width: 80%;"></div>
          <div class="skeleton-box skeleton-line price"></div>
          <div class="skeleton-box skeleton-line short"></div>
        </div>
      `;
      container.appendChild(card);
    }
  };

  // Render Friendly Gen Z Empty State
  const renderEmptyState = (container, message = 'Chưa tìm thấy item đúng vibe này.', subText = 'Thử nới ngân sách hoặc đổi style nhé.') => {
    if (!container) return;
    container.innerHTML = `
      <div style="grid-column: 1 / -1; padding: 48px 24px; text-align: center; background: #FFFFFF; border: 1px dashed var(--border-color); border-radius: var(--radius-xl);">
        <div style="font-size: 28px; margin-bottom: 12px;">👀</div>
        <h3 style="font-size: 16px; font-weight: 700; color: var(--text-primary); margin-bottom: 6px;">${message}</h3>
        <p style="font-size: 13.5px; color: var(--text-secondary); margin-bottom: 20px;">${subText}</p>
        <div style="display: flex; gap: 8px; justify-content: center; flex-wrap: wrap;">
          <button class="prompt-pill" onclick="Chat.sendPrompt('Tìm đồ dưới 500K')">💸 Dưới 500K</button>
          <button class="prompt-pill" onclick="Chat.sendPrompt('Gợi ý phong cách Casual')">👟 Casual</button>
          <button class="prompt-pill" onclick="Chat.sendPrompt('Outfit đi chơi cuối tuần')">✨ Đi chơi</button>
        </div>
      </div>
    `;
  };

  // Render Error State
  const renderErrorState = (container, retryCallback) => {
    if (!container) return;
    container.innerHTML = `
      <div style="grid-column: 1 / -1; padding: 40px 24px; text-align: center; background: #FFFFFF; border: 1px solid var(--border-color); border-radius: var(--radius-xl);">
        <div style="font-size: 26px; margin-bottom: 8px;">🛋️</div>
        <h3 style="font-size: 15px; font-weight: 700; color: var(--text-primary); margin-bottom: 4px;">Oops, stylist đang nghỉ một nhịp.</h3>
        <p style="font-size: 13px; color: var(--text-secondary); margin-bottom: 16px;">Thử gửi lại nhé hoặc kiểm tra kết nối mạng.</p>
        <button id="btnRetryLoad" class="btn-primary" style="padding: 9px 20px; font-size: 13px;">Thử lại</button>
      </div>
    `;

    const retryBtn = document.getElementById('btnRetryLoad');
    if (retryBtn && typeof retryCallback === 'function') {
      retryBtn.addEventListener('click', retryCallback);
    }
  };

  // Modal Handling - Owen / Atino Style Comprehensive Product Presentation
  const openProductModal = (product) => {
    const modal = document.getElementById('productModal');
    const modalBody = document.getElementById('modalBody');
    if (!modal || !modalBody) return;

    // Gallery images: Chỉ hiển thị hình ảnh thực của chính sản phẩm này
    let galleryImages = [];
    if (product.images) {
      try {
        const parsed = typeof product.images === 'string' ? JSON.parse(product.images) : product.images;
        if (Array.isArray(parsed) && parsed.length > 0) {
          galleryImages = parsed.filter(Boolean);
        }
      } catch (e) {
        galleryImages = String(product.images).split(',').map(s => s.trim()).filter(Boolean);
      }
    }
    if (!galleryImages.length && product.gallery_images && Array.isArray(product.gallery_images)) {
      galleryImages = product.gallery_images.filter(Boolean);
    }
    if (!galleryImages.length && product.image_url) {
      galleryImages = [product.image_url];
    }
    if (!galleryImages.length) {
      galleryImages = ['/static/images/placeholder.jpg'];
    }

    // Parse or generate available sizes
    let parsedSizes = ['2XL', 'XL', 'L', 'M'];
    if (product.sizes) {
      if (Array.isArray(product.sizes)) {
        parsedSizes = product.sizes;
      } else if (typeof product.sizes === 'string') {
        parsedSizes = product.sizes.split(',').map(s => s.trim().toUpperCase());
      }
    }

    // Colors matching the aesthetic
    const colorSwatches = [
      { name: 'Kem / Be', hex: '#E8DFD3', border: 'none' },
      { name: 'Trắng', hex: '#FDFDFD', border: '1px solid #D1D5DB' },
      { name: 'Đen', hex: '#1C1C1C', border: 'none' }
    ];

    const categoryCode = (product.category || 'SHIRT').toUpperCase();
    const productCode = `EVERN ${categoryCode} | ${product.id ? String(product.id).padStart(4, '0') : '4978'}`;

    // Store branch availability data
    const storeBranches = [
      { city: 'Hà Nội', name: 'L2-19 Vincom Ocean Park 1, HN, MB_CH38', phone: '0967284444', detail: 'L2-19/VMM Ocean Park 1, HN', stock: 'Còn hàng' },
      { city: 'Hà Nội', name: 'L2-24 Vincom Smart City, HN, MB_CH39', phone: '0967284444', detail: 'L2-24 Vincom Smart City, Đại Mỗ', stock: 'Còn hàng' },
      { city: 'Hà Nội', name: 'Tòa nhà Viwaseen, 48 Phố Tố Hữu, Nam Từ Liêm', phone: '1900 8079', detail: 'Tầng 17 Viwaseen, Nam Từ Liêm', stock: 'Còn hàng' },
      { city: 'TP.HCM', name: '186A Nam Kỳ Khởi Nghĩa, Phường Xuân Hòa, Q.3', phone: '0967284444', detail: '186A Nam Kỳ Khởi Nghĩa, TP.HCM', stock: 'Còn hàng' },
      { city: 'Đà Nẵng', name: 'Vincom Plaza Ngô Quyền, Sơn Trà, Đà Nẵng', phone: '0912345678', detail: 'Tầng 1 Vincom Plaza, Đà Nẵng', stock: 'Còn hàng' }
    ];

    let currentImgIdx = 0;
    let selectedQty = 1;
    let selectedSize = parsedSizes[parsedSizes.length > 2 ? 2 : 0] || 'L';
    let selectedColor = colorSwatches[0].name;

    modalBody.innerHTML = `
      <div class="pdp-container">
        <!-- LEFT: GALLERY AREA -->
        <div class="pdp-gallery-wrap">
          <!-- Thumbnails Strip (Chỉ hiển thị khi có > 1 ảnh) -->
          <div class="pdp-thumbs-col" style="${galleryImages.length <= 1 ? 'display: none;' : ''}">
            <button class="pdp-thumb-arrow" id="btnThumbUp" title="Ảnh trước">
              <i class="fa-solid fa-angle-up"></i>
            </button>
            <div class="pdp-thumb-list-wrap" id="pdpThumbList">
              ${galleryImages.map((img, idx) => `
                <div class="pdp-thumb-item ${idx === 0 ? 'active' : ''}" data-index="${idx}">
                  <img src="${img}" alt="Thumbnail ${idx + 1}" loading="lazy" onerror="this.onerror=null; this.src='/static/images/placeholder.jpg';">
                </div>
              `).join('')}
            </div>
            <button class="pdp-thumb-arrow" id="btnThumbDown" title="Ảnh tiếp theo">
              <i class="fa-solid fa-angle-down"></i>
            </button>
          </div>

          <!-- Main Stage Box -->
          <div class="pdp-main-stage" style="${galleryImages.length <= 1 ? 'width: 100%;' : ''}">
            <div class="pdp-main-stage-box">
              <div class="pdp-watermark">Evern</div>
              
              <!-- Next / Prev Chevrons -->
              ${galleryImages.length > 1 ? `
              <button class="pdp-nav-chevron prev" id="btnPdpPrev" aria-label="Xem ảnh trước">
                <i class="fa-solid fa-angle-left"></i>
              </button>` : ''}
              
              <div class="pdp-main-img-holder">
                <img id="pdpMainImg" src="${galleryImages[0]}" alt="${product.name}" onerror="this.onerror=null; this.src='/static/images/placeholder.jpg';">
              </div>

              ${galleryImages.length > 1 ? `
              <button class="pdp-nav-chevron next" id="btnPdpNext" aria-label="Xem ảnh kế tiếp">
                <i class="fa-solid fa-angle-right"></i>
              </button>` : ''}

              <div class="pdp-product-code-tag">${productCode}</div>
            </div>

            <!-- Click to zoom hint -->
            <div class="pdp-zoom-link" id="btnZoomHint">
              <i class="fa-solid fa-magnifying-glass"></i>
              <span>Click xem hình lớn hơn</span>
            </div>
          </div>
        </div>

        <!-- RIGHT: PRODUCT DETAILS & ACTIONS -->
        <div class="pdp-info-col">
          <h1 class="pdp-title">${product.name}</h1>
          <div class="pdp-status-stock">Còn hàng</div>
          
          <div class="pdp-divider-dotted"></div>

          <div class="pdp-price">${formatVND(product.price)}</div>

          <!-- COLOR SELECTION -->
          <div class="pdp-subheading">MÀU SẮC</div>
          <div class="pdp-colors-wrap" id="pdpColorsWrap">
            ${colorSwatches.map((c, i) => `
              <div class="pdp-color-swatch ${i === 0 ? 'active' : ''}" 
                   style="background: ${c.hex}; border: ${c.border};" 
                   data-name="${c.name}" 
                   title="Màu ${c.name}">
              </div>
            `).join('')}
          </div>

          <!-- SIZE SELECTION -->
          <div class="pdp-size-header-row">
            <span class="pdp-subheading" style="margin-bottom: 0;">KÍCH THƯỚC</span>
            <span class="pdp-size-guide-btn" id="btnSizeGuide">Hướng Dẫn Chọn Size</span>
          </div>
          <div class="pdp-sizes-row" id="pdpSizesWrap">
            ${parsedSizes.map((s, i) => `
              <button type="button" class="pdp-size-box ${s === selectedSize ? 'active' : ''}" data-size="${s}">
                ${s}
              </button>
            `).join('')}
          </div>

          <!-- QUANTITY STEPPER -->
          <div class="pdp-qty-stepper">
            <button type="button" class="pdp-qty-btn" id="btnQtyMinus">−</button>
            <input type="text" class="pdp-qty-input" id="pdpQtyInput" value="1" readonly>
            <button type="button" class="pdp-qty-btn" id="btnQtyPlus">+</button>
          </div>

          <!-- ACTION BUTTONS -->
          <div class="pdp-action-buttons">
            <button type="button" class="btn-pdp-cart" id="btnPdpAddToCart">
              THÊM VÀO GIỎ HÀNG
            </button>
            <button type="button" class="btn-pdp-buy" id="btnPdpBuyNow">
              MUA NGAY
            </button>
          </div>

          <!-- WISHLIST -->
          <button type="button" class="btn-pdp-wishlist" id="btnPdpWishlist">
            <i class="fa-regular fa-heart"></i>
            <span>YÊU THÍCH</span>
          </button>

          <!-- SHARE -->
          <div class="pdp-share-row">
            <span>CHIA SẺ</span>
            <a href="https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(window.location.href)}" 
               target="_blank" rel="noopener" class="pdp-fb-circle" title="Chia sẻ Facebook">
              <i class="fa-brands fa-facebook-f"></i>
            </a>
          </div>

          <!-- STORE AVAILABILITY BOX -->
          <div class="pdp-stores-box">
            <div class="pdp-stores-header">Cửa hàng còn sản phẩm này</div>
            <div class="pdp-stores-select-wrap">
              <select class="pdp-stores-select" id="pdpCitySelect">
                <option value="all">- Tỉnh thành -</option>
                <option value="Hà Nội" selected>Hà Nội</option>
                <option value="TP.HCM">TP. Hồ Chí Minh</option>
                <option value="Đà Nẵng">Đà Nẵng</option>
              </select>
            </div>
            <div class="pdp-stores-list" id="pdpStoresList">
              <!-- Rendered via JS -->
            </div>
          </div>
        </div>
      </div>
    `;

    // Bind Gallery thumbnail click & navigation
    const mainImgEl = document.getElementById('pdpMainImg');
    const thumbEls = modalBody.querySelectorAll('.pdp-thumb-item');

    const updateActiveImage = (idx) => {
      currentImgIdx = (idx + galleryImages.length) % galleryImages.length;
      mainImgEl.style.opacity = '0.3';
      setTimeout(() => {
        mainImgEl.src = galleryImages[currentImgIdx];
        mainImgEl.style.opacity = '1';
      }, 100);
      thumbEls.forEach((th, i) => {
        th.classList.toggle('active', i === currentImgIdx);
      });
    };

    thumbEls.forEach((th) => {
      th.addEventListener('click', () => {
        const idx = parseInt(th.dataset.index, 10);
        updateActiveImage(idx);
      });
    });

    const btnPrev = document.getElementById('btnPdpPrev');
    const btnNext = document.getElementById('btnPdpNext');
    if (btnPrev) btnPrev.addEventListener('click', () => updateActiveImage(currentImgIdx - 1));
    if (btnNext) btnNext.addEventListener('click', () => updateActiveImage(currentImgIdx + 1));

    const btnThumbUp = document.getElementById('btnThumbUp');
    const btnThumbDown = document.getElementById('btnThumbDown');
    if (btnThumbUp) btnThumbUp.addEventListener('click', () => updateActiveImage(currentImgIdx - 1));
    if (btnThumbDown) btnThumbDown.addEventListener('click', () => updateActiveImage(currentImgIdx + 1));

    // Zoom hint
    const btnZoom = document.getElementById('btnZoomHint');
    if (btnZoom) {
      btnZoom.addEventListener('click', () => {
        window.open(galleryImages[currentImgIdx], '_blank');
      });
    }

    // Color swatches click
    const swatches = modalBody.querySelectorAll('.pdp-color-swatch');
    swatches.forEach(sw => {
      sw.addEventListener('click', () => {
        swatches.forEach(s => s.classList.remove('active'));
        sw.classList.add('active');
        selectedColor = sw.dataset.name;
        showToast(`Đã chọn màu: ${selectedColor}`, '✦');
      });
    });

    // Sizes click
    const sizeBtns = modalBody.querySelectorAll('.pdp-size-box');
    sizeBtns.forEach(sb => {
      sb.addEventListener('click', () => {
        sizeBtns.forEach(b => b.classList.remove('active'));
        sb.classList.add('active');
        selectedSize = sb.dataset.size;
        showToast(`Đã chọn kích cỡ: ${selectedSize}`, '📏');
      });
    });

    // Size guide link
    const btnSizeGuide = document.getElementById('btnSizeGuide');
    if (btnSizeGuide) {
      btnSizeGuide.addEventListener('click', () => {
        showToast('Bảng size: S (45-55kg) · M (55-65kg) · L (65-75kg) · XL (75-85kg) · 2XL (>85kg)', '📏');
      });
    }

    // Quantity stepper
    const qtyInput = document.getElementById('pdpQtyInput');
    const btnQtyMinus = document.getElementById('btnQtyMinus');
    const btnQtyPlus = document.getElementById('btnQtyPlus');

    if (btnQtyMinus && qtyInput) {
      btnQtyMinus.addEventListener('click', () => {
        if (selectedQty > 1) {
          selectedQty--;
          qtyInput.value = selectedQty;
        }
      });
    }

    if (btnQtyPlus && qtyInput) {
      btnQtyPlus.addEventListener('click', () => {
        selectedQty++;
        qtyInput.value = selectedQty;
      });
    }

    // Add to cart & Buy now
    const btnCart = document.getElementById('btnPdpAddToCart');
    if (btnCart) {
      btnCart.addEventListener('click', () => {
        if (typeof Cart !== 'undefined') {
          Cart.addItem(product, selectedSize, selectedColor, selectedQty);
        } else {
          showToast(`Đã thêm ${selectedQty}x ${product.name} (Size ${selectedSize}, Màu ${selectedColor}) vào giỏ hàng!`, '🛍️');
        }
        closeProductModal();
      });
    }

    const btnBuy = document.getElementById('btnPdpBuyNow');
    if (btnBuy) {
      btnBuy.addEventListener('click', () => {
        if (typeof Cart !== 'undefined') {
          Cart.setBuyNowItem(product, selectedSize, selectedColor, selectedQty);
        }
        closeProductModal();
        if (!window.IS_LOGGED_IN) {
          showToast('Vui lòng đăng nhập để tiến hành mua ngay!', '🔒');
          setTimeout(() => {
            window.location.href = `/login?next=${encodeURIComponent('/checkout?mode=buy_now')}`;
          }, 800);
          return;
        }
        window.location.href = '/checkout?mode=buy_now';
      });
    }

    // Wishlist button
    const btnWishlist = document.getElementById('btnPdpWishlist');
    if (btnWishlist) {
      let isFav = false;
      if (typeof Products !== 'undefined' && Products.getSavedIds) {
        isFav = Products.getSavedIds().includes(product.id);
      }
      if (isFav) btnWishlist.classList.add('active');

      btnWishlist.addEventListener('click', () => {
        if (typeof Products !== 'undefined' && Products.toggleWishlist) {
          const fakeBtn = document.createElement('button');
          Products.toggleWishlist(product, fakeBtn);
          btnWishlist.classList.toggle('active');
        } else {
          btnWishlist.classList.toggle('active');
          showToast('Đã cập nhật danh sách yêu thích!', '♥');
        }
      });
    }

    // Render Store Availability List
    const storesListEl = document.getElementById('pdpStoresList');
    const citySelect = document.getElementById('pdpCitySelect');

    const renderStores = (filterCity) => {
      if (!storesListEl) return;
      const filtered = (filterCity === 'all' || !filterCity)
        ? storeBranches
        : storeBranches.filter(b => b.city.includes(filterCity) || filterCity.includes(b.city));

      storesListEl.innerHTML = filtered.map(b => `
        <div class="pdp-store-item">
          <div class="pdp-store-name">
            <i class="fa-solid fa-location-dot" style="font-size: 11px; margin-top: 3px; color: #111;"></i>
            <span>${b.name}</span>
          </div>
          <div class="pdp-store-phone">${b.phone}</div>
          <div class="pdp-store-stock">
            ${b.detail} <span class="stock-green">(${b.stock})</span>
          </div>
        </div>
      `).join('');
    };

    renderStores('Hà Nội');

    if (citySelect) {
      citySelect.addEventListener('change', (e) => {
        renderStores(e.target.value);
      });
    }

    // Open Modal
    modal.classList.add('open');
  };

  const closeProductModal = () => {
    const modal = document.getElementById('productModal');
    if (modal) modal.classList.remove('open');
  };


  // Sticky Header Scroll Effect (Throttled with requestAnimationFrame to prevent scroll jank)
  const initHeaderScroll = () => {
    const header = document.querySelector('.site-header');
    if (!header) return;

    let isScrolled = false;
    let ticking = false;

    window.addEventListener('scroll', () => {
      if (!ticking) {
        window.requestAnimationFrame(() => {
          const shouldScroll = window.scrollY > 30;
          if (shouldScroll !== isScrolled) {
            isScrolled = shouldScroll;
            header.classList.toggle('scrolled', isScrolled);
          }
          ticking = false;
        });
        ticking = true;
      }
    }, { passive: true });
  };

  // Ambient Scroll-to-Play Video Controller (Owen.vn inspired)
  // When scrolled into view: restarts from 0 and plays automatically
  // When scrolled away: pauses
  // When scrolled back: restarts from beginning (currentTime = 0) and plays
  const initScrollAutoplayVideos = () => {
    const videos = document.querySelectorAll('.ambient-scroll-video');
    if (!videos.length) return;

    // Ensure all videos start muted and paused
    videos.forEach((vid) => {
      vid.muted = true;
      try {
        vid.pause();
      } catch (e) {}
    });

    if ('IntersectionObserver' in window) {
      const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
          const video = entry.target;
          if (entry.isIntersecting) {
            // When scrolled into view: restart from beginning and play
            try {
              video.currentTime = 0;
            } catch (e) {}
            const playPromise = video.play();
            if (playPromise !== undefined) {
              playPromise.catch((err) => {
                console.log('Autoplay deferred by browser policy:', err);
              });
            }
          } else {
            // When scrolled away: pause the video
            video.pause();
          }
        });
      }, {
        threshold: 0.25 // Activates when 25% or more of the video area is visible
      });

      videos.forEach((video) => observer.observe(video));
    } else {
      videos.forEach((vid) => vid.play().catch(() => {}));
    }
  };

  // Ambient Hero Slider Controller (Hardware Accelerated & Buttery-Smooth)
  // Dual-buffered GPU cross-fading backdrop (Image 3) + glassic navigation (Image 2) + auto-slideshow
  const initHeroSlider = () => {
    const sliderTrack = document.getElementById('heroSliderTrack');
    const layerA = document.getElementById('sliderBackdropA');
    const layerB = document.getElementById('sliderBackdropB');
    const slides = document.querySelectorAll('.slider-slide');
    const dots = document.querySelectorAll('.slider-dot');
    const btnPrev = document.getElementById('btnSliderPrev');
    const btnNext = document.getElementById('btnSliderNext');
    const frame = document.querySelector('.slider-frame-bordered');

    if (!sliderTrack || !slides.length) return;

    let currentIndex = 0;
    let autoplayTimer = null;
    let activeLayerIsA = true;
    const totalSlides = slides.length;

    // Cross-fade dual backdrop layers smoothly on GPU compositor thread
    const updateBackdrop = (imgUrl) => {
      if (!imgUrl) return;
      if (!layerA && !layerB) {
        // Fallback if single container exists
        const singleBackdrop = document.getElementById('sliderBackdrop');
        if (singleBackdrop) singleBackdrop.style.backgroundImage = `url('${imgUrl}')`;
        return;
      }
      
      const incoming = activeLayerIsA ? layerB : layerA;
      const outgoing = activeLayerIsA ? layerA : layerB;
      if (incoming && outgoing) {
        incoming.style.backgroundImage = `url('${imgUrl}')`;
        incoming.classList.add('active');
        outgoing.classList.remove('active');
        activeLayerIsA = !activeLayerIsA;
      }
    };

    const updateSlider = (index) => {
      currentIndex = (index + totalSlides) % totalSlides;

      // Translate track smoothly with GPU acceleration
      sliderTrack.style.transform = `translate3d(-${currentIndex * 100}%, 0, 0)`;

      // Update active slide class
      slides.forEach((s, idx) => {
        s.classList.toggle('active', idx === currentIndex);
      });

      // Update dots
      dots.forEach((d, idx) => {
        d.classList.toggle('active', idx === currentIndex);
      });

      // Update synchronized ambient blurred backdrop cross-fade
      const bgUrl = slides[currentIndex].dataset.bg;
      if (bgUrl) {
        updateBackdrop(bgUrl);
      }
    };

    const nextSlide = () => updateSlider(currentIndex + 1);
    const prevSlide = () => updateSlider(currentIndex - 1);

    const startAutoplay = () => {
      stopAutoplay();
      autoplayTimer = setInterval(nextSlide, 4500);
    };

    const stopAutoplay = () => {
      if (autoplayTimer) {
        clearInterval(autoplayTimer);
        autoplayTimer = null;
      }
    };

    if (btnNext) {
      btnNext.addEventListener('click', (e) => {
        e.preventDefault();
        nextSlide();
        startAutoplay();
      });
    }

    if (btnPrev) {
      btnPrev.addEventListener('click', (e) => {
        e.preventDefault();
        prevSlide();
        startAutoplay();
      });
    }

    dots.forEach((dot) => {
      dot.addEventListener('click', (e) => {
        e.preventDefault();
        const idx = parseInt(dot.dataset.index, 10);
        if (!isNaN(idx)) {
          updateSlider(idx);
          startAutoplay();
        }
      });
    });

    if (frame) {
      frame.addEventListener('mouseenter', stopAutoplay);
      frame.addEventListener('mouseleave', startAutoplay);

      let touchStartX = 0;
      let touchEndX = 0;

      frame.addEventListener('touchstart', (e) => {
        touchStartX = e.changedTouches[0].screenX;
        stopAutoplay();
      }, { passive: true });

      frame.addEventListener('touchend', (e) => {
        touchEndX = e.changedTouches[0].screenX;
        if (touchStartX - touchEndX > 45) {
          nextSlide();
        } else if (touchEndX - touchStartX > 45) {
          prevSlide();
        }
        startAutoplay();
      }, { passive: true });
    }

    // Set initial backdrop and kick off autoplay
    updateSlider(0);
    startAutoplay();
  };

  return {
    formatVND,
    showToast,
    renderProductSkeletons,
    renderEmptyState,
    renderErrorState,
    openProductModal,
    closeProductModal,
    initHeaderScroll,
    initScrollAutoplayVideos,
    initHeroSlider
  };
})();
