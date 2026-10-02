# -*- coding: utf-8 -*-
"""Gera os graficos do relatorio a partir dos CSV.

Roda no notebook, nao na Raspberry. Le analise/turnos.csv (produzido por
analisar_sessoes.py na Rasp) mais os CSV auxiliares, e escreve os PNG.

Graficos sem titulo interno: na ABNT a legenda fica acima da figura,
dentro do documento. Largura de 16 cm, area util do modelo do Piic
(A4 com margens de 3 e 2 cm). Cinza com hachura, legivel em P&B.

    pip install matplotlib
    python3 gerar_graficos.py [pasta_analise]
"""

import os
import csv
import sys
from collections import Counter

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

LARGURA_CM = 16.0
LIMIAR_LITERATURA = 2.5      # Miller, Meyer e Smart (2025)

# Latencia medida na arquitetura anterior, com o LLM respondendo ao vivo.
# Troque pelos valores que voce mediu e registrou.
LLM_MIN = 30.0
LLM_MAX = 136.0

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

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "Liberation Serif", "DejaVu Serif"],
    "font.size": 10,
    "axes.linewidth": 0.8,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
})


def pol(cm):
    return cm / 2.54


def limpar(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def ler_turnos(pasta):
    caminho = os.path.join(pasta, "turnos.csv")
    if not os.path.exists(caminho):
        sys.exit("nao achei %s" % caminho)
    turnos = []
    with open(caminho, encoding="utf-8") as f:
        for linha in csv.DictReader(f):
            try:
                linha["tempo_s"] = float(linha["tempo_s"])
            except (ValueError, KeyError):
                linha["tempo_s"] = 0.0
            turnos.append(linha)
    return turnos


def ler_par(pasta, nome):
    """CSV de duas colunas: rotulo,valor. Devolve [] se nao existir."""
    caminho = os.path.join(pasta, nome)
    if not os.path.exists(caminho):
        return []
    itens = []
    with open(caminho, encoding="utf-8") as f:
        for linha in csv.reader(f):
            if len(linha) < 2:
                continue
            try:
                itens.append((linha[0].strip(), float(linha[1])))
            except ValueError:
                continue          # pula o cabecalho
    return itens


def gr1_latencia(pasta, turnos):
    tempos = [t["tempo_s"] for t in turnos]
    atual = sum(tempos) / len(tempos) if tempos else 0.0
    piso = 0.01                   # escala log nao aceita zero
    llm_medio = (LLM_MIN + LLM_MAX) / 2.0

    fig, ax = plt.subplots(figsize=(pol(LARGURA_CM), pol(8.0)))
    ax.bar([0], [llm_medio],
           yerr=[[llm_medio - LLM_MIN], [LLM_MAX - llm_medio]],
           color="0.55", edgecolor="black", linewidth=0.8,
           hatch="//", capsize=5, width=0.5)
    ax.bar([1], [max(atual, piso)], color="0.88", edgecolor="black",
           linewidth=0.8, hatch="..", width=0.5)

    ax.set_yscale("log")
    ax.set_ylim(piso / 2, LLM_MAX * 4)
    ax.set_xlim(-0.6, 1.6)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["LLM em tempo real\n(arquitetura anterior)",
                        "Rota deterministica\n(arquitetura atual)"], fontsize=9)
    ax.set_ylabel("Tempo de resposta (s), escala logaritmica")
    ax.axhline(LIMIAR_LITERATURA, color="black", linestyle="--", linewidth=1.0)
    ax.text(1.55, LIMIAR_LITERATURA * 1.25, "limiar de 2,5 s",
            fontsize=8, ha="right")
    ax.text(0, LLM_MAX * 1.4, "%.0f a %.0f s" % (LLM_MIN, LLM_MAX),
            ha="center", fontsize=9)
    ax.text(1, max(atual, piso) * 1.8, "%.1f s" % atual,
            ha="center", fontsize=9)
    limpar(ax)
    fig.savefig(os.path.join(pasta, "gr1_latencia.png"))
    plt.close(fig)


def barras_v(pasta, arquivo, itens, rotulo_y, percentual=False, total=0):
    if not itens:
        print("   sem dados para %s" % arquivo)
        return
    rotulos = [NOMES_ROTA.get(r, r) for r, _ in itens]
    valores = [v for _, v in itens]
    fig, ax = plt.subplots(figsize=(pol(LARGURA_CM), pol(8.0)))
    barras = ax.bar(range(len(itens)), valores, color="0.78",
                    edgecolor="black", linewidth=0.8, hatch="//", width=0.6)
    for b, v in zip(barras, valores):
        txt = "%d" % v if v == int(v) else "%.1f" % v
        if percentual and total:
            txt += "\n(%.0f%%)" % (100.0 * v / total)
        ax.text(b.get_x() + b.get_width() / 2, v + max(valores) * 0.02,
                txt, ha="center", va="bottom", fontsize=8)
    ax.set_xticks(range(len(itens)))
    ax.set_xticklabels(rotulos, fontsize=8)
    ax.set_ylabel(rotulo_y)
    ax.set_ylim(0, max(valores) * 1.25)
    limpar(ax)
    fig.savefig(os.path.join(pasta, arquivo))
    plt.close(fig)


def gr3_contextos(pasta, turnos):
    itens = Counter(t["contexto_banco"] for t in turnos
                    if t["contexto_banco"]).most_common()
    if not itens:
        print("   nenhum contexto acionado")
        return
    altura = max(5.0, 0.55 * len(itens) + 2.0)
    valores = [v for _, v in itens]
    fig, ax = plt.subplots(figsize=(pol(LARGURA_CM), pol(altura)))
    ax.barh(range(len(itens)), valores, color="0.78", edgecolor="black",
            linewidth=0.8, hatch="\\\\", height=0.6)
    for i, v in enumerate(valores):
        ax.text(v + max(valores) * 0.02, i, str(int(v)),
                va="center", fontsize=8)
    ax.set_yticks(range(len(itens)))
    ax.set_yticklabels([c for c, _ in itens], fontsize=8)
    ax.invert_yaxis()
    ax.set_xlabel("Numero de acionamentos")
    ax.set_xlim(0, max(valores) * 1.15)
    limpar(ax)
    fig.savefig(os.path.join(pasta, "gr3_contextos.png"))
    plt.close(fig)


def main():
    pasta = sys.argv[1] if len(sys.argv) > 1 else "analise"
    turnos = ler_turnos(pasta)
    print("%d turnos lidos de %s" % (len(turnos), pasta))

    gr1_latencia(pasta, turnos)
    print("   gr1_latencia.png")

    rotas = Counter(t["rota"] for t in turnos).most_common()
    barras_v(pasta, "gr2_rotas.png", rotas, "Numero de respostas",
             percentual=True, total=len(turnos))
    print("   gr2_rotas.png")

    gr3_contextos(pasta, turnos)
    print("   gr3_contextos.png")

    barras_v(pasta, "gr4_vosk.png", ler_par(pasta, "vosk.csv"),
             "Numero de frases")
    print("   gr4_vosk.png")

    barras_v(pasta, "gr5_filtro.png", ler_par(pasta, "filtro.csv"),
             "Frases recusadas")
    print("   gr5_filtro.png")

    print("\npronto, em %s" % os.path.abspath(pasta))


if __name__ == "__main__":
    main()
