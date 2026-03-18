/**
 * ISUFST CareHub Service Worker
 * Handles offline caching and push notifications
 */

const CACHE_NAME = 'carehub-v1';
const STATIC_ASSETS = [
    '/',
    '/static/css/output.css',
    '/static/css/fontawesome.min.css',
    '/static/css/animations.css',
    '/static/js/calendar.js',
    '/static/favicon.ico'
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
    console.log('[SW] Installing service worker...');
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                console.log('[SW] Caching static assets');
                return cache.addAll(STATIC_ASSETS);
            })
            .then(() => self.skipWaiting())
    );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
    console.log('[SW] Activating service worker...');
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames
                    .filter((name) => name !== CACHE_NAME)
                    .map((name) => {
                        console.log('[SW] Deleting old cache:', name);
                        return caches.delete(name);
                    })
            );
        }).then(() => self.clients.claim())
    );
});

// Fetch event - serve from cache, fallback to network
self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);

    // Skip non-GET requests
    if (request.method !== 'GET') return;

    // Skip API requests (network-first)
    if (url.pathname.startsWith('/api/') || url.pathname.startsWith('/notifications')) {
        event.respondWith(networkFirst(request));
        return;
    }

    // For static assets, use cache-first strategy
    if (url.pathname.startsWith('/static/')) {
        event.respondWith(cacheFirst(request));
        return;
    }

    // For HTML pages, use network-first with cache fallback
    event.respondWith(networkFirst(request));
});

// Cache-first strategy for static assets
async function cacheFirst(request) {
    const cached = await caches.match(request);
    if (cached) return cached;

    try {
        const response = await fetch(request);
        if (response.ok) {
            const cache = await caches.open(CACHE_NAME);
            cache.put(request, response.clone());
        }
        return response;
    } catch (error) {
        console.log('[SW] Fetch failed:', error);
        return new Response('Offline', { status: 503 });
    }
}

// Network-first strategy for dynamic content
async function networkFirst(request) {
    try {
        const response = await fetch(request);
        if (response.ok) {
            const cache = await caches.open(CACHE_NAME);
            cache.put(request, response.clone());
        }
        return response;
    } catch (error) {
        console.log('[SW] Network failed, trying cache:', error);
        const cached = await caches.match(request);
        if (cached) return cached;
        return new Response('Offline - Content not available', { status: 503 });
    }
}

// Push notification handler
self.addEventListener('push', (event) => {
    console.log('[SW] Push received:', event);

    let title = 'ISUFST CareHub';
    let body = 'You have a new notification';
    let icon = '/static/favicon.ico';
    let badge = '/static/favicon.ico';

    if (event.data) {
        try {
            const data = event.data.json();
            title = data.title || title;
            body = data.body || body;
            if (data.icon) icon = data.icon;
        } catch (e) {
            body = event.data.text();
        }
    }

    const options = {
        body: body,
        icon: icon,
        badge: badge,
        vibrate: [100, 50, 100],
        data: {
            dateOfArrival: Date.now(),
            primaryKey: 1
        },
        actions: [
            { action: 'open', title: 'Open App' },
            { action: 'close', title: 'Close' }
        ]
    };

    event.waitUntil(
        self.registration.showNotification(title, options)
    );
});

// Notification click handler
self.addEventListener('notificationclick', (event) => {
    console.log('[SW] Notification clicked:', event);

    event.notification.close();

    if (event.action === 'close') {
        return;
    }

    // Focus on existing window or open new one
    event.waitUntil(
        clients.matchAll({ type: 'window', includeUncontrolled: true })
            .then((clientList) => {
                for (const client of clientList) {
                    if (client.url.includes('/') && 'focus' in client) {
                        return client.focus();
                    }
                }
                if (clients.openWindow) {
                    return clients.openWindow('/');
                }
            })
    );
});

console.log('[SW] Service worker loaded');
