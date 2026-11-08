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

  function createDefaultLogoGroup(template, brandData) {
    if (!template || !template.layers) return null;
    const logoLayer = template.layers.find((l) => l.type === "logo" || l.id === "logo");
    if (!logoLayer) return null;

    const brandName = (brandData && brandData.name) || "TAIO.CLUB";
    const label = logoLayer.label === "$name" ? brandName : (logoLayer.label || brandName);
    const pillEnabled = logoLayer.pill !== undefined ? Boolean(logoLayer.pill) : true;
    const def = resolveTemplateDefault(template);

    return {
      id: "logo",
      type: "group",
      x: def.x,
      y: def.y,
      rotation: def.rotation || 0,
      z: 10,
      pill: { enabled: pillEnabled },
      children: [
        {
          id: "logo_img",
          type: "image",
          src: "brand",
          dx: -0.05,
          dy: 0,
          w: 0.055,
          visible: true,
        },
        {
          id: "logo_text",
          type: "text",
          text: label,
          dx: 0.035,
          dy: 0,
          style: {
            font: "BeVietnamPro",
            weight: logoLayer.weight || "Black",
            size: 0.032,
            color: "#FFFFFF",
          },
          visible: true,
        },
      ],
    };
  }

  function initTemplateScene(template, brandData) {
    currentTemplate = template;
    brandColors = brandData ? brandData.colors : null;
    templateDefaults = resolveTemplateDefault(template);

    const hasSaved = loadFromLocalStorage();
    if (!hasSaved) {
      const def = templateDefaults;
      stickerState.x = def.x;
      stickerState.y = def.y;
      stickerState.w = def.w;
      stickerState.rotation = def.rotation || 0;
      stickerState.opacity = def.opacity !== undefined ? def.opacity : 1.0;
      stickerState.visible = def.visible !== undefined ? def.visible : true;
      stickerState.pill = def.pill !== undefined ? def.pill : true;
    }

    if (objects.length === 0) {
      const defGroup = createDefaultLogoGroup(template, brandData);
      if (defGroup) {
        defGroup.x = stickerState.x;
        defGroup.y = stickerState.y;
        defGroup.rotation = stickerState.rotation;
        defGroup.pill = { enabled: stickerState.pill };
        objects = [defGroup];
      }
    }
  }
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

  function ungroupLogo() {
    const idx = objects.findIndex((o) => o.id === "logo" && o.type === "group");
    if (idx === -1) return;
    const group = objects[idx];
    recordSnapshot();

    const newObjs = [];
    const children = group.children || [];
    const imgChild = children.find((c) => c.type === "image" || c.id === "logo_img");
    const txtChild = children.find((c) => c.type === "text" || c.id === "logo_text");

    if (imgChild) {
      newObjs.push({
        id: "logo_img",
        type: "image",
        src: imgChild.src || "brand",
        x: Math.max(0, Math.min(1, group.x + (imgChild.dx || 0))),
        y: Math.max(0, Math.min(1, group.y + (imgChild.dy || 0))),
        w: imgChild.w || 0.08,
        rotation: group.rotation || 0,
        z: group.z || 10,
        visible: imgChild.visible !== false,
      });
    }

    if (txtChild) {
      newObjs.push({
        id: "logo_text",
        type: "text",
        text: txtChild.text || "TAIO.CLUB",
        x: Math.max(0, Math.min(1, group.x + (txtChild.dx || 0))),
        y: Math.max(0, Math.min(1, group.y + (txtChild.dy || 0))),
        style: txtChild.style || {
          font: "BeVietnamPro",
          weight: "Black",
          size: 0.035,
          color: "#FFFFFF",
        },
        rotation: group.rotation || 0,
        z: (group.z || 10) + 1,
        visible: txtChild.visible !== false,
      });
    }

    objects.splice(idx, 1, ...newObjs);
    selectedId = newObjs.length > 0 ? newObjs[0].id : null;
    selectedChildId = null;
    notifyChange();
  }

  function deleteSelected() {
    recordSnapshot();
    if (selectedChildId && selectedId === "logo") {
      const group = objects.find((o) => o.id === "logo");
      if (group && group.children) {
        group.children = group.children.filter((c) => c.id !== selectedChildId);
        if (group.children.length === 1) {
          group.children[0].dx = 0;
          group.children[0].dy = 0;
        } else if (group.children.length === 0) {
          objects = objects.filter((o) => o.id !== "logo");
          selectedId = null;
        }
        selectedChildId = null;
        notifyChange();
        return;
      }
    }

    if (selectedId) {
      objects = objects.filter((o) => o.id !== selectedId);
      selectedId = null;
      selectedChildId = null;
      notifyChange();
    }
  }

  function duplicateSelected() {
    if (!selectedId) return;
    const obj = objects.find((o) => o.id === selectedId);
    if (!obj) return;

    recordSnapshot();
    const cloned = JSON.parse(JSON.stringify(obj));
    cloned.id = `${obj.type}_${Date.now().toString(36)}`;
    cloned.x = Math.min(0.95, (cloned.x || 0.5) + 0.04);
    cloned.y = Math.min(0.95, (cloned.y || 0.5) + 0.04);
    cloned.z = (cloned.z || 10) + 1;

    objects.push(cloned);
    selectedId = cloned.id;
    selectedChildId = null;
    notifyChange();
  }

  function addFreeText() {
    const textCount =
      objects.filter((o) => o.type === "text").length +
      objects
        .filter((o) => o.type === "group")
        .reduce((acc, g) => acc + (g.children || []).filter((c) => c.type === "text").length, 0);

    if (textCount >= 10) {
      alert("Đã đạt giới hạn tối đa 10 đối tượng chữ mỗi video.");
      return null;
    }

    const id = `text_${Date.now().toString(36)}`;
    const newObj = {
      id: id,
      type: "text",
      text: "Nhập chữ…",
      x: 0.5,
      y: 0.28,
      rotation: 0,
      z: 20,
      style: {
        font: "BeVietnamPro",
        weight: "Bold",
        size: 0.045,
        color: "#FFFFFF",
        accent: "#FFD34D",
        stroke_width: 1,
        stroke_color: "#000000",
        shadow_dy: 2,
        shadow_color: "#00000088",
        align: "center",
      },
    };

    recordSnapshot();
    objects.push(newObj);
    selectObject(id);
    notifyChange();

    setTimeout(() => {
      const res = window.prompt("Nhập nội dung chữ:", "Nhập chữ…");
      if (res !== null && res.trim()) {
        recordSnapshot();
        newObj.text = res.trim();
        notifyChange();
      }
    }, 100);

    return newObj;
  }

  function moveLayer(direction) {
    if (!selectedId) return;
    const obj = objects.find((o) => o.id === selectedId);
    if (!obj) return;

    recordSnapshot();
    if (direction === "up") {
      obj.z = (obj.z || 10) + 1;
    } else if (direction === "down") {
      obj.z = Math.max(1, (obj.z || 10) - 1);
    }
    notifyChange();
  }

  window.TAIOSceneStore = {
    subscribe,
    resolveTemplateDefault,
    initTemplateScene,
    createDefaultLogoGroup,
    saveToLocalStorage,
    loadFromLocalStorage,
    recordSnapshot,
    undo,
    redo,
    notifyChange,
    getOverrides,
    selectObject,
    clearSelection,
    ungroupLogo,
    deleteSelected,
    duplicateSelected,
    addFreeText,
    moveLayer,
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
