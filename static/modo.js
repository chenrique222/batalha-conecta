/* Carregado antes da página para lembrar a escolha sem piscar os textos. */
"use strict";
try {
  const escolha = localStorage.getItem("batalha-modo");
  document.documentElement.dataset.modo = escolha === "icones" ? "icones" : "texto";
} catch (_) {
  document.documentElement.dataset.modo = "texto";
}
