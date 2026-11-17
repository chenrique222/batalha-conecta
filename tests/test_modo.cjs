/* Regressões do switch: preferência, anúncio, armazenamento indisponível e outras abas. */
const { JSDOM } = require('jsdom');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const raiz = path.resolve(__dirname, '..');
const base = process.env.BATALHA_TESTE_URL || 'http://127.0.0.1:5005';

(async () => {
  const html = await (await fetch(base + '/')).text();
  function abrir(preferencia, bloquear = false) {
    const dom = new JSDOM(html, { url: base, runScripts: 'outside-only' });
    const w = dom.window;
    const falas = [], modos = [];
    if (preferencia !== undefined) w.localStorage.setItem('batalha-modo', preferencia);
    if (bloquear) Object.defineProperty(w, 'localStorage', { get() { throw new Error('Armazenamento bloqueado'); } });
    w.SpeechSynthesisUtterance = function (text) { this.text = text; };
    w.speechSynthesis = { cancel() {}, getVoices: () => [], speak(frase) { falas.push(frase.text); } };
    w.document.addEventListener('modoalterado', e => modos.push(e.detail));
    for (const arquivo of ['modo.js', 'voz-audio.js', 'acessibilidade.js']) {
      vm.runInContext(fs.readFileSync(path.join(raiz, 'static', arquivo), 'utf8'), dom.getInternalVMContext());
    }
    return { dom, w, falas, modos, botao: w.document.querySelector('#alternar-modo') };
  }
  const a = abrir();
  assert.equal(a.botao.tagName, 'BUTTON');
  assert.equal(a.botao.getAttribute('role'), 'switch');
  assert.equal(a.botao.getAttribute('aria-checked'), 'false');
  a.botao.click();
  assert.equal(a.w.document.documentElement.dataset.modo, 'icones');
  assert.equal(a.botao.getAttribute('aria-checked'), 'true');
  assert.equal(a.botao.hasAttribute('aria-pressed'), false);
  // A segunda troca acontece enquanto a primeira narração ainda está em andamento.
  a.botao.click();
  assert.equal(a.botao.getAttribute('aria-checked'), 'false');
  assert.equal(a.falas.at(-1), 'Modo com textos ativado.');
  assert.equal(a.botao.hasAttribute('aria-pressed'), false);
  assert.deepEqual(a.modos, ['texto', 'icones', 'texto']);
  a.botao.click();
  const b = abrir(a.w.localStorage.getItem('batalha-modo'));
  assert.equal(b.botao.getAttribute('aria-checked'), 'true');
  b.w.dispatchEvent(new b.w.StorageEvent('storage', { key: 'batalha-modo', newValue: 'texto' }));
  assert.equal(b.w.document.documentElement.dataset.modo, 'texto');
  assert.equal(b.botao.getAttribute('aria-checked'), 'false');
  assert.equal(b.falas.length, 0, 'Outra aba não deve iniciar narração automaticamente');
  const c = abrir('valor-invalido');
  assert.equal(c.botao.getAttribute('aria-checked'), 'false');
  const d = abrir(undefined, true);
  d.botao.click();
  assert.equal(d.w.document.documentElement.dataset.modo, 'icones');
  assert.equal(d.botao.getAttribute('aria-checked'), 'true');
  for (const ambiente of [a, b, c, d]) ambiente.dom.window.close();
  console.log('OK switch: alternância rápida, anúncio correto, preferência recuperada, sincronização entre abas e armazenamento bloqueado.');
})().catch(erro => { console.error(erro); process.exitCode = 1; });
