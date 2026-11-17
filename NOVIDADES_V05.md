# Batalha Conecta — versão 0.5

## O que mudou

- Modo **Imagens e voz** com cores distintas por ação, mantendo desenhos e orientações em áudio.
- Ícones maiores: pessoas falando, trabalhadores, barraca, casa, livro, câmera e microfone.
- Botão verde de WhatsApp com o símbolo reconhecível do aplicativo.
- Um único **switch**, com bolinha móvel: livro à esquerda para textos; pessoa falando à direita para imagens e voz. Funciona com clique, toque e teclado (Tab, Espaço ou Enter).
- Quatro fotos de exemplo geradas por IA: bolos, artesanato, produção de farinha e construção. São ilustrações fictícias das categorias, sem representar profissionais reais cadastrados.

A escolha do modo continua salva neste navegador. A troca durante o cadastro conserva respostas confirmadas e fotos selecionadas. Recarregar ou sair da página ainda descarta rascunhos não publicados, como antes.

## Atualizar a instalação

1. Encerre o servidor antigo com Ctrl+C e extraia este ZIP em outra pasta.
2. Se já possui cadastros, copie a pasta `instance` inteira do projeto anterior para a nova pasta `Batalha_Conecta_Python`, antes de iniciar. Conserve a pasta antiga até conferir seus dados.
3. Inicie o projeto e abra http://127.0.0.1:5000. Use Ctrl+F5 para atualizar os recursos visuais.

Se o Windows bloquear `iniciar_windows.bat`, abra o terminal **dentro da pasta que contém `app.py`**. Com Python 3.12 instalado e disponível no comando `python`, execute um comando por vez:

```powershell
python --version
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip install -r requirements-voz.txt
.\.venv\Scripts\python.exe app.py
```

Se `python --version` não funcionar ou mostrar outra versão, resolva a instalação do Python antes dos demais comandos. Não é necessário executar como administrador nem desativar a proteção do Windows. Este pacote não inclui Python instalado ou a pasta `.venv` de outro computador.

## Como trocar as imagens e as cores depois

Abra `GUIA_PERSONALIZACAO.md`. Ele mostra os arquivos atuais, o campo `imagem` e o indicador `imagem_ia` em `dados.py`. Coloque sua imagem em `static/artes/`, altere o nome do arquivo nessa categoria e mantenha o `id` da categoria.

As cores específicas do modo de imagens ficam em `static/visual-acessivel.css`. As cores gerais do modo com textos continuam em `static/estilo.css`.

## Conferência desta atualização

- 21 testes Python passaram: cadastro, busca, contatos, uploads, galeria de até cinco fotos, avaliações em áudio e narração com serviço simulado.
- 14 testes de lógica JavaScript passaram: interpretação e confirmação de respostas, tempo de escuta e recuperação após interrupções.
- Fluxos com navegador e microfone simulados passaram: troca de modo conserva respostas e fotos, publicação após autorização, avaliação com pausas e recuperação de falhas.
- O switch recebeu verificações de alternância rápida durante a narração, preferência ao reabrir a página, sincronização entre abas e funcionamento sem armazenamento local.

A inspeção visual em navegador ficou indisponível neste ambiente porque o navegador não acessou o servidor de teste. Não foram testados um celular físico, o microfone real, o serviço online de voz ou o envio externo pelo WhatsApp nesta atualização. Os testes usam dados temporários, que não estão neste ZIP.

Para a turma, confira os dois modos em um celular e peça que alguém identifique as ações pelos desenhos e pelo áudio. Observe principalmente se as categorias amplas, como Outros serviços, ficam compreensíveis com a foto escolhida.
