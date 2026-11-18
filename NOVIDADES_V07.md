# Batalha Conecta — atualização 0.7

Esta atualização acrescenta um **assistente de IA gratuito** ao cadastro por voz. Ele faz duas coisas que antes dependiam do navegador e de regras fixas: **ouvir** (transformar a fala em texto) e **entender** (descobrir o que a pessoa quis dizer). A parte de **falar** continua com as vozes neurais Francisca e Antônio, que já são gratuitas e em português do Brasil, e agora também leem as explicações que o assistente escreve.

## O que mudou

| Parte | Antes (0.6) | Agora (0.7, com a chave) |
| --- | --- | --- |
| Ouvir | Reconhecimento do navegador. Só funcionava bem no Chrome e errava com sotaque, ruído e pausas. | Whisper large-v3, pela Groq. Funciona em qualquer navegador que grave áudio, inclusive Firefox e Safari. |
| Fim da fala | A pessoa precisava dizer “terminei”. | O aplicativo percebe o silêncio sozinho. “Terminei” e o botão de confirmação continuam valendo. |
| Entender | Só frases exatas: “sim”, “corrigir nome”, “publicar agora”. | Um modelo de linguagem interpreta frases livres: “meu nome é Maria das Dores”, “vendo beiju e goma”, “não, é com i”, “quero mudar o bairro”. |
| Dúvidas | Repetia a mesma pergunta. | Explica com uma frase curta e pede de novo. |
| Falar | Francisca e Antônio. Se a voz demorasse mais de 2,5 s, entrava a voz mecânica do aparelho. | Francisca e Antônio, tocadas frase por frase. As perguntas são preparadas antes e guardadas. |

**Sem a chave, nada muda:** o aplicativo abre e funciona como na versão 0.6.

## A voz do aplicativo

A voz "mecânica" ouvida na 0.6 era, na maior parte das vezes, a **voz do aparelho** (Microsoft Maria ou Daniel, no Windows). O aplicativo trocava para ela sempre que a voz natural demorava mais de 2,5 segundos.

- **Só vozes brasileiras:** uma versão de teste usou a voz Thalita (`pt-BR-ThalitaMultilingualNeural`). Por ser "multilíngue", ela adivinha o idioma de cada frase e, em frases curtas ou com nomes, falava com sotaque estrangeiro. Foi retirada; Francisca é o padrão e Antônio continua em **Ajuda**.
- **Fala em partes:** o texto é dividido em frases. A primeira toca assim que fica pronta (cerca de 1 segundo) e as seguintes são preparadas enquanto ela toca.
- **Preparo antecipado:** ao abrir a conversa, o aplicativo já pede a voz das perguntas.
- **Falas guardadas:** perguntas e orientações ficam em `instance/voz-cache` e tocam sem espera, mesmo após reiniciar. Frases com dados de uma pessoa nunca são guardadas em disco.
- **Aviso falado mais curto:** o texto completo sobre privacidade continua na tela.

## A escuta (correções após o primeiro teste real)

| Problema relatado | Causa | Correção |
| --- | --- | --- |
| "Diz que não entendeu antes de eu começar a falar" | O microfone era aberto de novo a cada pergunta e levava até 1,5 s: o começo da fala se perdia. No silêncio, o Whisper inventava frases como "Obrigado." ou "Legenda por…", e a IA respondia que não tinha entendido. | O microfone abre uma vez por conversa e escuta 0,15 s após a pergunta. Frases inventadas no silêncio são descartadas. Se nada for ouvido, o aplicativo pergunta de novo uma vez antes de pausar. Ruído constante (ventilador, rua) não conta mais como fala. |
| "Muito lento" | Depois da última palavra, a escuta esperava 6 segundos de silêncio. A IA usava o modelo maior. As falas longas só tocavam depois de prontas inteiras. | Espera de 2 s (3 s na descrição, 3,5 s no telefone, 1,5 s para "sim"). Modelo menor e mais rápido primeiro (`gpt-oss-20b`), o maior de reserva. Fala em partes. |

Com o microfone aberto durante toda a conversa, o navegador mostra o aviso de microfone em uso até a conversa ser pausada, cancelada ou publicada.

## Confirmação rápida (com o assistente de IA)

Antes, cada resposta tinha uma rodada extra: "Entendi: Dona Rosa. Está certo? Diga sim ou repetir." e a pessoa precisava dizer "sim". Eram cinco rodadas a mais de ouvir, enviar e falar.

Agora o aplicativo repete o que anotou e já faz a próxima pergunta: "Anotei: Dona Rosa. Se estiver errado, diga não. Qual é a sua atividade?". Se a pessoa disser "não", "tá errado" ou "voltar", ele refaz a pergunta anterior. No final, **todas as respostas são lidas de novo** e nada é publicado sem a pessoa dizer "publicar"; ali ela pode dizer "corrigir nome", "corrigir telefone" etc.

Sem o assistente de IA (reconhecimento do navegador, que erra mais), a confirmação de cada resposta continua como antes.

## Atividades

A atividade **Farinha e derivados** foi retirada e entrou **Corte e costura**, para as costureiras da cidade. Agora são cinco: Bolos e comidas, Artesanato, Corte e costura, Serviços de manutenção e Outros serviços. Quem estava cadastrado em Farinha e derivados passa automaticamente para **Bolos e comidas**, que agora cita "farinha e goma" na explicação; nenhum perfil, foto ou avaliação se perde. No cadastro falado, dizer "farinha", "goma", "tapioca" ou "beiju" escolhe Bolos e comidas, e "costureira", "costura", "roupa" ou "bainha" escolhe Corte e costura.

A imagem de Corte e costura (`static/artes/costura.png`) é uma **ilustração** feita para o projeto (máquina de costura, tecido, linhas, tesoura e fita métrica), não uma foto. O desenho original está em `costura.svg`, nas cores do site. Pode ser trocada por uma foto de uma costureira de Batalha, com autorização dela (veja `GUIA_PERSONALIZACAO.md`). Quem já estava cadastrado como costureira em Outros serviços continua lá; para mudar, basta fazer um novo cadastro.

## Perfis de exemplo

Agora são 13 perfis fictícios, para o site parecer em uso: 4 em Bolos e comidas, 3 em Artesanato, 2 em Corte e costura, 3 em Serviços de manutenção e 1 em Outros serviços. Eles estão em `EXEMPLOS`, no arquivo `dados.py`, e voltam sozinhos sempre que o site reinicia.

Os telefones são inventados, no padrão (86) 90000-01xx. Como um número inventado pode pertencer a alguém de verdade, nos exemplos o número aparece na tela, mas os botões de WhatsApp e de ligação ficam desligados, com um aviso. Os perfis de exemplo continuam com a marca "Perfil fictício para demonstração".

## Cores

A paleta foi refeita a partir da logo: azul-marinho e verde, com âmbar para "ouvir" e terracota para "parar". O cabeçalho virou uma faixa azul-marinho que integra a logo. No modo Imagens e voz, as ações mantêm os mesmos significados (verde = falar, azul = procurar, âmbar = ouvir, terracota = parar), agora em tons que combinam; os cartões de atividade e o menu deixaram de ter uma cor cada. Detalhes em `GUIA_PERSONALIZACAO.md`, seção 7.

## Modo feira

Abra `iniciar_feira.bat` (depois de ter usado o `iniciar_windows.bat` pelo menos uma vez). O site abre igual, em http://127.0.0.1:5000, mas os cadastros de teste ficam na pasta `instance-feira`, separados dos cadastros de verdade da pasta `instance`. No final da feira, feche a janela e apague a pasta `instance-feira`.

Recomendações para o estande: fone com microfone (a feira é barulhenta), caixa de som, internet com o roteador do celular como reserva, e pedir aos visitantes dados fictícios (nome de personagem, sem telefone real), porque os perfis publicados ficam visíveis.

## Modo feira com QR code (no celular dos visitantes)

Abra `iniciar_feira_qrcode.bat`. Ele:

1. liga o site com os dados de teste em `instance-feira`;
2. cria um endereço HTTPS temporário (`https://….trycloudflare.com`) com o programa gratuito **cloudflared**, da Cloudflare, sem conta. Na primeira vez, ele pergunta se pode baixar o programa do site oficial no GitHub;
3. abre no navegador um **cartaz com o QR code**, pronto para mostrar na tela ou imprimir (fica salvo em `instance-feira/cartaz-qrcode.html`).

O celular só libera o microfone em endereços HTTPS; por isso o acesso pelo Wi-Fi (`servir.py --rede`, endereço `http://192.168…`) não serve para o cadastro falado.

Cuidados:

- **O endereço muda toda vez que o programa é aberto** e para de funcionar quando a janela é fechada ou o computador dorme. Imprima o cartaz só depois de abrir, e desative a suspensão do notebook durante a feira.
- **A Cloudflare indica esse túnel apenas para testes**, sem garantia de funcionamento. Tenha o modo notebook (`iniciar_feira.bat`) como plano B.
- **Poucas pessoas falando ao mesmo tempo:** o plano grátis da Groq aceita cerca de 20 gravações por minuto, o que dá umas 3 pessoas fazendo o cadastro juntas. Acima disso, o aplicativo avisa e passa para o reconhecimento do navegador.
- **Qualquer pessoa com o link acessa o site** enquanto a janela estiver aberta. Use dados fictícios e apague `instance-feira` no final.
- A rede da escola pode bloquear o túnel; o roteador do celular costuma funcionar.

## Moderação (página do professor)

O site não tem contas. Para tirar do ar um perfil falso ou uma avaliação ofensiva, existe a página **/moderacao** (por exemplo, `https://batalha-conecta.onrender.com/moderacao`), protegida por uma senha.

- **Ligar:** crie a variável `BATALHA_MODERACAO_SENHA` com uma senha de pelo menos 8 caracteres. No Render: serviço **batalha-conecta → Environment → Add Environment Variable**. No computador: uma linha no arquivo `.env`. Sem essa variável, a página não existe.
- **Usar:** abra /moderacao, digite a senha, marque **Confirmo** ao lado do que quer tirar e toque em **Apagar perfil** ou **Apagar avaliação**. Apagar um perfil leva junto as fotos, o áudio e as avaliações dele. Não há como desfazer.
- **Segurança:** a senha nunca vai para o GitHub. Depois de 10 senhas erradas em 10 minutos, a entrada fica fechada por 5 minutos. A sessão de moderação dura 2 horas.
- Os quatro perfis de exemplo voltam sozinhos quando o site reinicia.
- **Capas das atividades:** na mesma página, a seção "Capas das atividades" troca a imagem de cada atividade. A imagem enviada é cortada pelo centro no formato 3:2 e salva em `capas/` (dentro da pasta de dados), sem apagar a original; o botão **Voltar à original** desfaz a troca. Use fotos próprias ou com autorização de quem aparece.
- **Atenção no Render gratuito:** o disco é temporário, então as capas trocadas pela moderação voltam à original quando o site reinicia ou dorme (15 minutos sem uso). A página avisa isso. Para uma troca permanente, a imagem precisa entrar no projeto: substitua o arquivo em `static/artes/` e envie ao GitHub.

## Como ativar (grátis, sem cartão)

1. Abra https://console.groq.com/keys e crie uma conta.
2. Clique em **Create API Key** e copie a chave, que começa com `gsk_`.
3. Abra `configurar_ia_windows.bat` (ou execute `python configurar_ia.py`), cole a chave e pressione Enter. O programa guarda a chave no arquivo `.env` e faz um teste real.
4. Feche e abra de novo o `iniciar_windows.bat`.
5. Em **Ajuda**, confira o quadro “Assistente de inteligência artificial”: deve dizer **Ativo nesta instalação**.

O arquivo `.env` contém a chave. **Não envie esse arquivo a ninguém e não o coloque no ZIP nem no Git** (ele já está no `.gitignore`). Para desativar, apague o `.env` e reinicie.

Opcional: no `.env`, a linha `BATALHA_IA_VOCABULARIO=` aceita nomes de bairros, povoados e produtos da região, separados por vírgula. Eles ajudam a IA a escrever certo o que ouviu. Veja `.env.exemplo`.

## Limites do plano gratuito

Conferidos em novembro de 2026; a Groq pode alterá-los.

- Escuta (`whisper-large-v3`): 20 pedidos por minuto e 2.000 por dia.
- Entendimento (`openai/gpt-oss-20b`, mais rápido, com `openai/gpt-oss-120b` de reserva): 30 pedidos por minuto e 1.000 por dia cada.

Um cadastro completo usa cerca de 10 a 15 pedidos de cada tipo. Dá para dezenas de cadastros por dia, mas **não para a turma inteira falando ao mesmo tempo com a mesma chave**. Quando o limite é atingido, o aplicativo avisa e continua com o reconhecimento do navegador e as regras fixas. Se a Groq trocar os modelos gratuitos, mude os nomes no `.env`, sem mexer no código.

## Segurança e privacidade

- A gravação de cada resposta é enviada pela internet à Groq, uma empresa de fora do Brasil. O Batalha Conecta não guarda esse áudio. A tela de cadastro e a página Ajuda avisam a pessoa antes de ela falar.
- **A IA sugere, o aplicativo confere.** Nada é publicado sem a pessoa ouvir o resumo e autorizar. As regras estão em `ia.py`, função `conferir`:
  - nome e comunidade só valem se todas as palavras foram ditas pela pessoa;
  - o telefone precisa bater, dígito a dígito, com os números falados;
  - a categoria precisa ser uma das cinco existentes;
  - “publicar” exige que a pessoa tenha dito publicar, autorizar ou divulgar, sem “não” na frase;
  - “cancelar” exige a palavra dita.
- A chave fica só no servidor. O navegador nunca a recebe.

## Para estudar com a turma

- `ia.py`: o agente. `transcrever` (ouvir), `entender` (pedir ao modelo) e `conferir` (validar a resposta).
- `static/escuta-ia.js`: grava no navegador e detecta o silêncio pelo volume.
- `static/cadastro-voz.js`: decide quando usar a IA e quando usar as regras fixas (`voz-logica.js`, função `clara`).
- `tests/simulacao_ia.py`: a IA de mentira usada nos testes. Bom exemplo de como testar sem internet.

## Verificação

Ambiente: Python 3.12 em Linux, com Node para os testes de interface.

- **53 testes Python** passaram (`python -m pytest -q` ou `python -m unittest discover -s tests`).
- **28 testes JavaScript** de lógica e escuta passaram (`npm run test:voz`).
- **Cenários de interface** passaram em navegador simulado (`python verificar_interface.py`), incluindo conversa natural com a IA, recusa de dado inventado, negação que não publica, queda do serviço e permissão de microfone negada.

**Limite importante:** nesses testes os serviços externos são simulados. A conexão real com a Groq foi conferida em uma instalação (entender e ouvir responderam), mas não com microfone de verdade. A voz Thalita consta na lista do serviço, e a qualidade só se julga ouvindo. Faça um cadastro falado completo antes de demonstrar para a turma.

## Como atualizar preservando os cadastros

Siga os mesmos passos de `NOVIDADES_V06.md`: copie a pasta `instance` antiga para dentro da nova pasta antes da primeira execução. Se já tiver um `.env`, copie-o também.
