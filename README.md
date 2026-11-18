# Batalha Conecta

Mural de trabalhadores de Batalha (PI), feito como projeto escolar do curso de Desenvolvimento de Sistemas. Quem precisa de um serviço encontra quem sabe fazer, e quem trabalha mostra o que faz, inclusive **falando**, para quem não lê.

- **Cadastro por voz:** perguntas faladas (vozes Francisca e Antônio) e respostas ouvidas e entendidas por um assistente de inteligência artificial gratuito (Groq).
- **Dois modos:** textos, ou imagens e voz para quem não lê.
- **Feito em Python** com Flask e SQLite.

## Como usar no Windows

1. Abra `iniciar_windows.bat`. Na primeira vez, ele prepara o Python (precisa de internet).
2. O site abre em http://127.0.0.1:5000.
3. Para ligar o assistente de IA, abra `configurar_ia_windows.bat` e cole uma chave gratuita da Groq. Veja `NOVIDADES_V07.md`.

Comece a leitura por `LEIA_PRIMEIRO.md`. Para a feira, veja a seção "Modo feira" em `NOVIDADES_V07.md`.

## Segurança

A chave da Groq fica no arquivo `.env`, e os cadastros ficam na pasta `instance`. **Nenhum dos dois vai para o GitHub** (estão no `.gitignore`). Nunca coloque a chave no código.

## Testes

```
python -m pytest -q
npm run test:voz
python verificar_interface.py
```
