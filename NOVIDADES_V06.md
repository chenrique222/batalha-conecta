# Batalha Conecta — atualização 0.6

Esta atualização aplica a marca enviada, reorganiza as atividades e reduz a espera pela narração. Mantém o switch de modo, o cadastro por voz, a galeria de até cinco fotos e as avaliações em áudio.

## O que mudou

- **Cabeçalho:** logo completa do PNG enviado, sobre uma base azul escura que permite ler as letras brancas.
- **Frase:** “Valorizando o serviço da nossa gente”.
- **Favicon e instalação:** o mapa verde do símbolo anterior, em fundo azul.
- **Categorias:** a organização abaixo vale para a página inicial, a busca, os perfis e o cadastro escrito ou falado.

| Categoria | O que reúne |
| --- | --- |
| Bolos e comidas | Bolos, doces e refeições. |
| Artesanato | Peças feitas à mão. |
| Farinha e derivados | Farinha, goma e tapioca de mandioca. Substitui o nome amplo “Trabalho rural”. |
| Serviços de manutenção | Pedreiro, pintura, elétrica e encanamento. |
| Outros serviços | Atividades que não se encaixam nas outras categorias. A barbearia é apenas um exemplo visual. |

## Como atualizar preservando os cadastros

1. Encerre o aplicativo antigo com **Ctrl+C** no terminal.
2. Faça uma cópia de segurança da pasta **instance inteira** da instalação antiga. Ela contém o banco, as fotos, os áudios e a chave da sessão.
3. Extraia o novo ZIP em outra pasta.
4. Copie a pasta `instance` antiga para dentro da nova pasta `Batalha_Conecta_Python`, antes da primeira execução.
5. Abra `iniciar_windows.bat` ou use os comandos abaixo no terminal, aberto dentro da nova pasta do projeto.
6. Acesse **http://127.0.0.1:5000** e pressione **Ctrl+F5**. Confira a marca e os seus perfis. Conserve a cópia antiga até terminar a conferência.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip install -r requirements-voz.txt
.\.venv\Scripts\python.exe app.py
```

Execute uma linha por vez. Se `py` não for reconhecido, teste `python --version`. Se esse comando mostrar um Python compatível instalado, use `python -m venv .venv` na primeira linha. Os demais comandos permanecem iguais. Não é necessário abrir o terminal como administrador nem ativar o ambiente com um script PowerShell. As instruções completas estão em `LEIA_PRIMEIRO.md`.

No primeiro início, uma atualização única move o pedreiro de exemplo para manutenção. Perfis antigos de “Trabalho rural” ou “Outros serviços” cujo **nome** contém pedreiro, pedreira, eletricista, encanador, encanadora, pintor ou pintora também passam para manutenção. Cadastros da antiga categoria rural ficam em “Farinha e derivados” se o nome mencionar farinha, farinhada, mandioca, goma ou tapioca; os demais vão para “Outros serviços”. Isso não apaga cadastros, fotos ou avaliações, nem altera contatos ou descrições. A regra não interpreta a descrição inteira: confira a classificação dos perfis antigos depois da atualização. Não há editor de categorias de perfis já publicados nesta versão.

O favicon usa arquivos com nomes novos. Se um aplicativo já instalado continuar mostrando o ícone antigo, confira primeiro a nova marca na aba do navegador; o atalho instalado pode depender de uma atualização do navegador ou de ser adicionado novamente.

## Por que a narração deve responder melhor

Antes, o navegador podia esperar até 20 segundos pelo áudio online. Agora, após **2,5 segundos sem áudio pronto**, tenta a voz do aparelho. Se a voz online demorar ou falhar, novas perguntas usam essa alternativa por 30 segundos, evitando repetir a espera. A voz do aparelho também precisa estar disponível e autorizada pelo navegador; esse prazo não é uma garantia de que qualquer aparelho começará a falar exatamente em 2,5 segundos.

Áudios já preparados são reaproveitados em memória. O servidor não segura mais uma trava global enquanto espera a internet: um áudio lento não bloqueia o acesso a outro já pronto. Pedidos iguais compartilham a mesma geração; até duas gerações distintas podem acontecer ao mesmo tempo. As duas amostras de **Ajuda** já acompanham o pacote e não precisam ser geradas de novo.

Para evitar a espera pelo serviço online desde a primeira pergunta, entre em **Ajuda → Voz rápida do aparelho**. A preferência fica salva nesse navegador. Francisca e Antônio continuam disponíveis como opções naturais; para textos novos, dependem da conexão com o serviço externo. O cache de textos narrados não é gravado em disco.

O prazo do microfone **não foi reduzido**: o assistente conserva até 30 segundos para começar a responder, uma pausa de 6 segundos após trechos comuns e 10 segundos ao ditar telefone. As confirmações têm pausa de 2,5 segundos. Dizer **“terminei”** ou tocar na confirmação encerra a resposta atual sem aguardar toda a pausa; ainda é necessário conferir antes de publicar. A gravação manual e as avaliações continuam aceitando pausas e têm limite de dois minutos.

## O que foi verificado

Passaram 25 testes Python e 14 testes de lógica/escuta em JavaScript. Os testes de interface com navegador simulado também passaram: switch, fotos, avaliações, cadastro por voz e narração. Foram simulados atraso de rede, áudio chegando depois da alternativa, cancelamento, decodificação lenta, reaproveitamento do áudio e ausência de voz no aparelho. A migração foi verificada com banco temporário, preservando fotos, contatos e avaliações.

A conexão real com a voz online não pôde ser validada neste ambiente por uma falha de certificado TLS; a verificação de segurança não foi desativada. O resultado de velocidade, a qualidade da voz, o microfone e o visual nos celulares da feira precisam ser conferidos nesses aparelhos. Os testes automatizados não representam uma medição de desempenho no seu computador.

Para o teste em aula: escolha uma voz em Ajuda, inicie um cadastro, faça uma pausa ao ditar, conclua com “terminei”, confira a resposta, corrija um campo e cancele ou publique um perfil fictício. Depois teste novamente com **Voz rápida do aparelho** e compare a espera.

## Arquivos para estudar

- `templates/base.html`: logo, frase e favicon.
- `dados.py`: nomes das categorias e atualização do banco antigo.
- `static/voz-logica.js`: perguntas e reconhecimento dos nomes de atividades.
- `static/voz-audio.js`: reprodução, cache e troca de voz se houver demora.
- `voz.py`: geração online, cache em memória e coordenação de pedidos.
- `GUIA_PERSONALIZACAO.md`: passo a passo para trocar imagens, cores e textos.

Os arquivos `NOVIDADES_V04.md`, `NOVIDADES_V05.md` e `ORIGEM_IMAGENS_V05.md` registram versões anteriores. Para o comportamento atual, use este guia.
