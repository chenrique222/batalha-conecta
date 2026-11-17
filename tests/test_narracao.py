"""O serviço externo é simulado aqui; preparar_voz.py testa a conexão real."""
import tempfile
import unittest
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import AsyncMock, Mock
from app import create_app
from voz import VozNatural, VozIndisponivel


class Narracao(unittest.TestCase):
    def setUp(self):
        self.dados = tempfile.TemporaryDirectory()
        self.app = create_app({"TESTING":True, "DATA_DIR":self.dados.name})
        self.cliente = self.app.test_client()
        self.cliente.get("/")
        with self.cliente.session_transaction() as sessao:
            self.csrf = sessao["csrf"]

    def tearDown(self):
        self.dados.cleanup()

    def test_validacao_nao_aciona_servico(self):
        voz = Mock()
        self.app.extensions["voz_natural"] = voz
        for texto, csrf, narrador in [("",self.csrf,"francisca"),("x"*2501,self.csrf,"antonio"),("Olá","invalido","francisca"),("Olá",self.csrf,"invalido")]:
            resposta = self.cliente.post("/api/voz",data={"texto":texto,"csrf":csrf,"narrador":narrador})
            self.assertEqual(resposta.status_code,400)
        voz.sintetizar.assert_not_called()

    def test_mp3_privado_e_escolha_de_voz(self):
        voz = Mock()
        voz.sintetizar.return_value = b"ID3" + b"a"*150
        self.app.extensions["voz_natural"] = voz
        resposta = self.cliente.post("/api/voz",data={"texto":"Olá!","csrf":self.csrf,"narrador":"antonio"})
        self.assertEqual(resposta.status_code,200)
        self.assertEqual(resposta.mimetype,"audio/mpeg")
        self.assertEqual(resposta.headers["Cache-Control"],"no-store")
        voz.sintetizar.assert_called_once_with("Olá!", "antonio")

    def test_servico_indisponivel_permite_alternativa(self):
        voz = Mock()
        voz.sintetizar.side_effect = VozIndisponivel("Confira a internet.")
        self.app.extensions["voz_natural"] = voz
        resposta = self.cliente.post("/api/voz",data={"texto":"Olá","csrf":self.csrf})
        self.assertEqual(resposta.status_code,503)
        self.assertIn("erros",resposta.json)

    def test_cache_separa_vozes_e_libera_trava_apos_falha(self):
        voz = VozNatural()
        voz._gerar = AsyncMock(return_value=b"ID3"+b"a"*150)
        voz.sintetizar("Olá", "francisca")
        voz.sintetizar("Olá", "francisca")
        voz.sintetizar("Olá", "antonio")
        self.assertEqual(voz._gerar.await_count,2)
        voz._gerar.side_effect = TimeoutError()
        with self.assertRaises(VozIndisponivel): voz.sintetizar("Novo texto")
        voz._gerar.side_effect = None
        self.assertTrue(voz.sintetizar("Novo texto"))

    def test_cache_nao_espera_uma_narracao_lenta(self):
        voz = VozNatural()
        voz._gerar = AsyncMock(return_value=b"ID3" + b"a"*150)
        pronto = voz.sintetizar("Já preparado")
        iniciou, liberar = threading.Event(), threading.Event()
        async def lento(texto, narrador):
            iniciou.set()
            await asyncio.to_thread(liberar.wait, 2)
            return b"ID3" + b"b"*150
        voz._gerar = lento
        with ThreadPoolExecutor(max_workers=2) as pool:
            tarefa = pool.submit(voz.sintetizar, "Texto demorado")
            self.assertTrue(iniciou.wait(1))
            try:
                cache = pool.submit(voz.sintetizar, "Já preparado")
                self.assertEqual(cache.result(timeout=.5), pronto)
            finally:
                liberar.set()
            self.assertTrue(tarefa.result(timeout=2))

    def test_pedidos_iguais_compartilham_uma_geracao(self):
        voz = VozNatural()
        iniciou, liberar = threading.Event(), threading.Event()
        chamadas = []
        async def gerar(texto, narrador):
            chamadas.append(texto)
            iniciou.set()
            await asyncio.to_thread(liberar.wait, 2)
            return b"ID3" + b"c"*150
        voz._gerar = gerar
        with ThreadPoolExecutor(max_workers=2) as pool:
            primeira = pool.submit(voz.sintetizar, "Mesma pergunta")
            self.assertTrue(iniciou.wait(1))
            segunda = pool.submit(voz.sintetizar, "Mesma pergunta")
            liberar.set()
            self.assertEqual(primeira.result(timeout=2), segunda.result(timeout=2))
        self.assertEqual(chamadas, ["Mesma pergunta"])
