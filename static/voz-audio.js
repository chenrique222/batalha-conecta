/* Narração com voz natural. As falas fixas são preparadas antes de serem
   necessárias; a voz do aparelho só entra se a voz natural falhar de verdade. */
"use strict";
let botaoFalando = null;
let geracaoFala = 0;
let pedidoVoz = null;
let fonteVoz = null;
let contextoVoz = null;
let limiteVoz = null;
const statusVoz = document.querySelector("#status-voz");
// Prazo para cada parte da fala. Uma frase curta costuma chegar em 1 a 2 segundos.
const ESPERA_VOZ_ONLINE = 5000;
const NARRADORES = ["francisca", "antonio", "aparelho"];
const AMOSTRAS_PRONTAS = ["francisca", "antonio"];
const PAUSA_SERVICO_LENTO = 30000;
const cacheAudios = new Map();
const servicoLentoAte = new Map();
let cacheAudioBytes = 0;
const TEXTO_AMOSTRA = "Olá! Vamos mostrar o seu trabalho? Você pode falar com calma. Estou aqui para ajudar.";
let narradorEscolhido = "francisca";
try { narradorEscolhido = localStorage.getItem("batalha-narrador") || "francisca"; } catch (_) {}
// Quem tinha escolhido Thalita (versão anterior) volta para Francisca.
if (!NARRADORES.includes(narradorEscolhido)) narradorEscolhido = "francisca";
// Falas fixas do aplicativo: o servidor pode guardá-las em disco. Respostas de pessoas nunca entram aqui.
const falasFixas = new Set([TEXTO_AMOSTRA]);
document.querySelectorAll("[data-falar]").forEach(elemento => { if (elemento.dataset.falar) falasFixas.add(elemento.dataset.falar); });
const preparadas = new Map();
let filaPreparo = Promise.resolve();

async function buscarVoz(texto, narrador, sinal, fixa = falasFixas.has(texto)) {
  const dados = new FormData();
  dados.set("texto", texto);
  dados.set("narrador", narrador);
  if (fixa) dados.set("fixa", "1");
  dados.set("csrf", document.querySelector('meta[name="csrf-token"]')?.content || "");
  const resposta = await fetch("/api/voz", {method:"POST", body:dados, signal:sinal, headers:{Accept:"audio/mpeg, application/json"}});
  if (!resposta.ok) throw new Error("Voz indisponível");
  return resposta.arrayBuffer();
}
/* Busca em segundo plano, uma de cada vez, as falas que a tela vai usar. */
/* `inteiras`: trechos que tocam como uma parte só, depois de uma frase variável ("Anotei: …"). */
function prepararFalas(textos, inteiras = []) {
  const narrador = narradorEscolhido;
  const primeiras = [], demais = [];
  for (const texto of textos) {
    if (!texto || texto.length > 2500) continue;
    falasFixas.add(texto);
    const partes = dividirFala(texto);
    primeiras.push(partes[0]);
    demais.push(...partes.slice(1));
  }
  for (const texto of [...primeiras, ...inteiras, ...demais]) {
    falasFixas.add(texto);
    // Sem saída de áudio para a voz natural, o preparo seria um pedido desperdiçado.
    if (narrador === "aparelho" || typeof fetch !== "function" || !(window.AudioContext || window.webkitAudioContext)) continue;
    const chave = narrador + "\u0000" + texto;
    if (cacheAudios.has(chave) || preparadas.has(chave) || preparadas.size >= 60) continue;
    const item = {iniciada:false, bytes:null};
    item.bytes = filaPreparo.then(() => { item.iniciada = true; return buscarVoz(texto, narrador); });
    item.bytes.catch(() => preparadas.delete(chave));
    preparadas.set(chave, item);
    filaPreparo = item.bytes.catch(() => {});
  }
}

function escolherNarrador(nome) {
  if (!NARRADORES.includes(nome)) return;
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

/* Divide a fala em frases. A primeira toca assim que fica pronta; as outras são
   preparadas enquanto ela toca. Assim, um texto longo não deixa a pessoa esperando. */
function dividirFala(texto) {
  const frases = (texto.match(/[^.!?…]+(?:[.!?…]+["”»)]*|$)/g) || [texto]).map(frase => frase.trim()).filter(Boolean);
  const partes = [];
  for (const frase of frases) {
    const ultima = partes[partes.length - 1];
    // A primeira parte fica curta para começar logo; uma frase muito curta ("Olá!") vai junto com a seguinte.
    // Depois da primeira parte, as frases se juntam até ~240 letras.
    if (ultima !== undefined && (ultima.length < 12 || (partes.length > 1 && ultima.length + frase.length < 240))) partes[partes.length - 1] = `${ultima} ${frase}`;
    else partes.push(frase);
  }
  return partes.length ? partes : [texto];
}

function falar(texto, botao, aoTerminar = null, aoFalhar = null) {
  if (!aoTerminar && botaoFalando === botao) { pararVoz(); return; }
  pararVoz();
  document.querySelectorAll("audio").forEach(audio => audio.pause());
  document.dispatchEvent(new Event("narracaoiniciada"));
  const atual = geracaoFala;
  const narrador = narradorEscolhido;
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
  /* Lê com a voz do aparelho o que ainda falta dizer. */
  function vozDoAparelho(resto = texto) {
    if (!vigente() || alternativaIniciada) return;
    alternativaIniciada = true;
    clearTimeout(limiteVoz);
    if (pedidoVoz) pedidoVoz.abort();
    pedidoVoz = null;
    if (!window.speechSynthesis) { terminarSemVoz(); return; }
    statusVoz.hidden = false;
    statusVoz.textContent = narrador === "aparelho" ? "Usando a voz do aparelho." : "Usando a voz do aparelho para evitar a espera.";
    const frase = new SpeechSynthesisUtterance(resto);
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
  if (narrador === "aparelho") { vozDoAparelho(); return; }
  const Contexto = window.AudioContext || window.webkitAudioContext;
  if (!Contexto) { vozDoAparelho(); return; }
  const amostra = texto === TEXTO_AMOSTRA;
  const amostraPronta = amostra && AMOSTRAS_PRONTAS.includes(narrador);
  const partes = amostraPronta ? [texto] : dividirFala(texto);
  const chaveDe = parte => narrador + "\u0000" + parte;
  const fixa = falasFixas.has(texto);
  const guardadaInicio = cacheAudios.has(chaveDe(partes[0]));
  // Depois de uma falha, não repetimos a mesma espera a cada pergunta.
  if (!guardadaInicio && !amostra && (servicoLentoAte.get(narrador) || 0) > Date.now()) { vozDoAparelho(); return; }
  const controlador = new AbortController();
  pedidoVoz = controlador;
  const carregando = new Map();
  /* Obtém o áudio de uma parte: memória, preparo antecipado, amostra ou servidor. */
  function carregar(indice) {
    if (carregando.has(indice)) return carregando.get(indice);
    const parte = partes[indice];
    const chave = chaveDe(parte);
    const promessa = (async () => {
      const guardado = cacheAudios.get(chave);
      if (guardado) { cacheAudios.delete(chave); cacheAudios.set(chave, guardado); return guardado.audio; }
      let bytes = null;
      const preparada = preparadas.get(chave);
      // Só aproveitamos o preparo que já começou; o que ainda está na fila demoraria mais.
      if (preparada && preparada.iniciada) bytes = await preparada.bytes.then(pronto => pronto.slice(0), () => null);
      if (!bytes && amostraPronta) {
        const resposta = await fetch(`/static/vozes/amostra-${narrador}.mp3`, {signal:controlador.signal});
        if (!resposta.ok) throw new Error("Voz indisponível");
        bytes = await resposta.arrayBuffer();
      } else if (!bytes) {
        bytes = await buscarVoz(parte, narrador, controlador.signal, fixa || falasFixas.has(parte));
      }
      const audio = await contextoVoz.decodeAudioData(bytes);
      guardarAudio(chave, audio);
      preparadas.delete(chave);
      return audio;
    })();
    promessa.catch(() => {});
    carregando.set(indice, promessa);
    return promessa;
  }
  function tocar(audio, depois) {
    if (!vigente() || alternativaIniciada) return;
    if (contextoVoz.state !== "running") throw new Error("Áudio pausado pelo navegador");
    const fonte = contextoVoz.createBufferSource();
    fonte.buffer = audio;
    fonte.connect(contextoVoz.destination);
    fonte.onended = () => {
      if (!vigente() || alternativaIniciada) return;
      fonte.disconnect();
      if (fonteVoz === fonte) fonteVoz = null;
      depois();
    };
    fonteVoz = fonte;
    fonte.start();
    clearTimeout(limiteVoz);
    statusVoz.hidden = true;
  }
  /* Toca a parte `indice`. O prazo vale para cada espera, não para a fala inteira. */
  function tocarParte(indice) {
    if (!vigente() || alternativaIniciada) return;
    const resto = () => partes.slice(indice).join(" ");
    const desistir = () => {
      if (!vigente() || alternativaIniciada) return;
      if (indice === 0 && !amostra) servicoLentoAte.set(narrador, Date.now() + PAUSA_SERVICO_LENTO);
      vozDoAparelho(resto());
    };
    // O prazo cobre também um download ou uma decodificação que não terminam.
    clearTimeout(limiteVoz);
    limiteVoz = setTimeout(desistir, ESPERA_VOZ_ONLINE);
    carregar(indice).then(audio => {
      if (!vigente() || alternativaIniciada) return;
      if (indice === 0 && !amostra) servicoLentoAte.delete(narrador);
      const proxima = indice + 1 < partes.length;
      if (proxima) carregar(indice + 1);
      tocar(audio, () => {
        if (!proxima) { pedidoVoz = null; terminar(); return; }
        tocarParte(indice + 1);
      });
    }).catch(desistir);
  }
  let pronta;
  try {
    contextoVoz ||= new Contexto();
    pronta = contextoVoz.resume();
  } catch (_) { vozDoAparelho(); return; }
  // Enquanto o navegador libera o som, a primeira e a segunda partes já são pedidas.
  if (contextoVoz) { carregar(0); if (partes.length > 1) carregar(1); }
  clearTimeout(limiteVoz);
  limiteVoz = setTimeout(() => {
    if (!vigente() || alternativaIniciada) return;
    if (!amostra && !guardadaInicio) servicoLentoAte.set(narrador, Date.now() + PAUSA_SERVICO_LENTO);
    vozDoAparelho();
  }, ESPERA_VOZ_ONLINE);
  Promise.resolve(pronta).then(() => tocarParte(0), () => {
    if (!vigente() || alternativaIniciada) return;
    vozDoAparelho();
  });
}
