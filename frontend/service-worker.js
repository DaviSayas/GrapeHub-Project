// GrapeHub Service Worker — caches static shell, never caches API responses.
const CACHE_NAME = 'grapehub-v1';
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/src/assets/styles.css',
  '/src/assets/vue.global.prod.js',
  '/src/assets/vue-router.global.prod.js',
  '/src/assets/chart.umd.min.js',
  '/manifest.json',
];

// API routes that must always go to the network (never cached)
const API_PREFIXES = [
  '/auth', '/users', '/producers', '/grapes', '/wines',
  '/stock', '/tastings', '/wishlist', '/reports', '/uploads', '/api',
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) =>
      Promise.allSettled(STATIC_ASSETS.map((u) => cache.add(u)))
    )
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((names) =>
      Promise.all(names.filter((n) => n !== CACHE_NAME).map((n) => caches.delete(n)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  const { request } = event;
  if (request.method !== 'GET') return;

  const url = new URL(request.url);
  const isApi = API_PREFIXES.some((p) => url.pathname.startsWith(p));

  // API → always network (no caching of dynamic data)
  if (isApi) {
    event.respondWith(fetch(request).catch(() =>
      new Response(JSON.stringify({ detail: 'Sem ligação à rede' }), {
        status: 503, headers: { 'Content-Type': 'application/json' },
      })
    ));
    return;
  }

  // Static → cache-first, fall back to network, then index.html
  event.respondWith(
    caches.match(request).then((cached) => {
      if (cached) return cached;
      return fetch(request).then((resp) => {
        if (resp && resp.status === 200) {
          const copy = resp.clone();
          caches.open(CACHE_NAME).then((c) => c.put(request, copy));
        }
        return resp;
      }).catch(() => caches.match('/index.html'));
    })
  );
});
