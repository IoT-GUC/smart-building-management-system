const CACHE_NAME = 'smartbms-cache-v2';
const STATIC_ASSETS = [
  '/uploads/bright_theme.css',
  '/uploads/graphs.js',
  '/uploads/help_system.js',
  '/uploads/search_system.js',
  '/uploads/realtime_toasts.js',
  '/uploads/analytics_widget.js',
  '/uploads/bulk_import.js',
  'https://cdn.jsdelivr.net/npm/chart.js'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(STATIC_ASSETS))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys.filter(key => key !== CACHE_NAME)
            .map(key => caches.delete(key))
      )
    ).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', event => {
  // Network-first for HTML pages (always get fresh content)
  if (event.request.mode === 'navigate' || event.request.headers.get('accept')?.includes('text/html')) {
    event.respondWith(
      fetch(event.request)
        .catch(() => caches.match('/') || new Response('Offline', { status: 503 }))
    );
    return;
  }
  
  // Cache-first for static assets only
  event.respondWith(
    caches.match(event.request)
      .then(cached => cached || fetch(event.request).then(response => {
        if (response.ok && STATIC_ASSETS.some(url => event.request.url.includes(url))) {
          const clone = response.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
        }
        return response;
      }))
      .catch(() => new Response('Offline', { status: 503 }))
  );
});
