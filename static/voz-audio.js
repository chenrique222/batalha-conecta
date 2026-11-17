/* Narração com cache em memória e alternativa rápida se a voz online demorar. */
"use strict";
let botaoFalando = null;
let geracaoFala = 0;
let pedidoVoz = null;
let fonteVoz = null;
let contextoVoz = null;
let limiteVoz = null;
const statusVoz = document.querySelector("#status-voz");
const ESPERA_VOZ_ONLINE = 2500;
const PAUSA_SERVICO_LENTO = 30000;
const cacheAudios = new Map();
const servicoLentoAte = new Map();
let cacheAudioBytes = 0;
const TEXTO_AMOSTRA = "Olá! Vamos mostrar o seu trabalho? Você pode falar com calma. Estou aqui para ajudar.";
let narradorEscolhido = "francisca";
try { narradorEscolhido = localStorage.getItem("batalha-narrador") || "francisca"; } catch (_) {}
if (!["francisca", "antonio", "aparelho"].includes(narradorEscolhido)) narradorEscolhido = "francisca";

function escolherNarrador(nome) {
  if (!["francisca", "antonio", "aparelho"].includes(nome)) return;
  narradorEscolhido = nome;
  try { localStorage.setItem("batalha-narrador", nome); } catch (_) {}
  document.querySelectorAll("[data-narrador]").forEach(botao => botao.setAttribute("aria-current", String(botao.dataset.narrador === nome)));
}
document.querySelectorAll("[data-narrador]").forEach(botao => botao.addEventListener("click", () => {
  escolherNarrador(botao.dataset.narrador);
  servicoLentoAte.delete(narradorEscolhido);
  falar(narradorEscolhido === "aparelho" ? "Você escolheu a voz do aparelho. Pode repetir as orientações quando quiser." : TEXTO_AMOSTRA, botao);
}));
escolherNarrador(narradorEscolhido);

function vozDisponivel() {
  return Boolean(window.AudioContext || window.webkitAudioContext || window.speechSynthesis);
}
function marcarNarracao(botao, falando) {
  botao.dataset.narrando = String(falando);
  if (botao.getAttribute("role") !== "switch") botao.setAttribute("aria-pressed", String(falando));
}
function guardarAudio(chave, audio) {
  const tamanho = audio.length * audio.numberOfChannels * 4;
  if (!Number.isFinite(tamanho) || tamanho > 6 * 1024 * 1024) return;
  const anterior = cacheAudios.get(chave);
  if (anterior) { cacheAudioBytes -= anterior.tamanho; cacheAudios.delete(chave); }
  cacheAudios.set(chave, {audio, tamanho});
  cacheAudioBytes += tamanho;
  while (cacheAudios.size > 32 || cacheAudioBytes > 24 * 1024 * 1024) {
    const primeira = cacheAudios.keys().next().value;
    cacheAudioBytes -= cacheAudios.get(primeira).tamanho;
    cacheAudios.delete(primeira);
  }
}
function pararVoz() {
  geracaoFala += 1;
  clearTimeout(limiteVoz);
  if (pedidoVoz) pedidoVoz.abort();
  pedidoVoz = null;
  if (fonteVoz) {
    fonteVoz.onended = null;
    try { fonteVoz.stop(); } catch (_) { /* Já terminou. */ }
    fonteVoz.disconnect();
    fonteVoz = null;
  }
  if (window.speechSynthesis) window.speechSynthesis.cancel();
  if (botaoFalando) marcarNarracao(botaoFalando, false);
  botaoFalando = null;
  statusVoz.hidden = true;
}

function falar(texto, botao, aoTerminar = null, aoFalhar = null) {
  if (!aoTerminar && botaoFalando === botao) { pararVoz(); return; }
  pararVoz();
  document.querySelectorAll("audio").forEach(audio => audio.pause());
  document.dispatchEvent(new Event("narracaoiniciada"));
  const atual = geracaoFala;
  const narrador = narradorEscolhido;
  const chave = narrador + "\u0000" + texto;
  let finalizada = false;
  let alternativaIniciada = false;
  botaoFalando = botao;
  marcarNarracao(botao, true);
  statusVoz.hidden = false;
  statusVoz.textContent = "Preparando a voz…";
  const vigente = () => atual === geracaoFala && !finalizada;
  const terminar = () => {
    if (!vigente()) return;
    finalizada = true;
    marcarNarracao(botao, false);
    botaoFalando = null;
    statusVoz.hidden = true;
    if (aoTerminar) aoTerminar();
  };
  function terminarSemVoz() {
    if (!vigente()) return;
    finalizada = true;
    marcarNarracao(botao, false);
    botaoFalando = null;
    statusVoz.hidden = false;
    statusVoz.textContent = "Não foi possível reproduzir a fala. Confira o volume e tente o botão de ouvir novamente.";
    if (aoFalhar) aoFalhar();
  }
  function vozDoAparelho() {
    if (!vigente() || alternativaIniciada) return;
    alternativaIniciada = true;
    clearTimeout(limiteVoz);
    if (pedidoVoz) pedidoVoz.abort();
    pedidoVoz = null;
    if (!window.speechSynthesis) { terminarSemVoz(); return; }
    statusVoz.hidden = false;
    statusVoz.textContent = narrador === "aparelho" ? "Usando a voz do aparelho." : "Usando a voz do aparelho para evitar a espera.";
    const frase = new SpeechSynthesisUtterance(texto);
    frase.lang = "pt-BR";
    frase.rate = 1;
    const vozes = window.speechSynthesis.getVoices();
    const brasileiras = vozes.filter(v => v.lang.replace("_", "-").toLowerCase() === "pt-br");
    frase.voice = brasileiras.find(v => /natural|neural/i.test(v.name)) || brasileiras[0] || vozes.find(v => v.lang.startsWith("pt")) || null;
    frase.onend = terminar;
    frase.onerror = evento => {
      if (vigente() && !["interrupted", "canceled"].includes(evento.error)) terminarSemVoz();
    };
    try { window.speechSynthesis.speak(frase); } catch (_) { terminarSemVoz(); }
  }
  function tocar(audio) {
    if (!vigente() || alternativaIniciada) return;
    if (contextoVoz.state !== "running") throw new Error("Áudio pausado pelo navegador");
    const fonte = contextoVoz.createBufferSource();
    fonte.buffer = audio;
    fonte.connect(contextoVoz.destination);
    fonte.onended = () => {
      if (!vigente() || alternativaIniciada) return;
      fonte.disconnect();
      if (fonteVoz === fonte) fonteVoz = null;
      terminar();
    };
    fonteVoz = fonte;
    fonte.start();
    clearTimeout(limiteVoz);
    pedidoVoz = null;
    statusVoz.hidden = true;
  }
  if (narrador === "aparelho") { vozDoAparelho(); return; }
  const Contexto = window.AudioContext || window.webkitAudioContext;
  if (!Contexto) { vozDoAparelho(); return; }
  const guardado = cacheAudios.get(chave);
  const amostra = texto === TEXTO_AMOSTRA;
  // Depois de uma falha, não repetimos a mesma espera a cada pergunta.
  if (!guardado && !amostra && (servicoLentoAte.get(narrador) || 0) > Date.now()) { vozDoAparelho(); return; }
  const controlador = new AbortController();
  pedidoVoz = controlador;
  const usarAlternativa = () => {
    if (!vigente() || alternativaIniciada) return;
    if (!amostra && !guardado) servicoLentoAte.set(narrador, Date.now() + PAUSA_SERVICO_LENTO);
    vozDoAparelho();
  };
  // O prazo cobre também um download ou uma decodificação que não terminam.
  limiteVoz = setTimeout(usarAlternativa, ESPERA_VOZ_ONLINE);
  let pronta;
  try {
    contextoVoz ||= new Contexto();
    pronta = contextoVoz.resume();
  } catch (_) { usarAlternativa(); return; }
  Promise.resolve(pronta).then(async () => {
    if (!vigente() || alternativaIniciada) return;
    if (guardado) {
      cacheAudios.delete(chave); cacheAudios.set(chave, guardado);
      tocar(guardado.audio); return;
    }
    let resposta;
    if (amostra) {
      resposta = await fetch(`/static/vozes/amostra-${narrador}.mp3`, {signal:controlador.signal});
    } else {
      const dados = new FormData();
      dados.set("texto", texto);
      dados.set("narrador", narrador);
      dados.set("csrf", document.querySelector('meta[name="csrf-token"]')?.content || "");
      resposta = await fetch("/api/voz", {method:"POST", body:dados, signal:controlador.signal, headers:{Accept:"audio/mpeg, application/json"}});
    }
    if (!resposta.ok) throw new Error("Voz indisponível");
    const bytes = await resposta.arrayBuffer();
    if (!vigente() || alternativaIniciada) return;
    const audio = await contextoVoz.decodeAudioData(bytes);
    if (!vigente() || alternativaIniciada) return;
    guardarAudio(chave, audio);
    if (!amostra) servicoLentoAte.delete(narrador);
    tocar(audio);
  }).catch(usarAlternativa);
}
