/**
 * TAIO Cover Studio — Layout Icons (FEATURE v1.5 P6)
 * Kho SVG nét 2D (stroke="currentColor") chuẩn CapCut/TikTok cho thanh Tab, Cột Quick-Rail và Toolbar.
 */

(function () {
  "use strict";

  const ICONS = {
    // 1. Mẫu: Khung chia dải chữ nhật (Template)
    template: `
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
        <line x1="3" y1="9" x2="21" y2="9"/>
        <line x1="9" y1="21" x2="9" y2="9"/>
      </svg>
    `,

    // 2. Nền: Giọt màu gradient / Palette (Background)
    background: `
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"/>
      </svg>
    `,

    // 3. Cap: Chữ T đơn giản (Caption chính)
    caption: `
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <polyline points="4 7 4 4 20 4 20 7"/>
        <line x1="12" y1="4" x2="12" y2="20"/>
      </svg>
    `,

    // 4. Logo: Huy hiệu tròn thương hiệu (Brand Badge)
    logo: `
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="9"/>
        <path d="M12 7v10"/>
        <path d="M8 12h8"/>
      </svg>
    `,

    // 5. + Chữ: Chữ T kèm dấu cộng (Add Free Text)
    add_text: `
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M3 6h10"/>
        <path d="M8 6v14"/>
        <path d="M18 11v6"/>
        <path d="M15 14h6"/>
      </svg>
    `,

    // 6. AI: Ngôi sao lấp lánh (AI Sparkles)
    ai: `
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M12 3l1.9 4.8L19 9.7l-4.1 3.5 1.3 5.4-4.2-2.8-4.2 2.8 1.3-5.4-4.1-3.5 5.1-1.9L12 3z"/>
      </svg>
    `,

    // 7. Lớp: 3 tấm thẻ xếp chồng lên nhau (Layers)
    layers: `
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <polygon points="12 2 2 7 12 12 22 7 12 2"/>
        <polyline points="2 17 12 22 22 17"/>
        <polyline points="2 12 12 17 22 12"/>
      </svg>
    `,

    // Cột TikTok Quick-Rail
    undo: `
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M3 7v6h6"/>
        <path d="M21 17a9 9 0 0 0-9-9 9 9 0 0 0-6 2.3L3 13"/>
      </svg>
    `,

    redo: `
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M21 7v6h-6"/>
        <path d="M3 17a9 9 0 0 1 9-9 9 9 0 0 1 6 2.3L21 13"/>
      </svg>
    `,

    download: `
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
        <polyline points="7 10 12 15 17 10"/>
        <line x1="12" y1="15" x2="12" y2="3"/>
      </svg>
    `,

    share: `
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8"/>
        <polyline points="16 6 12 2 8 6"/>
        <line x1="12" y1="2" x2="12" y2="15"/>
      </svg>
    `,

    telegram: `
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <line x1="22" y1="2" x2="11" y2="13"/>
        <polygon points="22 2 15 22 11 13 2 9 22 2"/>
      </svg>
    `,

    mp4: `
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <polygon points="5 3 19 12 5 21 5 3"/>
      </svg>
    `,

    edit: `
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M12 20h9"/>
        <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/>
      </svg>
    `,
  };

  function getIcon(name, size) {
    let svg = ICONS[name] || "";
    if (size && svg) {
      svg = svg.replace(/width="[0-9]+"/, `width="${size}"`).replace(/height="[0-9]+"/, `height="${size}"`);
    }
    return svg;
  }

  window.TAIOIcons = {
    get: getIcon,
    map: ICONS,
  };
})();
