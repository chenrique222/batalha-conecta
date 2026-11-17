/* Uma seleção pode receber fotos em várias visitas ao seletor do aparelho. */
"use strict";
class SeletorFotos {
  constructor(painel) {
    this.painel = painel;
    this.input = painel.querySelector('input[type="file"]');
    this.form = document.getElementById(painel.dataset.formulario);
    this.itens = [];
    this.input.addEventListener("change", () => this.adicionar([...this.input.files]));
    this.form.addEventListener("change", () => this.atualizarContagem());
    this.atualizarContagem();
  }
  quantidadeExistente() {
    const removidas = this.form.querySelectorAll('input[name="remover"]:checked').length;
    return Math.max(0, Number(this.painel.dataset.existentes) - removidas);
  }
  avisar(texto) {
    const aviso = this.painel.querySelector("[data-erros-fotos]");
    aviso.hidden = !texto;
    aviso.textContent = texto;
    if (texto && document.documentElement.dataset.modo === "icones") falar(texto, this.painel.querySelector("button"));
  }
  adicionar(arquivos) {
    this.input.value = "";
    if (this.itens.length + arquivos.length + this.quantidadeExistente() > 5) {
      this.avisar("A galeria pode ter até cinco fotos. Remova uma foto antes de adicionar outra.");
      return;
    }
    if (arquivos.some(f => !["image/jpeg", "image/png", "image/webp"].includes(f.type) || f.size > 5 * 1024 * 1024)) {
      this.avisar("Escolha fotos JPG, PNG ou WebP, de até cinco megabytes cada.");
      return;
    }
    this.avisar("");
    arquivos.forEach(arquivo => this.itens.push({arquivo, url:URL.createObjectURL(arquivo)}));
    this.renderizar();
  }
  renderizar() {
    const grade = this.painel.querySelector("[data-previas-fotos]");
    grade.replaceChildren();
    this.itens.forEach((item, indice) => {
      const bloco = document.createElement("div");
      const foto = document.createElement("img");
      foto.src = item.url;
      foto.alt = `Foto escolhida ${indice + 1}`;
      const remover = document.createElement("button");
      remover.type = "button";
      remover.className = "remover-foto";
      remover.textContent = "×";
      remover.setAttribute("aria-label", `Remover foto ${indice + 1}`);
      remover.addEventListener("click", () => {
        URL.revokeObjectURL(item.url);
        this.itens.splice(indice, 1);
        this.avisar("");
        this.renderizar();
      });
      bloco.append(foto, remover);
      grade.append(bloco);
    });
    this.atualizarContagem();
  }
  atualizarContagem() {
    this.painel.querySelector("[data-contagem-fotos]").textContent = `${this.quantidadeExistente() + this.itens.length} / 5`;
  }
  anexar(dados) {
    dados.delete("fotos");
    this.itens.forEach(item => dados.append("fotos", item.arquivo));
  }
  limpar() {
    this.itens.forEach(item => URL.revokeObjectURL(item.url));
    this.itens = [];
    this.input.value = "";
    this.renderizar();
  }
}
document.querySelectorAll("[data-seletor-fotos]").forEach(painel => {
  const seletor = new SeletorFotos(painel);
  if (painel.id === "galeria-cadastro") window.galeriaCadastro = seletor;
  if (painel.id === "galeria-edicao") {
    let enviando = false;
    seletor.form.addEventListener("submit", async evento => {
      evento.preventDefault();
      if (enviando) return;
      enviando = true;
      const botao = seletor.form.querySelector('[type="submit"]');
      botao.disabled = true;
      const dados = new FormData(seletor.form);
      seletor.anexar(dados);
      try {
        const resposta = await fetch(seletor.form.action, {method:"POST", body:dados, headers:{Accept:"application/json"}});
        const resultado = await resposta.json();
        if (!resposta.ok) throw new Error((resultado.erros || ["Não foi possível salvar as fotos."]).join(" "));
        window.location.assign(resultado.url);
        window.location.reload();
        return;
      } catch (erro) { seletor.avisar(erro.message === "Failed to fetch" ? "Confira a conexão e tente salvar novamente." : erro.message); }
      enviando = false;
      botao.disabled = false;
    });
  }
  window.addEventListener("pagehide", () => seletor.itens.forEach(item => URL.revokeObjectURL(item.url)));
});
// As miniaturas abrem uma foto maior. Esc, setas e botões funcionam no diálogo.
const ampliacao = document.querySelector("#foto-ampliada");
if (ampliacao) {
  const fotos = [...document.querySelectorAll("[data-ampliar-foto]")];
  let atual = 0;
  function mostrar(indice) {
    atual = (indice + fotos.length) % fotos.length;
    ampliacao.querySelector("img").src = fotos[atual].dataset.ampliarFoto;
    ampliacao.querySelector("img").alt = `Foto ${atual + 1} do trabalho`;
    ampliacao.querySelector("[data-posicao-foto]").textContent = `${atual + 1} / ${fotos.length}`;
  }
  fotos.forEach((foto, indice) => foto.addEventListener("click", () => { mostrar(indice); ampliacao.showModal(); }));
  ampliacao.querySelector("[data-fechar-foto]").addEventListener("click", () => ampliacao.close());
  ampliacao.querySelector("[data-foto-anterior]").addEventListener("click", () => mostrar(atual - 1));
  ampliacao.querySelector("[data-foto-proxima]").addEventListener("click", () => mostrar(atual + 1));
  ampliacao.addEventListener("keydown", evento => { if (evento.key === "ArrowLeft") mostrar(atual - 1); if (evento.key === "ArrowRight") mostrar(atual + 1); });
}
