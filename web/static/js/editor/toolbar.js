/**
 * TAIO Cover Studio — Editor Toolbar & Layers Drawer
 * Thanh công cụ nổi phía trên đối tượng và danh sách lớp (Layers List).
 */

(function () {
  "use strict";

  let toolbarEl = null;
  let layersDrawerEl = null;
  let btnToggleLayersEl = null;

  function initToolbar() {
    toolbarEl = document.getElementById("editorFloatingToolbar");
    layersDrawerEl = document.getElementById("editorLayersDrawer");
    btnToggleLayersEl = document.getElementById("btnToggleLayers");

    if (btnToggleLayersEl) {
      btnToggleLayersEl.addEventListener("click", () => {
        toggleLayersDrawer();
      });
    }
  }

  function toggleLayersDrawer(show) {
    if (!layersDrawerEl) return;
    const isHidden = layersDrawerEl.hidden;
    const nextState = show !== undefined ? !show : !isHidden;
    layersDrawerEl.hidden = nextState;
    if (!nextState) {
      renderLayersList();
    }
  }

  function updateToolbar() {
    const store = window.TAIOSceneStore;
    if (!toolbarEl) return;
    if (!store || (!store.selectedId && !store.selectedChildId)) {
      toolbarEl.hidden = true;
      return;
    }
    // Sẽ được kích hoạt đầy đủ ở P2 / P5 / P6 / P7
  }

  function renderLayersList() {
    if (!layersDrawerEl) return;
    // Dựng danh sách các lớp cho drawer
  }

  window.TAIOEditorToolbar = {
    initToolbar,
    updateToolbar,
    toggleLayersDrawer,
    renderLayersList,
  };
})();
