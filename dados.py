"""Dados do Batalha Conecta. Comece a leitura por CATEGORIAS e EXEMPLOS.

Uma lista guarda vários itens. Cada dicionário guarda os campos de um item.
As funções abaixo transformam esses itens em registros permanentes no SQLite.
"""
import sqlite3
import unicodedata
import re

CATEGORIAS = [
    {"id": "alimentacao", "nome": "Bolos e comidas", "exemplo": "Bolos, doces, refeições, farinha e goma", "imagem": "alimentacao-ia.png", "imagem_ia": True},
    {"id": "artesanato", "nome": "Artesanato", "exemplo": "Peças feitas à mão", "imagem": "artesanato-ia.png", "imagem_ia": True},
    {"id": "manutencao", "nome": "Serviços de manutenção", "exemplo": "Pedreiro, pintura, elétrica e encanamento", "imagem": "manutencao-ia.png", "imagem_ia": True},
    {"id": "servicos", "nome": "Outros serviços", "exemplo": "Atividades que não se encaixam nas outras categorias", "imagem": "outros-servicos-ia.png", "imagem_ia": True},
]

EXEMPLOS = [
    ("Artes da Rosa", "artesanato", "Faço cestas e peças de artesanato por encomenda. Conte sua ideia e combinamos os detalhes.", "Centro"),
    ("Farinha do Seu João", "alimentacao", "Produzo farinha de mandioca. Entre em contato para combinar quantidade e retirada.", "Comunidade rural"),
    ("Seu Antônio · Pedreiro", "manutencao", "Faço reformas e pequenos reparos. Podemos conversar sobre o serviço antes de combinar o valor.", "Batalha"),
    ("Bolos da Maria", "alimentacao", "Faço bolos caseiros por encomenda. Consulte sabores e disponibilidade para a sua data.", "Centro"),
]


def normalizar(texto):
    """Assim, 'JOÃO', 'joão' e 'joao' podem ser encontrados na mesma busca."""
    texto = unicodedata.normalize("NFKD", texto or "")
    return "".join(letra for letra in texto if not unicodedata.combining(letra)).casefold()


def conectar(caminho):
    conexao = sqlite3.connect(caminho, timeout=10)
    conexao.row_factory = sqlite3.Row
    conexao.execute("PRAGMA foreign_keys = ON")
    conexao.create_function("normalizar", 1, normalizar)
    return conexao


def preparar_banco(caminho):
    conexao = conectar(caminho)
    try:
        with conexao:
            conexao.execute("""
                CREATE TABLE IF NOT EXISTS profissionais (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    categoria TEXT NOT NULL,
                    descricao TEXT NOT NULL DEFAULT '',
                    comunidade TEXT NOT NULL,
                    telefone TEXT NOT NULL DEFAULT '',
                    foto TEXT,
                    audio TEXT,
                    demonstracao INTEGER NOT NULL DEFAULT 0,
                    envio_id TEXT UNIQUE NOT NULL,
                    criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conexao.execute("""
                CREATE TABLE IF NOT EXISTS fotos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    profissional_id INTEGER NOT NULL REFERENCES profissionais(id) ON DELETE CASCADE,
                    arquivo TEXT NOT NULL,
                    posicao INTEGER NOT NULL CHECK (posicao BETWEEN 0 AND 4),
                    UNIQUE (profissional_id, posicao)
                )
            """)
            # Mantém a foto dos cadastros feitos nas versões anteriores.
            conexao.execute("""
                INSERT INTO fotos (profissional_id, arquivo, posicao)
                SELECT id, foto, 0 FROM profissionais
                WHERE foto IS NOT NULL AND NOT EXISTS
                    (SELECT 1 FROM fotos WHERE profissional_id = profissionais.id)
            """)
            conexao.execute("""
                CREATE TABLE IF NOT EXISTS avaliacoes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    profissional_id INTEGER NOT NULL REFERENCES profissionais(id) ON DELETE CASCADE,
                    nome TEXT NOT NULL DEFAULT 'Visitante',
                    nota INTEGER NOT NULL CHECK (nota BETWEEN 1 AND 5),
                    audio TEXT NOT NULL,
                    envio_id TEXT UNIQUE NOT NULL,
                    criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conexao.execute("CREATE INDEX IF NOT EXISTS avaliacoes_perfil ON avaliacoes(profissional_id, id)")
            # INSERT OR IGNORE impede duplicar os exemplos ao reiniciar o app.
            for numero, exemplo in enumerate(EXEMPLOS, start=1):
                conexao.execute("""
                    INSERT OR IGNORE INTO profissionais
                    (nome, categoria, descricao, comunidade, demonstracao, envio_id)
                    VALUES (?, ?, ?, ?, 1, ?)
                """, (*exemplo, f"exemplo-{numero}"))
            # Uma atualização única mantém os mesmos IDs, contatos, fotos e avaliações.
            conexao.execute("CREATE TABLE IF NOT EXISTS migracoes (nome TEXT PRIMARY KEY)")
            if not conexao.execute("SELECT 1 FROM migracoes WHERE nome = 'categorias-v06'").fetchone():
                for perfil in conexao.execute("SELECT id, nome, categoria, envio_id, demonstracao FROM profissionais").fetchall():
                    nome = normalizar(perfil["nome"])
                    nova = perfil["categoria"]
                    if perfil["demonstracao"] and perfil["envio_id"] == "exemplo-3":
                        nova = "manutencao"
                    elif perfil["categoria"] in {"rural", "servicos"} and re.search(r"\b(pedreiro|pedreira|eletricista|encanador|encanadora|pintor|pintora)\b", nome):
                        nova = "manutencao"
                    elif perfil["categoria"] == "rural" and not re.search(r"\b(farinha|farinhada|mandioca|goma|tapioca)\b", nome):
                        # O antigo grupo era amplo. Não atribuímos produção de farinha sem indicação no nome.
                        nova = "servicos"
                    if nova != perfil["categoria"]:
                        conexao.execute("UPDATE profissionais SET categoria = ? WHERE id = ?", (nova, perfil["id"]))
                conexao.execute("INSERT INTO migracoes (nome) VALUES ('categorias-v06')")
            # Versão 0.7: "Farinha e derivados" deixou de existir. Farinha, goma e tapioca são comidas.
            if not conexao.execute("SELECT 1 FROM migracoes WHERE nome = 'categorias-v07'").fetchone():
                conexao.execute("UPDATE profissionais SET categoria = 'alimentacao' WHERE categoria = 'rural'")
                conexao.execute("INSERT INTO migracoes (nome) VALUES ('categorias-v07')")
    finally:
        conexao.close()


def buscar_profissionais(caminho, busca="", categoria=""):
    # Os valores entram por parâmetros (?), separados do comando SQL.
    termo = normalizar(busca.strip())
    conexao = conectar(caminho)
    try:
        registros = conexao.execute("""
            SELECT * FROM profissionais
            WHERE (? = '' OR categoria = ?)
              AND instr(normalizar(nome || ' ' || descricao || ' ' || comunidade), ?) > 0
            ORDER BY demonstracao ASC, id DESC
        """, (categoria, categoria, termo)).fetchall()
        return [dict(registro) for registro in registros]
    finally:
        conexao.close()


def buscar_por_id(caminho, identificador):
    conexao = conectar(caminho)
    try:
        registro = conexao.execute("SELECT * FROM profissionais WHERE id = ?", (identificador,)).fetchone()
        return dict(registro) if registro else None
    finally:
        conexao.close()


def buscar_envio(caminho, envio_id):
    conexao = conectar(caminho)
    try:
        registro = conexao.execute("SELECT id FROM profissionais WHERE envio_id = ?", (envio_id,)).fetchone()
        return registro["id"] if registro else None
    finally:
        conexao.close()


def cadastrar_profissional(caminho, campos):
    conexao = conectar(caminho)
    try:
        with conexao:
            cursor = conexao.execute("""
                INSERT INTO profissionais
                (nome, categoria, descricao, comunidade, telefone, foto, audio, envio_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, tuple(campos[chave] for chave in
                     ("nome", "categoria", "descricao", "comunidade", "telefone", "foto", "audio", "envio_id")))
            identificador = cursor.lastrowid
            fotos = campos.get("fotos", [campos["foto"]] if campos.get("foto") else [])
            if len(fotos) > 5:
                raise ValueError("Escolha no máximo cinco fotos.")
            conexao.executemany("INSERT INTO fotos (profissional_id, arquivo, posicao) VALUES (?, ?, ?)",
                                [(identificador, foto, posicao) for posicao, foto in enumerate(fotos)])
            return identificador
    finally:
        conexao.close()


def buscar_fotos(caminho, identificador):
    conexao = conectar(caminho)
    try:
        return [dict(item) for item in conexao.execute(
            "SELECT * FROM fotos WHERE profissional_id = ? ORDER BY posicao", (identificador,))]
    finally:
        conexao.close()


def atualizar_fotos(caminho, identificador, novas, remover):
    """Confere o limite dentro da transação, inclusive em envios simultâneos."""
    conexao = conectar(caminho)
    try:
        with conexao:
            conexao.execute("BEGIN IMMEDIATE")
            atuais = conexao.execute("SELECT * FROM fotos WHERE profissional_id = ? ORDER BY posicao", (identificador,)).fetchall()
            mantidas = [foto["arquivo"] for foto in atuais if str(foto["id"]) not in remover]
            apagadas = [foto["arquivo"] for foto in atuais if str(foto["id"]) in remover]
            todas = mantidas + novas
            if len(todas) > 5:
                raise ValueError("A galeria pode ter no máximo cinco fotos. Remova uma antes de adicionar outra.")
            conexao.execute("DELETE FROM fotos WHERE profissional_id = ?", (identificador,))
            conexao.executemany("INSERT INTO fotos (profissional_id, arquivo, posicao) VALUES (?, ?, ?)",
                                [(identificador, foto, posicao) for posicao, foto in enumerate(todas)])
            conexao.execute("UPDATE profissionais SET foto = ? WHERE id = ?", (todas[0] if todas else None, identificador))
            return apagadas
    finally:
        conexao.close()


def cadastrar_avaliacao(caminho, identificador, nome, nota, audio, envio_id):
    conexao = conectar(caminho)
    try:
        with conexao:
            cursor = conexao.execute("""
                INSERT INTO avaliacoes (profissional_id, nome, nota, audio, envio_id)
                VALUES (?, ?, ?, ?, ?)
            """, (identificador, nome, nota, audio, envio_id))
            return cursor.lastrowid
    finally:
        conexao.close()


def buscar_avaliacao_envio(caminho, envio_id, identificador):
    conexao = conectar(caminho)
    try:
        return conexao.execute("SELECT id FROM avaliacoes WHERE envio_id = ? AND profissional_id = ?",
                              (envio_id, identificador)).fetchone() is not None
    finally:
        conexao.close()


def buscar_avaliacoes(caminho, identificador, pagina=1):
    conexao = conectar(caminho)
    try:
        resumo = dict(conexao.execute("SELECT count(*) AS total, avg(nota) AS media FROM avaliacoes WHERE profissional_id = ?",
                                      (identificador,)).fetchone())
        registros = conexao.execute("""SELECT id, nome, nota, audio, criado_em FROM avaliacoes
            WHERE profissional_id = ? ORDER BY id DESC LIMIT 10 OFFSET ?""", (identificador, (pagina - 1) * 10))
        resumo["itens"] = [dict(item) for item in registros]
        return resumo
    finally:
        conexao.close()
