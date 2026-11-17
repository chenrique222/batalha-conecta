/* JavaScript cuida apenas das interações no navegador: voz, etapas e PWA. */
"use strict";

document.querySelectorAll("[data-falar]").forEach(botao => {
  botao.addEventListener("click", () => falar(botao.dataset.falar, botao));
});
document.querySelectorAll("audio").forEach(audio => audio.addEventListener("play", pararVoz));
window.addEventListener("pagehide", pararVoz);

// INSTALAÇÃO: o mesmo endereço se torna um ícone no celular.
let conviteInstalar = null;
const instalar = document.querySelector("#instalar-app");
const dialogInstalar = document.querySelector("#dialog-instalar");
window.addEventListener("beforeinstallprompt", evento => {
  evento.preventDefault();
  conviteInstalar = evento;
  if (instalar) instalar.querySelector("span").textContent = "Instalar aplicativo";
});
if (instalar) {
  instalar.addEventListener("click", async () => {
    if (conviteInstalar) {
      await conviteInstalar.prompt();
      await conviteInstalar.userChoice;
      conviteInstalar = null;
    } else {
      dialogInstalar.showModal();
      if (document.documentElement.dataset.modo === "icones") falar("Para instalar no Android, abra o menu do navegador e escolha instalar aplicativo. No iPhone, toque em compartilhar e adicionar à tela de início. Toque na marca de confirmação para fechar.", instalar);
    }
  });
  document.querySelector("#fechar-instalar").addEventListener("click", () => { pararVoz(); dialogInstalar.close(); });
  window.addEventListener("appinstalled", () => { instalar.hidden = true; });
  if (window.matchMedia("(display-mode: standalone)").matches || window.navigator.standalone) instalar.hidden = true;
}
if ("serviceWorker" in navigator && window.isSecureContext) {
  navigator.serviceWorker.register("/sw.js").catch(() => {
    // O site continua funcionando mesmo quando a instalação não está disponível.
  });
}

// CADASTRO: o formulário continua sendo enviado ao Python e ao banco único.
const formulario = document.querySelector("#form-cadastro");
if (formulario) prepararCadastro();

function prepararCadastro() {
  const passos = [...formulario.querySelectorAll(".passo")];
  const marcadores = [...document.querySelectorAll(".etapas li")];
  const anterior = document.querySelector("#passo-anterior");
  const proximo = document.querySelector("#proximo-passo");
  const publicar = document.querySelector("#publicar");
  const ajuda = document.querySelector("#ouvir-passo");
  const erros = document.querySelector("#erros-cadastro");
  const resumo = document.querySelector("#resumo-cadastro");
  const ouvirResumo = document.querySelector("#ouvir-resumo");
  const audio = document.querySelector("#audio");
  const previaAudio = document.querySelector("#previa-audio");
  const gravar = document.querySelector("#gravar");
  const statusGravacao = document.querySelector("#status-gravacao");
  const removerAudio = document.querySelector("#remover-audio");
  let etapa = 0;
  let audioURL = null;
  let audioGravado = null;
  let gravador = null;
  let fluxoMicrofone = null;
  let relogio = null;
  let gravacaoEmCurso = false;
  let enviando = false;
  let segundos = 0;

  formulario.noValidate = true;
  document.querySelector("#controles-passos").hidden = false;
  ajuda.hidden = false;
  ouvirResumo.hidden = false;

  function mostrarErros(mensagens) {
    erros.replaceChildren();
    mensagens.forEach(mensagem => {
      const linha = document.createElement("p");
      linha.textContent = mensagem;
      erros.append(linha);
    });
    erros.hidden = mensagens.length === 0;
    if (mensagens.length) erros.focus();
  }

  function audioEscolhido() { return audioGravado || audio.files[0]; }

  function validarEtapa(indice) {
    if (gravacaoEmCurso) {
      mostrarErros(["Pare a gravação antes de continuar."]);
      return false;
    }
    for (const campo of passos[indice].querySelectorAll("input, textarea")) {
      if (!campo.checkValidity()) {
        mostrarPasso(indice, false);
        campo.reportValidity();
        return false;
      }
    }
    if (indice === 1 && !formulario.elements.descricao.value.trim() && !audioEscolhido()) {
      mostrarErros(["Conte o que você faz por texto ou por áudio."]);
      return false;
    }
    return true;
  }

  function preencherResumo() {
    resumo.replaceChildren();
    const selecionada = formulario.querySelector("input[name=categoria]:checked");
    const categoria = selecionada ? selecionada.parentElement.querySelector("strong").textContent : "";
    const linhas = [
      ["Seu trabalho", formulario.elements.nome.value],
      ["Atividade", categoria],
      ["Apresentação", formulario.elements.descricao.value || "Apresentação em áudio"],
      ["Comunidade", formulario.elements.comunidade.value],
      ["Telefone", formulario.elements.telefone.value || "Não informado"],
      ["Áudio", audioEscolhido() ? "Áudio incluído" : "Sem áudio gravado"],
      ["Fotos", String(window.galeriaCadastro?.itens.length || 0)]
    ];
    linhas.forEach(([titulo, valor]) => {
      const linha = document.createElement("p");
      const rotulo = document.createElement("strong");
      rotulo.textContent = titulo;
      linha.append(rotulo, document.createTextNode(valor));
      resumo.append(linha);
    });
    (window.galeriaCadastro?.itens || []).forEach(item => {
      const imagem = document.createElement("img");
      imagem.src = item.url;
      imagem.alt = "Foto que aparecerá na galeria";
      resumo.append(imagem);
    });
    if (audioURL) {
      const tocador = document.createElement("audio");
      tocador.controls = true;
      tocador.src = audioURL;
      tocador.setAttribute("aria-label", "Confira sua apresentação em áudio");
      tocador.addEventListener("play", pararVoz);
      resumo.append(tocador);
    }
    ouvirResumo.dataset.falar = linhas.map(([titulo, valor]) => `${titulo}: ${valor}.`).join(" ");
  }

  function mostrarPasso(numero, moverFoco = true) {
    etapa = numero;
    passos.forEach((passo, indice) => { passo.hidden = indice !== numero; });
    marcadores.forEach((marcador, indice) => {
      if (indice === numero) marcador.setAttribute("aria-current", "step");
      else marcador.removeAttribute("aria-current");
    });
    anterior.hidden = numero === 0;
    proximo.hidden = numero === passos.length - 1;
    publicar.hidden = numero !== passos.length - 1;
    ajuda.dataset.falar = passos[numero].dataset.ajuda;
    if (numero === passos.length - 1) preencherResumo();
    if (moverFoco) {
      const titulo = passos[numero].querySelector("legend");
      titulo.setAttribute("tabindex", "-1");
      titulo.focus();
    }
  }

  proximo.addEventListener("click", () => {
    mostrarErros([]);
    if (validarEtapa(etapa)) mostrarPasso(etapa + 1);
  });
  anterior.addEventListener("click", () => { if (!gravacaoEmCurso) { mostrarErros([]); mostrarPasso(etapa - 1); } });
  ajuda.addEventListener("click", () => falar(ajuda.dataset.falar, ajuda));
  ouvirResumo.addEventListener("click", () => falar(ouvirResumo.dataset.falar, ouvirResumo));

  function atualizarAudio(arquivo) {
    previaAudio.pause();
    if (audioURL) URL.revokeObjectURL(audioURL);
    audioURL = arquivo ? URL.createObjectURL(arquivo) : null;
    previaAudio.hidden = !arquivo;
    removerAudio.hidden = !arquivo;
    if (audioURL) previaAudio.src = audioURL;
    else previaAudio.removeAttribute("src");
  }

  audio.addEventListener("change", () => {
    audioGravado = null;
    if (audio.files[0]?.size > 10 * 1024 * 1024) {
      audio.value = "";
      mostrarErros(["Escolha um áudio de até 10 MB."]);
    }
    atualizarAudio(audio.files[0]);
  });
  removerAudio.addEventListener("click", () => { audioGravado = null; audio.value = ""; atualizarAudio(null); statusGravacao.textContent = "Áudio removido."; });

  function liberarMicrofone() {
    if (fluxoMicrofone) fluxoMicrofone.getTracks().forEach(faixa => faixa.stop());
    fluxoMicrofone = null;
    clearInterval(relogio);
    gravacaoEmCurso = false;
    gravar.querySelector("span").textContent = "Gravar minha voz";
    gravar.setAttribute("aria-pressed", "false");
    audio.disabled = false;
    removerAudio.disabled = false;
  }

  if (window.isSecureContext && navigator.mediaDevices?.getUserMedia && window.MediaRecorder) {
    gravar.hidden = false;
    gravar.addEventListener("click", async () => {
      if (gravador && gravador.state === "recording") {
        gravar.disabled = true;
        gravador.stop();
        return;
      }
      pararVoz();
      gravar.disabled = true;
      statusGravacao.textContent = "Aguardando a permissão para usar o microfone…";
      try {
        fluxoMicrofone = await navigator.mediaDevices.getUserMedia({audio:true});
        const tipo = ["audio/webm;codecs=opus", "audio/mp4", "audio/ogg;codecs=opus"].find(valor => MediaRecorder.isTypeSupported(valor));
        gravador = tipo ? new MediaRecorder(fluxoMicrofone, {mimeType:tipo}) : new MediaRecorder(fluxoMicrofone);
        const partes = [];
        gravador.ondataavailable = evento => { if (evento.data.size) partes.push(evento.data); };
        gravador.onstop = () => {
          const gravacao = new Blob(partes, {type:gravador.mimeType || "audio/webm"});
          liberarMicrofone();
          gravar.disabled = false;
          if (gravacao.size > 10 * 1024 * 1024 || gravacao.size === 0) {
            statusGravacao.textContent = "Não foi possível salvar este áudio. Tente uma gravação menor.";
            return;
          }
          audioGravado = gravacao;
          audio.value = "";
          atualizarAudio(audioGravado);
          statusGravacao.textContent = "Gravação pronta. Ouça antes de continuar; você pode gravar novamente.";
        };
        gravador.onerror = () => {
          liberarMicrofone();
          gravar.disabled = false;
          statusGravacao.textContent = "Não foi possível gravar. Tente novamente ou escolha um áudio do aparelho.";
        };
        gravador.start();
        gravacaoEmCurso = true;
        gravar.disabled = false;
        audio.disabled = true;
        removerAudio.disabled = true;
        gravar.querySelector("span").textContent = "Parar gravação";
        gravar.setAttribute("aria-pressed", "true");
        segundos = 0;
        statusGravacao.textContent = "Gravando… 0 de 60 segundos.";
        relogio = setInterval(() => {
          segundos += 1;
          statusGravacao.textContent = `Gravando… ${segundos} de 60 segundos.`;
          if (segundos >= 60 && gravador.state === "recording") { gravar.disabled = true; gravador.stop(); }
        }, 1000);
      } catch (erro) {
        liberarMicrofone();
        gravar.disabled = false;
        statusGravacao.textContent = "O microfone não está disponível ou a permissão foi negada. Você pode escolher um áudio já salvo no aparelho.";
      }
    });
  } else {
    statusGravacao.textContent = "Para gravar aqui, use um navegador compatível com HTTPS ou localhost. Você também pode escolher um áudio salvo.";
  }
  window.addEventListener("pagehide", () => {
    if (gravador?.state === "recording") gravador.stop();
    liberarMicrofone();
    if (audioURL) URL.revokeObjectURL(audioURL);
  });
  // O assistente e a gravação manual nunca usam o microfone juntos.
  document.addEventListener("cadastrovozabrir", () => {
    if (gravador?.state === "recording") gravador.stop();
    liberarMicrofone();
  });

  formulario.addEventListener("submit", async evento => {
    evento.preventDefault();
    if (enviando) return;
    if (etapa < passos.length - 1) { proximo.click(); return; }
    mostrarErros([]);
    for (let numero = 0; numero < passos.length; numero += 1) {
      if (!validarEtapa(numero)) return;
    }
    const dados = new FormData(formulario);
    window.galeriaCadastro?.anexar(dados);
    if (audioGravado) {
      const extensao = audioGravado.type.includes("mp4") ? "m4a" : audioGravado.type.includes("ogg") ? "ogg" : "webm";
      dados.set("audio", audioGravado, `apresentacao.${extensao}`);
    }
    enviando = true;
    publicar.disabled = true;
    anterior.disabled = true;
    publicar.textContent = "Publicando…";
    try {
      const resposta = await fetch(formulario.action, {method:"POST", body:dados, headers:{Accept:"application/json"}});
      const resultado = await resposta.json();
      if (!resposta.ok) { mostrarErros(resultado.erros || ["Não foi possível publicar. Confira as informações."]); }
      else { window.location.assign(resultado.url); return; }
    } catch (erro) {
      mostrarErros(["Não foi possível confirmar a publicação. Confira a conexão e tente novamente. Seus dados continuam nesta tela."]);
    }
    enviando = false;
    publicar.disabled = false;
    anterior.disabled = false;
    publicar.textContent = "Publicar meu trabalho";
  });
  mostrarPasso(0, false);
}
