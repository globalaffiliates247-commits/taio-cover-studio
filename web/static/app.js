/**
 * TAIO Cover Studio - Trình điều khiển WYSIWYG Siêu Gọn
 * Tối ưu hóa tuyệt đối cho Mobile & Thao tác 1-chạm
 */

(function () {
  "use strict";

  const state = {
    video: null,          // { id, name, info }
    templateId: "footer_band",
    caption: "",
    logoId: null,
    timeSec: 1.0,
    config: null,
    currentJobId: null,
    pollTimer: null,
    previewDebounceTimer: null,
  };

  // DOM Elements
  const clipNameBadge = document.getElementById("clipNameBadge");
  const btnTriggerUpload = document.getElementById("btnTriggerUpload");
  const videoFileInput = document.getElementById("videoFileInput");
  const dropEmptyState = document.getElementById("dropEmptyState");
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
        renderAIProviders();
      }
    } catch (e) {
      console.warn("Chưa tải được config:", e);
    }

    // Nạp sẵn thông tin Telegram nếu đã lưu trước đó
    const savedToken = localStorage.getItem("taio_tele_token") || "";
    const savedChatId = localStorage.getItem("taio_tele_chatid") || "";
    if (savedToken) teleBotTokenInput.value = savedToken;
    if (savedChatId) teleChatIdInput.value = savedChatId;

    bindEvents();
    renderLiveHighlightPreview("");
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
    // 1. Tải Video
    btnTriggerUpload.addEventListener("click", () => videoFileInput.click());
    btnChangeVideo.addEventListener("click", () => videoFileInput.click());
    videoFileInput.addEventListener("change", (e) => {
      if (e.target.files && e.target.files[0]) uploadVideo(e.target.files[0]);
    });

    // 2. Mẫu lớp phủ A B C D
    templatePillsBar.querySelectorAll(".tpl-pill").forEach((btn) => {
      btn.addEventListener("click", () => {
        templatePillsBar.querySelectorAll(".tpl-pill").forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        state.templateId = btn.dataset.id;
        debouncedPreview();
      });
    });

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
      debouncedPreview();
    });

    // 6. Action Render
    btnRenderVideo.addEventListener("click", startRender);

    // 7. Save to Camera Roll (Web Share API)
    btnSaveToPhotos.addEventListener("click", saveVideoToPhotos);

    // 8. Telegram Modal
    btnSendTelegram.addEventListener("click", openTelegramModal);
    btnCloseTeleModal.addEventListener("click", () => (telegramModal.hidden = true));
    btnConfirmSendTelegram.addEventListener("click", sendVideoToTelegram);

    // 9. AI Modal
    btnOpenAIModal.addEventListener("click", () => (aiModal.hidden = false));
    btnCloseAIModal.addEventListener("click", () => (aiModal.hidden = true));
    btnGenerateAI.addEventListener("click", generateCaptionsAI);
  }

  // ==================== TẢI LÊN VIDEO ====================
  async function uploadVideo(file) {
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

    // Regex tìm **từ nhấn** hoặc *từ nhấn* hoặc <b>từ nhấn</b>
    const clean = escapeHtml(raw);
    const highlighted = clean.replace(
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

    previewLoadingOverlay.hidden = false;

    try {
      const payload = {
        video_id: state.video.id,
        template: state.templateId,
        caption: state.caption,
        t: state.timeSec,
        logo_id: state.logoId,
      };

      const res = await fetch("/api/preview", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.error || "Lỗi cập nhật ảnh xem trước");
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
      previewImage.src = URL.createObjectURL(blob);
      previewImage.hidden = false;
      playerResultVideo.hidden = true;
    } catch (err) {
      console.warn("Preview warning:", err.message);
    } finally {
      previewLoadingOverlay.hidden = true;
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

    btnRenderVideo.disabled = true;
    renderProgressCard.hidden = false;
    renderDoneActions.hidden = true;
    renderErrorMsg.hidden = true;
    renderStatusText.textContent = "Đang xử lý...";
    renderPctText.textContent = "0%";
    renderProgressBar.style.width = "0%";

    try {
      const payload = {
        video_id: state.video.id,
        video_name: state.video.name,
        template: state.templateId,
        caption: state.caption,
        logo_id: state.logoId,
      };

      const res = await fetch("/api/render", {
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

  function pollJobStatus() {
    clearInterval(state.pollTimer);

    state.pollTimer = setInterval(async () => {
      if (!state.currentJobId) {
        clearInterval(state.pollTimer);
        return;
      }

      try {
        const res = await fetch(`/api/job/${state.currentJobId}`);
        const job = await res.json();

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
        clearInterval(state.pollTimer);
        renderErrorMsg.textContent = err.message;
        renderErrorMsg.hidden = false;
        btnRenderVideo.disabled = false;
      }
    }, 700);
  }

  // ==================== LƯU VÀO CUỘN CAMERA (iOS / ANDROID) ====================
  async function saveVideoToPhotos() {
    if (!state.currentJobId) return;

    const downloadUrl = `/api/download/${state.currentJobId}`;
    const filename = state.video ? state.video.name : "TAIO.CoverClip.mp4";

    try {
      btnSaveToPhotos.textContent = "Đang tải tệp để lưu...";
      const resp = await fetch(downloadUrl);
      const blob = await resp.blob();
      const file = new File([blob], filename, { type: "video/mp4" });

      if (navigator.canShare && navigator.canShare({ files: [file] })) {
        await navigator.share({
          files: [file],
          title: filename,
        });
        btnSaveToPhotos.textContent = "📱 Đã mở bảng lưu!";
      } else {
        // Fallback: Mở video trong tab mới để chạm giữ "Lưu video"
        window.open(downloadUrl, "_blank");
        btnSaveToPhotos.textContent = "📱 Chạm giữ video để Lưu";
      }
    } catch (e) {
      if (e.name !== "AbortError") {
        window.open(downloadUrl, "_blank");
      }
    } finally {
      setTimeout(() => {
        btnSaveToPhotos.textContent = "📱 Lưu vào Cuộn Camera";
      }, 3000);
    }
  }

  // ==================== GỬI QUA TELEGRAM BOT ====================
  function openTelegramModal() {
    teleStatusMsg.hidden = true;
    telegramModal.hidden = false;
  }

  async function sendVideoToTelegram() {
    const token = teleBotTokenInput.value.trim();
    const chatId = teleChatIdInput.value.trim();

    if (!token || !chatId) {
      showTeleStatus("Vui lòng điền đủ Bot Token và Chat ID.", false);
      return;
    }

    // Lưu vào localStorage
    localStorage.setItem("taio_tele_token", token);
    localStorage.setItem("taio_tele_chatid", chatId);

    btnConfirmSendTelegram.disabled = true;
    btnConfirmSendTelegram.textContent = "Đang tải video sang Telegram...";
    teleStatusMsg.hidden = true;

    try {
      const payload = {
        job_id: state.currentJobId,
        bot_token: token,
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

      const res = await fetch("/api/suggest", {
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
