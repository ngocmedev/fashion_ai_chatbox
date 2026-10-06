/**
 * FASHION. — Personal Stylist Chat Module
 * Conversational Social Stylist, Flask API integration, Style Matches, Quick Prompts
 * Isolated private chat history for logged-in users, guest chat mode
 */

const Chat = (() => {
  let conversationStream;
  let chatForm;
  let chatInput;
  let liveGrid;
  let popupCard;
  let bubbleLauncher;
  let bubbleTooltip;
  let currentUserName = null;

  const init = () => {
    conversationStream = document.getElementById('chatStream');
    chatForm = document.getElementById('chatForm');
    chatInput = document.getElementById('chatInput');
    liveGrid = document.getElementById('liveRecommendationsGrid');
    popupCard = document.getElementById('chatPopupCard');
    bubbleLauncher = document.getElementById('chatBubbleLauncher');
    bubbleTooltip = document.getElementById('bubbleHintTooltip');

    if (bubbleLauncher) {
      bubbleLauncher.addEventListener('click', toggleChat);
    }

    const btnClose = document.getElementById('btnCloseChatPopup');
    if (btnClose) {
      btnClose.addEventListener('click', closeChat);
    }

    if (!chatForm || !chatInput) return;

    chatForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const message = chatInput.value.trim();
      if (!message) return;
      sendMessage(message);
      chatInput.value = '';
    });

    // Reset Chat Session
    const resetBtn = document.getElementById('btnResetSession');
    if (resetBtn) {
      resetBtn.addEventListener('click', resetConversation);
    }

    // Load private user chat history or guest banner
    loadHistory();
  };

  const openChat = () => {
    if (!popupCard) return;
    popupCard.classList.remove('collapsed');
    popupCard.classList.add('expanded');
    if (bubbleTooltip) bubbleTooltip.style.display = 'none';
    if (chatInput) {
      setTimeout(() => chatInput.focus(), 150);
    }
    scrollToBottom();
  };

  const closeChat = () => {
    if (!popupCard) return;
    popupCard.classList.remove('expanded');
    popupCard.classList.add('collapsed');
  };

  const toggleChat = () => {
    if (!popupCard) return;
    if (popupCard.classList.contains('expanded')) {
      closeChat();
    } else {
      openChat();
    }
  };

  const getTimeString = () => {
    return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const formatChatTime = (ts) => {
    if (!ts) return getTimeString();
    try {
      const d = new Date(ts.replace(' ', 'T'));
      if (isNaN(d.getTime())) return ts;
      return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch (e) {
      return ts;
    }
  };

  // Append user message bubble
  const appendUserMessage = (text, timeStr = null) => {
    if (!conversationStream) return;
    const entry = document.createElement('div');
    entry.className = 'chat-entry user';
    entry.innerHTML = `
      <div class="bubble-text">${escapeHtml(text)}</div>
      <span class="chat-time-meta">${timeStr || getTimeString()}</span>
    `;
    conversationStream.appendChild(entry);
    scrollToBottom();
  };

  const showTyping = () => {
    if (!conversationStream) return null;
    const typingEntry = document.createElement('div');
    typingEntry.className = 'chat-entry stylist';
    typingEntry.id = 'activeTypingIndicator';
    typingEntry.innerHTML = `
      <div class="typing-box-social">
        <span class="typing-dot-subtle"></span>
        <span class="typing-dot-subtle"></span>
        <span class="typing-dot-subtle"></span>
      </div>
    `;
    conversationStream.appendChild(typingEntry);
    scrollToBottom();
    return typingEntry;
  };

  const removeTyping = () => {
    const el = document.getElementById('activeTypingIndicator');
    if (el) el.remove();
  };

  // Append Stylist response with optional Style Matches & In-line Compact Vertical Products
  const appendStylistResponse = (replyText, products = [], entities = {}, timeStr = null, updateLiveGrid = true) => {
    if (!conversationStream) return;
    const entry = document.createElement('div');
    entry.className = 'chat-entry stylist';
    if (products && products.length > 0) {
      entry.classList.add('has-products');
    }

    // Style match tags
    let styleMatchHtml = '';
    const styleTags = [];
    if (entities && entities.occasion) styleTags.push(entities.occasion.toUpperCase());
    if (entities && entities.category) styleTags.push(entities.category.toUpperCase());
    if (entities && entities.color) styleTags.push(`TÔN SẮC ${entities.color.toUpperCase()}`);
    if (entities && entities.max_price) styleTags.push(`GIÁ TỐT`);

    if (styleTags.length > 0) {
      styleMatchHtml = `
        <div class="style-match-container">
          <div class="style-match-label">Style Match</div>
          <div class="style-tags-wrap">
            ${styleTags.map(t => `<span class="style-pill">${t}</span>`).join('')}
          </div>
        </div>
      `;
    }

    entry.innerHTML = `
      <div class="bubble-text">
        <p>${formatMessage(replyText)}</p>
        ${styleMatchHtml}
      </div>
      <span class="chat-time-meta">${timeStr || getTimeString()}</span>
    `;

    // If products returned, append an in-line compact vertical product container inside stylist response
    if (products && products.length > 0 && typeof Products !== 'undefined') {
      const renderFn = Products.renderVerticalList || Products.renderCarousel;
      if (typeof renderFn === 'function') {
        const listEl = renderFn(products);
        if (listEl && listEl instanceof HTMLElement) {
          const bubble = entry.querySelector('.bubble-text');
          if (bubble) bubble.appendChild(listEl);
        }
      }
    }

    conversationStream.appendChild(entry);
    scrollToBottom();

    // Also update the Live Recommendations grid on the right side if live interaction
    if (updateLiveGrid && liveGrid && products && products.length > 0 && typeof Products !== 'undefined') {
      Products.renderGrid(liveGrid, products);
      const sectionMeta = document.getElementById('liveRecommendationsMeta');
      if (sectionMeta) {
        sectionMeta.textContent = `${products.length} items phù hợp nhất`;
      }
    }
  };

  // Load chat history from backend
  const loadHistory = async () => {
    if (!conversationStream) return;
    try {
      const res = await fetch('/api/chat/history');
      if (!res.ok) return;
      const data = await res.json();

      conversationStream.innerHTML = '';

      if (data.is_logged_in) {
        currentUserName = data.user_name || (window.CURRENT_USER ? window.CURRENT_USER.full_name : 'Bạn');
        
        // Private history badge
        const badge = document.createElement('div');
        badge.className = 'chat-session-badge';
        badge.innerHTML = `<i class="fa-solid fa-lock"></i> Lịch sử tư vấn riêng của <strong>${escapeHtml(currentUserName)}</strong>`;
        conversationStream.appendChild(badge);

        if (data.history && data.history.length > 0) {
          data.history.forEach(item => {
            if (item.user_message) {
              appendUserMessage(item.user_message, formatChatTime(item.time));
            }
            if (item.bot_response) {
              appendStylistResponse(item.bot_response, [], {}, formatChatTime(item.time), false);
            }
          });
        } else {
          const welcome = document.createElement('div');
          welcome.className = 'chat-entry stylist';
          welcome.innerHTML = `
            <div class="bubble-text">
              <p>Xin chào <strong>${escapeHtml(currentUserName)}</strong>! Toàn bộ lịch sử tư vấn outfit sẽ được lưu riêng cho tài khoản của bạn. Bạn đang cần gợi ý phong cách gì hôm nay? ✨</p>
            </div>
            <span class="chat-time-meta">Vừa xong</span>
          `;
          conversationStream.appendChild(welcome);
        }
      } else {
        // Guest mode banner
        const guestBadge = document.createElement('div');
        guestBadge.className = 'chat-guest-badge';
        guestBadge.innerHTML = `<i class="fa-regular fa-user"></i> Bạn đang chat dạng Khách &bull; <a href="/login?next=${encodeURIComponent(window.location.pathname)}">Đăng nhập</a> để lưu lịch sử riêng`;
        conversationStream.appendChild(guestBadge);

        const welcome = document.createElement('div');
        welcome.className = 'chat-entry stylist';
        welcome.innerHTML = `
          <div class="bubble-text">
            <p>Chào bạn! Mình là Stylist riêng của bạn tại Evern. Bạn đang tìm outfit cho dịp gì hoặc muốn thử phong cách nào hôm nay? 👀</p>
          </div>
          <span class="chat-time-meta">Vừa xong</span>
        `;
        conversationStream.appendChild(welcome);
      }
      scrollToBottom();
    } catch (err) {
      console.warn('Error loading chat history:', err);
    }
  };

  // Send message to Flask backend
  const sendMessage = async (messageText) => {
    appendUserMessage(messageText);
    const typing = showTyping();

    // Update state text if live recommendations area is visible
    const sectionMeta = document.getElementById('liveRecommendationsMeta');
    if (sectionMeta) {
      sectionMeta.textContent = 'Styling your picks...';
    }

    try {
      const payload = { message: messageText };
      if (window.CURRENT_PRODUCT_CONTEXT) {
        payload.current_product = window.CURRENT_PRODUCT_CONTEXT;
      }

      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      removeTyping();

      if (!response.ok) {
        throw new Error(`Server returned status ${response.status}`);
      }

      const data = await response.json();
      appendStylistResponse(data.reply, data.products || [], data.entities || {});
    } catch (error) {
      console.error('Chat error:', error);
      removeTyping();
      appendStylistResponse('Oops, stylist đang nghỉ một nhịp. Bạn thử gửi lại nhé! ✨', []);
      if (liveGrid && typeof UI !== 'undefined' && UI.renderErrorState) {
        UI.renderErrorState(liveGrid, () => sendMessage(messageText));
      }
    }
  };

  const sendPrompt = (promptText) => {
    openChat();
    if (!chatInput || !chatForm) return;
    chatInput.value = promptText;
    chatForm.dispatchEvent(new Event('submit'));
  };

  const resetConversation = async () => {
    if (!conversationStream) return;

    try {
      await fetch('/api/chat/clear', { method: 'POST' });
    } catch (e) {
      console.error('Error clearing chat history:', e);
    }

    conversationStream.innerHTML = '';

    if (window.IS_LOGGED_IN) {
      const name = currentUserName || (window.CURRENT_USER ? window.CURRENT_USER.full_name : 'Bạn');
      const badge = document.createElement('div');
      badge.className = 'chat-session-badge';
      badge.innerHTML = `<i class="fa-solid fa-lock"></i> Lịch sử tư vấn riêng của <strong>${escapeHtml(name)}</strong>`;
      conversationStream.appendChild(badge);
    } else {
      const guestBadge = document.createElement('div');
      guestBadge.className = 'chat-guest-badge';
      guestBadge.innerHTML = `<i class="fa-regular fa-user"></i> Bạn đang chat dạng Khách &bull; <a href="/login?next=${encodeURIComponent(window.location.pathname)}">Đăng nhập</a> để lưu lịch sử riêng`;
      conversationStream.appendChild(guestBadge);
    }

    const resetMsg = document.createElement('div');
    resetMsg.className = 'chat-entry stylist';
    resetMsg.innerHTML = `
      <div class="bubble-text">
        <p>Phiên tư vấn mới đã sẵn sàng! Bạn đang tìm trang phục đi đâu, hoặc muốn thử phong cách nào hôm nay? 🕶️</p>
      </div>
      <span class="chat-time-meta">Vừa xong</span>
    `;
    conversationStream.appendChild(resetMsg);
    scrollToBottom();

    if (typeof UI !== 'undefined' && UI.showToast) {
      UI.showToast('Đã làm mới phiên tư vấn', '✦');
    }
  };

  const scrollToBottom = () => {
    if (conversationStream) {
      conversationStream.scrollTop = conversationStream.scrollHeight;
    }
  };

  const escapeHtml = (str) => {
    return String(str).replace(/[&<>"']/g, (m) => ({
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#39;'
    })[m]);
  };

  const formatMessage = (text) => {
    if (!text) return '';
    let formatted = escapeHtml(text);

    // 1. Markdown headers (###, ##, #) -> Clean bold headings without symbols
    formatted = formatted.replace(/^(?:#{1,6})\s*(.+)$/gm, '<strong>$1</strong>');

    // 2. Horizontal dividers (---, ***, ___) -> Clean subtle divider
    formatted = formatted.replace(/^(?:[-*_]){3,}\s*$/gm, '<div class="chat-divider"></div>');

    // 3. Remove backticks and bold the content: `CODE` -> <strong>CODE</strong>
    formatted = formatted.replace(/`([^`]+)`/g, '<strong>$1</strong>');

    // 4. Double asterisks **bold** -> <strong>bold</strong>
    formatted = formatted.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');

    // 5. Bullet bold prefix: "* *Điểm nhấn:*" -> "• <strong>Điểm nhấn:</strong>"
    formatted = formatted.replace(/^\s*[\*\-]\s*\*(.+?)\*[:]/gm, '• <strong>$1:</strong>');
    formatted = formatted.replace(/\*([^*]+)\*/g, '<strong>$1</strong>');

    // 6. Auto-bold Product Price (e.g., "Giá: 290,000đ", "1.450.000đ")
    formatted = formatted.replace(/(Giá\s*[:]\s*)(?!<strong>)(\d{1,3}(?:[.,]\d{3})*(?:\s*đ|\s*VND|\s*k)?)/gi, '$1<strong>$2</strong>');

    // 7. Auto-bold Size specification (e.g., "Size: S, M, L, XL, XXL")
    formatted = formatted.replace(/(Size\s*[:]\s*)(?!<strong>)([^|\n\r<]+)/gi, (m, p1, p2) => {
      return p1 + '<strong>' + p2.trim() + '</strong> ';
    });

    // 8. Clean up bullet list prefixes (e.g. "- Item" or "* Item")
    formatted = formatted.replace(/^\s*[\*\-]\s+/gm, '• ');

    // 9. Strip any leftover stray markdown symbols (*, `, _)
    formatted = formatted.replace(/[*`_]/g, '');

    // 10. Convert newlines to clean <br>
    formatted = formatted.replace(/\n{3,}/g, '<br><br>');
    formatted = formatted.replace(/\n/g, '<br>');

    return formatted;
  };

  return {
    init,
    sendMessage,
    sendPrompt,
    resetConversation,
    loadHistory,
    openChat,
    closeChat,
    toggleChat
  };
})();
