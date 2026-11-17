/* Relógio e serviço de voz simulados: verifica atrasos sem esperar pela internet. */
const {JSDOM, VirtualConsole} = require('jsdom');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const base = process.env.BATALHA_TESTE_URL || 'http://127.0.0.1:5005';
const script = fs.readFileSync(path.join(__dirname, '../static/voz-audio.js'), 'utf8');
const pendente = () => {
  let resolve, reject;
  const promise = new Promise((a, b) => {resolve = a; reject = b;});
  return {promise, resolve, reject};
};
const esvaziar = async () => {for (let i = 0; i < 20; i++) await Promise.resolve();};

(async () => {
  const html = await (await fetch(base + '/ajuda')).text();
  function abrir(opcoes = {}) {
    const erros = [], vc = new VirtualConsole();
    vc.on('jsdomError', erro => erros.push(erro.message));
    const dom = new JSDOM(html, {url:base + '/ajuda', runScripts:'outside-only', virtualConsole:vc});
    const w = dom.window;
    const estado = {tempo:1000, relogios:new Map(), id:0, pedidos:[], falas:[], fontes:[], terminou:0, falhou:0};
    w.Date.now = () => estado.tempo;
    w.setTimeout = (fn, ms) => {const id = ++estado.id; estado.relogios.set(id, {fn, quando:estado.tempo + ms}); return id;};
    w.clearTimeout = id => estado.relogios.delete(id);
    w.HTMLMediaElement.prototype.pause = () => {};
    w.SpeechSynthesisUtterance = function(text) {this.text = text;};
    if (!opcoes.semVozAparelho) w.speechSynthesis = {
      cancel() {}, getVoices:() => [{lang:'pt-BR', name:'Voz de teste'}],
      speak(frase) {estado.falas.push(frase);}
    };
    w.AudioContext = class {
      constructor() {this.state = 'running'; this.destination = {};}
      resume() {return opcoes.retomada?.promise || Promise.resolve();}
      decodeAudioData() {return opcoes.decodificacao?.promise || Promise.resolve({length:100, numberOfChannels:1});}
      createBufferSource() {
        const fonte = {iniciou:false, parou:false, connect() {}, disconnect() {}, start() {this.iniciou = true;}, stop() {this.parou = true;}};
        estado.fontes.push(fonte);
        return fonte;
      }
    };
    w.fetch = (url, args) => {const resposta = pendente(); estado.pedidos.push({url, args, resposta}); return resposta.promise;};
    vm.runInContext(script, dom.getInternalVMContext());
    const botao = w.document.querySelector('[data-narrador=francisca]');
    const falar = texto => w.falar(texto, botao, () => estado.terminou++, () => estado.falhou++);
    const responder = async (indice = 0) => {
      estado.pedidos[indice].resposta.resolve({ok:true, arrayBuffer:async () => new w.ArrayBuffer(16)});
      await esvaziar();
    };
    const avancar = async ms => {
      estado.tempo += ms;
      for (const [id, evento] of [...estado.relogios]) {
        if (evento.quando <= estado.tempo) {estado.relogios.delete(id); evento.fn();}
      }
      await esvaziar();
    };
    const fechar = () => {w.pararVoz(); assert.deepEqual(erros, []); dom.window.close();};
    return {w, estado, falar, responder, avancar, fechar};
  }

  const a = abrir();
  a.falar('Qual é o nome do seu trabalho?'); await esvaziar();
  assert.equal(a.estado.pedidos.length, 1);
  await a.avancar(2499); assert.equal(a.estado.falas.length, 0);
  await a.avancar(1); assert.equal(a.estado.falas.length, 1);
  assert.ok(a.estado.pedidos[0].args.signal.aborted);
  assert.equal(a.estado.terminou, 0, 'O microfone só deve abrir após terminar a voz alternativa');
  await a.responder();
  assert.equal(a.estado.fontes.length, 0, 'A resposta online atrasada não pode falar sobre a voz do aparelho');
  a.estado.falas[0].onend(); a.estado.falas[0].onend();
  assert.equal(a.estado.terminou, 1);
  a.falar('Que serviço você faz?'); await esvaziar();
  assert.equal(a.estado.pedidos.length, 1, 'A próxima pergunta não deve esperar o mesmo serviço lento');
  assert.equal(a.estado.falas.length, 2);
  a.estado.falas[1].onend();
  await a.avancar(30000);
  a.falar('Em qual comunidade?'); await esvaziar();
  assert.equal(a.estado.pedidos.length, 2, 'Após a pausa, a voz online pode ser tentada novamente');
  a.fechar();
  console.log('OK narração: alternativa após 2,5 s, áudio atrasado ignorado, conclusão única e pausa de 30 s.');

  const b = abrir();
  b.falar('Primeira pergunta'); await esvaziar();
  b.falar('Segunda pergunta'); await esvaziar();
  assert.ok(b.estado.pedidos[0].args.signal.aborted);
  await b.responder(0); assert.equal(b.estado.fontes.length, 0);
  await b.responder(1); assert.equal(b.estado.fontes.length, 1);
  assert.ok(b.estado.fontes[0].iniciou);
  b.estado.fontes[0].onended(); assert.equal(b.estado.terminou, 1);
  b.falar('Segunda pergunta'); await esvaziar();
  assert.equal(b.estado.pedidos.length, 2, 'Repetir deve usar o áudio já preparado');
  assert.equal(b.estado.fontes.length, 2);
  b.estado.fontes[1].onended();
  b.w.escolherNarrador('antonio');
  b.falar('Segunda pergunta'); await esvaziar();
  assert.equal(b.estado.pedidos.length, 3, 'Cada narrador deve ter seu próprio áudio');
  assert.equal(b.estado.pedidos[2].args.body.get('narrador'), 'antonio');
  b.fechar();
  console.log('OK narração: cancelamento descarta respostas antigas e cache separa os narradores.');

  for (const parte of ['retomada', 'decodificacao']) {
    const etapa = pendente(), c = abrir({[parte]:etapa});
    c.falar('Uma orientação'); await esvaziar();
    if (parte === 'decodificacao') await c.responder();
    await c.avancar(2500);
    assert.equal(c.estado.falas.length, 1, `${parte} travada também deve usar a alternativa`);
    etapa.resolve({length:100, numberOfChannels:1}); await esvaziar();
    assert.equal(c.estado.fontes.length, 0);
    c.fechar();
  }
  console.log('OK narração: retomada e decodificação demoradas respeitam o mesmo prazo.');

  const d = abrir();
  d.w.document.querySelector('[data-narrador=antonio]').click(); await esvaziar();
  assert.equal(d.estado.pedidos[0].url, '/static/vozes/amostra-antonio.mp3');
  assert.equal(d.estado.pedidos[0].args.method, undefined, 'A amostra local não solicita síntese ao serviço');
  await d.responder(); assert.ok(d.estado.fontes[0].iniciou);
  d.w.escolherNarrador('aparelho'); d.falar('Orientação imediata');
  assert.equal(d.estado.falas.length, 1); assert.equal(d.estado.pedidos.length, 1);
  d.fechar();
  const e = abrir({semVozAparelho:true});
  e.falar('Orientação indisponível'); await esvaziar(); await e.avancar(2500);
  assert.equal(e.estado.terminou, 0); assert.equal(e.estado.falhou, 1);
  await e.responder(); assert.equal(e.estado.fontes.length, 0);
  e.fechar();
  console.log('OK narração: amostras locais, voz do aparelho imediata e falha sem abrir o microfone.');
})().catch(erro => {console.error(erro); process.exitCode = 1;});
