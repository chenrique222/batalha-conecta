/* Assistente com perguntas fixas: não inventa informações e não é um chatbot.
   O navegador transcreve; o Python valida e salva o mesmo cadastro de antes. */
"use strict";
(function () {
  const painel = document.querySelector("#cadastro-voz");
  if (!painel) return;
  const logica = window.BatalhaVoz;
  const form = document.querySelector("#form-cadastro");
  const microfone = document.querySelector("#voz-microfone");
  const repetir = document.querySelector("#voz-repetir");
  const titulo = document.querySelector("#voz-titulo");
  const status = document.querySelector("#voz-status");
  const confirmacoes = document.querySelector("#voz-confirmacoes");
  const botaoPublicar = document.querySelector("#voz-publicar");
  const categoriaBotoes = document.querySelector("#voz-categorias");
  const indisponivel = document.querySelector("#voz-indisponivel");
  const marcadores = [...document.querySelectorAll("[data-corrigir]")];
  const Reconhecimento = window.SpeechRecognition || window.webkitSpeechRecognition;
  const disponivel = Boolean(Reconhecimento && vozDisponivel() && window.isSecureContext);
  const aviso = "Este cadastro transforma sua fala em texto. O navegador pode enviar sua voz ao serviço de reconhecimento pela internet. Você vai ouvir e conferir cada resposta. O perfil só será publicado quando você autorizar. Para pausar, toque no microfone novamente ou diga pausar. Para cancelar, diga cancelar cadastro.";
  let valores = {};
  let etapa = 0;
  let fase = "inicio";
  let pendente = "";
  let ativo = false;
  let geracao = 0;
  let timer = null;
  let escutaPaciente = null;
  let rascunhoEscuta = "";
  const terminarResposta = document.querySelector("#voz-terminar");
  let corrigindoResumo = false;
  let enviando = false;
  let contextoSom = null;
  let manualAlterado = false;
  form.addEventListener("input", () => { manualAlterado = true; });
  form.addEventListener("change", () => { manualAlterado = true; });

  function pararEscuta() {
    clearTimeout(timer);
    if (escutaPaciente) {
      rascunhoEscuta = escutaPaciente.cancelar();
      escutaPaciente = null;
    }
    terminarResposta.hidden = true;
    painel.classList.remove("escutando");
  }
  function pausar() {
    ativo = false;
    geracao += 1;
    pararEscuta();
    pararVoz();
    atualizar();
  }
  function prepararSinal() {
    const Contexto = window.AudioContext || window.webkitAudioContext;
    if (Contexto) {
      contextoSom ||= new Contexto();
      contextoSom.resume().catch(() => {});
    }
  }
  function sinal() {
    if (!contextoSom || contextoSom.state !== "running") return;
    const oscilador = contextoSom.createOscillator();
    const volume = contextoSom.createGain();
    oscilador.frequency.value = 660;
    volume.gain.value = 0.06;
    oscilador.connect(volume).connect(contextoSom.destination);
    oscilador.start();
    oscilador.stop(contextoSom.currentTime + 0.12);
  }
  function atualizar() {
    const atual = logica.etapas[etapa];
    titulo.textContent = fase === "revisao" ? "Ouça e confirme seu perfil" : fase === "inicio" ? "Vamos conversar?" : atual.titulo;
    const simbolo = fase === "revisao" ? "check" : atual.icone;
    painel.querySelector(".voz-ilustracao use").setAttribute("href", `/static/icons.svg#${simbolo}`);
    microfone.setAttribute("aria-pressed", String(ativo));
    const rotulo = ativo ? "Pausar conversa" : fase === "inicio" ? "Começar conversa" : "Continuar conversa";
    microfone.setAttribute("aria-label", rotulo);
    microfone.querySelector("span").textContent = rotulo;
    microfone.querySelector("use").setAttribute("href", `/static/icons.svg#${ativo ? "pausa" : "microfone"}`);
    confirmacoes.hidden = fase !== "confirmacao";
    botaoPublicar.hidden = fase !== "revisao";
    document.querySelector("#voz-fotos").hidden = fase !== "revisao";
    categoriaBotoes.hidden = !(fase === "resposta" && atual.campo === "categoria");
    marcadores.forEach((botao, indice) => {
      botao.disabled = enviando || !(botao.dataset.corrigir in valores);
      botao.classList.toggle("preenchido", botao.dataset.corrigir in valores);
      if (indice === etapa && fase !== "revisao") botao.setAttribute("aria-current", "step");
      else botao.removeAttribute("aria-current");
    });
    painel.querySelectorAll("button:not([data-corrigir])").forEach(botao => { botao.disabled = enviando; });
    microfone.disabled = enviando || !disponivel;
  }
  function mensagemAtual() {
    if (fase === "inicio") return `${aviso} Toque no microfone para começar.`;
    if (fase === "confirmacao") {
      const campo = logica.etapas[etapa].campo;
      return `Entendi: ${logica.lerValor(campo, pendente)}. Está certo? Diga sim ou repetir.`;
    }
    if (fase === "revisao") {
      return `${logica.resumo(valores)} Você escolheu ${window.galeriaCadastro?.itens.length || 0} fotos. Se quiser adicionar fotos, toque na câmera abaixo. Essas informações${valores.telefone ? ", incluindo seu número de contato," : ""} ficarão visíveis para quem acessar o projeto. Para corrigir, diga corrigir nome, atividade, descrição, comunidade ou telefone. Para autorizar a divulgação, diga publicar. Para sair sem publicar, diga cancelar cadastro.`;
    }
    return logica.etapas[etapa].pergunta;
  }
  function dizer(mensagem, ouvirDepois = true, preservarRascunho = false) {
    if (enviando) return;
    pararEscuta();
    if (!preservarRascunho) rascunhoEscuta = "";
    const atual = ++geracao;
    status.textContent = mensagem;
    atualizar();
    falar(mensagem, repetir, () => {
      if (atual !== geracao || !ativo || !ouvirDepois || enviando) return;
      timer = setTimeout(() => escutar(atual), 450);
    }, () => {
      if (atual !== geracao) return;
      pausar();
      indisponivel.hidden = false;
      status.textContent = "Não consegui ler a pergunta. Confira o volume e a voz em português do aparelho ou preencha com ajuda. A escuta está pausada.";
    });
  }
  function falha(mensagem) {
    pausar();
    status.textContent = mensagem;
    indisponivel.hidden = false;
    falar(mensagem, repetir);
  }
  function escutar(atual) {
    if (atual !== geracao || !ativo || enviando) return;
    const campo = logica.etapas[etapa].campo;
    escutaPaciente = new EscutaPaciente({
      Reconhecimento,
      rascunho:rascunhoEscuta,
      pausa:fase === "resposta" ? (campo === "telefone" ? 10000 : 6000) : 2500,
      onInicio(primeira) {
        if (atual !== geracao) return;
        painel.classList.add("escutando");
        terminarResposta.hidden = false;
        status.textContent = "Estou ouvindo. Fale no seu ritmo. Diga terminei ou use a marca de confirmação ao acabar.";
        if (primeira) sinal();
      },
      onParcial(texto) {
        if (atual !== geracao) return;
        rascunhoEscuta = texto;
        status.textContent = `Estou ouvindo: ${texto}`;
      },
      onFinal(texto) {
        if (atual !== geracao) return;
        escutaPaciente = null;
        rascunhoEscuta = "";
        terminarResposta.hidden = true;
        painel.classList.remove("escutando");
        receber(texto);
      },
      onErro(tipo, texto) {
        if (atual !== geracao) return;
        escutaPaciente = null;
        rascunhoEscuta = texto;
        const mensagens = {
          "not-allowed":"O microfone foi bloqueado. Permita o microfone nas configurações do navegador.",
          "service-not-allowed":"O serviço de reconhecimento não ficou disponível neste navegador.",
          "audio-capture":"Não encontrei um microfone disponível. Confira o aparelho.",
          "network":"O reconhecimento de voz não conseguiu se conectar. Confira a internet.",
          "no-speech":"Não ouvi uma resposta durante a espera."
        };
        falha(`${mensagens[tipo] || "Não foi possível iniciar a escuta."} ${texto ? "Guardei o trecho que você falou. Toque no microfone para continuar ou no alto-falante para recomeçar a resposta." : "Toque no microfone para tentar novamente ou preencha com ajuda."}`);
      }
    });
    escutaPaciente.iniciar();
  }
  terminarResposta.addEventListener("click", () => escutaPaciente?.finalizar());
  function receber(texto) {
    if (enviando) return;
    const comando = logica.limpar(texto);
    if (comando === "cancelar cadastro") { cancelar(); return; }
    if (comando === "pausar") { pausar(); status.textContent = "Conversa pausada. Toque no microfone para continuar."; falar(status.textContent, repetir); return; }
    if (comando === "ouvir de novo") { dizer(mensagemAtual()); return; }
    if (fase === "confirmacao") {
      if (logica.sim(texto)) { confirmar(); return; }
      if (logica.nao(texto)) { fase = "resposta"; dizer(mensagemAtual()); return; }
      dizer("Para confirmar essa resposta, diga sim. Para mudar, diga repetir.");
      return;
    }
    if (fase === "revisao") {
      const corrigir = logica.corrigirCampo(texto);
      if (corrigir >= 0) { editar(corrigir); return; }
      if (logica.publicar(texto)) { publicar(); return; }
      dizer("Para autorizar a divulgação, diga publicar. Você também pode dizer corrigir nome, atividade, descrição, comunidade ou telefone. Para sair, diga cancelar cadastro.");
      return;
    }
    const resultado = logica.validar(logica.etapas[etapa].campo, texto);
    if (resultado.erro) { dizer(resultado.erro); return; }
    pendente = resultado.valor;
    fase = "confirmacao";
    dizer(mensagemAtual());
  }
  function confirmar() {
    const campo = logica.etapas[etapa].campo;
    valores[campo] = pendente;
    form.elements[campo].value = pendente;
    if (corrigindoResumo || etapa === logica.etapas.length - 1) {
      fase = "revisao";
      corrigindoResumo = false;
    } else { etapa += 1; fase = "resposta"; }
    dizer(mensagemAtual());
  }
  function editar(indice) {
    if (enviando) return;
    corrigindoResumo = logica.etapas.every(item => item.campo in valores);
    etapa = indice;
    fase = "resposta";
    ativo = true;
    dizer(mensagemAtual());
  }
  function cancelar() {
    if (enviando) return;
    pausar();
    for (const campo of Object.keys(valores)) form.elements[campo].value = "";
    valores = {};
    window.galeriaCadastro?.limpar();
    rascunhoEscuta = "";
    pendente = "";
    etapa = 0;
    fase = "inicio";
    corrigindoResumo = false;
    atualizar();
    status.textContent = "Conversa cancelada. Este rascunho foi apagado e não foi publicado.";
    falar(status.textContent, repetir);
  }
  async function publicar() {
    if (enviando || fase !== "revisao") return;
    // A confirmação oral só funciona na revisão, depois de todas as respostas.
    if (!logica.etapas.every(item => item.campo in valores)) return;
    pausar();
    enviando = true;
    atualizar();
    status.textContent = "Publicando seu trabalho…";
    const dados = new FormData();
    for (const [campo, valor] of Object.entries(valores)) dados.set(campo, valor);
    dados.set("csrf", form.elements.csrf.value);
    dados.set("envio_id", form.elements.envio_id.value);
    dados.set("consentimento", "sim");
    window.galeriaCadastro?.anexar(dados);
    try {
      const resposta = await fetch(form.action, {method:"POST", body:dados, headers:{Accept:"application/json"}});
      const resultado = await resposta.json();
      if (!resposta.ok) throw new Error((resultado.erros || ["Não foi possível publicar."]).join(" "));
      fase = "concluido";
      status.textContent = "Seu trabalho foi publicado. Abrindo seu perfil.";
      let navegou = false;
      const abrirPerfil = () => {
        if (navegou) return;
        navegou = true;
        window.location.assign(resultado.url);
      };
      falar(status.textContent, repetir, abrirPerfil, abrirPerfil);
      // Há uma saída mesmo se o aparelho não devolver o evento de fim do áudio.
      timer = setTimeout(abrirPerfil, 15000);
      return;
    } catch (erro) {
      enviando = false;
      atualizar();
      falha(`${erro.message === "Failed to fetch" ? "A conexão falhou." : erro.message} Seus dados continuam nesta tela. Confira a conexão ou corrija as informações. Depois toque no microfone para ouvir o resumo e tentar novamente.`);
    }
  }
  function mostrarVoz(usar) {
    if (enviando) return;
    pausar();
    if (usar && manualAlterado) {
      // Alterações digitadas também são lidas na revisão antes de publicar.
      valores = {};
      for (const item of logica.etapas) {
        const entrada = form.elements[item.campo].value.trim();
        let resultado;
        if (item.campo === "categoria") resultado = logica.categorias[entrada] ? {valor:entrada} : {erro:true};
        else if (item.campo === "telefone" && !entrada) resultado = {valor:""};
        else resultado = logica.validar(item.campo, entrada);
        if (!resultado.erro) valores[item.campo] = resultado.valor;
      }
      const faltante = logica.etapas.findIndex(item => !(item.campo in valores));
      etapa = faltante < 0 ? logica.etapas.length - 1 : faltante;
      fase = faltante < 0 ? "revisao" : "resposta";
      corrigindoResumo = false;
      pendente = "";
      manualAlterado = false;
      rascunhoEscuta = "";
      atualizar();
    }
    const galeria = document.querySelector("#galeria-cadastro");
    document.querySelector(usar ? "#voz-fotos" : "#fotos-manuais").append(galeria);
    painel.hidden = !usar;
    form.hidden = usar;
    document.querySelector("#etapas-manuais").hidden = usar;
    document.querySelector("#usar-voz").setAttribute("aria-pressed", String(usar));
    document.querySelector("#usar-formulario").setAttribute("aria-pressed", String(!usar));
    if (usar) document.dispatchEvent(new Event("cadastrovozabrir"));
  }
  microfone.addEventListener("click", () => {
    if (ativo) { pausar(); status.textContent = "Conversa pausada."; return; }
    if (!disponivel) return;
    prepararSinal();
    ativo = true;
    indisponivel.hidden = true;
    if (fase === "inicio") { fase = "resposta"; dizer(`${aviso} Fale depois do sinal. Você pode fazer pausas. Ao acabar, diga terminei ou toque na marca de confirmação. ${mensagemAtual()}`); }
    else dizer(rascunhoEscuta ? `Já ouvi: ${rascunhoEscuta}. Pode continuar depois do sinal. Ao acabar, diga terminei.` : mensagemAtual(), true, true);
  });
  repetir.addEventListener("click", () => {
    // Repetir a orientação inicial não abre o microfone.
    if (fase !== "inicio" && disponivel) ativo = true;
    dizer(mensagemAtual(), fase !== "inicio");
  });
  document.querySelector("#voz-sim").addEventListener("click", () => { ativo = true; pararEscuta(); confirmar(); });
  document.querySelector("#voz-nao").addEventListener("click", () => { ativo = true; fase = "resposta"; dizer(mensagemAtual()); });
  botaoPublicar.addEventListener("click", publicar);
  document.querySelector("#voz-cancelar").addEventListener("click", cancelar);
  document.querySelector("#usar-voz").addEventListener("click", () => { mostrarVoz(true); dizer(mensagemAtual(), false); });
  document.querySelector("#usar-formulario").addEventListener("click", () => mostrarVoz(false));
  document.querySelector("#voz-formulario").addEventListener("click", () => { aplicarModo("texto"); mostrarVoz(false); });
  document.querySelector("#voz-ajuda").addEventListener("click", evento => falar("O ditado precisa de um navegador compatível, permissão de microfone e conexão. Você pode tentar Chrome atualizado no computador ou no Android. No celular, o endereço deve usar HTTPS. Para pedir acompanhamento, toque no desenho de livro e preencha com alguém de sua confiança. Nenhum número de telefone é obrigatório.", evento.currentTarget));
  marcadores.forEach((botao, indice) => botao.addEventListener("click", () => editar(indice)));
  categoriaBotoes.querySelectorAll("button").forEach(botao => botao.addEventListener("click", () => {
    ativo = true;
    pendente = botao.dataset.categoriaVoz;
    fase = "confirmacao";
    dizer(mensagemAtual());
  }));
  document.addEventListener("modoalterado", evento => mostrarVoz(evento.detail === "icones"));
  document.querySelector("#voz-fotos").addEventListener("click", () => { if (ativo) pausar(); }, true);
  document.querySelector("#galeria-cadastro").addEventListener("change", () => { if (ativo) pausar(); });
  // Outra leitura de tela interrompe a conversa; nunca ficamos ouvindo escondidos.
  document.addEventListener("click", evento => {
    if (ativo && !painel.contains(evento.target) && evento.target.closest("button, a, audio")) pausar();
  }, true);
  document.addEventListener("visibilitychange", () => { if (document.hidden && !enviando) pausar(); });
  window.addEventListener("pagehide", () => { pausar(); if (contextoSom) contextoSom.close().catch(() => {}); });
  indisponivel.hidden = disponivel;
  mostrarVoz(document.documentElement.dataset.modo === "icones");
  atualizar();
})();
