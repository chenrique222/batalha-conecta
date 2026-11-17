# Batalha Conecta: ícones e cadastro por voz

Esta atualização mantém o projeto em Flask/SQLite e acrescenta uma forma de usar as telas sem depender da leitura. É uma versão para experimentar com a turma.

## 1. Duas opções, uma escolha

| Opção | Como a pessoa usa |
| --- | --- |
| Interruptor à direita: **Imagens e voz** | Figuras, fotos e botões grandes; alto-falantes explicam as ações; o cadastro abre a conversa. |
| Interruptor à esquerda: **Textos** | Títulos, descrições e formulário escrito. Também permite preencher falando. |

O seletor é um único botão switch: cada toque move a bolinha entre o livro (textos) e a pessoa falando (imagens e voz). Também funciona com Tab, Espaço e Enter. Os nomes descrevem a interface, sem classificar a pessoa pela escolaridade.

A escolha fica no navegador do aparelho. Trocar de página conserva o modo. Outro aparelho pode ter outra preferência. Se o armazenamento do navegador estiver bloqueado, o seletor ainda funciona na página aberta. Os rótulos continuam disponíveis para leitores de tela mesmo quando não aparecem visualmente.

Na tela inicial, a pessoa falando no botão verde abre o cadastro; as pessoas com uma lupa no botão azul abrem a busca. Os alto-falantes explicam as opções. As ilustrações filtram por atividade. Na lista de perfis, o alto-falante lê a apresentação e a seta abre os detalhes. Não exigimos escrever uma busca no modo com ícones.

## 2. Abrir e testar no computador

1. Extraia o ZIP. Para experimentar, use uma pasta separada da instalação que já guarda seus cadastros.
2. Execute `iniciar_windows.bat` e abra **http://127.0.0.1:5000**.
3. Use um navegador que ofereça reconhecimento de fala; comece o teste pelo Chrome atualizado. Nem todo navegador ou instalação disponibiliza o serviço.
4. Toque no interruptor até a bolinha ficar à direita, junto à pessoa falando: **Imagens e voz**.
5. Toque na pessoa falando da tela inicial e depois no microfone grande da conversa.
6. Ouça a explicação inicial e permita o microfone quando o navegador pedir.
7. Responda depois do sinal sonoro e da mudança de aparência do botão. Faça pausas e, ao acabar, diga “terminei” ou toque na marca de confirmação. Não fale enquanto o sistema lê a pergunta.

O toque inicial e a permissão do navegador são necessários. Depois deles, o fluxo foi preparado para receber as respostas e confirmações por voz, sem digitação. Se o navegador encerrar um trecho normalmente, a escuta tenta retomar preservando o texto. Se houver bloqueio de permissão ou falha de rede, mostra uma orientação e permite retomar pelo microfone. Também há botões para confirmar e repetir.

## 3. Uma pergunta por vez

| Etapa | Exemplo de resposta fictícia |
| --- | --- |
| Nome | “Bolos da Rosa de teste” |
| Atividade | “Comidas” |
| Apresentação | “Faço bolos de milho por encomenda” |
| Bairro ou comunidade | “Centro” |
| WhatsApp com DDD | “Pular”, para testar sem divulgar nenhum contato |

Com o assistente de IA ativo, após cada resposta o aplicativo diz **“Anotei…”** e já faz a próxima pergunta; para corrigir, a pessoa diz **“não”** logo em seguida. Sem a IA, o assistente diz **“Entendi… Está certo?”** e a pessoa responde **“sim”** ou **“repetir”**. Nos dois casos, tudo é lido de novo antes de publicar. A atividade também pode ser escolhida por figura.

As atividades são **Bolos e comidas** (inclui farinha, goma e tapioca), **Artesanato**, **Serviços de manutenção** e **Outros serviços**. Dizer “pedreiro” seleciona manutenção. Outros serviços recebe atividades que não se encaixam nas demais; a foto de barbearia é só um exemplo. “Trabalho rural” deixou de ser uma opção ampla: o assistente pede uma atividade específica.

Para testar o telefone sem publicar um número, dite DDD e número **um dígito por vez**, confira a leitura e cancele o cadastro no final. “Meia” é interpretado como 6. Números incompletos e trechos que o sistema não entende são recusados; ele pede que a pessoa repita. Não presumimos que o reconhecimento esteja correto.

No final, o sistema lê todo o perfil e avisa que os dados, incluindo o contato informado, serão visíveis para quem acessar o projeto. Só então aceita **“publicar”** ou o botão de autorização. Dizer apenas “sim” nessa etapa não publica.

| Comando | Resultado |
| --- | --- |
| “Terminei” | Encerra a resposta atual e pede sua conferência. Não publica. |
| “Sim” | Confirma uma resposta que acabou de ser lida. |
| “Repetir” | Refaz a pergunta quando a resposta está em confirmação. |
| “Ouvir de novo” | Repete a orientação atual. |
| “Corrigir nome” | Na revisão, volta ao nome. |
| “Corrigir atividade/descrição/comunidade/telefone” | Na revisão, corrige o campo escolhido e lê o resumo novamente. |
| “Pausar” | Interrompe a escuta; o microfone permite retomar. |
| “Cancelar cadastro” | Apaga o rascunho da conversa e não publica. |
| “Publicar” | Na revisão final, autoriza a divulgação e envia ao Python. |

Trocar para Textos pausa a conversa e conserva as respostas confirmadas nos campos escritos. Ao voltar para a conversa, as alterações digitadas válidas são incorporadas; o assistente pergunta o que falta e lê a revisão antes de publicar. As fotos ficam disponíveis nos dois modos. Na revisão por voz, toque na câmera para escolher até cinco fotos. A seleção pausa a conversa para permitir a escolha no aparelho. Ao voltar, use o microfone ou o botão de publicar. A apresentação gravada separadamente continua sendo um recurso do formulário manual. Os rascunhos não são guardados após recarregar ou sair da página.

## 4. Cadastro sem e-mail: o que foi implementado

O cadastro cria um **perfil de trabalho na vitrine**. Não pede e-mail nem senha. O telefone é opcional: uma pessoa sem número também pode criar uma apresentação. Se houver contato, o perfil exibe atalhos para WhatsApp e ligação. O aplicativo não envia mensagem automaticamente nem verifica se o número tem WhatsApp.

O assistente salva a **transcrição confirmada**, sem anexar a gravação original. Se não houver fotos, usa a ilustração da atividade. Para incluir fotos, use a câmera na revisão final da conversa. Para acrescentar uma apresentação gravada separadamente, use o formulário com textos. Os dados das duas modalidades chegam à mesma rota Python e ao mesmo banco.

**Ainda não há login, recuperação de conta ou comprovação de que o telefone pertence à pessoa.** O navegador que criou um perfil pode gerenciar suas fotos durante a sessão. A alteração dos demais dados e a exclusão do perfil ainda não estão disponíveis. Informar um número não deve liberar o controle de um perfil. Essa distinção evita apresentar a vitrine como se já fosse um sistema de contas.

Para a próxima etapa de contas, uma proposta é usar telefone e confirmação de posse por um provedor de autenticação, com instruções faladas. A escolha do provedor, a experiência de confirmação e eventuais custos ainda precisam ser definidos. Não use a voz como senha nem reconheça uma pessoa apenas pelo timbre. Para esta versão escolar, o cadastro acompanhado e dados fictícios permitem testar o fluxo antes dessa integração.

## 5. O que cada parte faz

| Arquivo | Responsabilidade |
| --- | --- |
| `templates/base.html` | Coloca o switch de modo em todas as páginas. |
| `static/modo.js` | Recupera a preferência antes de exibir a página. |
| `static/acessibilidade.js` | Troca o modo e guarda a preferência. |
| `static/visual-acessivel.css` | Define o switch, as cores e os tamanhos do modo de imagens. |
| `static/estilo.css` | Oculta textos visualmente no modo de ícones e amplia controles. |
| `templates/cadastro.html` | Organiza os botões e as figuras da conversa. |
| `static/voz-logica.js` | Define perguntas e confere respostas, categorias e números. |
| `static/cadastro-voz.js` | Alterna pergunta, escuta, confirmação, revisão e envio. |
| `app.py` | Confere os campos, a sessão e a autorização antes de salvar. |
| `dados.py` | Grava o cadastro no SQLite, como na versão anterior. |

Python continua responsável pelas regras e pelos dados. JavaScript é necessário aqui porque o microfone, a leitura em voz alta e os cliques pertencem ao navegador. Não é preciso instalar Node para usar o projeto.

A narração usa o serviço online do Microsoft Edge através de `edge-tts`. Em Ajuda, a pessoa escolhe Francisca, Antônio ou **Voz rápida do aparelho**. Para gerar textos novos com uma voz natural, o texto é enviado ao serviço externo. As amostras de Ajuda são locais; áudios já preparados podem ser reaproveitados em memória. Se a voz online demorar mais de 2,5 segundos ou falhar, o app tenta a voz do aparelho e evita consultar o serviço lento nas próximas perguntas por 30 segundos. A alternativa depende de haver uma voz disponível no navegador.

O tempo de escuta não foi encurtado para acelerar a narração. Quando acabar sua resposta, diga **“terminei”** para não aguardar toda a pausa; isso ainda não publica o perfil. O assistente usa perguntas fixas e o reconhecimento do navegador. Ele não escreve uma descrição inventada nem é uma IA generativa treinada pela turma. Não foi contratado serviço pago nem inserida chave de API. Isso não garante disponibilidade permanente do serviço de reconhecimento ou ausência de custos de internet e hospedagem.

## 6. Atividade com os alunos

Como a turma estudou até estruturas de repetição, primeiro trabalhe a ideia de **perguntar → conferir → repetir se necessário** em Python:

```python
confirmacao = "não"

while confirmacao != "sim":
    nome = input("Qual é o nome do trabalho? ")
    print("Entendi:", nome)
    confirmacao = input("Está certo? Digite sim para confirmar: ").strip().lower()

print("Nome confirmado:", nome)
```

Este exercício roda no terminal e usa texto. No aplicativo, o reconhecimento fornece a resposta e a voz faz a pergunta, mas a necessidade de conferir antes de prosseguir é a mesma.

Em seguida, mostre a tabela de perguntas em `voz-logica.js`, sem exigir que a turma já domine eventos, funções assíncronas ou APIs. Peça que identifiquem os campos que o Python recebe. Use duas pessoas para testar: uma utiliza o sistema e a outra anota dúvidas, repetições e dificuldades. Avalie a clareza da interface, não a capacidade de leitura da pessoa.

## 7. O que conferir no celular

- O site deve usar **HTTPS**. O HTTP com IP da rede local serve para algumas telas, mas não é suficiente para este assistente. `localhost` no computador é uma exceção para desenvolvimento; no celular, ele aponta para o próprio celular.
- Confira se o aparelho oferece uma voz em português, se o volume está audível e se o serviço de reconhecimento está disponível.
- O navegador pode enviar a fala a um serviço externo para transcrição. A explicação inicial informa isso antes da escuta.
- Faça testes de sotaque, fala lenta, número ditado, ruído, silêncio, recusa de permissão, perda de internet, correção e cancelamento.
- O sistema pausa ao sair para outra aba e ao trocar de modalidade. Confirme que o indicador de uso do microfone deixa de aparecer.
- Ícones não têm significado universal. Observe se as pessoas reconhecem as figuras e entendem os áudios antes de considerar a experiência pronta.

Sem reconhecimento disponível, há ajuda falada e um botão para abrir o formulário acompanhado. Se o aparelho também não conseguir produzir voz, será preciso apoio ou mudança de aparelho; essa situação não é resolvida apenas ocultando textos.

## Referências

- Reconhecimento de fala e limites de compatibilidade: https://developer.mozilla.org/en-US/docs/Web/API/SpeechRecognition
- Microfone, contexto seguro e permissão: https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia
- Rótulos acessíveis para botões sem texto visual: https://www.w3.org/WAI/WCAG22/Techniques/aria/ARIA14

## 8. Fotos e avaliações na versão 0.4

A câmera na revisão do cadastro abre o seletor de fotos. A pessoa pode escolher uma de cada vez ou várias juntas, até cinco. Cada miniatura tem um xis para remover uma escolha antes do envio. No perfil, toque numa miniatura para ampliar. As setas percorrem as fotos.

Na área de avaliações, o alto-falante explica as estrelas e os controles. O microfone inicia a gravação, o quadrado encerra e o botão de reprodução permite ouvir. A gravação espera as pausas da pessoa e termina com o botão ou após dois minutos. Só o botão de autorização publica a voz. A nota vai de uma estrela (ruim) a cinco (excelente). O nome é opcional. O áudio publicado é a voz da pessoa, não uma transcrição nem uma narração artificial.
