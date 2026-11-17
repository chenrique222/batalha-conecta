/* Execute: node --test tests/test_voz.cjs. Não usa microfone nem serviços. */
const test = require("node:test");
const assert = require("node:assert/strict");
const voz = require("../static/voz-logica.js");

test("reconhece números ditados, incluindo meia, e preserva zeros", () => {
  assert.equal(voz.telefoneFalado("oito meia nove nove nove nove nove zero zero zero zero"), "86999990000");
  assert.equal(voz.telefoneFalado("+55 (86) 99999-0000"), "86999990000");
  assert.equal(voz.telefoneFalado("86 9 9999 0000"), "86999990000");
});
test("não adivinha telefone incompleto ou ambíguo", () => {
  for (const texto of ["123", "086999990000", "oitenta e seis nove nove", "86 99999 0000 talvez", "fone 86 99999 0000"]) assert.equal(voz.telefoneFalado(texto), null);
  assert.equal(voz.telefoneFalado("pular"), "");
  assert.equal(voz.telefoneFalado("Não tenho WhatsApp"), "");
});
test("confere uma categoria por vez", () => {
  assert.equal(voz.categoriaFalado("faço bolos"), "alimentacao");
  assert.equal(voz.categoriaFalado("artesanato"), "artesanato");
  assert.equal(voz.categoriaFalado("farinha de mandioca"), "rural");
  assert.equal(voz.categoriaFalado("trabalho rural"), "");
  assert.equal(voz.categoriaFalado("sou pedreiro"), "manutencao");
  assert.equal(voz.categoriaFalado("serviços de manutenção"), "manutencao");
  assert.equal(voz.categoriaFalado("sou eletricista"), "manutencao");
  assert.equal(voz.categoriaFalado("outros serviços"), "servicos");
  assert.equal(voz.categoriaFalado("sou cabeleireira"), "servicos");
  assert.equal(voz.categoriaFalado("manutenção ou outros serviços"), "");
  assert.equal(voz.categoriaFalado("comidas ou artesanato"), "");
  assert.equal(voz.categoriaFalado("não sei"), "");
});
test("não publica por um sim fora de contexto ou uma negação", () => {
  assert.equal(voz.publicar("sim"), false);
  assert.equal(voz.publicar("não publicar"), false);
  assert.equal(voz.publicar("Pode publicar!"), true);
  assert.equal(voz.sim("sim mas está errado"), false);
  assert.equal(voz.nao("Repetir"), true);
});
test("respostas longas são recusadas sem corte silencioso", () => {
  assert.ok(voz.validar("nome", "x".repeat(81)).erro);
  assert.ok(voz.validar("descricao", "x".repeat(701)).erro);
  assert.deepEqual(voz.validar("comunidade", "Centro"), {valor:"Centro"});
});
test("resumo lê cada dígito e permite corrigir dados específicos", () => {
  assert.equal(voz.lerValor("telefone", "86999990000"), "8, 6, 9, 9, 9, 9, 9, 0, 0, 0, 0");
  assert.equal(voz.corrigirCampo("corrigir WhatsApp"), 4);
  assert.equal(voz.corrigirCampo("corrigir descrição"), 2);
  assert.equal(voz.corrigirCampo("corrigir tudo"), -1);
});
