# -*- coding: utf-8 -*-
"""Analisador do log do Castor: extrai metricas e gera graficos.

Le ~/logs_ia/ros_chat.log, monta um registro por turno e produz:

    analise/turnos.csv        um turno por linha
    analise/resumo.txt        numeros consolidados
    analise/gr1_latencia.png  latencia por arquitetura
    analise/gr2_rotas.png     distribuicao das rotas de resposta
    analise/gr3_contextos.png contextos acionados
    analise/gr4_vosk.png      desempenho do reconhecimento (opcional)
    analise/gr5_filtro.png    recusas do filtro por classe (opcional)

Os graficos saem SEM titulo interno: na ABNT a legenda fica acima da
figura, dentro do documento. Largura de 16 cm, area util do modelo do
Piic (A4 com margens de 3 e 2 cm). Tons de cinza com hachura, legiveis
em impressao preto e branco.

    python3 analisar_sessoes.py
"""

import os
import re
import csv
import glob
from collections import Counter, defaultdict

CASA = os.path.expanduser("~")
LOGS = os.path.join(CASA, "logs_ia")
AQUI = os.path.dirname(os.path.abspath(__file__))
SAIDA = os.path.join(AQUI, "..", "analise")

LARGURA_CM = 16.0
LIMIAR_LITERATURA = 2.5     # Miller, Meyer e Smart (2025)

# Latencia medida na arquitetura anterior, com o LLM respondendo ao vivo.
# Ajuste estes valores para os que voce mediu e registrou.
LLM_MIN = 30.0
LLM_MAX = 136.0

RE_FALA = re.compile(r"\[chat\] Usu.rio disse:\s*(.+?)\s*$")
RE_RESP = re.compile(r"\[chat\] Castor responde:\s*(.+?)\s*\((\d+\.?\d*)s\)")
RE_BANCO = re.compile(r"\[BANCO\]\s*(\w+)")
RE_DIRETA = re.compile(r"\[DIRETA\] contexto '(\w+)'")
RE_VALID = re.compile(r"\[VALIDADOR\] resposta rejeitada \(([^)]+)\)")

NOMES_ROTA = {
    "seguranca":  "Seguranca\n(psicologa)",
    "persona":    "Persona",
    "identidade": "Identidade\n(acolhe)",
    "sobre_castor": "Sobre o Castor\n(sequencia)",
    "banco":      "Banco de\ncontexto",
    "nome":       "Nome",
    "sentimento": "Sentimento",
    "piada":      "Piada",
    "template":   "Template\ngenerico",
    "llm":        "LLM em\ntempo real",
}


def pol(cm):
    """Centimetros para polegadas, que e a unidade do matplotlib."""
    return cm / 2.54


def ler_turnos():
    arquivos = sorted(glob.glob(os.path.join(LOGS, "ros_chat.log*")))
    if not arquivos:
        print("nenhum log encontrado em %s" % LOGS)
        return []

    turnos = []
    atual = None
    for caminho in arquivos:
        with open(caminho, errors="replace") as f:
            for linha in f:
                m = RE_FALA.search(linha)
                if m:
                    atual = {"fala": m.group(1), "banco": "", "direta": "",
                             "persona": False, "identidade": False,
                             "sobre": False, "validador": "",
                             "resposta": "", "tempo": 0.0, "rota": ""}
                    continue
                if atual is None:
                    continue
                if "[PERSONA]" in linha:
                    atual["persona"] = True
                if "[IDENTIDADE]" in linha:
                    atual["identidade"] = True
                if "[SOBRE]" in linha:
                    atual["sobre"] = True
                m = RE_BANCO.search(linha)
                if m:
                    atual["banco"] = m.group(1)
                m = RE_DIRETA.search(linha)
                if m:
                    atual["direta"] = m.group(1)
                m = RE_VALID.search(linha)
                if m:
                    atual["validador"] = m.group(1)
                m = RE_RESP.search(linha)
                if m:
                    atual["resposta"] = m.group(1)
                    atual["tempo"] = float(m.group(2))
                    atual["rota"] = classificar(atual)
                    turnos.append(atual)
                    atual = None
    return turnos


def classificar(t):
    """Qual camada respondeu. A ordem espelha resposta_deterministica()."""
    if "psic" in t["resposta"].lower():
        return "seguranca"
    if t["sobre"]:
        return "sobre_castor"
    if t["identidade"]:
        return "identidade"
    if t["persona"]:
        return "persona"
    if t["banco"]:
        return "banco"
    d = t["direta"]
    if d in ("nome", "sentimento", "piada"):
        return d
    if d:
        return "template"
    return "llm"


def gravar_csv(turnos):
    caminho = os.path.join(SAIDA, "turnos.csv")
    with open(caminho, "w") as f:
        w = csv.writer(f)
        w.writerow(["fala", "rota", "contexto_banco", "tempo_s",
                    "validador", "resposta"])
        for t in turnos:
            w.writerow([t["fala"], t["rota"], t["banco"],
                        "%.3f" % t["tempo"], t["validador"], t["resposta"]])
    return caminho


def resumo(turnos):
    tempos = sorted(t["tempo"] for t in turnos)
    n = len(turnos)
    rotas = Counter(t["rota"] for t in turnos)
    contextos = Counter(t["banco"] for t in turnos if t["banco"])
    rejeicoes = Counter(t["validador"] for t in turnos if t["validador"])
    dentro = sum(1 for x in tempos if x <= LIMIAR_LITERATURA)

    L = []
    L.append("turnos analisados: %d" % n)
    if n:
        L.append("tempo medio:   %.3f s" % (sum(tempos) / n))
        L.append("tempo mediano: %.3f s" % tempos[n // 2])
        L.append("tempo maximo:  %.3f s" % tempos[-1])
        L.append("dentro do limiar de %.1f s: %d de %d (%.1f%%)"
                 % (LIMIAR_LITERATURA, dentro, n, 100.0 * dentro / n))
    L.append("")
    L.append("rotas de resposta:")
    for r, c in rotas.most_common():
        L.append("   %-12s %4d  (%.1f%%)" % (r, c, 100.0 * c / max(n, 1)))
    determ = n - rotas.get("llm", 0)
    L.append("   determinismo: %d de %d (%.1f%%)"
             % (determ, n, 100.0 * determ / max(n, 1)))
    L.append("")
    L.append("contextos acionados: %d distintos" % len(contextos))
    for c, q in contextos.most_common():
        L.append("   %-14s %4d" % (c, q))
    L.append("")
    L.append("rejeicoes do validador: %d" % sum(rejeicoes.values()))
    for r, q in rejeicoes.most_common():
        L.append("   %-30s %d" % (r, q))

    texto = "\n".join(L)
    with open(os.path.join(SAIDA, "resumo.txt"), "w") as f:
        f.write(texto + "\n")
    return texto, rotas, contextos, tempos


def preparar_matplotlib():
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return None
    plt.rcParams.update({
        "font.family": "serif",
        "font.serif": ["Times New Roman", "Liberation Serif", "DejaVu Serif"],
        "font.size": 10,
        "axes.linewidth": 0.8,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
    })
    return plt


def limpar_eixo(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def grafico_latencia(plt, turnos):
    """Latencia da arquitetura anterior contra a atual, escala log."""
    medidos = [t["tempo"] for t in turnos]
    if not medidos:
        return
    atual = sum(medidos) / len(medidos)
    piso = 0.01           # escala log nao aceita zero
    llm_medio = (LLM_MIN + LLM_MAX) / 2.0

    fig, ax = plt.subplots(figsize=(pol(LARGURA_CM), pol(7.5)))
    rotulos = ["LLM em tempo real\n(arquitetura anterior)",
               "Rota deterministica\n(arquitetura atual)"]
    valores = [llm_medio, max(atual, piso)]
    erros = [[llm_medio - LLM_MIN], [LLM_MAX - llm_medio]]

    b1 = ax.bar([0], [valores[0]], yerr=[[erros[0][0]], [erros[1][0]]],
                color="0.55", edgecolor="black", linewidth=0.8,
                hatch="//", capsize=4, width=0.5)
    b2 = ax.bar([1], [valores[1]], color="0.85", edgecolor="black",
                linewidth=0.8, hatch="..", width=0.5)

    ax.set_yscale("log")
    ax.set_ylim(piso / 2, LLM_MAX * 3)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(rotulos, fontsize=9)
    ax.set_ylabel("Tempo de resposta (s), escala logaritmica")
    ax.axhline(LIMIAR_LITERATURA, color="black", linestyle="--", linewidth=1.0)
    ax.text(1.45, LIMIAR_LITERATURA * 1.2, "limiar de 2,5 s",
            fontsize=8, ha="right")
    ax.text(0, LLM_MAX * 1.3, "%.0f a %.0f s" % (LLM_MIN, LLM_MAX),
            ha="center", fontsize=9)
    ax.text(1, max(atual, piso) * 1.6, "%.1f s" % atual,
            ha="center", fontsize=9)
    limpar_eixo(ax)
    fig.savefig(os.path.join(SAIDA, "gr1_latencia.png"))
    plt.close(fig)


def grafico_rotas(plt, rotas, total):
    if not rotas:
        return
    itens = rotas.most_common()
    fig, ax = plt.subplots(figsize=(pol(LARGURA_CM), pol(8.0)))
    qtds = [q for _, q in itens]
    barras = ax.bar(range(len(itens)), qtds, color="0.78",
                    edgecolor="black", linewidth=0.8, hatch="//", width=0.6)
    for b, q in zip(barras, qtds):
        ax.text(b.get_x() + b.get_width() / 2, q + max(qtds) * 0.02,
                "%d\n(%.0f%%)" % (q, 100.0 * q / total),
                ha="center", va="bottom", fontsize=8)
    ax.set_xticks(range(len(itens)))
    ax.set_xticklabels([NOMES_ROTA.get(r, r) for r, _ in itens], fontsize=8)
    ax.set_ylabel("Numero de respostas")
    ax.set_ylim(0, max(qtds) * 1.25)
    limpar_eixo(ax)
    fig.savefig(os.path.join(SAIDA, "gr2_rotas.png"))
    plt.close(fig)


def grafico_contextos(plt, contextos):
    if not contextos:
        return
    itens = contextos.most_common()
    altura = max(5.0, 0.55 * len(itens) + 2.0)
    fig, ax = plt.subplots(figsize=(pol(LARGURA_CM), pol(altura)))
    qtds = [q for _, q in itens]
    ax.barh(range(len(itens)), qtds, color="0.78", edgecolor="black",
            linewidth=0.8, hatch="\\\\", height=0.6)
    for i, q in enumerate(qtds):
        ax.text(q + max(qtds) * 0.02, i, str(q), va="center", fontsize=8)
    ax.set_yticks(range(len(itens)))
    ax.set_yticklabels([c for c, _ in itens], fontsize=8)
    ax.invert_yaxis()
    ax.set_xlabel("Numero de acionamentos")
    ax.set_xlim(0, max(qtds) * 1.15)
    limpar_eixo(ax)
    fig.savefig(os.path.join(SAIDA, "gr3_contextos.png"))
    plt.close(fig)


def grafico_de_csv(plt, nome_csv, nome_png, rotulo_x):
    """Grafico de barras a partir de um CSV de duas colunas: rotulo,valor.

    Usado para dados que nao estao no log, como o desempenho do Vosk e as
    recusas do filtro. Se o CSV nao existir, o grafico e apenas pulado.
    """
    caminho = os.path.join(SAIDA, nome_csv)
    if not os.path.exists(caminho):
        print("   (%s ausente, grafico pulado)" % nome_csv)
        return
    rotulos, valores = [], []
    with open(caminho) as f:
        for linha in csv.reader(f):
            if len(linha) < 2 or not linha[1].strip().replace(".", "").isdigit():
                continue
            rotulos.append(linha[0].strip())
            valores.append(float(linha[1]))
    if not valores:
        return
    fig, ax = plt.subplots(figsize=(pol(LARGURA_CM), pol(7.5)))
    barras = ax.bar(range(len(valores)), valores, color="0.78",
                    edgecolor="black", linewidth=0.8, hatch="//", width=0.6)
    for b, v in zip(barras, valores):
        ax.text(b.get_x() + b.get_width() / 2, v + max(valores) * 0.02,
                ("%d" % v) if v == int(v) else ("%.1f" % v),
                ha="center", va="bottom", fontsize=9)
    ax.set_xticks(range(len(rotulos)))
    ax.set_xticklabels(rotulos, fontsize=8)
    ax.set_ylabel(rotulo_x)
    ax.set_ylim(0, max(valores) * 1.2)
    limpar_eixo(ax)
    fig.savefig(os.path.join(SAIDA, nome_png))
    plt.close(fig)


def modelos_de_csv():
    """Cria os CSV de exemplo para os dados que nao vem do log."""
    vosk = os.path.join(SAIDA, "vosk.csv")
    if not os.path.exists(vosk):
        with open(vosk, "w") as f:
            f.write("rotulo,quantidade\n")
            f.write("Correto,16\n")
            f.write("Parcialmente correto,4\n")
            f.write("Incorreto,0\n")
        print("   modelo criado: analise/vosk.csv (ajuste com seus numeros)")
    filtro = os.path.join(SAIDA, "filtro.csv")
    if not os.path.exists(filtro):
        with open(filtro, "w") as f:
            f.write("classe,recusas\n")
            for c in ["familia", "amigos", "robo", "sexual", "violencia",
                      "substancia", "religiao", "avaliacao", "sondagem",
                      "genero"]:
                f.write("%s,0\n" % c)
        print("   modelo criado: analise/filtro.csv (preencha ao gerar)")


def main():
    if not os.path.isdir(SAIDA):
        os.makedirs(SAIDA)

    turnos = ler_turnos()
    if not turnos:
        print("nenhum turno encontrado. Rode ./protocolo_teste.sh antes.")
        return

    caminho = gravar_csv(turnos)
    texto, rotas, contextos, tempos = resumo(turnos)
    print(texto)
    print("\ncsv: %s" % caminho)

    modelos_de_csv()

    plt = preparar_matplotlib()
    if plt is None:
        print("\nmatplotlib ausente. Para gerar os graficos:")
        print("   pip3 install matplotlib")
        print("Os CSV ja estao prontos, da para gerar no notebook tambem.")
        return

    grafico_latencia(plt, turnos)
    grafico_rotas(plt, rotas, len(turnos))
    grafico_contextos(plt, contextos)
    grafico_de_csv(plt, "vosk.csv", "gr4_vosk.png", "Numero de frases")
    grafico_de_csv(plt, "filtro.csv", "gr5_filtro.png", "Frases recusadas")

    print("\ngraficos salvos em: %s" % os.path.abspath(SAIDA))


if __name__ == "__main__":
    main()
