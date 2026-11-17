# Verificação da versão 0.4

Ambiente de teste: Python 3.12 em Linux, Flask 3.1.3, Pillow 12.3.0, edge-tts 7.3.1 e Node para os testes de interface. Node não é necessário para usar o aplicativo.

## Servidor Python

**21 testes passaram.** Os testes cobrem cadastro, busca, banco compartilhado, arquivos, sessão, publicação sem duplicação, recursos PWA, cinco fotos por perfil, rejeição da sexta foto, remoção de arquivos após envio inválido, migração da foto antiga, edição restrita à sessão criadora, limite de galeria em envios simultâneos, áudio das avaliações, notas de 1 a 5, consentimento, persistência, média e paginação das avaliações.

A integração de narração testa seleção da voz, formato MP3, ausência de cache público, cache separado por voz e recuperação quando o serviço não responde. Nessa bateria, o serviço externo é simulado.

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

## Síntese real e instalação

Foram gerados dois MP3 reais pelo serviço usado pelo edge-tts: Francisca com cerca de 7 segundos e Antônio com cerca de 8,8 segundos. Os arquivos foram lidos por um decodificador de mídia e acompanham o pacote. O ambiente de teste utiliza uma cadeia de certificados própria, configurada apenas para esse teste. A validação TLS permaneceu ativa. O aplicativo distribuído usa a configuração padrão da biblioteca.

Também foi concluído o download de todas as dependências para CPython 3.12 em Windows x64, incluindo edge-tts e aiohttp. Essa verificação confirma a disponibilidade dos pacotes, não a execução do arquivo `.bat` em Windows.

## Interações e escuta

**14 testes JavaScript** de lógica do cadastro e tolerância a pausas passaram.

```text
npm run test:voz
```

**10 cenários de interação** passaram em DOM simulado, com chamadas reais ao servidor Flask e a um banco temporário. Incluem seleção cumulativa de fotos, remoção, publicação de cinco fotos, ampliação, gravação de avaliação com microfone simulado, conferência, autorização, falha de conexão preservando áudio, recusa de permissão, limite de dois minutos, descarte, escolha de voz, alternância dos modos e conversa completa com correção antes de publicar.

Para reproduzir os cenários, instale Node.js, execute `npm install` e depois:

```powershell
.\.venv\Scripts\python.exe verificar_interface.py
```

O verificador usa um banco temporário e não modifica os cadastros da instalação.

## Limites da verificação

O navegador completo não pôde ser iniciado neste ambiente. Os testes de interação usam jsdom e simulam captura, reprodução de áudio e reconhecimento de fala. Eles verificam estados, dados enviados e persistência, mas não comprovam qualidade audível, layout renderizado, permissão de microfone real ou comportamento em todos os celulares.

O microfone físico do professor, a execução do iniciador em Windows e a instalação como PWA devem ser conferidos nos aparelhos usados na feira. As vozes naturais dependem de um serviço externo e de internet. Para gravar pelo celular, o endereço precisa usar HTTPS.
> Atualização 0.6: os resultados atuais estão em `NOVIDADES_V06.md`. Passaram 25 testes Python, 14 testes de lógica/escuta e os testes de interface simulada, incluindo atrasos da narração e migração de categorias. O conteúdo abaixo registra verificações da versão anterior.

