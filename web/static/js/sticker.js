/**
 * TAIO Cover Studio — Sticker Direct Manipulation (Sticker Logo)
 * Tuân thủ Direct Manipulation & Fitts's Law
 * - 1 ngón / chuột: kéo để di chuyển (kèm Smart Guides hít 8px)
 * - 2 ngón: pinch để phóng to/thu nhỏ, xoay hai ngón để xoay
 * - Tay cầm góc: đổi cỡ (≥ 44×44px touch target)
 * - Tay cầm tròn đỉnh: xoay (Shift để nhảy bước 15°)
 * - Phím mũi tên: dịch 1px (Shift + mũi tên: 10px) theo khung xuất
 * - Chạm đúp / double click: khôi phục mặc định mẫu
 * - Bảng số chính xác & lưới 9 vị trí nhanh lề 5%
 * - Vùng an toàn nền tảng (TikTok, Reels, Shorts)
 * - Nhớ vị trí theo mẫu bằng localStorage
 */

(function () {
  "use strict";

  const SNAP_THRESHOLD_PX = 8;
  const SAFE_MARGIN = 0.05; // 5% lề an toàn

  let wrapperEl = null;
  let previewImgEl = null;
  let stageEl = null;
  let stickerEl = null;
  let stickerImgEl = null;
  let safeZoneOverlayEl = null;

  // Guide lines DOM
  let guideCenterXEl = null;
  let guideCenterYEl = null;
  let guideMarginLeftEl = null;
  let guideMarginRightEl = null;
  let guideMarginTopEl = null;
  let guideMarginBottomEl = null;

  // Numeric inputs DOM
  let numXEl = null;
  let numYEl = null;
  let numWEl = null;
  let numRotEl = null;
  let numOpacityEl = null;
  let chkPillEl = null;
  let chkHideEl = null;
  let chkShowSafeZoneEl = null;
  let selSafePlatformEl = null;

  // State
  let currentTemplate = null;
  let currentLogoId = null;
  let brandColors = null;
  let safeZonesConfig = null;
  let onOverridesChangedCallback = null;

  const stickerState = {
    x: 0.82,
    y: 0.06,
    w: 0.22,
    rotation: 0,
    opacity: 1.0,
    visible: true,
    pill: true,
    aspectRatio: 0.25, // height / width
  };

  let templateDefaults = { ...stickerState };

  // Pointer tracking
  let isDragging = false;
  let transformMode = "idle"; // 'idle' | 'move' | 'resize' | 'rotate' | 'pinch'
  let activeHandle = null;
  const activePointers = new Map();
  let dragStartPointer = { x: 0, y: 0 };
  let dragStartState = { ...stickerState };
  let initialPinchDistance = 0;
  let initialPinchAngle = 0;
  let initialPinchW = 0.22;
  let initialPinchRot = 0;
  let lastTapTime = 0;

  // Debounce preview timer
  let changeDebounceTimer = null;

  // Canvas bounds cache
  let canvasRect = { left: 0, top: 0, width: 1, height: 1, canvasW: 1080, canvasH: 1920 };

  /**
   * Tính toán hình chữ nhật hiển thị thực tế của preview canvas bên trong previewWrapper
   * (Tuân theo object-fit: contain của previewImage)
   */
  function updateCanvasBounds() {
    if (!wrapperEl) return canvasRect;
    const wrapRect = wrapperEl.getBoundingClientRect();
    if (!previewImgEl || previewImgEl.hidden || !previewImgEl.naturalWidth || !previewImgEl.naturalHeight) {
      canvasRect = {
        left: wrapRect.left,
        top: wrapRect.top,
        width: wrapRect.width,
        height: wrapRect.height,
        canvasW: 1080,
        canvasH: 1920,
      };
      if (stageEl) {
        stageEl.style.left = "0px";
        stageEl.style.top = "0px";
        stageEl.style.width = wrapRect.width + "px";
        stageEl.style.height = wrapRect.height + "px";
      }
      return canvasRect;
    }

    const naturalW = previewImgEl.naturalWidth;
    const naturalH = previewImgEl.naturalHeight;
    const naturalAspect = naturalW / naturalH;
    const wrapAspect = wrapRect.width / wrapRect.height;

    let renderW, renderH, offsetLeft, offsetTop;
    if (wrapAspect > naturalAspect) {
      // Chiều cao là giới hạn
      renderH = wrapRect.height;
      renderW = renderH * naturalAspect;
      offsetTop = 0;
      offsetLeft = (wrapRect.width - renderW) / 2;
    } else {
      // Chiều rộng là giới hạn
      renderW = wrapRect.width;
      renderH = renderW / naturalAspect;
      offsetLeft = 0;
      offsetTop = (wrapRect.height - renderH) / 2;
    }

    canvasRect = {
      left: wrapRect.left + offsetLeft,
      top: wrapRect.top + offsetTop,
      width: Math.max(renderW, 10),
      height: Math.max(renderH, 10),
      canvasW: naturalW,
      canvasH: naturalH,
    };

    if (stageEl) {
      stageEl.style.left = offsetLeft + "px";
      stageEl.style.top = offsetTop + "px";
      stageEl.style.width = canvasRect.width + "px";
      stageEl.style.height = canvasRect.height + "px";
    }

    renderStickerDOM();
    updateSafeZonesDOM();
    return canvasRect;
  }

  /**
   * Chuyển đổi toạ độ màn hình (screen clientX, clientY) sang toạ độ tỉ lệ chuẩn hoá (0..1)
   */
  function screenToNormalized(clientX, clientY) {
    const normX = (clientX - canvasRect.left) / canvasRect.width;
    const normY = (clientY - canvasRect.top) / canvasRect.height;
    return {
      x: Math.max(-0.5, Math.min(1.5, normX)),
      y: Math.max(-0.5, Math.min(1.5, normY)),
    };
  }

  /**
   * Chuyển đổi toạ độ tỉ lệ chuẩn hoá (0..1) sang toạ độ màn hình
   */
  function normalizedToScreen(normX, normY) {
    return {
      x: canvasRect.left + normX * canvasRect.width,
      y: canvasRect.top + normY * canvasRect.height,
    };
  }

  /**
   * Khôi phục hoặc tính toán vị trí mặc định từ template
   */
  function resolveTemplateDefault(template) {
    if (!template || !template.layers) {
      return { x: 0.82, y: 0.06, w: 0.22, rotation: 0, opacity: 1.0, visible: true, pill: true };
    }
    const logoLayer = template.layers.find((l) => l.type === "logo" || l.id === "logo");
    if (!logoLayer) {
      return { x: 0.82, y: 0.06, w: 0.22, rotation: 0, opacity: 1.0, visible: false, pill: true };
    }

    const scale = logoLayer.scale || 0.22;
    const pill = logoLayer.pill !== undefined ? Boolean(logoLayer.pill) : true;

    if (logoLayer.pos === "custom" && logoLayer.x !== undefined && logoLayer.y !== undefined) {
      return {
        x: Number(logoLayer.x),
        y: Number(logoLayer.y),
        w: scale,
        rotation: 0,
        opacity: 1.0,
        visible: true,
        pill: pill,
      };
    }

    if (logoLayer.pos === "top-right") {
      const marginR = logoLayer.margin_right !== undefined ? logoLayer.margin_right : 0.04;
      const topY = logoLayer.y !== undefined ? logoLayer.y : 0.04;
      return {
        x: 1.0 - marginR - scale / 2,
        y: topY + 0.035,
        w: scale,
        rotation: 0,
        opacity: 1.0,
        visible: true,
        pill: pill,
      };
    }

    return {
      x: 0.5,
      y: 0.65,
      w: scale,
      rotation: 0,
      opacity: 1.0,
      visible: true,
      pill: pill,
    };
  }

  /**
   * Nạp ảnh khối logo transparent RGBA từ máy chủ
   */
  async function loadStickerImage() {
    if (!currentTemplate) return;
    const tplId = currentTemplate.id;
    const logoId = currentLogoId || "";
    const pill = stickerState.pill ? "1" : "0";
    const url = `/api/layer-image?template=${encodeURIComponent(tplId)}&layer=logo&logo_id=${encodeURIComponent(logoId)}&pill=${pill}&t=${Date.now()}`;

    try {
      const img = new Image();
      img.crossOrigin = "anonymous";
      img.onload = () => {
        if (img.naturalWidth && img.naturalHeight) {
          stickerState.aspectRatio = img.naturalHeight / img.naturalWidth;
        }
        if (stickerImgEl) {
          stickerImgEl.src = img.src;
        }
        renderStickerDOM();
      };
      img.src = url;
    } catch (e) {
      console.warn("Không thể tải sticker logo layer:", e);
    }
  }

  /**
   * Lưu / Đọc vị trí từ localStorage theo từng mẫu
   */
  function saveToLocalStorage() {
    if (!currentTemplate) return;
    try {
      const key = `taio_sticker_overrides_${currentTemplate.id}`;
      localStorage.setItem(key, JSON.stringify({
        x: stickerState.x,
        y: stickerState.y,
        w: stickerState.w,
        rotation: stickerState.rotation,
        opacity: stickerState.opacity,
        visible: stickerState.visible,
        pill: stickerState.pill,
      }));
    } catch (_) {}
  }

  function loadFromLocalStorage() {
    if (!currentTemplate) return false;
    try {
      const key = `taio_sticker_overrides_${currentTemplate.id}`;
      const raw = localStorage.getItem(key);
      if (raw) {
        const data = JSON.parse(raw);
        if (typeof data.x === "number" && typeof data.y === "number") {
          stickerState.x = Math.max(0, Math.min(1, data.x));
          stickerState.y = Math.max(0, Math.min(1, data.y));
          stickerState.w = Math.max(0.05, Math.min(1.0, data.w || 0.22));
          stickerState.rotation = Math.max(-180, Math.min(180, data.rotation || 0));
          stickerState.opacity = Math.max(0, Math.min(1.0, data.opacity !== undefined ? data.opacity : 1.0));
          stickerState.visible = data.visible !== undefined ? Boolean(data.visible) : true;
          stickerState.pill = data.pill !== undefined ? Boolean(data.pill) : true;
          return true;
        }
      }
    } catch (_) {}
    return false;
  }

  /**
   * Cập nhật vị trí & kích thước phần tử DOM của sticker
   */
  function renderStickerDOM() {
    if (!stickerEl || !stageEl) return;

    if (!stickerState.visible) {
      stickerEl.style.display = "none";
      syncInputs();
      return;
    }

    stickerEl.style.display = "block";

    const stageW = canvasRect.width;
    const stageH = canvasRect.height;

    const pxW = Math.max(16, stickerState.w * stageW);
    const pxH = Math.max(16, pxW * stickerState.aspectRatio);

    const pxCenterX = stickerState.x * stageW;
    const pxCenterY = stickerState.y * stageH;

    stickerEl.style.width = `${pxW}px`;
    stickerEl.style.height = `${pxH}px`;
    stickerEl.style.left = `${pxCenterX}px`;
    stickerEl.style.top = `${pxCenterY}px`;
    stickerEl.style.transform = `translate(-50%, -50%) rotate(${stickerState.rotation}deg)`;
    stickerEl.style.opacity = `${stickerState.opacity}`;

    syncInputs();
  }

  /**
   * Đồng bộ giá trị sang bảng số và công tắc
   */
  function syncInputs() {
    if (numXEl && document.activeElement !== numXEl) {
      numXEl.value = Math.round(stickerState.x * 100);
    }
    if (numYEl && document.activeElement !== numYEl) {
      numYEl.value = Math.round(stickerState.y * 100);
    }
    if (numWEl && document.activeElement !== numWEl) {
      numWEl.value = Math.round(stickerState.w * 100);
    }
    if (numRotEl && document.activeElement !== numRotEl) {
      numRotEl.value = Math.round(stickerState.rotation);
    }
    if (numOpacityEl && document.activeElement !== numOpacityEl) {
      numOpacityEl.value = Math.round(stickerState.opacity * 100);
    }
    if (chkPillEl) {
      chkPillEl.checked = stickerState.pill;
    }
    if (chkHideEl) {
      chkHideEl.checked = !stickerState.visible;
    }
  }

  /**
   * Báo cáo thay đổi overrides kèm debounce 300ms
   */
  function notifyChange() {
    saveToLocalStorage();
    renderStickerDOM();

    if (changeDebounceTimer) {
      clearTimeout(changeDebounceTimer);
    }
    changeDebounceTimer = setTimeout(() => {
      if (typeof onOverridesChangedCallback === "function") {
        onOverridesChangedCallback(getOverrides());
      }
    }, 300);
  }

  /**
   * Smart Guides: Hít vào các đường dóng khi cách ≤ 8px
   */
  function applySmartGuides(candidateX, candidateY) {
    const stageW = canvasRect.width;
    const stageH = canvasRect.height;
    const halfW = stickerState.w / 2;
    const halfH = (stickerState.w * stickerState.aspectRatio * (stageW / stageH)) / 2;

    let snappedX = candidateX;
    let snappedY = candidateY;

    // Ẩn tất cả đường dóng ban đầu
    hideGuides();

    // 1. Trục dọc: Giữa (0.5), Lề trái 5% (0.05 + halfW), Lề phải 95% (0.95 - halfW)
    const distCenterV = Math.abs(candidateX - 0.5) * stageW;
    const distLeftV = Math.abs(candidateX - (SAFE_MARGIN + halfW)) * stageW;
    const distRightV = Math.abs(candidateX - (1.0 - SAFE_MARGIN - halfW)) * stageW;

    if (distCenterV <= SNAP_THRESHOLD_PX) {
      snappedX = 0.5;
      showGuide(guideCenterXEl, 0.5 * stageW, null);
    } else if (distLeftV <= SNAP_THRESHOLD_PX) {
      snappedX = SAFE_MARGIN + halfW;
      showGuide(guideMarginLeftEl, SAFE_MARGIN * stageW, null);
    } else if (distRightV <= SNAP_THRESHOLD_PX) {
      snappedX = 1.0 - SAFE_MARGIN - halfW;
      showGuide(guideMarginRightEl, (1.0 - SAFE_MARGIN) * stageW, null);
    }

    // 2. Trục ngang: Giữa (0.5), Lề trên 5% (0.05 + halfH), Lề dưới 95% (0.95 - halfH)
    const distCenterH = Math.abs(candidateY - 0.5) * stageH;
    const distTopH = Math.abs(candidateY - (SAFE_MARGIN + halfH)) * stageH;
    const distBottomH = Math.abs(candidateY - (1.0 - SAFE_MARGIN - halfH)) * stageH;

    if (distCenterH <= SNAP_THRESHOLD_PX) {
      snappedY = 0.5;
      showGuide(guideCenterYEl, null, 0.5 * stageH);
    } else if (distTopH <= SNAP_THRESHOLD_PX) {
      snappedY = SAFE_MARGIN + halfH;
      showGuide(guideMarginTopEl, null, SAFE_MARGIN * stageH);
    } else if (distBottomH <= SNAP_THRESHOLD_PX) {
      snappedY = 1.0 - SAFE_MARGIN - halfH;
      showGuide(guideMarginBottomEl, null, (1.0 - SAFE_MARGIN) * stageH);
    }

    return { x: snappedX, y: snappedY };
  }

  function showGuide(el, xPx, yPx) {
    if (!el) return;
    el.hidden = false;
    if (xPx !== null) {
      el.style.left = `${xPx}px`;
    }
    if (yPx !== null) {
      el.style.top = `${yPx}px`;
    }
  }

  function hideGuides() {
    [
      guideCenterXEl,
      guideCenterYEl,
      guideMarginLeftEl,
      guideMarginRightEl,
      guideMarginTopEl,
      guideMarginBottomEl,
    ].forEach((g) => {
      if (g) g.hidden = true;
    });
  }

  /**
   * Xử lý sự kiện kéo thả, phóng to, thu nhỏ, xoay bằng Pointer Events
   */
  function bindPointerEvents() {
    if (!stickerEl) return;

    stickerEl.addEventListener("pointerdown", onPointerDown);
    window.addEventListener("pointermove", onPointerMove, { passive: false });
    window.addEventListener("pointerup", onPointerUp);
    window.addEventListener("pointercancel", onPointerUp);

    // Bắt phím mũi tên khi sticker có focus
    stickerEl.addEventListener("keydown", (e) => {
      if (["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown"].includes(e.key)) {
        e.preventDefault();
        const step = e.shiftKey ? 10 : 1;
        const canvasW = canvasRect.canvasW || 1080;
        const canvasH = canvasRect.canvasH || 1920;

        if (e.key === "ArrowLeft") stickerState.x -= step / canvasW;
        if (e.key === "ArrowRight") stickerState.x += step / canvasW;
        if (e.key === "ArrowUp") stickerState.y -= step / canvasH;
        if (e.key === "ArrowDown") stickerState.y += step / canvasH;

        stickerState.x = Math.max(0, Math.min(1, stickerState.x));
        stickerState.y = Math.max(0, Math.min(1, stickerState.y));
        renderStickerDOM();
        notifyChange();
      }
    });

    // Chạm đúp / double click để về mặc định
    stickerEl.addEventListener("dblclick", (e) => {
      e.preventDefault();
      resetToDefault();
    });
  }

  function onPointerDown(e) {
    // Ngăn cuộn trang trên mobile khi thao tác trên sticker
    e.preventDefault();
    stickerEl.focus();

    // Xử lý double-tap trên màn hình cảm ứng
    const now = Date.now();
    if (now - lastTapTime < 300) {
      resetToDefault();
      lastTapTime = 0;
      return;
    }
    lastTapTime = now;

    activePointers.set(e.pointerId, { x: e.clientX, y: e.clientY });
    updateCanvasBounds();

    const targetHandle = e.target.dataset.handle;
    if (targetHandle === "rotate") {
      transformMode = "rotate";
      activeHandle = "rotate";
    } else if (targetHandle) {
      transformMode = "resize";
      activeHandle = targetHandle;
    } else if (activePointers.size === 2) {
      transformMode = "pinch";
      initPinchState();
    } else {
      transformMode = "move";
      dragStartPointer = { x: e.clientX, y: e.clientY };
      dragStartState = { ...stickerState };
    }

    stickerEl.classList.add("active");
    if (stickerEl.setPointerCapture) {
      try {
        stickerEl.setPointerCapture(e.pointerId);
      } catch (_) {}
    }
  }

  function initPinchState() {
    const pts = Array.from(activePointers.values());
    if (pts.length < 2) return;
    const dx = pts[1].x - pts[0].x;
    const dy = pts[1].y - pts[0].y;
    initialPinchDistance = Math.hypot(dx, dy);
    initialPinchAngle = Math.atan2(dy, dx) * (180 / Math.PI);
    initialPinchW = stickerState.w;
    initialPinchRot = stickerState.rotation;
  }

  function onPointerMove(e) {
    if (!activePointers.has(e.pointerId)) return;
    activePointers.set(e.pointerId, { x: e.clientX, y: e.clientY });

    // Ngăn chặn cuộn trang
    e.preventDefault();

    if (activePointers.size === 2) {
      // Thao tác 2 ngón: Pinch & Rotate
      const pts = Array.from(activePointers.values());
      const dx = pts[1].x - pts[0].x;
      const dy = pts[1].y - pts[0].y;
      const currentDistance = Math.hypot(dx, dy);
      const currentAngle = Math.atan2(dy, dx) * (180 / Math.PI);

      if (initialPinchDistance > 0) {
        const scale = currentDistance / initialPinchDistance;
        stickerState.w = Math.max(0.05, Math.min(1.0, initialPinchW * scale));
        const deltaAngle = currentAngle - initialPinchAngle;
        let newRot = initialPinchRot + deltaAngle;
        while (newRot > 180) newRot -= 360;
        while (newRot < -180) newRot += 360;
        stickerState.rotation = newRot;
      }
      renderStickerDOM();
      return;
    }

    const stageW = canvasRect.width;
    const stageH = canvasRect.height;
    const centerScreen = normalizedToScreen(stickerState.x, stickerState.y);

    if (transformMode === "move") {
      const deltaScreenX = e.clientX - dragStartPointer.x;
      const deltaScreenY = e.clientY - dragStartPointer.y;

      const candX = dragStartState.x + deltaScreenX / stageW;
      const candY = dragStartState.y + deltaScreenY / stageH;

      const snapped = applySmartGuides(candX, candY);
      stickerState.x = Math.max(0, Math.min(1.0, snapped.x));
      stickerState.y = Math.max(0, Math.min(1.0, snapped.y));

      renderStickerDOM();
    } else if (transformMode === "resize") {
      // Tính khoảng cách từ tâm tới con trỏ
      const distFromCenter = Math.hypot(e.clientX - centerScreen.x, e.clientY - centerScreen.y);
      const newScreenW = distFromCenter * 2 * Math.cos(Math.PI / 4);
      const candW = newScreenW / stageW;
      stickerState.w = Math.max(0.05, Math.min(1.0, candW));

      renderStickerDOM();
    } else if (transformMode === "rotate") {
      // Góc từ tâm sticker tới con trỏ
      const angleRad = Math.atan2(e.clientY - centerScreen.y, e.clientX - centerScreen.x);
      let angleDeg = angleRad * (180 / Math.PI) + 90; // +90 vì tay cầm nằm ở đỉnh trên

      while (angleDeg > 180) angleDeg -= 360;
      while (angleDeg < -180) angleDeg += 360;

      // Giữ Shift để nhảy bước 15°
      if (e.shiftKey) {
        angleDeg = Math.round(angleDeg / 15) * 15;
      } else {
        // Hít vào các góc chuẩn (0, 90, -90, 180) khi cách <= 3°
        [0, 90, -90, 180, -180].forEach((snapAngle) => {
          if (Math.abs(angleDeg - snapAngle) <= 3) {
            angleDeg = snapAngle;
          }
        });
      }

      stickerState.rotation = angleDeg;
      renderStickerDOM();
    }
  }

  function onPointerUp(e) {
    if (activePointers.has(e.pointerId)) {
      activePointers.delete(e.pointerId);
      if (stickerEl && stickerEl.releasePointerCapture) {
        try {
          stickerEl.releasePointerCapture(e.pointerId);
        } catch (_) {}
      }
    }

    if (activePointers.size === 0) {
      transformMode = "idle";
      hideGuides();
      if (stickerEl) stickerEl.classList.remove("active");
      notifyChange();
    }
  }

  /**
   * Khôi phục sticker về vị trí mặc định của template
   */
  function resetToDefault() {
    templateDefaults = resolveTemplateDefault(currentTemplate);
    stickerState.x = templateDefaults.x;
    stickerState.y = templateDefaults.y;
    stickerState.w = templateDefaults.w;
    stickerState.rotation = templateDefaults.rotation || 0;
    stickerState.opacity = templateDefaults.opacity !== undefined ? templateDefaults.opacity : 1.0;
    stickerState.visible = templateDefaults.visible !== undefined ? templateDefaults.visible : true;
    stickerState.pill = templateDefaults.pill !== undefined ? templateDefaults.pill : true;

    loadStickerImage();
    renderStickerDOM();
    notifyChange();
  }

  /**
   * Cập nhật hiển thị vùng an toàn (Safe Zones Overlay)
   */
  function updateSafeZonesDOM() {
    if (!safeZoneOverlayEl) return;
    if (!chkShowSafeZoneEl || !chkShowSafeZoneEl.checked) {
      safeZoneOverlayEl.hidden = true;
      return;
    }

    safeZoneOverlayEl.hidden = false;
    const platformKey = (selSafePlatformEl && selSafePlatformEl.value) || "tiktok";
    const platforms = (safeZonesConfig && safeZonesConfig.platforms) || {};
    const platform = platforms[platformKey] || { top: 0.1, bottom: 0.22, right: 0.16, left: 0.04 };

    const topEl = safeZoneOverlayEl.querySelector(".safe-zone-top");
    const bottomEl = safeZoneOverlayEl.querySelector(".safe-zone-bottom");
    const rightEl = safeZoneOverlayEl.querySelector(".safe-zone-right");
    const leftEl = safeZoneOverlayEl.querySelector(".safe-zone-left");
    const badgeEl = safeZoneOverlayEl.querySelector(".safe-zone-badge");

    if (topEl) topEl.style.height = `${(platform.top || 0.1) * 100}%`;
    if (bottomEl) bottomEl.style.height = `${(platform.bottom || 0.22) * 100}%`;
    if (rightEl) {
      rightEl.style.width = `${(platform.right || 0.16) * 100}%`;
      rightEl.style.top = `${(platform.top || 0.1) * 100}%`;
      rightEl.style.bottom = `${(platform.bottom || 0.22) * 100}%`;
    }
    if (leftEl) {
      leftEl.style.width = `${(platform.left || 0.04) * 100}%`;
      leftEl.style.top = `${(platform.top || 0.1) * 100}%`;
      leftEl.style.bottom = `${(platform.bottom || 0.22) * 100}%`;
    }
    if (badgeEl) {
      badgeEl.textContent = `Vùng an toàn: ${platform.name || platformKey.toUpperCase()}`;
    }
  }

  /**
   * Thiết lập vị trí theo lưới 9 ô nhanh (cách lề 5%)
   */
  function applyQuickGridPosition(pos) {
    const halfW = stickerState.w / 2;
    const stageW = canvasRect.width || 1;
    const stageH = canvasRect.height || 1;
    const halfH = (stickerState.w * stickerState.aspectRatio * (stageW / stageH)) / 2;

    switch (pos) {
      case "tl":
        stickerState.x = SAFE_MARGIN + halfW;
        stickerState.y = SAFE_MARGIN + halfH;
        break;
      case "tc":
        stickerState.x = 0.5;
        stickerState.y = SAFE_MARGIN + halfH;
        break;
      case "tr":
        stickerState.x = 1.0 - SAFE_MARGIN - halfW;
        stickerState.y = SAFE_MARGIN + halfH;
        break;
      case "ml":
        stickerState.x = SAFE_MARGIN + halfW;
        stickerState.y = 0.5;
        break;
      case "mc":
        stickerState.x = 0.5;
        stickerState.y = 0.5;
        break;
      case "mr":
        stickerState.x = 1.0 - SAFE_MARGIN - halfW;
        stickerState.y = 0.5;
        break;
      case "bl":
        stickerState.x = SAFE_MARGIN + halfW;
        stickerState.y = 1.0 - SAFE_MARGIN - halfH;
        break;
      case "bc":
        stickerState.x = 0.5;
        stickerState.y = 1.0 - SAFE_MARGIN - halfH;
        break;
      case "br":
        stickerState.x = 1.0 - SAFE_MARGIN - halfW;
        stickerState.y = 1.0 - SAFE_MARGIN - halfH;
        break;
    }

    renderStickerDOM();
    notifyChange();
  }

  /**
   * Khởi tạo các phần tử DOM điều khiển trong panel
   */
  function bindPanelControls() {
    numXEl = document.getElementById("numStickerX");
    numYEl = document.getElementById("numStickerY");
    numWEl = document.getElementById("numStickerW");
    numRotEl = document.getElementById("numStickerRot");
    numOpacityEl = document.getElementById("numStickerOpacity");
    chkPillEl = document.getElementById("chkStickerPill");
    chkHideEl = document.getElementById("chkStickerHide");
    chkShowSafeZoneEl = document.getElementById("chkShowSafeZone");
    selSafePlatformEl = document.getElementById("selSafePlatformSelect");

    const btnReset = document.getElementById("btnResetStickerPos");
    if (btnReset) {
      btnReset.addEventListener("click", resetToDefault);
    }

    // Sự kiện 9 vị trí nhanh
    document.querySelectorAll(".btn-grid-pos").forEach((btn) => {
      btn.addEventListener("click", () => {
        applyQuickGridPosition(btn.dataset.pos);
      });
    });

    // Nhập số trực tiếp
    if (numXEl) {
      numXEl.addEventListener("input", () => {
        const val = parseFloat(numXEl.value);
        if (!isNaN(val)) {
          stickerState.x = Math.max(0, Math.min(100, val)) / 100;
          renderStickerDOM();
          notifyChange();
        }
      });
    }
    if (numYEl) {
      numYEl.addEventListener("input", () => {
        const val = parseFloat(numYEl.value);
        if (!isNaN(val)) {
          stickerState.y = Math.max(0, Math.min(100, val)) / 100;
          renderStickerDOM();
          notifyChange();
        }
      });
    }
    if (numWEl) {
      numWEl.addEventListener("input", () => {
        const val = parseFloat(numWEl.value);
        if (!isNaN(val)) {
          stickerState.w = Math.max(5, Math.min(100, val)) / 100;
          renderStickerDOM();
          notifyChange();
        }
      });
    }
    if (numRotEl) {
      numRotEl.addEventListener("input", () => {
        const val = parseFloat(numRotEl.value);
        if (!isNaN(val)) {
          stickerState.rotation = Math.max(-180, Math.min(180, val));
          renderStickerDOM();
          notifyChange();
        }
      });
    }
    if (numOpacityEl) {
      numOpacityEl.addEventListener("input", () => {
        const val = parseFloat(numOpacityEl.value);
        if (!isNaN(val)) {
          stickerState.opacity = Math.max(0, Math.min(100, val)) / 100;
          renderStickerDOM();
          notifyChange();
        }
      });
    }

    if (chkPillEl) {
      chkPillEl.addEventListener("change", () => {
        stickerState.pill = chkPillEl.checked;
        loadStickerImage();
        notifyChange();
      });
    }

    if (chkHideEl) {
      chkHideEl.addEventListener("change", () => {
        stickerState.visible = !chkHideEl.checked;
        renderStickerDOM();
        notifyChange();
      });
    }

    if (chkShowSafeZoneEl) {
      chkShowSafeZoneEl.addEventListener("change", updateSafeZonesDOM);
    }
    if (selSafePlatformEl) {
      selSafePlatformEl.addEventListener("change", updateSafeZonesDOM);
    }
  }

  // ==================== PUBLIC API ====================
  const TAIOSticker = {
    init(options) {
      wrapperEl = options.previewWrapper || document.getElementById("previewWrapper");
      previewImgEl = options.previewImage || document.getElementById("previewImage");
      onOverridesChangedCallback = options.onOverridesChanged;

      stageEl = document.getElementById("stickerStage");
      stickerEl = document.getElementById("logoSticker");
      stickerImgEl = document.getElementById("logoStickerImg");
      safeZoneOverlayEl = document.getElementById("safeZoneOverlay");

      guideCenterXEl = document.getElementById("guideCenterX");
      guideCenterYEl = document.getElementById("guideCenterY");
      guideMarginLeftEl = document.getElementById("guideMarginLeft");
      guideMarginRightEl = document.getElementById("guideMarginRight");
      guideMarginTopEl = document.getElementById("guideMarginTop");
      guideMarginBottomEl = document.getElementById("guideMarginBottom");

      bindPointerEvents();
      bindPanelControls();

      if (window.ResizeObserver && wrapperEl) {
        const ro = new ResizeObserver(() => {
          updateCanvasBounds();
        });
        ro.observe(wrapperEl);
      }
      window.addEventListener("resize", updateCanvasBounds);
    },

    setSafeZonesConfig(config) {
      safeZonesConfig = config;
      updateSafeZonesDOM();
    },

    setTemplate(template, brandData) {
      currentTemplate = template;
      brandColors = brandData ? brandData.colors : null;
      templateDefaults = resolveTemplateDefault(template);

      const hasSaved = loadFromLocalStorage();
      if (!hasSaved) {
        stickerState.x = templateDefaults.x;
        stickerState.y = templateDefaults.y;
        stickerState.w = templateDefaults.w;
        stickerState.rotation = templateDefaults.rotation || 0;
        stickerState.opacity = templateDefaults.opacity !== undefined ? templateDefaults.opacity : 1.0;
        stickerState.visible = templateDefaults.visible !== undefined ? templateDefaults.visible : true;
        stickerState.pill = templateDefaults.pill !== undefined ? templateDefaults.pill : true;
      }

      loadStickerImage();
      updateCanvasBounds();
    },

    setLogoId(logoId) {
      currentLogoId = logoId;
      loadStickerImage();
    },

    updateCanvasLayout() {
      updateCanvasBounds();
    },

    getOverrides() {
      return {
        layers: {
          logo: {
            x: Math.round(stickerState.x * 10000) / 10000,
            y: Math.round(stickerState.y * 10000) / 10000,
            w: Math.round(stickerState.w * 10000) / 10000,
            rotation: Math.round(stickerState.rotation * 10) / 10,
            opacity: Math.round(stickerState.opacity * 100) / 100,
            visible: stickerState.visible,
            pill: stickerState.pill,
          },
        },
      };
    },

    getState() {
      return { ...stickerState };
    },
  };

  window.TAIOSticker = TAIOSticker;
})();
