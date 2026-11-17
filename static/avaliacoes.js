/* Grava a voz de verdade. Não transcreve nem encerra por pausas na fala. */
"use strict";
(function () {
  const form = document.querySelector("#form-avaliacao");
  if (!form) return;
  const gravar = document.querySelector("#avaliacao-gravar");
  const parar = document.querySelector("#avaliacao-parar");
  const arquivo = document.querySelector("#avaliacao-arquivo");
  const previa = document.querySelector("#avaliacao-previa");
  const refazer = document.querySelector("#avaliacao-refazer");
  const publicar = document.querySelector("#avaliacao-publicar");
  const status = document.querySelector("#avaliacao-status");
  const erro = document.querySelector("#avaliacao-erro");
  const tempo = document.querySelector("#avaliacao-tempo");
  const disponivel = Boolean(window.isSecureContext && navigator.mediaDevices?.getUserMedia && window.MediaRecorder);
  let fluxo = null, gravador = null, relogio = null, dadosAudio = null, previaURL = null;
  let estado = "vazio", geracao = 0, inicio = 0, falhou = false, saiu = false;

  function informar(texto, falarTambem = false) {
    status.textContent = texto;
    if (falarTambem && document.documentElement.dataset.modo === "icones") falar(texto, refazer);
  }
  function mostrarErro(texto) {
    erro.hidden = !texto;
    erro.textContent = texto;
    if (texto && document.documentElement.dataset.modo === "icones") falar(texto, refazer);
  }
  function atualizar() {
    const ocupado = ["permissao", "gravando", "parando", "enviando"].includes(estado);
    gravar.hidden = !disponivel || estado === "gravando" || estado === "parando";
    gravar.disabled = ocupado;
    gravar.setAttribute("aria-pressed", String(estado === "gravando"));
    parar.hidden = estado !== "gravando";
    arquivo.disabled = ocupado;
    previa.hidden = !dadosAudio || ocupado;
    refazer.hidden = !dadosAudio || ocupado;
    publicar.disabled = ocupado || !dadosAudio || !form.querySelector('[name="nota"]:checked');
    form.querySelectorAll('[name="nota"], [name="nome"]').forEach(campo => { campo.disabled = estado === "enviando"; });
    tempo.hidden = estado !== "gravando";
    form.classList.toggle("gravando", estado === "gravando");
  }
  function liberar() {
    clearInterval(relogio);
    if (fluxo) fluxo.getTracks().forEach(faixa => faixa.stop());
    fluxo = null;
  }
  function mostrarAudio(blob) {
    previa.pause();
    if (previaURL) URL.revokeObjectURL(previaURL);
    dadosAudio = blob;
    previaURL = blob ? URL.createObjectURL(blob) : null;
    if (previaURL) previa.src = previaURL;
    else previa.removeAttribute("src");
    estado = blob ? "pronto" : "vazio";
    atualizar();
  }
  function terminar() {
    if (estado !== "gravando") return;
    estado = "parando";
    if (gravador?.state === "recording") gravador.stop();
    liberar();
    atualizar();
  }
  gravar.addEventListener("click", async () => {
    if (!["vazio", "pronto"].includes(estado) || !disponivel) return;
    pararVoz();
    document.querySelectorAll("audio").forEach(audio => audio.pause());
    mostrarErro("");
    estado = "permissao";
    atualizar();
    informar("Permita o microfone. A gravação começa quando o contador aparecer.");
    const tentativa = ++geracao;
    try {
      const novoFluxo = await navigator.mediaDevices.getUserMedia({audio:{echoCancellation:true, noiseSuppression:true}, video:false});
      if (tentativa !== geracao || saiu) { novoFluxo.getTracks().forEach(faixa => faixa.stop()); return; }
      fluxo = novoFluxo;
      const tipo = ["audio/webm;codecs=opus", "audio/mp4", "audio/ogg;codecs=opus"].find(valor => MediaRecorder.isTypeSupported(valor));
      gravador = new MediaRecorder(fluxo, tipo ? {mimeType:tipo, audioBitsPerSecond:64000} : {});
      const partes = [];
      falhou = false;
      let tamanho = 0;
      gravador.ondataavailable = evento => {
        if (!evento.data.size || tentativa !== geracao) return;
        partes.push(evento.data);
        tamanho += evento.data.size;
        if (tamanho > 10 * 1024 * 1024) { falhou = true; terminar(); }
      };
      gravador.onstop = () => {
        liberar();
        if (tentativa !== geracao || saiu) return;
        const blob = new Blob(partes, {type:gravador.mimeType || "audio/webm"});
        if (falhou || !blob.size || blob.size > 10 * 1024 * 1024) {
          estado = dadosAudio ? "pronto" : "vazio";
          atualizar();
          mostrarErro("Não foi possível salvar a gravação. Tente novamente ou escolha um áudio de até dez megabytes.");
          return;
        }
        arquivo.value = "";
        mostrarAudio(blob);
        informar("Gravação pronta. Ouça para conferir. Escolha as estrelas e toque na marca de confirmação para autorizar a publicação da sua voz neste perfil.", true);
      };
      gravador.onerror = () => {
        falhou = true;
        terminar();
        liberar();
        estado = dadosAudio ? "pronto" : "vazio";
        atualizar();
        mostrarErro("O microfone parou. Tente gravar novamente.");
      };
      fluxo.getAudioTracks().forEach(faixa => faixa.addEventListener("ended", terminar));
      gravador.start(1000);
      estado = "gravando";
      inicio = Date.now();
      tempo.querySelector("[data-tempo]").textContent = "0:00 / 2:00";
      informar("Gravando. Fale no seu ritmo. Toque no quadrado quando terminar.");
      atualizar();
      relogio = setInterval(() => {
        const segundos = Math.min(120, Math.floor((Date.now() - inicio) / 1000));
        tempo.querySelector("[data-tempo]").textContent = `${Math.floor(segundos / 60)}:${String(segundos % 60).padStart(2, "0")} / 2:00`;
        if (segundos >= 120) terminar();
      }, 250);
    } catch (_) {
      if (tentativa !== geracao) return;
      liberar();
      estado = dadosAudio ? "pronto" : "vazio";
      atualizar();
      mostrarErro("Não consegui abrir o microfone. Permita o acesso no navegador ou use o desenho de celular para escolher um áudio salvo.");
    }
  });
  parar.addEventListener("click", terminar);
  refazer.addEventListener("click", () => {
    if (!["vazio", "pronto"].includes(estado)) return;
    pararVoz();
    arquivo.value = "";
    mostrarAudio(null);
    mostrarErro("");
    informar("Áudio descartado. Toque no microfone para gravar outra vez.", true);
  });
  arquivo.addEventListener("change", () => {
    const escolhido = arquivo.files[0];
    if (!escolhido) return;
    if (!escolhido.size || escolhido.size > 10 * 1024 * 1024) {
      arquivo.value = "";
      mostrarErro("Escolha um áudio com conteúdo e até dez megabytes.");
      return;
    }
    pararVoz();
    mostrarErro("");
    mostrarAudio(escolhido);
    informar("Áudio escolhido. Ouça para conferir antes de publicar.", true);
  });
  form.querySelectorAll('[name="nota"]').forEach(campo => campo.addEventListener("change", () => {
    atualizar();
    if (document.documentElement.dataset.modo === "icones" && estado !== "gravando") falar(campo.getAttribute("aria-label"), gravar);
  }));
  form.addEventListener("submit", async evento => {
    evento.preventDefault();
    if (estado !== "pronto" || !dadosAudio) return;
    if (!form.reportValidity()) return;
    pararVoz();
    previa.pause();
    const dados = new FormData(form);
    const extensao = dadosAudio.type.includes("mp4") ? "m4a" : dadosAudio.type.includes("ogg") ? "ogg" : "webm";
    dados.set("audio", dadosAudio, dadosAudio.name || `avaliacao.${extensao}`);
    dados.set("consentimento", "sim");
    estado = "enviando";
    mostrarErro("");
    atualizar();
    informar("Publicando sua avaliação…");
    try {
      const resposta = await fetch(form.action, {method:"POST", body:dados, headers:{Accept:"application/json"}});
      const resultado = await resposta.json();
      if (!resposta.ok) throw new Error((resultado.erros || ["Não foi possível publicar."]).join(" "));
      try { sessionStorage.setItem("batalha-avaliacao-enviada", "sim"); } catch (_) {}
      window.location.assign(resultado.url);
      window.location.reload();
      return;
    } catch (falha) {
      estado = "pronto";
      atualizar();
      mostrarErro(falha.message === "Failed to fetch" ? "A conexão falhou. Seu áudio continua nesta tela. Tente publicar novamente." : falha.message);
    }
  });
  function cancelarEspera() {
    if (estado === "permissao") {
      geracao += 1;
      estado = dadosAudio ? "pronto" : "vazio";
      atualizar();
    }
    terminar();
  }
  // Uma narração nunca deve entrar no áudio da avaliação.
  document.addEventListener("narracaoiniciada", cancelarEspera);
  document.querySelectorAll("audio").forEach(audio => audio.addEventListener("play", cancelarEspera));
  document.addEventListener("visibilitychange", () => { if (document.hidden) cancelarEspera(); });
  window.addEventListener("pagehide", () => {
    saiu = true;
    geracao += 1;
    terminar();
    liberar();
    if (previaURL) URL.revokeObjectURL(previaURL);
  });
  if (!disponivel) informar("Para gravar, abra o aplicativo por HTTPS ou localhost e permita o microfone. Você pode escolher um áudio já salvo no aparelho.");
  try {
    if (sessionStorage.getItem("batalha-avaliacao-enviada")) {
      sessionStorage.removeItem("batalha-avaliacao-enviada");
      informar("Sua avaliação foi publicada. Ela aparece na lista acima.");
    }
  } catch (_) {}
  atualizar();
})();
