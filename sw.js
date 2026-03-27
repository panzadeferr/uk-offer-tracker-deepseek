// Money Hunters UK — Service Worker v2
// Strategy: Network first for HTML, cache first for static assets
const CACHE = 'mh-v2';

// Static assets to precache (rarely change)
const PRECACHE = [
  '/manifest.json',
  '/icon-192.png',
  '/icon-512.png',
  '/apple-touch-icon.png'
];

// HTML pages — always try network first
const HTML_PAGES = ['/', '/index.html', '/app.html'];

self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE)
      .then(c => c.addAll(PRECACHE).catch(() => {}))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE).map(k => {
        console.log('[SW] Deleting old cache:', k);
        return caches.delete(k);
      }))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;

  const url = new URL(e.request.url);

  // Never cache external APIs
  if (
    url.hostname.includes('reddit.com') ||
    url.hostname.includes('rss2json') ||
    url.hostname.includes('supabase.co') ||
    url.hostname.includes('railway.app') ||
    url.hostname.includes('brevo.com')
  ) {
    return;
  }

  // HTML pages — network first, fall back to cache
  if (e.request.destination === 'document' || HTML_PAGES.includes(url.pathname)) {
    e.respondWith(
      fetch(e.request)
        .then(response => {
          if (response.ok) {
            const clone = response.clone();
            caches.open(CACHE).then(c => c.put(e.request, clone));
          }
          return response;
        })
        .catch(() => {
          return caches.match(e.request)
            .then(cached => cached || caches.match('/index.html'));
        })
    );
    return;
  }

  // Static assets — cache first, network fallback
  e.respondWith(
    caches.match(e.request).then(cached => {
      if (cached) return cached;
      return fetch(e.request).then(response => {
        if (response.ok) {
          const clone = response.clone();
          caches.open(CACHE).then(c => c.put(e.request, clone));
        }
        return response;
      });
    })
  );
});

// Push notification handler
self.addEventListener('push', e => {
  if (!e.data) return;
  const data = e.data.json();
  self.registration.showNotification(data.title || 'Money Hunters UK', {
    body: data.body || 'New deal available',
    icon: '/icon-192.png',
    badge: '/icon-192.png',
    data: { url: data.url || '/' },
    vibrate: [100, 50, 100]
  });
});

self.addEventListener('notificationclick', e => {
  e.notification.close();
  e.waitUntil(clients.openWindow(e.notification.data?.url || '/'));
});
