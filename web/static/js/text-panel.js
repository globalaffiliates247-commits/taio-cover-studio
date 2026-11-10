/**
 * TAIO Cover Studio — Text Style Customization Panel ("Aa")
 * Mượn Text Styles của CapCut và Brand Kit của Canva
 * Dạng Bottom Sheet trên mobile & Popover trên desktop với các tab:
 * 1. Kiểu sẵn (Presets)
 * 2. Font & Cỡ chữ (Hick's Law, Tinker 1963)
 * 3. Màu sắc (Màu chính, Accent 1 **, Accent 2 ==)
 * 4. Nền & Viền (TikTok lines, block, stroke, shadow)
 * 5. Khoảng cách & Vị trí (Align, Vị trí dọc, Letter-spacing)
 * Kèm kiểm tra tương phản chuẩn WCAG 2.1 (< 4.5:1)
 */

(function () {
  "use strict";

  let modalEl = null;
  let btnOpenEl = null;
  let btnCloseEl = null;
  let onStyleChangedCallback = null;
  let contrastWarnEl = null;

  // Cấu hình từ /api/config
  let fontsConfig = [];
  let defaultPresets = [];

  // Trạng thái style hiện tại
  const currentStyle = {
    font_family: "Be Vietnam Pro",
    weight: "Bold",
    case_mode: "uppercase",
    size_mode: "auto",
    size: 42,
    color: "#FFFFFF",
    accent_color: "#FFD34D",
    accent2_color: "#38BDF8",
    accent_style: "color", // 'color' | 'marker' | 'underline'
    stroke_width: 0,
    stroke_color: "#000000",
    shadow_dx: 0,
    shadow_dy: 2,
    shadow_color: "#000000",
    shadow_opacity: 0.8,
    bg_style: "none", // 'none' | 'lines' | 'block'
    bg_color: "#000000",
    bg_opacity: 0.8,
    bg_radius: 6,
    bg_padding: 8,
    align: "center",
    y_offset_ratio: 0.0,
    letter_spacing: 0.0,
    line_spacing: 1.18,
  };

  let changeDebounceTimer = null;

  /**
   * Tính độ chói tương đối (relative luminance) theo WCAG 2.1
   */
  function hexToRgb(hex) {
    let clean = hex.replace("#", "").trim();
    if (clean.length === 3) {
      clean = clean.split("").map((c) => c + c).join("");
    }
    const num = parseInt(clean, 16);
    return {
      r: (num >> 16) & 255,
      g: (num >> 8) & 255,
      b: num & 255,
    };
  }

  function getLuminance(r, g, b) {
    const a = [r, g, b].map((v) => {
      v /= 255;
      return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
    });
    return a[0] * 0.2126 + a[1] * 0.7152 + a[2] * 0.0722;
  }

  function getContrastRatio(hex1, hex2) {
    try {
      const rgb1 = hexToRgb(hex1);
      const rgb2 = hexToRgb(hex2);
      const l1 = getLuminance(rgb1.r, rgb1.g, rgb1.b);
      const l2 = getLuminance(rgb2.r, rgb2.g, rgb2.b);
      const lighter = Math.max(l1, l2);
      const darker = Math.min(l1, l2);
      return (lighter + 0.05) / (darker + 0.05);
    } catch (_) {
      return 7.0;
    }
  }

  /**
   * Kiểm tra tương phản WCAG 2.1
   */
  function checkContrast() {
    if (!contrastWarnEl) return;

    let bgHex = "#000000"; // Mặc định nền tối
    if (currentStyle.bg_style !== "none") {
      bgHex = currentStyle.bg_color || "#000000";
    }

    const textHex = currentStyle.color || "#FFFFFF";
    const ratio = getContrastRatio(textHex, bgHex);

    // WCAG 2.1 tiêu chí 1.4.3: Tối thiểu 4.5:1
    const hasStrokeOrShadow = currentStyle.stroke_width > 0 || currentStyle.shadow_dy > 0;
    if (ratio < 4.5 && !hasStrokeOrShadow && currentStyle.bg_style === "none") {
      contrastWarnEl.hidden = false;
      contrastWarnEl.innerHTML = `⚠️ Độ tương phản chữ thấp (${ratio.toFixed(1)}:1) — nên thêm viền, bóng hoặc nền chữ.`;
    } else {
      contrastWarnEl.hidden = true;
    }
  }

  /**
   * Lưu / Đọc custom presets từ localStorage
   */
  function getCustomPresets() {
    try {
      const raw = localStorage.getItem("taio_custom_text_presets");
      if (raw) return JSON.parse(raw);
    } catch (_) {}
    return [];
  }

  function saveCustomPreset(name) {
    const list = getCustomPresets();
    list.unshift({
      id: "custom_" + Date.now(),
      name: name || "Kiểu của tôi",
      style: { ...currentStyle },
    });
    try {
      localStorage.setItem("taio_custom_text_presets", JSON.stringify(list.slice(0, 10)));
    } catch (_) {}
    renderPresetsList();
  }

  let currentTarget = "caption";

  function notifyChange() {
    checkContrast();
    if (changeDebounceTimer) clearTimeout(changeDebounceTimer);
    changeDebounceTimer = setTimeout(() => {
      if (currentTarget === "caption") {
        if (typeof onStyleChangedCallback === "function") {
          onStyleChangedCallback({ ...currentStyle });
        }
      } else {
        const store = window.TAIOSceneStore;
        const views = window.TAIOEditorViews;
        if (store) {
          const obj = (store.objects || []).find((o) => o.id === currentTarget);
          if (obj && obj.type === "text") {
            if (!obj.style) obj.style = {};
            Object.assign(obj.style, currentStyle);
            obj.style.size_px = currentStyle.size || 48;
            obj.style.size = currentStyle.size || 48;
            if (views && views.loadObjectImage) {
              views.loadObjectImage(obj);
            }
            store.notifyChange();
          }
        }
      }
    }, 300);
  }

  /**
   * Render danh sách bộ kiểu có sẵn (Presets)
   */
  function renderPresetsList() {
    const container = document.getElementById("textPresetsContainer");
    if (!container) return;
    container.innerHTML = "";

    const allPresets = [...defaultPresets, ...getCustomPresets()];

    allPresets.forEach((p) => {
      const card = document.createElement("button");
      card.type = "button";
      card.className = "text-preset-card";
      card.innerHTML = `
        <div class="preset-name">${escapeHtml(p.name)}</div>
        <div class="preset-sub">${escapeHtml(p.description || "Tuỳ chỉnh")}</div>
      `;
      card.addEventListener("click", () => {
        applyStyleObject(p.style);
        notifyChange();
      });
      container.appendChild(card);
    });
  }

  function escapeHtml(str) {
    if (!str) return "";
    return str.replace(/[&<>"']/g, (m) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
    })[m]);
  }

  function applyStyleObject(st) {
    if (!st) return;
    Object.assign(currentStyle, st);
    syncDOMValues();
  }

  /**
   * Đồng bộ giá trị currentStyle vào toàn bộ controls trên UI
   */
  function syncDOMValues() {
    const selFont = document.getElementById("selFontFamily");
    const selWeight = document.getElementById("selFontWeight");
    const chkSizeAuto = document.getElementById("chkSizeAuto");
    const sliderSize = document.getElementById("sliderFontSize");
    const valSize = document.getElementById("valFontSize");

    const colorPrimary = document.getElementById("colTextPrimary");
    const colorAccent1 = document.getElementById("colTextAccent1");
    const colorAccent2 = document.getElementById("colTextAccent2");

    const selAccentStyle = document.getElementById("selAccentStyle");
    const sliderStroke = document.getElementById("sliderStrokeWidth");
    const colStroke = document.getElementById("colStrokeColor");
    const sliderShadow = document.getElementById("sliderShadowDy");
    const colShadow = document.getElementById("colShadowColor");

    const selBgStyle = document.getElementById("selBgStyle");
    const colBg = document.getElementById("colBgColor");
    const sliderBgOpacity = document.getElementById("sliderBgOpacity");

    const sliderYOffset = document.getElementById("sliderYOffset");
    const sliderLetterSpacing = document.getElementById("sliderLetterSpacing");
    const sliderLineSpacing = document.getElementById("sliderLineSpacing");

    if (selFont) selFont.value = currentStyle.font_family;
    if (selWeight) selWeight.value = currentStyle.weight;

    if (chkSizeAuto) {
      chkSizeAuto.checked = currentStyle.size_mode === "auto";
      if (sliderSize) sliderSize.disabled = chkSizeAuto.checked;
    }
    if (sliderSize) sliderSize.value = currentStyle.size || 42;
    if (valSize) valSize.textContent = `${sliderSize.value}px`;

    // Case mode buttons
    document.querySelectorAll(".btn-case-mode").forEach((btn) => {
      btn.classList.toggle("active", btn.dataset.mode === currentStyle.case_mode);
    });

    if (colorPrimary) colorPrimary.value = currentStyle.color;
    if (colorAccent1) colorAccent1.value = currentStyle.accent_color;
    if (colorAccent2) colorAccent2.value = currentStyle.accent2_color;

    if (selAccentStyle) selAccentStyle.value = currentStyle.accent_style || "color";
    if (sliderStroke) sliderStroke.value = currentStyle.stroke_width || 0;
    if (colStroke) colStroke.value = currentStyle.stroke_color || "#000000";
    if (sliderShadow) sliderShadow.value = currentStyle.shadow_dy || 0;
    if (colShadow) colShadow.value = currentStyle.shadow_color || "#000000";

    if (selBgStyle) selBgStyle.value = currentStyle.bg_style || "none";
    if (colBg) colBg.value = currentStyle.bg_color || "#000000";
    if (sliderBgOpacity) sliderBgOpacity.value = Math.round((currentStyle.bg_opacity || 0.8) * 100);

    // Alignment buttons
    document.querySelectorAll(".btn-align-mode").forEach((btn) => {
      btn.classList.toggle("active", btn.dataset.align === currentStyle.align);
    });

    if (sliderYOffset) sliderYOffset.value = Math.round((currentStyle.y_offset_ratio || 0.0) * 100);
    if (sliderLetterSpacing) sliderLetterSpacing.value = Math.round((currentStyle.letter_spacing || 0.0) * 100);
    if (sliderLineSpacing) sliderLineSpacing.value = Math.round((currentStyle.line_spacing || 1.18) * 100);

    checkContrast();
  }

  function openModal(target = "caption") {
    currentTarget = target || "caption";
    const titleEl = document.getElementById("textStyleModalTitle");
    const store = window.TAIOSceneStore;

    if (currentTarget === "caption") {
      if (titleEl) titleEl.textContent = "Đang chỉnh: Caption";
    } else {
      const obj = store ? (store.objects || []).find((o) => o.id === currentTarget) : null;
      if (obj && obj.type === "text") {
        const previewText = obj.text ? (obj.text.length > 15 ? obj.text.slice(0, 15) + "…" : obj.text) : "Nhập chữ…";
        if (titleEl) titleEl.textContent = `Đang chỉnh: Chữ tự do · '${previewText}'`;
        if (obj.style) {
          const st = { ...obj.style };
          if (st.size_px) {
            st.size = st.size_px;
          } else if (st.size) {
            st.size = st.size < 1 ? Math.round(st.size * 1080) : Math.round(st.size);
            st.size_px = st.size;
          } else {
            st.size = 48;
            st.size_px = 48;
          }
          st.size_mode = st.size_mode || "fixed";
          applyStyleObject(st);
        }
      }
    }
    syncDOMValues();
    if (modalEl) modalEl.hidden = false;
  }

  function updateSize(newSizePx) {
    currentStyle.size = newSizePx;
    currentStyle.size_px = newSizePx;
    currentStyle.size_mode = "fixed";
    const sliderSize = document.getElementById("sliderFontSize");
    const valSize = document.getElementById("valFontSize");
    const chkSizeAuto = document.getElementById("chkSizeAuto");
    if (sliderSize) {
      sliderSize.value = newSizePx;
      sliderSize.disabled = false;
    }
    if (valSize) valSize.textContent = `${newSizePx}px`;
    if (chkSizeAuto) chkSizeAuto.checked = false;
  }

  /**
   * Khởi tạo các sự kiện trong Text Panel
   */
  function bindEvents() {
    modalEl = document.getElementById("textStyleModal");
    btnOpenEl = document.getElementById("btnOpenTextStyleModal");
    btnCloseEl = document.getElementById("btnCloseTextStyleModal");
    contrastWarnEl = document.getElementById("contrastWarningBanner");

    if (btnOpenEl) {
      btnOpenEl.addEventListener("click", () => {
        openModal("caption");
      });
    }
    if (btnCloseEl) {
      btnCloseEl.addEventListener("click", () => {
        if (modalEl) modalEl.hidden = true;
      });
    }

    // Tab switching
    document.querySelectorAll(".text-tab-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        document.querySelectorAll(".text-tab-btn").forEach((b) => b.classList.remove("active"));
        document.querySelectorAll(".text-tab-content").forEach((c) => (c.hidden = true));
        btn.classList.add("active");
        const targetId = btn.dataset.tab;
        const targetContent = document.getElementById(targetId);
        if (targetContent) targetContent.hidden = false;
      });
    });

    // Preset save button
    const btnSavePreset = document.getElementById("btnSaveCurrentStyle");
    if (btnSavePreset) {
      btnSavePreset.addEventListener("click", () => {
        const name = prompt("Đặt tên cho kiểu chữ này:", "Kiểu của tôi");
        if (name && name.trim()) {
          saveCustomPreset(name.trim());
        }
      });
    }

    // Font family & weight
    const selFont = document.getElementById("selFontFamily");
    if (selFont) {
      selFont.addEventListener("change", () => {
        currentStyle.font_family = selFont.value;
        notifyChange();
      });
    }
    const selWeight = document.getElementById("selFontWeight");
    if (selWeight) {
      selWeight.addEventListener("change", () => {
        currentStyle.weight = selWeight.value;
        notifyChange();
      });
    }

    // Size mode & size slider
    const chkSizeAuto = document.getElementById("chkSizeAuto");
    const sliderSize = document.getElementById("sliderFontSize");
    const valSize = document.getElementById("valFontSize");

    if (chkSizeAuto) {
      chkSizeAuto.addEventListener("change", () => {
        currentStyle.size_mode = chkSizeAuto.checked ? "auto" : "fixed";
        if (sliderSize) sliderSize.disabled = chkSizeAuto.checked;
        notifyChange();
      });
    }
    if (sliderSize) {
      sliderSize.addEventListener("input", () => {
        currentStyle.size = parseInt(sliderSize.value, 10);
        if (valSize) valSize.textContent = `${sliderSize.value}px`;
        notifyChange();
      });
    }

    // Case mode buttons
    document.querySelectorAll(".btn-case-mode").forEach((btn) => {
      btn.addEventListener("click", () => {
        currentStyle.case_mode = btn.dataset.mode;
        syncDOMValues();
        notifyChange();
      });
    });

    // Colors
    const colPrimary = document.getElementById("colTextPrimary");
    if (colPrimary) {
      colPrimary.addEventListener("input", () => {
        currentStyle.color = colPrimary.value;
        notifyChange();
      });
    }
    const colAccent1 = document.getElementById("colTextAccent1");
    if (colAccent1) {
      colAccent1.addEventListener("input", () => {
        currentStyle.accent_color = colAccent1.value;
        notifyChange();
      });
    }
    const colAccent2 = document.getElementById("colTextAccent2");
    if (colAccent2) {
      colAccent2.addEventListener("input", () => {
        currentStyle.accent2_color = colAccent2.value;
        notifyChange();
      });
    }

    // Accent style (color, marker, underline)
    const selAccentStyle = document.getElementById("selAccentStyle");
    if (selAccentStyle) {
      selAccentStyle.addEventListener("change", () => {
        currentStyle.accent_style = selAccentStyle.value;
        notifyChange();
      });
    }

    // Stroke
    const sliderStroke = document.getElementById("sliderStrokeWidth");
    if (sliderStroke) {
      sliderStroke.addEventListener("input", () => {
        currentStyle.stroke_width = parseInt(sliderStroke.value, 10);
        notifyChange();
      });
    }
    const colStroke = document.getElementById("colStrokeColor");
    if (colStroke) {
      colStroke.addEventListener("input", () => {
        currentStyle.stroke_color = colStroke.value;
        notifyChange();
      });
    }

    // Shadow
    const sliderShadow = document.getElementById("sliderShadowDy");
    if (sliderShadow) {
      sliderShadow.addEventListener("input", () => {
        currentStyle.shadow_dy = parseInt(sliderShadow.value, 10);
        notifyChange();
      });
    }
    const colShadow = document.getElementById("colShadowColor");
    if (colShadow) {
      colShadow.addEventListener("input", () => {
        currentStyle.shadow_color = colShadow.value;
        notifyChange();
      });
    }

    // Background
    const selBgStyle = document.getElementById("selBgStyle");
    if (selBgStyle) {
      selBgStyle.addEventListener("change", () => {
        currentStyle.bg_style = selBgStyle.value;
        notifyChange();
      });
    }
    const colBg = document.getElementById("colBgColor");
    if (colBg) {
      colBg.addEventListener("input", () => {
        currentStyle.bg_color = colBg.value;
        notifyChange();
      });
    }
    const sliderBgOpacity = document.getElementById("sliderBgOpacity");
    if (sliderBgOpacity) {
      sliderBgOpacity.addEventListener("input", () => {
        currentStyle.bg_opacity = parseInt(sliderBgOpacity.value, 10) / 100;
        notifyChange();
      });
    }

    // Align buttons
    document.querySelectorAll(".btn-align-mode").forEach((btn) => {
      btn.addEventListener("click", () => {
        currentStyle.align = btn.dataset.align;
        syncDOMValues();
        notifyChange();
      });
    });

    // Vertical position (Y-Offset)
    const sliderYOffset = document.getElementById("sliderYOffset");
    if (sliderYOffset) {
      sliderYOffset.addEventListener("input", () => {
        currentStyle.y_offset_ratio = parseInt(sliderYOffset.value, 10) / 100;
        notifyChange();
      });
    }

    // Letter spacing
    const sliderLetterSpacing = document.getElementById("sliderLetterSpacing");
    if (sliderLetterSpacing) {
      sliderLetterSpacing.addEventListener("input", () => {
        currentStyle.letter_spacing = parseInt(sliderLetterSpacing.value, 10) / 100;
        notifyChange();
      });
    }

    // Line spacing
    const sliderLineSpacing = document.getElementById("sliderLineSpacing");
    if (sliderLineSpacing) {
      sliderLineSpacing.addEventListener("input", () => {
        currentStyle.line_spacing = parseInt(sliderLineSpacing.value, 10) / 100;
        notifyChange();
      });
    }
  }

  // ==================== PUBLIC API ====================
  const TAIOTextPanel = {
    init(options) {
      onStyleChangedCallback = options.onStyleChanged;
      bindEvents();
    },

    setConfig(config) {
      if (config.fonts) fontsConfig = config.fonts;
      if (config.text_styles) defaultPresets = config.text_styles;
      renderPresetsList();
    },

    getCaptionOverrides() {
      const overrides = {
        style: { ...currentStyle },
      };
      if (currentStyle.size_mode === "auto") {
        delete overrides.style.size;
      }
      return overrides;
    },

    setStyle(style) {
      applyStyleObject(style);
    },

    openModal(target) {
      openModal(target);
    },

    updateSize(newSizePx) {
      updateSize(newSizePx);
    },
  };

  window.TAIOTextPanel = TAIOTextPanel;
})();
