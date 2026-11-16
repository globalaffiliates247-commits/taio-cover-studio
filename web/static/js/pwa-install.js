/**
 * TAIO Cover Studio — PWA Install & Platform Shortcut Guide
 * Tự động phát hiện hệ điều hành (Android, PC Windows, Mac, iOS) và hiển thị
 * popover / bottom sheet hướng dẫn tạo lối tắt / cài đặt PWA theo đúng thiết bị.
 */

(function () {
  "use strict";

  let deferredPrompt = null;
  let detectedPlatform = "android"; // 'android' | 'ios' | 'pc' | 'mac'

  // Phát hiện hệ điều hành và trình duyệt của người dùng
  function detectUserPlatform() {
    const ua = navigator.userAgent || navigator.vendor || window.opera || "";
    const platform = navigator.platform || "";

    // Kiểm tra iOS (iPhone, iPad, iPod)
    const isIOS = /iPad|iPhone|iPod/.test(ua) || (platform === "MacIntel" && navigator.maxTouchPoints > 1);
    if (isIOS) return "ios";

    // Kiểm tra Android
    if (/Android/i.test(ua)) return "android";

    // Kiểm tra macOS (không phải iPad)
    if (/Macintosh|MacIntel|MacPPC|Mac68K/i.test(ua) || /Mac OS X/i.test(ua)) return "mac";

    // Kiểm tra Windows / PC / Linux
    if (/Win32|Win64|Windows|WinCE/i.test(ua) || /Linux/i.test(platform)) return "pc";

    return "android";
  }

  function getPlatformDisplayName(plat) {
    switch (plat) {
      case "android": return "Android";
      case "ios": return "iPhone / iPad (iOS)";
      case "mac": return "Mac (macOS)";
      case "pc": return "PC (Windows / Máy tính)";
      default: return "Thiết bị của bạn";
    }
  }

  function initPwa() {
    detectedPlatform = detectUserPlatform();

    // 1. Lắng nghe sự kiện trước khi cài đặt của Chromium (Android, Windows, Chrome Mac)
    window.addEventListener("beforeinstallprompt", (e) => {
      e.preventDefault();
      deferredPrompt = e;
      const btnInstallNow = document.getElementById("pwaBtnInstallDirect");
      if (btnInstallNow) {
        btnInstallNow.hidden = false;
      }
      // Đổi nhãn nút trên header thành "Cài đặt ngay"
      const btnHeader = document.getElementById("btnPwaInstall");
      if (btnHeader) {
        btnHeader.classList.add("can-install-direct");
      }
    });

    // 2. Lắng nghe khi đã cài đặt thành công
    window.addEventListener("appinstalled", () => {
      deferredPrompt = null;
      console.log("TAIO Cover Studio PWA đã được cài đặt thành công.");
      const btnHeader = document.getElementById("btnPwaInstall");
      if (btnHeader) {
        btnHeader.classList.remove("can-install-direct");
        btnHeader.title = "Đã cài đặt ứng dụng";
      }
    });

    // 3. Đăng ký Service Worker nếu trình duyệt hỗ trợ
    if ("serviceWorker" in navigator) {
      window.addEventListener("load", () => {
        navigator.serviceWorker.register("/sw.js").catch((err) => {
          console.debug("ServiceWorker registration:", err);
        });
      });
    }

    // 4. Gắn sự kiện click mở popover
    const btnPwa = document.getElementById("btnPwaInstall");
    const modalPwa = document.getElementById("pwaModal");
    const btnClosePwa = document.getElementById("btnClosePwaModal");
    const pwaOverlay = document.getElementById("pwaModalOverlay");

    if (btnPwa) {
      btnPwa.addEventListener("click", () => {
        openPwaModal();
      });
    }

    if (btnClosePwa) {
      btnClosePwa.addEventListener("click", () => {
        closePwaModal();
      });
    }

    if (pwaOverlay) {
      pwaOverlay.addEventListener("click", (e) => {
        if (e.target === pwaOverlay) {
          closePwaModal();
        }
      });
    }

    // Sự kiện chuyển Tab hệ điều hành
    const tabButtons = document.querySelectorAll(".pwa-tab-btn");
    tabButtons.forEach((btn) => {
      btn.addEventListener("click", () => {
        const targetPlat = btn.dataset.plat;
        switchPwaTab(targetPlat);
      });
    });

    // Sự kiện nút Cài đặt ngay (1 chạm)
    const btnInstallDirect = document.getElementById("pwaBtnInstallDirect");
    if (btnInstallDirect) {
      btnInstallDirect.addEventListener("click", async () => {
        if (!deferredPrompt) {
          alert("Trình duyệt chưa sẵn sàng mở hộp thoại tự động. Vui lòng làm theo hướng dẫn các bước bên dưới!");
          return;
        }
        deferredPrompt.prompt();
        const { outcome } = await deferredPrompt.userChoice;
        console.log("PWA install choice:", outcome);
        if (outcome === "accepted") {
          deferredPrompt = null;
          closePwaModal();
        }
      });
    }

    // Nhấn ESC để đóng
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && modalPwa && !modalPwa.hidden) {
        closePwaModal();
      }
    });
  }

  function openPwaModal() {
    const modalPwa = document.getElementById("pwaModal");
    if (!modalPwa) return;

    // Cập nhật nhãn thiết bị đã phát hiện
    const detectedBadge = document.getElementById("pwaDetectedBadge");
    if (detectedBadge) {
      detectedBadge.textContent = `🎯 Đã phát hiện: ${getPlatformDisplayName(detectedPlatform)}`;
    }

    // Tự động kích hoạt tab khớp với thiết bị hiện tại
    switchPwaTab(detectedPlatform);

    // Kiểm tra xem nút Cài đặt ngay có dùng được không
    const btnInstallDirect = document.getElementById("pwaBtnInstallDirect");
    if (btnInstallDirect) {
      btnInstallDirect.hidden = !deferredPrompt;
    }

    modalPwa.hidden = false;
    document.body.style.overflow = "hidden";
  }

  function closePwaModal() {
    const modalPwa = document.getElementById("pwaModal");
    if (modalPwa) {
      modalPwa.hidden = true;
    }
    document.body.style.overflow = "";
  }

  function switchPwaTab(plat) {
    const tabButtons = document.querySelectorAll(".pwa-tab-btn");
    tabButtons.forEach((btn) => {
      const isTarget = btn.dataset.plat === plat;
      btn.classList.toggle("active", isTarget);
    });

    const contentPanels = document.querySelectorAll(".pwa-guide-panel");
    contentPanels.forEach((panel) => {
      panel.hidden = panel.id !== `pwaGuide_${plat}`;
    });
  }

  // Khởi tạo khi DOM sẵn sàng
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initPwa);
  } else {
    initPwa();
  }
})();
