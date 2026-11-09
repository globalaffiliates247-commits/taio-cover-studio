/**
 * TAIO Cover Studio — Result Actions (FEATURE v1.5 P3)
 * Tải video một lần duy nhất với thanh tiến độ stream, gán blob cho player phát thử,
 * và tích hợp nút "📤 Lưu / Chia sẻ" (iOS Share Sheet).
 */

(function () {
  "use strict";

  const state = {
    jobId: null,
    filename: "TAIO.CoverClip.mp4",
    blob: null,
    blobUrl: null,
    file: null,
    isDownloading: false,
  };

  let btnSaveShareEl = null;
  let btnDownloadMp4El = null;
  let statusTextEl = null;
  let progressBarEl = null;
  let pctTextEl = null;
  let playerVideoEl = null;

  function isIOS() {
    return (
      /iPad|iPhone|iPod/.test(navigator.userAgent) ||
      (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1)
    );
  }

  function init(options) {
    options = options || {};
    btnSaveShareEl = options.btnSaveShare || document.getElementById("btnSaveToPhotos");
    btnDownloadMp4El = options.btnDownloadMp4 || document.getElementById("btnDownloadVideo");
    statusTextEl = options.statusText || document.getElementById("renderStatusText");
    progressBarEl = options.progressBar || document.getElementById("renderProgressBar");
    pctTextEl = options.pctText || document.getElementById("renderPctText");
    playerVideoEl = options.playerVideo || document.getElementById("playerResultVideo");

    if (btnSaveShareEl) {
      btnSaveShareEl.textContent = "📤 Lưu / Chia sẻ";
      btnSaveShareEl.addEventListener("click", handleSaveShareClick);
    }

    if (btnDownloadMp4El) {
      btnDownloadMp4El.addEventListener("click", handleDownloadMp4Click);
    }
  }

  /**
   * Tải file video một lần duy nhất với stream progress, không tải lần hai
   */
  async function downloadResultOnce(jobId, filename, onComplete) {
    if (!jobId) return;

    cleanup();
    state.jobId = jobId;
    state.filename = filename || "TAIO.CoverClip.mp4";
    state.isDownloading = true;

    if (btnSaveShareEl) {
      btnSaveShareEl.disabled = true;
      btnSaveShareEl.textContent = "⏳ Đang tải về điện thoại…";
    }
    if (statusTextEl) {
      statusTextEl.textContent = "Đang tải về điện thoại…";
    }

    const downloadUrl = `/api/download/${jobId}`;

    try {
      const resp = await fetch(downloadUrl);
      if (!resp.ok) {
        throw new Error(`Mã phản hồi HTTP ${resp.status}`);
      }

      const contentLength = resp.headers.get("content-length");
      const totalBytes = contentLength ? parseInt(contentLength, 10) : 0;

      let blob;
      if (resp.body && totalBytes > 0 && typeof ReadableStream !== "undefined") {
        const reader = resp.body.getReader();
        const chunks = [];
        let receivedBytes = 0;

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          chunks.push(value);
          receivedBytes += value.length;

          const pct = Math.round((receivedBytes / totalBytes) * 100);
          if (progressBarEl) progressBarEl.style.width = `${pct}%`;
          if (pctTextEl) pctTextEl.textContent = `${pct}%`;
          if (statusTextEl) {
            statusTextEl.textContent = `Đang tải về điện thoại… ${pct}%`;
          }
        }
        blob = new Blob(chunks, { type: "video/mp4" });
      } else {
        blob = await resp.blob();
      }

      if (!blob || blob.size < 100) {
        throw new Error("Tệp video rỗng hoặc không hoàn chỉnh.");
      }

      state.blob = blob;
      state.blobUrl = URL.createObjectURL(blob);
      state.file = new File([blob], state.filename, { type: "video/mp4" });
      state.isDownloading = false;

      // Gán trực tiếp blob URL cho player phát thử (KHÔNG gọi tải từ server lần 2)
      if (playerVideoEl) {
        playerVideoEl.src = state.blobUrl;
        playerVideoEl.hidden = false;
        const previewImage = document.getElementById("previewImage");
        if (previewImage) previewImage.hidden = true;
        const stickerStage = document.getElementById("stickerStage");
        if (stickerStage) stickerStage.hidden = true;
      }

      // Cập nhật TAIOSavePhotos nếu có
      if (window.TAIOSavePhotos && window.TAIOSavePhotos.setPreparedFile) {
        window.TAIOSavePhotos.setPreparedFile(state.file, state.blobUrl, state.filename);
      }

      if (btnSaveShareEl) {
        btnSaveShareEl.disabled = false;
        btnSaveShareEl.textContent = "📤 Lưu / Chia sẻ";
      }
      if (btnDownloadMp4El) {
        btnDownloadMp4El.href = state.blobUrl;
        btnDownloadMp4El.download = state.filename;
      }
      if (statusTextEl) {
        statusTextEl.textContent = " Video đã sẵn sàng!";
      }

      console.info(
        "[result-actions] Đã tải video vào bộ nhớ:",
        state.filename,
        `(${(blob.size / (1024 * 1024)).toFixed(2)} MB)`
      );

      if (typeof onComplete === "function") {
        onComplete(state.file, state.blobUrl);
      }
    } catch (err) {
      state.isDownloading = false;
      console.warn("[result-actions] Lỗi tải video:", err);
      if (statusTextEl) {
        statusTextEl.textContent = `Lỗi tải video: ${err.message}`;
      }
      if (btnSaveShareEl) {
        btnSaveShareEl.disabled = false;
        btnSaveShareEl.textContent = "📤 Lưu / Chia sẻ";
      }
    }
  }

  function handleSaveShareClick() {
    if (state.isDownloading || !state.file) {
      if (btnSaveShareEl) {
        btnSaveShareEl.textContent = "⏳ Video đang được tải về, vui lòng chờ…";
        setTimeout(() => {
          if (btnSaveShareEl) btnSaveShareEl.textContent = "📤 Lưu / Chia sẻ";
        }, 2000);
      }
      return;
    }

    const shareData = {
      files: [state.file],
      title: state.filename,
    };

    if (navigator.share && navigator.canShare && navigator.canShare(shareData)) {
      navigator
        .share(shareData)
        .then(() => {
          console.info("[result-actions] Mở share sheet thành công!");
        })
        .catch((e) => {
          if (e.name !== "AbortError") {
            console.warn("[result-actions] Share error:", e);
            fallbackDownload();
          }
        });
    } else {
      fallbackDownload();
    }
  }

  function handleDownloadMp4Click(e) {
    if (isIOS()) {
      alert("Mẹo trên iPhone: Muốn lưu trực tiếp vào ứng dụng Ảnh hoặc chọn thư mục iCloud, hãy bấm nút '📤 Lưu / Chia sẻ'.");
    }
    if (state.blobUrl) {
      const a = document.createElement("a");
      a.href = state.blobUrl;
      a.download = state.filename;
      a.style.display = "none";
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      e.preventDefault();
    }
  }

  function fallbackDownload() {
    if (state.blobUrl) {
      const a = document.createElement("a");
      a.href = state.blobUrl;
      a.download = state.filename;
      a.style.display = "none";
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    }
  }

  function cleanup() {
    if (state.blobUrl) {
      URL.revokeObjectURL(state.blobUrl);
      state.blobUrl = null;
    }
    state.blob = null;
    state.file = null;
    state.isDownloading = false;
    state.jobId = null;
  }

  window.addEventListener("beforeunload", cleanup);

  window.TAIOResultActions = {
    init,
    downloadResultOnce,
    cleanup,
    getState: () => ({ ...state }),
  };
})();
