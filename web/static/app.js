/**
 * TAIO Cover Studio - Trình điều khiển giao diện Frontend (Vanilla JavaScript)
 * Tuân thủ Hick's Law: Mỗi bước 1 quyết định, tối giản, mượt mà.
 */

(function () {
  "use strict";

  // Trạng thái ứng dụng (Application State)
  const state = {
    video: null,          // { id, name, info }
    templateId: "footer_band",
    caption: "",
    logoId: null,         // null = Dùng logo mặc định của brand
    timeSec: 1.0,
    config: null,         // { templates, ai, brand }
    currentJobId: null,
    pollTimer: null,
    previewDebounceTimer: null,
  };

  // DOM Elements
  const headerBrandName = document.getElementById("headerBrandName");
  const headerBrandLogo = document.getElementById("headerBrandLogo");
  const headerBrandTagline = document.getElementById("headerBrandTagline");

  // Step 1: Video
  const videoDropzone = document.getElementById("videoDropzone");
  const videoFileInput = document.getElementById("videoFileInput");
  const videoInfoBanner = document.getElementById("videoInfoBanner");
  const videoFilename = document.getElementById("videoFilename");
  const videoMetaBadge = document.getElementById("videoMetaBadge");
  const btnRemoveVideo = document.getElementById("btnRemoveVideo");
  const uploadErrorMsg = document.getElementById("uploadErrorMsg");

  // Step 2: Templates
  const templateGrid = document.getElementById("templateGrid");

  // Step 3: Caption & AI
  const captionInput = document.getElementById("captionInput");
  const aiAccordion = document.getElementById("aiAccordion");
  const aiProviderSelect = document.getElementById("aiProviderSelect");
  const aiStyleSelect = document.getElementById("aiStyleSelect");
  const aiContextInput = document.getElementById("aiContextInput");
  const btnGenerateAI = document.getElementById("btnGenerateAI");
  const aiErrorMsg = document.getElementById("aiErrorMsg");
  const aiResultsList = document.getElementById("aiResultsList");
  const aiSummaryNote = document.getElementById("aiSummaryNote");
  const aiCardsContainer = document.getElementById("aiCardsContainer");

  // Step 4: Logo
  const logoThumbnailImg = document.getElementById("logoThumbnailImg");
  const logoStatusLabel = document.getElementById("logoStatusLabel");
  const logoFileInput = document.getElementById("logoFileInput");
  const btnUploadCustomLogo = document.getElementById("btnUploadCustomLogo");
  const btnResetDefaultLogo = document.getElementById("btnResetDefaultLogo");

  // Step 5: Render
  const btnRenderVideo = document.getElementById("btnRenderVideo");
  const renderProgressCard = document.getElementById("renderProgressCard");
  const renderStatusText = document.getElementById("renderStatusText");
  const renderPctText = document.getElementById("renderPctText");
  const renderProgressBar = document.getElementById("renderProgressBar");
  const renderDoneActions = document.getElementById("renderDoneActions");
  const btnDownloadVideo = document.getElementById("btnDownloadVideo");
  const renderErrorMsg = document.getElementById("renderErrorMsg");

  // Right column: Preview
  const previewCanvasBox = document.getElementById("previewCanvasBox");
  const previewEmptyState = document.getElementById("previewEmptyState");
  const previewImage = document.getElementById("previewImage");
  const previewLoadingOverlay = document.getElementById("previewLoadingOverlay");
  const previewTimeline = document.getElementById("previewTimeline");
  const timelineSlider = document.getElementById("timelineSlider");
  const timelineTimeLabel = document.getElementById("timelineTimeLabel");
  const timelineDurationLabel = document.getElementById("timelineDurationLabel");
  const warningBanner = document.getElementById("warningBanner");
  const warningText = document.getElementById("warningText");

  // ==================== KHỞI TẠO ====================
  async function init() {
    try {
      const res = await fetch("/api/config");
      if (!res.ok) throw new Error("Không thể nạp cấu hình hệ thống");
      state.config = await res.json();
      renderBrandInfo();
      renderTemplates();
      renderAIProviders();
    } catch (err) {
      console.error("Lỗi khởi tạo:", err);
    }

    bindEvents();
  }

  function renderBrandInfo() {
    if (!state.config || !state.config.brand) return;
    const b = state.config.brand;
    if (b.name) headerBrandName.textContent = b.name;
    if (b.tagline) headerBrandTagline.textContent = b.tagline;
  }

  function renderTemplates() {
    if (!state.config || !state.config.templates) return;
    templateGrid.innerHTML = "";
    state.config.templates.forEach((tpl) => {
      const card = document.createElement("div");
      card.className = "template-card" + (tpl.id === state.templateId ? " active" : "");
      card.dataset.id = tpl.id;
      card.innerHTML = `
        <div class="template-card-title">${escapeHtml(tpl.name || tpl.id)}</div>
        <div class="template-card-desc">${escapeHtml(tpl.description || "")}</div>
      `;
      card.addEventListener("click", () => {
        document.querySelectorAll(".template-card").forEach((c) => c.classList.remove("active"));
        card.classList.add("active");
        state.templateId = tpl.id;
        debouncedPreview();
      });
      templateGrid.appendChild(card);
    });
  }

  function renderAIProviders() {
    if (!state.config || !state.config.ai) return;
    aiProviderSelect.innerHTML = "";
    const providers = state.config.ai.providers || [];
    const defaultId = state.config.ai.default;

    providers.forEach((p) => {
      const opt = document.createElement("option");
      opt.value = p.id;
      opt.textContent = `${p.label} (${p.model || ""}) ${p.ready ? "✓ Sẵn sàng" : "⚠️ Chưa cấu hình Key"}`;
      if (p.id === defaultId) opt.selected = true;
      aiProviderSelect.appendChild(opt);
    });
  }

  // ==================== SỰ KIỆN GIAO DIỆN ====================
  function bindEvents() {
    // Dropzone
    videoDropzone.addEventListener("click", () => videoFileInput.click());
    videoFileInput.addEventListener("change", (e) => {
      if (e.target.files && e.target.files[0]) uploadVideo(e.target.files[0]);
    });

    videoDropzone.addEventListener("dragover", (e) => {
      e.preventDefault();
      videoDropzone.classList.add("dragover");
    });
    videoDropzone.addEventListener("dragleave", () => videoDropzone.classList.remove("dragover"));
    videoDropzone.addEventListener("drop", (e) => {
      e.preventDefault();
      videoDropzone.classList.remove("dragover");
      if (e.dataTransfer.files && e.dataTransfer.files[0]) {
        uploadVideo(e.dataTransfer.files[0]);
      }
    });

    btnRemoveVideo.addEventListener("click", resetVideo);

    // Caption Input
    captionInput.addEventListener("input", (e) => {
      state.caption = e.target.value;
      debouncedPreview();
    });

    // Timeline Slider
    timelineSlider.addEventListener("input", (e) => {
      state.timeSec = parseFloat(e.target.value);
      formatTimelineLabels();
      debouncedPreview();
    });

    // Logo Buttons
    btnUploadCustomLogo.addEventListener("click", () => logoFileInput.click());
    logoFileInput.addEventListener("change", (e) => {
      if (e.target.files && e.target.files[0]) uploadLogo(e.target.files[0]);
    });

    btnResetDefaultLogo.addEventListener("click", () => {
      state.logoId = null;
      logoThumbnailImg.src = "/static/brand-logo";
      logoStatusLabel.textContent = "Logo mặc định của TAIO";
      btnResetDefaultLogo.hidden = true;
      debouncedPreview();
    });

    // AI Suggestions
    btnGenerateAI.addEventListener("click", generateCaptionsAI);

    // Render Video
    btnRenderVideo.addEventListener("click", startRender);
  }

  // ==================== XỬ LÝ UPLOAD ====================
  async function uploadVideo(file) {
    uploadErrorMsg.hidden = true;
    uploadErrorMsg.textContent = "";

    const formData = new FormData();
    formData.append("file", file);
    formData.append("kind", "video");

    videoDropzone.style.opacity = "0.5";
    videoDropzone.style.pointerEvents = "none";

    try {
      const res = await fetch("/api/upload", { method: "POST", body: formData });
      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.error || "Lỗi khi tải video lên");
      }

      state.video = data;
      videoFilename.textContent = data.name;
      if (data.info) {
        videoMetaBadge.textContent = data.info.summary || "";
        timelineSlider.max = Math.max(data.info.duration || 10, 1);
        timelineDurationLabel.textContent = `/ ${data.info.formatted_duration || "0:00"}`;
      }

      videoDropzone.hidden = true;
      videoInfoBanner.hidden = false;
      previewTimeline.hidden = false;
      btnRenderVideo.disabled = false;

      formatTimelineLabels();
      triggerPreview();
    } catch (err) {
      uploadErrorMsg.textContent = err.message;
      uploadErrorMsg.hidden = false;
    } finally {
      videoDropzone.style.opacity = "1";
      videoDropzone.style.pointerEvents = "auto";
    }
  }

  function resetVideo() {
    state.video = null;
    videoFileInput.value = "";
    videoDropzone.hidden = false;
    videoInfoBanner.hidden = true;
    previewTimeline.hidden = true;
    btnRenderVideo.disabled = true;

    previewImage.hidden = true;
    previewEmptyState.hidden = false;
    warningBanner.hidden = true;
  }

  async function uploadLogo(file) {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("kind", "logo");

    try {
      const res = await fetch("/api/upload", { method: "POST", body: formData });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Lỗi khi tải logo");

      state.logoId = data.id;
      logoThumbnailImg.src = URL.createObjectURL(file);
      logoStatusLabel.textContent = `Logo riêng: ${data.name}`;
      btnResetDefaultLogo.hidden = false;

      debouncedPreview();
    } catch (err) {
      alert("Lỗi tải logo: " + err.message);
    }
  }

  // ==================== XEM TRƯỚC (PREVIEW) ====================
  function debouncedPreview() {
    clearTimeout(state.previewDebounceTimer);
    state.previewDebounceTimer = setTimeout(triggerPreview, 350);
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
        const errJson = await res.json();
        throw new Error(errJson.error || "Lỗi kết xuất xem trước");
      }

      // Đọc header X-Warnings (hex-encoded UTF-8)
      const hexWarnings = res.headers.get("X-Warnings");
      if (hexWarnings) {
        try {
          const bytes = new Uint8Array(hexWarnings.match(/.{1,2}/g).map((byte) => parseInt(byte, 16)));
          const decodedWarn = new TextDecoder("utf-8").decode(bytes);
          if (decodedWarn.trim()) {
            warningText.textContent = decodedWarn;
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
      previewEmptyState.hidden = true;
    } catch (err) {
      console.error("Preview error:", err);
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

  // ==================== GỢI Ý CAPTION BẰNG AI ====================
  async function generateCaptionsAI() {
    if (!state.video) {
      alert("Vui lòng tải video lên trước khi yêu cầu AI gợi ý caption.");
      return;
    }

    aiErrorMsg.hidden = true;
    aiErrorMsg.textContent = "";

    const btnText = btnGenerateAI.querySelector(".btn-text");
    const btnSpinner = btnGenerateAI.querySelector(".btn-spinner");
    btnGenerateAI.disabled = true;
    if (btnSpinner) btnSpinner.hidden = false;
    btnText.textContent = "Đang phân tích khung hình & tạo gợi ý...";

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
      if (!res.ok) {
        throw new Error(data.error || "Lỗi khi gợi ý caption bằng AI");
      }

      renderAICaptionResults(data);
    } catch (err) {
      aiErrorMsg.textContent = err.message;
      aiErrorMsg.hidden = false;
    } finally {
      btnGenerateAI.disabled = false;
      if (btnSpinner) btnSpinner.hidden = true;
      btnText.textContent = "✨ Gợi ý 5 caption thu hút";
    }
  }

  function renderAICaptionResults(data) {
    aiSummaryNote.textContent = data.summary ? `Tóm tắt video: "${data.summary}"` : "";
    aiCardsContainer.innerHTML = "";

    const captions = data.captions || [];
    captions.forEach((item) => {
      const card = document.createElement("div");
      card.className = "ai-caption-card";
      card.innerHTML = `
        <div class="ai-card-text">${escapeHtml(item.text)}</div>
        <div class="ai-card-meta">
          <span class="ai-angle-badge">${escapeHtml(item.angle || "curiosity")}</span>
          <span>${escapeHtml(item.why || "")}</span>
        </div>
      `;
      card.addEventListener("click", () => {
        captionInput.value = item.text;
        state.caption = item.text;
        debouncedPreview();
      });
      aiCardsContainer.appendChild(card);
    });

    aiResultsList.hidden = false;
  }

  // ==================== XUẤT VIDEO (RENDER & JOBS) ====================
  async function startRender() {
    if (!state.video) return;

    btnRenderVideo.disabled = true;
    renderProgressCard.hidden = false;
    renderDoneActions.hidden = true;
    renderErrorMsg.hidden = true;
    renderStatusText.textContent = "Đang xếp hàng xuất video...";
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
      if (!res.ok) throw new Error(data.error || "Không thể khởi tạo lệnh xuất video");

      state.currentJobId = data.job_id;
      pollJobStatus();
    } catch (err) {
      renderErrorMsg.textContent = err.message;
      renderErrorMsg.hidden = false;
      btnRenderVideo.disabled = false;
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
        if (!res.ok) throw new Error("Không thể kiểm tra tiến độ");
        const job = await res.json();

        if (job.status === "queued") {
          renderStatusText.textContent = "Đang đợi trong hàng đợi...";
          renderProgressBar.style.width = "5%";
          renderPctText.textContent = "Chờ...";
        } else if (job.status === "running") {
          const pct = Math.round((job.progress || 0) * 100);
          renderStatusText.textContent = "Đang xuất video...";
          renderPctText.textContent = `${pct}%`;
          renderProgressBar.style.width = `${pct}%`;
        } else if (job.status === "done") {
          clearInterval(state.pollTimer);
          renderStatusText.textContent = " Xuất video thành công!";
          renderPctText.textContent = "100%";
          renderProgressBar.style.width = "100%";

          btnDownloadVideo.href = `/api/download/${state.currentJobId}`;
          renderDoneActions.hidden = false;
          btnRenderVideo.disabled = false;
        } else if (job.status === "error") {
          clearInterval(state.pollTimer);
          renderErrorMsg.textContent = job.error || "Lỗi khi xuất video";
          renderErrorMsg.hidden = false;
          renderStatusText.textContent = "Thất bại";
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

  function escapeHtml(str) {
    if (!str) return "";
    return str
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  // Khởi chạy khi DOM sẵn sàng
  document.addEventListener("DOMContentLoaded", init);
})();
