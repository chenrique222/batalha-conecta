/* Conversa completa com o assistente de IA simulado (tests/simulacao_ia.py).
   O navegador é o jsdom; o servidor Flask e o banco temporário são reais. */
const {JSDOM, VirtualConsole} = require('jsdom');
const fs = require('node:fs');
const assert = require('node:assert/strict');
const path = require('node:path');
const raiz = path.resolve(__dirname, '..');
const base = process.env.BATALHA_TESTE_URL_IA;
const esperar = (ms = 15) => new Promise(r => setTimeout(r, ms));
async function ate(condicao, descricao) {
  for (let i = 0; i < 300; i++) { if (condicao()) return; await esperar(); }
  assert.fail(`Tempo esgotado: ${descricao}`);
}
async function ambiente({gravador = true, reconhecimento = false, permissao = true} = {}) {
  const pagina = await fetch(base + '/cadastro');
  const cookie = pagina.headers.get('set-cookie').split(';')[0];
  const falhas = [];
  const virtual = new VirtualConsole(); virtual.on('jsdomError', e => { if (!e.message.startsWith('Not implemented: navigation')) falhas.push(e.message); });
  const dom = new JSDOM(await pagina.text(), {url:base + '/cadastro', runScripts:'outside-only', pretendToBeVisual:true, virtualConsole:virtual});
  const w = dom.window, d = w.document;
  const s = {gravando:null, navegador:null, microfones:0, soltos:0, falas:[], pedidos:{}, fala:'', avanco:0};
  w.localStorage.setItem('batalha-modo', 'icones');
  w.localStorage.setItem('batalha-narrador', 'aparelho');
  Object.defineProperty(w, 'isSecureContext', {value:true});
  w.matchMedia = () => ({matches:false});
  w.HTMLMediaElement.prototype.pause = () => {};
  // Cada resposta "dura" dois segundos, sem o teste precisar esperar.
  const agoraReal = w.Date.now.bind(w.Date);
  w.Date.now = () => agoraReal() + s.avanco;
  w.SpeechSynthesisUtterance = function (texto) { this.text = texto; };
  w.speechSynthesis = {getVoices:() => [], cancel() { clearTimeout(s.timerFala); },
    speak(frase) { s.falas.push(frase.text); s.timerFala = setTimeout(() => frase.onend?.(), 1); }};
  const setReal = w.setTimeout.bind(w);
  w.setTimeout = (fn, tempo) => setReal(fn, tempo === 150 ? 1 : tempo);
  const no = () => ({connect:() => no(), disconnect() {}, start() {}, stop() {}, frequency:{}, gain:{}});
  w.AudioContext = class {
    constructor() { this.state = 'running'; this.currentTime = 0; this.destination = {}; }
    resume() { return Promise.resolve(); } close() { return Promise.resolve(); }
    createOscillator() { return no(); } createGain() { return no(); } createMediaStreamSource() { return no(); }
    createAnalyser() { return {fftSize:1024, getFloatTimeDomainData(amostras) { amostras.fill(0.001); }}; }
  };
  if (gravador) {
    Object.defineProperty(w.navigator, 'mediaDevices', {value:{getUserMedia() {
      if (!permissao) return Promise.reject(Object.assign(new Error('negado'), {name:'NotAllowedError'}));
      s.microfones++;
      return Promise.resolve({getTracks:() => [{stop() { s.soltos++; }}]});
    }}});
    w.MediaRecorder = class {
      static isTypeSupported(tipo) { return tipo.startsWith('audio/ogg'); }
      constructor() { this.state = 'inactive'; this.mimeType = 'audio/ogg;codecs=opus'; }
      start() { this.state = 'recording'; s.gravando = this; }
      stop() {
        this.state = 'inactive'; if (s.gravando === this) s.gravando = null;
        // A "gravação" leva a fala escrita; o servidor simulado a devolve como texto.
        this.ondataavailable?.({data:new w.Blob(['OggS' + s.fala.padEnd(220)], {type:'audio/ogg'})}); this.onstop?.();
      }
    };
  }
  if (reconhecimento) w.SpeechRecognition = class {
    start() { s.navegador = this; this.onstart?.(); }
    stop() { if (s.navegador === this) s.navegador = null; setTimeout(() => this.onend?.(), 0); }
    abort() { if (s.navegador === this) s.navegador = null; }
  };
  w.fetch = async (url, opcoes) => {
    const rota = new URL(url, base).pathname;
    s.pedidos[rota] = (s.pedidos[rota] || 0) + 1;
    const dados = new FormData();
    for (const [k, v] of opcoes.body.entries()) {
      if (v instanceof w.Blob) {
        const bytes = await new Promise(resolve => { const leitor = new w.FileReader(); leitor.onload = () => resolve(new Uint8Array(leitor.result)); leitor.readAsArrayBuffer(v); });
        dados.append(k, new Blob([bytes], {type:v.type}), v.name === undefined ? 'arquivo' : v.name);
      } else dados.append(k, v);
    }
    return fetch(new URL(url, base), {method:opcoes.method, headers:{...opcoes.headers, Cookie:cookie}, body:dados});
  };
  for (const arquivo of ['modo.js', 'voz-audio.js', 'galeria.js', 'app.js', 'acessibilidade.js', 'voz-logica.js', 'escuta.js', 'escuta-ia.js', 'cadastro-voz.js'])
    require('node:vm').runInContext(fs.readFileSync(path.join(raiz, 'static', arquivo), 'utf8'), dom.getInternalVMContext());
  const a = {w, d, dom, s, falhas, status:() => d.querySelector('#voz-status').textContent, ultima:() => s.falas.at(-1) || ''};
  a.click = async seletor => { d.querySelector(seletor).click(); await esperar(); };
  a.ouvindo = () => ate(() => s.gravando, `abrir o microfone; última fala: ${a.ultima()}`);
  // Fala, toca em Terminei e espera a conversa reagir com uma nova fala do aplicativo.
  a.responder = async (texto, continuaOuvindo = true) => {
    await a.ouvindo();
    const falas = s.falas.length;
    s.fala = texto; s.avanco += 2000;
    d.querySelector('#voz-terminar').click();
    await ate(() => s.falas.length > falas || a.status().includes('Publicando') || a.status().includes('foi publicado'), `reação a "${texto}"`);
    if (continuaOuvindo) await a.ouvindo();
  };
  return a;
}
const entendidos = a => a.s.pedidos['/api/ia/entender'] || 0;
const ouvidos = a => a.s.pedidos['/api/ia/transcrever'] || 0;

(async () => {
  const a = await ambiente();
  assert.equal(a.d.querySelector('#cadastro-voz').dataset.ia, '1');
  assert.equal(a.d.querySelector('#voz-microfone').disabled, false, 'Sem reconhecimento do navegador, a IA basta');
  await a.click('#voz-microfone');
  assert.ok(a.s.falas[0].includes('inteligência artificial'), 'A pessoa é avisada de que a voz vai para um serviço de IA');
  await a.responder('Meu nome é Dona Rosa.');
  assert.ok(a.ultima().startsWith('Anotei: Dona Rosa.'), a.ultima());
  assert.ok(a.ultima().includes('atividade'), 'Confirmação rápida: repete e já faz a próxima pergunta. ' + a.ultima());
  await a.responder('Não, tá errado.');
  assert.ok(a.ultima().includes('nome'), 'Dizer não logo depois volta para a pergunta anterior: ' + a.ultima());
  await a.responder('Meu nome é Dona Rosa.');
  assert.ok(a.ultima().startsWith('Anotei: Dona Rosa.'), a.ultima());
  await a.responder('Eu vendo beiju e goma na feira.');
  assert.ok(a.ultima().startsWith('Anotei: Farinha e derivados.'), a.ultima());
  await a.responder('Faço beiju e goma fresquinha por encomenda.');
  await a.responder('O que é comunidade?');
  assert.ok(a.ultima().includes('lugar onde você trabalha'), 'A IA explica com as próprias palavras e volta a ouvir');
  const antes = entendidos(a);
  await a.responder('Centro.');
  assert.ok(a.ultima().startsWith('Anotei: Centro.'), a.ultima());
  await a.responder('Meu zap é 86 99981-2345.');
  assert.ok(a.ultima().startsWith('Anotei: 8, 6, 9, 9, 9, 8, 1, 2, 3, 4, 5.'), a.ultima());
  assert.ok(a.ultima().includes('Para autorizar'), 'Depois da última resposta, vem a revisão completa');
  assert.equal(a.d.querySelector('#voz-publicar').hidden, false);
  await a.responder('Não quero publicar ainda.');
  assert.equal(a.s.pedidos['/cadastro'] || 0, 0, 'Negação nunca publica, mesmo se o modelo errar');
  assert.ok(a.ultima().startsWith('Para autorizar'), a.ultima());
  await a.responder('Quero mudar o bairro.');
  assert.ok(a.ultima().includes('bairro ou comunidade'), a.ultima());
  await a.responder('Bairro São José.');
  assert.equal(a.d.querySelector('#comunidade').value, 'Bairro São José');
  await a.responder('Pode publicar sim, pode publicar.', false);
  await ate(() => a.status().includes('foi publicado'), 'publicação');
  assert.equal(a.s.pedidos['/cadastro'], 1);
  const perfis = await (await fetch(base + '/api/profissionais?busca=Dona%20Rosa')).json();
  assert.equal(perfis.length, 1);
  assert.deepEqual([perfis[0].categoria, perfis[0].comunidade, perfis[0].telefone, perfis[0].descricao], ['rural', 'Bairro São José', '86999812345', 'Faço beiju e goma fresquinha por encomenda.']);
  assert.equal(a.s.microfones, a.s.soltos, 'Todo microfone aberto foi solto');
  assert.deepEqual(a.falhas, []); a.dom.window.close();
  console.log('OK IA: conversa natural, explicação de dúvida, telefone conferido, negação não publica, correção e publicação.');

  const b = await ambiente(); await b.click('#voz-microfone');
  await b.responder('inventar um nome');
  assert.ok(b.ultima().startsWith('Não entendi'), 'Valor que a pessoa não disse é recusado');
  assert.equal(b.d.querySelector('#voz-confirmacoes').hidden, true);
  await b.responder('falhar Oficina do Zé');
  assert.ok(b.ultima().startsWith('Anotei: falhar Oficina do Zé.'), 'Se a IA falha ao entender, valem as regras fixas: ' + b.ultima());
  const pedidos = entendidos(b);
  await b.responder('Faço farinha de mandioca e goma.');
  assert.equal(entendidos(b), pedidos, 'Depois da falha, a IA descansa um minuto');
  assert.ok(b.ultima().startsWith('Anotei: Farinha e derivados.'), b.ultima());
  b.s.avanco += 61000;
  await b.responder('Faço beiju por encomenda.');
  assert.equal(entendidos(b), pedidos + 1, 'Passado o descanso, a IA volta');
  assert.ok(b.ultima().includes('comunidade'), b.ultima());
  await b.ouvindo(); await b.click('#voz-microfone');
  assert.equal(b.s.gravando, null); assert.equal(b.s.microfones, b.s.soltos, 'Pausar solta o microfone');
  const enviados = ouvidos(b); await esperar(60);
  assert.equal(ouvidos(b), enviados, 'Pausar não envia a gravação interrompida');
  assert.deepEqual(b.falhas, []); b.dom.window.close();
  console.log('OK IA: invenção recusada, falha ao entender cai nas regras fixas, descanso de um minuto e pausa sem envio.');

  const c = await ambiente({reconhecimento:true}); await c.click('#voz-microfone');
  await c.responder('sem escuta agora', false);
  assert.ok(c.ultima().includes('reconhecimento do navegador'), c.ultima());
  await ate(() => c.s.navegador, 'reconhecimento do navegador assumir');
  assert.equal(c.s.gravando, null); assert.equal(c.s.microfones, c.s.soltos);
  const resultado = [{transcript:'Meu nome é Seu Chico'}]; resultado.isFinal = true;
  c.s.navegador.onresult({resultIndex:0, results:[resultado]});
  const falas = c.s.falas.length; c.d.querySelector('#voz-terminar').click();
  await ate(() => c.s.falas.length > falas, 'resposta pelo navegador');
  assert.ok(c.ultima().startsWith('Anotei: Seu Chico.'), 'O texto do navegador também é entendido pela IA');
  c.dom.window.close();
  const e = await ambiente(); await e.click('#voz-microfone');
  await e.responder('sem escuta agora', false);
  assert.ok(e.status().includes('não respondeu')); assert.equal(e.d.querySelector('#voz-indisponivel').hidden, false);
  assert.equal(e.s.gravando, null); assert.equal(e.d.querySelector('#voz-microfone').getAttribute('aria-pressed'), 'false');
  e.dom.window.close();
  console.log('OK IA: serviço de escuta fora do ar passa para o navegador ou pausa com explicação.');

  const f = await ambiente({permissao:false}); await f.click('#voz-microfone');
  await ate(() => f.status().includes('bloqueado'), 'aviso de permissão');
  assert.equal(f.d.querySelector('#voz-indisponivel').hidden, false); f.dom.window.close();
  const g = await ambiente({gravador:false});
  assert.equal(g.d.querySelector('#voz-microfone').disabled, true);
  assert.equal(g.d.querySelector('#voz-indisponivel').hidden, false); g.dom.window.close();
  const h = await ambiente(); await h.click('#voz-microfone');
  await h.responder('silêncio', false);
  assert.ok(h.ultima().includes('Pode falar agora'), 'Na primeira vez sem fala, pergunta de novo sem pausar: ' + h.ultima());
  await h.ouvindo();
  assert.equal(h.s.microfones, 1, 'O microfone da conversa é aberto uma vez só');
  await h.responder('silêncio', false);
  assert.ok(h.status().includes('Não ouvi'), h.status());
  assert.equal(h.d.querySelector('#voz-microfone').getAttribute('aria-pressed'), 'false', 'Na segunda vez, a conversa pausa');
  assert.equal(h.s.microfones, h.s.soltos, 'Ao pausar, o microfone é solto');
  h.dom.window.close();
  console.log('OK IA: permissão negada, navegador sem gravação e gravação sem fala são explicados.');
})().catch(erro => { console.error(erro); process.exitCode = 1; });
