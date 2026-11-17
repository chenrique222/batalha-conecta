"""Modo feira com QR code: os visitantes abrem o Batalha Conecta no próprio celular.

Como funciona:
1. O site roda neste computador, com os dados de teste em instance-feira.
2. O programa cloudflared, da Cloudflare, cria um endereço HTTPS temporário
   (https://....trycloudflare.com) que leva até este computador. É grátis e não
   precisa de conta. O celular só libera o microfone em endereços HTTPS.
3. Um cartaz com o QR code desse endereço abre no navegador, para mostrar ou imprimir.

O endereço muda toda vez que este programa é aberto e deixa de funcionar quando
ele é fechado. Execute com:  iniciar_feira_qrcode.bat
"""
import base64
import html
import io
import os
import platform
import re
import shutil
import socket
import subprocess
import sys
import threading
import time
import urllib.request
import webbrowser
from pathlib import Path

PASTA = Path(__file__).resolve().parent
# Os testes da feira ficam separados dos cadastros de verdade (pasta instance).
os.environ.setdefault("BATALHA_DADOS", str(PASTA / "instance-feira"))
DADOS = Path(os.environ["BATALHA_DADOS"])
PORTA = int(os.environ.get("PORT", 5000))
ENDERECO = re.compile(r"https://[a-z0-9-]+\.trycloudflare\.com")
DOWNLOAD_WINDOWS = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"


def porta_livre(porta):
    with socket.socket() as teste:
        return teste.connect_ex(("127.0.0.1", porta)) != 0


def achar_cloudflared():
    """Procura o cloudflared instalado ou na pasta do projeto. No Windows, oferece baixar."""
    local = PASTA / ("cloudflared.exe" if os.name == "nt" else "cloudflared")
    if local.is_file():
        return str(local)
    instalado = shutil.which("cloudflared")
    if instalado:
        return instalado
    if os.name != "nt" or platform.machine().lower() not in ("amd64", "x86_64"):
        print("Instale o cloudflared: https://developers.cloudflare.com/tunnel/downloads/")
        return None
    print("Para criar o endereço do QR code, é preciso o programa cloudflared, da Cloudflare.")
    print(f"Ele será baixado do site oficial no GitHub:\n  {DOWNLOAD_WINDOWS}")
    if input("Baixar agora para a pasta do projeto? (s/n) ").strip().lower() not in ("s", "sim"):
        return None
    print("Baixando...", flush=True)
    provisorio = local.with_suffix(".baixando")
    try:
        with urllib.request.urlopen(DOWNLOAD_WINDOWS, timeout=120) as resposta, open(provisorio, "wb") as destino:
            shutil.copyfileobj(resposta, destino)
        provisorio.replace(local)
    except OSError as erro:
        provisorio.unlink(missing_ok=True)
        print(f"Não foi possível baixar: {erro}")
        print("Baixe pelo link acima, salve como cloudflared.exe na pasta do projeto e abra este programa de novo.")
        return None
    return str(local)


def iniciar_site():
    from app import app  # importado só agora: BATALHA_DADOS já está definido
    from waitress import serve
    # Mais linhas de atendimento: vários celulares falando ao mesmo tempo.
    linha = threading.Thread(target=serve, kwargs={"app": app, "host": "127.0.0.1", "port": PORTA, "threads": 16,
                                                    "max_request_body_size": 20 * 1024 * 1024}, daemon=True)
    linha.start()
    for _ in range(50):
        if not porta_livre(PORTA):
            return True
        time.sleep(0.2)
    return False


def abrir_tunel(executavel):
    """Liga o cloudflared e devolve (processo, endereço https)."""
    processo = subprocess.Popen([executavel, "tunnel", "--no-autoupdate", "--url", f"http://127.0.0.1:{PORTA}"],
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
    achado = {}
    pronto = threading.Event()

    def ler():
        # Continua lendo depois de achar o endereço, para o programa nunca travar com a saída cheia.
        for linha in processo.stdout:
            encontrado = ENDERECO.search(linha)
            if encontrado and "url" not in achado:
                achado["url"] = encontrado.group(0)
                pronto.set()
        pronto.set()

    threading.Thread(target=ler, daemon=True).start()
    pronto.wait(60)
    return processo, achado.get("url")


def esperar_endereco(url, limite=60):
    """O endereço novo leva alguns segundos para funcionar em toda a internet."""
    fim = time.monotonic() + limite
    while time.monotonic() < fim:
        try:
            with urllib.request.urlopen(url, timeout=10) as resposta:
                if resposta.status == 200:
                    return True
        except OSError:
            pass
        time.sleep(3)
    return False


def gerar_cartaz(url):
    import qrcode
    imagem = qrcode.make(url, box_size=12, border=2)
    memoria = io.BytesIO()
    imagem.save(memoria, format="PNG")
    png = base64.b64encode(memoria.getvalue()).decode("ascii")
    endereco = html.escape(url)
    DADOS.mkdir(parents=True, exist_ok=True)
    (DADOS / "qrcode-feira.png").write_bytes(memoria.getvalue())
    cartaz = DADOS / "cartaz-qrcode.html"
    cartaz.write_text(f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<title>Batalha Conecta · Teste no seu celular</title>
<style>
 body{{margin:0;font-family:system-ui,"Segoe UI",sans-serif;background:#f5f6f2;color:#17284a;text-align:center}}
 header{{background:#0b2149;color:#fff;padding:22px}} header h1{{margin:0;font-size:38px}} header p{{margin:6px 0 0;color:#c4d2e8;font-size:18px}}
 main{{padding:24px}} img{{width:min(70vh,90vw);height:auto;image-rendering:pixelated;border:10px solid #fff;border-radius:18px;box-shadow:0 4px 18px #0b214922}}
 ol{{display:inline-block;text-align:left;font-size:21px;line-height:1.6;margin:18px auto}}
 .endereco{{font-family:monospace;font-size:17px;word-break:break-all;color:#1b3f78}}
 .aviso{{max-width:760px;margin:14px auto 0;font-size:15px;color:#4f5d73}}
 @media print{{body{{background:#fff}} header{{-webkit-print-color-adjust:exact;print-color-adjust:exact}}}}
</style></head><body>
<header><h1>Batalha Conecta</h1><p>Valorizando o serviço da nossa gente · Teste no seu celular</p></header>
<main>
<img src="data:image/png;base64,{png}" alt="QR code para abrir o Batalha Conecta">
<ol><li>Aponte a câmera do celular para o código.</li><li>Toque em <strong>Mostrar meu trabalho</strong>.</li><li>Quando o celular pedir, <strong>permita o microfone</strong>.</li><li>Use um <strong>nome de personagem</strong>. Não diga telefone real.</li></ol>
<p class="endereco">{endereco}</p>
<p class="aviso">Versão de teste para a feira. Sua voz é enviada pela internet a um serviço de inteligência artificial e não fica guardada.
Os perfis de teste ficam visíveis para quem acessar este endereço e são apagados no final da feira.</p>
</main></body></html>""", encoding="utf-8")
    return cartaz


def principal():
    print("BATALHA CONECTA - MODO FEIRA COM QR CODE\n")
    if not (PASTA / ".env").is_file():
        print("ATENÇÃO: sem o arquivo .env, o assistente de IA fica desligado. No celular, o cadastro falado depende dele.\n")
    if not porta_livre(PORTA):
        print(f"A porta {PORTA} já está em uso. Feche a outra janela do Batalha Conecta e tente de novo.")
        return 1
    executavel = achar_cloudflared()
    if not executavel:
        print("Sem o cloudflared, use o modo feira no notebook: iniciar_feira.bat")
        return 1
    print(f"Testes da feira em: {DADOS}")
    if not iniciar_site():
        print("O site não abriu. Veja as mensagens acima.")
        return 1
    print(f"Site ligado neste computador: http://127.0.0.1:{PORTA}")
    print("Criando o endereço público (pode levar até 1 minuto)...", flush=True)
    processo, url = abrir_tunel(executavel)
    if not url:
        processo.terminate()
        print("Não foi possível criar o endereço. Confira a internet e tente de novo.")
        print("A rede da escola pode bloquear esse tipo de conexão; o roteador do celular costuma funcionar.")
        return 1
    print(f"Endereço criado: {url}")
    print("Conferindo se o endereço já abre...", flush=True)
    if not esperar_endereco(url):
        print("O endereço ainda não respondeu daqui. Teste no celular; se não abrir em 1 minuto, feche e abra de novo.")
    cartaz = gerar_cartaz(url)
    webbrowser.open(cartaz.as_uri())
    print(f"\nCartaz com o QR code aberto no navegador. Também foi salvo em:\n  {cartaz}")
    print("\nMantenha esta janela aberta durante a feira. Para encerrar, pressione Ctrl+C.")
    print("O endereço muda toda vez que este programa é aberto: imprima o cartaz depois de abrir.")
    print("No final da feira, apague a pasta instance-feira.")
    try:
        while processo.poll() is None:
            time.sleep(1)
        print("O túnel da Cloudflare caiu. Feche esta janela e abra de novo para criar um endereço novo.")
        return 1
    except KeyboardInterrupt:
        print("\nEncerrando...")
        return 0
    finally:
        if processo.poll() is None:
            processo.terminate()


if __name__ == "__main__":
    sys.exit(principal())
