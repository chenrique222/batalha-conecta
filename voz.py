"""Narração neural em português brasileiro, com cache pequeno só na memória.

O edge-tts usa o serviço online do Microsoft Edge. Não exige chave de API,
mas depende de internet e da disponibilidade desse serviço externo.
"""
import asyncio
import hashlib
import threading
from collections import OrderedDict
from concurrent.futures import Future, TimeoutError as EsperaEsgotada
from pathlib import Path

# Só vozes exclusivamente brasileiras. As vozes "multilíngues" (como pt-BR-ThalitaMultilingualNeural)
# adivinham o idioma de cada frase e, em frases curtas ou com nomes, falam com sotaque estrangeiro.
VOZES = {"francisca": "pt-BR-FranciscaNeural", "antonio": "pt-BR-AntonioNeural"}
RITMOS = {"francisca": "+0%", "antonio": "+0%"}
LIMITE_DISCO = 60 * 1024 * 1024


class VozIndisponivel(RuntimeError):
    pass


class VozNatural:
    def __init__(self, pasta_cache=None):
        # Falas fixas (perguntas, orientações) ficam em disco: tocam na hora, mesmo após reiniciar.
        self._pasta = Path(pasta_cache) if pasta_cache else None
        self._trava = threading.Lock()
        self._cache = OrderedDict()
        self._cache_bytes = 0
        self._em_curso = {}
        # A fala é pedida em partes e as perguntas são preparadas antes: precisa de algumas vagas.
        self._vagas = threading.BoundedSemaphore(5)

    async def _gerar(self, texto, narrador):
        import edge_tts
        comunicacao = edge_tts.Communicate(texto, VOZES[narrador], rate=RITMOS[narrador],
                                          connect_timeout=2, receive_timeout=4)
        partes = []
        async for parte in comunicacao.stream():
            if parte["type"] == "audio":
                partes.append(parte["data"])
        conteudo = b"".join(partes)
        if len(conteudo) < 100:
            raise VozIndisponivel("A voz natural não retornou áudio.")
        return conteudo

    def _arquivo(self, texto, narrador):
        if not self._pasta:
            return None
        marca = hashlib.sha256(f"{VOZES[narrador]}|{RITMOS[narrador]}|{texto}".encode("utf-8")).hexdigest()
        return self._pasta / f"{marca}.mp3"

    def _ler_disco(self, arquivo):
        try:
            conteudo = arquivo.read_bytes() if arquivo and arquivo.is_file() else b""
        except OSError:
            return None
        return conteudo if len(conteudo) >= 100 else None

    def _gravar_disco(self, arquivo, conteudo):
        """Guarda a fala e apaga as mais antigas quando a pasta passa do limite."""
        try:
            self._pasta.mkdir(parents=True, exist_ok=True)
            provisorio = arquivo.with_suffix(f".{threading.get_ident()}.tmp")
            provisorio.write_bytes(conteudo)
            provisorio.replace(arquivo)
            guardados = sorted(self._pasta.glob("*.mp3"), key=lambda item: item.stat().st_mtime)
            total = sum(item.stat().st_size for item in guardados)
            while guardados and total > LIMITE_DISCO:
                antigo = guardados.pop(0)
                total -= antigo.stat().st_size
                antigo.unlink()
        except OSError:
            pass  # Sem espaço ou sem permissão: a voz continua funcionando sem o disco.

    def sintetizar(self, texto, narrador="francisca", guardar=False):
        """`guardar=True` só para falas fixas do aplicativo, nunca para dados de uma pessoa."""
        if narrador not in VOZES:
            raise ValueError("Escolha uma das vozes disponíveis.")
        chave = (texto, narrador)
        arquivo = self._arquivo(texto, narrador)
        with self._trava:
            na_memoria = chave in self._cache
        if not na_memoria:
            conteudo = self._ler_disco(arquivo)
            if conteudo:
                return conteudo
        # A trava protege só as estruturas de memória, nunca a espera pela internet.
        with self._trava:
            if chave in self._cache:
                self._cache.move_to_end(chave)
                return self._cache[chave]
            tarefa = self._em_curso.get(chave)
            criar = tarefa is None
            if criar:
                if not self._vagas.acquire(blocking=False):
                    raise VozIndisponivel("Use a voz do aparelho enquanto a voz natural está ocupada.")
                tarefa = Future()
                self._em_curso[chave] = tarefa
        if not criar:
            try:
                return tarefa.result(timeout=6)
            except EsperaEsgotada as erro:
                raise VozIndisponivel("A voz natural demorou. Use a voz do aparelho.") from erro
        try:
            async def com_limite():
                return await asyncio.wait_for(self._gerar(texto, narrador), timeout=6)
            conteudo = asyncio.run(com_limite())
            with self._trava:
                if len(conteudo) <= 2 * 1024 * 1024:
                    self._cache[chave] = conteudo
                    self._cache_bytes += len(conteudo)
                    while len(self._cache) > 64 or self._cache_bytes > 12 * 1024 * 1024:
                        _, antigo = self._cache.popitem(last=False)
                        self._cache_bytes -= len(antigo)
            if guardar and arquivo:
                self._gravar_disco(arquivo, conteudo)
            tarefa.set_result(conteudo)
            return conteudo
        except Exception as erro:
            falha = VozIndisponivel("A voz natural não está disponível. Confira a internet ou use a voz do aparelho.")
            tarefa.set_exception(falha)
            raise falha from erro
        finally:
            with self._trava:
                self._em_curso.pop(chave, None)
            self._vagas.release()
