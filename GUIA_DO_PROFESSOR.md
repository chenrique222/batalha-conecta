# Batalha Conecta · guia para ensinar a programação

Professor Carlos Henrique · Desenvolvimento de Sistemas

**Ponto de partida da turma:** estruturas de repetição. Não apresente o projeto completo como se todos os seus conceitos já tivessem sido estudados. Use o aplicativo funcionando para mostrar o objetivo e avance pelos exemplos menores da pasta `aulas`.

O objetivo é que os estudantes consigam explicar o caminho entre uma ação na tela e um registro salvo. O pacote contém uma implementação para o professor demonstrar; a aprendizagem acontece reconstruindo partes, fazendo previsões e testando mudanças.

## Preparação do professor

1. Execute o projeto conforme `LEIA_PRIMEIRO.md`.
2. Teste pesquisa, filtro e um cadastro fictício.
3. Deixe o VS Code e o navegador lado a lado.
4. Antes da aula com áudio, teste o microfone no endereço localhost e confira o volume.
5. Comece as atividades com os perfis fictícios. Os dados da pesquisa de campo só devem substituir exemplos quando houver autorização para sua utilização.

## Sequência sugerida

Cada etapa pode ocupar uma ou mais aulas de 50 minutos, conforme o ritmo da turma. Avance quando os alunos conseguirem explicar o resultado e fazer uma mudança pequena sem copiar uma solução completa.

| Etapa | Conteúdo novo | Resultado observável |
| --- | --- | --- |
| 1 | Lista e busca em textos | Encontrar um serviço no terminal. |
| 2 | Dicionário | Separar nome, atividade e comunidade. |
| 3 | Função, parâmetro e retorno | Reaproveitar uma busca. |
| 4 | Biblioteca, Flask e endereço de página | Mostrar os nomes no navegador. |
| 5 | HTML e template | Entender cartões, links e o `for` da página. |
| 6 | Formulário e validação | Enviar um cadastro com campos coerentes. |
| 7 | SQLite, INSERT e SELECT | Fechar e reabrir sem perder cadastros. |
| 8 | Áudio, interface no celular e PWA | Demonstrar site e app usando o mesmo banco. |

## Aula 1 · uma busca que usa repetição

**Explique:** “O programa vai olhar os serviços um por um. Quando encontrar o texto que procuramos, vai mostrar aquele serviço.”

Abra `aulas/01_busca.py` e execute:

```powershell
.\.venv\Scripts\python.exe aulas\01_busca.py
```

Antes de executar, peça previsões: “Se eu escrever `bolo`, o que deve aparecer? E se eu escrever `dentista`?”

| Trecho | Explicação para a turma |
| --- | --- |
| `servicos = [...]` | A lista guarda vários serviços. |
| `input(...)` | A pessoa informa o que quer encontrar. |
| `.lower()` | Transforma letras em minúsculas para facilitar a comparação. |
| `encontrou = False` | Antes da busca, ainda não encontramos nada. |
| `for servico in servicos:` | Cada volta examina um serviço da lista. |
| `if busca in servico.lower():` | Verifica se o texto procurado aparece naquele serviço. |
| `encontrou = True` | Registra que pelo menos um resultado foi encontrado. |

**Demonstração:** execute com `bolo`, depois `pedreiro`, depois uma palavra ausente. Digite também uma busca vazia: explique por que todos aparecem — o texto vazio está contido em qualquer texto.

**Atividade:** adicionar uma costureira e um segundo vendedor de bolos. Fazer três pesquisas e anotar os resultados esperados antes de executar.

**Critério para avançar:** o aluno explica por que o `for` percorre a lista inteira e identifica a diferença entre variável de busca e item examinado.

## Aula 2 · um perfil tem vários campos

Abra `aulas/02_perfis.py`. Mostre apenas um dicionário primeiro:

```python
pessoa = {
    "nome": "Artes da Rosa",
    "atividade": "artesanato",
    "comunidade": "Centro"
}

print(pessoa["nome"])
```

**Explique:** “Cada informação tem uma identificação. Quando usamos `pessoa['nome']`, escolhemos o campo nome desse perfil.”

Depois mostre a lista com três dicionários. O `for` continua sendo o mesmo conceito; o item de cada volta agora é um conjunto de campos.

**Atividade:** criar um perfil fictício de produtor de farinha. Acrescentar a chave `descricao` em todos os perfis e mostrar seu valor.

**Pergunta de verificação:** “Por que é mais fácil pesquisar só a comunidade quando ela tem seu próprio campo?”

## Aula 3 · dar um nome a uma tarefa

Abra `aulas/03_funcoes.py`.

**Explique:** “A função `procurar` recebe uma lista e uma atividade. Ela devolve uma lista menor, com os perfis encontrados.”

Trabalhe `def`, parâmetros, `append` e `return` em momentos separados. Diferencie mostrar uma informação com `print` de devolver um resultado com `return`.

**Demonstração:** chame a função duas vezes com buscas diferentes. Mostre que não foi necessário reescrever a repetição.

**Atividade:** incluir busca pelo nome, além da atividade. Depois criar uma função `mostrar_perfil(pessoa)` que escreva os campos de um perfil.

## Aula 4 · levar o Python para o navegador

Execute `aulas/04_primeira_pagina.py` e abra http://127.0.0.1:5001.

**Explique:** “O navegador pede uma página. O Flask recebe o pedido, executa a função e envia o resultado. O Python continua rodando no computador que é o servidor.”

| Trecho | Significado |
| --- | --- |
| `from flask import ...` | Usa ferramentas da biblioteca Flask. |
| `app = Flask(__name__)` | Cria a aplicação. |
| `@app.get('/')` | Associa o endereço inicial à função abaixo. Introduza como uma ligação entre URL e função; a teoria completa de decoradores pode vir depois. |
| `render_template_string(...)` | Monta HTML a partir do modelo e dos dados. |
| `{{ nome }}` | Coloca o valor do nome na página. |
| `{% for nome in profissionais %}` | Repete um trecho de HTML para cada nome. |

O `for` dentro do modelo é escrito na linguagem de templates Jinja. Ele se parece com o `for` do Python, mas usa delimitadores próprios.

**Atividade:** mudar o título, acrescentar um nome e atualizar a página. Peça para identificar o que pertence ao Python e o que pertence ao HTML.

## Aula 5 · entender as telas do projeto

Volte à aplicação completa. Abra `templates/inicio.html`, depois `templates/profissionais.html`.

Mostre que `base.html` contém elementos repetidos: cabeçalho, navegação e rodapé. As outras páginas preenchem a área de conteúdo. Não peça que os alunos memorizem todos os arquivos.

**Demonstração:** encontre o laço `{% for pessoa in profissionais %}`. Mostre um cartão no navegador e o trecho responsável por seu nome.

**Atividade:** mudar um texto explicativo e um espaçamento. Usar F5 para verificar a alteração. Manter o texto legível e os botões grandes.

**Conexão com o Figma:** o desenho ajuda a escolher a organização e as cores; os arquivos HTML e CSS implementam esse desenho. Não há sincronização automática com o Figma.

## Aula 6 · receber e conferir o cadastro

Abra o cadastro no navegador. Depois localize `cadastro()` em `app.py`.

Explique os pedidos com um exemplo concreto:

- **GET:** abrir a página para preencher.
- **POST:** enviar o formulário preenchido.

Mostre apenas um campo por vez:

```python
nome = request.form.get("nome", "").strip()

if len(nome) < 2:
    print("O nome precisa ser preenchido.")
```

Esse trecho é uma explicação isolada; na aplicação, as mensagens de erro são mostradas na tela.

**Atividade:** escrever no caderno três regras de validação: categoria escolhida, nome preenchido e comunidade informada. Testar o formulário deixando um campo obrigatório vazio.

O navegador ajuda a verificar campos, e o Python verifica novamente ao receber os dados. Isso é necessário porque os pedidos podem chegar ao servidor por outros meios.

Os campos ocultos de sessão e envio evitam pedidos sem sessão válida e publicações duplicadas. Explique sua finalidade; deixe a implementação detalhada para depois de dominar o fluxo principal.

## Aula 7 · salvar para encontrar depois

Abra `dados.py`. Comece pela tabela `profissionais` e explique o identificador `id`.

Use exemplos pequenos antes da consulta completa:

```sql
SELECT nome, categoria, comunidade FROM profissionais;
```

```sql
SELECT nome FROM profissionais WHERE categoria = 'artesanato';
```

No Python, mostre a separação entre o comando e o valor:

```python
conexao.execute(
    "SELECT nome FROM profissionais WHERE categoria = ?",
    (categoria,)
)
```

O `?` recebe o valor de forma controlada. Não monte SQL juntando diretamente o texto digitado pelo usuário.

**Demonstração:** cadastre um perfil, feche o servidor, execute novamente e encontre o mesmo perfil.

**Atividade:** relacionar os campos do formulário às colunas da tabela. Escrever uma consulta para uma categoria e explicar seu resultado.

Essa primeira versão usa uma tabela. Categorias em tabela própria, contas e relacionamentos com chaves estrangeiras são expansões posteriores.

## Aula 8 · voz, celular e conexão com a cidade

Abra o mesmo servidor no computador e no celular, seguindo `LEIA_PRIMEIRO.md`.

**Demonstração:** envie um cadastro pelo celular e atualize a busca no computador. Explique: “Os dois aparelhos pedem informações ao mesmo Python, que usa o mesmo banco”.

Mostre que HTML organiza a tela, CSS muda seu encaixe e JavaScript aciona recursos do navegador. A gravação usa o microfone do aparelho e envia o arquivo ao Python. Python guarda o caminho junto ao perfil.

**Atividade de observação:** convide uma pessoa para encontrar um trabalhador e ouvir uma apresentação. Observe onde ela hesita, precisa de ajuda ou não reconhece um botão. A avaliação é da interface.

Teste símbolos, palavras, tamanho dos botões e instruções com o público. A presença de áudio, por si só, não comprova que o aplicativo seja acessível a todas as pessoas. A versão 0.2 acrescenta modo com ícones e cadastro guiado por fala. O roteiro está em `GUIA_ICONES_E_VOZ.md`. A disponibilidade e a precisão do reconhecimento precisam ser verificadas nos aparelhos e com as pessoas que usarão o projeto.

Na rede local HTTP, o microfone pode ficar indisponível: use um áudio salvo para a demonstração. Para instalar o PWA e testar todos os recursos nos celulares, disponibilize a aplicação em HTTPS.

## Como distribuir o trabalho da turma

Depois de todos compreenderem o fluxo básico, forme grupos por entrega:

| Grupo | Entrega e forma de verificar |
| --- | --- |
| Perfis e linguagem | Escrever exemplos claros e organizar categorias; conferir se os colegas compreendem os nomes. |
| Interface | Ajustar títulos, botões e espaçamento; testar celular e computador. |
| Python e dados | Explicar a busca e as validações; demonstrar persistência após reiniciar. |
| Voz e testes | Preparar áudios autorizados e observar o uso; registrar dificuldades concretas. |

Cada grupo deve demonstrar uma alteração, apontar o arquivo correspondente e explicar o que mudou. Reserve uma parte comum da avaliação para todos: “O que acontece entre clicar em Publicar e encontrar o perfil na lista?”

## Apresentação na feira

1. Apresente a necessidade: divulgar o trabalho local com fotos e voz.
2. Peça ao visitante para encontrar um serviço em um dos perfis demonstrativos.
3. Mostre a descrição falada ou uma apresentação gravada pela equipe.
4. Faça um cadastro fictício e encontre-o em outro aparelho que acesse o mesmo servidor.
5. Explique a contribuição dos alunos: programação, dados, telas e testes com usuários.

Conte os resultados da pesquisa quando ela tiver sido aplicada. Não apresente exemplos fictícios como trabalhadores reais ou como resultados já coletados.

## Limites da primeira versão

Não há contas de usuário, recuperação de acesso, edição/exclusão autônoma, pagamentos, avaliações ou atendimento automatizado. O pacote permite demonstrar a base do serviço: encontrar, apresentar e cadastrar trabalhos. Áudio e telefone dependem dos recursos do aparelho; instalação PWA depende do navegador e do endereço seguro.

Depois dessa base, as prioridades são testar com o público, simplificar o cadastro conforme as dificuldades observadas e implementar responsabilidade e controle sobre cada perfil antes de uso público.
