/**
 * TAIO Cover Studio — Editor Guides & Safe Zones
 * Quản lý đường dóng thông minh (Smart Guides) và vùng an toàn (Safe Zones).
 */

(function () {
  "use strict";

  const SNAP_THRESHOLD_PX = 8;
  const SAFE_MARGIN = 0.05; // 5% lề an toàn mặc định

  let guideCenterXEl = null;
  let guideCenterYEl = null;
  let guideMarginLeftEl = null;
  let guideMarginRightEl = null;
  let guideMarginTopEl = null;
  let guideMarginBottomEl = null;
  let safeZoneOverlayEl = null;
  let safeZonesConfig = null;

  function initGuides(elements) {
    guideCenterXEl = elements.guideCenterX || document.getElementById("guideCenterX");
    guideCenterYEl = elements.guideCenterY || document.getElementById("guideCenterY");
    guideMarginLeftEl = elements.guideMarginLeft || document.getElementById("guideMarginLeft");
    guideMarginRightEl = elements.guideMarginRight || document.getElementById("guideMarginRight");
    guideMarginTopEl = elements.guideMarginTop || document.getElementById("guideMarginTop");
    guideMarginBottomEl = elements.guideMarginBottom || document.getElementById("guideMarginBottom");
    safeZoneOverlayEl = elements.safeZoneOverlay || document.getElementById("safeZoneOverlay");
  }

  function setSafeZonesConfig(config) {
    safeZonesConfig = config;
  }

  function showGuide(el, xPx, yPx) {
    if (!el) return;
    el.hidden = false;
    if (xPx !== null && xPx !== undefined) {
      el.style.left = `${xPx}px`;
    }
    if (yPx !== null && yPx !== undefined) {
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
   * Tính toán hít thông minh (Smart Guides Snap)
   */
  function applySmartGuides(candidateX, candidateY, objW, objH, canvasRect) {
    const stageW = canvasRect.width || 1;
    const stageH = canvasRect.height || 1;
    const halfW = (objW || 0.22) / 2;
    const halfH = (objH || (objW * 0.25 * (stageW / stageH))) / 2;

    let snappedX = candidateX;
    let snappedY = candidateY;

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

  /**
   * Cập nhật hiển thị vùng an toàn (Safe Zones Overlay)
   */
  function updateSafeZonesDOM(show, platformKey) {
    if (!safeZoneOverlayEl) return;
    if (!show) {
      safeZoneOverlayEl.hidden = true;
      return;
    }

    safeZoneOverlayEl.hidden = false;
    const key = platformKey || "tiktok";
    const platforms = (safeZonesConfig && safeZonesConfig.platforms) || {};
    const platform = platforms[key] || { top: 0.1, bottom: 0.22, right: 0.16, left: 0.04 };

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
      badgeEl.textContent = `Vùng an toàn: ${platform.name || key.toUpperCase()}`;
    }
  }

  window.TAIOEditorGuides = {
    initGuides,
    setSafeZonesConfig,
    showGuide,
    hideGuides,
    applySmartGuides,
    updateSafeZonesDOM,
    SAFE_MARGIN,
    SNAP_THRESHOLD_PX,
  };
})();
