/**
 * TAIO Cover Studio — Export Quality Sheet (FEATURE v1.5 P2)
 * Popup chọn mức nén khi bấm "Xuất video" với ước tính dung lượng phía client.
 */

(function () {
  "use strict";

  const STORAGE_KEY_QUALITY = "taio_export_quality";
  const STORAGE_KEY_REMEMBER = "taio_export_remember_quality";

  const PROFILES = [
    {
      id: "light",
      name: "Nhẹ",
      desc: "Gửi Telegram, Zalo, xem nhanh",
      crf: 26,
      multiplier: 1.0,
      badge: "Siêu nhẹ",
    },
    {
      id: "balanced",
      name: "Cân bằng",
      desc: "Đăng TikTok, Reels, Facebook",
      crf: 23,
      multiplier: 1.5,
      badge: "Khuyên dùng",
    },
    {
      id: "high",
      name: "Chất lượng cao",
      desc: "Lưu trữ, đăng YouTube",
      crf: 20,
      multiplier: 3.0,
      badge: "Sắc nét",
    },
  ];

  let currentQuality = "balanced";
  let confirmCallback = null;
  let sheetEl = null;

  function getSavedSettings() {
    try {
      const q = localStorage.getItem(STORAGE_KEY_QUALITY) || "balanced";
      const rem = localStorage.getItem(STORAGE_KEY_REMEMBER) === "true";
      return { quality: q, remember: rem };
    } catch (_) {
      return { quality: "balanced", remember: false };
    }
  }

  function saveSettings(quality, remember) {
    try {
      localStorage.setItem(STORAGE_KEY_QUALITY, quality);
      localStorage.setItem(STORAGE_KEY_REMEMBER, remember ? "true" : "false");
    } catch (_) {}
  }

  function formatBytes(bytes) {
    if (!bytes || bytes <= 0) return "≈ 5 MB";
    const mb = bytes / (1024 * 1024);
    if (mb < 1) return `≈ ${(bytes / 1024).toFixed(0)} KB`;
    return `≈ ${mb.toFixed(1).replace(".", ",")} MB`;
  }

  function estimateSize(profile, videoInfo) {
    if (!videoInfo || !videoInfo.duration) {
      return profile.id === "light" ? "≈ 4 MB" : profile.id === "balanced" ? "≈ 7 MB" : "≈ 14 MB";
    }

    const duration = Number(videoInfo.duration) || 10;
    const w = Number(videoInfo.width) || 720;
    const h = Number(videoInfo.height) || 1280;
    const minDim = Math.min(w, h);
    const floorBr = minDim <= 720 ? 600000 : 1200000;

    let srcBr = Number(videoInfo.bit_rate) || 0;
    if (srcBr <= 0) {
      srcBr = minDim <= 720 ? 1200000 : 2500000;
    }

    const maxRate = Math.max(srcBr * profile.multiplier, floorBr);
    const audioBr = videoInfo.has_audio ? (Number(videoInfo.audio_bit_rate) || 128000) : 0;
    const totalBytes = ((maxRate + audioBr) * duration) / 8;

    return formatBytes(totalBytes);
  }

  function ensureSheetDOM() {
    sheetEl = document.getElementById("exportQualitySheet");
    if (sheetEl) return sheetEl;

    sheetEl = document.createElement("div");
    sheetEl.id = "exportQualitySheet";
    sheetEl.className = "export-quality-sheet-overlay";
    sheetEl.hidden = true;

    sheetEl.innerHTML = `
      <div class="export-sheet-container" role="dialog" aria-modal="true" aria-labelledby="exportSheetTitle">
        <div class="export-sheet-header">
          <h3 id="exportSheetTitle" class="export-sheet-title">Chọn mức nén khi xuất</h3>
          <button type="button" class="btn-sheet-close" id="btnCloseExportSheet" aria-label="Đóng">✕</button>
        </div>
        <p class="export-sheet-subtitle">Tối ưu dung lượng phù hợp cho mục đích sử dụng, không làm giảm thời gian xử lý.</p>
        
        <div class="quality-cards-grid" id="qualityCardsGrid"></div>

        <div class="export-sheet-options">
          <label class="checkbox-label remember-choice-label">
            <input type="checkbox" id="chkRememberExportQuality">
            <span>Nhớ lựa chọn, lần sau xuất luôn</span>
          </label>
        </div>

        <div class="export-sheet-actions">
          <button type="button" class="btn-primary btn-confirm-export" id="btnConfirmExportAction">
            🚀 Xuất video ngay
          </button>
        </div>
      </div>
    `;

    document.body.appendChild(sheetEl);

    // Event listeners
    sheetEl.addEventListener("click", (e) => {
      if (e.target === sheetEl) {
        close();
      }
    });

    const btnClose = sheetEl.querySelector("#btnCloseExportSheet");
    if (btnClose) btnClose.addEventListener("click", close);

    const btnConfirm = sheetEl.querySelector("#btnConfirmExportAction");
    if (btnConfirm) {
      btnConfirm.addEventListener("click", () => {
        const chkRemember = sheetEl.querySelector("#chkRememberExportQuality");
        const remember = chkRemember ? chkRemember.checked : false;
        saveSettings(currentQuality, remember);
        const cb = confirmCallback;
        close();
        if (typeof cb === "function") {
          cb(currentQuality);
        }
      });
    }

    return sheetEl;
  }

  function renderCards(videoInfo) {
    const grid = sheetEl.querySelector("#qualityCardsGrid");
    if (!grid) return;
    grid.innerHTML = "";

    PROFILES.forEach((p) => {
      const isSelected = p.id === currentQuality;
      const card = document.createElement("div");
      card.className = `quality-card ${isSelected ? "selected" : ""}`;
      card.dataset.quality = p.id;
      card.tabIndex = 0;

      const sizeStr = estimateSize(p, videoInfo);

      card.innerHTML = `
        <div class="quality-card-head">
          <span class="quality-name">${p.name}</span>
          <span class="quality-badge">${p.badge}</span>
        </div>
        <div class="quality-card-desc">${p.desc}</div>
        <div class="quality-card-size">${sizeStr} <span class="size-hint">ước tính</span></div>
        <div class="quality-check-indicator">✓</div>
      `;

      card.addEventListener("click", () => {
        currentQuality = p.id;
        grid.querySelectorAll(".quality-card").forEach((c) => {
          c.classList.toggle("selected", c.dataset.quality === p.id);
        });
      });

      grid.appendChild(card);
    });
  }

  function open(videoInfo, onConfirm, forcePrompt = false) {
    ensureSheetDOM();
    const saved = getSavedSettings();

    if (saved.remember && !forcePrompt) {
      if (typeof onConfirm === "function") {
        onConfirm(saved.quality);
        return;
      }
    }

    currentQuality = saved.quality || "balanced";
    confirmCallback = onConfirm;

    renderCards(videoInfo);

    const chkRemember = sheetEl.querySelector("#chkRememberExportQuality");
    if (chkRemember) {
      chkRemember.checked = saved.remember;
    }

    sheetEl.hidden = false;
    document.body.style.overflow = "hidden";
  }

  function close() {
    if (sheetEl) {
      sheetEl.hidden = true;
    }
    document.body.style.overflow = "";
    confirmCallback = null;
  }

  window.TAIOExportSheet = {
    open,
    close,
    getSavedSettings,
    saveSettings,
  };
})();
