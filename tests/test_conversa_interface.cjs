const {JSDOM, VirtualConsole} = require('jsdom');
const fs = require('node:fs');
const assert = require('node:assert/strict');
const path = require('node:path');
const raiz = path.resolve(__dirname, '..');
const base = process.env.BATALHA_TESTE_URL || 'http://127.0.0.1:5005';
const esperar = () => new Promise(r => setTimeout(r, 25));
async function ambiente({voz=true, modo='icones'}={}) {
  const pagina = await fetch(base+'/cadastro');
  const cookie = pagina.headers.get('set-cookie').split(';')[0];
  const falhas=[];
  const virtual = new VirtualConsole(); virtual.on('jsdomError', e => {if(!e.message.startsWith('Not implemented: navigation')) falhas.push(e.message);});
  const dom = new JSDOM(await pagina.text(), {url:base+'/cadastro',runScripts:'outside-only',pretendToBeVisual:true,virtualConsole:virtual});
  const w=dom.window; const d=w.document;
  const situacao = {atual:null, postagens:0, falas:[], timer:null, falharEnvio:false};
  w.localStorage.setItem('batalha-modo',modo);
  Object.defineProperty(w, 'isSecureContext', {value:true});
  w.matchMedia=()=>({matches:false});
  w.HTMLMediaElement.prototype.pause=()=>{};
  w.URL.createObjectURL=()=>`blob:http://localhost/foto-${Math.random()}`;
  w.URL.revokeObjectURL=()=>{};
  w.SpeechSynthesisUtterance=function(texto){this.text=texto;};
  w.speechSynthesis={getVoices:()=>[],speaking:false,
    cancel(){ clearTimeout(situacao.timer); this.speaking=false; },
    speak(frase){ this.speaking=true; situacao.falas.push(frase.text); situacao.timer=setTimeout(()=>{this.speaking=false; frase.onend?.();},1); }};
  const setReal=w.setTimeout.bind(w);
  w.setTimeout=(fn,tempo)=>setReal(fn,tempo===450?1:tempo);
  class MicrofoneFalso {
    start(){situacao.atual=this; this.onstart?.();}
    stop(){if(situacao.atual===this)situacao.atual=null;setTimeout(()=>this.onend?.(),0);}
    abort(){if(situacao.atual===this)situacao.atual=null;}
  }
  if(voz) w.SpeechRecognition=MicrofoneFalso;
  w.fetch=async(url,opcoes)=>{
    situacao.postagens++;
    if(situacao.falharEnvio)throw new Error('Failed to fetch');
    const dados=new FormData();
    for(const [k,v] of opcoes.body.entries()) {
      if(v instanceof w.Blob) {
        const bytes=await new Promise(resolve=>{const leitor=new w.FileReader();leitor.onload=()=>resolve(new Uint8Array(leitor.result));leitor.readAsArrayBuffer(v)});
        dados.append(k,new Blob([bytes],{type:v.type}),v.name === undefined ? 'arquivo' : v.name);
      } else dados.append(k,v);
    }
    return fetch(url,{method:opcoes.method,headers:{...opcoes.headers,Cookie:cookie},body:dados});
  };
  for(const arquivo of ['modo.js','voz-audio.js','galeria.js','app.js','acessibilidade.js','voz-logica.js','escuta.js','cadastro-voz.js']) require('node:vm').runInContext(fs.readFileSync(path.join(raiz,'static',arquivo),'utf8'),dom.getInternalVMContext());
  const click=async seletor=>{d.querySelector(seletor).click();await esperar();};
  const responder=async texto=>{assert.ok(situacao.atual,`Não estava escutando: ${texto}; última fala: ${situacao.falas.at(-1)}`);const mic=situacao.atual; const resultado=[{transcript:texto}]; resultado.isFinal=true; mic.onresult({resultIndex:0,results:[resultado]}); d.querySelector('#voz-terminar').click(); await esperar();};
  return {w,d,dom,situacao,click,responder,falhas};
}
async function preencher(a, nome) {
  await a.click('#voz-microfone');
  for(const resposta of [nome,'comidas','Faço bolos por encomenda','Centro','pular']) { await a.responder(resposta); assert.equal(a.d.querySelector('#voz-confirmacoes').hidden,false); await a.responder('sim'); }
  assert.equal(a.d.querySelector('#voz-publicar').hidden,false);
  assert.equal(a.situacao.postagens,0,'Não publicar antes da autorização final');
}
(async()=>{
  const a=await ambiente();
  assert.equal(a.d.documentElement.dataset.modo,'icones');
  assert.equal(a.d.querySelector('#form-cadastro').hidden,true);
  assert.equal(a.d.querySelector('#alternar-modo').getAttribute('aria-checked'),'true');
  await preencher(a,'Perfil simulado sem email');
  await a.responder('sim'); assert.equal(a.situacao.postagens,0);
  await a.responder('não publicar'); assert.equal(a.situacao.postagens,0);
  await a.responder('corrigir nome'); await a.responder('Perfil corrigido por voz'); await a.responder('sim');
  assert.equal(a.d.querySelector('#nome').value,'Perfil corrigido por voz');
  await a.click('#galeria-cadastro [data-falar]');
  assert.equal(a.situacao.atual,null,'Escolher fotos pausa o ditado');
  assert.ok(a.situacao.falas.at(-1).includes('cinco fotos'));
  const png=Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aUv8AAAAASUVORK5CYII=','base64');
  const entrada=a.d.querySelector('#galeria-cadastro-arquivo');
  Object.defineProperty(entrada,'files',{configurable:true,value:[new a.w.File([png],'primeira.png',{type:'image/png'}),new a.w.File([png],'segunda.png',{type:'image/png'})]});
  entrada.dispatchEvent(new a.w.Event('change',{bubbles:true}));
  await a.click('#voz-microfone');
  await a.responder('publicar');
  for(let i=0;i<30 && !a.d.querySelector('#voz-status').textContent.includes('foi publicado');i++)await esperar();
  assert.equal(a.situacao.postagens,1);
  assert.ok(a.d.querySelector('#voz-status').textContent.includes('foi publicado'));
  const perfis=await(await fetch(base+'/api/profissionais?busca=Perfil%20corrigido%20por%20voz')).json();
  assert.equal(perfis.length,1); assert.equal(perfis[0].telefone,'');
  const perfilHtml=await(await fetch(base+perfis[0].perfil_url)).text();
  assert.equal((perfilHtml.match(/data-ampliar-foto=/g)||[]).length,2,'Fotos escolhidas na conversa devem acompanhar o cadastro');
  assert.deepEqual(a.falhas,[]); a.dom.window.close();
  console.log('OK: conversa, confirmação de cada resposta, correção, autorização, publicação real no SQLite de teste.');

  const b=await ambiente(); await b.click('#voz-microfone'); await b.responder('Teste pausado'); await b.responder('sim');
  assert.ok(b.situacao.atual);
  await b.click('#alternar-modo');
  assert.equal(b.situacao.atual,null); assert.equal(b.d.querySelector('#form-cadastro').hidden,false);
  assert.equal(b.d.querySelector('#nome').value,'Teste pausado');
  assert.equal(b.w.localStorage.getItem('batalha-modo'),'texto');
  b.d.querySelector('#nome').value='Nome corrigido digitando';
  b.d.querySelector('#nome').dispatchEvent(new b.w.Event('input',{bubbles:true}));
  await b.click('#alternar-modo');
  assert.equal(b.d.querySelector('#nome').value,'Nome corrigido digitando');
  await b.click('#voz-microfone');
  await b.responder('cancelar cadastro'); assert.equal(b.situacao.atual,null); assert.equal(b.situacao.postagens,0);
  assert.equal(b.d.querySelector('#nome').value,''); b.dom.window.close();
  console.log('OK: troca de modo pausa escuta, guarda preferência e preserva campos; cancelar apaga rascunho.');

  const c=await ambiente({voz:false});
  assert.equal(c.d.querySelector('#voz-microfone').disabled,true);
  assert.equal(c.d.querySelector('#voz-indisponivel').hidden,false);
  await c.click('#voz-formulario');assert.equal(c.d.documentElement.dataset.modo,'texto');assert.equal(c.d.querySelector('#form-cadastro').hidden,false);
  c.dom.window.close(); console.log('OK: navegador sem reconhecimento oferece preenchimento acompanhado.');

  const e=await ambiente(); await e.click('#voz-microfone');
  e.situacao.atual.onerror({error:'not-allowed'});await esperar();
  assert.equal(e.situacao.atual,null); assert.equal(e.d.querySelector('#voz-indisponivel').hidden,false);
  assert.ok(e.d.querySelector('#voz-status').textContent.includes('bloqueado')); e.dom.window.close();
  console.log('OK: permissão negada interrompe escuta e explica recuperação.');

  const f=await ambiente();await preencher(f,'Teste falha de rede'); f.situacao.falharEnvio=true;
  await f.responder('publicar'); assert.equal(f.d.querySelector('#nome').value,'Teste falha de rede');
  assert.equal(f.d.querySelector('#voz-publicar').disabled,false); assert.equal(f.situacao.atual,null);
  assert.ok(f.d.querySelector('#voz-status').textContent.includes('Seus dados continuam')); f.dom.window.close();
  console.log('OK: falha de envio preserva respostas e permite tentar novamente sem escuta oculta.');
})().catch(erro=>{console.error(erro);process.exitCode=1;});
