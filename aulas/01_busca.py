"""Aula 1 — listas, repetição e condição. Execute este arquivo sozinho."""

servicos = [
    "Artes da Rosa - artesanato",
    "Farinha do Seu João - farinha de mandioca",
    "Seu Antônio - pedreiro",
    "Bolos da Maria - bolos",
]

busca = input("Qual serviço você procura? ").lower()
encontrou = False

for servico in servicos:
    if busca in servico.lower():
        print(servico)
        encontrou = True

if encontrou == False:
    print("Nenhum serviço encontrado.")

# Desafio: adicione uma costureira e procure pela palavra "costura".
