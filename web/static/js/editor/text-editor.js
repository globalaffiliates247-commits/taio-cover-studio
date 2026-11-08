/**
 * TAIO Cover Studio — Editor Text Editor & Facade
 * Quản lý tuỳ chỉnh chữ và facade tương thích ngược window.TAIOSticker.
 */

(function () {
  "use strict";

  function initTextEditor() {
    // Sẽ kết nối bảng tuỳ chọn chữ dùng chung ở P6
  }

  // ==================== FACADE TAIOSticker (Tương thích ngược 100%) ====================
  const TAIOSticker = {
    init(options) {
      const guides = window.TAIOEditorGuides;
      const transform = window.TAIOEditorTransform;
      const views = window.TAIOEditorViews;
      const toolbar = window.TAIOEditorToolbar;
      const store = window.TAIOSceneStore;

      if (store && options.onOverridesChanged) {
        store.subscribe(options.onOverridesChanged);
      }
      if (guides) {
        guides.initGuides({
          guideCenterX: document.getElementById("guideCenterX"),
          guideCenterY: document.getElementById("guideCenterY"),
          guideMarginLeft: document.getElementById("guideMarginLeft"),
          guideMarginRight: document.getElementById("guideMarginRight"),
          guideMarginTop: document.getElementById("guideMarginTop"),
          guideMarginBottom: document.getElementById("guideMarginBottom"),
          safeZoneOverlay: document.getElementById("safeZoneOverlay"),
        });
      }
      if (transform) {
        transform.initTransform(options);
      }
      if (views) {
        views.initViews();
      }
      if (toolbar) {
        toolbar.initToolbar();
      }
      initTextEditor();
    },

    setSafeZonesConfig(config) {
      if (window.TAIOEditorGuides) {
        window.TAIOEditorGuides.setSafeZonesConfig(config);
        const chkShow = document.getElementById("chkShowSafeZone");
        const selPlatform = document.getElementById("selSafePlatformSelect");
        window.TAIOEditorGuides.updateSafeZonesDOM(
          chkShow ? chkShow.checked : false,
          selPlatform ? selPlatform.value : "tiktok"
        );
      }
    },

    setTemplate(template, brandData) {
      const store = window.TAIOSceneStore;
      const views = window.TAIOEditorViews;
      const transform = window.TAIOEditorTransform;
      if (!store) return;

      store.currentTemplate = template;
      store.brandColors = brandData ? brandData.colors : null;
      store.templateDefaults = store.resolveTemplateDefault(template);

      const hasSaved = store.loadFromLocalStorage();
      if (!hasSaved) {
        const def = store.templateDefaults;
        store.stickerState.x = def.x;
        store.stickerState.y = def.y;
        store.stickerState.w = def.w;
        store.stickerState.rotation = def.rotation || 0;
        store.stickerState.opacity = def.opacity !== undefined ? def.opacity : 1.0;
        store.stickerState.visible = def.visible !== undefined ? def.visible : true;
        store.stickerState.pill = def.pill !== undefined ? def.pill : true;
      }

      if (views) {
        views.loadStickerImage();
      }
      if (transform) {
        transform.updateCanvasBounds();
      }
    },

    setLogoId(logoId) {
      const store = window.TAIOSceneStore;
      const views = window.TAIOEditorViews;
      if (store) {
        store.currentLogoId = logoId;
      }
      if (views) {
        views.loadStickerImage();
      }
    },

    updateCanvasLayout() {
      if (window.TAIOEditorTransform) {
        window.TAIOEditorTransform.updateCanvasBounds();
      }
    },

    getOverrides() {
      return window.TAIOSceneStore ? window.TAIOSceneStore.getOverrides() : {};
    },

    getState() {
      return window.TAIOSceneStore ? { ...window.TAIOSceneStore.stickerState } : {};
    },
  };

  window.TAIOEditorText = {
    initTextEditor,
  };

  window.TAIOSticker = TAIOSticker;
})();
