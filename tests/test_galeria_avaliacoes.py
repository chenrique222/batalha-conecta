"""Integrações reais de arquivos, SQLite e sessões, sem acessar serviços externos."""
import io
import sqlite3
import tempfile
import unittest
import wave
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from PIL import Image
from app import create_app
from dados import preparar_banco, buscar_fotos, buscar_avaliacoes, atualizar_fotos


def imagem(cor="green"):
    arquivo = io.BytesIO()
    Image.new("RGB", (60, 40), cor).save(arquivo, "PNG")
    arquivo.seek(0)
    return arquivo, "foto.png"


def audio():
    arquivo = io.BytesIO()
    with wave.open(arquivo, "wb") as wav:
        wav.setnchannels(1); wav.setsampwidth(2); wav.setframerate(8000)
        wav.writeframes(b"\x01\x00" * 8000)
    arquivo.seek(0)
    return arquivo, "opiniao.wav"


class GaleriaEAvaliacoes(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.TemporaryDirectory()
        self.raiz = Path(self.pasta.name)
        self.banco = self.raiz / "batalha.db"
        self.app = create_app({"TESTING":True,"DATA_DIR":self.pasta.name})
        self.cliente = self.app.test_client()

    def tearDown(self): self.pasta.cleanup()

    def cadastro(self, fotos=0):
        self.cliente.get("/cadastro")
        with self.cliente.session_transaction() as sessao:
            campos = {"csrf":sessao["csrf"],"envio_id":sessao["envio_id"],"nome":"Galeria teste",
                      "categoria":"servicos","descricao":"Reparos","comunidade":"Centro","consentimento":"sim"}
        if fotos: campos["fotos"] = [imagem() for _ in range(fotos)]
        return campos

    def publicar(self, fotos=0):
        resposta = self.cliente.post("/cadastro",data=self.cadastro(fotos),headers={"Accept":"application/json"})
        self.assertEqual(resposta.status_code,201,resposta.data)
        return int(resposta.json["url"].split("/")[-1])

    def formulario_avaliacao(self, identificador=1):
        self.cliente.get(f"/profissional/{identificador}")
        with self.cliente.session_transaction() as sessao:
            return {"csrf":sessao["csrf"], "envio_id":sessao["avaliacoes_tokens"][str(identificador)],
                    "nota":"5", "consentimento":"sim", "audio":audio()}

    def test_cinco_fotos_persistem_com_capa_e_sexta_e_recusada(self):
        identificador = self.publicar(5)
        fotos = buscar_fotos(self.banco, identificador)
        self.assertEqual(len(fotos),5)
        pagina = self.cliente.get(f"/profissional/{identificador}").text
        self.assertEqual(pagina.count('data-ampliar-foto='),5)
        for foto in fotos:
            with self.cliente.get('/uploads/'+foto['arquivo']) as resposta:
                self.assertEqual(resposta.status_code,200)
                self.assertEqual(Image.open(io.BytesIO(resposta.data)).format, "WEBP")
        resposta = self.cliente.post("/cadastro", data=self.cadastro(6),headers={"Accept":"application/json"})
        self.assertEqual(resposta.status_code,400)
        self.assertEqual(len(list((self.raiz/'uploads').iterdir())),5)

    def test_lote_parcial_invalido_e_foto_grande_nao_deixam_residuos(self):
        campos = self.cadastro(2)
        campos["fotos"].append((io.BytesIO(b'nao e imagem'), 'foto.png'))
        self.assertEqual(self.cliente.post('/cadastro',data=campos).status_code,400)
        self.assertEqual(list((self.raiz/'uploads').iterdir()),[])
        campos = self.cadastro()
        campos['fotos'] = [(io.BytesIO(b'x'*(5*1024*1024+1)), 'foto.png')]
        self.assertEqual(self.cliente.post('/cadastro',data=campos).status_code,400)

    def test_migracao_preserva_foto_antiga_e_nao_duplica(self):
        with sqlite3.connect(self.banco) as conexao:
            conexao.execute("UPDATE profissionais SET foto = ? WHERE id = 1", ('a'*32+'.webp',))
        preparar_banco(self.banco); preparar_banco(self.banco)
        self.assertEqual(len(buscar_fotos(self.banco,1)),1)

    def test_so_criador_edita_fotos_e_limite_considera_as_atuais(self):
        identificador = self.publicar(5)
        fotos = buscar_fotos(self.banco,identificador)
        with self.cliente.session_transaction() as sessao: csrf = sessao['csrf']
        url = f'/profissional/{identificador}/fotos'
        resposta = self.cliente.post(url,data={'csrf':csrf,'fotos':[imagem()]})
        self.assertEqual(resposta.status_code,400)
        self.assertEqual(len(list((self.raiz/'uploads').iterdir())),5)
        resposta = self.cliente.post(url,data={'csrf':csrf,'remover':str(fotos[0]['id']),'fotos':[imagem('red')]})
        self.assertEqual(resposta.status_code,200)
        self.assertEqual(len(buscar_fotos(self.banco,identificador)),5)
        self.assertFalse((self.raiz/'uploads'/fotos[0]['arquivo']).exists())
        outro = self.app.test_client(); outro.get('/')
        with outro.session_transaction() as sessao: csrf_outro = sessao['csrf']
        self.assertEqual(outro.post(url,data={'csrf':csrf_outro,'fotos':[imagem()]}).status_code,403)

    def test_limite_de_fotos_resiste_a_envios_simultaneos(self):
        identificador = self.publicar(4)
        def adicionar(nome):
            try: atualizar_fotos(self.banco, identificador, [nome], set()); return True
            except ValueError: return False
        with ThreadPoolExecutor(max_workers=2) as executor:
            resultados = list(executor.map(adicionar,['novo1.webp','novo2.webp']))
        self.assertEqual(sorted(resultados),[False,True])
        self.assertEqual(len(buscar_fotos(self.banco,identificador)),5)

    def test_avaliacao_reproduzivel_persiste_e_retry_nao_duplica(self):
        campos = self.formulario_avaliacao()
        campos['nome'] = '<script>nome</script>'
        resposta = self.cliente.post('/profissional/1/avaliacoes',data=campos)
        self.assertEqual(resposta.status_code,201,resposta.data)
        campos['audio'] = audio()
        self.assertEqual(self.cliente.post('/profissional/1/avaliacoes',data=campos).status_code,200)
        dados = buscar_avaliacoes(self.banco,1)
        self.assertEqual(dados['total'],1); self.assertEqual(dados['media'],5)
        outra = create_app({'TESTING':True,'DATA_DIR':self.pasta.name}).test_client()
        pagina = outra.get('/profissional/1').text
        self.assertIn('&lt;script&gt;nome&lt;/script&gt;',pagina)
        self.assertNotIn('<script>nome</script>',pagina)
        with outra.get('/uploads/'+dados['itens'][0]['audio']) as arquivo:
            self.assertEqual(arquivo.status_code,200)
            self.assertEqual(arquivo.data[:4],b'RIFF')

    def test_avaliacoes_invalidas_nao_gravam(self):
        for alteracao in [{'nota':'0'},{'nota':'6'},{'nota':''},{'consentimento':'nao'},{'csrf':'errado'},
                          {'envio_id':'errado'},{'nome':'a'*81},{'audio':(io.BytesIO(b'<html>texto</html>'),'voz.mp3')}]:
            campos = self.formulario_avaliacao(); campos.update(alteracao)
            resposta = self.cliente.post('/profissional/1/avaliacoes',data=campos)
            self.assertEqual(resposta.status_code,400,resposta.data)
        campos=self.formulario_avaliacao(); del campos['audio']
        self.assertEqual(self.cliente.post('/profissional/1/avaliacoes',data=campos).status_code,400)
        self.assertEqual(buscar_avaliacoes(self.banco,1)['total'],0)
        self.assertEqual(list((self.raiz/'uploads').iterdir()),[])

    def test_token_vinculado_ao_perfil_e_audio_muito_grande_recusado(self):
        campos=self.formulario_avaliacao()
        self.assertEqual(self.cliente.post('/profissional/2/avaliacoes',data=campos).status_code,400)
        campos=self.formulario_avaliacao(); campos['audio']=(io.BytesIO(b'RIFF'+b'x'*(10*1024*1024)), 'voz.wav')
        self.assertEqual(self.cliente.post('/profissional/1/avaliacoes',data=campos).status_code,400)
        self.assertEqual(list((self.raiz/'uploads').iterdir()),[])

    def test_media_e_paginacao_dez_por_pagina(self):
        for indice in range(12):
            campos=self.formulario_avaliacao(); campos['nota']=str(indice%5+1)
            self.assertEqual(self.cliente.post('/profissional/1/avaliacoes',data=campos).status_code,201)
        resumo=buscar_avaliacoes(self.banco,1)
        self.assertEqual(resumo['total'],12); self.assertEqual(len(resumo['itens']),10)
        self.assertAlmostEqual(resumo['media'],33/12)
        self.assertEqual(len(buscar_avaliacoes(self.banco,1,2)['itens']),2)
