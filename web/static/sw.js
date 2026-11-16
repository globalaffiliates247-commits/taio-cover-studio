// Minimal Service Worker for TAIO Cover Studio PWA installability
const CACHE_NAME = 'taio-cover-studio-v1';

self.addEventListener('install', (event) => {
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(self.clients.claim());
});

self.addEventListener('fetch', (event) => {
  // Network first strategy - pass through all dynamic requests
  event.respondWith(
    fetch(event.request).catch(() => caches.match(event.request))
  );
});
