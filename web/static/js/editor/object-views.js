/**
 * TAIO Cover Studio — Editor Object Views
 * Dựng và cập nhật phần tử DOM cho các đối tượng trên sân khấu, nạp ảnh từ server.
 */

(function () {
  "use strict";

  let stageEl = null;
  let stickerEl = null;
  let stickerImgEl = null;
  let bandHandleEl = null;
  let bandLineEl = null;

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

    if (stageEl && !bandHandleEl) {
      bandLineEl = document.createElement("div");
      bandLineEl.className = "band-edge-line";
      bandLineEl.style.display = "none";
      stageEl.appendChild(bandLineEl);

      bandHandleEl = document.createElement("div");
      bandHandleEl.className = "band-handle";
      bandHandleEl.dataset.handle = "band-top";
      bandHandleEl.style.display = "none";
      bandHandleEl.title = "Kéo lên/xuống để đổi chiều cao dải chân trang";
      stageEl.appendChild(bandHandleEl);
    }

    bindPanelControls();
  }

  async function loadStickerImage() {
    const store = window.TAIOSceneStore;
    if (!store || !store.currentTemplate) return;

    const pMode = store.stickerState.pillMode || (store.stickerState.pill ? "translucent" : "none");
    if (!store.stickerState.translucent) store.stickerState.translucent = { opacity: 0.50 };
    if (!store.stickerState.solid) store.stickerState.solid = { color: "#1A56DB", opacity: 1.0 };

    let pColor = "#000000";
    let pOpacity = 0.50;
    if (pMode === "translucent") {
      pColor = "#000000";
      pOpacity = store.stickerState.translucent.opacity !== undefined ? store.stickerState.translucent.opacity : 0.50;
    } else if (pMode === "solid") {
      pColor = store.stickerState.solid.color || "#1A56DB";
      pOpacity = store.stickerState.solid.opacity !== undefined ? store.stickerState.solid.opacity : 1.0;
    }

    const logoGroup = (store.objects || []).find((o) => o.id === "logo" && o.type === "group");
    if (logoGroup && logoGroup.customized) {
      try {
        const resp = await fetch("/api/object-image", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            object: {
              ...logoGroup,
              pill: {
                ...(logoGroup.pill || {}),
                enabled: store.stickerState.pill && pMode !== "none",
                mode: pMode,
                color: pColor,
                opacity: pOpacity,
                translucent: { opacity: store.stickerState.translucent.opacity },
                solid: { color: store.stickerState.solid.color, opacity: store.stickerState.solid.opacity },
              },
            },
            logo_id: store.currentLogoId || null,
          }),
        });
        if (resp.ok) {
          const blob = await resp.blob();
          const objUrl = URL.createObjectURL(blob);
          const img = new Image();
          img.onload = () => {
            if (img.naturalWidth && img.naturalHeight) {
              store.stickerState.aspectRatio = img.naturalHeight / img.naturalWidth;
            }
            if (stickerImgEl) {
              stickerImgEl.src = objUrl;
            }
            renderDOM();
          };
          img.src = objUrl;
          return;
        }
      } catch (e) {
        console.warn("Không thể tải custom logo group image:", e);
      }
    }

    const tplId = store.currentTemplate.id;
    const logoId = store.currentLogoId || "";
    const pill = (store.stickerState.pill && pMode !== "none") ? "1" : "0";
    const url = `/api/layer-image?template=${encodeURIComponent(tplId)}&layer=logo&logo_id=${encodeURIComponent(logoId)}&pill=${pill}&pill_mode=${pMode}&pill_color=${encodeURIComponent(pColor)}&pill_opacity=${pOpacity}&t=${Date.now()}`;

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

  const objectImageCache = new Map();

  async function loadObjectImage(obj) {
    const store = window.TAIOSceneStore;
    const payload = {
      object: obj,
      logo_id: store ? store.currentLogoId : null,
    };
    try {
      const resp = await fetch("/api/object-image", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (resp.ok) {
        const blob = await resp.blob();
        const objUrl = URL.createObjectURL(blob);
        const tempImg = new Image();
        tempImg.onload = () => {
          objectImageCache.set(obj.id, {
            url: objUrl,
            aspect: tempImg.naturalHeight / (tempImg.naturalWidth || 1),
            w: tempImg.naturalWidth,
            h: tempImg.naturalHeight,
          });
          renderDOM();
        };
        tempImg.src = objUrl;
      }
    } catch (e) {
      console.warn("Không thể tải object image:", e);
    }
  }

  function renderDOM() {
    const store = window.TAIOSceneStore;
    const transform = window.TAIOEditorTransform;
    if (!store || !transform) return;

    const state = store.stickerState;
    const canvasRect = transform.canvasRect;

    if (!stickerEl || !stageEl) return;

    const stageW = canvasRect.width;
    const stageH = canvasRect.height;
    const hasLogoGroup = (store.objects || []).some((o) => o.id === "logo" && o.type === "group");

    if (!state.visible || !hasLogoGroup) {
      stickerEl.style.display = "none";
    } else {
      stickerEl.style.display = "block";

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
        if (store.selectedChildId) {
          stickerEl.classList.add("group-selected-child");
        } else {
          stickerEl.classList.remove("group-selected-child");
        }
      } else {
        stickerEl.classList.remove("selected");
        stickerEl.classList.remove("group-selected-child");
      }
    }

    if (window.TAIOEditorToolbar) {
      window.TAIOEditorToolbar.updateToolbar();
    }

    // Render tay cầm dải chân trang (mẫu footer_band / bg_band)
    if (bandHandleEl && bandLineEl) {
      const isBand = store.currentTemplate && store.currentTemplate.id === "footer_band";
      const isBandSelected = store.selectedId === "bg_band";
      if (isBand && isBandSelected) {
        let bandH = 0.44;
        if (window.TAIOLayerControls) {
          const val = window.TAIOLayerControls.getControlValue("band_height");
          if (typeof val === "number") bandH = val;
        }
        updateBandHandlePosition(bandH);
        bandLineEl.style.display = "block";
        bandHandleEl.style.display = "block";
      } else {
        bandLineEl.style.display = "none";
        bandHandleEl.style.display = "none";
      }
    }

    // Render các đối tượng scene độc lập (text, image ngoài logo)
    const existingBoxes = new Map();
    stageEl.querySelectorAll(".scene-obj-box").forEach((el) => {
      existingBoxes.set(el.dataset.id, el);
    });

    const activeIds = new Set();
    const objs = store.objects || [];

    objs.forEach((obj) => {
      if (obj.id === "logo") return;
      activeIds.add(obj.id);

      let box = existingBoxes.get(obj.id);
      if (!box) {
        box = document.createElement("div");
        box.className = "sticker-box scene-obj-box";
        box.dataset.id = obj.id;
        box.tabIndex = 0;
        box.innerHTML = `
          <img class="sticker-img scene-obj-img" src="data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7" draggable="false" alt="">
          <div class="sticker-handle handle-tl" data-handle="tl"></div>
          <div class="sticker-handle handle-tr" data-handle="tr"></div>
          <div class="sticker-handle handle-bl" data-handle="bl"></div>
          <div class="sticker-handle handle-br" data-handle="br"></div>
          <div class="sticker-rotator-line"></div>
          <div class="sticker-rotator" data-handle="rotate" title="Kéo để xoay (Giữ Shift nhảy 15°)"></div>
        `;
        stageEl.appendChild(box);
      }

      if (obj.visible === false) {
        box.style.display = "none";
        return;
      }
      box.style.display = "block";

      const cached = objectImageCache.get(obj.id);
      const imgEl = box.querySelector(".scene-obj-img");
      if (cached) {
        if (imgEl && imgEl.src !== cached.url) {
          imgEl.src = cached.url;
        }
        const aspect = cached.aspect || 0.3;
        const objW = (obj.w || (obj.style && obj.style.size ? obj.style.size * 3.5 : 0.28)) * stageW;
        const objH = objW * aspect;
        box.style.width = `${Math.max(24, objW)}px`;
        box.style.height = `${Math.max(24, objH)}px`;
      } else {
        const estW = (obj.w || 0.28) * stageW;
        box.style.width = `${Math.max(24, estW)}px`;
        box.style.height = `${Math.max(24, estW * 0.3)}px`;
        loadObjectImage(obj);
      }

      box.style.left = `${(obj.x || 0.5) * stageW}px`;
      box.style.top = `${(obj.y || 0.5) * stageH}px`;
      box.style.transform = `translate(-50%, -50%) rotate(${obj.rotation || 0}deg)`;
      box.style.opacity = `${obj.opacity !== undefined ? obj.opacity : 1.0}`;

      if (store.selectedId === obj.id) {
        box.classList.add("selected");
      } else {
        box.classList.remove("selected");
      }
    });

    // Dọn dẹp DOM của đối tượng bị xoá
    existingBoxes.forEach((el, id) => {
      if (!activeIds.has(id)) {
        el.remove();
        objectImageCache.delete(id);
      }
    });

    syncInputs();
  }

  function updateBandHandlePosition(bandH) {
    if (!bandHandleEl || !bandLineEl || !window.TAIOEditorTransform) return;
    const canvasRect = window.TAIOEditorTransform.canvasRect;
    const stageH = canvasRect.height;
    const topPx = (1.0 - bandH) * stageH;
    bandLineEl.style.top = `${topPx}px`;
    bandHandleEl.style.top = `${topPx}px`;
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

    const pillSegments = document.getElementById("logoPillModeSegments");
    const pillColorPanel = document.getElementById("logoPillColorPanel");
    const pillPalette = document.getElementById("logoPillPalette");
    const pillColorCustom = document.getElementById("logoPillColorCustom");
    const rngPillOpacity = document.getElementById("rngLogoPillOpacity");
    const lblPillOpacity = document.getElementById("lblLogoPillOpacity");
    const logoPillOpacityRow = document.getElementById("logoPillOpacityRow");

    let pillToastTimer = null;
    function showPillModeToast(mode) {
      const toastEl = document.getElementById("pillModeToast");
      if (!toastEl) return;
      const labels = { none: "Không nền", translucent: "Trong mờ", solid: "Màu đặc" };
      toastEl.textContent = labels[mode] || mode;
      toastEl.style.display = "inline-block";
      toastEl.style.opacity = "1";
      if (pillToastTimer) clearTimeout(pillToastTimer);
      pillToastTimer = setTimeout(() => {
        toastEl.style.opacity = "0";
        setTimeout(() => { toastEl.style.display = "none"; }, 300);
      }, 1500);
    }

    function syncLogoGroupPill() {
      const lg = (store.objects || []).find((o) => o.id === "logo" && o.type === "group");
      if (!store.stickerState.translucent) store.stickerState.translucent = { opacity: 0.50 };
      if (!store.stickerState.solid) store.stickerState.solid = { color: "#1A56DB", opacity: 1.0 };
      const mode = store.stickerState.pillMode || "translucent";

      if (lg) {
        if (!lg.pill) lg.pill = {};
        lg.pill.enabled = store.stickerState.pill && mode !== "none";
        lg.pill.mode = mode;
        lg.pill.translucent = { opacity: store.stickerState.translucent.opacity };
        lg.pill.solid = { color: store.stickerState.solid.color, opacity: store.stickerState.solid.opacity };
        if (mode === "translucent") {
          lg.pill.color = "#000000";
          lg.pill.opacity = store.stickerState.translucent.opacity;
        } else if (mode === "solid") {
          lg.pill.color = store.stickerState.solid.color;
          lg.pill.opacity = store.stickerState.solid.opacity;
        } else {
          lg.pill.opacity = 0;
        }
        lg.customized = true;
      }
    }

    function updatePillControlsUI(mode) {
      if (!store.stickerState.translucent) store.stickerState.translucent = { opacity: 0.50 };
      if (!store.stickerState.solid) store.stickerState.solid = { color: "#1A56DB", opacity: 1.0 };

      if (pillSegments) {
        pillSegments.querySelectorAll(".btn-segment").forEach((b) => {
          b.classList.toggle("active", b.dataset.mode === mode);
        });
      }

      if (mode === "none") {
        if (pillPalette) pillPalette.style.display = "none";
        if (logoPillOpacityRow) logoPillOpacityRow.style.display = "none";
      } else if (mode === "translucent") {
        if (pillPalette) pillPalette.style.display = "none";
        if (logoPillOpacityRow) logoPillOpacityRow.style.display = "flex";
        if (rngPillOpacity) {
          rngPillOpacity.min = "0";
          rngPillOpacity.max = "80";
          const opVal = Math.round((store.stickerState.translucent.opacity !== undefined ? store.stickerState.translucent.opacity : 0.50) * 100);
          rngPillOpacity.value = String(opVal);
          if (lblPillOpacity) lblPillOpacity.textContent = `${opVal}%`;
        }
      } else if (mode === "solid") {
        if (pillPalette) pillPalette.style.display = "flex";
        if (logoPillOpacityRow) logoPillOpacityRow.style.display = "flex";
        if (rngPillOpacity) {
          rngPillOpacity.min = "0";
          rngPillOpacity.max = "100";
          const opVal = Math.round((store.stickerState.solid.opacity !== undefined ? store.stickerState.solid.opacity : 1.0) * 100);
          rngPillOpacity.value = String(opVal);
          if (lblPillOpacity) lblPillOpacity.textContent = `${opVal}%`;
        }
        if (pillPalette) {
          const activeCol = (store.stickerState.solid.color || "#1A56DB").toUpperCase();
          pillPalette.querySelectorAll(".color-swatch-btn").forEach((sw) => {
            sw.classList.toggle("active", (sw.dataset.color || "").toUpperCase() === activeCol);
          });
        }
      }
    }

    if (pillSegments) {
      pillSegments.querySelectorAll(".btn-segment").forEach((btn) => {
        btn.addEventListener("click", () => {
          const mode = btn.dataset.mode || "translucent";
          store.stickerState.pillMode = mode;
          store.stickerState.pill = mode !== "none";
          showPillModeToast(mode);
          updatePillControlsUI(mode);
          syncLogoGroupPill();
          loadStickerImage();
          store.notifyChange();
        });
      });
    }

    if (pillPalette) {
      pillPalette.querySelectorAll(".color-swatch-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
          pillPalette.querySelectorAll(".color-swatch-btn").forEach((b) => b.classList.remove("active"));
          btn.classList.add("active");
          const color = btn.dataset.color || "#1A56DB";
          if (!store.stickerState.solid) store.stickerState.solid = { color, opacity: 1.0 };
          store.stickerState.solid.color = color;
          syncLogoGroupPill();
          loadStickerImage();
          store.notifyChange();
        });
      });
    }

    if (pillColorCustom) {
      pillColorCustom.addEventListener("input", (e) => {
        if (!store.stickerState.solid) store.stickerState.solid = { color: e.target.value, opacity: 1.0 };
        store.stickerState.solid.color = e.target.value;
        syncLogoGroupPill();
        loadStickerImage();
        store.notifyChange();
      });
    }

    if (rngPillOpacity) {
      rngPillOpacity.addEventListener("input", () => {
        const val = parseInt(rngPillOpacity.value, 10) || 0;
        const op = val / 100.0;
        if (lblPillOpacity) lblPillOpacity.textContent = `${val}%`;
        if (store.stickerState.pillMode === "translucent") {
          if (!store.stickerState.translucent) store.stickerState.translucent = {};
          store.stickerState.translucent.opacity = op;
        } else if (store.stickerState.pillMode === "solid") {
          if (!store.stickerState.solid) store.stickerState.solid = {};
          store.stickerState.solid.opacity = op;
        }
        syncLogoGroupPill();
        loadStickerImage();
        store.notifyChange();
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
    updateBandHandlePosition,
    applyQuickGridPosition,
  };
})();
