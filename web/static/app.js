/**
 * TAIO Cover Studio - Trình điều khiển WYSIWYG Siêu Gọn
 * Tối ưu hóa tuyệt đối cho Mobile & Thao tác 1-chạm
 */

(function () {
  "use strict";

  const state = {
    video: null,          // { id, name, info }
    videoFile: null,      // Đối tượng File gốc trong bộ nhớ để tự khôi phục
    videoUrl: null,       // Đường dẫn URL video gốc để tự khôi phục
    bootId: null,         // boot_id từ máy chủ
    templateId: "lower_third_fade", // Mẫu A (Mờ dần) mặc định
    caption: "",
    logoId: null,
    timeSec: 1.0,
    config: null,
    currentJobId: null,
    pollTimer: null,
    previewDebounceTimer: null,
    previewRequestId: 0,
  };

  // DOM Elements
  const clipNameBadge = document.getElementById("clipNameBadge");
  const btnTriggerUpload = document.getElementById("btnTriggerUpload");
  const videoFileInput = document.getElementById("videoFileInput");
  const dropEmptyState = document.getElementById("dropEmptyState");
  const dropUrlBox = document.getElementById("dropUrlBox");
  const videoUrlInput = document.getElementById("videoUrlInput");
  const btnLoadVideoUrl = document.getElementById("btnLoadVideoUrl");
  const urlErrorHint = document.getElementById("urlErrorHint");
  const previewImage = document.getElementById("previewImage");
  const playerResultVideo = document.getElementById("playerResultVideo");
  const previewLoadingOverlay = document.getElementById("previewLoadingOverlay");
  const previewTopPills = document.getElementById("previewTopPills");
  const videoMetaBadge = document.getElementById("videoMetaBadge");
  const btnChangeVideo = document.getElementById("btnChangeVideo");
  const previewBottomBar = document.getElementById("previewBottomBar");
  const timelineSlider = document.getElementById("timelineSlider");
  const timelineTimeLabel = document.getElementById("timelineTimeLabel");
  const timelineDurationLabel = document.getElementById("timelineDurationLabel");

  // Controls
  const templatePillsBar = document.getElementById("templatePillsBar");
  const captionInput = document.getElementById("captionInput");
  const liveHighlightText = document.getElementById("liveHighlightText");
  const btnOpenAIModal = document.getElementById("btnOpenAIModal");
  const logoThumbnailImg = document.getElementById("logoThumbnailImg");
  const logoStatusLabel = document.getElementById("logoStatusLabel");
  const logoFileInput = document.getElementById("logoFileInput");
  const btnUploadCustomLogo = document.getElementById("btnUploadCustomLogo");
  const btnResetDefaultLogo = document.getElementById("btnResetDefaultLogo");
  const warningBanner = document.getElementById("warningBanner");
  const warningText = document.getElementById("warningText");

  // Actions
  const btnRenderVideo = document.getElementById("btnRenderVideo");
  const renderProgressCard = document.getElementById("renderProgressCard");
  const renderStatusText = document.getElementById("renderStatusText");
  const renderPctText = document.getElementById("renderPctText");
  const renderProgressBar = document.getElementById("renderProgressBar");
  const renderDoneActions = document.getElementById("renderDoneActions");
  const btnSaveToPhotos = document.getElementById("btnSaveToPhotos");
  const btnDownloadVideo = document.getElementById("btnDownloadVideo");
  const btnSendTelegram = document.getElementById("btnSendTelegram");
  const renderErrorMsg = document.getElementById("renderErrorMsg");

  // Modals
  const aiModal = document.getElementById("aiModal");
  const btnCloseAIModal = document.getElementById("btnCloseAIModal");
  const aiProviderSelect = document.getElementById("aiProviderSelect");
  const aiStyleSelect = document.getElementById("aiStyleSelect");
  const aiContextInput = document.getElementById("aiContextInput");
  const btnGenerateAI = document.getElementById("btnGenerateAI");
  const aiCardsContainer = document.getElementById("aiCardsContainer");

  const telegramModal = document.getElementById("telegramModal");
  const btnCloseTeleModal = document.getElementById("btnCloseTeleModal");
  const teleBotTokenInput = document.getElementById("teleBotTokenInput");
  const teleChatIdInput = document.getElementById("teleChatIdInput");
  const btnConfirmSendTelegram = document.getElementById("btnConfirmSendTelegram");
  const teleStatusMsg = document.getElementById("teleStatusMsg");

  // ==================== KHỞI TẠO ====================
  async function init() {
    try {
      const res = await fetch("/api/config");
      if (res.ok) {
        state.config = await res.json();
        state.bootId = state.config.boot_id || null;
        if (state.config.version_info) {
          const appVersionBadge = document.getElementById("appVersionBadge");
          if (appVersionBadge) {
            appVersionBadge.textContent = state.config.version_info.label;
          }
        }
        if (window.TAIOLayerControls) {
          window.TAIOLayerControls.init({
            container: document.getElementById("layerControlsStrip"),
            palettes: state.config.palettes || null,
            onChange: () => {
              debouncedPreview();
            },
          });
        }
        renderTemplatePills();
        renderAIProviders();
      }
    } catch (e) {
      console.warn("Chưa tải được config:", e);
    }

    // Xoá token khỏi localStorage để bảo vệ bảo mật
    localStorage.removeItem("taio_tele_token");

    const defaultChatId = (state.config && state.config.telegram) ? state.config.telegram.default_chat_id : "";
    const savedChatId = localStorage.getItem("taio_tele_chatid") || defaultChatId || "";
    if (savedChatId) teleChatIdInput.value = savedChatId;

    // Ẩn trường nhập bot token trên giao diện vì token cấu hình tại server
    if (teleBotTokenInput) {
      teleBotTokenInput.style.display = "none";
      const tokenLabel = teleBotTokenInput.previousElementSibling;
      if (tokenLabel && tokenLabel.classList && tokenLabel.classList.contains("tele-label")) {
        tokenLabel.style.display = "none";
      }
    }

    bindEvents();
    renderLiveHighlightPreview("");

    // Khởi tạo bộ tương tác Sticker (FEATURE v1.2 P3)
    if (window.TAIOSticker) {
      window.TAIOSticker.init({
        previewWrapper: previewWrapper,
        previewImage: previewImage,
        onOverridesChanged: (overrides, meta) => {
          if (meta && meta.type === "object_transform") {
            return;
          }
          debouncedPreview();
        },
      });
      if (state.config && state.config.safe_zones) {
        window.TAIOSticker.setSafeZonesConfig(state.config.safe_zones);
      }
    }

    // Khởi tạo bảng Aa Tuỳ chỉnh chữ (FEATURE v1.2 P4)
    if (window.TAIOTextPanel) {
      window.TAIOTextPanel.init({
        onStyleChanged: () => {
          debouncedPreview();
        },
      });
      if (state.config) {
        window.TAIOTextPanel.setConfig(state.config);
      }
    }

    // Khởi tạo module lưu ảnh Cuộn Camera (FIX v1.3.1)
    if (window.TAIOSavePhotos) {
      window.TAIOSavePhotos.init({
        btnSave: btnSaveToPhotos,
        statusEl: renderErrorMsg,
        onRetryRender: () => {
          showRenderFailedWithRetry();
        },
      });
    }

    if (previewImage) {
      previewImage.addEventListener("load", () => {
        if (window.TAIOSticker) {
          window.TAIOSticker.updateCanvasLayout();
        }
      });
    }
  }

  function renderTemplatePills() {
    if (!state.config || !state.config.templates) return;
    templatePillsBar.innerHTML = "";
    const templates = state.config.templates;
    if (templates.length > 0 && !state.templateId) {
      state.templateId = templates[0].id;
    }

    templates.forEach((tpl, idx) => {
      const letter = String.fromCharCode(65 + idx); // A, B, C, D...
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = `tpl-pill ${tpl.id === state.templateId ? "active" : ""}`;
      btn.dataset.id = tpl.id;
      btn.innerHTML = `
        <span class="tpl-letter">${letter}</span>
        <span class="tpl-shortname">${escapeHtml(tpl.short_name || tpl.name)}</span>
      `;
      btn.addEventListener("click", () => {
        templatePillsBar.querySelectorAll(".tpl-pill").forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        state.templateId = tpl.id;
        if (window.TAIOSticker) {
          window.TAIOSticker.setTemplate(tpl, state.config ? state.config.brand : null);
        }
        if (window.TAIOLayerControls) {
          window.TAIOLayerControls.setTemplate(tpl, state.config ? state.config.palettes : null);
        }
        debouncedPreview();
      });
      templatePillsBar.appendChild(btn);
    });

    const activeTpl = templates.find((t) => t.id === state.templateId) || templates[0];
    if (activeTpl && window.TAIOSticker) {
      window.TAIOSticker.setTemplate(activeTpl, state.config ? state.config.brand : null);
    }
    if (activeTpl && window.TAIOLayerControls) {
      window.TAIOLayerControls.setTemplate(activeTpl, state.config ? state.config.palettes : null);
    }
  }

  function renderAIProviders() {
    if (!state.config || !state.config.ai) return;
    aiProviderSelect.innerHTML = "";
    (state.config.ai.providers || []).forEach((p) => {
      const opt = document.createElement("option");
      opt.value = p.id;
      opt.textContent = `${p.label} ${p.ready ? "✓" : "⚠️"}`;
      if (p.id === state.config.ai.default) opt.selected = true;
      aiProviderSelect.appendChild(opt);
    });
  }

  // ==================== SỰ KIỆN GIAO DIỆN ====================
  function bindEvents() {
    // 1. Tải Video (Tệp hoặc URL)
    btnTriggerUpload.addEventListener("click", () => videoFileInput.click());
    btnChangeVideo.addEventListener("click", () => resetToPickVideo());
    videoFileInput.addEventListener("change", (e) => {
      if (e.target.files && e.target.files[0]) uploadVideo(e.target.files[0]);
    });

    if (dropUrlBox) {
      dropUrlBox.addEventListener("click", (e) => {
        e.stopPropagation();
      });
    }

    if (btnLoadVideoUrl) {
      btnLoadVideoUrl.addEventListener("click", () => {
        if (videoUrlInput) loadVideoFromUrl(videoUrlInput.value.trim());
      });
    }

    if (videoUrlInput) {
      videoUrlInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
          e.preventDefault();
          loadVideoFromUrl(videoUrlInput.value.trim());
        }
      });
    }

    // 2. Mẫu lớp phủ được tạo động qua renderTemplatePills()

    // 3. Caption & Highlight thời gian thực
    captionInput.addEventListener("input", (e) => {
      state.caption = e.target.value;
      renderLiveHighlightPreview(state.caption);
      debouncedPreview();
    });

    // 4. Timeline
    timelineSlider.addEventListener("input", (e) => {
      state.timeSec = parseFloat(e.target.value);
      formatTimelineLabels();
      debouncedPreview();
    });

    // 5. Logo
    btnUploadCustomLogo.addEventListener("click", () => logoFileInput.click());
    logoFileInput.addEventListener("change", (e) => {
      if (e.target.files && e.target.files[0]) uploadLogo(e.target.files[0]);
    });
    btnResetDefaultLogo.addEventListener("click", () => {
      state.logoId = null;
      logoThumbnailImg.src = "/static/brand-logo";
      logoStatusLabel.textContent = "Logo TAIO";
      btnResetDefaultLogo.hidden = true;
      if (window.TAIOSticker) {
        window.TAIOSticker.setLogoId(null);
      }
      debouncedPreview();
    });

    // 6. Action Render
    btnRenderVideo.addEventListener("click", startRender);

    // 7. Save to Camera Roll (được quản lý bởi save-photos.js)

    // 8. Telegram Modal
    btnSendTelegram.addEventListener("click", openTelegramModal);
    btnCloseTeleModal.addEventListener("click", () => (telegramModal.hidden = true));
    btnConfirmSendTelegram.addEventListener("click", sendVideoToTelegram);

    // 9. AI Modal
    btnOpenAIModal.addEventListener("click", () => (aiModal.hidden = false));
    btnCloseAIModal.addEventListener("click", () => (aiModal.hidden = true));
    btnGenerateAI.addEventListener("click", generateCaptionsAI);
  }

  // ==================== TẢI LÊN VIDEO & TỰ PHỤC HỒI ====================
  function resetToPickVideo(msg) {
    if (window.TAIOSavePhotos) {
      window.TAIOSavePhotos.cleanup();
    }
    state.video = null;
    state.videoFile = null;
    state.videoUrl = null;
    state.currentJobId = null;
    clearInterval(state.pollTimer);

    if (videoUrlInput) videoUrlInput.value = "";
    if (urlErrorHint) urlErrorHint.hidden = true;

    dropEmptyState.hidden = false;
    previewImage.hidden = true;
    playerResultVideo.hidden = true;
    previewTopPills.hidden = true;
    previewBottomBar.hidden = true;
    btnRenderVideo.disabled = true;
    renderProgressCard.hidden = true;

    const logoSticker = document.getElementById("logoSticker");
    if (logoSticker) logoSticker.hidden = true;

    if (msg) {
      alert(msg);
    }
  }

  async function ensureVideoOnServer() {
    if (state.videoFile) {
      renderProgressCard.hidden = false;
      renderStatusText.textContent = "Máy chủ vừa khởi động lại, đang tải lại video…";
      renderPctText.textContent = "...";
      renderProgressBar.style.width = "40%";
      previewLoadingOverlay.hidden = false;

      const formData = new FormData();
      formData.append("file", state.videoFile);
      formData.append("kind", "video");

      const res = await fetch("/api/upload", { method: "POST", body: formData });
      const data = await res.json();
      if (!res.ok) {
        previewLoadingOverlay.hidden = true;
        throw new Error(data.error || "Không thể tải lại video lên máy chủ");
      }

      state.video = data;
      clipNameBadge.textContent = data.name || "TAIO.CoverClip";
    } else if (state.videoUrl) {
      renderProgressCard.hidden = false;
      renderStatusText.textContent = "Máy chủ vừa khởi động lại, đang tải lại URL video…";
      renderPctText.textContent = "...";
      renderProgressBar.style.width = "40%";
      previewLoadingOverlay.hidden = false;

      const res = await fetch("/api/upload-url", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: state.videoUrl }),
      });
      const data = await res.json();
      if (!res.ok) {
        previewLoadingOverlay.hidden = true;
        throw new Error(data.error || "Không thể tải lại video từ URL");
      }

      state.video = data;
      clipNameBadge.textContent = data.name || "TAIO.CoverClip";
    } else {
      resetToPickVideo("Phiên làm việc đã hết hạn, vui lòng chọn lại video.");
      throw new Error("Phiên làm việc đã hết hạn, vui lòng chọn lại video.");
    }

    try {
      const cfgRes = await fetch("/api/config");
      if (cfgRes.ok) {
        const cfgData = await cfgRes.json();
        state.bootId = cfgData.boot_id || null;
      }
    } catch (_) {}

    previewLoadingOverlay.hidden = true;
    return state.video;
  }

  async function fetchWithVideoRecovery(url, options = {}, retryCount = 1) {
    const res = await fetch(url, options);
    if (!res.ok) {
      const clone = res.clone();
      const errJson = await clone.json().catch(() => ({}));
      if (errJson.code === "VIDEO_NOT_FOUND" && retryCount > 0 && state.videoFile) {
        await ensureVideoOnServer();
        if (options.body && typeof options.body === "string") {
          try {
            const bodyObj = JSON.parse(options.body);
            if (bodyObj.video_id) {
              bodyObj.video_id = state.video.id;
              options.body = JSON.stringify(bodyObj);
            }
          } catch (_) {}
        }
        return fetchWithVideoRecovery(url, options, retryCount - 1);
      }
    }
    return res;
  }

  async function uploadVideo(file) {
    if (window.TAIOSavePhotos) {
      window.TAIOSavePhotos.cleanup();
    }
    state.videoFile = file;
    previewLoadingOverlay.hidden = false;
    renderErrorMsg.hidden = true;

    const formData = new FormData();
    formData.append("file", file);
    formData.append("kind", "video");

    try {
      const res = await fetch("/api/upload", { method: "POST", body: formData });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Lỗi khi tải video");

      state.video = data;

      // Cập nhật tên chuẩn hoá theo quy ước (TAIO.CoverClip_071101.mp4)
      clipNameBadge.textContent = data.name || "TAIO.CoverClip";
      if (data.info) {
        videoMetaBadge.textContent = `${data.info.width}×${data.info.height} · ${data.info.formatted_duration || "0:00"}`;
        timelineSlider.max = Math.max(data.info.duration || 10, 1);
        timelineDurationLabel.textContent = `/ ${data.info.formatted_duration || "0:00"}`;
      }

      dropEmptyState.hidden = true;
      playerResultVideo.hidden = true;
      previewTopPills.hidden = false;
      previewBottomBar.hidden = false;
      btnRenderVideo.disabled = false;

      formatTimelineLabels();
      triggerPreview();
    } catch (err) {
      alert("Lỗi tải video: " + err.message);
    } finally {
      previewLoadingOverlay.hidden = true;
    }
  }

  async function loadVideoFromUrl(url) {
    if (!url) {
      if (urlErrorHint) {
        urlErrorHint.textContent = "Vui lòng nhập đường dẫn URL video.";
        urlErrorHint.hidden = false;
      }
      return;
    }

    if (!url.startsWith("http://") && !url.startsWith("https://")) {
      if (urlErrorHint) {
        urlErrorHint.textContent = "Đường dẫn URL phải bắt đầu bằng http:// hoặc https://";
        urlErrorHint.hidden = false;
      }
      return;
    }

    if (urlErrorHint) urlErrorHint.hidden = true;
    if (btnLoadVideoUrl) {
      btnLoadVideoUrl.disabled = true;
      btnLoadVideoUrl.textContent = "Đang tải…";
    }
    previewLoadingOverlay.hidden = false;
    renderErrorMsg.hidden = true;

    if (window.TAIOSavePhotos) {
      window.TAIOSavePhotos.cleanup();
    }

    try {
      const res = await fetch("/api/upload-url", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: url }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Không thể tải video từ URL");

      state.video = data;
      state.videoUrl = url;
      state.videoFile = null;

      clipNameBadge.textContent = data.name || "TAIO.CoverClip";
      if (data.info) {
        videoMetaBadge.textContent = `${data.info.width}×${data.info.height} · ${data.info.formatted_duration || "0:00"}`;
        timelineSlider.max = Math.max(data.info.duration || 10, 1);
        timelineDurationLabel.textContent = `/ ${data.info.formatted_duration || "0:00"}`;
      }

      dropEmptyState.hidden = true;
      playerResultVideo.hidden = true;
      previewTopPills.hidden = false;
      previewBottomBar.hidden = false;
      btnRenderVideo.disabled = false;
      renderDoneActions.hidden = true;

      formatTimelineLabels();
      triggerPreview();
      if (videoUrlInput) videoUrlInput.value = "";
    } catch (err) {
      if (urlErrorHint) {
        urlErrorHint.textContent = err.message || "Lỗi khi tải URL";
        urlErrorHint.hidden = false;
      }
    } finally {
      if (btnLoadVideoUrl) {
        btnLoadVideoUrl.disabled = false;
        btnLoadVideoUrl.textContent = "Tải URL";
      }
      previewLoadingOverlay.hidden = true;
    }
  }

  async function uploadLogo(file) {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("kind", "logo");

    try {
      const res = await fetch("/api/upload", { method: "POST", body: formData });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Lỗi tải logo");

      state.logoId = data.id;
      logoThumbnailImg.src = URL.createObjectURL(file);
      logoStatusLabel.textContent = "Logo riêng";
      btnResetDefaultLogo.hidden = false;
      if (window.TAIOSticker) {
        window.TAIOSticker.setLogoId(state.logoId);
      }
      debouncedPreview();
    } catch (err) {
      alert("Lỗi logo: " + err.message);
    }
  }

  // ==================== LIVE HIGHLIGHT PREVIEW TRÊN UI ====================
  function renderLiveHighlightPreview(raw) {
    if (!raw || !raw.trim()) {
      liveHighlightText.innerHTML = '<span style="color:#64748B">Chưa nhập</span>';
      return;
    }

    // Regex tìm ==từ nhấn 2== (xanh) và **từ nhấn 1** (vàng)
    const clean = escapeHtml(raw);
    let highlighted = clean.replace(
      /==(.*?)==/gi,
      '<span class="accent-word-2">$1</span>'
    );
    highlighted = highlighted.replace(
      /(?:\*\*|\*|&lt;b&gt;)(.*?)(?:\*\*|\*|&lt;\/b&gt;)/gi,
      '<span class="accent-word">$1</span>'
    );
    liveHighlightText.innerHTML = highlighted;
  }

  // ==================== XEM TRƯỚC (PREVIEW) ====================
  function debouncedPreview() {
    clearTimeout(state.previewDebounceTimer);
    state.previewDebounceTimer = setTimeout(triggerPreview, 250);
  }

  async function triggerPreview() {
    if (!state.video) return;

    const reqId = ++state.previewRequestId;
    previewLoadingOverlay.hidden = false;

    try {
      const stickerOverrides = window.TAIOSticker ? window.TAIOSticker.getOverrides() : {};
      const captionOverrides = window.TAIOTextPanel ? window.TAIOTextPanel.getCaptionOverrides() : {};
      const layerOverrides = window.TAIOLayerControls ? window.TAIOLayerControls.getOverrides() : {};
      const combinedOverrides = {
        layers: {
          ...(layerOverrides.layers || {}),
          ...(stickerOverrides.layers || {}),
          caption: captionOverrides,
        },
      };
      if (stickerOverrides.objects && stickerOverrides.objects.length > 0) {
        combinedOverrides.objects = stickerOverrides.objects;
      }

      const payload = {
        video_id: state.video.id,
        template: state.templateId,
        caption: state.caption,
        t: state.timeSec,
        logo_id: state.logoId,
        overrides: combinedOverrides,
        exclude_layers: ["logo"],
        exclude_objects: true,
      };

      const res = await fetchWithVideoRecovery("/api/preview", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (reqId < state.previewRequestId) {
        return; // Request cũ hơn, bỏ qua
      }

      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        const err = new Error(errJson.error || "Lỗi cập nhật ảnh xem trước");
        err.code = errJson.code;
        throw err;
      }

      // Đọc cảnh báo từ header X-Warnings
      const hexWarnings = res.headers.get("X-Warnings");
      if (hexWarnings) {
        try {
          const bytes = new Uint8Array(hexWarnings.match(/.{1,2}/g).map((b) => parseInt(b, 16)));
          const decoded = new TextDecoder("utf-8").decode(bytes);
          if (decoded.trim()) {
            warningText.textContent = decoded;
            warningBanner.hidden = false;
          } else {
            warningBanner.hidden = true;
          }
        } catch (e) {
          warningBanner.hidden = true;
        }
      } else {
        warningBanner.hidden = true;
      }

      const blob = await res.blob();
      if (reqId < state.previewRequestId) return;

      previewImage.src = URL.createObjectURL(blob);
      previewImage.classList.remove("stale");
      previewImage.style.opacity = "1";
      previewImage.hidden = false;
      playerResultVideo.hidden = true;

      const logoSticker = document.getElementById("logoSticker");
      if (logoSticker) {
        logoSticker.hidden = false;
      }
      if (window.TAIOSticker) {
        window.TAIOSticker.updateCanvasLayout();
      }
    } catch (err) {
      if (reqId < state.previewRequestId) return;
      // Không giữ ảnh cũ im lặng: hiện cảnh báo và làm mờ ảnh
      previewImage.classList.add("stale");
      previewImage.style.opacity = "0.4";
      warningText.textContent = "Không thể cập nhật xem trước: " + (err.message || "Mất kết nối máy chủ");
      warningBanner.hidden = false;
      console.warn("Preview warning:", err);
    } finally {
      if (reqId === state.previewRequestId) {
        previewLoadingOverlay.hidden = true;
      }
    }
  }

  function formatTimelineLabels() {
    const sec = Math.floor(state.timeSec);
    const m = Math.floor(sec / 60);
    const s = sec % 60;
    timelineTimeLabel.textContent = `${m}:${s < 10 ? "0" : ""}${s}`;
  }

  // ==================== XUẤT VIDEO ====================
  async function startRender() {
    if (!state.video) return;

    if (window.TAIOSavePhotos) {
      window.TAIOSavePhotos.cleanup();
    }

    btnRenderVideo.disabled = true;
    renderProgressCard.hidden = false;
    renderDoneActions.hidden = true;
    renderErrorMsg.hidden = true;
    renderStatusText.textContent = "Đang xử lý...";
    renderPctText.textContent = "0%";
    renderProgressBar.style.width = "0%";

    try {
      const stickerOverrides = window.TAIOSticker ? window.TAIOSticker.getOverrides() : {};
      const captionOverrides = window.TAIOTextPanel ? window.TAIOTextPanel.getCaptionOverrides() : {};
      const layerOverrides = window.TAIOLayerControls ? window.TAIOLayerControls.getOverrides() : {};
      const combinedOverrides = {
        layers: {
          ...(layerOverrides.layers || {}),
          ...(stickerOverrides.layers || {}),
          caption: captionOverrides,
        },
      };
      if (stickerOverrides.objects && stickerOverrides.objects.length > 0) {
        combinedOverrides.objects = stickerOverrides.objects;
      }

      const payload = {
        video_id: state.video.id,
        video_name: state.video.name,
        template: state.templateId,
        caption: state.caption,
        logo_id: state.logoId,
        overrides: combinedOverrides,
      };

      const res = await fetchWithVideoRecovery("/api/render", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Lỗi tạo lệnh xuất");

      state.currentJobId = data.job_id;
      pollJobStatus();
    } catch (err) {
      renderErrorMsg.textContent = err.message;
      renderErrorMsg.hidden = false;
      btnRenderVideo.disabled = false;
      renderProgressCard.hidden = true;
    }
  }

  function showRenderFailedWithRetry(customMsg) {
    btnRenderVideo.disabled = false;
    renderProgressBar.style.width = "0%";
    renderPctText.textContent = "";
    renderStatusText.textContent = "Tiến trình bị gián đoạn";

    const msg = customMsg || "Máy chủ bị khởi động lại khi đang xuất (thường do thiếu RAM).";
    renderErrorMsg.innerHTML = `${escapeHtml(msg)} <button type="button" id="btnRetryRender" style="margin-left:8px;padding:4px 12px;border-radius:6px;background:#3B82F6;color:#fff;border:none;cursor:pointer;font-weight:600">Xuất lại</button>`;
    renderErrorMsg.hidden = false;

    const retryBtn = document.getElementById("btnRetryRender");
    if (retryBtn) {
      retryBtn.onclick = async () => {
        renderErrorMsg.hidden = true;
        try {
          await ensureVideoOnServer();
          startRender();
        } catch (e) {
          renderErrorMsg.textContent = e.message;
          renderErrorMsg.hidden = false;
        }
      };
    }
  }

  function pollJobStatus() {
    clearInterval(state.pollTimer);
    let networkErrorCount = 0;
    const pollStartTime = Date.now();
    const MAX_POLL_MS = 20 * 60 * 1000; // Thời gian chờ tối đa 20 phút

    state.pollTimer = setInterval(async () => {
      if (!state.currentJobId) {
        clearInterval(state.pollTimer);
        return;
      }

      if (Date.now() - pollStartTime > MAX_POLL_MS) {
        clearInterval(state.pollTimer);
        showRenderFailedWithRetry("Quá thời gian chờ xuất video (20 phút). Bấm Xuất lại.");
        return;
      }

      try {
        const res = await fetch(`/api/job/${state.currentJobId}`);
        networkErrorCount = 0;

        if (res.status === 404) {
          clearInterval(state.pollTimer);
          showRenderFailedWithRetry();
          return;
        }

        const job = await res.json();

        // Kiểm tra nếu máy chủ khởi động lại và đổi boot_id
        if (job.boot_id && state.bootId && job.boot_id !== state.bootId) {
          clearInterval(state.pollTimer);
          state.bootId = job.boot_id;
          showRenderFailedWithRetry();
          return;
        }

        if (job.status === "running") {
          const pct = Math.round((job.progress || 0) * 100);
          renderStatusText.textContent = "Đang xuất video...";
          renderPctText.textContent = `${pct}%`;
          renderProgressBar.style.width = `${pct}%`;
        } else if (job.status === "done") {
          clearInterval(state.pollTimer);
          renderStatusText.textContent = " Xuất video thành công!";
          renderPctText.textContent = "100%";
          renderProgressBar.style.width = "100%";

          const downloadUrl = `/api/download/${state.currentJobId}`;
          btnDownloadVideo.href = downloadUrl;
          btnDownloadVideo.download = state.video.name || "TAIO.CoverClip.mp4";

          // Chuẩn bị tải sẵn file để lưu Cuộn Camera tức thì (FIX v1.3.1)
          if (window.TAIOSavePhotos) {
            window.TAIOSavePhotos.prepareResultFile(state.currentJobId, state.video.name || "TAIO.CoverClip.mp4");
          }

          // Hiển thị trực tiếp video phát thử trên khung preview
          playerResultVideo.src = downloadUrl;
          playerResultVideo.hidden = false;
          previewImage.hidden = true;

          renderDoneActions.hidden = false;
          btnRenderVideo.disabled = false;
        } else if (job.status === "error") {
          clearInterval(state.pollTimer);
          renderErrorMsg.textContent = job.error || "Lỗi khi xuất video";
          renderErrorMsg.hidden = false;
          btnRenderVideo.disabled = false;
        }
      } catch (err) {
        networkErrorCount++;
        if (networkErrorCount >= 3) {
          clearInterval(state.pollTimer);
          showRenderFailedWithRetry();
        }
      }
    }, 700);
  }

  // ==================== GỬI QUA TELEGRAM BOT ====================
  function openTelegramModal() {
    teleStatusMsg.hidden = true;
    telegramModal.hidden = false;
  }

  async function sendVideoToTelegram() {
    const chatId = teleChatIdInput.value.trim();

    if (!chatId) {
      showTeleStatus("Vui lòng điền Chat ID Telegram của bạn.", false);
      return;
    }

    // Lưu chatId vào localStorage, xoá bỏ token cũ nếu có
    localStorage.removeItem("taio_tele_token");
    localStorage.setItem("taio_tele_chatid", chatId);

    btnConfirmSendTelegram.disabled = true;
    btnConfirmSendTelegram.textContent = "Đang tải video sang Telegram...";
    teleStatusMsg.hidden = true;

    try {
      const payload = {
        job_id: state.currentJobId,
        chat_id: chatId,
      };

      const res = await fetch("/api/send-telegram", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Lỗi khi gửi video");

      showTeleStatus(data.message || "Đã gửi video thành công vào Telegram!", true);
      btnSendTelegram.textContent = "✓ Đã gửi Telegram!";
      setTimeout(() => {
        telegramModal.hidden = true;
        btnSendTelegram.textContent = "✈️ Gửi qua Telegram";
      }, 2000);
    } catch (err) {
      showTeleStatus(err.message, false);
    } finally {
      btnConfirmSendTelegram.disabled = false;
      btnConfirmSendTelegram.textContent = "🚀 Gửi video vào Telegram ngay";
    }
  }

  function showTeleStatus(msg, isSuccess) {
    teleStatusMsg.textContent = msg;
    teleStatusMsg.className = "tele-status-msg " + (isSuccess ? "success" : "error");
    teleStatusMsg.hidden = false;
  }

  // ==================== GỢI Ý AI ====================
  async function generateCaptionsAI() {
    if (!state.video) {
      alert("Vui lòng tải video lên trước.");
      return;
    }

    const btnText = btnGenerateAI.querySelector(".btn-ai-text");
    btnGenerateAI.disabled = true;
    btnText.textContent = "Đang phân tích khung hình...";

    try {
      const payload = {
        video_id: state.video.id,
        provider: aiProviderSelect.value,
        style: aiStyleSelect.value,
        context: aiContextInput.value.trim(),
        n: 5,
      };

      const res = await fetchWithVideoRecovery("/api/suggest", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Lỗi AI gợi ý");

      aiCardsContainer.innerHTML = "";
      (data.captions || []).forEach((c) => {
        const item = document.createElement("div");
        item.className = "ai-item-card";
        item.innerHTML = `
          <div class="ai-item-text">${escapeHtml(c.text)}</div>
          <div class="ai-item-tag">${escapeHtml(c.angle || "gợi ý")} · ${escapeHtml(c.why || "")}</div>
        `;
        item.addEventListener("click", () => {
          captionInput.value = c.text;
          state.caption = c.text;
          renderLiveHighlightPreview(c.text);
          debouncedPreview();
          aiModal.hidden = true;
        });
        aiCardsContainer.appendChild(item);
      });
    } catch (err) {
      alert("Lỗi AI: " + err.message);
    } finally {
      btnGenerateAI.disabled = false;
      btnText.textContent = "✨ Gợi ý 5 caption thu hút";
    }
  }

  function escapeHtml(str) {
    if (!str) return "";
    return str
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  document.addEventListener("DOMContentLoaded", init);
})();
