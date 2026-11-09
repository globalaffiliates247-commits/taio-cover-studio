/**
 * TAIO Cover Studio — Horizontal Tabs (FEATURE v1.5 P6)
 * Hàng tab có icon 2D nét 22px kiểu CapCut cuộn ngang, mở ngăn nội dung ~166px.
 */

(function () {
  "use strict";

  const TAB_DEFS = [
    { id: "template", label: "Mẫu", icon: "template", panelId: "tabPanelTemplate" },
    { id: "background", label: "Nền", icon: "background", panelId: "tabPanelBackground" },
    { id: "caption", label: "Cap", icon: "caption", panelId: "tabPanelCaption" },
    { id: "logo", label: "Logo", icon: "logo", panelId: "tabPanelLogo" },
    { id: "add_text", label: "+ Chữ", icon: "add_text", panelId: "tabPanelAddText" },
    { id: "ai", label: "AI", icon: "ai", panelId: "tabPanelAI" },
    { id: "layers", label: "Lớp", icon: "layers", panelId: "tabPanelLayers" },
  ];

  const state = {
    activeTab: "template",
    isCollapsed: false,
    tabsBarEl: null,
    panelContentEl: null,
  };

  function init(options) {
    options = options || {};
    state.tabsBarEl = options.tabsBarEl || document.getElementById("capcutTabsBar");
    state.panelContentEl = options.panelContentEl || document.getElementById("capcutPanelContent");

    if (!state.tabsBarEl) return;

    renderTabs();
    openTab(state.activeTab);

    // Lắng nghe khi người dùng chọn đối tượng trên canvas để tự mở tab tương ứng
    if (window.TAIOSceneStore) {
      window.TAIOSceneStore.subscribe((obj, meta) => {
        if (meta && meta.type === "selection_changed") {
          const selId = window.TAIOSceneStore.selectedId;
          if (selId === "logo") {
            openTab("logo", true);
          } else if (selId && selId.startsWith("text_")) {
            openTab("add_text", true);
          }
        }
      });
    }
  }

  function renderTabs() {
    if (!state.tabsBarEl) return;
    const icons = window.TAIOIcons || { get: () => "" };
    state.tabsBarEl.innerHTML = "";

    TAB_DEFS.forEach((tab) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = `capcut-tab-btn ${state.activeTab === tab.id ? "active" : ""}`;
      btn.dataset.tab = tab.id;

      const iconWrap = document.createElement("div");
      iconWrap.className = "tab-btn-icon";
      iconWrap.innerHTML = icons.get(tab.icon, 22);

      const labelWrap = document.createElement("span");
      labelWrap.className = "tab-btn-label";
      labelWrap.textContent = tab.label;

      btn.appendChild(iconWrap);
      btn.appendChild(labelWrap);

      btn.addEventListener("click", () => {
        if (state.activeTab === tab.id) {
          // Bấm tab đang mở lần nữa -> thu bảng lại để preview to hơn
          toggleCollapse();
        } else {
          openTab(tab.id);
        }
      });

      state.tabsBarEl.appendChild(btn);
    });
  }

  function openTab(tabId, expandOnly) {
    state.activeTab = tabId;
    if (expandOnly || state.isCollapsed) {
      state.isCollapsed = false;
    }

    if (state.tabsBarEl) {
      state.tabsBarEl.querySelectorAll(".capcut-tab-btn").forEach((btn) => {
        const isActive = btn.dataset.tab === tabId && !state.isCollapsed;
        btn.classList.toggle("active", isActive);
      });
    }

    if (state.panelContentEl) {
      state.panelContentEl.hidden = state.isCollapsed;
      state.panelContentEl.querySelectorAll(".capcut-tab-panel").forEach((panel) => {
        const isTarget = panel.dataset.tab === tabId;
        panel.hidden = !isTarget;
      });
    }

    // Cuộn tab vào vùng nhìn thấy nếu cần
    const activeBtn = state.tabsBarEl ? state.tabsBarEl.querySelector(`[data-tab="${tabId}"]`) : null;
    if (activeBtn && activeBtn.scrollIntoView) {
      activeBtn.scrollIntoView({ behavior: "smooth", inline: "nearest", block: "nearest" });
    }
  }

  function toggleCollapse() {
    state.isCollapsed = !state.isCollapsed;
    if (state.panelContentEl) {
      state.panelContentEl.hidden = state.isCollapsed;
    }
    if (state.tabsBarEl) {
      state.tabsBarEl.querySelectorAll(".capcut-tab-btn").forEach((btn) => {
        if (state.isCollapsed) {
          btn.classList.remove("active");
        } else if (btn.dataset.tab === state.activeTab) {
          btn.classList.add("active");
        }
      });
    }
  }

  window.TAIOTabs = {
    init,
    openTab,
    toggleCollapse,
  };
})();
