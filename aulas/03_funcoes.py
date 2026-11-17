"""Aula 3 — uma função reúne uma tarefa que podemos usar várias vezes."""

def procurar(profissionais, atividade):
    encontrados = []
    for pessoa in profissionais:
        if atividade.lower() in pessoa["atividade"].lower():
            encontrados.append(pessoa)
    return encontrados


profissionais = [
    {"nome": "Artes da Rosa", "atividade": "artesanato"},
    {"nome": "Bolos da Maria", "atividade": "bolos"},
    {"nome": "Seu Antônio", "atividade": "pedreiro"},
]

busca = input("Qual atividade? ")
resultado = procurar(profissionais, busca)

for pessoa in resultado:
    print(pessoa["nome"])

# Desafio: altere a função para também procurar pelo nome.
