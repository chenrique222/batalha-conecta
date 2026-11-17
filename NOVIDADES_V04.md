# Batalha Conecta · Atualização 0.4

## Como abrir sem perder os cadastros

1. Feche a versão anterior usando Ctrl+C na janela do Python.
2. Extraia o novo ZIP em outra pasta.
3. Se quiser manter os cadastros já feitos, **copie a pasta inteira `instance` da versão anterior** para dentro da nova pasta `Batalha_Conecta_Python`, antes de abrir o app. Ela contém o banco, as fotos, os áudios e a chave da instalação. Guarde a pasta anterior como cópia de segurança. Se estiver usando `BATALHA_DADOS`, mantenha o mesmo caminho configurado.
4. Abra `iniciar_windows.bat`. A primeira instalação exige internet. Não copie ambientes `.venv` entre pastas.
5. Abra **http://127.0.0.1:5000** no computador e pressione Ctrl+F5 se as telas parecerem antigas.

Se aparecer que o Python 3.12 não está instalado, use `py install 3.12` no PowerShell e depois confira com `py -3.12 --version`. O iniciador também tenta usar outra versão compatível já instalada.

O banco cria as novas tabelas sem apagar os perfis. A foto dos cadastros antigos passa a ser a primeira foto da galeria. Não há reinicialização do banco nesta atualização.

## 1. Nova narração

O pacote usa `edge-tts` com as vozes brasileiras **Francisca** e **Antônio**. O Piper e o ONNX Runtime deixaram de ser dependências. Francisca é a voz inicial. Em **Ajuda → Escolha a voz que prefere**, toque em cada opção para ouvir e escolher. A preferência fica salva neste navegador.

As duas vozes naturais precisam de internet. O texto a ser lido é enviado ao serviço de voz da Microsoft. A biblioteca não pede uma chave de API neste fluxo. É uma integração comunitária com um serviço externo, cuja disponibilidade pode mudar. Se houver falha, o aplicativo informa e tenta a voz do aparelho. A opção de usar diretamente a voz do aparelho também fica em Ajuda.

As amostras `vozes/amostra-francisca.mp3` e `vozes/amostra-antonio.mp3` acompanham o pacote. Elas permitem comparar as vozes mesmo antes de abrir o projeto. São exemplos fixos. As perguntas e descrições do aplicativo são sintetizadas quando necessárias, com cache pequeno na memória do servidor.

## 2. Avaliação em áudio

1. Abra o perfil do profissional e vá até **Quem contratou conta**.
2. Escolha de **1 a 5 estrelas**. O nome é opcional.
3. Toque no microfone e permita seu uso. Conte se o serviço foi bem executado, se valeu a pena e se contrataria novamente.
4. Toque no quadrado **Terminei**. A gravação aceita pausas e vai até **2 minutos**. Ela não termina ao detectar silêncio.
5. Ouça a prévia. Se precisar, use **Gravar novamente**.
6. Toque em **Autorizar e publicar avaliação**. O comentário e as estrelas passam a aparecer no perfil.

É possível escolher um áudio salvo no aparelho, de até **10 MB**. O limite de dois minutos controla a gravação feita pelo app. Para arquivos já existentes, o servidor valida o tamanho e o formato, sem medir a duração. Os formatos aceitos são MP3, M4A, WAV, OGG e WebM.

Não é necessário e-mail, login ou serviço de transcrição. O áudio é enviado ao servidor do projeto e fica disponível a quem acessar o perfil. O botão de parar não publica a avaliação. O app evita duplicar a mesma tentativa de envio. Se a conexão falhar, mantém o áudio na página para tentar de novo. Recarregar ou fechar a página descarta um áudio ainda não enviado.

As avaliações são relatos dos visitantes. Não há comprovação da contratação nem moderação implementada nesta versão escolar. Não apresente as estrelas como avaliações verificadas.

## 3. Galeria de até cinco fotos

No formulário com textos, a seleção aparece em **Apresente seu trabalho**. Na conversa por voz, aparece na **revisão final**, antes de publicar. Toque na câmera para escolher imagens. A conversa pausa durante a escolha.

- Até **5 fotos por perfil**, com **5 MB por foto**.
- Formatos JPG, PNG e WebP.
- Escolha várias de uma vez ou acrescente aos poucos.
- O xis remove uma foto antes do envio.
- A primeira imagem será a capa do perfil.
- No perfil, toque nas miniaturas para ampliar e use as setas para navegar.

As imagens são redimensionadas para até 1400 × 1400 pixels, convertidas em WebP e salvas sem os metadados originais. O servidor também verifica o limite de cinco, inclusive quando chegam envios simultâneos.

Após criar um perfil, o mesmo navegador mostra **Gerenciar minhas fotos**. Marque as imagens que deseja remover, acrescente outras e toque em **Salvar fotos**. Essa permissão depende da sessão do navegador. Não é uma conta recuperável. Perfis criados em versões anteriores não recebem autorização de edição automaticamente. Os demais visitantes podem consultar a galeria e avaliar o serviço, mas não alterar fotos do perfil.

## 4. Computador e celular

No computador que executa Python, abra `http://127.0.0.1:5000` e permita o microfone. Para gravar no celular, o endereço do site precisa usar **HTTPS**. Abrir o IP do computador por HTTP não equivale a abrir localhost no computador. Sem gravação disponível, use um arquivo de áudio já salvo.

Site e PWA usam o mesmo Python e o mesmo banco quando acessados pelo mesmo endereço. Atualize o perfil em outro aparelho para ver novas fotos e avaliações. A sincronização não é por WebSocket.

## 5. Onde estão os códigos

| Parte | Arquivos principais |
| --- | --- |
| Narração | `voz.py`, `static/voz-audio.js`, `requirements-voz.txt` |
| Escolha da voz | `templates/ajuda.html` |
| Fotos | `static/galeria.js`, `templates/componentes.html`, `templates/perfil.html` |
| Gravação da avaliação | `static/avaliacoes.js` |
| Validação e recebimento | `app.py` |
| Tabelas e persistência | `dados.py` |
| Testes do servidor | `tests/test_galeria_avaliacoes.py`, `tests/test_narracao.py` |

Para os alunos que estudaram até repetição, comece pela regra **percorrer as fotos e conferir se há no máximo cinco**. Depois mostre por que o cadastro, as fotos e as avaliações são guardados em tabelas diferentes, ligados pelo identificador do profissional. Funções assíncronas, eventos do navegador e permissões de microfone são assuntos posteriores, para demonstração orientada.
