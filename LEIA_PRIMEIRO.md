> Atualização 0.7: assistente de IA gratuito para ouvir e entender o cadastro por voz. Ative em poucos minutos seguindo `NOVIDADES_V07.md`. Sem a chave, o aplicativo funciona como na 0.6.
>
> Atualização 0.6: logo completa, favicon do mapa, nova frase, categorias reorganizadas e menor espera pela voz. Veja `NOVIDADES_V06.md` para atualizar preservando seus cadastros e `GUIA_PERSONALIZACAO.md` para editar o visual.

# Batalha Conecta · versão 0.7

Versão funcional para estudar e demonstrar com a turma de Desenvolvimento de Sistemas.

Esta versão usa as vozes neurais brasileiras **Francisca** e **Antônio**, via `edge-tts`, e mantém **avaliações em áudio** e **galeria de até cinco fotos por perfil**. Em **Ajuda**, ouça e escolha a narração. As vozes naturais precisam de internet para textos novos e enviam o texto a ser narrado ao serviço da Microsoft. A fala toca frase por frase; se uma parte falhar ou passar de 5 segundos, o app tenta a voz do aparelho. A opção **Voz rápida do aparelho** evita essa espera desde o início. As amostras de Ajuda já acompanham o pacote.

Escolha entre **Imagens e voz** (pessoa falando) e **Textos** (livro) no interruptor no topo da tela. O cadastro por voz faz perguntas, lê as respostas, permite correções e publica após autorização. Não exige e-mail. Leia `GUIA_ICONES_E_VOZ.md` para testar com a turma, conhecer os comandos e distinguir cadastro de perfil de acesso a uma conta.

Extraia o ZIP, instale Python 3.12 de 64 bits e execute `iniciar_windows.bat`. Depois abra **http://127.0.0.1:5000**.

O cabeçalho usa a logo completa enviada pelo professor e a frase “Valorizando o serviço da nossa gente”. O mapa identifica o favicon. A paleta combina azul sóbrio, verde suave e fundos claros. Leia `GUIA_PERSONALIZACAO.md` para trocar imagens, cores e textos. Tem página inicial, busca por atividade/nome/comunidade, perfis, cadastro em etapas, galeria, apresentação e avaliações por áudio, contatos, leitura de orientações e arquivos de instalação como PWA.

Os quatro perfis iniciais são fictícios, não têm telefone e usam ilustrações. A opção “Ouvir descrição” usa a voz neural escolhida; se indisponível, tenta a voz do aparelho. É uma leitura sintetizada, não uma gravação da pessoa. Para demonstrar a voz de um trabalhador, crie um perfil e grave ou envie um áudio.

No novo assistente, a fala vira texto e o áudio original não é anexado ao perfil. A gravação de apresentação continua disponível no formulário com textos. Sem configuração, o assistente usa o reconhecimento do navegador, que pode depender de internet e varia por navegador. Com uma chave gratuita da Groq, um assistente de IA passa a ouvir e a entender as respostas com mais acerto, em qualquer navegador que grave áudio; a voz é enviada a esse serviço externo. O pacote não traz chave: veja `NOVIDADES_V07.md`.

## 1. Abrir no Windows

1. Clique com o botão direito no ZIP e escolha **Extrair tudo**. Entre na pasta extraída `Batalha_Conecta_Python`.
2. Se precisar, instale Python 3.12 de 64 bits. Se o gerenciador `py` disser que a versão não está instalada, execute `py install 3.12` e confira com `py -3.12 --version`. [Python para Windows](https://www.python.org/downloads/windows/)
3. Abra `iniciar_windows.bat`. Na primeira execução, ele prepara o ambiente e baixa as dependências. Essa etapa usa internet.
4. Abra http://127.0.0.1:5000 no navegador.
5. Mantenha a janela do terminal aberta. Use **Ctrl+C** para encerrar.

Alternativa pelo terminal do VS Code, aberto dentro da pasta do projeto:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip install -r requirements-voz.txt
.\.venv\Scripts\python.exe preparar_voz.py
.\.venv\Scripts\python.exe app.py
```

Os comandos usam diretamente o Python da pasta `.venv`. O iniciador usa `.venv-v04` se encontrar um ambiente `.venv` antigo incompatível. A instalação de `requirements-voz.txt` habilita a voz natural. `preparar_voz.py` é um teste opcional que gera amostras das duas vozes. O app também abre sem a voz natural, usando a voz disponível no aparelho.

Se `py` não existir e `python --version` mostrar a versão correta, substitua `py -3.12` por `python` no primeiro comando. Se a porta 5000 já estiver ocupada, encerre a outra execução do projeto ou use:

```powershell
.\.venv\Scripts\python.exe -m flask --app app run --debug --port 5002
```

Nesse caso, abra http://127.0.0.1:5002.

No macOS/Linux, os comandos equivalentes são:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip install -r requirements-voz.txt
.venv/bin/python preparar_voz.py
.venv/bin/python app.py
```

## 2. Programar e acompanhar o resultado

Abra a pasta no VS Code e deixe o navegador ao lado. Com `app.py` em execução:

- Altere um texto em `templates/inicio.html`, salve com Ctrl+S e atualize o navegador com F5.
- Altere cores e tamanhos em `static/estilo.css`, salve e atualize a página.
- Altere uma regra em Python e salve. O servidor de desenvolvimento reinicia automaticamente; atualize o navegador para fazer uma nova solicitação.
- Confira o terminal se aparecer um erro.

O navegador não recebe atualização automática a cada tecla digitada. O ciclo é **editar → salvar → atualizar → testar**. Para JavaScript ou CSS que pareça antigo, use Ctrl+F5.

O Figma serve como referência visual. Alterações no Figma não são copiadas automaticamente para o código.

## 3. Testar o primeiro fluxo

1. Na tela inicial, escolha **Procurar um serviço**.
2. Pesquise `joao`: o perfil “Farinha do Seu João” deve aparecer, mesmo sem o acento na pesquisa.
3. Selecione **Artesanato** e abra “Artes da Rosa”.
4. Use **Ouvir descrição**. A narração usa a voz neural escolhida; se falhar, aparece um aviso de uso da voz do aparelho.
5. Volte ao início e escolha **Mostrar meu trabalho**.
6. Selecione uma atividade; informe um nome fictício e descreva o trabalho por texto ou por áudio.
7. Acrescente até cinco fotos JPG, PNG ou WebP, com até 5 MB cada. Fotos são opcionais. A descrição em texto ou a apresentação em áudio é obrigatória.
8. Informe uma comunidade. O telefone é opcional. Deixe vazio para evitar contatos reais durante a aula.
9. Confira, marque a confirmação e publique.
10. Abra a mesma aplicação em outra aba ou janela e faça uma nova busca: o perfil deverá aparecer.
11. Encerre o programa, inicie novamente e procure o perfil. Ele continua salvo.

O arquivo `instance/batalha.db` é criado automaticamente. A pasta `instance/uploads` guarda fotos e áudios. A chave de sessão também é criada dentro de `instance`. Preserve essa pasta para manter os dados; ela não acompanha o ZIP original.

## 4. Como site e app trabalham juntos

Esta versão é uma **aplicação web progressiva (PWA)**: o mesmo site pode ganhar um ícone no celular e abrir em uma janela própria, quando o navegador permite a instalação.

| Parte | Função |
| --- | --- |
| Navegador do computador | Mostra o site com layout mais largo. |
| Navegador ou PWA do celular | Mostra a mesma aplicação adaptada a uma tela pequena. |
| Flask, no servidor Python | Recebe as buscas e os cadastros de todos os aparelhos. |
| SQLite, no servidor | Guarda uma única lista compartilhada de profissionais. |
| Pasta de arquivos do servidor | Guarda as fotos e os áudios dos perfis. |

**Exemplo:** um cadastro enviado pelo celular é salvo no servidor. Ao atualizar a lista no computador, o perfil aparece. Não é necessário copiar o cadastro entre duas aplicações.

Esta versão não faz atualização instantânea por WebSocket: a lista muda ao abrir a página, atualizar ou fazer uma nova busca. Também não envia cadastros offline; se a conexão falhar, o formulário mostra a falha e permite tentar novamente.

Abrir o projeto separadamente em dois computadores cria dois bancos separados. Para compartilhar dados, todos devem acessar **a mesma instalação** por seu endereço.

### Teste em aparelhos da mesma rede

Pare a execução anterior com Ctrl+C e execute:

```powershell
.\.venv\Scripts\python.exe servir.py --rede
```

No Windows, execute `ipconfig` para encontrar o endereço IPv4 da conexão Wi-Fi. Se ele for, por exemplo, `192.168.1.20`, abra **http://192.168.1.20:5000** no celular conectado à mesma rede. Esse IP é apenas um exemplo: use o mostrado pelo seu computador. No celular, `localhost` aponta para o próprio celular.

Se necessário, permita o acesso do Python na rede privada do Windows. Redes escolares com isolamento entre aparelhos podem impedir a conexão; isso precisa ser verificado com a equipe responsável pela rede. O computador que executa Python precisa continuar ligado.

Esse endereço HTTP da rede serve para testar telas, busca e cadastro. **Gravação direta pelo microfone e instalação completa como PWA exigem HTTPS ou localhost em navegadores compatíveis.** Na rede HTTP, use um arquivo de áudio já salvo como alternativa.

### Para disponibilizar na internet

A publicação ainda não foi feita. Precisaremos de uma hospedagem que execute Python/Flask, forneça HTTPS e mantenha os dados permanentemente.

Uma instalação única pode usar SQLite em disco persistente. Se houver múltiplas instâncias de servidor ou maior volume de acessos, migre os dados para um banco compartilhado como PostgreSQL e os arquivos para armazenamento persistente compartilhado. O banco não deve ficar em um disco temporário que seja apagado a cada publicação.

`servir.py` usa Waitress, sem depurador. Um comando possível em um servidor com porta configurada é `python servir.py --rede --porta 8080`. A plataforma de hospedagem deve cuidar do HTTPS e encaminhar o tráfego para esse servidor. Não publique usando o depurador de `app.py`.

O cadastro desta versão é aberto para demonstração. O navegador que criou um perfil pode gerenciar suas fotos enquanto a sessão estiver ativa. Ainda não há conta recuperável, comprovação de titularidade, alteração dos outros dados ou exclusão de avaliações pela interface. Antes de abrir para uso real na cidade, precisamos desenvolver identificação dos responsáveis pelos perfis, edição/exclusão autorizada, moderação e backups. Isso faz parte da próxima versão, não está implementado neste pacote.

### Instalar no celular

Depois de haver um endereço HTTPS:

- Android: abra o endereço e use **Instalar aplicativo** ou **Adicionar à tela inicial**, conforme o navegador.
- iPhone: abra no Safari, use **Compartilhar → Adicionar à Tela de Início**.

A instalação pela loja de aplicativos é um trabalho adicional. O pacote entregue implementa a base PWA e os arquivos de instalação; a confirmação da instalação e do microfone precisa ser feita nos celulares que serão usados na feira.

Quando não há conexão, o app exibe uma tela de aviso. Os perfis não são armazenados para consulta offline nesta versão.

## 5. Onde mudar cada coisa

| Arquivo | O que estudar ou alterar |
| --- | --- |
| `app.py` | Endereços das páginas, validação e recebimento do cadastro. |
| `dados.py` | Categorias, exemplos e comandos de banco de dados. |
| `templates/inicio.html` | Tela inicial. |
| `templates/profissionais.html` | Lista, busca e categorias. |
| `templates/perfil.html` | Galeria, apresentação, contato e avaliações. |
| `templates/cadastro.html` | Campos e etapas do cadastro. |
| `templates/base.html` | Cabeçalho e navegação comuns às telas. |
| `static/estilo.css` | Cores, letras, espaçamento e adaptação ao celular. |
| `static/app.js` | Gravação manual, etapas, prévias e envio do formulário. |
| `voz.py`, `preparar_voz.py` e `vozes/` | Síntese neural online, teste de conexão e amostras. |
| `static/galeria.js` | Seleciona, remove e amplia fotos. |
| `static/avaliacoes.js` | Grava, confere e publica avaliações em áudio. |
| `static/voz-audio.js` | Reprodução da voz do servidor e alternativa pela voz do aparelho. |
| `static/escuta.js` | Reúne trechos ditados, tolera pausas e controla o tempo de resposta. |
| `static/modo.js` e `static/acessibilidade.js` | Escolha e memorização do modo de apresentação. |
| `static/voz-logica.js` | Perguntas, reconhecimento de categorias e conferência de números ditados. |
| `static/cadastro-voz.js` | Conversa, confirmações, pausa, correções e envio do cadastro por voz. |
| `GUIA_ICONES_E_VOZ.md` | Roteiro de demonstração e limites da versão 0.6. |
| `NOVIDADES_V07.md` | Como ativar o assistente de IA gratuito, limites e privacidade. |
| `static/manifest.webmanifest` | Nome, ícone e modo de abertura do PWA. |
| `static/sw.js` | Exibição do aviso quando o servidor fica indisponível. |
| `aulas/` | Quatro exemplos curtos para aprender antes do projeto completo. |
| `GUIA_DO_PROFESSOR.md` | Sequência de ensino, demonstrações e exercícios. |
| `tests/test_app.py` | Verificações automatizadas de comportamentos importantes. |

Os exemplos só são inseridos se ainda não existirem. Alterar o texto de um exemplo em `dados.py` não substitui um registro já salvo. Para aulas iniciais, faça mudanças na tela ou crie um novo cadastro pelo formulário.

## 6. Verificações

Na pasta principal:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Os 25 testes Python verificam cadastro, busca, galeria de cinco fotos, migração de fotos e categorias antigas, alteração autorizada da galeria, avaliações, prevenção de duplicação e narração com o serviço simulado. Incluem o reaproveitamento de áudios sem bloqueio por outro pedido lento.

Voz audível, permissão de microfone, ligação, abertura do WhatsApp e instalação no celular precisam de teste no aparelho. Os testes não fazem ligações nem enviam mensagens.

As regras da conversa e da escuta têm 28 testes opcionais, executados com `npm run test:voz`. Para testar também a interface com navegador simulado, instale as dependências de desenvolvimento com `npm install` e execute `.\.venv\Scripts\python.exe verificar_interface.py`. Esses testes usam dados temporários. Node não é necessário para abrir o aplicativo. Consulte `NOVIDADES_V07.md` para os resultados e limites dos testes desta atualização.

## Referências técnicas

- Flask: https://flask.palletsprojects.com/en/stable/quickstart/
- SQLite com Flask: https://flask.palletsprojects.com/en/stable/tutorial/database/
- Publicação do Flask: https://flask.palletsprojects.com/en/stable/deploying/
- PWA instalável: https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps/Guides/Making_PWAs_installable
- Narração neural usada pelo projeto: https://github.com/rany2/edge-tts
- Microfone e permissões: https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia

As fotografias de exemplo foram geradas por IA e não retratam os profissionais cadastrados. A logo foi fornecida pelo professor. Consulte `ORIGEM_IMAGENS_V06.md` para os recursos visuais e suas origens.
