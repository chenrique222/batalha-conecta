/* Regras da conversa. Não acessa microfone, rede nem banco de dados.
   Pode ser estudado e testado separadamente da interface. */
"use strict";
(function (raiz) {
  const limpar = texto => texto.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase().replace(/[^a-z0-9 ]/g, " ").replace(/\s+/g, " ").trim();
  const etapas = [
    {campo:"nome", titulo:"Como podemos chamar você?", icone:"pessoa", pergunta:"Qual é o seu nome ou o nome do seu trabalho?"},
    {campo:"categoria", titulo:"Qual é sua atividade?", icone:"loja", pergunta:"Qual é a sua atividade? Diga: comidas, artesanato, farinha e derivados, manutenção ou outros serviços."},
    {campo:"descricao", titulo:"Conte o que você faz", icone:"microfone", pergunta:"Conte em uma frase o que você faz. Por exemplo: faço bolos de milho por encomenda."},
    {campo:"comunidade", titulo:"Onde fica seu trabalho?", icone:"local", pergunta:"Qual é o seu bairro ou comunidade? Não precisa dizer o endereço da sua casa."},
    {campo:"telefone", titulo:"Como falar com você?", icone:"whatsapp", pergunta:"Qual é o seu WhatsApp com DDD? Fale um número de cada vez, começando pelo DDD. Se não quiser informar, diga pular."}
  ];
  const categorias = {alimentacao:"Bolos e comidas", artesanato:"Artesanato", rural:"Farinha e derivados", manutencao:"Serviços de manutenção", servicos:"Outros serviços"};
  const palavras = {
    alimentacao:/\b(comida|comidas|alimentacao|bolo|bolos|doce|doces|refeicao|refeicoes)\b/,
    artesanato:/\b(artesanato|artesa|artesao|cesta|cestas|croche)\b/,
    rural:/\b(farinha|farinhada|mandioca|goma|tapioca|derivados)\b/,
    manutencao:/\b(manutencao|pedreiro|pedreira|reparo|reparos|reforma|reformas|pintor|pintora|pintura|eletricista|eletrica|encanador|encanadora|encanamento|construcao)\b/,
    servicos:/\b(outros? servicos?|outra atividade|outras atividades|costura|costureira|costureiro|cabeleireiro|cabeleireira|barbeiro|manicure|entregas)\b/
  };
  function categoriaFalado(texto) {
    const normal = limpar(texto);
    const encontrados = Object.keys(palavras).filter(chave => palavras[chave].test(normal));
    return encontrados.length === 1 ? encontrados[0] : "";
  }
  function telefoneFalado(texto) {
    let normal = limpar(texto);
    if (/^(pular|pule|sem telefone|nao tenho|nao tenho whatsapp|nao quero informar)$/.test(normal)) return "";
    const numeros = {zero:"0",um:"1",uma:"1",dois:"2",duas:"2",tres:"3",quatro:"4",cinco:"5",seis:"6",meia:"6",sete:"7",oito:"8",nove:"9"};
    normal = normal.split(" ").map(parte => numeros[parte] ?? parte).join(" ");
    // Só aceitamos dígitos e separadores: não adivinhamos trechos duvidosos.
    if (!/^[0-9 ]+$/.test(normal)) return null;
    let numero = normal.replace(/ /g, "");
    if (/^55\d{10,11}$/.test(numero)) numero = numero.slice(2);
    return /^[1-9]\d{9,10}$/.test(numero) ? numero : null;
  }
  function validar(campo, texto) {
    const valor = texto.trim();
    if (campo === "categoria") {
      const categoria = categoriaFalado(valor);
      return categoria ? {valor:categoria} : {erro:"Não consegui escolher uma atividade. Diga apenas uma: comidas, artesanato, farinha e derivados, manutenção ou outros serviços."};
    }
    if (campo === "telefone") {
      const telefone = telefoneFalado(valor);
      return telefone !== null ? {valor:telefone} : {erro:"Não consegui conferir o número. Diga o DDD e o telefone, um dígito de cada vez. Ou diga pular."};
    }
    const maximo = campo === "descricao" ? 700 : 80;
    if (valor.length < 2 || valor.length > maximo) return {erro:campo === "descricao" ? "Conte seu trabalho em uma frase mais curta." : "Não entendi. Diga novamente, de forma curta."};
    return {valor};
  }
  const sim = texto => /^(sim|sim esta certo|esta certo|esta correto|correto|confirmo|pode continuar|isso|isso mesmo)$/.test(limpar(texto));
  const nao = texto => /^(nao|nao esta certo|repetir|repita|corrigir|tentar novamente)$/.test(limpar(texto));
  const publicar = texto => /^(publicar|pode publicar|quero publicar|sim publicar|sim pode publicar)$/.test(limpar(texto));
  function lerValor(campo, valor) {
    if (campo === "categoria") return categorias[valor] || valor;
    if (campo === "telefone") return valor ? valor.split("").join(", ") : "sem telefone";
    return valor;
  }
  function resumo(valores) {
    return `Seu trabalho: ${valores.nome}. Atividade: ${lerValor("categoria", valores.categoria)}. Apresentação: ${valores.descricao}. Comunidade: ${valores.comunidade}. WhatsApp: ${lerValor("telefone", valores.telefone)}.`;
  }
  function corrigirCampo(texto) {
    const normal = limpar(texto);
    if (!normal.startsWith("corrigir ")) return -1;
    const campos = {nome:0,atividade:1,categoria:1,descricao:2,apresentacao:2,comunidade:3,bairro:3,telefone:4,numero:4,whatsapp:4};
    return campos[normal.slice(9)] ?? -1;
  }
  const api = {limpar, etapas, categorias, categoriaFalado, telefoneFalado, validar, sim, nao, publicar, lerValor, resumo, corrigirCampo};
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else raiz.BatalhaVoz = api;
})(typeof window !== "undefined" ? window : {});
