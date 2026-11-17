"""Atualização de categorias em um banco antigo, sem alterar perfis e seus arquivos."""
import tempfile
import unittest
from pathlib import Path
from dados import preparar_banco, conectar, CATEGORIAS


class Categorias(unittest.TestCase):
    def test_migracao_preserva_dados_e_so_executa_uma_vez(self):
        with tempfile.TemporaryDirectory() as pasta:
            banco = Path(pasta) / "teste.db"
            preparar_banco(banco)
            c = conectar(banco)
            with c:
                c.execute("DELETE FROM migracoes WHERE nome='categorias-v06'")
                c.execute("UPDATE profissionais SET categoria='servicos' WHERE envio_id='exemplo-3'")
                c.execute("""INSERT INTO profissionais
                    (nome,categoria,descricao,comunidade,telefone,foto,audio,envio_id)
                    VALUES ('Pedro · Pedreiro','servicos','Reformas','Centro','86999990000','foto.webp','voz.ogg','pessoa-real')""")
                identificador = c.execute("SELECT id FROM profissionais WHERE envio_id='pessoa-real'").fetchone()[0]
                c.execute("INSERT INTO fotos(profissional_id,arquivo,posicao) VALUES (?,'foto.webp',0)", (identificador,))
                c.execute("INSERT INTO avaliacoes(profissional_id,nota,audio,envio_id) VALUES (?,5,'avaliacao.ogg','avaliacao-1')", (identificador,))
                for nome, categoria, envio in [('Plantio do José','rural','plantio'), ('Farinha da Luzia','rural','farinha'), ('Costura da Ana','servicos','costura')]:
                    c.execute("INSERT INTO profissionais(nome,categoria,comunidade,envio_id) VALUES (?,?,'Centro',?)", (nome,categoria,envio))
            antes = dict(c.execute("SELECT * FROM profissionais WHERE id=?", (identificador,)).fetchone())
            c.close()
            preparar_banco(banco)
            c = conectar(banco)
            depois = dict(c.execute("SELECT * FROM profissionais WHERE id=?", (identificador,)).fetchone())
            self.assertEqual(depois, {**antes, "categoria":"manutencao"})
            categorias = dict(c.execute("SELECT envio_id,categoria FROM profissionais"))
            self.assertEqual(categorias['exemplo-3'], 'manutencao')
            self.assertEqual(categorias['exemplo-2'], 'rural')
            self.assertEqual(categorias['plantio'], 'servicos')
            self.assertEqual(categorias['farinha'], 'rural')
            self.assertEqual(categorias['costura'], 'servicos')
            self.assertEqual(c.execute("SELECT arquivo FROM fotos WHERE profissional_id=?", (identificador,)).fetchone()[0], 'foto.webp')
            self.assertEqual(c.execute("SELECT audio FROM avaliacoes WHERE profissional_id=?", (identificador,)).fetchone()[0], 'avaliacao.ogg')
            with c:
                c.execute("UPDATE profissionais SET categoria='servicos' WHERE id=?", (identificador,))
            c.close()
            preparar_banco(banco)
            c = conectar(banco)
            self.assertEqual(c.execute("SELECT categoria FROM profissionais WHERE id=?", (identificador,)).fetchone()[0], 'servicos')
            self.assertEqual(c.execute("SELECT COUNT(*) FROM profissionais WHERE envio_id='exemplo-3'").fetchone()[0], 1)
            c.close()

    def test_categorias_distintas_e_imagens_presentes(self):
        raiz = Path(__file__).resolve().parents[1]
        self.assertEqual(len({c['id'] for c in CATEGORIAS}), 5)
        for categoria in CATEGORIAS:
            self.assertTrue((raiz/'static/artes'/categoria['imagem']).is_file(), categoria['imagem'])
