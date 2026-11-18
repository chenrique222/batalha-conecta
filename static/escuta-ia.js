/* Escuta com IA: grava a resposta, percebe sozinha quando a pessoa parou de
   falar e envia o áudio para o servidor transformar em texto (ia.py).
   Tem os mesmos métodos de escuta.js, para a conversa trocar uma pela outra. */
"use strict";
(function (raiz) {
  class EscutaIA {
    static suportada(janela) {
      return Boolean(janela && janela.navigator?.mediaDevices?.getUserMedia && janela.MediaRecorder && (janela.AudioContext || janela.webkitAudioContext));
    }
    constructor(opcoes) {
      this.opcoes = {esperaInicial:30000, pausa:6000, duracaoMaxima:120000, intervalo:100,
        // Ajustes da detecção de fala. Volume vai de 0 a 1; um quadro dura `intervalo` ms.
        limiarMinimo:0.012, quadrosDeFala:3, aquecimento:300,
        // Com `compartilhado`, o microfone pertence à conversa inteira e não é desligado aqui.
        compartilhado:false,
        // Envoltas em funções: chamadas como `this.opcoes.agendar(...)`, as originais dão
        // "Illegal invocation" no Chrome, porque precisam ser chamadas a partir da janela.
        agendar:(funcao, tempo) => setTimeout(funcao, tempo), cancelarTimer:id => clearTimeout(id),
        repetir:(funcao, tempo) => setInterval(funcao, tempo), cancelarRepeticao:id => clearInterval(id),
        agora:() => Date.now(), abrirMicrofone:EscutaIA.abrirMicrofone, criarGravador:EscutaIA.criarGravador,
        criarMedidor:EscutaIA.criarMedidor, ...opcoes};
      this.anterior = opcoes.rascunho || "";
      this.encerrada = false;
      this.finalizando = false;
      this.parou = false;
      this.temFala = false;
      this.manual = false;
      this.timers = new Set();
      this.pedacos = [];
      this.ruido = null;
      this.pico = 0;
      this.seguidos = 0;
      this.ultimoSom = 0;
      this.pedido = typeof AbortController === "undefined" ? null : new AbortController();
    }
    /* ----- Partes do navegador. Os testes trocam estas três funções. ----- */
    static abrirMicrofone() {
      return navigator.mediaDevices.getUserMedia({audio:{echoCancellation:true, noiseSuppression:true, autoGainControl:true}, video:false});
    }
    static criarGravador(fluxo) {
      const tipo = ["audio/webm;codecs=opus", "audio/mp4", "audio/ogg;codecs=opus"].find(valor => MediaRecorder.isTypeSupported(valor));
      // Voz não precisa de alta qualidade: arquivo pequeno chega mais rápido.
      return new MediaRecorder(fluxo, tipo ? {mimeType:tipo, audioBitsPerSecond:32000} : {});
    }
    static criarMedidor(fluxo, contextoPronto) {
      const Contexto = window.AudioContext || window.webkitAudioContext;
      const contexto = contextoPronto || new Contexto();
      if (contexto.state === "suspended") contexto.resume().catch(() => {});
      const origem = contexto.createMediaStreamSource(fluxo);
      const analisador = contexto.createAnalyser();
      analisador.fftSize = 1024;
      origem.connect(analisador);
      const amostras = new Float32Array(analisador.fftSize);
      return {
        // Volume médio do instante (RMS), de 0 a 1.
        nivel() {
          analisador.getFloatTimeDomainData(amostras);
          let soma = 0;
          for (const amostra of amostras) soma += amostra * amostra;
          return Math.sqrt(soma / amostras.length);
        },
        fechar() {
          try { origem.disconnect(); } catch (_) { /* Já desligado. */ }
          if (!contextoPronto) contexto.close().catch(() => {});
        }
      };
    }
    /* ----- Relógios ----- */
    agendar(funcao, tempo) {
      const id = this.opcoes.agendar(() => { this.timers.delete(id); if (!this.encerrada) funcao(); }, tempo);
      this.timers.add(id);
      return id;
    }
    remover(id) { if (id != null) { this.opcoes.cancelarTimer(id); this.timers.delete(id); } }
    iniciar() {
      if (this.encerrada) return this;
      Promise.resolve().then(() => this.opcoes.abrirMicrofone()).then(fluxo => {
        if (this.encerrada) { if (!this.opcoes.compartilhado) EscutaIA.soltar(fluxo); return; }
        this.fluxo = fluxo;
        this.medidor = this.opcoes.criarMedidor(fluxo, this.opcoes.contexto);
        this.gravador = this.opcoes.criarGravador(fluxo);
        this.gravador.ondataavailable = evento => { if (evento.data && evento.data.size) this.pedacos.push(evento.data); };
        this.gravador.onstop = () => this.aoParar();
        this.gravador.onerror = () => this.erro("audio-capture");
        this.gravador.start();
        this.inicio = this.opcoes.agora();
        this.inicioTimer = this.agendar(() => { if (!this.temFala) this.erro("no-speech"); }, this.opcoes.esperaInicial);
        this.agendar(() => this.finalizar(true), this.opcoes.duracaoMaxima);
        this.medicao = this.opcoes.repetir(() => this.medir(), this.opcoes.intervalo);
        this.opcoes.onInicio?.(true);
      }).catch(falha => {
        const nome = falha && falha.name;
        this.erro(nome === "NotAllowedError" || nome === "SecurityError" ? "not-allowed" : nome === "NotFoundError" || nome === "NotReadableError" ? "audio-capture" : "start-failed");
      });
      return this;
    }
    /* Chamado dez vezes por segundo: separa voz de ruído e percebe o silêncio. */
    medir() {
      if (this.encerrada || this.finalizando) return;
      const agora = this.opcoes.agora();
      const nivel = this.medidor.nivel();
      // O ruído do ambiente desce depressa e sobe devagar: a fala não vira "ruído".
      // O primeiro valor tem teto: se a pessoa já estiver falando, a voz não vira "ruído".
      if (this.ruido === null) this.ruido = Math.min(nivel, 0.03);
      else if (nivel < this.ruido) this.ruido = (this.ruido + nivel) / 2;
      // Antes da fala, o ruído pode subir mais rápido (ventilador, rua): ele não vira "fala".
      else this.ruido += (nivel - this.ruido) * (this.temFala ? 0.002 : 0.03);
      // O começo é ignorado: ali toca o sinal sonoro que avisa a pessoa.
      if (agora - this.inicio < this.opcoes.aquecimento) return;
      let limiar = Math.max(this.opcoes.limiarMinimo, this.ruido * 3);
      if (this.temFala) limiar = Math.min(limiar, Math.max(this.opcoes.limiarMinimo, this.pico * 0.5));
      if (nivel > limiar) {
        this.seguidos += 1;
        // Para começar, exigimos som contínuo: uma batida ou um clique não contam.
        if (!this.temFala && this.seguidos >= this.opcoes.quadrosDeFala) {
          this.temFala = true;
          this.remover(this.inicioTimer);
          this.opcoes.onFala?.();
        }
        if (this.temFala) {
          // Depois, qualquer som adia o fim: números ditados são palavras curtas.
          this.pico = Math.max(this.pico * 0.98, nivel);
          this.ultimoSom = agora;
        }
      } else {
        this.seguidos = 0;
        if (this.temFala && agora - this.ultimoSom >= this.opcoes.pausa) this.finalizar(true);
      }
    }
    /* Sem argumento, foi a pessoa que tocou em "Terminei": o áudio é enviado mesmo
       que o medidor não tenha percebido a voz (fala baixa, microfone distante). */
    finalizar(automatico = false) {
      if (this.encerrada || this.finalizando) return;
      if (!this.gravador) { this.erro("no-speech"); return; }
      this.finalizando = true;
      this.manual = !automatico;
      this.pararMedicao();
      try {
        if (this.gravador.state !== "inactive") this.gravador.stop();
        else { this.aoParar(); return; }
      } catch (_) { this.aoParar(); return; }
      this.agendar(() => this.aoParar(), 2000);
    }
    aoParar() {
      if (this.encerrada || this.parou) return;
      this.parou = true;
      const duracao = this.opcoes.agora() - this.inicio;
      const tipo = (this.gravador.mimeType || this.pedacos[0]?.type || "audio/webm").split(";")[0];
      const audio = new Blob(this.pedacos, {type:tipo});
      this.liberar();
      if (!this.finalizando) { this.erro("audio-capture"); return; }
      if (!audio.size || (!this.temFala && !(this.manual && duracao >= 700))) { this.erro("no-speech"); return; }
      this.opcoes.onProcessando?.();
      Promise.resolve().then(() => this.opcoes.transcrever(audio, this.pedido?.signal)).then(texto => {
        if (this.encerrada) return;
        const completo = [this.anterior, String(texto || "").trim()].filter(Boolean).join(" ").replace(/\bterminei[.!?\s]*$/i, "").trim();
        this.cancelar();
        if (completo) this.opcoes.onFinal(completo);
        else this.opcoes.onErro("no-speech", "");
      }, falha => {
        if (this.encerrada) return;
        this.erro(falha && falha.tipo ? falha.tipo : "ia-indisponivel");
      });
    }
    pararMedicao() {
      if (this.medicao != null) this.opcoes.cancelarRepeticao(this.medicao);
      this.medicao = null;
    }
    static soltar(fluxo) {
      try { fluxo.getTracks().forEach(faixa => faixa.stop()); } catch (_) { /* Já liberado. */ }
    }
    liberar() {
      this.pararMedicao();
      if (this.medidor) { this.medidor.fechar(); this.medidor = null; }
      if (this.fluxo && !this.opcoes.compartilhado) EscutaIA.soltar(this.fluxo);
      this.fluxo = null;
    }
    erro(tipo) {
      if (this.encerrada) return;
      const texto = this.cancelar();
      this.opcoes.onErro(tipo, texto);
    }
    /* Para tudo e solta o microfone. Devolve o trecho já transformado em texto antes. */
    cancelar() {
      if (this.encerrada) return this.anterior;
      this.encerrada = true;
      for (const timer of this.timers) this.opcoes.cancelarTimer(timer);
      this.timers.clear();
      if (this.gravador) {
        this.gravador.ondataavailable = this.gravador.onstop = this.gravador.onerror = null;
        try { if (this.gravador.state !== "inactive") this.gravador.stop(); } catch (_) { /* Já parou. */ }
      }
      this.liberar();
      try { this.pedido?.abort(); } catch (_) { /* Nada em andamento. */ }
      return this.anterior;
    }
  }
  if (typeof module !== "undefined" && module.exports) module.exports = EscutaIA;
  else raiz.EscutaIA = EscutaIA;
})(typeof window !== "undefined" ? window : {});
