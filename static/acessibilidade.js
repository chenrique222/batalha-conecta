"use strict";
const alternarModo = document.querySelector("#alternar-modo");
function aplicarModo(modo, anunciar = false, origem = null) {
  modo = modo === "icones" ? "icones" : "texto";
  document.documentElement.dataset.modo = modo;
  alternarModo?.setAttribute("aria-checked", String(modo === "icones"));
  try { localStorage.setItem("batalha-modo", modo); } catch (_) { /* A escolha ainda funciona nesta aba. */ }
  document.dispatchEvent(new CustomEvent("modoalterado", {detail:modo}));
  if (anunciar) {
    const explicacao = modo === "icones"
      ? "Imagens e voz ativado. A bolinha do interruptor está à direita, perto da pessoa falando. Toque no interruptor novamente para voltar aos textos, do lado do livro. O botão verde com uma pessoa falando abre seu cadastro. O botão azul com pessoas e uma lupa procura serviços. Os alto-falantes amarelos explicam as opções."
      : "Modo com textos ativado.";
    // Uma nova alternância anuncia o novo estado, mesmo se a fala anterior não acabou.
    pararVoz();
    falar(explicacao, origem || alternarModo);
  }
}
alternarModo?.addEventListener("click", () => aplicarModo(
  document.documentElement.dataset.modo === "icones" ? "texto" : "icones", true, alternarModo
));
aplicarModo(document.documentElement.dataset.modo === "icones" ? "icones" : "texto");
window.addEventListener("storage", evento => {
  if (evento.key === "batalha-modo") aplicarModo(evento.newValue === "icones" ? "icones" : "texto");
});
