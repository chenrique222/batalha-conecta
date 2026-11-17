const test = require("node:test");
const assert = require("node:assert/strict");
const EscutaPaciente = require("../static/escuta.js");

function ambiente(opcoes={}) {
  let tempo = 0, id = 0;
  const timers = new Map(), sessoes = [], finais = [], erros = [], parciais = [];
  const avancar = duracao => {
    const fim = tempo + duracao;
    while (true) {
      const proximo = [...timers].filter(([,v])=>v.quando<=fim).sort((a,b)=>a[1].quando-b[1].quando)[0];
      if (!proximo) break;
      timers.delete(proximo[0]);tempo=proximo[1].quando;proximo[1].funcao();
    }
    tempo=fim;
  };
  class Reconhecimento {
    constructor(){sessoes.push(this);this.paradas=0;}
    start(){this.onstart?.();}
    stop(){this.paradas++;this.onend?.();}
    abort(){this.abortado=true;}
    resultado(partes){this.onresult?.({resultIndex:0,results:partes.map(([texto,final=true])=>{const r=[{transcript:texto}];r.isFinal=final;return r;})});}
  }
  const escuta=new EscutaPaciente({Reconhecimento, onFinal:t=>finais.push(t),onErro:(tipo,texto)=>erros.push({tipo,texto}),onParcial:t=>parciais.push(t),
    agora:()=>tempo,agendar:(funcao,ms)=>{timers.set(++id,{funcao,quando:tempo+ms});return id;},cancelarTimer:i=>timers.delete(i),...opcoes});
  escuta.iniciar();
  return {escuta,sessoes,finais,erros,parciais,avancar,timers};
}
test("não encerra na primeira frase; aguarda 6 segundos após o último trecho",()=>{
  const a=ambiente(), rec=a.sessoes[0];
  assert.equal(rec.continuous,true);assert.equal(rec.interimResults,true);
  rec.resultado([["Faço bolos"]]);a.avancar(4000);
  assert.equal(rec.paradas,0);assert.deepEqual(a.finais,[]);
  rec.resultado([["Faço bolos"],["por encomenda"]]);a.avancar(5999);assert.deepEqual(a.finais,[]);
  a.avancar(1);assert.deepEqual(a.finais,["Faço bolos por encomenda"]);
});
test("substitui resultados intermediários em vez de duplicar palavras",()=>{
  const a=ambiente(), rec=a.sessoes[0];
  rec.resultado([["Bolo",false]]);rec.resultado([["Bolos da Rosa",false]]);rec.resultado([["Bolos da Rosa",true]]);
  a.escuta.finalizar();assert.deepEqual(a.finais,["Bolos da Rosa"]);
});
test("reabre depois de encerramento precoce e preserva os dígitos repetidos",()=>{
  const a=ambiente({pausa:10000});
  a.sessoes[0].resultado([["8 6 9"]]);a.sessoes[0].onend();a.avancar(350);
  assert.equal(a.sessoes.length,2);a.sessoes[1].resultado([["9 9 9 9 0 0 0 0"]]);
  a.avancar(9000);assert.deepEqual(a.finais,[]);a.avancar(1000);
  assert.deepEqual(a.finais,["8 6 9 9 9 9 9 0 0 0 0"]);
});
test("silêncio inicial não pausa imediatamente; espera 30 segundos",()=>{
  const a=ambiente();a.avancar(5000);
  a.sessoes[0].onerror({error:"no-speech"});a.sessoes[0].onend();a.avancar(350);
  assert.deepEqual(a.erros,[]);assert.equal(a.sessoes.length,2);
  a.avancar(24649);assert.deepEqual(a.erros,[]);a.avancar(1);
  assert.equal(a.erros[0].tipo,"no-speech");
});
test("terminei conclui e é retirado da resposta",()=>{
  const a=ambiente();a.sessoes[0].resultado([["Centro. Terminei."]]);
  assert.deepEqual(a.finais,["Centro."]);assert.equal(a.escuta.encerrada,true);
});
test("cancelar aborta escuta e todos os relógios sem enviar resposta",()=>{
  const a=ambiente();a.sessoes[0].resultado([["Trecho em andamento"]]);
  assert.equal(a.escuta.cancelar(),"Trecho em andamento");a.avancar(200000);
  assert.deepEqual(a.finais,[]);assert.equal(a.sessoes.length,1);assert.equal(a.timers.size,0);
});
test("falha real preserva o trecho para retomar e não reabre sem ação",()=>{
  const a=ambiente();a.sessoes[0].resultado([["Faço bolos"]]);a.sessoes[0].onerror({error:"network"});
  a.avancar(200000);assert.deepEqual(a.erros,[{tipo:"network",texto:"Faço bolos"}]);assert.equal(a.sessoes.length,1);
  const b=ambiente({rascunho:a.erros[0].texto});b.sessoes[0].resultado([["de milho"]]);b.escuta.finalizar();
  assert.deepEqual(b.finais,["Faço bolos de milho"]);
});
test("limite total encerra aos 120 segundos preservando o que foi reconhecido",()=>{
  const a=ambiente({pausa:200000});a.sessoes[0].resultado([["Resposta longa"]]);
  a.avancar(119999);assert.deepEqual(a.finais,[]);a.avancar(1);
  assert.deepEqual(a.finais,["Resposta longa"]);
});
