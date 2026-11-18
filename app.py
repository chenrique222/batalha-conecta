"""Batalha Conecta — versão didática 0.7, para testes locais.

Python recebe pedidos do navegador, consulta o banco e devolve as páginas.
Leia GUIA_DO_PROFESSOR.md para estudar uma parte de cada vez.
"""
import hmac
import io
import os
import re
import secrets
import threading
import time
import sqlite3
import warnings
from pathlib import Path
from uuid import uuid4

from flask import Flask, abort, jsonify, redirect, render_template, request, send_file, send_from_directory, session, url_for
from PIL import Image, ImageOps, UnidentifiedImageError

from dados import CATEGORIAS, buscar_envio, buscar_por_id, buscar_profissionais, cadastrar_profissional, preparar_banco
from dados import buscar_fotos, atualizar_fotos, buscar_avaliacoes, cadastrar_avaliacao, buscar_avaliacao_envio
from dados import listar_para_moderacao, listar_avaliacoes_recentes, apagar_profissional, apagar_avaliacao
from voz import VozNatural, VozIndisponivel, VOZES
from ia import AgenteIA, IAIndisponivel, CAMPOS, FASES, carregar_env

PASTA = Path(__file__).resolve().parent
# A chave gratuita do assistente de IA fica no arquivo .env, fora do ZIP e do Git.
carregar_env(PASTA / ".env")
Image.MAX_IMAGE_PIXELS = 20_000_000


def salvar_foto(arquivo, destino):
    """Confere a imagem, retira metadados e cria um nome aleatório."""
    if not arquivo or not arquivo.filename:
        return None
    if len(arquivo.read(5 * 1024 * 1024 + 1)) > 5 * 1024 * 1024:
        raise ValueError("Cada foto pode ter no máximo 5 MB.")
    arquivo.stream.seek(0)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(arquivo.stream) as original:
                if original.format not in {"JPEG", "PNG", "WEBP"}:
                    raise ValueError("Escolha uma foto JPG, PNG ou WebP.")
                foto = ImageOps.exif_transpose(original).convert("RGB")
                foto.thumbnail((1400, 1400))
                nome = uuid4().hex + ".webp"
                foto.save(destino / nome, "WEBP", quality=85)
                return nome
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise ValueError("Não foi possível ler a foto. Escolha uma imagem JPG, PNG ou WebP de até 20 megapixels.")


def extensao_audio(conteudo):
    """Conferimos a assinatura do arquivo; não confiamos apenas na extensão."""
    if conteudo.startswith(b"RIFF") and conteudo[8:12] == b"WAVE":
        return ".wav"
    if conteudo.startswith(b"OggS"):
        return ".ogg"
    if conteudo.startswith(b"\x1a\x45\xdf\xa3"):
        return ".webm"
    if len(conteudo) > 12 and conteudo[4:8] == b"ftyp":
        return ".m4a"
    if conteudo.startswith(b"ID3") or (len(conteudo) > 2 and conteudo[0] == 255 and conteudo[1] & 224 == 224):
        return ".mp3"
    raise ValueError("Escolha um áudio MP3, M4A, WAV, OGG ou WebM válido.")


def salvar_audio(arquivo, destino):
    if not arquivo or not arquivo.filename:
        return None
    conteudo = arquivo.read(10 * 1024 * 1024 + 1)
    if not conteudo or len(conteudo) > 10 * 1024 * 1024:
        raise ValueError("O áudio precisa ter conteúdo e no máximo 10 MB.")
    extensao = extensao_audio(conteudo)
    nome = uuid4().hex + extensao
    (destino / nome).write_bytes(conteudo)
    return nome


def create_app(configuracao=None):
    app = Flask(__name__)
    pasta_dados = Path(os.environ.get("BATALHA_DADOS", PASTA / "instance"))
    app.config.update(
        DATA_DIR=pasta_dados,
        MAX_CONTENT_LENGTH=36 * 1024 * 1024,
        TEMPLATES_AUTO_RELOAD=True,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
    )
    if configuracao:
        app.config.update(configuracao)
    pasta_dados = Path(app.config["DATA_DIR"])
    pasta_dados.mkdir(parents=True, exist_ok=True)
    pasta_uploads = pasta_dados / "uploads"
    pasta_uploads.mkdir(exist_ok=True)
    caminho_banco = pasta_dados / "batalha.db"
    # A chave fica apenas na instalação local; não é distribuída no ZIP.
    chave = pasta_dados / ".secret_key"
    if not chave.exists():
        try:
            with chave.open("x") as arquivo:
                arquivo.write(secrets.token_hex(32))
        except FileExistsError:
            pass
    app.secret_key = os.environ.get("BATALHA_SECRET_KEY") or chave.read_text().strip()
    preparar_banco(caminho_banco)
    app.extensions["voz_natural"] = VozNatural(pasta_cache=pasta_dados / "voz-cache")
    # Nos testes, a IA só existe se for simulada: nenhuma chave real é usada.
    app.extensions["agente_ia"] = AgenteIA(categorias=CATEGORIAS) if app.config.get("TESTING") else AgenteIA.do_ambiente(categorias=CATEGORIAS)

    @app.context_processor
    def contexto_comum():
        if "csrf" not in session:
            session["csrf"] = secrets.token_hex(32)
        return {"categorias": CATEGORIAS, "categorias_por_id": {c["id"]: c for c in CATEGORIAS}, "csrf": session["csrf"],
                "ia_ativa": app.extensions["agente_ia"].ativo}

    @app.before_request
    def conferir_formulario():
        if request.method == "POST":
            recebido = request.form.get("csrf", "")
            esperado = session.get("csrf", "")
            if not esperado or not hmac.compare_digest(recebido, esperado):
                abort(400, description="Sua sessão mudou. Atualize a página e tente outra vez.")

    @app.after_request
    def cabecalhos(resposta):
        resposta.headers["X-Content-Type-Options"] = "nosniff"
        resposta.headers["Referrer-Policy"] = "same-origin"
        resposta.headers["Permissions-Policy"] = "microphone=(self), camera=(self), geolocation=()"
        resposta.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self'; "
            "img-src 'self' data: blob:; media-src 'self' blob:; "
            "connect-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'self'; form-action 'self'"
        )
        if not request.path.startswith("/static/"):
            resposta.headers["Cache-Control"] = "no-store"
        if request.path.startswith("/moderacao"):
            resposta.headers["X-Robots-Tag"] = "noindex, nofollow"
        return resposta

    @app.get("/")
    def inicio():
        return render_template("inicio.html", ativo="inicio", fala="Bem-vindo ao Batalha Conecta. O interruptor no alto da tela alterna os modos. A bolinha à esquerda, perto do livro, mostra textos. À direita, perto da pessoa falando, mostra imagens e voz. A pessoa falando abre seu cadastro. As pessoas com uma lupa procuram serviços. Você também pode tocar na foto de uma atividade. Os alto-falantes explicam cada opção. As imagens de atividades são exemplos, não fotos dos profissionais cadastrados.")

    @app.post("/api/voz")
    def sintetizar_voz():
        texto = request.form.get("texto", "").strip()
        if not texto or len(texto) > 2500:
            return jsonify({"erros": ["A fala precisa ter entre 1 e 2500 caracteres."]}), 400
        narrador = request.form.get("narrador", "francisca")
        if narrador not in VOZES:
            return jsonify({"erros": ["Escolha uma das vozes disponíveis."]}), 400
        try:
            voz = app.extensions["voz_natural"]
            # "fixa" marca perguntas e orientações do aplicativo: podem ficar guardadas em disco.
            conteudo = voz.sintetizar(texto, narrador, guardar=True) if request.form.get("fixa") == "1" else voz.sintetizar(texto, narrador)
        except VozIndisponivel as erro:
            return jsonify({"erros": [str(erro)]}), 503
        return send_file(io.BytesIO(conteudo), mimetype="audio/mpeg", download_name="orientacao.mp3", max_age=0)

    @app.post("/api/ia/transcrever")
    def ia_transcrever():
        """OUVIR: recebe a gravação de uma resposta e devolve o texto. O áudio não é guardado."""
        agente = app.extensions["agente_ia"]
        if not agente.ativo:
            return jsonify({"erros": ["O assistente de IA não está configurado."], "motivo": "sem-chave"}), 503
        campo = request.form.get("campo", "")
        fase = request.form.get("fase", "")
        arquivo = request.files.get("audio")
        conteudo = arquivo.read(4 * 1024 * 1024 + 1) if arquivo else b""
        if campo not in CAMPOS or fase not in FASES or not 200 <= len(conteudo) <= 4 * 1024 * 1024:
            return jsonify({"erros": ["Envie uma resposta gravada de até 4 MB."]}), 400
        try:
            extensao = extensao_audio(conteudo)
            texto = agente.transcrever(conteudo, "resposta" + extensao, campo, fase)
        except ValueError as erro:
            return jsonify({"erros": [str(erro)]}), 400
        except IAIndisponivel as erro:
            return jsonify({"erros": [str(erro)], "motivo": erro.motivo}), 503
        return jsonify({"texto": texto})

    @app.post("/api/ia/entender")
    def ia_entender():
        """ENTENDER: recebe o texto de uma fala e devolve a intenção e o valor conferidos."""
        agente = app.extensions["agente_ia"]
        if not agente.ativo:
            return jsonify({"erros": ["O assistente de IA não está configurado."], "motivo": "sem-chave"}), 503
        texto = " ".join(request.form.get("texto", "").split())
        campo = request.form.get("campo", "")
        fase = request.form.get("fase", "")
        pendente = request.form.get("pendente", "")[:700]
        if campo not in CAMPOS or fase not in FASES or not 1 <= len(texto) <= 1000:
            return jsonify({"erros": ["A fala precisa ter entre 1 e 1000 caracteres."]}), 400
        try:
            return jsonify(agente.entender(texto, fase, campo, pendente))
        except IAIndisponivel as erro:
            return jsonify({"erros": [str(erro)], "motivo": erro.motivo}), 503

    @app.get("/profissionais")
    def profissionais():
        busca = request.args.get("busca", "").strip()[:120]
        categoria = request.args.get("categoria", "")
        if categoria and categoria not in {c["id"] for c in CATEGORIAS}:
            abort(404)
        lista = buscar_profissionais(caminho_banco, busca, categoria)
        return render_template("profissionais.html", profissionais=lista, busca=busca, categoria=categoria,
                               ativo="buscar", fala=f"Encontramos {len(lista)} perfis. As figuras filtram por atividade. Os quatro quadradinhos mostram todas. Use o alto-falante de cada perfil para ouvir o nome e o trabalho. A seta abre o perfil. No modo com textos, você também pode escrever o que procura.")

    @app.get("/profissional/<int:identificador>")
    def perfil(identificador):
        pessoa = buscar_por_id(caminho_banco, identificador)
        if pessoa is None:
            abort(404)
        publicado = session.pop("ultimo_cadastro", None) == identificador
        tokens = session.get("avaliacoes_tokens", {})
        tokens[str(identificador)] = secrets.token_hex(24)
        session["avaliacoes_tokens"] = dict(list(tokens.items())[-20:])
        pagina = max(1, min(request.args.get("pagina", 1, type=int), 100000))
        avaliacoes = buscar_avaliacoes(caminho_banco, identificador, pagina)
        aviso_imagem = ""
        if not pessoa["foto"]:
            # Uma categoria desconhecida (de uma versão antiga) não derruba a página.
            categoria_imagem = next((item for item in CATEGORIAS if item["id"] == pessoa["categoria"]), CATEGORIAS[-1])
            aviso_imagem = "A imagem é um exemplo gerado por inteligência artificial, não é uma foto deste profissional. " if categoria_imagem.get("imagem_ia") else "A imagem representa a atividade, não é uma foto deste profissional. "
        if pessoa["demonstracao"]:
            aviso_imagem += "Este perfil é fictício, para demonstração. "
        return render_template("perfil.html", pessoa=pessoa, publicado=publicado, ativo="buscar",
                               fotos=buscar_fotos(caminho_banco, identificador), avaliacoes=avaliacoes, pagina=pagina,
                               pode_editar=identificador in session.get("meus_perfis", []),
                               avaliacao_envio=tokens[str(identificador)],
                               fala=f"Perfil de {pessoa['nome']}. {aviso_imagem}Região: {pessoa['comunidade']}. {pessoa['descricao']} Você pode ouvir a apresentação e usar os botões de contato. A câmera mostra as fotos do trabalho. Mais abaixo, ouça as avaliações ou toque no microfone para contar como foi o serviço.")

    @app.post("/profissional/<int:identificador>/fotos")
    def editar_fotos(identificador):
        if buscar_por_id(caminho_banco, identificador) is None:
            abort(404)
        if identificador not in session.get("meus_perfis", []):
            abort(403, description="Só o navegador que criou este perfil pode alterar suas fotos nesta versão.")
        arquivos = [foto for foto in request.files.getlist("fotos") if foto.filename]
        novas = []
        try:
            if len(arquivos) > 5:
                raise ValueError("Escolha no máximo cinco fotos.")
            for arquivo in arquivos:
                novas.append(salvar_foto(arquivo, pasta_uploads))
            apagadas = atualizar_fotos(caminho_banco, identificador, novas, set(request.form.getlist("remover")))
        except Exception as erro:
            for nome in novas:
                (pasta_uploads / nome).unlink(missing_ok=True)
            if isinstance(erro, ValueError):
                return jsonify({"erros": [str(erro)]}), 400
            raise
        for nome in apagadas:
            (pasta_uploads / nome).unlink(missing_ok=True)
        return jsonify({"url": url_for("perfil", identificador=identificador) + "#galeria"})

    @app.post("/profissional/<int:identificador>/avaliacoes")
    def avaliar(identificador):
        if buscar_por_id(caminho_banco, identificador) is None:
            abort(404)
        envio_id = request.form.get("envio_id", "")
        esperado = session.get("avaliacoes_tokens", {}).get(str(identificador), "")
        if not esperado or not hmac.compare_digest(envio_id, esperado):
            abort(400, description="Atualize o perfil antes de enviar sua avaliação.")
        destino = url_for("perfil", identificador=identificador) + "#avaliacoes"
        if buscar_avaliacao_envio(caminho_banco, envio_id, identificador):
            return jsonify({"url": destino})
        nome = request.form.get("nome", "").strip() or "Visitante"
        nota = request.form.get("nota", "")
        erros = []
        if len(nome) > 80:
            erros.append("Use até 80 letras no nome, ou deixe vazio.")
        if nota not in {"1", "2", "3", "4", "5"}:
            erros.append("Escolha de uma a cinco estrelas para avaliar o serviço.")
        if request.form.get("consentimento") != "sim":
            erros.append("Confirme que deseja publicar sua voz neste perfil.")
        audio = None
        if not erros:
            try:
                audio = salvar_audio(request.files.get("audio"), pasta_uploads)
                if not audio:
                    raise ValueError("Grave ou escolha um áudio para contar sua experiência.")
                cadastrar_avaliacao(caminho_banco, identificador, nome, int(nota), audio, envio_id)
            except ValueError as erro:
                erros.append(str(erro))
            except sqlite3.IntegrityError:
                if audio:
                    (pasta_uploads / audio).unlink(missing_ok=True)
                if not buscar_avaliacao_envio(caminho_banco, envio_id, identificador):
                    raise
            except Exception:
                if audio:
                    (pasta_uploads / audio).unlink(missing_ok=True)
                raise
        if erros:
            if audio:
                (pasta_uploads / audio).unlink(missing_ok=True)
            return jsonify({"erros": erros}), 400
        return jsonify({"url": destino}), 201

    @app.route("/cadastro", methods=["GET", "POST"])
    def cadastro():
        campos = {chave: request.form.get(chave, "").strip() for chave in ("nome", "categoria", "descricao", "comunidade", "telefone")}
        erros = []
        if request.method == "GET":
            session["envio_id"] = secrets.token_hex(24)
            campos["categoria"] = request.args.get("categoria", "")
        else:
            envio_id = request.form.get("envio_id", "")
            if not envio_id or not hmac.compare_digest(envio_id, session.get("envio_id", "")):
                abort(400, description="Abra o cadastro novamente para continuar.")
            anterior = buscar_envio(caminho_banco, envio_id)
            if anterior:
                session["meus_perfis"] = list(dict.fromkeys(session.get("meus_perfis", []) + [anterior]))[-20:]
                return jsonify({"url": url_for("perfil", identificador=anterior)}) if request.accept_mimetypes.best == "application/json" else redirect(url_for("perfil", identificador=anterior))
            if not 2 <= len(campos["nome"]) <= 80:
                erros.append("Informe seu nome ou o nome do trabalho, com 2 a 80 letras.")
            if campos["categoria"] not in {c["id"] for c in CATEGORIAS}:
                erros.append("Escolha uma atividade.")
            if not 2 <= len(campos["comunidade"]) <= 80:
                erros.append("Informe seu bairro ou comunidade, com 2 a 80 letras.")
            if len(campos["descricao"]) > 700:
                erros.append("Use no máximo 700 caracteres na descrição.")
            telefone = re.sub(r"\D", "", campos["telefone"])
            if len(telefone) in {12, 13} and telefone.startswith("55"):
                telefone = telefone[2:]
            if campos["telefone"] and (len(telefone) not in {10, 11} or telefone.startswith("0")):
                erros.append("Informe DDD e telefone com 10 ou 11 números, ou deixe vazio.")
            campos["telefone"] = telefone
            if request.form.get("consentimento") != "sim":
                erros.append("Confirme que deseja mostrar essas informações no projeto.")
            enviados = []
            fotos = [foto for foto in request.files.getlist("fotos") + request.files.getlist("foto") if foto.filename]
            if len(fotos) > 5:
                erros.append("Escolha no máximo cinco fotos.")
            if not erros:
                try:
                    campos["fotos"] = []
                    for arquivo in fotos:
                        nome = salvar_foto(arquivo, pasta_uploads)
                        campos["fotos"].append(nome)
                        enviados.append(nome)
                    campos["foto"] = campos["fotos"][0] if campos["fotos"] else None
                    campos["audio"] = salvar_audio(request.files.get("audio"), pasta_uploads)
                    if campos["audio"]:
                        enviados.append(campos["audio"])
                    if not campos["descricao"] and not campos["audio"]:
                        raise ValueError("Conte o que você faz por texto ou por áudio.")
                    campos["envio_id"] = envio_id
                    identificador = cadastrar_profissional(caminho_banco, campos)
                except ValueError as erro:
                    erros.append(str(erro))
                except sqlite3.IntegrityError:
                    # Se dois cliques chegarem juntos, mantemos apenas um registro.
                    identificador = buscar_envio(caminho_banco, envio_id)
                    for nome in enviados:
                        (pasta_uploads / nome).unlink(missing_ok=True)
                    if identificador is None:
                        raise
                except Exception:
                    for nome in enviados:
                        (pasta_uploads / nome).unlink(missing_ok=True)
                    raise
                if erros:
                    for nome in enviados:
                        (pasta_uploads / nome).unlink(missing_ok=True)
                else:
                    session["ultimo_cadastro"] = identificador
                    session["meus_perfis"] = (session.get("meus_perfis", []) + [identificador])[-20:]
                    destino = url_for("perfil", identificador=identificador)
                    if request.accept_mimetypes.best == "application/json":
                        return jsonify({"url": destino}), 201
                    return redirect(destino, code=303)
        if erros and request.accept_mimetypes.best == "application/json":
            return jsonify({"erros": erros}), 400
        return render_template("cadastro.html", campos=campos, erros=erros,
                               envio_id=session["envio_id"], ativo="cadastro",
                               fala="Você pode cadastrar seu trabalho sem e-mail. No modo imagens e voz, toque no microfone grande para começar. " + ("Um assistente de inteligência artificial ouve suas respostas: sua voz é enviada pela internet a um serviço externo e não fica guardada aqui. " if app.extensions["agente_ia"].ativo else "O navegador pode enviar sua fala ao serviço de reconhecimento pela internet. ") + "Ouça cada pergunta, fale depois do sinal e confirme a resposta. O WhatsApp é opcional. No final, ouça o resumo antes de autorizar a publicação. O interruptor com a bolinha à esquerda, do lado do livro, permite preencher com textos."), 400 if erros else 200

    @app.get("/api/profissionais")
    def api_profissionais():
        """A mesma informação também fica disponível para um futuro app separado."""
        lista = buscar_profissionais(caminho_banco, request.args.get("busca", "")[:120], request.args.get("categoria", ""))
        for pessoa in lista:
            pessoa.pop("envio_id", None)
            pessoa["perfil_url"] = url_for("perfil", identificador=pessoa["id"])
        return jsonify(lista)

    @app.get("/ajuda")
    def ajuda():
        return render_template("ajuda.html", ativo="ajuda", fala="Você pode procurar um serviço e abrir um perfil. Para divulgar seu trabalho, escolha Mostrar meu trabalho e siga as etapas. O botão Ouvir esta tela explica a página. Esta versão foi criada para testes da turma.")

    @app.get("/uploads/<nome>")
    def upload(nome):
        if not re.fullmatch(r"[a-f0-9]{32}\.(webp|mp3|m4a|wav|ogg|webm)", nome):
            abort(404)
        return send_from_directory(pasta_uploads, nome, conditional=True)

    @app.get("/manifest.webmanifest")
    def manifest():
        return send_from_directory(app.static_folder, "manifest.webmanifest", mimetype="application/manifest+json")

    @app.get("/sw.js")
    def service_worker():
        return send_from_directory(app.static_folder, "sw.js", mimetype="text/javascript")

    # ----- Moderação: página do professor, protegida por senha -----
    # A senha vem da variável BATALHA_MODERACAO_SENHA (no Render ou no arquivo .env), nunca do código.
    # Sem a variável, a página nem existe (404).
    senha_moderacao = str(app.config.get("MODERACAO_SENHA") or os.environ.get("BATALHA_MODERACAO_SENHA", "")).strip()
    # Contra quem tenta adivinhar a senha: após 10 erros em 10 minutos, a entrada fica fechada por 5 minutos.
    tentativas = {"falhas": [], "fechado_ate": 0.0}
    trava_tentativas = threading.Lock()
    DURACAO_MODERACAO = 2 * 60 * 60

    def moderador_ativo():
        return bool(senha_moderacao) and session.get("moderador_ate", 0) > time.time()

    def exigir_moderador():
        if not senha_moderacao:
            abort(404)
        if not moderador_ativo():
            abort(403, description="Entre com a senha da moderação para continuar.")

    def remover_arquivos(nomes):
        for nome in nomes:
            if nome and "/" not in nome and "\\" not in nome:
                (pasta_uploads / nome).unlink(missing_ok=True)

    @app.template_filter("data_local")
    def data_local(texto):
        """O banco guarda a hora universal (UTC). Batalha-PI fica em UTC-3 o ano todo."""
        from datetime import datetime, timedelta
        try:
            momento = datetime.strptime(str(texto), "%Y-%m-%d %H:%M:%S") - timedelta(hours=3)
        except ValueError:
            return texto
        return momento.strftime("%d/%m/%Y às %H:%M")

    @app.get("/moderacao")
    def moderacao():
        if not senha_moderacao:
            abort(404)
        aviso = session.pop("moderacao_aviso", "")
        if not moderador_ativo():
            return render_template("moderacao.html", entrou=False, aviso=aviso, senha_curta=len(senha_moderacao) < 8,
                                   fala="Página de moderação, para o professor. Digite a senha para entrar.")
        return render_template("moderacao.html", entrou=True, aviso=aviso, perfis=listar_para_moderacao(caminho_banco),
                               avaliacoes=listar_avaliacoes_recentes(caminho_banco),
                               fala="Página de moderação. Para apagar, marque Confirmo e toque em Apagar. O que for apagado não volta.")

    @app.post("/moderacao/entrar")
    def moderacao_entrar():
        if not senha_moderacao:
            abort(404)
        agora = time.time()
        with trava_tentativas:
            if tentativas["fechado_ate"] > agora:
                session["moderacao_aviso"] = "Muitas tentativas erradas. Espere alguns minutos e tente de novo."
                return redirect(url_for("moderacao"))
            senha = request.form.get("senha", "")
            if len(senha_moderacao) >= 8 and hmac.compare_digest(senha.encode("utf-8"), senha_moderacao.encode("utf-8")):
                tentativas["falhas"].clear()
                session["moderador_ate"] = agora + DURACAO_MODERACAO
                session["csrf"] = secrets.token_hex(32)  # novo código de formulário depois de entrar
                return redirect(url_for("moderacao"))
            tentativas["falhas"] = [momento for momento in tentativas["falhas"] if momento > agora - 600] + [agora]
            if len(tentativas["falhas"]) >= 10:
                tentativas["fechado_ate"] = agora + 300
                tentativas["falhas"].clear()
        session["moderacao_aviso"] = "Senha incorreta."
        return redirect(url_for("moderacao"))

    @app.post("/moderacao/sair")
    def moderacao_sair():
        session.pop("moderador_ate", None)
        return redirect(url_for("moderacao") if senha_moderacao else url_for("inicio"))

    @app.post("/moderacao/perfil/<int:identificador>/apagar")
    def moderacao_apagar_perfil(identificador):
        exigir_moderador()
        if request.form.get("confirmar") != "sim":
            session["moderacao_aviso"] = "Marque a caixa de confirmação antes de apagar."
            return redirect(url_for("moderacao"))
        pessoa = buscar_por_id(caminho_banco, identificador)
        arquivos = apagar_profissional(caminho_banco, identificador)
        if arquivos is None:
            session["moderacao_aviso"] = "Esse perfil já tinha sido apagado."
        else:
            remover_arquivos(arquivos)
            session["moderacao_aviso"] = f"Perfil \"{pessoa['nome']}\" apagado, com suas fotos e avaliações."
        return redirect(url_for("moderacao"))

    @app.post("/moderacao/avaliacao/<int:identificador>/apagar")
    def moderacao_apagar_avaliacao(identificador):
        exigir_moderador()
        if request.form.get("confirmar") != "sim":
            session["moderacao_aviso"] = "Marque a caixa de confirmação antes de apagar."
            return redirect(url_for("moderacao") + "#avaliacoes")
        arquivo = apagar_avaliacao(caminho_banco, identificador)
        if arquivo is None:
            session["moderacao_aviso"] = "Essa avaliação já tinha sido apagada."
        else:
            remover_arquivos([arquivo])
            session["moderacao_aviso"] = "Avaliação apagada."
        return redirect(url_for("moderacao") + "#avaliacoes")

    @app.errorhandler(400)
    @app.errorhandler(403)
    @app.errorhandler(404)
    @app.errorhandler(413)
    def erro_pagina(erro):
        mensagem = {404: "Não encontramos esta página ou perfil.", 413: "Os arquivos ultrapassam o limite. Use até cinco fotos de 5 MB e um áudio de 10 MB."}.get(erro.code, erro.description)
        if request.accept_mimetypes.best == "application/json":
            return jsonify({"erros": [mensagem]}), erro.code
        return render_template("erro.html", mensagem=mensagem, fala=mensagem), erro.code

    return app


app = create_app()

if __name__ == "__main__":
    # O depurador fica restrito ao próprio computador. Para a rede, veja servir.py.
    app.run(host="127.0.0.1", port=5000, debug=True)
