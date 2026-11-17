/* Teste do DOM com navegador e microfone simulados; publica no Flask de teste. */
const {JSDOM, VirtualConsole} = require('jsdom');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const raiz = path.resolve(__dirname, '..');
const base = process.env.BATALHA_TESTE_URL || 'http://127.0.0.1:5005';
const esperar = () => new Promise(r => setTimeout(r, 20));
async function blobBytes(w, blob) {
  return new Promise((resolve, reject) => { const leitor = new w.FileReader(); leitor.onload=()=>resolve(new Uint8Array(leitor.result)); leitor.onerror=reject; leitor.readAsArrayBuffer(blob); });
}
async function ambiente(url='/cadastro', modo='texto', cookieInicial='') {
  const resposta = await fetch(base+url,{headers:cookieInicial?{Cookie:cookieInicial}:{}});
  let cookie=resposta.headers.get('set-cookie')?.split(';')[0] || cookieInicial;
  const falhas=[], virtual=new VirtualConsole();
  virtual.on('jsdomError',e=>{if(!e.message.startsWith('Not implemented: navigation'))falhas.push(e.message)});
  const dom=new JSDOM(await resposta.text(),{url:base+url,runScripts:'outside-only',pretendToBeVisual:true,virtualConsole:virtual});
  const w=dom.window,d=w.document;
  const estado={posts:[],falas:[],falhar:false,microfones:[],relogios:[],simularPermissaoNegada:false,tempo:Date.now()};
  w.localStorage.setItem('batalha-modo',modo);
  Object.defineProperty(w,'isSecureContext',{value:true});
  w.matchMedia=()=>({matches:false});
  w.HTMLMediaElement.prototype.pause=()=>{};
  w.URL.createObjectURL=()=>`blob:http://127.0.0.1/foto-${Math.random()}`;
  w.URL.revokeObjectURL=()=>{};
  w.SpeechSynthesisUtterance=function(texto){this.text=texto};
  w.speechSynthesis={getVoices:()=>[],cancel(){},speak(frase){estado.falas.push(frase.text);setTimeout(()=>frase.onend?.(),0)}};
  w.HTMLDialogElement.prototype.showModal=function(){this.open=true};
  w.HTMLDialogElement.prototype.close=function(){this.open=false};
  w.Date.now=()=>estado.tempo;
  w.setInterval=fn=>{estado.relogios.push(fn);return estado.relogios.length-1};
  w.clearInterval=id=>{estado.relogios[id]=null};
  w.navigator.mediaDevices={getUserMedia:async()=>{
    if(estado.simularPermissaoNegada)throw new Error('NotAllowedError');
    const track={parada:false,stop(){this.parada=true},addEventListener(){}};
    estado.microfones.push(track);
    return {getTracks:()=>[track],getAudioTracks:()=>[track]};
  }};
  class Gravador {
    constructor(){this.state='inactive';this.mimeType='audio/webm'}
    static isTypeSupported(tipo){return tipo.startsWith('audio/webm')}
    start(){this.state='recording'}
    stop(){this.state='inactive';setTimeout(()=>{this.ondataavailable?.({data:new w.Blob([new Uint8Array([26,69,223,163,1,2,3,4])],{type:this.mimeType})});this.onstop?.()},0)}
  }
  w.MediaRecorder=Gravador;
  w.fetch=async(url,opcoes)=>{
    if(estado.falhar)throw new Error('Failed to fetch');
    const dados=new FormData();
    for(const [k,v] of opcoes.body.entries()) {
      if(v instanceof w.Blob)dados.append(k,new Blob([await blobBytes(w,v)],{type:v.type}),v.name === undefined ? 'arquivo' : v.name);
      else dados.append(k,v);
    }
    const r=await fetch(new URL(url,base),{method:opcoes.method,body:dados,headers:{...opcoes.headers,Cookie:cookie}});
    cookie=r.headers.get('set-cookie')?.split(';')[0] || cookie;
    const json=await r.clone().json();
    estado.posts.push({url:String(url),status:r.status,json,dados});
    return r;
  };
  for(const arquivo of ['modo.js','voz-audio.js','galeria.js','app.js','acessibilidade.js','voz-logica.js','escuta.js','cadastro-voz.js','avaliacoes.js'])vm.runInContext(fs.readFileSync(path.join(raiz,'static',arquivo),'utf8'),dom.getInternalVMContext());
  const click=async sel=>{d.querySelector(sel).click();await esperar()};
  return {w,d,dom,estado,click,cookie:()=>cookie,falhas};
}
function selecionar(a,selector,arquivos) {
  const input=a.d.querySelector(selector);
  Object.defineProperty(input,'files',{configurable:true,value:arquivos});
  input.dispatchEvent(new a.w.Event('change',{bubbles:true}));
}
async function aguardarPost(a) {
  for(let i=0;i<40&&!a.estado.posts.length;i++)await esperar();
  assert.ok(a.estado.posts.length,'O formulário não chegou ao servidor');
  assert.equal(a.estado.posts.at(-1).status,201,JSON.stringify(a.estado.posts.at(-1).json));
}
(async()=>{
  const a=await ambiente();
  const png=Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aUv8AAAAASUVORK5CYII=','base64');
  const fotos=Array.from({length:5},(_,i)=>new a.w.File([png],`foto${i}.png`,{type:'image/png'}));
  selecionar(a,'#galeria-cadastro-arquivo',fotos);
  assert.equal(a.d.querySelectorAll('[data-previas-fotos] img').length,5);
  selecionar(a,'#galeria-cadastro-arquivo',[fotos[0]]);
  assert.equal(a.d.querySelectorAll('[data-previas-fotos] img').length,5);
  assert.ok(a.d.querySelector('[data-erros-fotos]').textContent.includes('cinco'));
  await a.click('.remover-foto');
  assert.equal(a.d.querySelectorAll('[data-previas-fotos] img').length,4);
  selecionar(a,'#galeria-cadastro-arquivo',[fotos[0]]);
  await a.click('[name=categoria][value=servicos]'); await a.click('#proximo-passo');
  a.d.querySelector('#nome').value='Galeria da interface'; a.d.querySelector('#descricao').value='Trabalho demonstrativo';
  await a.click('#proximo-passo'); a.d.querySelector('#comunidade').value='Centro';
  await a.click('#proximo-passo'); assert.equal(a.d.querySelectorAll('#resumo-cadastro img').length,5);
  await a.click('[name=consentimento]'); await a.click('#publicar'); await aguardarPost(a);
  const perfil=a.estado.posts.at(-1).json.url;
  const cookie=a.cookie();
  assert.deepEqual(a.falhas,[]);a.dom.window.close();
  console.log('OK galeria: seleção cumulativa, sexta recusada, remoção, resumo e publicação de cinco fotos.');

  const b=await ambiente(perfil,'icones',cookie);
  assert.equal(b.d.querySelectorAll('[data-ampliar-foto]').length,5);
  await b.click('[data-ampliar-foto]');assert.ok(b.d.querySelector('#foto-ampliada').open);
  await b.click('[data-foto-proxima]');assert.equal(b.d.querySelector('[data-posicao-foto]').textContent,'2 / 5');
  await b.click('[data-fechar-foto]');
  await b.click('[name=nota][value="5"]');
  await b.click('#avaliacao-gravar');
  assert.equal(b.d.querySelector('#avaliacao-parar').hidden,false);
  assert.equal(b.d.querySelector('#avaliacao-publicar').disabled,true);
  assert.equal(b.estado.posts.length,0);
  b.estado.tempo+=90000;b.estado.relogios.filter(Boolean).forEach(fn=>fn());
  assert.equal(b.d.querySelector('#avaliacao-parar').hidden,false,'Não deve parar antes de dois minutos');
  await b.click('#avaliacao-parar');
  assert.equal(b.d.querySelector('#avaliacao-previa').hidden,false);
  assert.equal(b.d.querySelector('#avaliacao-publicar').disabled,false);
  assert.ok(b.estado.microfones.every(m=>m.parada));
  assert.equal(b.estado.posts.length,0,'Parar não publica automaticamente');
  b.estado.falhar=true;await b.click('#avaliacao-publicar');
  assert.equal(b.d.querySelector('#avaliacao-previa').hidden,false);assert.equal(b.d.querySelector('#avaliacao-publicar').disabled,false);
  b.estado.falhar=false;await b.click('#avaliacao-publicar');await aguardarPost(b);
  assert.equal(b.estado.posts.at(-1).dados.get('consentimento'),'sim');
  assert.ok(b.estado.posts.at(-1).dados.get('audio').size);
  assert.deepEqual(b.falhas,[]);b.dom.window.close();
  console.log('OK avaliação: gravar com pausas, parar, conferir, falha de rede preserva áudio e publicação autorizada.');

  const c=await ambiente(perfil);
  assert.equal(c.d.querySelectorAll('.avaliacao-card audio').length,1);
  assert.ok(c.d.querySelector('.media-avaliacoes').textContent.includes('5.0'));
  c.estado.simularPermissaoNegada=true;await c.click('#avaliacao-gravar');
  assert.ok(c.d.querySelector('#avaliacao-erro').textContent.includes('microfone'));
  assert.equal(c.d.querySelector('#avaliacao-arquivo').disabled,false);
  c.estado.simularPermissaoNegada=false;await c.click('#avaliacao-gravar');
  c.estado.tempo+=120000;c.estado.relogios.filter(Boolean).forEach(fn=>fn());await esperar();
  assert.equal(c.d.querySelector('#avaliacao-parar').hidden,true);assert.equal(c.d.querySelector('#avaliacao-previa').hidden,false);
  await c.click('#avaliacao-refazer');assert.equal(c.d.querySelector('#avaliacao-previa').hidden,true);
  assert.ok(c.estado.microfones.every(m=>m.parada));assert.deepEqual(c.falhas,[]);c.dom.window.close();
  console.log('OK avaliação: outro visitante ouve, permissão negada, limite de dois minutos e descarte.');

  const d=await ambiente('/cadastro','icones');
  assert.ok(d.d.querySelector('#voz-fotos #galeria-cadastro'));
  selecionar(d,'#galeria-cadastro-arquivo',[new d.w.File([png],'voz-foto.png',{type:'image/png'})]);
  await d.click('#alternar-modo');assert.ok(d.d.querySelector('#fotos-manuais #galeria-cadastro'));
  assert.equal(d.w.galeriaCadastro.itens.length,1);
  await d.click('#alternar-modo');assert.equal(d.w.galeriaCadastro.itens.length,1);
  await d.click('#voz-cancelar');assert.equal(d.w.galeriaCadastro.itens.length,0);
  assert.deepEqual(d.falhas,[]);d.dom.window.close();
  console.log('OK fotos nos dois modos: troca preserva seleção; cancelar conversa apaga fotos do rascunho.');

  const e=await ambiente('/ajuda');
  await e.click('[data-narrador=antonio]');assert.equal(e.w.localStorage.getItem('batalha-narrador'),'antonio');
  await e.click('[data-narrador=aparelho]');assert.equal(e.w.localStorage.getItem('batalha-narrador'),'aparelho');
  assert.ok(e.estado.falas.length);assert.deepEqual(e.falhas,[]);e.dom.window.close();
  console.log('OK escolha de narração: preferência salva e voz do aparelho disponível.');
})().catch(erro=>{console.error(erro);process.exitCode=1;});
