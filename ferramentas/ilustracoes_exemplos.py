"""Gera as ilustrações dos perfis de exemplo do Batalha Conecta (SVG -> WebP).

Estilo comum: parede em tom claro, bancada de madeira e objetos com sombra suave,
nas cores da paleta do site. Cada perfil mostra o seu produto ou serviço.
"""
import subprocess
import sys
from pathlib import Path

from PIL import Image

L, A = 1200, 800
SAIDA = Path(sys.argv[1] if len(sys.argv) > 1 else "saida")
SAIDA.mkdir(parents=True, exist_ok=True)

MARINHO, AZUL, VERDE, VERDE_VIVO = "#0b2149", "#1b3f78", "#0f7a55", "#2fbf71"
AMBAR, AMBAR_ESC, TERRA, TERRA_ESC = "#f0b23e", "#b9821a", "#b4452c", "#8f3420"
CREME, MADEIRA, MADEIRA_ESC = "#fff8e8", "#c48a52", "#9a6436"


def cena(fundo1, fundo2, corpo, mesa=True, mesa1=MADEIRA, mesa2=MADEIRA_ESC, horizonte=560):
    bancada = f'''
  <rect y="{horizonte}" width="{L}" height="{A - horizonte}" fill="url(#mesa)"/>
  <rect y="{horizonte}" width="{L}" height="12" fill="#ffffff" opacity=".18"/>
  <path d="M0 {horizonte + 90} C300 {horizonte + 80} 600 {horizonte + 105} 1200 {horizonte + 88}" stroke="#000" stroke-opacity=".08" stroke-width="3" fill="none"/>''' if mesa else ""
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {L} {A}" width="{L}" height="{A}">
  <defs>
    <linearGradient id="parede" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{fundo1}"/><stop offset="1" stop-color="{fundo2}"/></linearGradient>
    <linearGradient id="mesa" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{mesa1}"/><stop offset="1" stop-color="{mesa2}"/></linearGradient>
    <linearGradient id="metal" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#8d98a8"/><stop offset=".5" stop-color="#eef1f5"/><stop offset="1" stop-color="#8d98a8"/></linearGradient>
    <filter id="sombra" x="-30%" y="-30%" width="160%" height="170%"><feDropShadow dx="0" dy="12" stdDeviation="12" flood-color="#3a2a1a" flood-opacity=".25"/></filter>
  </defs>
  <rect width="{L}" height="{A}" fill="url(#parede)"/>
  <ellipse cx="960" cy="140" rx="380" ry="230" fill="#ffffff" opacity=".35"/>{bancada}
  <g filter="url(#sombra)">{corpo}</g>
</svg>'''


def rosa():  # cerâmica de barro e bordado
    vasos = f'''
    <path d="M190 560 C130 520 140 380 210 350 L210 320 L290 320 L290 350 C360 380 370 520 310 560 Z" fill="#c4643f"/>
    <path d="M160 450 C220 470 280 470 340 450" stroke="#f6d3a8" stroke-width="10" fill="none"/>
    <path d="M170 480 C230 500 270 500 330 480" stroke="#8f3420" stroke-width="6" fill="none" stroke-dasharray="14 10"/>
    <rect x="200" y="306" width="100" height="22" rx="8" fill="#a8502e"/>
    <path d="M380 560 C350 540 345 470 390 450 L390 430 L450 430 L450 450 C495 470 490 540 460 560 Z" fill="#d98a5a"/>
    <path d="M370 505 H470" stroke="#fff4dc" stroke-width="8"/>'''
    bastidor = f'''
    <circle cx="790" cy="370" r="175" fill="#fff8ea"/>
    <circle cx="790" cy="370" r="175" fill="none" stroke="#d9a46d" stroke-width="22"/>
    <rect x="770" y="176" width="40" height="30" rx="8" fill="#b4823f"/>
    <g transform="translate(790 370)">
      <path d="M0 10 C-10 60 10 100 0 140" stroke="{VERDE}" stroke-width="8" fill="none"/>
      <path d="M0 70 C30 50 60 60 70 80 C40 95 15 88 0 70 Z" fill="{VERDE_VIVO}"/>
      <path d="M0 95 C-30 75 -60 85 -70 105 C-40 118 -15 112 0 95 Z" fill="{VERDE_VIVO}"/>
      {''.join(f'<ellipse cx="0" cy="-38" rx="26" ry="44" fill="{TERRA}" transform="rotate({ang})"/>' for ang in range(0, 360, 60))}
      <circle r="24" fill="{AMBAR}"/>
      <circle cx="-110" cy="-60" r="16" fill="#1b3f78"/><circle cx="110" cy="-50" r="14" fill="{AMBAR}"/><circle cx="95" cy="70" r="12" fill="#1b3f78"/>
    </g>
    <path d="M940 560 C1000 520 1060 520 1100 560" stroke="{TERRA}" stroke-width="10" fill="none"/>
    <path d="M1020 520 L1120 480" stroke="#8d98a8" stroke-width="5"/>'''
    return cena("#fcefe0", "#f3dcc4", vasos + bastidor)


def joao():  # farinha de mandioca
    saco = f'''
    <path d="M150 560 C120 470 140 330 190 300 L420 300 C470 330 490 470 460 560 Z" fill="#d9bf8c"/>
    <path d="M150 560 C120 470 140 330 190 300 L420 300 C470 330 490 470 460 560 Z" fill="none" stroke="#a88a52" stroke-width="6"/>
    <path d="M180 330 C260 310 350 310 430 330" stroke="#a88a52" stroke-width="6" fill="none"/>
    <path d="M200 300 C230 230 380 230 410 300 Z" fill="#f6ead0"/>
    {''.join(f'<circle cx="{x}" cy="{y}" r="4" fill="#e6d3a8"/>' for x, y in [(240, 280), (300, 262), (350, 275), (280, 285), (330, 290), (380, 288)])}
    <rect x="245" y="390" width="120" height="70" rx="10" fill="#f6ead0" opacity=".85"/>
    <path d="M270 425 h70" stroke="#a88a52" stroke-width="8" stroke-linecap="round"/>'''
    gamela = f'''
    <ellipse cx="770" cy="540" rx="210" ry="40" fill="#8a5a30"/>
    <path d="M560 520 C580 600 960 600 980 520 Z" fill="#a86a3a"/>
    <ellipse cx="770" cy="520" rx="210" ry="44" fill="#b77a45"/>
    <ellipse cx="770" cy="512" rx="180" ry="32" fill="#f3e4c0"/>
    <path d="M640 505 C700 470 840 470 900 505" fill="#fbf1d8"/>'''
    mandioca = f'''
    <g transform="translate(800 640) rotate(-8)"><path d="M0 0 C40 -30 170 -20 210 10 C170 40 40 40 0 0 Z" fill="#7a4b26"/><path d="M15 0 C60 -14 150 -10 195 8" stroke="#5c3518" stroke-width="5" fill="none"/></g>
    <g transform="translate(860 700) rotate(6)"><path d="M0 0 C40 -26 150 -18 180 8 C150 34 40 32 0 0 Z" fill="#8a5a2e"/><ellipse cx="4" cy="0" rx="10" ry="16" fill="#f6ead0"/></g>'''
    return cena("#fbf3dc", "#efdcb2", saco + gamela + mandioca)


def antonio():  # pedreiro
    tijolos = []
    for linha in range(6):
        y = 160 + linha * 62
        deslocamento = 0 if linha % 2 == 0 else -70
        for coluna in range(6):
            x = 520 + deslocamento + coluna * 140
            if x > 1210 or x + 130 < 500 or (linha < 2 and coluna > 3):
                continue
            tijolos.append(f'<rect x="{x}" y="{y}" width="130" height="54" rx="6" fill="{"#c4643f" if (linha + coluna) % 3 else "#b4553a"}"/>')
    parede = f'<rect x="500" y="150" width="720" height="410" fill="#e8dccb"/>' + "".join(tijolos)
    ferramentas = f'''
    <g transform="translate(130 610) rotate(-6)">
      <path d="M0 40 L170 0 L210 60 Z" fill="url(#metal)" stroke="#6f7a8a" stroke-width="3"/>
      <rect x="200" y="22" width="26" height="40" rx="6" fill="#6f7a8a"/>
      <rect x="220" y="28" width="110" height="28" rx="14" fill="{AMBAR}"/>
    </g>
    <rect x="120" y="500" width="330" height="44" rx="10" fill="{AMBAR}"/>
    <rect x="120" y="500" width="330" height="44" rx="10" fill="none" stroke="{AMBAR_ESC}" stroke-width="5"/>
    <rect x="255" y="508" width="60" height="28" rx="14" fill="#e8f6ee" stroke="{VERDE}" stroke-width="4"/>
    <circle cx="285" cy="522" r="7" fill="{VERDE_VIVO}"/>
    <path d="M330 640 L360 760 L540 760 L570 640 Z" fill="#6f7a8a"/>
    <ellipse cx="450" cy="640" rx="120" ry="26" fill="#9aa4b2"/>
    <ellipse cx="450" cy="640" rx="100" ry="18" fill="#c9c2b5"/>'''
    return cena("#eef2f6", "#dde4ec", parede + ferramentas, horizonte=560)


def maria():  # bolo caseiro
    bolo = f'''
    <ellipse cx="520" cy="540" rx="250" ry="34" fill="#dfe5ec"/>
    <rect x="505" y="540" width="30" height="20" fill="#dfe5ec"/>
    <path d="M330 520 C330 380 710 380 710 520 C710 545 330 545 330 520 Z" fill="#d98a3a"/>
    <path d="M330 470 C330 420 710 420 710 470" fill="none"/>
    <path d="M345 450 C400 400 640 400 695 450 C660 470 380 470 345 450 Z" fill="#e9a650"/>
    <ellipse cx="520" cy="430" rx="70" ry="18" fill="#8a4a1e" opacity=".75"/>
    <path d="M330 500 C420 520 620 520 710 500" stroke="#b86d28" stroke-width="6" fill="none"/>
    {''.join(f'<circle cx="{x}" cy="{y}" r="5" fill="#fff4dc" opacity=".9"/>' for x, y in [(400, 470), (460, 480), (580, 478), (640, 468), (520, 488)])}'''
    fatia = f'''
    <ellipse cx="900" cy="560" rx="130" ry="26" fill="#f6f8fb"/>
    <path d="M820 545 L960 490 L990 545 Z" fill="#e9a650"/>
    <path d="M820 545 L990 545 L990 560 L820 560 Z" fill="#d98a3a"/>
    <path d="M840 538 L955 495" stroke="#f6d39a" stroke-width="6"/>'''
    cafe = f'''
    <path d="M150 470 L250 470 L240 560 L160 560 Z" fill="#ffffff"/>
    <path d="M250 490 C290 490 290 535 245 535" stroke="#ffffff" stroke-width="12" fill="none"/>
    <ellipse cx="200" cy="472" rx="50" ry="10" fill="#6b3a1c"/>
    <path d="M185 440 C175 420 200 410 190 390 M215 440 C205 420 230 410 220 390" stroke="#ffffff" stroke-width="6" opacity=".6" fill="none"/>'''
    return cena("#fdf0de", "#f5dfc0", bolo + fatia + cafe)


def lucia():  # bolo de aniversário e docinhos
    bolo = f'''
    <rect x="390" y="420" width="380" height="140" rx="22" fill="#fbe4dc"/>
    <rect x="450" y="300" width="260" height="130" rx="20" fill="#ffffff"/>
    <path d="M390 450 C430 480 470 440 510 470 C550 500 590 440 630 470 C670 500 710 440 770 460 L770 440 L390 440 Z" fill="#f4a9b8"/>
    <path d="M450 330 C490 355 530 320 570 345 C610 370 650 320 710 340 L710 320 L450 320 Z" fill="#f4a9b8"/>
    {''.join(f'<circle cx="{x}" cy="{y}" r="9" fill="{c}"/>' for x, y, c in [(420, 520, AMBAR), (480, 530, VERDE_VIVO), (540, 520, "#1b3f78"), (600, 530, AMBAR), (660, 520, VERDE_VIVO), (720, 530, "#1b3f78"), (480, 400, AMBAR), (580, 405, VERDE_VIVO), (680, 400, "#1b3f78")])}
    {''.join(f'<rect x="{x}" y="230" width="16" height="70" rx="4" fill="{c}"/><path d="M{x + 8} 225 C{x - 4} 205 {x + 20} 195 {x + 8} 180 C{x + 26} 200 {x + 22} 215 {x + 8} 225 Z" fill="{AMBAR}"/>' for x, c in [(500, "#7ec8e3"), (572, "#f4a9b8"), (644, VERDE_VIVO)])}
    <rect x="370" y="556" width="420" height="16" rx="8" fill="#dfe5ec"/>'''
    docinhos = "".join(f'''
    <path d="M{x - 42} {y} L{x + 42} {y} L{x + 32} {y + 40} L{x - 32} {y + 40} Z" fill="{forma}"/>
    <circle cx="{x}" cy="{y - 8}" r="34" fill="#5a2d14"/>
    {''.join(f'<circle cx="{x + dx}" cy="{y - 8 + dy}" r="4" fill="{c}"/>' for dx, dy, c in [(-14, -16, "#f4a9b8"), (10, -20, AMBAR), (16, 4, VERDE_VIVO), (-8, 6, "#7ec8e3"), (0, -4, "#fff")])}'''
                       for x, y, forma in [(930, 520, "#f4a9b8"), (1030, 520, AMBAR), (980, 440, "#7ec8e3")])
    return cena("#fdeef2", "#f6d9e2", bolo + docinhos)


def raimundo():  # salgados
    bandeja = f'''
    <ellipse cx="600" cy="560" rx="440" ry="60" fill="#c4cad5"/>
    <ellipse cx="600" cy="548" rx="420" ry="54" fill="#eef1f5"/>'''
    coxinhas = "".join(f'''
    <path d="M{x} {y - 110} C{x - 20} {y - 70} {x - 70} {y - 40} {x - 64} {y} C{x - 56} {y + 30} {x + 56} {y + 30} {x + 64} {y} C{x + 70} {y - 40} {x + 20} {y - 70} {x} {y - 110} Z" fill="#d9822b"/>
    <path d="M{x - 40} {y - 10} C{x - 20} {y + 6} {x + 20} {y + 6} {x + 40} {y - 10}" stroke="#b5641c" stroke-width="5" fill="none"/>
    {''.join(f'<circle cx="{x + dx}" cy="{y + dy}" r="3" fill="#f6c76a"/>' for dx, dy in [(-20, -40), (10, -60), (25, -20), (-35, -5), (5, -15)])}'''
                       for x, y in [(330, 530), (450, 515), (390, 470)])
    pasteis = "".join(f'''
    <g transform="translate({x} {y}) rotate({r})">
      <path d="M-90 0 C-90 -80 90 -80 90 0 Z" fill="#e9b04a"/>
      <path d="M-90 0 H90" stroke="#c98f1e" stroke-width="10" stroke-dasharray="8 8"/>
      <circle cx="-30" cy="-30" r="6" fill="#f6d39a"/><circle cx="20" cy="-40" r="5" fill="#f6d39a"/>
    </g>''' for x, y, r in [(640, 540, -6), (700, 480, 8)])
    empadas = "".join(f'''
    <path d="M{x - 46} {y} L{x + 46} {y} L{x + 36} {y - 46} L{x - 36} {y - 46} Z" fill="#d9a050"/>
    <ellipse cx="{x}" cy="{y - 48}" rx="40" ry="16" fill="#efc275"/>
    <path d="M{x - 30} {y - 52} C{x - 10} {y - 40} {x + 10} {y - 60} {x + 30} {y - 46}" stroke="#c98f1e" stroke-width="4" fill="none"/>'''
                      for x, y in [(860, 545), (950, 545), (905, 495)])
    molho = f'''
    <ellipse cx="1060" cy="470" rx="58" ry="20" fill="#ffffff"/>
    <path d="M1002 470 C1006 510 1114 510 1118 470 Z" fill="#ffffff"/>
    <ellipse cx="1060" cy="470" rx="48" ry="14" fill="{TERRA}"/>'''
    return cena("#fff4e0", "#f3dfb8", bandeja + coxinhas + pasteis + empadas + molho)


def francisca():  # cestaria de palha
    def cesta(x, y, largura, altura, cor="#d9b26b"):
        tramas = "".join(f'<path d="M{x - largura / 2 + 6} {y - altura + i} H{x + largura / 2 - 6}" stroke="#b48a44" stroke-width="5"/>' for i in range(18, int(altura), 22))
        verticais = "".join(f'<path d="M{x - largura / 2 + i} {y - altura + 10} V{y - 6}" stroke="#c49a52" stroke-width="4" opacity=".6"/>' for i in range(20, int(largura) - 10, 26))
        return f'''<path d="M{x - largura / 2} {y - altura} L{x + largura / 2} {y - altura} L{x + largura / 2 - 18} {y} L{x - largura / 2 + 18} {y} Z" fill="{cor}"/>{tramas}{verticais}
        <rect x="{x - largura / 2 - 6}" y="{y - altura - 12}" width="{largura + 12}" height="18" rx="9" fill="#b48a44"/>'''
    chapeu = f'''
    <ellipse cx="830" cy="300" rx="250" ry="70" fill="#e2c07a"/>
    <path d="M700 300 C700 170 960 170 960 300 Z" fill="#d9b26b"/>
    <path d="M705 270 C760 250 900 250 955 270 L957 300 L703 300 Z" fill="{TERRA}"/>
    {''.join(f'<path d="M{620 + i * 30} 270 C{640 + i * 30} 300 {640 + i * 30} 320 {620 + i * 30} 350" stroke="#c49a52" stroke-width="3" opacity=".7" fill="none"/>' for i in range(14))}'''
    bolsa = f'''
    <path d="M940 560 L1130 560 L1110 420 L960 420 Z" fill="#d9b26b"/>
    <path d="M985 420 C985 330 1085 330 1085 420" stroke="#b48a44" stroke-width="14" fill="none"/>
    {''.join(f'<path d="M955 {440 + i * 22} H1120" stroke="#b48a44" stroke-width="5"/>' for i in range(5))}
    <circle cx="1035" cy="470" r="20" fill="{VERDE_VIVO}"/>'''
    return cena("#f6f2e2", "#e9dfc0", chapeu + cesta(260, 560, 260, 200) + cesta(520, 560, 220, 150, "#e2c07a") + bolsa)


def ana():  # biscuit
    def boneca(x, y, roupa, cabelo):
        return f'''
    <path d="M{x - 55} {y} C{x - 55} {y - 90} {x + 55} {y - 90} {x + 55} {y} Z" fill="{roupa}"/>
    <circle cx="{x}" cy="{y - 120}" r="50" fill="#f6d2b8"/>
    <path d="M{x - 52} {y - 125} C{x - 50} {y - 190} {x + 50} {y - 190} {x + 52} {y - 125} C{x + 30} {y - 150} {x - 30} {y - 150} {x - 52} {y - 125} Z" fill="{cabelo}"/>
    <circle cx="{x - 18}" cy="{y - 118}" r="6" fill="#3a2a1a"/><circle cx="{x + 18}" cy="{y - 118}" r="6" fill="#3a2a1a"/>
    <circle cx="{x - 30}" cy="{y - 100}" r="9" fill="#f4a9b8" opacity=".7"/><circle cx="{x + 30}" cy="{y - 100}" r="9" fill="#f4a9b8" opacity=".7"/>
    <path d="M{x - 12} {y - 96} C{x - 4} {y - 88} {x + 4} {y - 88} {x + 12} {y - 96}" stroke="#a8402a" stroke-width="4" fill="none"/>'''
    base = f'''
    <ellipse cx="560" cy="555" rx="300" ry="34" fill="#ffffff"/>
    <rect x="260" y="520" width="600" height="36" fill="#ffffff"/>
    <ellipse cx="560" cy="520" rx="300" ry="34" fill="#f6f8fb"/>'''
    flores = "".join(f'''<g transform="translate({x} {y})">{''.join(f'<circle cx="0" cy="-20" r="16" fill="{c}" transform="rotate({a})"/>' for a in range(0, 360, 72))}<circle r="12" fill="{AMBAR}"/></g>''' for x, y, c in [(330, 500, "#f4a9b8"), (790, 500, "#7ec8e3"), (950, 470, VERDE_VIVO), (1060, 510, "#f4a9b8")])
    cogumelo = f'''
    <rect x="1000" y="380" width="44" height="80" rx="16" fill="#fff4dc"/>
    <path d="M950 390 C950 300 1094 300 1094 390 Z" fill="{TERRA}"/>
    <circle cx="990" cy="350" r="12" fill="#fff"/><circle cx="1040" cy="330" r="10" fill="#fff"/><circle cx="1060" cy="370" r="8" fill="#fff"/>'''
    return cena("#eef4fb", "#dbe7f5", base + boneca(480, 520, "#7ec8e3", "#5a2d14") + boneca(650, 520, "#f4a9b8", AMBAR) + flores + cogumelo, mesa1="#e8d3b8", mesa2="#d2b48f")


def cleide():  # ateliê: manequim com vestido
    manequim = f'''
    <rect x="490" y="560" width="20" height="120" fill="#6b4a2a"/>
    <path d="M420 690 L580 690" stroke="#6b4a2a" stroke-width="16" stroke-linecap="round"/>
    <path d="M440 180 C440 150 560 150 560 180 L575 260 C600 300 600 330 580 350 L420 350 C400 330 400 300 425 260 Z" fill="#efe3cf"/>
    <rect x="485" y="140" width="30" height="40" rx="10" fill="#d9c4a2"/>
    <path d="M425 260 C460 280 540 280 575 260 L585 350 C640 430 680 520 700 570 L300 570 C320 520 360 430 415 350 Z" fill="{VERDE}"/>
    <path d="M415 350 C470 370 530 370 585 350" stroke="{AMBAR}" stroke-width="12" fill="none"/>
    {''.join(f'<path d="M{400 + i * 50} 400 C{390 + i * 50} 470 {380 + i * 50} 520 {360 + i * 54} 570" stroke="#0b6646" stroke-width="4" fill="none" opacity=".6"/>' for i in range(5))}
    {''.join(f'<circle cx="{x}" cy="{y}" r="7" fill="#ffffff" opacity=".85"/>' for x, y in [(450, 430), (520, 460), (580, 420), (420, 510), (560, 520), (640, 540), (360, 545)])}'''
    fita = f'''
    <path d="M430 300 C470 320 530 320 570 300" stroke="{AMBAR}" stroke-width="16" fill="none"/>
    <path d="M570 300 C640 330 660 420 640 480" stroke="{AMBAR}" stroke-width="16" fill="none"/>
    <path d="M570 300 C640 330 660 420 640 480" stroke="{AMBAR_ESC}" stroke-width="8" stroke-dasharray="2 12" fill="none"/>'''
    tecidos = f'''
    <path d="M790 120 H1120" stroke="#8d98a8" stroke-width="10" stroke-linecap="round"/>
    <path d="M820 120 C800 260 860 380 830 470 L900 470 C930 380 880 260 890 120 Z" fill="{TERRA}"/>
    <path d="M910 120 C900 240 950 360 930 440 L1000 440 C1010 360 970 240 980 120 Z" fill="#7ec8e3"/>
    <path d="M1000 120 C990 260 1040 370 1020 500 L1090 500 C1110 370 1070 260 1070 120 Z" fill="{AMBAR}"/>
    {''.join(f'<circle cx="{1035 + dx}" cy="{180 + dy}" r="6" fill="#fff4dc"/>' for dx, dy in [(0, 0), (10, 60), (-6, 120), (12, 180), (0, 240)])}'''
    return cena("#f3f0fa", "#e3dcf0", manequim + fita + tecidos, mesa1="#d9c4a2", mesa2="#bfa47c")


def graca():  # consertos de roupa
    calca = f'''
    <path d="M330 170 L560 170 L590 560 L475 560 L450 300 L425 560 L300 560 Z" fill="#3c6aa8"/>
    <path d="M330 170 L560 170 L562 205 L328 205 Z" fill="#2f5a92"/>
    <path d="M445 205 L452 290" stroke="#c9d6ea" stroke-width="5" stroke-dasharray="6 6"/>
    <path d="M300 520 L425 520 M475 520 L590 520" stroke="{AMBAR}" stroke-width="5" stroke-dasharray="10 8"/>
    <path d="M360 230 C380 250 400 250 420 232" stroke="#c9d6ea" stroke-width="4" fill="none"/>
    <path d="M440 120 C440 90 460 80 470 100" stroke="#8d98a8" stroke-width="8" fill="none"/>
    <path d="M300 172 L445 110 L590 172" stroke="#8d98a8" stroke-width="10" fill="none" stroke-linejoin="round"/>'''
    alfinetes = "".join(f'<path d="M{x} 515 L{x + 10} 548" stroke="#b4bcc6" stroke-width="4"/><circle cx="{x}" cy="513" r="7" fill="{c}"/>' for x, c in [(330, TERRA), (370, AMBAR), (510, VERDE_VIVO), (550, TERRA)])
    ferro = f'''
    <path d="M760 520 C760 440 840 400 960 400 L1040 400 C1060 400 1070 420 1070 440 L1070 520 Z" fill="#f6f8fb"/>
    <path d="M760 520 L1070 520 L1070 545 L740 545 C740 530 748 522 760 520 Z" fill="url(#metal)"/>
    <path d="M880 400 C880 340 1030 340 1030 400" stroke="{AZUL}" stroke-width="22" fill="none" stroke-linecap="round"/>
    <circle cx="960" cy="460" r="20" fill="{AMBAR}"/>'''
    linha = f'''
    <rect x="650" y="470" width="70" height="16" rx="6" fill="#e2b07a"/>
    <rect x="658" y="484" width="54" height="60" fill="{TERRA}"/>
    <rect x="650" y="542" width="70" height="16" rx="6" fill="#e2b07a"/>
    <path d="M685 470 C700 420 740 430 760 470" stroke="{TERRA}" stroke-width="3" fill="none"/>'''
    return cena("#eef5f1", "#d9eadf", calca + alfinetes + ferro + linha)


def ze():  # eletricista
    lampada = f'''
    <circle cx="420" cy="290" r="150" fill="#fff6c9" opacity=".7"/>
    <circle cx="420" cy="290" r="105" fill="#fde58a"/>
    <path d="M380 380 L460 380 L452 440 L388 440 Z" fill="#fde58a"/>
    <path d="M385 440 H455 M388 462 H452 M392 484 H448" stroke="#8d98a8" stroke-width="16" stroke-linecap="round"/>
    <path d="M390 300 C400 260 440 260 450 300 L440 380 M400 380 L390 300" stroke="{AMBAR_ESC}" stroke-width="6" fill="none"/>
    {''.join(f'<path d="M{420 + 170 * dx} {290 + 170 * dy} L{420 + 215 * dx} {290 + 215 * dy}" stroke="{AMBAR}" stroke-width="12" stroke-linecap="round"/>' for dx, dy in [(-1, 0), (1, 0), (0, -1), (-.7, -.7), (.7, -.7)])}'''
    tomada = f'''
    <rect x="770" y="160" width="190" height="190" rx="30" fill="#ffffff"/>
    <circle cx="865" cy="255" r="62" fill="#eef1f5"/>
    <circle cx="840" cy="250" r="11" fill="#3a2a1a"/><circle cx="890" cy="250" r="11" fill="#3a2a1a"/><circle cx="865" cy="285" r="8" fill="#3a2a1a"/>'''
    ferramentas = f'''
    <g transform="translate(700 510) rotate(-12)"><rect width="150" height="34" rx="17" fill="{AMBAR}"/><rect x="150" y="12" width="140" height="10" fill="url(#metal)"/></g>
    <g transform="translate(900 470) rotate(20)">
      <path d="M0 0 L120 30 L120 46 L0 20 Z" fill="#6f7a8a"/><path d="M0 60 L120 30 L120 46 L0 80 Z" fill="#6f7a8a"/>
      <path d="M-120 -20 L0 0 L0 20 L-120 10 Z" fill="{TERRA}"/><path d="M-120 90 L0 60 L0 80 L-120 70 Z" fill="{TERRA}"/>
    </g>
    <ellipse cx="200" cy="540" rx="90" ry="34" fill="#c4643f"/>
    <path d="M110 540 C110 470 290 470 290 540" fill="#c4643f"/>
    <path d="M120 520 C160 500 240 500 280 520 M115 500 C160 480 240 480 285 500" stroke="#8f3420" stroke-width="5" fill="none"/>
    <path d="M285 520 C340 520 330 600 390 600" stroke="#c4643f" stroke-width="10" fill="none"/>'''
    return cena("#eaf0f8", "#d3dfee", lampada + tomada + ferramentas)


def chico():  # pintor
    parede = f'''
    <rect x="0" y="0" width="{L}" height="560" fill="#e9e2d3"/>
    <path d="M0 0 H700 C690 120 720 260 690 380 C680 450 700 520 690 560 H0 Z" fill="#7cc4a0"/>
    {''.join(f'<path d="M{690 + dx} {y} C{700 + dx} {y + 30} {690 + dx} {y + 60} {700 + dx} {y + 80}" stroke="#7cc4a0" stroke-width="10" fill="none"/>' for dx, y in [(0, 300), (8, 120)])}'''
    rolo = f'''
    <g transform="translate(760 210) rotate(-8)">
      <rect x="0" y="0" width="180" height="70" rx="30" fill="#7cc4a0"/>
      <rect x="0" y="0" width="180" height="70" rx="30" fill="none" stroke="#5aa883" stroke-width="5"/>
      <path d="M180 35 H230 V160" stroke="#8d98a8" stroke-width="12" fill="none" stroke-linejoin="round"/>
      <rect x="214" y="150" width="32" height="140" rx="14" fill="{AMBAR}"/>
    </g>'''
    lata = f'''
    <path d="M250 430 L470 430 L455 560 L265 560 Z" fill="#c9d0db"/>
    <ellipse cx="360" cy="430" rx="110" ry="26" fill="#eef1f5"/>
    <ellipse cx="360" cy="432" rx="96" ry="20" fill="#7cc4a0"/>
    <path d="M300 445 C300 480 290 500 300 520" stroke="#7cc4a0" stroke-width="16" stroke-linecap="round" fill="none"/>
    <rect x="270" y="470" width="180" height="50" rx="8" fill="{VERDE}"/>
    <path d="M250 430 C250 360 470 360 470 430" stroke="#8d98a8" stroke-width="6" fill="none"/>'''
    pincel = f'''
    <g transform="translate(940 520) rotate(-30)">
      <rect x="0" y="0" width="170" height="30" rx="15" fill="{TERRA}"/>
      <rect x="-40" y="-5" width="45" height="40" rx="4" fill="url(#metal)"/>
      <path d="M-40 -5 L-95 -10 L-95 40 L-40 35 Z" fill="#7cc4a0"/>
    </g>
    <ellipse cx="620" cy="600" rx="60" ry="14" fill="#7cc4a0" opacity=".7"/>'''
    return cena("#e9e2d3", "#e9e2d3", parede + rolo + lata + pincel)


def leo():  # barbearia
    espelho = f'''
    <circle cx="560" cy="280" r="190" fill="#c9a26b"/>
    <circle cx="560" cy="280" r="170" fill="#dceaf5"/>
    <path d="M440 200 L520 140 M450 260 L590 150" stroke="#ffffff" stroke-width="14" stroke-linecap="round" opacity=".7"/>'''
    poste = f'''
    <rect x="150" y="100" width="110" height="20" rx="10" fill="#8d98a8"/>
    <rect x="160" y="120" width="90" height="380" rx="14" fill="#ffffff"/>
    <clipPath id="listras"><rect x="160" y="120" width="90" height="380" rx="14"/></clipPath>
    <g clip-path="url(#listras)">{''.join(f'<path d="M130 {y} L280 {y - 90} L280 {y - 50} L130 {y + 40} Z" fill="{c}"/>' for y, c in [(170, TERRA), (250, AZUL), (330, TERRA), (410, AZUL), (490, TERRA), (570, AZUL)])}</g>
    <rect x="150" y="500" width="110" height="20" rx="10" fill="#8d98a8"/>
    <circle cx="205" cy="90" r="20" fill="#8d98a8"/>'''
    maquina = f'''
    <g transform="translate(800 470) rotate(-14)">
      <rect x="0" y="0" width="220" height="72" rx="30" fill="#2b2f36"/>
      <rect x="-30" y="8" width="40" height="56" rx="6" fill="url(#metal)"/>
      {''.join(f'<path d="M-30 {14 + i * 9} H-46" stroke="#8d98a8" stroke-width="4"/>' for i in range(6))}
      <rect x="80" y="22" width="60" height="28" rx="14" fill="{AMBAR}"/>
    </g>'''
    pente = f'''
    <rect x="320" y="520" width="240" height="30" rx="8" fill="{AZUL}"/>
    {''.join(f'<rect x="{326 + i * 14}" y="548" width="7" height="34" rx="3" fill="{AZUL}"/>' for i in range(16))}'''
    tesoura = f'''
    <g transform="translate(640 560) rotate(-6)">
      <path d="M0 0 L190 -16 L190 -4 Z" fill="url(#metal)"/><path d="M0 6 L190 24 L188 34 Z" fill="url(#metal)"/>
      <circle cx="-34" cy="-14" r="24" fill="none" stroke="{TERRA}" stroke-width="10"/><circle cx="-30" cy="26" r="22" fill="none" stroke="{TERRA}" stroke-width="10"/>
    </g>'''
    return cena("#eef1f4", "#d9dfe6", poste + espelho + maquina + pente + tesoura, mesa1="#3b3f46", mesa2="#2b2f36")


ILUSTRACOES = {"rosa": rosa, "joao": joao, "antonio": antonio, "maria": maria, "lucia": lucia,
               "raimundo": raimundo, "francisca": francisca, "ana": ana, "cleide": cleide,
               "graca": graca, "ze": ze, "chico": chico, "leo": leo}

if __name__ == "__main__":
    for nome, funcao in ILUSTRACOES.items():
        svg = SAIDA / f"{nome}.svg"
        svg.write_text(funcao(), encoding="utf-8")
        png = SAIDA / f"{nome}.png"
        subprocess.run(["rsvg-convert", "-w", str(L), "-h", str(A), str(svg), "-o", str(png)], check=True)
        imagem = Image.open(png).convert("RGB")
        # Aproxima cerca de 15%: os objetos ficam maiores no cartão.
        imagem = imagem.crop((78, 90, 1122, 786)).resize((L, A), Image.LANCZOS)
        imagem.save(SAIDA / f"{nome}.webp", "WEBP", quality=86)
        png.unlink()
    print("ok", len(ILUSTRACOES))
