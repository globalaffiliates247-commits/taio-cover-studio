/**
 * web/static/js/save-photos.js
 * Quản lý tính năng "Lưu vào Cuộn Camera" trên iOS/Android (Web Share API) (FIX v1.3.1).
 * Tách độc lập khỏi app.js, tải sẵn video vào bộ nhớ ngay khi render xong để đảm bảo
 * transient user activation của WebKit trên iOS.
 */

(function () {
  "use strict";

  const state = {
    resultFile: null,
    blobUrl: null,
    isPreparing: false,
    currentJobId: null,
    filename: "TAIO.CoverClip.mp4",
  };

  let btnSaveEl = null;
  let statusEl = null;
  let onRetryRenderCallback = null;

  function init(options) {
    options = options || {};
    btnSaveEl = options.btnSave || document.getElementById("btnSaveToPhotos");
    statusEl = options.statusEl || document.getElementById("renderErrorMsg");
    onRetryRenderCallback = options.onRetryRender || null;

    if (btnSaveEl) {
      btnSaveEl.addEventListener("click", handleSaveClick);
    }

    window.addEventListener("beforeunload", cleanup);
  }

  /**
   * Tải sẵn video ngay khi xuất xong về bộ nhớ trình duyệt (FIX-1)
   */
  async function prepareResultFile(jobId, filename) {
    if (!jobId) return;

    cleanup();
    state.currentJobId = jobId;
    state.filename = filename || "TAIO.CoverClip.mp4";
    state.isPreparing = true;

    if (btnSaveEl) {
      btnSaveEl.disabled = true;
      btnSaveEl.textContent = "⏳ Đang chuẩn bị video…";
    }

    const downloadUrl = `/api/download/${jobId}`;

    try {
      const resp = await fetch(downloadUrl);
      if (!resp.ok) {
        throw new Error(`Mã phản hồi HTTP ${resp.status}`);
      }

      const contentType = resp.headers.get("content-type") || "";
      if (contentType.includes("application/json")) {
        const errData = await resp.json().catch(() => ({}));
        throw new Error(errData.error || "Tệp video không tồn tại trên máy chủ.");
      }

      const blob = await resp.blob();
      if (!blob || blob.size < 100) {
        throw new Error("Tệp video rỗng hoặc không hoàn chỉnh.");
      }

      state.blobUrl = URL.createObjectURL(blob);
      state.resultFile = new File([blob], state.filename, { type: "video/mp4" });
      state.isPreparing = false;

      if (btnSaveEl) {
        btnSaveEl.disabled = false;
        btnSaveEl.textContent = "📱 Lưu vào Cuộn Camera";
      }

      console.info(
        "[save-photos] Đã tải sẵn video vào RAM:",
        state.filename,
        `(${(blob.size / (1024 * 1024)).toFixed(2)} MB)`
      );
    } catch (err) {
      state.isPreparing = false;
      state.resultFile = null;
      console.warn("[save-photos] Lỗi tải sẵn video:", err);

      if (btnSaveEl) {
        btnSaveEl.disabled = false;
        btnSaveEl.textContent = "📱 Lưu vào Cuộn Camera";
      }

      if (statusEl && typeof onRetryRenderCallback === "function") {
        statusEl.innerHTML = `${escapeHtml(err.message)} <button type="button" id="btnRetrySavePhotos" style="margin-left:8px;padding:3px 10px;border-radius:6px;background:#3B82F6;color:#fff;border:none;cursor:pointer;font-weight:600">Xuất lại</button>`;
        statusEl.hidden = false;
        const retryBtn = document.getElementById("btnRetrySavePhotos");
        if (retryBtn) {
          retryBtn.onclick = () => {
            statusEl.hidden = true;
            onRetryRenderCallback();
          };
        }
      }
    }
  }

  /**
   * Handler xử lý cú chạm nút Lưu vào Cuộn Camera (FIX-2)
   * Phải kích hoạt navigator.share NGAY LẬP TỨC trong synchronous user activation call stack,
   * tuyệt đối không được có bất kỳ lệnh await nào (fetch, blob, setTimeout...) trước share.
   */
  function handleSaveClick() {
    // 1. Nếu file chưa sẵn sàng (người dùng bấm quá sớm): KHÔNG chờ đợi rồi mới share
    if (state.isPreparing || !state.resultFile) {
      if (btnSaveEl) {
        const originalText = btnSaveEl.textContent;
        btnSaveEl.textContent = "⏳ Video đang được chuẩn bị, bấm lại sau giây lát";
        setTimeout(() => {
          if (btnSaveEl) {
            btnSaveEl.textContent = state.resultFile ? "📱 Lưu vào Cuộn Camera" : originalText;
          }
        }, 2500);
      }
      return;
    }

    // 2. Kiểm tra đồng bộ canShare trước, không có await
    const shareData = {
      files: [state.resultFile],
      title: state.filename,
    };

    if (navigator.share && navigator.canShare && navigator.canShare(shareData)) {
      // Kích hoạt ngay lập tức trong cú chạm
      navigator
        .share(shareData)
        .then(() => {
          console.info("[save-photos] Chia sẻ thành công!");
          if (btnSaveEl) {
            btnSaveEl.textContent = "📱 Đã mở bảng lưu!";
            setTimeout(() => {
              if (btnSaveEl) btnSaveEl.textContent = "📱 Lưu vào Cuộn Camera";
            }, 3000);
          }
        })
        .catch((e) => {
          console.info("[save-photos]", e.name, e.message);
        });
    }
  }

  /**
   * Giải phóng bộ nhớ
   */
  function cleanup() {
    if (state.blobUrl) {
      URL.revokeObjectURL(state.blobUrl);
      state.blobUrl = null;
    }
    state.resultFile = null;
    state.isPreparing = false;
    state.currentJobId = null;
  }

  function escapeHtml(str) {
    if (!str) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  window.TAIOSavePhotos = {
    init: init,
    prepareResultFile: prepareResultFile,
    cleanup: cleanup,
    reset: cleanup,
    getResultFile: () => state.resultFile,
  };
})();
