"""Verificações dos cadastros, arquivos e banco compartilhado. Sem serviços externos."""
import io
import re
import tempfile
import unittest
import wave
from pathlib import Path

from PIL import Image
from app import create_app
from dados import EXEMPLOS


class FluxoDoAplicativo(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.TemporaryDirectory()
        self.configuracao = {"TESTING": True, "DATA_DIR": self.pasta.name}
        self.app = create_app(self.configuracao)
        self.cliente = self.app.test_client()

    def tearDown(self):
        self.pasta.cleanup()

    def formulario(self):
        self.cliente.get("/cadastro")
        with self.cliente.session_transaction() as sessao:
            return {"csrf": sessao["csrf"], "envio_id": sessao["envio_id"],
                    "nome": "Oficina de teste", "categoria": "servicos",
                    "descricao": "Reparos demonstrativos", "comunidade": "Centro",
                    "telefone": "", "consentimento": "sim"}

    def test_busca_sem_acentos_e_filtro(self):
        resposta = self.cliente.get("/api/profissionais?busca=joao")
        self.assertEqual([p["nome"] for p in resposta.json], ["Farinha do Seu João"])
        resposta = self.cliente.get("/api/profissionais?categoria=artesanato")
        self.assertEqual(len(resposta.json), sum(1 for exemplo in EXEMPLOS if exemplo[1] == "artesanato"))
        self.assertNotIn("envio_id", resposta.json[0])
        self.assertEqual(self.cliente.get("/api/profissionais?busca=xyz-inexistente").json, [])

    def test_exemplos_por_atividade_e_contato_desligado(self):
        por_atividade = {}
        for exemplo in EXEMPLOS:
            por_atividade[exemplo[1]] = por_atividade.get(exemplo[1], 0) + 1
            self.assertRegex(exemplo[4], r"^869000001\d\d$", "Telefone fictício no padrão combinado")
        self.assertEqual(por_atividade, {"alimentacao": 4, "artesanato": 3, "costura": 2, "manutencao": 3, "servicos": 1})
        self.assertEqual(len({exemplo[0] for exemplo in EXEMPLOS}), len(EXEMPLOS), "Nomes sem repetição")
        barbeiro = next(p for p in self.cliente.get("/api/profissionais?busca=barbearia").json)
        pagina = self.cliente.get(f"/profissional/{barbeiro['id']}").get_data(as_text=True)
        self.assertIn("(86) 90000-0113", pagina)
        self.assertNotIn("wa.me/5586900000113", pagina, "Exemplo não abre WhatsApp")
        self.assertNotIn("tel:+5586900000113", pagina, "Exemplo não faz ligação")
        self.assertIn("o número é fictício", pagina)
        # Cada exemplo tem a sua ilustração, diferente da capa da atividade.
        pasta = Path(__file__).resolve().parent.parent / "static" / "exemplos"
        imagens = [exemplo[5] for exemplo in EXEMPLOS]
        self.assertEqual(len(set(imagens)), len(imagens))
        for imagem in imagens:
            self.assertTrue((pasta / imagem).is_file(), imagem)
        self.assertIn("/static/exemplos/leo.webp", pagina)
        self.assertIn("Ilustração de exemplo", pagina)
        lista = self.cliente.get("/profissionais").get_data(as_text=True)
        self.assertEqual(sum(lista.count(f"/static/exemplos/{imagem}") > 0 for imagem in imagens), len(imagens))

    def test_cadastro_persiste_e_outra_sessao_enxerga(self):
        campos = self.formulario()
        resposta = self.cliente.post("/cadastro", data=campos, headers={"Accept": "application/json"})
        self.assertEqual(resposta.status_code, 201, resposta.data)
        nova_app = create_app(self.configuracao)
        outro_cliente = nova_app.test_client()
        perfis = outro_cliente.get("/api/profissionais?busca=Oficina").json
        self.assertEqual(len(perfis), 1)
        self.assertEqual(outro_cliente.get(resposta.json["url"]).status_code, 200)
        self.cliente.post("/cadastro", data=campos, headers={"Accept": "application/json"})
        self.assertEqual(len(outro_cliente.get("/api/profissionais?busca=Oficina").json), 1)

    def test_campos_invalidos_e_csrf_nao_gravam(self):
        campos = self.formulario()
        campos["csrf"] = "invalido"
        self.assertEqual(self.cliente.post("/cadastro", data=campos).status_code, 400)
        campos = self.formulario()
        campos.update(nome="", telefone="123", categoria="inexistente", consentimento="nao")
        resposta = self.cliente.post("/cadastro", data=campos, headers={"Accept": "application/json"})
        self.assertEqual(resposta.status_code, 400)
        self.assertGreaterEqual(len(resposta.json["erros"]), 4)
        self.assertEqual(len(self.cliente.get("/api/profissionais").json), len(EXEMPLOS))

    def test_foto_audio_e_contato(self):
        campos = self.formulario()
        imagem = io.BytesIO()
        Image.new("RGB", (40, 60), "green").save(imagem, format="PNG")
        imagem.seek(0)
        som = io.BytesIO()
        with wave.open(som, "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(8000)
            wav.writeframes(b"\x00\x00" * 800)
        som.seek(0)
        campos.update(descricao="", telefone="(86) 99999-0000", foto=(imagem, "foto.png"), audio=(som, "voz.wav"))
        resposta = self.cliente.post("/cadastro", data=campos, headers={"Accept": "application/json"})
        self.assertEqual(resposta.status_code, 201, resposta.data)
        perfil = self.cliente.get(resposta.json["url"]).get_data(as_text=True)
        self.assertIn("https://wa.me/5586999990000", perfil)
        self.assertIn("tel:+5586999990000", perfil)
        for url in re.findall(r'"(/uploads/[^\"]+)"', perfil):
            with self.cliente.get(url) as arquivo:
                self.assertEqual(arquivo.status_code, 200)
        self.assertIn("Minha apresentação em áudio", perfil)

    def test_arquivos_invalidos_nao_deixam_residuos(self):
        campos = self.formulario()
        imagem = io.BytesIO()
        Image.new("RGB", (20, 20), "blue").save(imagem, format="PNG")
        imagem.seek(0)
        campos.update(foto=(imagem, "foto.png"), audio=(io.BytesIO(b"<script>teste</script>"), "voz.mp3"))
        resposta = self.cliente.post("/cadastro", data=campos, headers={"Accept": "application/json"})
        self.assertEqual(resposta.status_code, 400)
        self.assertEqual(list((Path(self.pasta.name) / "uploads").iterdir()), [])
        self.assertEqual(len(self.cliente.get("/api/profissionais").json), len(EXEMPLOS))

    def test_texto_e_busca_nao_viram_codigo(self):
        campos = self.formulario()
        campos["nome"] = '<script>alert("teste")</script>'
        resposta = self.cliente.post("/cadastro", data=campos, headers={"Accept": "application/json"})
        html = self.cliente.get(resposta.json["url"]).get_data(as_text=True)
        self.assertNotIn('<script>alert("teste")</script>', html)
        self.assertIn("&lt;script&gt;", html)
        self.assertEqual(self.cliente.get("/api/profissionais", query_string={"busca": "' OR 1=1 --"}).json, [])

    def test_paginas_pwa_e_erro(self):
        for caminho in ["/", "/profissionais", "/profissional/1", "/cadastro", "/ajuda", "/sw.js", "/static/offline.html", "/static/modo.js", "/static/acessibilidade.js", "/static/voz-logica.js", "/static/cadastro-voz.js"]:
            with self.cliente.get(caminho) as resposta:
                self.assertEqual(resposta.status_code, 200, caminho)
        manifest = self.cliente.get("/manifest.webmanifest")
        self.assertIn("application/manifest+json", manifest.content_type)
        for icone in manifest.json["icons"]:
            with self.cliente.get(icone["src"]) as resposta:
                self.assertEqual(resposta.status_code, 200)
                tamanho = int(icone["sizes"].split("x")[0])
                self.assertEqual(Image.open(io.BytesIO(resposta.data)).size, (tamanho, tamanho))
        manifest.close()
        self.assertEqual(self.cliente.get("/profissional/99999").status_code, 404)
        self.assertEqual(self.cliente.get("/uploads/arquivo.html").status_code, 404)

    def test_limite_de_upload(self):
        campos = self.formulario()
        self.app.config["MAX_CONTENT_LENGTH"] = 1024
        campos["audio"] = (io.BytesIO(b"x" * 5000), "voz.wav")
        resposta = self.cliente.post("/cadastro", data=campos, headers={"Accept": "application/json"})
        self.assertEqual(resposta.status_code, 413)


if __name__ == "__main__":
    unittest.main()
