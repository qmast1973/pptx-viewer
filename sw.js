// 앱 설치용 서비스 워커 (tools/build.py 가 VERSION 을 채워 sw.js 로 만든다 — sw.js 는 직접 고치지 않음)
// - 앱 파일을 보관해 두고 빠르게·인터넷 없이도 연다. 화면(index.html)은 인터넷이 되면 항상 새 판을 먼저 받는다
// - 다른 앱(카톡 등)에서 '공유'로 보낸 .pptx 를 받아 화면으로 넘긴다 (manifest share_target)
const VERSION = "4f154dbc16ec";
const CACHE = "pv-" + VERSION, SHARE = "pv-share";
const CORE = ["./", "index.html", "manifest.webmanifest", "vendor/pptx-vanilla-viewer.bundle.js",
  "icons/icon-192.png", "icons/icon-512.png", "icons/icon-maskable-512.png", "icons/apple-touch-icon.png"];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(CORE)).then(() => self.skipWaiting()));
});
self.addEventListener("activate", (e) => {
  e.waitUntil(caches.keys().then((ks) => Promise.all(ks.filter((k) => k.startsWith("pv-") && k !== CACHE && k !== SHARE).map((k) => caches.delete(k))))
    .then(() => self.clients.claim()));
});

self.addEventListener("fetch", (e) => {
  const req = e.request, url = new URL(req.url);
  // 공유로 받은 파일: 잠시 보관하고 화면을 ?shared=1 로 연다
  if (req.method === "POST" && url.pathname.endsWith("/share-target")) {
    e.respondWith((async () => {
      try {
        const fd = await req.formData(), f = fd.get("file");
        if (f && typeof f !== "string") {
          const c = await caches.open(SHARE);
          await c.put("shared-file", new Response(f, { headers: { "Content-Type": f.type || "application/octet-stream", "X-File-Name": encodeURIComponent(f.name || "공유받은 파일.pptx") } }));
        }
      } catch { /* 받지 못하면 그냥 화면만 연다 */ }
      return Response.redirect(new URL("./?shared=1", self.registration.scope).href, 303);
    })());
    return;
  }
  if (req.method !== "GET") return;
  if (req.mode === "navigate") {                 // 화면: 인터넷 먼저, 안 되면 보관본
    e.respondWith(fetch(req).then((res) => { const cp = res.clone(); caches.open(CACHE).then((c) => c.put("index.html", cp)); return res; })
      .catch(() => caches.match("index.html", { ignoreSearch: true }).then((r) => r || caches.match("./"))));
    return;
  }
  if (url.origin === location.origin) {         // 앱 파일: 보관본 먼저
    e.respondWith(caches.match(req, { ignoreSearch: true }).then((r) => r || fetch(req).then((res) => {
      if (res.ok) { const cp = res.clone(); caches.open(CACHE).then((c) => c.put(req, cp)); } return res; })));
    return;
  }
  if (/fonts\.(googleapis|gstatic)\.com$/.test(url.hostname)) {   // 글꼴: 받아 두고 인터넷이 없으면 보관본
    e.respondWith(caches.open(CACHE).then((c) => c.match(req).then((hit) => {
      const net = fetch(req).then((res) => { if (res.ok || res.type === "opaque") c.put(req, res.clone()); return res; }).catch(() => hit);
      return hit || net;
    })));
  }
});
