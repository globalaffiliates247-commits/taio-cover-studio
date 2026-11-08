/**
 * TAIO Cover Studio — Editor Transform
 * Xử lý kéo thả, phóng to, thu nhỏ, xoay, tay cầm, phím mũi tên và quy đổi toạ độ.
 */

(function () {
  "use strict";

  let wrapperEl = null;
  let previewImgEl = null;
  let stageEl = null;
  let stickerEl = null;

  // Canvas bounds cache
  let canvasRect = { left: 0, top: 0, width: 1, height: 1, canvasW: 1080, canvasH: 1920 };

  // Pointer tracking
  let transformMode = "idle"; // 'idle' | 'move' | 'resize' | 'rotate' | 'pinch' | 'band-height'
  let activeHandle = null;
  let activeObjId = null;
  const activePointers = new Map();
  let dragStartPointer = { x: 0, y: 0 };
  let dragStartState = {};
  let initialPinchDistance = 0;
  let initialPinchAngle = 0;
  let initialPinchW = 0.22;
  let initialPinchRot = 0;
  let lastTapTime = 0;

  function initTransform(options) {
    wrapperEl = options.previewWrapper || document.getElementById("previewWrapper");
    previewImgEl = options.previewImage || document.getElementById("previewImage");
    stageEl = document.getElementById("stickerStage");
    stickerEl = document.getElementById("logoSticker");

    bindPointerEvents();

    if (window.ResizeObserver && wrapperEl) {
      const ro = new ResizeObserver(() => {
        updateCanvasBounds();
      });
      ro.observe(wrapperEl);
    }
    window.addEventListener("resize", updateCanvasBounds);
  }

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
      renderH = wrapRect.height;
      renderW = renderH * naturalAspect;
      offsetTop = 0;
      offsetLeft = (wrapRect.width - renderW) / 2;
    } else {
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

    if (window.TAIOEditorViews) {
      window.TAIOEditorViews.renderDOM();
    }
    return canvasRect;
  }

  function screenToNormalized(clientX, clientY) {
    const normX = (clientX - canvasRect.left) / canvasRect.width;
    const normY = (clientY - canvasRect.top) / canvasRect.height;
    return {
      x: Math.max(-0.5, Math.min(1.5, normX)),
      y: Math.max(-0.5, Math.min(1.5, normY)),
    };
  }

  function normalizedToScreen(normX, normY) {
    return {
      x: canvasRect.left + normX * canvasRect.width,
      y: canvasRect.top + normY * canvasRect.height,
    };
  }

  function bindPointerEvents() {
    if (!stickerEl) return;

    stickerEl.addEventListener("pointerdown", onPointerDown);
    window.addEventListener("pointermove", onPointerMove, { passive: false });
    window.addEventListener("pointerup", onPointerUp);
    window.addEventListener("pointercancel", onPointerUp);

    // Chạm vào vùng trống trên khung xem trước -> Bỏ chọn (ẩn toàn bộ tay cầm)
    if (stageEl) {
      stageEl.addEventListener("pointerdown", (e) => {
        const bandHandle = e.target.closest(".band-handle");
        if (bandHandle) {
          e.preventDefault();
          transformMode = "band-height";
          activePointers.set(e.pointerId, { x: e.clientX, y: e.clientY });
          if (bandHandle.setPointerCapture) {
            try {
              bandHandle.setPointerCapture(e.pointerId);
            } catch (_) {}
          }
          return;
        }

        const sceneBox = e.target.closest(".scene-obj-box");
        if (sceneBox) {
          e.preventDefault();
          const objId = sceneBox.dataset.id;
          activeObjId = objId;
          const store = window.TAIOSceneStore;
          store.selectObject(objId);

          activePointers.set(e.pointerId, { x: e.clientX, y: e.clientY });
          updateCanvasBounds();

          const targetHandle = e.target.dataset.handle;
          const obj = (store.objects || []).find((o) => o.id === objId);

          if (targetHandle === "rotate") {
            transformMode = "rotate";
            activeHandle = "rotate";
          } else if (targetHandle) {
            transformMode = "resize";
            activeHandle = targetHandle;
          } else {
            transformMode = "move";
            dragStartPointer = { x: e.clientX, y: e.clientY };
            dragStartState = {
              x: obj ? (obj.x || 0.5) : 0.5,
              y: obj ? (obj.y || 0.5) : 0.5,
              w: obj ? (obj.w || 0.28) : 0.28,
              rotation: obj ? (obj.rotation || 0) : 0,
            };
          }

          if (sceneBox.setPointerCapture) {
            try {
              sceneBox.setPointerCapture(e.pointerId);
            } catch (_) {}
          }
          return;
        }

        const store = window.TAIOSceneStore;
        // Chạm vào dải chân trang (mẫu footer_band) -> Chọn dải chân trang
        if (store.currentTemplate && store.currentTemplate.id === "footer_band") {
          let bandH = 0.44;
          if (window.TAIOLayerControls) {
            const val = window.TAIOLayerControls.getControlValue("band_height");
            if (typeof val === "number") bandH = val;
          }
          const normY = (e.clientY - canvasRect.top) / canvasRect.height;
          if (normY >= 1.0 - bandH - 0.02 && normY <= 1.05 && !e.target.closest(".sticker-box")) {
            store.selectObject("bg_band");
            return;
          }
        }

        if (
          !e.target.closest(".sticker-box") &&
          !e.target.closest(".band-handle") &&
          !e.target.closest(".editor-floating-toolbar")
        ) {
          window.TAIOSceneStore.clearSelection();
        }
      });
    }
    if (wrapperEl) {
      wrapperEl.addEventListener("pointerdown", (e) => {
        if (
          !e.target.closest(".sticker-box") &&
          !e.target.closest(".band-handle") &&
          !e.target.closest(".editor-floating-toolbar")
        ) {
          window.TAIOSceneStore.clearSelection();
        }
      });
    }

    // Phím tắt bàn phím máy tính (FEATURE v1.4 P7)
    window.addEventListener("keydown", (e) => {
      const tag = (document.activeElement && document.activeElement.tagName) || "";
      if (
        tag === "INPUT" ||
        tag === "TEXTAREA" ||
        (document.activeElement && document.activeElement.isContentEditable)
      ) {
        return;
      }

      const store = window.TAIOSceneStore;
      if (!store) return;

      // Esc -> Bỏ chọn
      if (e.key === "Escape") {
        store.clearSelection();
        return;
      }

      // Ctrl/Cmd + Z / Ctrl/Cmd + Shift + Z -> Hoàn tác / Làm lại
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "z") {
        e.preventDefault();
        if (e.shiftKey) {
          store.redo();
        } else {
          store.undo();
        }
        return;
      }

      // Ctrl/Cmd + D -> Nhân bản
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "d") {
        e.preventDefault();
        if (store.selectedId) {
          store.duplicateSelected();
        }
        return;
      }

      // Delete / Backspace -> Xoá
      if (e.key === "Delete" || e.key === "Backspace") {
        if (store.selectedId) {
          e.preventDefault();
          store.deleteSelected();
        }
        return;
      }

      // Phím mũi tên -> Dịch 1px (Shift: 10px) theo khung xuất
      if (["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown"].includes(e.key)) {
        if (store.selectedId) {
          e.preventDefault();
          const step = e.shiftKey ? 10 : 1;
          const canvasW = canvasRect.canvasW || 1080;
          const canvasH = canvasRect.canvasH || 1920;

          if (store.selectedId === "logo") {
            const state = store.stickerState;
            if (e.key === "ArrowLeft") state.x -= step / canvasW;
            if (e.key === "ArrowRight") state.x += step / canvasW;
            if (e.key === "ArrowUp") state.y -= step / canvasH;
            if (e.key === "ArrowDown") state.y += step / canvasH;
            state.x = Math.max(0, Math.min(1, state.x));
            state.y = Math.max(0, Math.min(1, state.y));
          } else {
            const obj = (store.objects || []).find((o) => o.id === store.selectedId);
            if (obj) {
              if (e.key === "ArrowLeft") obj.x = (obj.x || 0.5) - step / canvasW;
              if (e.key === "ArrowRight") obj.x = (obj.x || 0.5) + step / canvasW;
              if (e.key === "ArrowUp") obj.y = (obj.y || 0.5) - step / canvasH;
              if (e.key === "ArrowDown") obj.y = (obj.y || 0.5) + step / canvasH;
              obj.x = Math.max(0, Math.min(1, obj.x));
              obj.y = Math.max(0, Math.min(1, obj.y));
            }
          }

          if (window.TAIOEditorViews) window.TAIOEditorViews.renderDOM();
          store.notifyChange();
        }
      }
    });

    stickerEl.addEventListener("dblclick", (e) => {
      e.preventDefault();
      const rect = stickerEl.getBoundingClientRect();
      const relX = (e.clientX - rect.left) / rect.width;
      if (relX < 0.45) {
        window.TAIOSceneStore.selectObject("logo", "logo_img");
      } else {
        window.TAIOSceneStore.selectObject("logo", "logo_text");
      }
    });
  }

  function onPointerDown(e) {
    e.preventDefault();
    stickerEl.focus();

    const now = Date.now();
    if (now - lastTapTime < 300) {
      // Chạm lần 2 / chạm đúp: chọn đối tượng con dưới ngón tay (FEATURE v1.4 P5)
      const rect = stickerEl.getBoundingClientRect();
      const relX = (e.clientX - rect.left) / rect.width;
      if (relX < 0.45) {
        window.TAIOSceneStore.selectObject("logo", "logo_img");
      } else {
        window.TAIOSceneStore.selectObject("logo", "logo_text");
      }
      lastTapTime = 0;
      return;
    }
    lastTapTime = now;

    // Chọn cả nhóm khi chạm lần đầu
    if (window.TAIOSceneStore.selectedId !== "logo" || window.TAIOSceneStore.selectedChildId) {
      window.TAIOSceneStore.selectObject("logo", null);
    }
    activeObjId = "logo";

    activePointers.set(e.pointerId, { x: e.clientX, y: e.clientY });
    updateCanvasBounds();

    const targetHandle = e.target.dataset.handle;
    const state = window.TAIOSceneStore.stickerState;

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
      dragStartState = { ...state };
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
    const state = window.TAIOSceneStore.stickerState;
    initialPinchDistance = Math.hypot(dx, dy);
    initialPinchAngle = Math.atan2(dy, dx) * (180 / Math.PI);
    initialPinchW = state.w;
    initialPinchRot = state.rotation;
  }

  function onPointerMove(e) {
    if (!activePointers.has(e.pointerId)) return;
    activePointers.set(e.pointerId, { x: e.clientX, y: e.clientY });
    e.preventDefault();

    if (transformMode === "band-height") {
      const stageH = canvasRect.height;
      const normY = (e.clientY - canvasRect.top) / stageH;
      let candH = 1.0 - normY;

      // Hít vào các mốc 0.25 / 0.33 / 0.44 / 0.50 khi cách <= 8px
      const snapPoints = [0.25, 0.33, 0.44, 0.50];
      for (const pt of snapPoints) {
        if (Math.abs(candH - pt) * stageH <= 8) {
          candH = pt;
          break;
        }
      }
      candH = Math.max(0.12, Math.min(0.80, candH));

      if (window.TAIOLayerControls) {
        window.TAIOLayerControls.setControlValue("band_height", candH, false);
      }
      if (window.TAIOEditorViews) {
        window.TAIOEditorViews.updateBandHandlePosition(candH);
      }
      return;
    }

    if (activeObjId && activeObjId !== "logo") {
      const store = window.TAIOSceneStore;
      const obj = (store.objects || []).find((o) => o.id === activeObjId);
      if (!obj) return;

      const stageW = canvasRect.width;
      const stageH = canvasRect.height;
      const centerScreen = normalizedToScreen(obj.x || 0.5, obj.y || 0.5);

      if (transformMode === "move") {
        const deltaScreenX = e.clientX - dragStartPointer.x;
        const deltaScreenY = e.clientY - dragStartPointer.y;

        const candX = dragStartState.x + deltaScreenX / stageW;
        const candY = dragStartState.y + deltaScreenY / stageH;

        let snapped = { x: candX, y: candY };
        if (window.TAIOEditorGuides) {
          snapped = window.TAIOEditorGuides.applySmartGuides(candX, candY, obj.w || 0.28, null, canvasRect);
        }
        obj.x = Math.max(0, Math.min(1.0, snapped.x));
        obj.y = Math.max(0, Math.min(1.0, snapped.y));

        if (window.TAIOEditorViews) window.TAIOEditorViews.renderDOM();
      } else if (transformMode === "resize") {
        const distFromCenter = Math.hypot(e.clientX - centerScreen.x, e.clientY - centerScreen.y);
        const newScreenW = distFromCenter * 2 * Math.cos(Math.PI / 4);
        const candW = newScreenW / stageW;
        if (obj.type === "text" && obj.style) {
          obj.style.size = Math.max(0.015, Math.min(0.12, candW / 3.5));
        } else {
          obj.w = Math.max(0.04, Math.min(0.9, candW));
        }
        if (window.TAIOEditorViews) window.TAIOEditorViews.renderDOM();
      } else if (transformMode === "rotate") {
        const angleRad = Math.atan2(e.clientY - centerScreen.y, e.clientX - centerScreen.x);
        let angleDeg = angleRad * (180 / Math.PI) + 90;
        while (angleDeg > 180) angleDeg -= 360;
        while (angleDeg < -180) angleDeg += 360;
        if (e.shiftKey) {
          angleDeg = Math.round(angleDeg / 15) * 15;
        } else {
          [0, 90, -90, 180, -180].forEach((snapAngle) => {
            if (Math.abs(angleDeg - snapAngle) <= 3) angleDeg = snapAngle;
          });
        }
        obj.rotation = angleDeg;
        if (window.TAIOEditorViews) window.TAIOEditorViews.renderDOM();
      }
      return;
    }

    const state = window.TAIOSceneStore.stickerState;

    if (activePointers.size === 2) {
      const pts = Array.from(activePointers.values());
      const dx = pts[1].x - pts[0].x;
      const dy = pts[1].y - pts[0].y;
      const currentDistance = Math.hypot(dx, dy);
      const currentAngle = Math.atan2(dy, dx) * (180 / Math.PI);

      if (initialPinchDistance > 0) {
        const scale = currentDistance / initialPinchDistance;
        state.w = Math.max(0.05, Math.min(1.0, initialPinchW * scale));
        const deltaAngle = currentAngle - initialPinchAngle;
        let newRot = initialPinchRot + deltaAngle;
        while (newRot > 180) newRot -= 360;
        while (newRot < -180) newRot += 360;
        state.rotation = newRot;
      }
      if (window.TAIOEditorViews) window.TAIOEditorViews.renderDOM();
      return;
    }

    const stageW = canvasRect.width;
    const stageH = canvasRect.height;
    const centerScreen = normalizedToScreen(state.x, state.y);

    if (transformMode === "move") {
      const deltaScreenX = e.clientX - dragStartPointer.x;
      const deltaScreenY = e.clientY - dragStartPointer.y;

      const candX = dragStartState.x + deltaScreenX / stageW;
      const candY = dragStartState.y + deltaScreenY / stageH;

      let snapped = { x: candX, y: candY };
      if (window.TAIOEditorGuides) {
        snapped = window.TAIOEditorGuides.applySmartGuides(candX, candY, state.w, null, canvasRect);
      }
      state.x = Math.max(0, Math.min(1.0, snapped.x));
      state.y = Math.max(0, Math.min(1.0, snapped.y));

      if (window.TAIOEditorViews) window.TAIOEditorViews.renderDOM();
    } else if (transformMode === "resize") {
      const distFromCenter = Math.hypot(e.clientX - centerScreen.x, e.clientY - centerScreen.y);
      const newScreenW = distFromCenter * 2 * Math.cos(Math.PI / 4);
      const candW = newScreenW / stageW;
      state.w = Math.max(0.05, Math.min(1.0, candW));

      if (window.TAIOEditorViews) window.TAIOEditorViews.renderDOM();
    } else if (transformMode === "rotate") {
      const angleRad = Math.atan2(e.clientY - centerScreen.y, e.clientX - centerScreen.x);
      let angleDeg = angleRad * (180 / Math.PI) + 90;

      while (angleDeg > 180) angleDeg -= 360;
      while (angleDeg < -180) angleDeg += 360;

      if (e.shiftKey) {
        angleDeg = Math.round(angleDeg / 15) * 15;
      } else {
        [0, 90, -90, 180, -180].forEach((snapAngle) => {
          if (Math.abs(angleDeg - snapAngle) <= 3) {
            angleDeg = snapAngle;
          }
        });
      }

      state.rotation = angleDeg;
      if (window.TAIOEditorViews) window.TAIOEditorViews.renderDOM();
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
      activeObjId = null;
      if (window.TAIOEditorGuides) {
        window.TAIOEditorGuides.hideGuides();
      }
      if (stickerEl) stickerEl.classList.remove("active");
      window.TAIOSceneStore.recordSnapshot();
      window.TAIOSceneStore.notifyChange();
    }
  }

  function resetToDefault() {
    const store = window.TAIOSceneStore;
    store.templateDefaults = store.resolveTemplateDefault(store.currentTemplate);
    const def = store.templateDefaults;
    store.stickerState.x = def.x;
    store.stickerState.y = def.y;
    store.stickerState.w = def.w;
    store.stickerState.rotation = def.rotation || 0;
    store.stickerState.opacity = def.opacity !== undefined ? def.opacity : 1.0;
    store.stickerState.visible = def.visible !== undefined ? def.visible : true;
    store.stickerState.pill = def.pill !== undefined ? def.pill : true;

    if (window.TAIOEditorViews) {
      window.TAIOEditorViews.loadStickerImage();
      window.TAIOEditorViews.renderDOM();
    }
    store.recordSnapshot();
    store.notifyChange();
  }

  window.TAIOEditorTransform = {
    initTransform,
    updateCanvasBounds,
    screenToNormalized,
    normalizedToScreen,
    resetToDefault,
    get canvasRect() {
      return canvasRect;
    },
  };
})();
