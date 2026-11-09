/**
 * TAIO Cover Studio — Quick Rail (FEATURE v1.5 P6)
 * Cột icon nổi bên phải khung video kiểu TikTok (44x44px target, 28px icon).
 */

(function () {
  "use strict";

  const state = {
    railEl: null,
    mode: "editing", // "editing" | "result"
    hasShownIntro: false,
  };

  function init(options) {
    options = options || {};
    state.railEl = options.railEl || document.getElementById("quickRail");
    if (!state.railEl) return;

    renderRail();
    checkFirstTimeIntro();
  }

  function setMode(mode) {
    if (state.mode !== mode) {
      state.mode = mode;
      renderRail();
    }
  }

  function renderRail() {
    if (!state.railEl) return;
    const icons = window.TAIOIcons || { get: () => "" };
    state.railEl.innerHTML = "";

    if (state.mode === "editing") {
      // 5 nút khi đang chỉnh: Hoàn tác · Làm lại · Thêm chữ · Lớp · Tải xuống
      const buttons = [
        {
          id: "railBtnUndo",
          label: "Hoàn tác",
          icon: icons.get("undo", 24),
          action: () => {
            if (window.TAIOSceneStore) window.TAIOSceneStore.undo();
          },
        },
        {
          id: "railBtnRedo",
          label: "Làm lại",
          icon: icons.get("redo", 24),
          action: () => {
            if (window.TAIOSceneStore) window.TAIOSceneStore.redo();
          },
        },
        {
          id: "railBtnAddText",
          label: "+ Chữ",
          icon: icons.get("add_text", 24),
          action: () => {
            const btnAdd = document.getElementById("btnAddFreeText");
            if (btnAdd) btnAdd.click();
            if (window.TAIOTabs) window.TAIOTabs.openTab("add_text");
          },
        },
        {
          id: "railBtnLayers",
          label: "Lớp",
          icon: icons.get("layers", 24),
          action: () => {
            if (window.TAIOTabs) window.TAIOTabs.openTab("layers");
          },
        },
        {
          id: "railBtnDownload",
          label: "Tải xuống",
          icon: icons.get("download", 24),
          action: () => {
            if (window.TAIOExportSheet) {
              window.TAIOExportSheet.openSheet();
            } else {
              const btn = document.getElementById("btnRenderVideo");
              if (btn) btn.click();
            }
          },
        },
      ];

      buttons.forEach((item) => {
        const btn = createRailButton(item);
        state.railEl.appendChild(btn);
      });
    } else {
      // 4 nút sau khi xuất xong: Lưu / Chia sẻ · Gửi về TAIO.CLUB · Tải MP4 · Chỉnh tiếp
      const buttons = [
        {
          id: "railBtnSaveShare",
          label: "Lưu / Chia sẻ",
          icon: icons.get("share", 24),
          action: () => {
            const btn = document.getElementById("btnSaveToPhotos");
            if (btn) btn.click();
          },
        },
        {
          id: "railBtnTelegram",
          label: "Gửi về TAIO",
          icon: icons.get("telegram", 24),
          action: () => {
            const btn = document.getElementById("btnTriggerSendTelegram");
            if (btn) btn.click();
          },
        },
        {
          id: "railBtnDownloadMp4",
          label: "Tải MP4",
          icon: icons.get("mp4", 24),
          action: () => {
            const btn = document.getElementById("btnDownloadVideo");
            if (btn) btn.click();
          },
        },
        {
          id: "railBtnEditMore",
          label: "Chỉnh tiếp",
          icon: icons.get("edit", 24),
          action: () => {
            setMode("editing");
            const playerVideo = document.getElementById("playerResultVideo");
            const previewImage = document.getElementById("previewImage");
            const stickerStage = document.getElementById("stickerStage");
            if (playerVideo) playerVideo.hidden = true;
            if (previewImage) previewImage.hidden = false;
            if (stickerStage) stickerStage.hidden = false;
          },
        },
      ];

      buttons.forEach((item) => {
        const btn = createRailButton(item);
        state.railEl.appendChild(btn);
      });
    }
  }

  function createRailButton(item) {
    const wrap = document.createElement("div");
    wrap.className = "quick-rail-item";

    const tooltip = document.createElement("span");
    tooltip.className = "quick-rail-tooltip";
    tooltip.textContent = item.label;

    const btn = document.createElement("button");
    btn.type = "button";
    btn.id = item.id;
    btn.className = "quick-rail-btn";
    btn.setAttribute("aria-label", item.label);
    btn.title = item.label;
    btn.innerHTML = item.icon;
    btn.addEventListener("click", item.action);

    wrap.appendChild(tooltip);
    wrap.appendChild(btn);
    return wrap;
  }

  function checkFirstTimeIntro() {
    try {
      const shown = localStorage.getItem("taio_quick_rail_intro");
      if (shown) return;
    } catch (_) {}

    // Hiện chú thích chữ nhỏ bên trái trong 4 giây
    if (!state.railEl) return;
    state.railEl.classList.add("show-tooltips");

    const timer = setTimeout(() => {
      dismissTooltips();
    }, 4000);

    function onDismiss() {
      clearTimeout(timer);
      dismissTooltips();
      window.removeEventListener("pointerdown", onDismiss);
    }

    window.addEventListener("pointerdown", onDismiss, { once: true });
  }

  function dismissTooltips() {
    if (state.railEl) {
      state.railEl.classList.remove("show-tooltips");
    }
    try {
      localStorage.setItem("taio_quick_rail_intro", "1");
    } catch (_) {}
  }

  window.TAIOQuickRail = {
    init,
    setMode,
  };
})();
