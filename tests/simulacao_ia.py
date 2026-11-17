"""Serviço de IA de mentira para os testes: nenhuma chave, nenhuma internet.

A "gravação" é o texto da fala depois de uma assinatura de áudio. O modelo de
linguagem é trocado por regras simples. A conferência das respostas
(AgenteIA.conferir) é a verdadeira.
"""
from dados import CATEGORIAS
from ia import AgenteIA, IAIndisponivel, digitos_falados, limpar


def gravacao(fala):
    """Bytes aceitos como áudio OGG pelo servidor, com a fala escrita dentro."""
    return b"OggS" + fala.encode("utf-8").ljust(220)


class AgenteSimulado(AgenteIA):
    def __init__(self):
        super().__init__(chave="simulada", categorias=CATEGORIAS)
        self.ouvidas = []
        self.perguntas = 0

    def transcrever(self, conteudo, nome_arquivo="resposta.webm", campo="", fase="resposta"):
        fala = conteudo[4:].decode("utf-8").strip()
        self.ouvidas.append((fala, campo, fase, nome_arquivo))
        if fala.startswith("sem escuta"):
            raise IAIndisponivel("Serviço simulado fora do ar.")
        return "" if fala == "silêncio" else fala

    def _perguntar(self, modelo, mensagens, com_esquema):
        import json
        situacao = json.loads(mensagens[1]["content"])
        fala, campo = situacao["transcricao"], situacao["campo"]
        normal = limpar(fala)
        self.perguntas += 1
        vazio = {"campo": None, "valor": None, "fala": None}
        if normal.startswith("falhar"):
            raise IAIndisponivel("Serviço simulado fora do ar.", "falha", 500)
        if "inventar" in normal:
            return {**vazio, "intencao": "responder", "valor": "Nome Inventado"}
        if "o que e" in normal:
            return {**vazio, "intencao": "duvida", "fala": "É o nome do lugar onde você trabalha, como o seu bairro."}
        if "publi" in normal:
            return {**vazio, "intencao": "publicar"}
        if "mudar o bairro" in normal:
            return {**vazio, "intencao": "corrigir", "campo": "comunidade"}
        if normal in ("ta certinho", "isso ai mesmo"):
            return {**vazio, "intencao": "sim"}
        if normal.startswith("ta errado"):
            return {**vazio, "intencao": "nao"}
        if campo == "nome" and normal.startswith("meu nome e "):
            return {**vazio, "intencao": "responder", "valor": fala[len("Meu nome é "):].rstrip(".")}
        if campo == "categoria":
            return {**vazio, "intencao": "responder", "valor": "alimentacao" if "beiju" in normal else "nenhuma"}
        if campo == "telefone":
            if "nao tenho" in normal:
                return {**vazio, "intencao": "pular"}
            return {**vazio, "intencao": "responder", "valor": digitos_falados(fala)}
        return {**vazio, "intencao": "responder", "valor": fala}
