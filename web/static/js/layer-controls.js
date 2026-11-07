/**
 * web/static/js/layer-controls.js
 * Quản lý thanh điều khiển độ mờ & màu cho các mẫu lớp phủ (FEATURE v1.3.0).
 * Tự động render controls khai báo trong template.controls (CapCut / Instagram adjustment sliders).
 */

(function () {
  "use strict";

  let containerEl = null;
  let currentTemplate = null;
  let palettesConfig = null;
  let changeCallback = null;
  let debounceTimer = null;

  // Trạng thái giá trị đang chọn cho template hiện tại: { controlId: value }
  let currentValues = {};

  const STORAGE_PREFIX = "taio_layer_controls_";

  function getStorageKey(tplId) {
    return `${STORAGE_PREFIX}${tplId}`;
  }

  function loadSavedValues(tplId) {
    try {
      const raw = localStorage.getItem(getStorageKey(tplId));
      if (raw) {
        return JSON.parse(raw);
      }
    } catch (e) {
      console.warn("Lỗi đọc layer-controls localStorage:", e);
    }
    return {};
  }

  function saveValues(tplId, values) {
    try {
      localStorage.setItem(getStorageKey(tplId), JSON.stringify(values));
    } catch (e) {
      console.warn("Lỗi ghi layer-controls localStorage:", e);
    }
  }

  function clearSavedValues(tplId) {
    try {
      localStorage.removeItem(getStorageKey(tplId));
    } catch (e) {
      console.warn("Lỗi xoá layer-controls localStorage:", e);
    }
  }

  /**
   * Khởi tạo module
   */
  function init(options) {
    options = options || {};
    containerEl = options.container || document.getElementById("layerControlsStrip");
    palettesConfig = options.palettes || null;
    changeCallback = options.onChange || null;
  }

  /**
   * Cập nhật template đang hoạt động
   */
  function setTemplate(template, palettes) {
    currentTemplate = template;
    if (palettes) palettesConfig = palettes;

    if (!containerEl) {
      containerEl = document.getElementById("layerControlsStrip");
    }
    if (!containerEl) return;

    const controls = (template && template.controls) || [];
    if (!controls || controls.length === 0) {
      containerEl.style.display = "none";
      containerEl.innerHTML = "";
      currentValues = {};
      return;
    }

    containerEl.style.display = "block";
    renderControls(controls);
  }

  /**
   * Dựng giao diện điều khiển
   */
  function renderControls(controls) {
    const saved = loadSavedValues(currentTemplate.id);
    currentValues = {};

    containerEl.innerHTML = "";
    const inner = document.createElement("div");
    inner.className = "layer-controls-inner";

    controls.forEach((ctrl) => {
      // Xác định giá trị hiện tại (ưu tiên saved, fallback default)
      let val = ctrl.default;
      if (saved && saved[ctrl.id] !== undefined) {
        val = saved[ctrl.id];
      }
      currentValues[ctrl.id] = val;

      const item = document.createElement("div");
      item.className = "layer-control-item";
      item.dataset.controlId = ctrl.id;

      if (ctrl.type === "opacity") {
        renderOpacityControl(item, ctrl, val);
      } else if (ctrl.type === "color") {
        renderColorControl(item, ctrl, val);
      }

      inner.appendChild(item);
    });

    // Nút khôi phục Mặc định
    const actionsRow = document.createElement("div");
    actionsRow.className = "layer-controls-actions";
    actionsRow.innerHTML = `
      <button type="button" class="btn-layer-reset" title="Khôi phục thiết lập gốc của mẫu">
        ↺ Mặc định
      </button>
    `;
    actionsRow.querySelector(".btn-layer-reset").addEventListener("click", () => {
      resetToDefault();
    });
    inner.appendChild(actionsRow);

    containerEl.appendChild(inner);
  }

  /**
   * Render thanh trượt Opacity (0 - 100%)
   */
  function renderOpacityControl(container, ctrl, initialVal) {
    const min = ctrl.min !== undefined ? ctrl.min : 0;
    const max = ctrl.max !== undefined ? ctrl.max : 1;
    const step = ctrl.step !== undefined ? ctrl.step : 0.01;

    // Quy đổi ra phần trăm để hiển thị (0..100)
    const currentNum = typeof initialVal === "number" ? initialVal : ctrl.default;
    const currentPct = Math.round(currentNum * 100);

    const labelRow = document.createElement("div");
    labelRow.className = "layer-control-label-row";
    labelRow.innerHTML = `
      <span class="layer-ctrl-label">${escapeHtml(ctrl.label || "Độ đậm")}</span>
      <span class="layer-ctrl-val" id="val_${ctrl.id}">${currentPct}%</span>
    `;

    const slider = document.createElement("input");
    slider.type = "range";
    slider.className = "layer-slider";
    slider.id = `slider_${ctrl.id}`;
    slider.min = min * 100;
    slider.max = max * 100;
    slider.step = step * 100;
    slider.value = currentPct;

    const valBadge = labelRow.querySelector(`#val_${ctrl.id}`);

    // Cập nhật số đọc ngay lập tức khi kéo nhưng KHÔNG gọi server
    slider.addEventListener("input", (e) => {
      const pct = parseInt(e.target.value, 10);
      valBadge.textContent = `${pct}%`;
      currentValues[ctrl.id] = pct / 100.0;
      saveValues(currentTemplate.id, currentValues);

      // Debounce 250ms cho việc gọi server preview khi dừng kéo
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => {
        notifyChange();
      }, 250);
    });

    // Khi thả chuột / ngón tay (change event)
    slider.addEventListener("change", (e) => {
      clearTimeout(debounceTimer);
      const pct = parseInt(e.target.value, 10);
      currentValues[ctrl.id] = pct / 100.0;
      saveValues(currentTemplate.id, currentValues);
      notifyChange();
    });

    container.appendChild(labelRow);
    container.appendChild(slider);
  }

  /**
   * Render bảng màu: 1 chấm Mặc định + 6 chấm palette + 1 chấm tuỳ chọn (+)
   */
  function renderColorControl(container, ctrl, initialVal) {
    let currentColor = initialVal; // null hoặc "#RRGGBB"

    const labelRow = document.createElement("div");
    labelRow.className = "layer-control-label-row";
    labelRow.innerHTML = `
      <span class="layer-ctrl-label">${escapeHtml(ctrl.label || "Màu")}</span>
      <span class="layer-ctrl-val-color-name" id="colorName_${ctrl.id}">
        ${currentColor ? currentColor : "Mặc định"}
      </span>
    `;

    const dotsRow = document.createElement("div");
    dotsRow.className = "color-dots-row";

    // 1. Chấm đầu tiên: Mặc định (null)
    const defDot = document.createElement("button");
    defDot.type = "button";
    defDot.className = `color-dot default-dot ${!currentColor ? "active" : ""}`;
    defDot.title = "Mặc định";
    defDot.dataset.color = "null";
    defDot.innerHTML = `<span class="default-slash">⊘</span>`;
    defDot.addEventListener("click", () => {
      selectColor(null, "Mặc định");
    });
    dotsRow.appendChild(defDot);

    // Lấy palette từ config hoặc fallback basic6
    let paletteItems = [];
    if (palettesConfig && ctrl.palette && palettesConfig[ctrl.palette]) {
      paletteItems = palettesConfig[ctrl.palette];
    } else {
      paletteItems = [
        { name: "Đỏ", hex: "#E53935" },
        { name: "Cam", hex: "#FB8C00" },
        { name: "Vàng", hex: "#FDD835" },
        { name: "Xanh lá", hex: "#43A047" },
        { name: "Xanh dương", hex: "#1E88E5" },
        { name: "Tím", hex: "#8E24AA" },
      ];
    }

    let isPaletteMatched = !currentColor;

    paletteItems.forEach((item) => {
      const dot = document.createElement("button");
      dot.type = "button";
      const isAct = currentColor && currentColor.toUpperCase() === item.hex.toUpperCase();
      if (isAct) isPaletteMatched = true;
      dot.className = `color-dot ${isAct ? "active" : ""}`;
      dot.title = item.name;
      dot.dataset.color = item.hex;
      dot.style.backgroundColor = item.hex;
      dot.addEventListener("click", () => {
        selectColor(item.hex, item.name);
      });
      dotsRow.appendChild(dot);
    });

    // Chấm tuỳ chọn (+)
    const customDot = document.createElement("label");
    customDot.className = `color-dot custom-dot ${currentColor && !isPaletteMatched ? "active" : ""}`;
    customDot.title = "Màu khác...";
    customDot.innerHTML = `
      <span class="custom-plus">+</span>
      <input type="color" class="custom-color-input" value="${currentColor || "#E53935"}">
    `;
    const colorInput = customDot.querySelector(".custom-color-input");
    colorInput.addEventListener("input", (e) => {
      const hex = e.target.value.toUpperCase();
      selectColor(hex, hex);
    });
    dotsRow.appendChild(customDot);

    function selectColor(hex, name) {
      currentColor = hex;
      currentValues[ctrl.id] = hex;
      saveValues(currentTemplate.id, currentValues);

      // Cập nhật giao diện dots
      dotsRow.querySelectorAll(".color-dot").forEach((d) => d.classList.remove("active"));
      if (!hex) {
        defDot.classList.add("active");
        labelRow.querySelector(`#colorName_${ctrl.id}`).textContent = "Mặc định";
      } else {
        let found = false;
        dotsRow.querySelectorAll(".color-dot[data-color]").forEach((d) => {
          if (d.dataset.color && d.dataset.color.toUpperCase() === hex.toUpperCase()) {
            d.classList.add("active");
            found = true;
          }
        });
        if (!found) {
          customDot.classList.add("active");
        }
        labelRow.querySelector(`#colorName_${ctrl.id}`).textContent = name || hex;
      }

      notifyChange();
    }

    container.appendChild(labelRow);
    container.appendChild(dotsRow);
  }

  function notifyChange() {
    if (typeof changeCallback === "function") {
      changeCallback();
    }
  }

  /**
   * Khôi phục về mặc định của template
   */
  function resetToDefault() {
    if (!currentTemplate) return;
    clearSavedValues(currentTemplate.id);
    setTemplate(currentTemplate, palettesConfig);
    notifyChange();
  }

  /**
   * Tạo payload overrides từ các controls hiện tại
   * Trả về định dạng: { layers: { <layer_id>: { opacity, color, gradient_darken } } }
   */
  function getOverrides() {
    if (!currentTemplate || !currentTemplate.controls || currentTemplate.controls.length === 0) {
      return {};
    }

    const layersOverride = {};

    currentTemplate.controls.forEach((ctrl) => {
      const val = currentValues[ctrl.id];
      const targetLayers = ctrl.layers || [];

      targetLayers.forEach((layerId) => {
        if (!layersOverride[layerId]) {
          layersOverride[layerId] = {};
        }

        if (ctrl.type === "opacity") {
          if (val !== undefined && val !== null) {
            layersOverride[layerId].opacity = Number(val);
          }
        } else if (ctrl.type === "color") {
          if (val !== undefined && val !== null && val !== "null") {
            layersOverride[layerId].color = String(val);
            if (ctrl.gradient_darken !== undefined) {
              layersOverride[layerId].gradient_darken = Number(ctrl.gradient_darken);
            }
          }
        }
      });
    });

    return { layers: layersOverride };
  }

  function escapeHtml(text) {
    if (!text) return "";
    return String(text)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  // Xuất API toàn cục
  window.TAIOLayerControls = {
    init: init,
    setTemplate: setTemplate,
    getOverrides: getOverrides,
    resetToDefault: resetToDefault,
  };
})();
