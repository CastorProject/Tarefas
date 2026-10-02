# -*- coding: utf-8 -*-
"""Classificador Naive Bayes de contexto, treinado nos proprios bancos.

Palavra-chave tem teto: exige que a crianca use exatamente a palavra
prevista. O classificador pergunta outra coisa: dadas estas palavras
juntas, qual assunto e mais provavel? Assim "gente eu sofro violem",
truncado pelo reconhecedor, ainda pesa para seguranca.

Entra DEPOIS do casamento por palavra-chave, nunca antes: a chave e
precisa, o classificador e abrangente. E so aceita acima de um limiar
de confianca, para nao chutar.

Python puro, sem sklearn. Treina em milissegundos, na hora de subir.
"""

import math
from collections import defaultdict

import bancos

LIMIAR = 0.45          # abaixo disso, prefere nao responder
MIN_PALAVRAS_UTEIS = 1

_prior = {}
_prob = {}
_vocab = set()
_treinado = [False]


def _tokens(texto):
    """Reaproveita a normalizacao do bancos: lema, regua e sem acento."""
    saida = []
    for formas in bancos.radicais(texto):
        if formas:
            saida.append(sorted(formas)[0])
    return saida


def treinar(frases_seguranca=None):
    """Monta o modelo a partir dos bancos e da lista de seguranca."""
    global _prior, _prob, _vocab
    docs = defaultdict(list)

    # Um documento por contexto: palavras-chave mais o texto do banco.
    for nome, palavras in bancos.PALAVRAS_BANCO.items():
        for p in palavras:
            docs[nome] += _tokens(p) * 3      # chave pesa mais
        banco = bancos.BANCOS.get(nome, {})
        for chave in ("perguntas", "curiosidades", "convites"):
            for frase in banco.get(chave, []):
                docs[nome] += _tokens(frase)

    # Classe de seguranca, a mais importante de todas.
    for frase in (frases_seguranca or []):
        docs["seguranca"] += _tokens(frase) * 2

    total_docs = float(sum(len(v) for v in docs.values())) or 1.0
    _vocab = set()
    for v in docs.values():
        _vocab.update(v)
    tamanho_vocab = len(_vocab) or 1

    _prior = {}
    _prob = {}
    for classe, toks in docs.items():
        # A priori UNIFORME, nao proporcional ao tamanho da classe.
        # A classe de seguranca tem muito mais exemplos que as outras, e
        # com a priori proporcional ela dominava o calculo: "meu cachorro
        # e branco" chegou a ser classificado como sofrimento. Com a
        # priori uniforme, quem decide e a evidencia das palavras.
        _prior[classe] = math.log(1.0 / max(len(docs), 1))
        contagem = defaultdict(int)
        for t in toks:
            contagem[t] += 1
        n = float(len(toks))
        _prob[classe] = {}
        for t in _vocab:
            # Laplace: palavra nao vista na classe nao zera a conta toda
            _prob[classe][t] = math.log((contagem[t] + 1.0) /
                                        (n + tamanho_vocab))
        _prob[classe]["__default__"] = math.log(1.0 / (n + tamanho_vocab))

    _treinado[0] = True
    return len(_prior), len(_vocab)


def classificar(texto):
    """Devolve (classe, confianca). Confianca de 0 a 1."""
    if not _treinado[0] or not texto:
        return "", 0.0
    toks = [t for t in _tokens(texto) if t in _vocab]
    if len(toks) < MIN_PALAVRAS_UTEIS:
        return "", 0.0

    escores = {}
    for classe in _prior:
        s = _prior[classe]
        tabela = _prob[classe]
        padrao = tabela["__default__"]
        for t in toks:
            s += tabela.get(t, padrao)
        escores[classe] = s

    # log para probabilidade, de forma estavel
    maior = max(escores.values())
    soma = sum(math.exp(v - maior) for v in escores.values())
    melhor = max(escores, key=escores.get)
    conf = math.exp(escores[melhor] - maior) / soma
    return melhor, conf


def classificar_com_limiar(texto):
    """So devolve classe se passar do limiar. Senao devolve ''."""
    classe, conf = classificar(texto)
    if conf >= LIMIAR:
        return classe, conf
    return "", conf



# ---------------------------------------------------------------------
# Detector binario de sofrimento.
#
# O classificador de 23 classes se mostrou instavel com treino sintetico:
# confianca baixa e sensivel a qualquer ajuste. Reduzindo a pergunta para
# duas classes, "isto tem carga de sofrimento ou nao", a evidencia por
# classe aumenta muito e o resultado fica estavel.
#
# O roteamento de assunto continua por palavra-chave, que ja funciona.
# Aqui interessa so o caso em que errar custa caro.
# ---------------------------------------------------------------------

_bin_prob = {}
_bin_vocab = set()
_bin_pronto = [False]

LIMIAR_SOFRIMENTO = 0.60   # acima disso, trata como sofrimento


def treinar_sofrimento(frases_seguranca):
    """Duas classes: sofrimento contra o resto do conteudo dos bancos."""
    global _bin_prob, _bin_vocab, _bin_pronto
    docs = {"sofrimento": [], "neutro": []}

    for frase in (frases_seguranca or []):
        docs["sofrimento"] += _tokens(frase)

    for nome, palavras in bancos.PALAVRAS_BANCO.items():
        for p in palavras:
            docs["neutro"] += _tokens(p)
        banco = bancos.BANCOS.get(nome, {})
        for chave in ("perguntas", "curiosidades", "convites", "reacoes"):
            for frase in banco.get(chave, []):
                docs["neutro"] += _tokens(frase)

    _bin_vocab = set(docs["sofrimento"]) | set(docs["neutro"])
    tam = len(_bin_vocab) or 1
    _bin_prob = {}
    for classe, toks in docs.items():
        cont = {}
        for t in toks:
            cont[t] = cont.get(t, 0) + 1
        n = float(len(toks))
        tabela = {}
        for t in _bin_vocab:
            tabela[t] = math.log((cont.get(t, 0) + 1.0) / (n + tam))
        tabela["__default__"] = math.log(1.0 / (n + tam))
        _bin_prob[classe] = tabela

    _bin_pronto[0] = True
    return len(docs["sofrimento"]), len(docs["neutro"]), len(_bin_vocab)


def risco_sofrimento(texto):
    """Probabilidade de 0 a 1 de a fala ter carga de sofrimento."""
    if not _bin_pronto[0] or not texto:
        return 0.0
    toks = [t for t in _tokens(texto) if t in _bin_vocab]
    if not toks:
        return 0.0
    escores = {}
    for classe in ("sofrimento", "neutro"):
        tabela = _bin_prob[classe]
        padrao = tabela["__default__"]
        s = math.log(0.5)
        for t in toks:
            s += tabela.get(t, padrao)
        escores[classe] = s
    maior = max(escores.values())
    soma = sum(math.exp(v - maior) for v in escores.values())
    return math.exp(escores["sofrimento"] - maior) / soma


def parece_sofrimento(texto):
    return risco_sofrimento(texto) >= LIMIAR_SOFRIMENTO
