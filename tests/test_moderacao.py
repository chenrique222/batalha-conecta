"""Página de moderação: senha, bloqueio de tentativas e exclusão de perfis e avaliações."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app import create_app
from dados import conectar

SENHA = "professor-batalha-2026"


class Moderacao(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.TemporaryDirectory()
        self.app = create_app({"TESTING": True, "DATA_DIR": self.pasta.name, "MODERACAO_SENHA": SENHA})
        self.cliente = self.app.test_client()
        self.banco = Path(self.pasta.name) / "batalha.db"
        self.uploads = Path(self.pasta.name) / "uploads"

    def tearDown(self):
        self.pasta.cleanup()

    def csrf(self):
        self.cliente.get("/moderacao")
        with self.cliente.session_transaction() as sessao:
            return sessao["csrf"]

    def entrar(self, senha=SENHA):
        return self.cliente.post("/moderacao/entrar", data={"csrf": self.csrf(), "senha": senha})

    def perfil_com_arquivos(self):
        """Cria um perfil com foto, áudio e uma avaliação, com os arquivos no disco."""
        self.uploads.mkdir(parents=True, exist_ok=True)
        nomes = {"foto": "a" * 32 + ".webp", "audio": "b" * 32 + ".ogg", "avaliacao": "c" * 32 + ".webm"}
        for nome in nomes.values():
            (self.uploads / nome).write_bytes(b"x")
        c = conectar(self.banco)
        with c:
            c.execute("INSERT INTO profissionais(nome,categoria,comunidade,foto,audio,envio_id) VALUES ('Perfil falso','servicos','Centro',?,?,'falso')",
                      (nomes["foto"], nomes["audio"]))
            ident = c.execute("SELECT id FROM profissionais WHERE envio_id='falso'").fetchone()[0]
            c.execute("INSERT OR IGNORE INTO fotos(profissional_id,arquivo,posicao) VALUES (?,?,0)", (ident, nomes["foto"]))
            c.execute("INSERT INTO avaliacoes(profissional_id,nota,audio,envio_id) VALUES (?,1,?,'av-falsa')", (ident, nomes["avaliacao"]))
        c.close()
        return ident, nomes

    def test_sem_senha_configurada_a_pagina_nao_existe(self):
        with patch.dict("os.environ", {"BATALHA_MODERACAO_SENHA": ""}):
            app = create_app({"TESTING": True, "DATA_DIR": self.pasta.name})
        cliente = app.test_client()
        self.assertEqual(cliente.get("/moderacao").status_code, 404)

    def test_senha_curta_nao_permite_entrar(self):
        app = create_app({"TESTING": True, "DATA_DIR": self.pasta.name, "MODERACAO_SENHA": "1234"})
        cliente = app.test_client()
        self.assertIn("pelo menos 8 caracteres", cliente.get("/moderacao").get_data(as_text=True))
        with cliente.session_transaction() as sessao:
            csrf = sessao["csrf"]
        cliente.post("/moderacao/entrar", data={"csrf": csrf, "senha": "1234"})
        self.assertNotIn("Sair da moderação", cliente.get("/moderacao").get_data(as_text=True))

    def test_senha_errada_e_certa(self):
        pagina = self.cliente.get("/moderacao")
        self.assertEqual(pagina.status_code, 200)
        self.assertEqual(pagina.headers["X-Robots-Tag"], "noindex, nofollow")
        self.entrar("errada")
        self.assertIn("Senha incorreta", self.cliente.get("/moderacao").get_data(as_text=True))
        self.entrar()
        texto = self.cliente.get("/moderacao").get_data(as_text=True)
        self.assertIn("Sair da moderação", texto)
        self.assertIn("Farinha do Seu João", texto, "A lista mostra os perfis")

    def test_apagar_sem_entrar_e_proibido(self):
        ident, _ = self.perfil_com_arquivos()
        resposta = self.cliente.post(f"/moderacao/perfil/{ident}/apagar", data={"csrf": self.csrf(), "confirmar": "sim"})
        self.assertEqual(resposta.status_code, 403)
        self.assertIsNotNone(conectar(self.banco).execute("SELECT 1 FROM profissionais WHERE id=?", (ident,)).fetchone())

    def test_apagar_perfil_leva_fotos_avaliacoes_e_arquivos(self):
        ident, nomes = self.perfil_com_arquivos()
        self.entrar()
        csrf = self.csrf()
        self.cliente.post(f"/moderacao/perfil/{ident}/apagar", data={"csrf": csrf})
        self.assertIn("Marque a caixa", self.cliente.get("/moderacao").get_data(as_text=True), "Sem confirmar, nada é apagado")
        self.assertTrue((self.uploads / nomes["foto"]).exists())
        self.cliente.post(f"/moderacao/perfil/{ident}/apagar", data={"csrf": csrf, "confirmar": "sim"})
        self.assertIn("Perfil falso", self.cliente.get("/moderacao").get_data(as_text=True).split("Perfis (")[0], "Aviso de confirmação")
        c = conectar(self.banco)
        for tabela, coluna in (("profissionais", "id"), ("fotos", "profissional_id"), ("avaliacoes", "profissional_id")):
            self.assertEqual(c.execute(f"SELECT COUNT(*) FROM {tabela} WHERE {coluna}=?", (ident,)).fetchone()[0], 0, tabela)
        c.close()
        for nome in nomes.values():
            self.assertFalse((self.uploads / nome).exists(), nome)
        self.assertEqual(self.cliente.get(f"/profissional/{ident}").status_code, 404)

    def test_apagar_avaliacao(self):
        ident, nomes = self.perfil_com_arquivos()
        self.entrar()
        av = conectar(self.banco).execute("SELECT id FROM avaliacoes WHERE envio_id='av-falsa'").fetchone()[0]
        self.cliente.post(f"/moderacao/avaliacao/{av}/apagar", data={"csrf": self.csrf(), "confirmar": "sim"})
        c = conectar(self.banco)
        self.assertEqual(c.execute("SELECT COUNT(*) FROM avaliacoes WHERE id=?", (av,)).fetchone()[0], 0)
        self.assertIsNotNone(c.execute("SELECT 1 FROM profissionais WHERE id=?", (ident,)).fetchone(), "O perfil continua")
        c.close()
        self.assertFalse((self.uploads / nomes["avaliacao"]).exists())
        self.assertTrue((self.uploads / nomes["foto"]).exists())

    def test_muitas_tentativas_fecham_a_entrada(self):
        for _ in range(10):
            self.entrar("errada")
        self.entrar()  # mesmo a senha certa espera o bloqueio acabar
        texto = self.cliente.get("/moderacao").get_data(as_text=True)
        self.assertIn("Muitas tentativas", texto)
        self.assertNotIn("Sair da moderação", texto)

    def test_sair(self):
        self.entrar()
        self.cliente.post("/moderacao/sair", data={"csrf": self.csrf()})
        self.assertNotIn("Sair da moderação", self.cliente.get("/moderacao").get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()
