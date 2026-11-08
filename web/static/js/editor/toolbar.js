/**
 * TAIO Cover Studio — Editor Toolbar & Layers Drawer
 * Thanh công cụ nổi phía trên đối tượng và danh sách lớp (Layers List).
 */

(function () {
  "use strict";

  let toolbarEl = null;
  let innerEl = null;
  let layersDrawerEl = null;
  let layersListEl = null;
  let btnToggleLayersEl = null;
  let btnCloseLayersEl = null;
  let btnUndoEl = null;
  let btnRedoEl = null;

  function initToolbar() {
    toolbarEl = document.getElementById("editorFloatingToolbar");
    innerEl = document.getElementById("floatingToolbarInner");
    layersDrawerEl = document.getElementById("editorLayersDrawer");
    layersListEl = document.getElementById("editorLayersList");
    btnToggleLayersEl = document.getElementById("btnToggleLayers");
    btnCloseLayersEl = document.getElementById("btnCloseLayersDrawer");
    btnUndoEl = document.getElementById("btnEditorUndo");
    btnRedoEl = document.getElementById("btnEditorRedo");

    if (btnToggleLayersEl) {
      btnToggleLayersEl.addEventListener("click", () => {
        toggleLayersDrawer();
      });
    }

    if (btnCloseLayersEl) {
      btnCloseLayersEl.addEventListener("click", () => {
        toggleLayersDrawer(false);
      });
    }

    if (btnUndoEl) {
      btnUndoEl.addEventListener("click", () => {
        if (window.TAIOSceneStore) window.TAIOSceneStore.undo();
      });
    }

    if (btnRedoEl) {
      btnRedoEl.addEventListener("click", () => {
        if (window.TAIOSceneStore) window.TAIOSceneStore.redo();
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
    const transform = window.TAIOEditorTransform;
    if (!toolbarEl || !innerEl || !store) return;

    if (layersDrawerEl && !layersDrawerEl.hidden) {
      renderLayersList();
    }

    const selId = store.selectedId;
    const selChild = store.selectedChildId;

    if (!selId || selId === "bg_band") {
      toolbarEl.hidden = true;
      return;
    }

    // Xác định vị trí hiển thị thanh công cụ ngay phía trên đối tượng
    let targetEl = null;
    if (selId === "logo") {
      targetEl = document.getElementById("logoSticker");
    } else {
      targetEl = document.querySelector(`.scene-obj-box[data-id="${selId}"]`);
    }

    if (!targetEl || targetEl.style.display === "none") {
      toolbarEl.hidden = true;
      return;
    }

    const stageEl = document.getElementById("stickerStage");
    if (!stageEl) return;

    const targetRect = targetEl.getBoundingClientRect();
    const stageRect = stageEl.getBoundingClientRect();

    const topPx = targetRect.top - stageRect.top;
    const leftPx = targetRect.left - stageRect.left + targetRect.width / 2;

    toolbarEl.style.top = `${topPx}px`;
    toolbarEl.style.left = `${leftPx}px`;
    toolbarEl.hidden = false;

    // Dựng các nút hành động cho toolbar
    innerEl.innerHTML = "";

    if (selId === "logo" && !selChild) {
      // Chọn cả nhóm logo
      addActionButton("Bỏ nhóm", () => store.ungroupLogo());
      addActionButton("Nhân bản", () => store.duplicateSelected());
      addActionButton("🗑 Xoá", () => store.deleteSelected(), true);
    } else if (selId === "logo" && selChild === "logo_text") {
      // Chọn chữ trong nhóm logo
      addActionButton("✏️ Sửa chữ", () => onEditLogoText());
      addActionButton("Aa Kiểu", () => onOpenTextOptions());
      addActionButton("🗑 Xoá", () => store.deleteSelected(), true);
    } else if (selId === "logo" && selChild === "logo_img") {
      // Chọn ảnh trong nhóm logo
      addActionButton("🖼 Thay ảnh", () => onChangeLogoImage());
      addActionButton("🗑 Xoá", () => store.deleteSelected(), true);
    } else {
      // Đối tượng chữ hoặc ảnh tự do
      const obj = (store.objects || []).find((o) => o.id === selId);
      if (obj && obj.type === "text") {
        addActionButton("✏️ Sửa chữ", () => onEditFreeText(obj));
        addActionButton("Aa Kiểu", () => onOpenTextOptions());
        addActionButton("Nhân bản", () => store.duplicateSelected());
        addActionButton("🗑 Xoá", () => store.deleteSelected(), true);
      } else if (obj && obj.type === "image") {
        addActionButton("🖼 Thay ảnh", () => onChangeLogoImage());
        addActionButton("Nhân bản", () => store.duplicateSelected());
        addActionButton("🗑 Xoá", () => store.deleteSelected(), true);
      } else {
        addActionButton("🗑 Xoá", () => store.deleteSelected(), true);
      }
    }
  }

  function addActionButton(label, onClick, isDanger = false) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = `btn-float-action ${isDanger ? "btn-danger" : ""}`;
    btn.textContent = label;
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      onClick();
    });
    innerEl.appendChild(btn);
  }

  function onEditLogoText() {
    const store = window.TAIOSceneStore;
    const group = (store.objects || []).find((o) => o.id === "logo");
    const child = group ? (group.children || []).find((c) => c.id === "logo_text") : null;
    const curText = child ? child.text : "TAIO.CLUB";
    const res = window.prompt("Nhập nội dung chữ logo:", curText);
    if (res !== null) {
      store.recordSnapshot();
      if (child) child.text = res.trim() || "TAIO.CLUB";
      store.notifyChange();
    }
  }

  function onEditFreeText(obj) {
    const store = window.TAIOSceneStore;
    const curText = obj.text || "";
    const res = window.prompt("Nhập nội dung chữ:", curText);
    if (res !== null) {
      store.recordSnapshot();
      obj.text = res.trim() || "Chữ";
      store.notifyChange();
    }
  }

  function onOpenTextOptions() {
    const btnAa = document.getElementById("btnOpenTextStyleModal");
    if (btnAa) btnAa.click();
  }

  function onChangeLogoImage() {
    const btnChange = document.getElementById("btnTriggerLogoUpload") || document.getElementById("logoFileInput");
    if (btnChange) btnChange.click();
  }

  function renderLayersList() {
    if (!layersListEl) return;
    const store = window.TAIOSceneStore;
    if (!store) return;

    layersListEl.innerHTML = "";
    const objs = store.objects || [];

    if (objs.length === 0) {
      layersListEl.innerHTML = `<div style="padding: 10px; color: #94A3B8; font-size: 12px; text-align: center;">Chưa có lớp nào</div>`;
      return;
    }

    // Hiển thị lớp từ trên xuống dưới (z cao nhất lên đầu)
    const sorted = [...objs].sort((a, b) => (b.z || 10) - (a.z || 10));

    sorted.forEach((obj) => {
      const row = document.createElement("div");
      const isSel = store.selectedId === obj.id;
      row.className = `layer-item-row ${isSel ? "active" : ""}`;

      let name = obj.id;
      if (obj.type === "group" && obj.id === "logo") name = "🏷️ Nhóm Logo";
      else if (obj.type === "text") name = `🔤 "${(obj.text || "").slice(0, 12)}"`;
      else if (obj.type === "image") name = `🖼️ Ảnh`;

      row.innerHTML = `
        <span class="layer-item-name">${name}</span>
        <div class="layer-item-actions">
          <button type="button" class="btn-layer-vis" title="Ẩn/Hiện">${obj.visible !== false ? "👁" : "🕶"}</button>
          <button type="button" class="btn-layer-del" title="Xoá">🗑</button>
        </div>
      `;

      row.addEventListener("click", (e) => {
        if (e.target.closest(".btn-layer-vis") || e.target.closest(".btn-layer-del")) return;
        store.selectObject(obj.id);
      });

      row.querySelector(".btn-layer-vis").addEventListener("click", (e) => {
        e.stopPropagation();
        store.recordSnapshot();
        obj.visible = obj.visible === false ? true : false;
        store.notifyChange();
        renderLayersList();
      });

      row.querySelector(".btn-layer-del").addEventListener("click", (e) => {
        e.stopPropagation();
        store.selectObject(obj.id);
        store.deleteSelected();
        renderLayersList();
      });

      layersListEl.appendChild(row);
    });
  }

  window.TAIOEditorToolbar = {
    initToolbar,
    updateToolbar,
    toggleLayersDrawer,
    renderLayersList,
  };
})();
