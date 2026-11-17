/* Guarda apenas a tela de desconexão e seus recursos. Cadastros exigem rede. */
const CACHE = "batalha-conecta-v6-marca-voz-1";
const RECURSOS = ["/static/offline.html", "/static/estilo.css", "/static/favicon-mapa.svg"];
self.addEventListener("install", evento => {
  evento.waitUntil(caches.open(CACHE).then(cache => cache.addAll(RECURSOS)).then(() => self.skipWaiting()));
});
self.addEventListener("activate", evento => {
  evento.waitUntil(caches.keys().then(chaves => Promise.all(chaves.filter(chave => chave.startsWith("batalha-conecta-") && chave !== CACHE).map(chave => caches.delete(chave)))).then(() => self.clients.claim()));
});
self.addEventListener("fetch", evento => {
  const pedido = evento.request;
  if (pedido.method !== "GET") return;
  const url = new URL(pedido.url);
  if (url.origin !== self.location.origin) return;
  if (pedido.mode === "navigate") {
    evento.respondWith(fetch(pedido).catch(() => caches.match("/static/offline.html")));
  } else if (RECURSOS.includes(url.pathname)) {
    evento.respondWith(fetch(pedido).then(resposta => {
      if (resposta.ok) {
        const copia = resposta.clone();
        evento.waitUntil(caches.open(CACHE).then(cache => cache.put(pedido, copia)));
      }
      return resposta;
    }).catch(() => caches.match(pedido)));
  }
});
