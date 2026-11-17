"""Testes opcionais: instale Node.js e execute npm install antes deste script."""
import os
import subprocess
import sys
import tempfile
import threading
from pathlib import Path


def verificar():
    with tempfile.TemporaryDirectory() as pasta, tempfile.TemporaryDirectory() as pasta_ia:
        os.environ["BATALHA_DADOS"] = pasta
        # O banco é temporário. Nenhum cadastro do professor é alterado.
        from app import create_app
        from werkzeug.serving import make_server
        app = create_app({"TESTING":True,"DATA_DIR":pasta})
        servidor = make_server("127.0.0.1", 0, app, threaded=True)
        thread = threading.Thread(target=servidor.serve_forever, daemon=True)
        thread.start()
        ambiente = dict(os.environ, BATALHA_TESTE_URL=f"http://127.0.0.1:{servidor.server_port}")
        # Segundo servidor, com o assistente de IA simulado: sem chave e sem internet.
        sys.path.insert(0, str(Path(__file__).parent / "tests"))
        from simulacao_ia import AgenteSimulado
        app_ia = create_app({"TESTING":True,"DATA_DIR":pasta_ia})
        app_ia.extensions["agente_ia"] = AgenteSimulado()
        servidor_ia = make_server("127.0.0.1", 0, app_ia, threaded=True)
        thread_ia = threading.Thread(target=servidor_ia.serve_forever, daemon=True)
        thread_ia.start()
        ambiente["BATALHA_TESTE_URL_IA"] = f"http://127.0.0.1:{servidor_ia.server_port}"
        try:
            for arquivo in ("test_modo.cjs", "test_interface.cjs", "test_conversa_interface.cjs", "test_narracao_interface.cjs", "test_ia_interface.cjs"):
                subprocess.run(["node", str(Path(__file__).parent / "tests" / arquivo)], env=ambiente, check=True)
        finally:
            for parar, espera in ((servidor, thread), (servidor_ia, thread_ia)):
                parar.shutdown()
                parar.server_close()
                espera.join(timeout=5)


if __name__ == "__main__":
    verificar()
