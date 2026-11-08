/**
 * TAIO Cover Studio — Editor Scene Store
 * Quản lý trạng thái Scene, danh sách đối tượng, chọn/bỏ chọn, hoàn tác/làm lại.
 */

(function () {
  "use strict";

  const MAX_HISTORY = 50;

  let currentTemplate = null;
  let currentLogoId = null;
  let brandColors = null;
  let onOverridesChangedCallback = null;
  let changeDebounceTimer = null;

  // Scene state
  let objects = [];
  let selectedId = null;
  let selectedChildId = null;

  // Lịch sử hoàn tác (Undo / Redo)
  const undoStack = [];
  const redoStack = [];

  // Trạng thái tương thích ngược cho logo sticker (v1.2 & v1.3)
  const stickerState = {
    x: 0.82,
    y: 0.06,
    w: 0.22,
    rotation: 0,
    opacity: 1.0,
    visible: true,
    pill: true,
    aspectRatio: 0.25,
  };

  let templateDefaults = { ...stickerState };

  function subscribe(callback) {
    onOverridesChangedCallback = callback;
  }

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

  function saveToLocalStorage() {
    if (!currentTemplate) return;
    try {
      const key = `taio_sticker_overrides_${currentTemplate.id}`;
      localStorage.setItem(
        key,
        JSON.stringify({
          x: stickerState.x,
          y: stickerState.y,
          w: stickerState.w,
          rotation: stickerState.rotation,
          opacity: stickerState.opacity,
          visible: stickerState.visible,
          pill: stickerState.pill,
        })
      );
      if (objects.length > 0) {
        localStorage.setItem(`taio_scene_${currentTemplate.id}`, JSON.stringify(objects));
      }
    } catch (_) {}
  }

  function loadFromLocalStorage() {
    if (!currentTemplate) return false;
    let loaded = false;
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
          loaded = true;
        }
      }
      const rawScene = localStorage.getItem(`taio_scene_${currentTemplate.id}`);
      if (rawScene) {
        const parsedScene = JSON.parse(rawScene);
        if (Array.isArray(parsedScene)) {
          objects = parsedScene;
        }
      }
    } catch (_) {}
    return loaded;
  }

  function recordSnapshot() {
    const snapshot = {
      objects: JSON.parse(JSON.stringify(objects)),
      sticker: { ...stickerState },
    };
    undoStack.push(snapshot);
    if (undoStack.length > MAX_HISTORY) {
      undoStack.shift();
    }
    redoStack.length = 0; // Xoá redo khi có thao tác mới
  }

  function undo() {
    if (undoStack.length === 0) return false;
    const currentSnapshot = {
      objects: JSON.parse(JSON.stringify(objects)),
      sticker: { ...stickerState },
    };
    redoStack.push(currentSnapshot);

    const prev = undoStack.pop();
    if (prev) {
      objects = prev.objects || [];
      if (prev.sticker) Object.assign(stickerState, prev.sticker);
      notifyChange(0, false);
      return true;
    }
    return false;
  }

  function redo() {
    if (redoStack.length === 0) return false;
    const currentSnapshot = {
      objects: JSON.parse(JSON.stringify(objects)),
      sticker: { ...stickerState },
    };
    undoStack.push(currentSnapshot);

    const next = redoStack.pop();
    if (next) {
      objects = next.objects || [];
      if (next.sticker) Object.assign(stickerState, next.sticker);
      notifyChange(0, false);
      return true;
    }
    return false;
  }

  function notifyChange(debounceMs = 300, recordHistory = true) {
    saveToLocalStorage();
    if (recordHistory) {
      // Có thể ghi snapshot khi kết thúc thao tác
    }
    if (window.TAIOEditorViews) {
      window.TAIOEditorViews.renderDOM();
    }

    if (changeDebounceTimer) {
      clearTimeout(changeDebounceTimer);
    }
    const delay = typeof debounceMs === "number" ? debounceMs : 300;
    changeDebounceTimer = setTimeout(() => {
      if (typeof onOverridesChangedCallback === "function") {
        onOverridesChangedCallback(getOverrides());
      }
    }, delay);
  }

  function getOverrides() {
    const overrides = {
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
    if (objects && objects.length > 0) {
      overrides.objects = objects;
    }
    return overrides;
  }

  function selectObject(id, childId = null) {
    selectedId = id;
    selectedChildId = childId;
    if (window.TAIOEditorViews) {
      window.TAIOEditorViews.renderDOM();
    }
    if (window.TAIOEditorToolbar) {
      window.TAIOEditorToolbar.updateToolbar();
    }
  }

  function clearSelection() {
    selectedId = null;
    selectedChildId = null;
    if (window.TAIOEditorViews) {
      window.TAIOEditorViews.renderDOM();
    }
    if (window.TAIOEditorToolbar) {
      window.TAIOEditorToolbar.updateToolbar();
    }
  }

  window.TAIOSceneStore = {
    subscribe,
    resolveTemplateDefault,
    saveToLocalStorage,
    loadFromLocalStorage,
    recordSnapshot,
    undo,
    redo,
    notifyChange,
    getOverrides,
    selectObject,
    clearSelection,
    get selectedId() {
      return selectedId;
    },
    set selectedId(val) {
      selectedId = val;
    },
    get selectedChildId() {
      return selectedChildId;
    },
    set selectedChildId(val) {
      selectedChildId = val;
    },
    get objects() {
      return objects;
    },
    set objects(val) {
      objects = val;
    },
    get stickerState() {
      return stickerState;
    },
    get templateDefaults() {
      return templateDefaults;
    },
    set templateDefaults(val) {
      templateDefaults = val;
    },
    get currentTemplate() {
      return currentTemplate;
    },
    set currentTemplate(val) {
      currentTemplate = val;
    },
    get currentLogoId() {
      return currentLogoId;
    },
    set currentLogoId(val) {
      currentLogoId = val;
    },
    get brandColors() {
      return brandColors;
    },
    set brandColors(val) {
      brandColors = val;
    },
  };
})();
