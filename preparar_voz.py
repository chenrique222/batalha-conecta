"""Gera amostras das duas vozes, sem exigir modelos locais ou ONNX Runtime."""
import sys
from pathlib import Path
from voz import VozNatural


def preparar():
    destino = Path(__file__).resolve().parent / "vozes"
    destino.mkdir(exist_ok=True)
    voz = VozNatural()
    for nome in ("francisca", "antonio"):
        conteudo = voz.sintetizar("Olá! Vamos mostrar o seu trabalho? Você pode falar com calma. Estou aqui para ajudar.", nome)
        (destino / f"amostra-{nome}.mp3").write_bytes(conteudo)
        print(f"Voz {nome} testada. Amostra em vozes/amostra-{nome}.mp3.", flush=True)


if __name__ == "__main__":
    try:
        preparar()
    except Exception as erro:
        print(str(erro), file=sys.stderr)
        raise SystemExit(1)
