# Batalha Conecta — trocar imagens, cores e textos

Este guia usa os arquivos reais deste projeto. Faça uma alteração por vez, salve e confira no navegador. Você pode abrir este arquivo no VS Code e pressionar Ctrl+Shift+V para visualizar o guia formatado.

## 1. Abrir esta atualização

1. Feche a execução antiga com Ctrl+C na janela do terminal.
2. Extraia o novo ZIP em outra pasta. Abra a pasta `Batalha_Conecta_Python` extraída.
3. Se já fez cadastros, copie a pasta **instance inteira** do projeto antigo para a nova pasta `Batalha_Conecta_Python`, antes de iniciar. Ela contém o banco, as fotos, os áudios e a chave da sessão. Não apague a pasta antiga até conferir seus dados.
4. Execute `iniciar_windows.bat` e mantenha a janela aberta. A alternativa pelo terminal está em `NOVIDADES_V06.md`.
5. Abra http://127.0.0.1:5000 e pressione Ctrl+F5 para carregar o visual atualizado.

No VS Code, escolha **Arquivo → Abrir Pasta** e selecione essa mesma pasta do projeto.

## 2. O que foi personalizado

A logo completa enviada foi guardada sem alteração de tamanho, cores ou transparência em `static/artes/batalha-conecta-logo-completa.png`. O arquivo recebido tem **2048 × 1152 pixels**. O cabeçalho mostra a marca completa sobre uma base azul escura, para destacar as letras brancas. Uma janela de apresentação elimina apenas as margens transparentes; o PNG original permanece intacto.

Abaixo da marca aparece **“Valorizando o serviço da nossa gente”**. O mapa verde usado antes no cabeçalho agora também identifica a aba do navegador e o aplicativo instalado.

A paleta “Sertão conectado” parte da logo: o **azul-marinho** do fundo e o **verde** do mapa e das setas, com o **âmbar** do sol e a **terracota** do barro. Cada cor tem um único significado, igual nos dois modos: verde para falar e confirmar, azul para procurar, âmbar para ouvir e terracota para parar ou cancelar. Ações de apoio (ajuda, fotos, celular) usam azul claro. No modo Imagens e voz, as cores ficam mais fortes; no modo com textos, em tons claros. Cada cor acompanha um desenho e uma orientação em áudio.

## 3. Onde fica cada mudança

Os caminhos desta tabela começam dentro da pasta `Batalha_Conecta_Python`.

| O que você quer mudar | Arquivo ou local |
| --- | --- |
| Símbolo e frase do cabeçalho | `templates/base.html` |
| Arquivo da logo completa | `static/artes/batalha-conecta-logo-completa.png` |
| Favicon da aba | `static/favicon-mapa.svg` e `static/favicon-mapa.ico` |
| Cores do aplicativo | Início de `static/estilo.css`, no bloco `:root` |
| Cores e tamanho dos botões no modo de imagens | `static/visual-acessivel.css` |
| Switch de modo | `templates/base.html` e `static/acessibilidade.js` |
| Ícones dos botões | `static/icons.svg` |
| Imagens das atividades | Pasta `static/artes/` e lista `CATEGORIAS` em `dados.py` |
| Textos da página inicial | `templates/inicio.html` |
| Fotos de um trabalhador | Opção **Gerenciar minhas fotos** no perfil |

HTML organiza o conteúdo. CSS define a aparência. Python fornece as informações e as regras. Para estas primeiras alterações, basta localizar e substituir os valores indicados.

## 4. Primeira atividade — trocar a imagem de alimentação

1. Escolha uma foto de comida. Para este cartão, uma imagem horizontal de **1200 × 800 pixels** é um bom ponto de partida. Mantenha o assunto no centro, porque alguns tamanhos de tela recortam as bordas.
2. Salve como `alimentacao.jpg` dentro de `static/artes/`. Use nomes simples, sem espaços nem acentos. Se a imagem for PNG, use `alimentacao.png`. Renomear a extensão de um arquivo não converte seu formato.
3. No VS Code, abra `dados.py`.
4. No início do arquivo, localize esta linha dentro da lista `CATEGORIAS`.

```python
{"id": "alimentacao", "nome": "Bolos e comidas", "exemplo": "Bolos, doces e refeições", "imagem": "alimentacao-ia.png", "imagem_ia": True},
```

5. Troque **somente o nome do arquivo** no campo `imagem`. Os demais valores devem ficar como estão no seu arquivo.

```python
"imagem": "alimentacao.jpg"
```

6. Se a nova imagem for uma foto real, troque também `"imagem_ia": True` por `"imagem_ia": False` nessa categoria. Isso retira a identificação de IA dessa imagem. Salve com Ctrl+S. Se iniciou com `iniciar_windows.bat`, a execução de desenvolvimento acompanha alterações no Python. Aguarde a reinicialização e atualize o navegador com Ctrl+F5.
7. Confira a imagem na página inicial, na seleção de atividade do cadastro e nos perfis dessa categoria que ainda não têm foto própria. A lista de categorias é compartilhada entre essas telas.

Cada item da lista tem informações entre aspas. O campo `imagem` informa qual arquivo o aplicativo deve procurar. **Mantenha o campo `id`**, porque ele também identifica a categoria dos cadastros no banco.

| Categoria | Arquivo atual |
| --- | --- |
| Bolos e comidas | `alimentacao-ia.png` |
| Artesanato | `artesanato-ia.png` |
| Farinha e derivados | `rural-ia.png` |
| Serviços de manutenção | `manutencao-ia.png` |
| Outros serviços | `outros-servicos-ia.png` |

Se a imagem não aparecer, confira o nome, a extensão e a pasta. Não escreva `static/artes/` dentro do campo `imagem`, pois o aplicativo já acrescenta esse caminho.

### Mostrar a imagem inteira ou preencher o cartão

Em `static/estilo.css`, procure `.categoria-card img`. Os tamanhos maiores do modo de imagens ficam em `static/visual-acessivel.css`. A propriedade `object-fit:cover` preenche a área e pode recortar as bordas. Para mostrar a imagem inteira, troque apenas essa propriedade por `object-fit:contain`. Podem aparecer espaços nas laterais. Essa regra afeta todos os cartões de categorias.

## 5. Trocar as fotos da galeria

1. Abra o perfil no mesmo navegador em que ele foi cadastrado, com a sessão ainda ativa.
2. Toque em **Gerenciar minhas fotos**.
3. Marque as fotos que deseja remover e escolha as novas em **Adicionar fotos**.
4. Mantenha no máximo **cinco fotos ao todo**, entre as que ficaram e as novas. O app aceita JPG, PNG e WebP, até 5 MB por foto.
5. Toque em **Salvar fotos**. A primeira foto da lista será a capa.

A edição da galeria depende da sessão do navegador que criou o perfil. Os perfis fictícios iniciais usam a ilustração da categoria. Não renomeie os arquivos dentro de `instance/uploads` manualmente, porque seus nomes também estão registrados no banco.

## 6. Trocar a logo do cabeçalho no futuro

Para uma nova logo completa, prefira PNG transparente, horizontal, com pouco espaço vazio ao redor. Uma largura de 1200 pixels já permite boa apresentação nesse cabeçalho. Preserve as proporções; não estique a imagem.

O SVG atual usa uma janela ajustada ao PNG recebido. Para uma arte com outro enquadramento, use uma imagem comum seguindo estes passos:

1. Coloque a nova arte, por exemplo `minha-logo.png`, em `static/artes/`.
2. Em `templates/base.html`, encontre `<svg class="marca-logo-completa"`.
3. Substitua **somente esse SVG inteiro**, até o `</svg>` correspondente, pelo elemento abaixo. Mantenha o link da marca e a frase ao redor.

```html
<img class="marca-logo-completa"
     src="{{ url_for('static', filename='artes/minha-logo.png') }}"
     alt="">
```

4. Em `static/visual-acessivel.css`, acrescente esta regra para preservar a proporção da nova imagem:

```css
img.marca-logo-completa { object-fit: contain; padding: 8px; }
```

5. Salve e atualize com Ctrl+F5. O link ao redor da imagem já informa “Batalha Conecta, início” para leitores de tela, por isso o `alt` fica vazio. A logo continua aparecendo no modo de imagens.

O favicon e o ícone do aplicativo são arquivos separados: `static/favicon-mapa.svg`, `static/favicon-mapa.ico`, `static/icon-mapa-192.png`, `static/icon-mapa-512.png` e `static/icon-mapa-maskable.png`. Para trocar esses ícones, use uma versão só com o emblema, quadrada, e exporte nos tamanhos indicados. O arquivo ICO contém 16, 32 e 48 pixels. `templates/base.html` referencia o favicon; `static/manifest.webmanifest` referencia os ícones de instalação. Alterar o nome de um arquivo exige atualizar suas referências.

## 7. Alterar uma cor

Abra `static/estilo.css`. A paleta está organizada no começo, dentro de `:root`. O valor que começa com `#` é um código de cor.

| Variável | Cor atual | Uso |
| --- | --- | --- |
| `--marca-fundo` | `#0b2149` | Faixa do cabeçalho e fundo da logo |
| `--fundo` | `#f5f6f2` | Fundo da página |
| `--papel` | `#ffffff` | Cartões e campos |
| `--texto` | `#17284a` | Texto principal |
| `--secundario` | `#4f5d73` | Legendas e explicações |
| `--azul-forte` | `#1b3f78` | Títulos e botões principais |
| `--azul` | `#e6edf7` | Fundos azulados suaves, ações de apoio |
| `--verde-forte` | `#0f7a55` | Falar, confirmar, seleções |
| `--verde` | `#dff1e7` | Fundos verdes suaves |
| `--verde-vivo` | `#2fbf71` | Destaques: microfone ouvindo, menu atual |
| `--ambar` | `#f0b23e` | Botões de ouvir (alto-falante) |
| `--ambar-claro` | `#fcf1d8` | Avisos e botões de ouvir no modo textos |
| `--terracota` | `#b4452c` | Parar, cancelar e erros |

Todas as combinações de texto e fundo foram conferidas com contraste de pelo menos 4,5:1, o mínimo recomendado para leitura.

Por exemplo, para experimentar um fundo levemente mais quente, substitua apenas a linha correspondente.

```css
--fundo: #faf9f5;
```

Salve e confira com Ctrl+F5. Mantenha os textos escuros nos fundos claros e confira se as palavras e os ícones continuam fáceis de distinguir. As cores de erro, gravação e estrelas têm funções próprias.

A cor da moldura do aplicativo instalado também aparece em `theme_color` de `static/manifest.webmanifest` e na meta `theme-color` de `templates/base.html` e `static/offline.html`. Nesta atualização, todos usam `#0b2149`, o azul-marinho da logo.

## 8. Alterar a frase abaixo do nome

Em `templates/base.html`, procure este trecho.

```html
<small class="marca-frase texto-ui">Valorizando o serviço da nossa gente</small>
```

Troque somente as palavras entre as tags. Este é um exemplo para experimentar.

```html
<small class="marca-frase texto-ui">Seu trabalho tem valor</small>
```

Salve e atualize a página. Confira também no celular para ver se a frase cabe. Em **Imagens e voz**, esse texto fica visualmente oculto conforme o modo escolhido.

## 9. Exercício para a turma

Cada dupla pode trocar uma imagem de categoria, experimentar uma cor de fundo e escrever uma nova frase. Depois, deve explicar qual arquivo mudou e demonstrar o resultado nos modos **Textos** e **Imagens e voz**.

O ciclo de trabalho é **editar → salvar → atualizar → conferir**. Para voltar atrás no VS Code, use Ctrl+Z e salve novamente. Se estiver executando com `servir.py`, encerre e inicie o servidor após alterações em Python.

## 10. O switch e as novas cores

No alto de cada página, um único interruptor alterna os modos. Com a bolinha à esquerda, junto ao livro, aparecem textos. Com a bolinha à direita, junto à pessoa falando, aparecem imagens e orientações por voz. Você também pode selecioná-lo com Tab e ativá-lo com Espaço ou Enter. A preferência fica salva neste navegador.

Para alterar as cores do modo de imagens, abra `static/visual-acessivel.css` e edite as variáveis no início. As regras começam com `html[data-modo="icones"]` para afetar somente esse modo. O valor interno continua sendo `icones` para reconhecer a preferência já salva de versões anteriores.

As cinco categorias usam imagens geradas por IA como exemplos fictícios. O pedreiro representa **Serviços de manutenção**. A barbearia ilustra uma possibilidade de **Outros serviços**, que acolhe atividades fora das demais categorias e não se limita a cortes de cabelo. O áudio explica essa abrangência. Observe com os participantes se isso fica claro. A origem das imagens está em `ORIGEM_IMAGENS_V06.md`.

O símbolo do WhatsApp fica no trecho `<symbol id="whatsapp">` de `static/icons.svg`. O botão de contato está em `templates/perfil.html`, na classe `botao-whatsapp`. Ele abre o WhatsApp com o número informado; não envia mensagens automaticamente.
