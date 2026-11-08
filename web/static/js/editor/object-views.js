/**
 * TAIO Cover Studio — Editor Object Views
 * Dựng và cập nhật phần tử DOM cho các đối tượng trên sân khấu, nạp ảnh từ server.
 */

(function () {
  "use strict";

  let stageEl = null;
  let stickerEl = null;
  let stickerImgEl = null;

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

  function initViews() {
    stageEl = document.getElementById("stickerStage");
    stickerEl = document.getElementById("logoSticker");
    stickerImgEl = document.getElementById("logoStickerImg");

    bindPanelControls();
  }

  async function loadStickerImage() {
    const store = window.TAIOSceneStore;
    if (!store || !store.currentTemplate) return;
    const tplId = store.currentTemplate.id;
    const logoId = store.currentLogoId || "";
    const pill = store.stickerState.pill ? "1" : "0";
    const url = `/api/layer-image?template=${encodeURIComponent(tplId)}&layer=logo&logo_id=${encodeURIComponent(logoId)}&pill=${pill}&t=${Date.now()}`;

    try {
      const img = new Image();
      img.crossOrigin = "anonymous";
      img.onload = () => {
        if (img.naturalWidth && img.naturalHeight) {
          store.stickerState.aspectRatio = img.naturalHeight / img.naturalWidth;
        }
        if (stickerImgEl) {
          stickerImgEl.src = img.src;
        }
        renderDOM();
      };
      img.src = url;
    } catch (e) {
      console.warn("Không thể tải sticker logo layer:", e);
    }
  }

  function renderDOM() {
    const store = window.TAIOSceneStore;
    const transform = window.TAIOEditorTransform;
    if (!store || !transform) return;

    const state = store.stickerState;
    const canvasRect = transform.canvasRect;

    if (!stickerEl || !stageEl) return;

    if (!state.visible) {
      stickerEl.style.display = "none";
      syncInputs();
      return;
    }

    stickerEl.style.display = "block";

    const stageW = canvasRect.width;
    const stageH = canvasRect.height;

    const pxW = Math.max(16, state.w * stageW);
    const pxH = Math.max(16, pxW * state.aspectRatio);

    const pxCenterX = state.x * stageW;
    const pxCenterY = state.y * stageH;

    stickerEl.style.width = `${pxW}px`;
    stickerEl.style.height = `${pxH}px`;
    stickerEl.style.left = `${pxCenterX}px`;
    stickerEl.style.top = `${pxCenterY}px`;
    stickerEl.style.transform = `translate(-50%, -50%) rotate(${state.rotation}deg)`;
    stickerEl.style.opacity = `${state.opacity}`;

    if (store.selectedId === "logo") {
      stickerEl.classList.add("selected");
    } else {
      stickerEl.classList.remove("selected");
    }

    syncInputs();
  }

  function syncInputs() {
    const store = window.TAIOSceneStore;
    if (!store) return;
    const state = store.stickerState;

    if (numXEl && document.activeElement !== numXEl) {
      numXEl.value = Math.round(state.x * 100);
    }
    if (numYEl && document.activeElement !== numYEl) {
      numYEl.value = Math.round(state.y * 100);
    }
    if (numWEl && document.activeElement !== numWEl) {
      numWEl.value = Math.round(state.w * 100);
    }
    if (numRotEl && document.activeElement !== numRotEl) {
      numRotEl.value = Math.round(state.rotation);
    }
    if (numOpacityEl && document.activeElement !== numOpacityEl) {
      numOpacityEl.value = Math.round(state.opacity * 100);
    }
    if (chkPillEl) {
      chkPillEl.checked = state.pill;
    }
    if (chkHideEl) {
      chkHideEl.checked = !state.visible;
    }
  }

  function bindPanelControls() {
    const store = window.TAIOSceneStore;
    const transform = window.TAIOEditorTransform;
    const guides = window.TAIOEditorGuides;

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
    if (btnReset && transform) {
      btnReset.addEventListener("click", transform.resetToDefault);
    }

    // Sự kiện 9 vị trí nhanh
    document.querySelectorAll(".btn-grid-pos").forEach((btn) => {
      btn.addEventListener("click", () => {
        applyQuickGridPosition(btn.dataset.pos);
      });
    });

    if (numXEl) {
      numXEl.addEventListener("input", () => {
        const val = parseFloat(numXEl.value);
        if (!isNaN(val)) {
          store.stickerState.x = Math.max(0, Math.min(100, val)) / 100;
          renderDOM();
          store.notifyChange();
        }
      });
    }
    if (numYEl) {
      numYEl.addEventListener("input", () => {
        const val = parseFloat(numYEl.value);
        if (!isNaN(val)) {
          store.stickerState.y = Math.max(0, Math.min(100, val)) / 100;
          renderDOM();
          store.notifyChange();
        }
      });
    }
    if (numWEl) {
      numWEl.addEventListener("input", () => {
        const val = parseFloat(numWEl.value);
        if (!isNaN(val)) {
          store.stickerState.w = Math.max(5, Math.min(100, val)) / 100;
          renderDOM();
          store.notifyChange();
        }
      });
    }
    if (numRotEl) {
      numRotEl.addEventListener("input", () => {
        const val = parseFloat(numRotEl.value);
        if (!isNaN(val)) {
          store.stickerState.rotation = Math.max(-180, Math.min(180, val));
          renderDOM();
          store.notifyChange();
        }
      });
    }
    if (numOpacityEl) {
      numOpacityEl.addEventListener("input", () => {
        const val = parseFloat(numOpacityEl.value);
        if (!isNaN(val)) {
          store.stickerState.opacity = Math.max(0, Math.min(100, val)) / 100;
          renderDOM();
          store.notifyChange();
        }
      });
    }

    if (chkPillEl) {
      chkPillEl.addEventListener("change", () => {
        store.stickerState.pill = chkPillEl.checked;
        loadStickerImage();
        store.notifyChange();
      });
    }

    if (chkHideEl) {
      chkHideEl.addEventListener("change", () => {
        store.stickerState.visible = !chkHideEl.checked;
        renderDOM();
        store.notifyChange();
      });
    }

    if (chkShowSafeZoneEl && guides) {
      chkShowSafeZoneEl.addEventListener("change", () => {
        guides.updateSafeZonesDOM(chkShowSafeZoneEl.checked, selSafePlatformEl ? selSafePlatformEl.value : "tiktok");
      });
    }
    if (selSafePlatformEl && guides) {
      selSafePlatformEl.addEventListener("change", () => {
        guides.updateSafeZonesDOM(chkShowSafeZoneEl ? chkShowSafeZoneEl.checked : false, selSafePlatformEl.value);
      });
    }
  }

  function applyQuickGridPosition(pos) {
    const store = window.TAIOSceneStore;
    const transform = window.TAIOEditorTransform;
    const guides = window.TAIOEditorGuides;
    if (!store || !transform) return;

    const canvasRect = transform.canvasRect;
    const safeMargin = guides ? guides.SAFE_MARGIN : 0.05;
    const state = store.stickerState;
    const halfW = state.w / 2;
    const stageW = canvasRect.width || 1;
    const stageH = canvasRect.height || 1;
    const halfH = (state.w * state.aspectRatio * (stageW / stageH)) / 2;

    switch (pos) {
      case "tl":
        state.x = safeMargin + halfW;
        state.y = safeMargin + halfH;
        break;
      case "tc":
        state.x = 0.5;
        state.y = safeMargin + halfH;
        break;
      case "tr":
        state.x = 1.0 - safeMargin - halfW;
        state.y = safeMargin + halfH;
        break;
      case "ml":
        state.x = safeMargin + halfW;
        state.y = 0.5;
        break;
      case "mc":
        state.x = 0.5;
        state.y = 0.5;
        break;
      case "mr":
        state.x = 1.0 - safeMargin - halfW;
        state.y = 0.5;
        break;
      case "bl":
        state.x = safeMargin + halfW;
        state.y = 1.0 - safeMargin - halfH;
        break;
      case "bc":
        state.x = 0.5;
        state.y = 1.0 - safeMargin - halfH;
        break;
      case "br":
        state.x = 1.0 - safeMargin - halfW;
        state.y = 1.0 - safeMargin - halfH;
        break;
    }

    renderDOM();
    store.recordSnapshot();
    store.notifyChange();
  }

  window.TAIOEditorViews = {
    initViews,
    loadStickerImage,
    renderDOM,
    applyQuickGridPosition,
  };
})();
