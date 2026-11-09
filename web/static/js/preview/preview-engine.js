/**
 * TAIO Cover Studio — Preview Engine (FEATURE v1.5 P7)
 * Bộ nhớ đệm LRU Map tối đa 40 ảnh blob URL phía client và cơ chế tua mượt video tại chỗ.
 */

(function () {
  "use strict";

  const MAX_CACHE_SIZE = 40;
  const lruCache = new Map(); // key -> { blobUrl, timestamp }

  let scrubVideoEl = null;
  let previewImgEl = null;
  let scrubDebounceTimer = null;
  let localVideoUrl = null;

  function init(options) {
    options = options || {};
    previewImgEl = options.previewImg || document.getElementById("previewImage");

    // Tạo phần tử video ẩn phục vụ tua mượt tại chỗ nếu chưa có
    scrubVideoEl = document.getElementById("scrubLocalVideo");
    if (!scrubVideoEl) {
      scrubVideoEl = document.createElement("video");
      scrubVideoEl.id = "scrubLocalVideo";
      scrubVideoEl.className = "preview-screen";
      scrubVideoEl.muted = true;
      scrubVideoEl.playsInline = true;
      scrubVideoEl.hidden = true;
      const stage = document.querySelector(".preview-stage-container") || document.getElementById("previewWrapper");
      if (stage && previewImgEl) {
        stage.insertBefore(scrubVideoEl, previewImgEl);
      }
    }
  }

  function computeCacheKey(templateId, overrides, caption, timeSec) {
    // Overrides không gồm objects để di chuyển/kéo thả không làm mất cache
    const nonObjOverrides = { ...overrides };
    delete nonObjOverrides.objects;

    const roundedT = Math.round((parseFloat(timeSec) || 0) * 10) / 10;
    const rawKey = `${templateId || ""}|${caption || ""}|${roundedT}|${JSON.stringify(nonObjOverrides)}`;
    return rawKey;
  }

  function getCachedPreview(key) {
    if (!lruCache.has(key)) return null;

    const entry = lruCache.get(key);
    // Làm mới vị trí LRU
    lruCache.delete(key);
    lruCache.set(key, entry);
    return entry.blobUrl;
  }

  function setCachedPreview(key, blob) {
    if (!key || !blob) return null;

    // Giới hạn 40 ảnh
    if (lruCache.size >= MAX_CACHE_SIZE) {
      const oldestKey = lruCache.keys().next().value;
      if (oldestKey) {
        const oldEntry = lruCache.get(oldestKey);
        if (oldEntry && oldEntry.blobUrl) {
          try {
            URL.revokeObjectURL(oldEntry.blobUrl);
          } catch (_) {}
        }
        lruCache.delete(oldestKey);
      }
    }

    const blobUrl = URL.createObjectURL(blob);
    lruCache.set(key, { blobUrl, timestamp: Date.now() });
    return blobUrl;
  }

  function clearCache() {
    lruCache.forEach((entry) => {
      if (entry && entry.blobUrl) {
        try {
          URL.revokeObjectURL(entry.blobUrl);
        } catch (_) {}
      }
    });
    lruCache.clear();
  }

  function setupLocalVideoSource(videoFile, videoId) {
    if (localVideoUrl) {
      try {
        URL.revokeObjectURL(localVideoUrl);
      } catch (_) {}
      localVideoUrl = null;
    }

    if (!scrubVideoEl) return;

    if (videoFile instanceof File) {
      localVideoUrl = URL.createObjectURL(videoFile);
      scrubVideoEl.src = localVideoUrl;
      scrubVideoEl.load();
    } else if (videoId) {
      scrubVideoEl.src = `/api/video/${encodeURIComponent(videoId)}`;
      scrubVideoEl.load();
    }
  }

  function onScrubInput(timeSec, onFinalCommit) {
    // 1. Phản hồi mượt ngay tại chỗ: tua video local
    if (scrubVideoEl && scrubVideoEl.src && !isNaN(scrubVideoEl.duration)) {
      scrubVideoEl.currentTime = timeSec;
      scrubVideoEl.hidden = false;
      if (previewImgEl) {
        // Tạm mờ ảnh cũ để hiện frame video dưới
        previewImgEl.style.opacity = "0.7";
      }
    }

    // 2. Debounce 300ms sau khi dừng tua mới gọi lấy ảnh chính xác từ server hoặc cache
    if (scrubDebounceTimer) {
      clearTimeout(scrubDebounceTimer);
    }

    scrubDebounceTimer = setTimeout(() => {
      if (scrubVideoEl) {
        scrubVideoEl.hidden = true;
      }
      if (previewImgEl) {
        previewImgEl.style.opacity = "1";
      }
      if (typeof onFinalCommit === "function") {
        onFinalCommit(timeSec);
      }
    }, 300);
  }

  window.TAIOPreviewEngine = {
    init,
    computeCacheKey,
    getCachedPreview,
    setCachedPreview,
    clearCache,
    setupLocalVideoSource,
    onScrubInput,
  };
})();
