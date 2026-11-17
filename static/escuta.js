/* Mantém uma resposta aberta mesmo quando o navegador encerra um trecho.
   Os relógios são separados: espera inicial, pausa entre frases e limite total. */
"use strict";
(function (raiz) {
  class EscutaPaciente {
    constructor(opcoes) {
      this.opcoes = {esperaInicial:30000, pausa:6000, duracaoMaxima:120000,
        agendar:setTimeout, cancelarTimer:clearTimeout, agora:Date.now, ...opcoes};
      this.rec = null;
      this.encerrada = false;
      this.timers = new Set();
      this.anterior = opcoes.rascunho || "";
      this.atuais = [];
      this.temFala = Boolean(this.anterior);
      this.iniciada = false;
      this.falhasRapidas = 0;
      this.finalizando = false;
    }
    agendar(funcao, tempo) {
      const id = this.opcoes.agendar(() => { this.timers.delete(id); if (!this.encerrada) funcao(); }, tempo);
      this.timers.add(id);
      return id;
    }
    remover(id) { if (id != null) { this.opcoes.cancelarTimer(id); this.timers.delete(id); } }
    texto() { return [this.anterior, ...this.atuais.map(item => item.texto)].filter(Boolean).join(" ").trim(); }
    iniciar() {
      if (this.encerrada) return;
      this.reiniciar();
      return this;
    }
    reiniciar() {
      if (this.encerrada || this.finalizando) return;
      const rec = new this.opcoes.Reconhecimento();
      this.rec = rec;
      this.atuais = [];
      rec.lang = "pt-BR";
      rec.continuous = true;
      rec.interimResults = true;
      rec.maxAlternatives = 1;
      const inicioTrecho = this.opcoes.agora();
      let recebeuNesteTrecho = false;
      rec.onstart = () => {
        if (this.encerrada || rec !== this.rec) return;
        const primeira = !this.iniciada;
        if (primeira) {
          this.iniciada = true;
          this.inicioTimer = this.agendar(() => { if (!this.temFala) this.erro("no-speech"); }, this.opcoes.esperaInicial);
          this.agendar(() => this.finalizar(), this.opcoes.duracaoMaxima);
        }
        this.opcoes.onInicio?.(primeira);
      };
      rec.onspeechstart = () => {
        if (this.encerrada || rec !== this.rec) return;
        this.remover(this.pausaTimer);
        this.remover(this.inicioTimer);
      };
      rec.onspeechend = () => {
        if (!this.encerrada && rec === this.rec && this.temFala && !this.finalizando) this.esperarPausa();
      };
      rec.onresult = evento => {
        if (this.encerrada || rec !== this.rec) return;
        // A lista do evento já contém os trechos desta sessão. Substituir evita duplicação.
        this.atuais = Array.from(evento.results, resultado => ({texto:resultado[0].transcript.trim(), final:resultado.isFinal}));
        const texto = this.texto();
        if (!texto) return;
        recebeuNesteTrecho = true;
        this.falhasRapidas = 0;
        this.temFala = true;
        this.remover(this.inicioTimer);
        this.opcoes.onParcial?.(texto);
        if (/\bterminei[.!?\s]*$/i.test(texto) && this.atuais.every(item => item.final)) this.finalizar();
        else if (!this.finalizando) this.esperarPausa();
      };
      rec.onerror = evento => {
        if (this.encerrada || rec !== this.rec) return;
        // O silêncio breve não descarta a resposta. onend reabre a escuta.
        if (evento.error !== "no-speech") this.erro(evento.error);
      };
      rec.onend = () => {
        if (this.encerrada || rec !== this.rec) return;
        this.anterior = this.texto();
        this.atuais = [];
        this.rec = null;
        if (this.finalizando) { this.concluir(); return; }
        if (!recebeuNesteTrecho && this.opcoes.agora() - inicioTrecho < 1000) this.falhasRapidas += 1;
        else this.falhasRapidas = 0;
        if (this.falhasRapidas >= 5) { this.erro("service-not-allowed"); return; }
        this.agendar(() => this.reiniciar(), 350);
      };
      try { rec.start(); }
      catch (_) { this.erro("start-failed"); }
    }
    esperarPausa() {
      this.remover(this.pausaTimer);
      this.pausaTimer = this.agendar(() => this.finalizar(), this.opcoes.pausa);
    }
    finalizar() {
      if (this.encerrada || this.finalizando) return;
      this.finalizando = true;
      this.remover(this.pausaTimer);
      if (this.rec) {
        // stop pede o último resultado; abort o descartaria.
        try { this.rec.stop(); } catch (_) { this.concluir(); return; }
        this.agendar(() => this.concluir(), 1800);
      } else this.concluir();
    }
    concluir() {
      if (this.encerrada) return;
      const texto = this.texto().replace(/\bterminei[.!?\s]*$/i, "").trim();
      this.cancelar();
      if (texto) this.opcoes.onFinal(texto);
      else this.opcoes.onErro("no-speech", "");
    }
    erro(tipo) {
      const texto = this.texto();
      this.cancelar();
      this.opcoes.onErro(tipo, texto);
    }
    cancelar() {
      const texto = this.texto();
      this.encerrada = true;
      for (const timer of this.timers) this.opcoes.cancelarTimer(timer);
      this.timers.clear();
      if (this.rec) {
        const rec = this.rec;
        this.rec = null;
        rec.onstart = rec.onresult = rec.onend = rec.onerror = rec.onspeechstart = rec.onspeechend = null;
        try { rec.abort(); } catch (_) { /* Já foi encerrado pelo navegador. */ }
      }
      return texto;
    }
  }
  if (typeof module !== "undefined" && module.exports) module.exports = EscutaPaciente;
  else raiz.EscutaPaciente = EscutaPaciente;
})(typeof window !== "undefined" ? window : {});
