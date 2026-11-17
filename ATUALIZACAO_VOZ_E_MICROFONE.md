# Voz e microfone · versão 0.4

A narração foi substituída pelas vozes neurais **Francisca** e **Antônio**, por meio de `edge-tts`. O roteiro completo de atualização e uso está em **NOVIDADES_V04.md**.

## Narração

Execute `iniciar_windows.bat`. O iniciador instala o aplicativo e a biblioteca de voz. Não instala Piper nem ONNX Runtime. Em **Ajuda**, escolha e ouça uma das vozes. Elas precisam de internet. A opção **Voz do aparelho** usa o recurso do navegador, cuja qualidade e disponibilidade dependem do dispositivo.

Para gerar novamente as duas amostras, abra o terminal na pasta do projeto e execute com o Python do ambiente virtual:

```powershell
.\.venv\Scripts\python.exe preparar_voz.py
```

O script grava `vozes/amostra-francisca.mp3` e `vozes/amostra-antonio.mp3`. Se o iniciador usou `.venv-v04`, substitua esse nome no caminho. Esse teste acessa o serviço externo. Falha de conexão, proxy ou indisponibilidade do serviço pode impedir a síntese.

## Ditado do cadastro

A narração fala. O reconhecimento do navegador escuta e transforma a fala em texto. Trocar a narração não substitui o reconhecimento.

O cadastro mantém os ajustes de escuta da versão anterior:

- Espera até 30 segundos pela primeira resposta.
- Tolera pausas de 6 segundos entre trechos, ou 10 segundos ao ditar o telefone.
- Tenta retomar uma sessão encerrada normalmente pelo navegador.
- Preserva o trecho já reconhecido após interrupções tratadas.
- Oferece o comando e o botão **Terminei**.
- Limita cada resposta a dois minutos.

Depois de ouvir a pergunta e o sinal, fale com calma. Confira a leitura da resposta antes de confirmar. Na revisão, escolha as fotos e autorize a publicação. O navegador pode enviar a fala ao serviço de reconhecimento.

## Avaliações gravadas

A avaliação guarda o áudio original. Não usa reconhecimento de fala e não encerra por silêncio. Toque no microfone para gravar, no quadrado para parar e ouça antes de publicar. Há um limite de dois minutos por gravação e de 10 MB por arquivo. Mudar para outra aba ou iniciar uma orientação falada encerra a gravação para liberar o microfone. O áudio concluído permanece para conferência na página aberta.

No modo de ícones, os alto-falantes explicam o uso. Para testar no celular, use HTTPS. A gravação física, o volume, o ruído do ambiente e o funcionamento das permissões devem ser conferidos nos aparelhos da feira.
