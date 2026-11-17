"""Servidor para demonstração em rede. Execute com --rede para liberar a LAN."""
import argparse
import os
from waitress import serve
from app import app

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Executar o Batalha Conecta")
    parser.add_argument("--rede", action="store_true", help="Permitir acesso de outros aparelhos da mesma rede")
    parser.add_argument("--porta", type=int, default=int(os.environ.get("PORT", 5000)))
    opcoes = parser.parse_args()
    host = "0.0.0.0" if opcoes.rede else "127.0.0.1"
    print(f"Batalha Conecta: http://127.0.0.1:{opcoes.porta}", flush=True)
    # Várias linhas de atendimento: vários celulares podem falar ao mesmo tempo.
    serve(app, host=host, port=opcoes.porta, threads=16, max_request_body_size=20 * 1024 * 1024)
