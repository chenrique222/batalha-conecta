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
    {"id": "costura", "nome": "Corte e costura", "exemplo": "Roupas sob medida, consertos, ajustes e bainhas", "imagem": "costura.png", "imagem_ia": False},
    {"id": "manutencao", "nome": "Serviços de manutenção", "exemplo": "Pedreiro, pintura, elétrica e encanamento", "imagem": "manutencao-ia.png", "imagem_ia": True},
    {"id": "servicos", "nome": "Outros serviços", "exemplo": "Atividades que não se encaixam nas outras categorias", "imagem": "outros-servicos-ia.png", "imagem_ia": True},
]

# Perfis fictícios para demonstração (nome, categoria, descrição, comunidade, telefone fictício).
# Os telefones seguem o padrão (86) 90000-01xx e os botões de contato ficam desligados nos exemplos,
# para ninguém ligar por engano para um número que possa existir.
# A ordem só pode crescer no final: o envio_id de cada exemplo depende da posição.
EXEMPLOS = [
    ("Artes da Rosa", "artesanato", "Faço cestas e peças de artesanato por encomenda. Conte sua ideia e combinamos os detalhes.", "Centro", "86900000101"),
    ("Farinha do Seu João", "alimentacao", "Produzo farinha de mandioca. Entre em contato para combinar quantidade e retirada.", "Comunidade rural", "86900000102"),
    ("Seu Antônio · Pedreiro", "manutencao", "Faço reformas e pequenos reparos. Podemos conversar sobre o serviço antes de combinar o valor.", "Batalha", "86900000103"),
    ("Bolos da Maria", "alimentacao", "Faço bolos caseiros por encomenda. Consulte sabores e disponibilidade para a sua data.", "Centro", "86900000104"),
    ("Doces e Bolos da Tia Lúcia", "alimentacao", "Bolos de aniversário confeitados, bolos de pote e docinhos para festas. Encomendas com três dias de antecedência.", "Bairro Novo", "86900000105"),
    ("Salgados do Seu Raimundo", "alimentacao", "Coxinha, pastel, empada e quibe por encomenda para festas e eventos. Vendo o cento frito ou congelado.", "Centro", "86900000106"),
    ("Cestaria da Dona Francisca", "artesanato", "Cestas, bolsas e chapéus de palha de carnaúba feitos à mão. Faço sob encomenda e vendo na feira de sábado.", "Zona rural", "86900000107"),
    ("Biscuit da Ana Clara", "artesanato", "Lembrancinhas, topos de bolo e enfeites em biscuit para aniversários, batizados e casamentos.", "Vila Nova", "86900000108"),
    ("Ateliê da Cleide · Costura sob medida", "costura", "Vestidos de festa, fardamentos escolares e roupas sob medida. Tiro as medidas na sua casa ou no ateliê.", "Centro", "86900000109"),
    ("Dona Graça Consertos de Roupa", "costura", "Bainhas, ajustes, troca de zíper e reforma de roupas. Serviço rápido, entrego em até dois dias.", "Bairro Novo", "86900000110"),
    ("Zé da Elétrica · Reparos", "manutencao", "Instalação elétrica, troca de tomadas, chuveiros e disjuntores. Atendo em casa e faço orçamento sem compromisso.", "Vila Nova", "86900000111"),
    ("Reformas do Chico Pintor", "manutencao", "Pintura de casas, massa corrida, textura e pequenos reparos em paredes e telhados.", "Batalha", "86900000112"),
    ("Barbearia do Léo", "servicos", "Corte masculino, barba e pigmentação. Atendo com hora marcada, de segunda a sábado.", "Centro", "86900000113"),
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
                    (nome, categoria, descricao, comunidade, telefone, demonstracao, envio_id)
                    VALUES (?, ?, ?, ?, ?, 1, ?)
                """, (*exemplo, f"exemplo-{numero}"))
                # Exemplos criados em versões antigas, sem telefone, recebem o número fictício.
                conexao.execute("UPDATE profissionais SET telefone = ? WHERE envio_id = ? AND demonstracao = 1 AND (telefone IS NULL OR telefone = '')",
                                (exemplo[4], f"exemplo-{numero}"))
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


# ----- Moderação (página do professor) -----

def listar_para_moderacao(caminho):
    """Todos os perfis, do mais novo ao mais antigo, com a contagem de fotos e avaliações."""
    conexao = conectar(caminho)
    try:
        registros = conexao.execute("""
            SELECT p.id, p.nome, p.categoria, p.comunidade, p.telefone, p.descricao, p.demonstracao, p.criado_em,
                   (SELECT COUNT(*) FROM fotos WHERE profissional_id = p.id) AS fotos,
                   (SELECT COUNT(*) FROM avaliacoes WHERE profissional_id = p.id) AS avaliacoes
            FROM profissionais p ORDER BY p.id DESC
        """).fetchall()
        return [dict(registro) for registro in registros]
    finally:
        conexao.close()


def listar_avaliacoes_recentes(caminho, limite=100):
    conexao = conectar(caminho)
    try:
        registros = conexao.execute("""
            SELECT a.id, a.nome, a.nota, a.audio, a.criado_em, a.profissional_id, p.nome AS perfil
            FROM avaliacoes a JOIN profissionais p ON p.id = a.profissional_id
            ORDER BY a.id DESC LIMIT ?
        """, (limite,)).fetchall()
        return [dict(registro) for registro in registros]
    finally:
        conexao.close()


def apagar_profissional(caminho, identificador):
    """Apaga o perfil, suas fotos e avaliações. Devolve os nomes dos arquivos a remover, ou None."""
    conexao = conectar(caminho)
    try:
        with conexao:
            pessoa = conexao.execute("SELECT foto, audio FROM profissionais WHERE id = ?", (identificador,)).fetchone()
            if pessoa is None:
                return None
            arquivos = {pessoa["foto"], pessoa["audio"]}
            arquivos |= {linha[0] for linha in conexao.execute("SELECT arquivo FROM fotos WHERE profissional_id = ?", (identificador,))}
            arquivos |= {linha[0] for linha in conexao.execute("SELECT audio FROM avaliacoes WHERE profissional_id = ?", (identificador,))}
            # ON DELETE CASCADE remove as linhas de fotos e avaliações.
            conexao.execute("DELETE FROM profissionais WHERE id = ?", (identificador,))
        return sorted(arquivo for arquivo in arquivos if arquivo)
    finally:
        conexao.close()


def apagar_avaliacao(caminho, identificador):
    """Apaga uma avaliação. Devolve o nome do arquivo de áudio, ou None se ela não existir."""
    conexao = conectar(caminho)
    try:
        with conexao:
            avaliacao = conexao.execute("SELECT audio FROM avaliacoes WHERE id = ?", (identificador,)).fetchone()
            if avaliacao is None:
                return None
            conexao.execute("DELETE FROM avaliacoes WHERE id = ?", (identificador,))
        return avaliacao["audio"]
    finally:
        conexao.close()
