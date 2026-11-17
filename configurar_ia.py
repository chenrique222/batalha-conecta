"""Ativa o assistente de IA gratuito: guarda a chave da Groq no arquivo .env e testa.

Crie a chave, sem cartão de crédito, em https://console.groq.com/keys
Execute:  python configurar_ia.py        (ou abra configurar_ia_windows.bat)
"""
import sys
from pathlib import Path

from dados import CATEGORIAS
from ia import AgenteIA, IAIndisponivel, carregar_env

ARQUIVO = Path(__file__).resolve().parent / ".env"


def guardar_chave(chave):
    """Troca só a linha da chave; as outras configurações do .env são mantidas."""
    linhas = ARQUIVO.read_text(encoding="utf-8-sig").splitlines() if ARQUIVO.exists() else []
    linhas = [linha for linha in linhas if not linha.strip().startswith("GROQ_API_KEY=")]
    linhas.append(f"GROQ_API_KEY={chave}")
    ARQUIVO.write_text("\n".join(linhas) + "\n", encoding="utf-8")


def configurar():
    print("ASSISTENTE DE IA DO BATALHA CONECTA")
    print("1. Abra https://console.groq.com/keys e entre com uma conta (é grátis, sem cartão).")
    print("2. Clique em Create API Key e copie a chave, que começa com gsk_.")
    chave = input("3. Cole a chave aqui e pressione Enter (vazio mantém a atual): ").strip()
    if chave:
        if not chave.startswith("gsk_") or " " in chave:
            print("Essa chave não parece ser da Groq. Ela começa com gsk_ e não tem espaços.", file=sys.stderr)
            return 1
        guardar_chave(chave)
        print(f"Chave guardada em {ARQUIVO.name}. Não envie esse arquivo a ninguém.")
    carregar_env(ARQUIVO)
    agente = AgenteIA.do_ambiente(categorias=CATEGORIAS)
    if chave:
        agente.chave = chave
    if not agente.ativo:
        print("Nenhuma chave configurada. O cadastro por voz continua com o reconhecimento do navegador.")
        return 1
    print("Testando a conexão com o serviço...", flush=True)
    try:
        nome = agente.testar()
    except IAIndisponivel as erro:
        print(f"O teste falhou: {erro}", file=sys.stderr)
        print("Confira a internet e a chave. O aplicativo abre mesmo assim e usa o navegador para ouvir.", file=sys.stderr)
        return 1
    print(f'Funcionou. De "Meu nome é Maria das Dores." o assistente entendeu: {nome}')
    print("Reinicie o aplicativo (iniciar_windows.bat) para usar o assistente.")
    return 0


if __name__ == "__main__":
    raise SystemExit(configurar())
