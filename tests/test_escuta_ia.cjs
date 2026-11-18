/* Execute: node --test tests/test_escuta_ia.cjs. Microfone, relógio e serviço são simulados. */
const test = require("node:test");
const assert = require("node:assert/strict");
const EscutaIA = require("../static/escuta-ia.js");
const voz = require("../static/voz-logica.js");

const esvaziar = async () => { for (let i = 0; i < 20; i++) await Promise.resolve(); };
async function ambiente(opcoes = {}) {
  let tempo = 0, id = 0;
  const timers = new Map(), repeticoes = new Map();
  const a = {volume:0.001, finais:[], erros:[], eventos:[], enviados:[], faixasParadas:0, medidorFechado:false, sinais:[],
    transcricao:Promise.resolve("Faço bolos."), abrir:() => Promise.resolve({getTracks:() => [{stop() { a.faixasParadas++; }}]})};
  // Avança o relógio de 100 em 100 ms, como o navegador faria.
  a.avancar = async duracao => {
    for (const fim = tempo + duracao; tempo < fim;) {
      tempo += 100;
      for (const [chave, timer] of [...timers]) if (timer.quando <= tempo && timers.delete(chave)) timer.funcao();
      for (const repeticao of [...repeticoes.values()]) repeticao();
      await esvaziar();
    }
  };
  a.falar = async (duracao, volume = 0.2) => { a.volume = volume; await a.avancar(duracao); a.volume = 0.001; };
  a.escuta = new EscutaIA({
    agora:() => tempo, agendar:(funcao, ms) => { timers.set(++id, {funcao, quando:tempo + ms}); return id; }, cancelarTimer:i => timers.delete(i),
    repetir:funcao => { repeticoes.set(++id, funcao); return id; }, cancelarRepeticao:i => repeticoes.delete(i),
    abrirMicrofone:() => a.abrir(),
    criarMedidor:() => ({nivel:() => a.volume, fechar() { a.medidorFechado = true; }}),
    criarGravador:() => (a.gravador = {state:"inactive", mimeType:"audio/webm;codecs=opus",
      start() { this.state = "recording"; },
      stop() { this.state = "inactive"; this.ondataavailable?.({data:new Blob(["audio"])}); this.onstop?.(); }}),
    transcrever:(audio, sinal) => { a.enviados.push(audio); a.sinais.push(sinal); return a.transcricao; },
    onInicio:() => a.eventos.push("inicio"), onFala:() => a.eventos.push("fala"), onProcessando:() => a.eventos.push("processando"),
    onFinal:texto => a.finais.push(texto), onErro:(tipo, texto) => a.erros.push({tipo, texto}), ...opcoes});
  a.timers = timers; a.repeticoes = repeticoes;
  a.escuta.iniciar();
  await esvaziar();
  return a;
}

test("espera a pausa inteira depois da fala e envia uma gravação só", async () => {
  const a = await ambiente();
  await a.avancar(1000); await a.falar(2000); await a.avancar(4000);
  assert.deepEqual(a.finais, []); assert.equal(a.enviados.length, 0);
  await a.falar(1000);                      // voltou a falar: a pausa recomeça
  await a.avancar(5800); assert.equal(a.enviados.length, 0);
  await a.avancar(300);
  assert.deepEqual(a.finais, ["Faço bolos."]); assert.equal(a.enviados.length, 1);
  assert.equal(a.enviados[0].type, "audio/webm");
  assert.deepEqual(a.eventos, ["inicio", "fala", "processando"]);
  assert.equal(a.faixasParadas, 1, "o microfone é solto"); assert.equal(a.medidorFechado, true);
  assert.equal(a.timers.size + a.repeticoes.size, 0);
});
test("o sinal sonoro e estalos curtos não contam como fala", async () => {
  const a = await ambiente();
  await a.falar(300, 0.5);                  // sinal do começo, dentro do aquecimento
  await a.avancar(1000); await a.falar(200, 0.5); await a.avancar(1000);
  assert.equal(a.escuta.temFala, false);
  await a.avancar(28000);
  assert.deepEqual(a.erros, [{tipo:"no-speech", texto:""}]); assert.equal(a.enviados.length, 0);
});
test("ruído constante do ambiente não segura a escuta nem esconde a voz", async () => {
  const a = await ambiente();
  a.volume = 0.03; await a.avancar(3000);   // feira barulhenta
  assert.equal(a.escuta.temFala, false);
  a.volume = 0.2; await a.avancar(1500);
  assert.equal(a.escuta.temFala, true);
  a.volume = 0.03; await a.avancar(6200);
  assert.deepEqual(a.finais, ["Faço bolos."]);
});
test("números ditados devagar: palavras curtas adiam o fim", async () => {
  const a = await ambiente({pausa:10000});
  await a.avancar(600); await a.falar(500);
  for (let i = 0; i < 5; i++) { await a.avancar(8000); await a.falar(200); }
  assert.deepEqual(a.finais, []);
  await a.avancar(10100); assert.equal(a.finais.length, 1);
});
test("tocar em Terminei envia mesmo se o medidor não percebeu a voz baixa", async () => {
  const a = await ambiente();
  await a.avancar(500); a.escuta.finalizar(); await esvaziar();
  assert.deepEqual(a.erros, [{tipo:"no-speech", texto:""}], "toque imediato não envia gravação vazia");
  const b = await ambiente();
  await b.avancar(1500); b.escuta.finalizar(); await esvaziar();
  assert.equal(b.enviados.length, 1); assert.deepEqual(b.finais, ["Faço bolos."]);
});
test("retira terminei, junta o trecho anterior e trata resposta vazia", async () => {
  const a = await ambiente({rascunho:"Faço bolos"});
  a.transcricao = Promise.resolve(" de milho. Terminei. ");
  await a.avancar(600); await a.falar(1000); a.escuta.finalizar(); await esvaziar();
  assert.deepEqual(a.finais, ["Faço bolos de milho."]);
  const b = await ambiente();
  b.transcricao = Promise.resolve("");
  await b.avancar(600); await b.falar(1000); b.escuta.finalizar(); await esvaziar();
  assert.deepEqual(b.erros, [{tipo:"no-speech", texto:""}]);
});
test("falha do serviço preserva o trecho anterior e avisa para usar a alternativa", async () => {
  const a = await ambiente({rascunho:"Faço bolos"});
  a.transcricao = Promise.reject(new Error("503"));
  await a.avancar(600); await a.falar(1000); a.escuta.finalizar(); await esvaziar();
  assert.deepEqual(a.erros, [{tipo:"ia-indisponivel", texto:"Faço bolos"}]); assert.deepEqual(a.finais, []);
});
test("cancelar solta o microfone, aborta o envio e nada mais acontece", async () => {
  const a = await ambiente({rascunho:"Trecho"});
  await a.avancar(600); await a.falar(1000);
  assert.equal(a.escuta.cancelar(), "Trecho");
  await a.avancar(200000);
  assert.equal(a.faixasParadas, 1); assert.equal(a.gravador.state, "inactive");
  assert.deepEqual([a.finais, a.erros, a.enviados], [[], [], []]);
  const b = await ambiente();
  let resolver; b.transcricao = new Promise(r => { resolver = r; });
  await b.avancar(600); await b.falar(1000); b.escuta.finalizar(); await esvaziar();
  b.escuta.cancelar(); assert.equal(b.sinais[0].aborted, true);
  resolver("chegou tarde"); await esvaziar();
  assert.deepEqual([b.finais, b.erros], [[], []]);
});
test("permissão negada, falta de microfone e cancelamento antes de abrir", async () => {
  for (const [nome, tipo] of [["NotAllowedError", "not-allowed"], ["NotFoundError", "audio-capture"], ["OutroErro", "start-failed"]]) {
    const a = await ambiente({abrirMicrofone:() => Promise.reject(Object.assign(new Error(nome), {name:nome}))});
    assert.deepEqual(a.erros, [{tipo, texto:""}]);
  }
  let entregar; const fluxo = {getTracks:() => [{stop() { fluxo.parado = true; }}]};
  const b = await ambiente({abrirMicrofone:() => new Promise(r => { entregar = r; })});
  b.escuta.cancelar(); entregar(fluxo); await esvaziar();
  assert.equal(fluxo.parado, true, "microfone concedido depois do cancelamento é solto");
  assert.deepEqual(b.eventos, []);
});
test("limites: 30 s para começar e 120 s no total", async () => {
  const a = await ambiente();
  await a.avancar(29900); assert.deepEqual(a.erros, []);
  await a.avancar(200); assert.equal(a.erros[0].tipo, "no-speech");
  const b = await ambiente();
  await b.avancar(1000); b.volume = 0.2; await b.avancar(118800); assert.equal(b.enviados.length, 0);
  await b.avancar(300); assert.equal(b.enviados.length, 1);
});
test("triagem: as regras fixas resolvem o que é certo; o resto vai para a IA", () => {
  assert.equal(voz.clara("confirmacao", "nome", "Sim."), true);
  assert.equal(voz.clara("confirmacao", "nome", "Tá certinho"), false);
  assert.equal(voz.clara("revisao", "telefone", "Pode publicar!"), true);
  assert.equal(voz.clara("revisao", "telefone", "não quero publicar"), false);
  assert.equal(voz.clara("revisao", "telefone", "corrigir nome"), true);
  assert.equal(voz.clara("resposta", "telefone", "86 99981-2345"), true);
  assert.equal(voz.clara("resposta", "telefone", "meu zap é 86 99981-2345"), false);
  assert.equal(voz.clara("resposta", "telefone", "Pular."), true);
  assert.equal(voz.clara("resposta", "categoria", "Artesanato."), true);
  assert.equal(voz.clara("resposta", "categoria", "eu vendo bolo e também faço crochê para fora"), false);
  assert.equal(voz.clara("resposta", "nome", "Maria"), false);
  assert.equal(voz.clara("resposta", "nome", "Cancelar cadastro."), true);
  assert.deepEqual(voz.validar("comunidade", "Centro."), {valor:"Centro"});
  assert.deepEqual(voz.validar("descricao", "Faço bolos."), {valor:"Faço bolos."});
});
test("ruído constante do ambiente (ventilador, rua) não é tomado por fala", async () => {
  const a = await ambiente();
  a.volume = 0.02; await a.avancar(3000);
  assert.equal(a.escuta.temFala, false, "ruído constante não vira fala");
  a.volume = 0.2; await a.avancar(800); a.volume = 0.02;
  assert.equal(a.escuta.temFala, true, "a voz, mais alta que o ruído, é percebida");
  await a.avancar(6100);
  assert.deepEqual(a.finais, ["Faço bolos."], "com o ruído de volta, o silêncio da pessoa encerra a resposta");
});
test("quem já está falando quando o microfone abre também é ouvido", async () => {
  const a = await ambiente();
  await a.falar(1500); await a.avancar(6100);
  assert.deepEqual(a.finais, ["Faço bolos."]);
});
test("microfone da conversa (compartilhado) não é desligado entre as respostas", async () => {
  const a = await ambiente({compartilhado:true});
  await a.falar(1000); await a.avancar(6100);
  assert.deepEqual(a.finais, ["Faço bolos."]);
  assert.equal(a.faixasParadas, 0, "quem solta o microfone é a conversa, ao pausar ou terminar");
  assert.equal(a.medidorFechado, true);
});
test("relógios padrão funcionam no navegador (sem 'Illegal invocation')", () => {
  // No Chrome, setTimeout e parecidas falham se chamadas a partir de outro objeto.
  const originais = {setTimeout, clearTimeout, setInterval, clearInterval};
  const exigente = original => function (...args) {
    if (this !== undefined && this !== globalThis) throw new TypeError("Illegal invocation");
    return original(...args);
  };
  for (const nome of Object.keys(originais)) globalThis[nome] = exigente(originais[nome]);
  try {
    const escuta = new EscutaIA({transcrever: async () => "", onFinal() {}, onErro() {}});
    const id = escuta.agendar(() => {}, 10);
    escuta.remover(id);
    const repeticao = escuta.opcoes.repetir(() => {}, 10);
    escuta.opcoes.cancelarRepeticao(repeticao);
    assert.equal(typeof escuta.opcoes.agora(), "number");
  } finally {
    Object.assign(globalThis, originais);
  }
});
