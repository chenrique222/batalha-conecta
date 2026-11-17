"""Aula 4 — primeira página. Execute e abra http://127.0.0.1:5001."""
from flask import Flask, render_template_string

app = Flask(__name__)


@app.get("/")
def inicio():
    profissionais = ["Artes da Rosa", "Bolos da Maria", "Seu Antônio"]
    return render_template_string("""
        <!doctype html>
        <html lang="pt-BR">
        <meta charset="utf-8">
        <title>Batalha Conecta — primeira página</title>
        <h1>Batalha Conecta</h1>
        <p>Conheça quem trabalha na nossa cidade:</p>
        <ul>
          {% for nome in profissionais %}
            <li>{{ nome }}</li>
          {% endfor %}
        </ul>
        </html>
    """, profissionais=profissionais)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001, debug=True)
