"""Testes opcionais: instale Node.js e execute npm install antes deste script."""
import os
import subprocess
import tempfile
import threading
from pathlib import Path


def verificar():
    with tempfile.TemporaryDirectory() as pasta:
        os.environ["BATALHA_DADOS"] = pasta
        # O banco é temporário. Nenhum cadastro do professor é alterado.
        from app import create_app
        from werkzeug.serving import make_server
        app = create_app({"TESTING":True,"DATA_DIR":pasta})
        servidor = make_server("127.0.0.1", 0, app, threaded=True)
        thread = threading.Thread(target=servidor.serve_forever, daemon=True)
        thread.start()
        ambiente = dict(os.environ, BATALHA_TESTE_URL=f"http://127.0.0.1:{servidor.server_port}")
        try:
            for arquivo in ("test_modo.cjs", "test_interface.cjs", "test_conversa_interface.cjs", "test_narracao_interface.cjs"):
                subprocess.run(["node", str(Path(__file__).parent / "tests" / arquivo)], env=ambiente, check=True)
        finally:
            servidor.shutdown()
            servidor.server_close()
            thread.join(timeout=5)


if __name__ == "__main__":
    verificar()
