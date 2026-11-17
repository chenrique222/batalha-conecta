"""Assistente de IA: o serviço externo é simulado. configurar_ia.py testa a conexão real."""
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app import create_app
from dados import CATEGORIAS
from ia import AgenteIA, IAIndisponivel, carregar_env, conferir_telefone, digitos_falados
from simulacao_ia import AgenteSimulado, gravacao


def resposta_modelo(objeto):
    return 200, json.dumps({"choices": [{"message": {"content": json.dumps(objeto)}}]}).encode()


class Transporte:
    """Guarda os pedidos e devolve as respostas combinadas, em ordem."""

    def __init__(self, *respostas):
        self.respostas = list(respostas)
        self.pedidos = []

    def __call__(self, url, cabecalhos, corpo, espera):
        self.pedidos.append({"url": url, "cabecalhos": cabecalhos, "corpo": corpo})
        resposta = self.respostas.pop(0)
        if isinstance(resposta, Exception):
            raise resposta
        return resposta


def agente(*respostas, **opcoes):
    transporte = Transporte(*respostas)
    return AgenteIA(chave="gsk_teste", categorias=CATEGORIAS, transporte=transporte, **opcoes), transporte


class Configuracao(unittest.TestCase):
    def test_env_nao_substitui_variavel_existente_e_ignora_comentarios(self):
        with tempfile.TemporaryDirectory() as pasta, patch.dict(os.environ, {"BATALHA_IA_URL": "https://ja-definida"}, clear=False):
            os.environ.pop("GROQ_API_KEY", None)
            arquivo = Path(pasta) / ".env"
            arquivo.write_text('# comentário\nGROQ_API_KEY="gsk_do_arquivo"\nBATALHA_IA_URL=https://do-arquivo\nlinha sem igual\n', encoding="utf-8")
            carregar_env(arquivo)
            self.assertEqual(os.environ["GROQ_API_KEY"], "gsk_do_arquivo")
            self.assertEqual(os.environ["BATALHA_IA_URL"], "https://ja-definida")
            carregar_env(Path(pasta) / "inexistente")
            os.environ.pop("GROQ_API_KEY", None)

    def test_sem_chave_fica_inativo_e_nao_chama_o_servico(self):
        transporte = Transporte()
        sem_chave = AgenteIA(categorias=CATEGORIAS, transporte=transporte)
        self.assertFalse(sem_chave.ativo)
        with self.assertRaises(IAIndisponivel) as erro:
            sem_chave.entender("Maria", "resposta", "nome")
        self.assertEqual(erro.exception.motivo, "sem-chave")
        self.assertEqual(transporte.pedidos, [])


class Telefones(unittest.TestCase):
    def test_reune_digitos_palavras_e_dezenas(self):
        self.assertEqual(digitos_falados("oitenta e seis, nove nove nove, oitenta e um, vinte e três, quarenta e cinco"), "86999812345")
        self.assertEqual(digitos_falados("oito meia nove nove nove nove nove zero zero zero zero"), "86999990000")
        self.assertEqual(digitos_falados("dezenove trinta"), "1930")

    def test_so_aceita_numero_que_foi_dito(self):
        self.assertEqual(conferir_telefone("86999812345", "Meu zap é +55 86 99981-2345."), "86999812345")
        self.assertIsNone(conferir_telefone("86999812346", "Meu zap é 86 99981-2345."))
        self.assertIsNone(conferir_telefone("8699981234", "86 99981-2345"))
        self.assertIsNone(conferir_telefone("06999812345", "0 6 9 9 9 8 1 2 3 4 5"))


class Escuta(unittest.TestCase):
    def test_envia_audio_em_portugues_com_dica_e_sem_guardar(self):
        ia, transporte = agente((200, json.dumps({"text": " Centro. "}).encode()), vocabulario="Povoado Exemplo")
        self.assertEqual(ia.transcrever(b"OggS" + b"x" * 300, "resposta.ogg", "comunidade"), "Centro.")
        pedido = transporte.pedidos[0]
        self.assertEqual(pedido["url"], "https://api.groq.com/openai/v1/audio/transcriptions")
        self.assertEqual(pedido["cabecalhos"]["Authorization"], "Bearer gsk_teste")
        self.assertIn("multipart/form-data; boundary=", pedido["cabecalhos"]["Content-Type"])
        self.assertNotIn("Python-urllib", pedido["cabecalhos"]["User-Agent"])
        corpo = pedido["corpo"]
        for trecho in (b'name="model"\r\n\r\nwhisper-large-v3\r\n', b'name="language"\r\n\r\npt\r\n', b'filename="resposta.ogg"', b"OggS" + b"x" * 300, "Povoado Exemplo".encode()):
            self.assertIn(trecho, corpo)

    def test_descarta_silencio_e_frases_inventadas_mas_preserva_respostas_curtas(self):
        casos = [
            ({"text": "Legendas pela comunidade Amara.org"}, ""),
            ({"text": "x", "segments": [{"text": " Obrigado.", "no_speech_prob": 0.9, "avg_logprob": -1.4}]}, ""),
            ({"text": "x", "segments": [{"text": " Faço bolos", "no_speech_prob": 0.1, "avg_logprob": -0.2}, {"text": " de milho.", "no_speech_prob": 0.7, "avg_logprob": -0.3}]}, "Faço bolos de milho."),
            ({"text": "Outros serviços."}, "Outros serviços."),
            ({"text": "Cancelar cadastro."}, "Cancelar cadastro."),
            ({"text": "   "}, ""),
        ]
        for dados, esperado in casos:
            ia, _ = agente((200, json.dumps(dados).encode()))
            self.assertEqual(ia.transcrever(b"OggS" + b"x" * 300, "resposta.ogg", "categoria"), esperado)

    def test_limite_do_servico_e_chave_recusada_viram_motivos(self):
        for status, motivo in ((429, "limite"), (401, "sem-chave"), (500, "falha")):
            ia, _ = agente((status, b"{}"))
            with self.assertRaises(IAIndisponivel) as erro:
                ia.transcrever(b"OggS" + b"x" * 300)
            self.assertEqual(erro.exception.motivo, motivo)
        ia, _ = agente(OSError("sem internet"))
        with self.assertRaises(IAIndisponivel):
            ia.transcrever(b"OggS" + b"x" * 300)

    def test_freio_proprio_antes_do_limite_gratuito(self):
        tempo = [0.0]
        ia, transporte = agente(*[(200, b'{"text":"Sim"}')] * 19, relogio=lambda: tempo[0])
        for _ in range(18):
            ia.transcrever(b"OggS" + b"x" * 300)
        with self.assertRaises(IAIndisponivel) as erro:
            ia.transcrever(b"OggS" + b"x" * 300)
        self.assertEqual(erro.exception.motivo, "limite")
        self.assertEqual(len(transporte.pedidos), 18)
        tempo[0] = 61
        self.assertEqual(ia.transcrever(b"OggS" + b"x" * 300), "Sim")


class Entendimento(unittest.TestCase):
    def test_pedido_usa_formato_garantido_e_limpa_o_nome(self):
        ia, transporte = agente(resposta_modelo({"intencao": "responder", "campo": None, "valor": "Maria das Dores.", "fala": None}))
        resultado = ia.entender("Meu nome é Maria das Dores.", "resposta", "nome")
        self.assertEqual(resultado, {"intencao": "responder", "campo": "nome", "valor": "Maria das Dores", "fala": None})
        corpo = json.loads(transporte.pedidos[0]["corpo"])
        self.assertEqual(transporte.pedidos[0]["url"], "https://api.groq.com/openai/v1/chat/completions")
        self.assertEqual(corpo["model"], "openai/gpt-oss-20b", "O modelo mais rápido vem primeiro")
        self.assertEqual(corpo["response_format"]["type"], "json_schema")
        self.assertTrue(corpo["response_format"]["json_schema"]["strict"])
        esquema = corpo["response_format"]["json_schema"]["schema"]
        self.assertEqual(sorted(esquema["required"]), sorted(esquema["properties"]))
        self.assertFalse(esquema["additionalProperties"])
        self.assertIn("rural", corpo["messages"][0]["content"])
        self.assertEqual(json.loads(corpo["messages"][1]["content"])["transcricao"], "Meu nome é Maria das Dores.")

    def test_falas_inventadas_no_silencio_sao_descartadas(self):
        ia = AgenteIA(chave="x")
        for inventada in ("Obrigado.", "Tchau, tchau!", "Legenda por Sônia Ruberti", "Música"):
            self.assertEqual(ia._texto_ouvido({"text": inventada}), "", inventada)
        # A mesma palavra dentro de uma resposta de verdade continua valendo.
        self.assertEqual(ia._texto_ouvido({"text": "Obrigado, meu nome é José."}), "Obrigado, meu nome é José.")

    def test_modelo_sem_formato_garantido_usa_json_simples_e_lembra(self):
        certo = {"intencao": "sim", "campo": None, "valor": None, "fala": None}
        ia, transporte = agente((400, b'{"error":{}}'), (200, json.dumps({"choices": [{"message": {"content": "Claro: " + json.dumps(certo)}}]}).encode()), resposta_modelo(certo))
        self.assertEqual(ia.entender("isso aí", "confirmacao", "nome", "Maria")["intencao"], "sim")
        self.assertEqual(json.loads(transporte.pedidos[1]["corpo"])["response_format"], {"type": "json_object"})
        ia.entender("isso aí", "confirmacao", "nome", "Maria")
        self.assertEqual(json.loads(transporte.pedidos[2]["corpo"])["response_format"], {"type": "json_object"})

    def test_limite_no_primeiro_modelo_tenta_o_segundo(self):
        ia, transporte = agente((429, b"{}"), resposta_modelo({"intencao": "nao", "campo": None, "valor": None, "fala": None}))
        self.assertEqual(ia.entender("tá errado", "confirmacao", "nome", "Maria")["intencao"], "nao")
        self.assertEqual([json.loads(p["corpo"])["model"] for p in transporte.pedidos], ["openai/gpt-oss-20b", "openai/gpt-oss-120b"])

    def test_sem_internet_ou_chave_recusada_nao_insiste(self):
        for resposta, motivo in ((OSError("sem internet"), "falha"), ((401, b"{}"), "sem-chave")):
            ia, transporte = agente(resposta)
            with self.assertRaises(IAIndisponivel) as erro:
                ia.entender("Maria", "resposta", "nome")
            self.assertEqual(erro.exception.motivo, motivo)
            self.assertEqual(len(transporte.pedidos), 1)

    def test_resposta_ilegivel_tenta_outro_modelo_e_depois_desiste(self):
        ia, transporte = agente((200, b"nao e json"), (200, json.dumps({"choices": [{"message": {"content": "sem chaves"}}]}).encode()))
        with self.assertRaises(IAIndisponivel):
            ia.entender("Maria", "resposta", "nome")
        self.assertEqual(len(transporte.pedidos), 2)


class Conferencia(unittest.TestCase):
    def setUp(self):
        self.ia = AgenteIA(chave="gsk_teste", categorias=CATEGORIAS)

    def conferir(self, bruto, fala, fase, campo):
        return self.ia.conferir({"campo": None, "valor": None, "fala": None, **bruto}, fala, fase, campo)

    def test_publicar_exige_a_palavra_e_nenhuma_negacao(self):
        publicar = {"intencao": "publicar"}
        self.assertEqual(self.conferir(publicar, "Pode publicar sim.", "revisao", "telefone")["intencao"], "publicar")
        self.assertEqual(self.conferir(publicar, "Eu autorizo.", "revisao", "telefone")["intencao"], "publicar")
        for fala in ("Não quero publicar ainda.", "Sim.", "Tá bom, pode ir."):
            self.assertEqual(self.conferir(publicar, fala, "revisao", "telefone")["intencao"], "duvida")
        self.assertEqual(self.conferir(publicar, "Pode publicar.", "confirmacao", "nome")["intencao"], "duvida")

    def test_cancelar_exige_a_palavra(self):
        self.assertEqual(self.conferir({"intencao": "cancelar"}, "Quero cancelar tudo.", "resposta", "nome")["intencao"], "cancelar")
        self.assertEqual(self.conferir({"intencao": "cancelar"}, "Não sei.", "resposta", "nome")["intencao"], "duvida")

    def test_valores_seguem_as_regras_do_formulario(self):
        responder = lambda valor: {"intencao": "responder", "valor": valor}
        self.assertEqual(self.conferir(responder("rural"), "Vendo beiju e goma.", "resposta", "categoria")["valor"], "rural")
        self.assertEqual(self.conferir(responder("pesca"), "Sou pescador.", "resposta", "categoria")["intencao"], "duvida")
        self.assertEqual(self.conferir(responder("86999812345"), "É 86 99981-2345.", "resposta", "telefone")["valor"], "86999812345")
        self.assertEqual(self.conferir(responder("86999812345"), "É 86 9998.", "resposta", "telefone")["intencao"], "duvida")
        self.assertEqual(self.conferir(responder("x" * 81), "x" * 81, "resposta", "nome")["intencao"], "duvida")
        self.assertEqual(self.conferir({"intencao": "responder", "valor": None}, "hum", "resposta", "nome")["intencao"], "duvida")
        self.assertEqual(self.conferir({"intencao": "pular"}, "não tenho", "resposta", "telefone"), {"intencao": "pular", "campo": "telefone", "valor": "", "fala": None})
        self.assertEqual(self.conferir({"intencao": "pular"}, "não tenho", "resposta", "nome")["intencao"], "duvida")

    def test_nao_aceita_informacao_que_a_pessoa_nao_disse(self):
        responder = lambda valor: {"intencao": "responder", "valor": valor}
        self.assertEqual(self.conferir(responder("Maria Aparecida"), "Meu nome é Maria.", "resposta", "nome")["intencao"], "duvida")
        self.assertEqual(self.conferir(responder("Maria"), "Não, é Maria com i.", "confirmacao", "nome")["valor"], "Maria")
        self.assertEqual(self.conferir(responder("Faço os melhores bolos da região, com entrega grátis."), "Eu faço bolo.", "resposta", "descricao")["intencao"], "duvida")
        self.assertEqual(self.conferir(responder("Faço bolos de milho por encomenda."), "É... eu faço, faço bolo de milho por encomenda, terminei.", "resposta", "descricao")["valor"], "Faço bolos de milho por encomenda.")

    def test_intencao_fora_de_hora_e_corrigir(self):
        self.assertEqual(self.conferir({"intencao": "sim"}, "sim", "resposta", "nome")["intencao"], "duvida")
        self.assertEqual(self.conferir({"intencao": "apagar_tudo"}, "x", "revisao", "nome")["intencao"], "duvida")
        self.assertEqual(self.conferir({"intencao": "corrigir", "campo": "comunidade"}, "muda o bairro", "revisao", "telefone")["campo"], "comunidade")
        self.assertEqual(self.conferir({"intencao": "corrigir", "campo": "senha"}, "muda a senha", "revisao", "telefone")["intencao"], "duvida")
        fala = self.conferir({"intencao": "duvida", "fala": "  Pode   repetir?  " + "x" * 400}, "hã", "resposta", "nome")["fala"]
        self.assertTrue(fala.startswith("Pode repetir?"))
        self.assertLessEqual(len(fala), 240)


class ConexaoHTTP(unittest.TestCase):
    """Usa um servidor local no lugar da Groq para exercitar o envio verdadeiro (urllib)."""

    def setUp(self):
        import threading
        from http.server import BaseHTTPRequestHandler, HTTPServer
        recebidos = self.recebidos = []

        class Servico(BaseHTTPRequestHandler):
            def do_POST(self):
                corpo = self.rfile.read(int(self.headers["Content-Length"]))
                recebidos.append((self.path, dict(self.headers), corpo))
                if self.headers["Authorization"] != "Bearer gsk_local":
                    status, resposta = 401, {"error": {"message": "Invalid API Key"}}
                elif self.path.endswith("/audio/transcriptions"):
                    status, resposta = 200, {"text": "Bairro Centro.", "segments": [{"text": " Bairro Centro.", "no_speech_prob": 0.01, "avg_logprob": -0.1}]}
                else:
                    status, resposta = 200, {"choices": [{"message": {"content": json.dumps({"intencao": "responder", "campo": None, "valor": "Centro", "fala": None})}}]}
                dados = json.dumps(resposta).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(dados)))
                self.end_headers()
                self.wfile.write(dados)

            def log_message(self, *argumentos):
                pass

        self.servidor = HTTPServer(("127.0.0.1", 0), Servico)
        threading.Thread(target=self.servidor.serve_forever, daemon=True).start()
        self.url = f"http://127.0.0.1:{self.servidor.server_port}/openai/v1"

    def tearDown(self):
        self.servidor.shutdown()
        self.servidor.server_close()

    def test_ouve_e_entende_por_http_de_verdade(self):
        ia = AgenteIA(chave="gsk_local", url=self.url, categorias=CATEGORIAS)
        self.assertEqual(ia.transcrever(b"OggS" + bytes(range(256)) * 2, "resposta.ogg", "comunidade"), "Bairro Centro.")
        self.assertEqual(ia.entender("Bairro Centro.", "resposta", "comunidade")["valor"], "Centro")
        caminho, cabecalhos, corpo = self.recebidos[0]
        self.assertEqual(caminho, "/openai/v1/audio/transcriptions")
        limite = cabecalhos["Content-Type"].split("boundary=")[1].encode()
        partes = corpo.split(b"--" + limite)
        self.assertEqual(len(partes), 8, "cinco campos, o arquivo e o fechamento")
        self.assertTrue(partes[-1].startswith(b"--"))
        self.assertIn(b"OggS" + bytes(range(256)) * 2, partes[6], "o áudio chega inteiro, byte a byte")
        self.assertEqual(json.loads(self.recebidos[1][2])["messages"][1]["role"], "user")

    def test_chave_recusada_e_servico_desligado(self):
        with self.assertRaises(IAIndisponivel) as erro:
            AgenteIA(chave="gsk_errada", url=self.url, categorias=CATEGORIAS).entender("Maria", "resposta", "nome")
        self.assertEqual(erro.exception.motivo, "sem-chave")
        with self.assertRaises(IAIndisponivel) as erro:
            AgenteIA(chave="gsk_local", url="http://127.0.0.1:9/openai/v1", categorias=CATEGORIAS).entender("Maria", "resposta", "nome")
        self.assertEqual((erro.exception.motivo, erro.exception.status), ("falha", None))

    def test_aplicativo_real_liga_a_ia_pela_chave_do_ambiente(self):
        with tempfile.TemporaryDirectory() as pasta, patch.dict(os.environ, {"GROQ_API_KEY": "gsk_local", "BATALHA_IA_URL": self.url}, clear=False):
            app = create_app({"DATA_DIR": pasta})
            self.assertTrue(app.extensions["agente_ia"].ativo)
            cliente = app.test_client()
            self.assertIn('data-ia="1"', cliente.get("/cadastro").get_data(as_text=True))
            with cliente.session_transaction() as sessao:
                csrf = sessao["csrf"]
            resposta = cliente.post("/api/ia/transcrever", content_type="multipart/form-data",
                                    data={"campo": "comunidade", "fase": "resposta", "csrf": csrf, "audio": (io.BytesIO(gravacao("x")), "resposta.ogg")})
            self.assertEqual(resposta.json, {"texto": "Bairro Centro."})
        with tempfile.TemporaryDirectory() as pasta, patch.dict(os.environ, {}, clear=False):
            os.environ.pop("GROQ_API_KEY", None)
            os.environ.pop("BATALHA_IA_CHAVE", None)
            self.assertFalse(create_app({"DATA_DIR": pasta}).extensions["agente_ia"].ativo)


class Rotas(unittest.TestCase):
    def setUp(self):
        self.dados = tempfile.TemporaryDirectory()
        self.app = create_app({"TESTING": True, "DATA_DIR": self.dados.name})
        self.cliente = self.app.test_client()
        self.cliente.get("/")
        with self.cliente.session_transaction() as sessao:
            self.csrf = sessao["csrf"]

    def tearDown(self):
        self.dados.cleanup()

    def ouvir(self, fala, campo="nome", fase="resposta", csrf=None, conteudo=None):
        dados = {"campo": campo, "fase": fase, "csrf": self.csrf if csrf is None else csrf,
                 "audio": (io.BytesIO(gravacao(fala) if conteudo is None else conteudo), "resposta.ogg")}
        return self.cliente.post("/api/ia/transcrever", data=dados, content_type="multipart/form-data")

    def test_sem_chave_o_app_funciona_como_antes(self):
        self.assertFalse(self.app.extensions["agente_ia"].ativo)
        pagina = self.cliente.get("/cadastro").get_data(as_text=True)
        self.assertIn('data-ia="0"', pagina)
        self.assertIn("reconhecimento", pagina)
        self.assertEqual(self.ouvir("Maria").status_code, 503)
        resposta = self.cliente.post("/api/ia/entender", data={"texto": "Maria", "fase": "resposta", "campo": "nome", "csrf": self.csrf})
        self.assertEqual((resposta.status_code, resposta.json["motivo"]), (503, "sem-chave"))
        self.assertIn("Desativado", self.cliente.get("/ajuda").get_data(as_text=True))

    def test_com_ia_ouve_entende_e_nao_guarda_o_audio(self):
        simulado = self.app.extensions["agente_ia"] = AgenteSimulado()
        pagina = self.cliente.get("/cadastro").get_data(as_text=True)
        self.assertIn('data-ia="1"', pagina)
        self.assertIn("inteligência artificial", pagina)
        self.assertIn("Ativo nesta instalação", self.cliente.get("/ajuda").get_data(as_text=True))
        resposta = self.ouvir("Meu nome é Dona Rosa.")
        self.assertEqual((resposta.status_code, resposta.json), (200, {"texto": "Meu nome é Dona Rosa."}))
        self.assertEqual(resposta.headers["Cache-Control"], "no-store")
        self.assertEqual(simulado.ouvidas[0][1:], ("nome", "resposta", "resposta.ogg"))
        self.assertEqual(list((Path(self.dados.name) / "uploads").iterdir()), [])
        resposta = self.cliente.post("/api/ia/entender", data={"texto": "Meu nome é Dona Rosa.", "fase": "resposta", "campo": "nome", "csrf": self.csrf})
        self.assertEqual(resposta.json, {"intencao": "responder", "campo": "nome", "valor": "Dona Rosa", "fala": None})

    def test_validacao_nao_aciona_o_servico(self):
        simulado = self.app.extensions["agente_ia"] = AgenteSimulado()
        self.assertEqual(self.ouvir("Maria", csrf="invalido").status_code, 400)
        self.assertEqual(self.ouvir("Maria", campo="senha").status_code, 400)
        self.assertEqual(self.ouvir("Maria", fase="outra").status_code, 400)
        self.assertEqual(self.ouvir("", conteudo=b"curto").status_code, 400)
        self.assertEqual(self.ouvir("", conteudo=b"<html>" + b"x" * 300).status_code, 400)
        self.assertEqual(self.ouvir("", conteudo=b"OggS" + b"x" * (4 * 1024 * 1024)).status_code, 400)
        for dados in ({"texto": "", "fase": "resposta", "campo": "nome"}, {"texto": "x" * 1001, "fase": "resposta", "campo": "nome"},
                      {"texto": "Maria", "fase": "resposta", "campo": "senha"}, {"texto": "Maria", "fase": "x", "campo": "nome"}):
            self.assertEqual(self.cliente.post("/api/ia/entender", data={**dados, "csrf": self.csrf}).status_code, 400)
        self.assertEqual(self.cliente.post("/api/ia/entender", data={"texto": "Maria", "fase": "resposta", "campo": "nome"}).status_code, 400)
        self.assertEqual((simulado.ouvidas, simulado.perguntas), ([], 0))

    def test_falha_do_servico_avisa_o_navegador_para_usar_a_alternativa(self):
        self.app.extensions["agente_ia"] = AgenteSimulado()
        resposta = self.ouvir("sem escuta agora")
        self.assertEqual((resposta.status_code, resposta.json["motivo"]), (503, "falha"))
        resposta = self.cliente.post("/api/ia/entender", data={"texto": "falhar agora", "fase": "resposta", "campo": "nome", "csrf": self.csrf})
        self.assertEqual(resposta.status_code, 503)
        self.assertEqual(self.ouvir("silêncio").json, {"texto": ""})


if __name__ == "__main__":
    unittest.main()
