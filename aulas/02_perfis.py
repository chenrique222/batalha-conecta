"""Aula 2 — um dicionário reúne as informações de uma pessoa."""

profissionais = [
    {"nome": "Artes da Rosa", "atividade": "artesanato", "comunidade": "Centro"},
    {"nome": "Bolos da Maria", "atividade": "bolos", "comunidade": "Centro"},
    {"nome": "Seu Antônio", "atividade": "pedreiro", "comunidade": "Batalha"},
]

for pessoa in profissionais:
    print("Nome:", pessoa["nome"])
    print("Atividade:", pessoa["atividade"])
    print("Comunidade:", pessoa["comunidade"])
    print()

# Desafio: acrescente a chave "descricao" aos três perfis e mostre seu conteúdo.
