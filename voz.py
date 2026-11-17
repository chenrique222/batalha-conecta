"""Narração neural em português brasileiro, com cache pequeno só na memória.

O edge-tts usa o serviço online do Microsoft Edge. Não exige chave de API,
mas depende de internet e da disponibilidade desse serviço externo.
"""
import asyncio
import threading
from collections import OrderedDict
from concurrent.futures import Future, TimeoutError as EsperaEsgotada

VOZES = {"francisca": "pt-BR-FranciscaNeural", "antonio": "pt-BR-AntonioNeural"}


class VozIndisponivel(RuntimeError):
    pass


class VozNatural:
    def __init__(self):
        self._trava = threading.Lock()
        self._cache = OrderedDict()
        self._cache_bytes = 0
        self._em_curso = {}
        self._vagas = threading.BoundedSemaphore(2)

    async def _gerar(self, texto, narrador):
        import edge_tts
        comunicacao = edge_tts.Communicate(texto, VOZES[narrador], rate="-5%",
                                          connect_timeout=2, receive_timeout=4)
        partes = []
        async for parte in comunicacao.stream():
            if parte["type"] == "audio":
                partes.append(parte["data"])
        conteudo = b"".join(partes)
        if len(conteudo) < 100:
            raise VozIndisponivel("A voz natural não retornou áudio.")
        return conteudo

    def sintetizar(self, texto, narrador="francisca"):
        if narrador not in VOZES:
            raise ValueError("Escolha uma das vozes disponíveis.")
        chave = (texto, narrador)
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
