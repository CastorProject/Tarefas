# -*- coding: utf-8 -*-
"""Bancos de resposta do Castor.

Le os JSON de ../respostas/ e monta o turno combinando:
    reacao + (convite | curiosidade) + pergunta

Regras de projeto:
  - Nunca presumir familia, amigos ou que a crianca gosta de estar com gente.
  - Nao inventa fato: so usa o que esta nos JSON.
  - Responde em menos de 25 palavras (limite do validador).
"""

import os
import re
import re as _re_mod
import json
import random

PASTA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "respostas")

BANCOS = {}
PERSONA = {}
IDENTIDADE = {}
SOBRE = {}
CONVERSA = {}

_ultimo = {}          # evita repetir a mesma frase seguidas vezes
_contador_turno = 0   # a cada N turnos solta uma curiosidade

MAX_PALAVRAS = 22
TURNOS_ATE_CURIOSIDADE = 3

try:
    _TEXTO = unicode
except NameError:
    _TEXTO = str


def _saida(s):
    """Em Python 2 devolve str utf-8; em Python 3 devolve str."""
    if str is bytes and isinstance(s, _TEXTO):
        return s.encode("utf-8")
    return s


def carregar():
    """Le todos os JSON da pasta respostas/. Chamar uma vez no inicio."""
    global BANCOS, PERSONA, IDENTIDADE, SOBRE, CONVERSA
    BANCOS = {}
    PERSONA = {}
    IDENTIDADE = {}
    SOBRE = {}
    CONVERSA = {}
    if not os.path.isdir(PASTA):
        print("[BANCOS] pasta nao encontrada: %s" % PASTA)
        return 0
    for arquivo in sorted(os.listdir(PASTA)):
        if not arquivo.endswith(".json"):
            continue
        nome = arquivo[:-5]
        caminho = os.path.join(PASTA, arquivo)
        try:
            f = open(caminho)
            dados = json.load(f)
            f.close()
        except Exception as e:
            print("[BANCOS] erro em %s: %s" % (arquivo, e))
            continue
        if nome == "persona":
            PERSONA = dados
        elif nome == "autismo":
            IDENTIDADE = dados
        elif nome == "sobre_castor":
            SOBRE = dados
        elif nome == "conversa":
            CONVERSA = dados
        elif nome == "psicologa":
            pass          # usado pelo interaction.py, nao e banco de contexto
        else:
            BANCOS[nome] = dados
    print("[BANCOS] %d contextos + persona com %d topicos"
          % (len(BANCOS), len(PERSONA)))
    return len(BANCOS)


_usados = {}


def _sortear(chave, opcoes):
    """Sorteia sem repetir NENHUMA ja usada, ate esgotar o banco.

    Evitar so a ultima nao basta: com 5 frases a crianca ouve a mesma
    pergunta de novo no terceiro turno.
    """
    if not opcoes:
        return ""
    usados = _usados.setdefault(chave, set())
    livres = [o for o in opcoes if o not in usados]
    if not livres:
        usados.clear()
        livres = list(opcoes)
    escolha = random.choice(livres)
    usados.add(escolha)
    return escolha


def reiniciar():
    """Zera o estado. Chamar quando comecar uma sessao nova."""
    global _banco_atual, _turnos_no_banco, _contador_turno
    _usados.clear()
    _ultimo.clear()
    _banco_atual = ""
    _turnos_no_banco = 0
    _contador_turno = 0
    _passo_sobre[0] = 0
    _turno_escuta[0] = 0


# Ordem de checagem da persona: do mais especifico ao mais generico.
# Dicionario nao tem ordem garantida em Python 2, entao a ordem fica aqui.
ORDEM_PERSONA = ["nome", "idade", "origem", "e_robo", "cor", "animal",
                 "musica_gosto", "gosta_fazer", "sabe_fazer",
                 "sentimento_dele", "amizade", "nao_provou",
                 "nao_conheceu", "gosta_generico"]


def resposta_persona(texto):
    """Responde perguntas sobre o proprio Castor. '' se nao for uma."""
    if not PERSONA or not texto:
        return ""
    t = texto.lower()
    ordem = [x for x in ORDEM_PERSONA if x in PERSONA]
    ordem += [x for x in PERSONA if x not in ORDEM_PERSONA]
    for topico in ordem:
        for gatilho in PERSONA[topico].get("gatilhos", []):
            if gatilho in t:
                return _saida(_sortear("persona:" + topico,
                                       PERSONA[topico].get("respostas", [])))
    return ""


# Palavras frequentes demais para indicar assunto. Sem isso, "gosto",
# "tenho" ou "muito" casariam com quase qualquer curiosidade.
PALAVRAS_COMUNS = set((
    "gosto gosta gostar gostei tenho temos muito muita pouco pouca meu minha "
    "seu sua esse essa isso aqui ali fazer faco faz fazendo quero quer acho "
    "achei vejo viu ontem hoje amanha tambem porque quando onde como mais "
    "menos ficar fica ficou ter tem dele dela nosso nossa para pela pelo "
    "pode posso sabe sabia coisa coisas gente sempre nunca agora depois"
).split())


def _curiosidade_relacionada(banco, texto, chave):
    """Curiosidade que fala do que a crianca citou, ou '' se nao houver.

    Sem isso o robo responde "sabia que o polvo tem tres coracoes?" para
    quem acabou de falar do proprio cachorro - e parece que nao ouviu.
    """
    opcoes = banco.get("curiosidades", [])
    if not opcoes or not texto:
        return ""
    t = sem_diminutivo(texto.lower())
    palavras = [p for p in re.findall(r"\w{4,}", t)
                if p not in PALAVRAS_COMUNS]
    if not palavras:
        return ""

    # Pontua: vence a curiosidade que casa com MAIS palavras da fala.
    # Sem isso, "meu gato dorme muito" casava com "Peixe dorme de olho
    # aberto" so pelo verbo, e o robo falava do bicho errado.
    melhores, pontos = [], 0
    for c in opcoes:
        cl = sem_diminutivo(c.lower())
        n = sum(1 for p in palavras if p in cl)
        if n > pontos:
            melhores, pontos = [c], n
        elif n == pontos and n > 0:
            melhores.append(c)

    if pontos == 0:
        return ""
    return _sortear(chave, melhores)


def resposta_do_banco(contexto, texto=""):
    """Monta um turno do banco daquele contexto. '' se nao existir banco."""
    global _contador_turno
    banco = BANCOS.get(contexto)
    if not banco:
        return ""

    _contador_turno += 1
    partes = []

    reacao = _sortear(contexto + ":reacoes", banco.get("reacoes", []))
    if reacao:
        partes.append(reacao)

    # De tempos em tempos ensina algo - mas so se a curiosidade falar do
    # que a crianca citou. Senao convida ela a contar, que e sempre no tema.
    meio = ""
    if _contador_turno % TURNOS_ATE_CURIOSIDADE == 0:
        meio = _curiosidade_relacionada(banco, texto,
                                        contexto + ":curiosidades")
    if not meio:
        meio = _sortear(contexto + ":convites", banco.get("convites", []))
    if meio:
        partes.append(meio)

    # so acrescenta pergunta se o meio nao foi ja um convite/pergunta
    if meio and meio.endswith(".") or not meio:
        pergunta = _sortear(contexto + ":perguntas", banco.get("perguntas", []))
        if pergunta:
            partes.append(pergunta)

    frase = " ".join(partes).strip()
    while len(frase.split()) > MAX_PALAVRAS and len(partes) > 1:
        partes.pop()
        frase = " ".join(partes).strip()
    return _saida(frase)


def contextos_disponiveis():
    return sorted(BANCOS.keys())


# --- deteccao de contexto dos bancos -------------------------------------
# Independente do detectar_contexto() do interaction.py, que continua
# cuidando do prompt do LLM. Aqui so decide QUAL banco abrir.
# Ordem: do mais especifico ao mais generico (primeiro que casar vence).

PALAVRAS_BANCO = {
    "comemoracoes": ["aniversario", "aniversário", "parabens", "parabéns", "festa",
                     "comemorar", "velinha", "ganhei", "passei de ano", "formatura"],
    "jogos_cartas": ["carta", "baralho", "deck", "magic", "pokemon", "pokémon",
                     "yugioh", "yu-gi-oh", "beyblade", "uno", "truco", "dixit",
                     "tabuleiro"],
    "quebracabeca": ["quebra-cabeca", "quebra-cabeça", "quebra cabeca",
                     "quebra cabeça", "lego", "montar", "montei", "montando", "pecinha", "peça",
                     "caca-palavra", "caça-palavra", "caça palavras", "encaixar"],
    "espaco":       ["espaco", "espaço", "planeta", "estrela", "lua", "marte",
                     "jupiter", "júpiter", "saturno", "foguete", "astronauta",
                     "galaxia", "galáxia", "universo", "cometa"],
    "desenhos":     ["desenho animado", "cartoon", "anime", "episodio", "episódio",
                     "personagem", "dublador"],
    "historias":    ["historia", "história", "livro", "ler", "leitura", "conto",
                     "fabula", "fábula", "autor", "biblioteca", "gibi", "quadrinho"],
    "musica":       ["musica", "música", "cantar", "cantei", "cantando", "cantoria", "cancao", "canção", "cantiga",
                     "violao", "violão", "guitarra", "piano", "bateria", "tambor",
                     "danc", "danç", "ritmo", "banda"],
    "esportes":     ["futebol", "bola", "gol", "basquete", "volei", "vôlei",
                     "correr", "corri", "corrida", "natacao", "natação",
                     "nadar", "nadei", "nadando", "time",
                     "campeonato", "skate"],
    "veiculos":     ["carro", "moto", "onibus", "ônibus", "caminhao", "caminhão",
                     "trem", "aviao", "avião", "barco", "navio", "submarino",
                     "bicicleta", "helicoptero", "helicóptero", "trator"],
    "profissoes":   ["profissao", "profissão", "trabalho", "trabalhar", "medico",
                     "médico", "professor", "bombeiro", "policial", "veterinario",
                     "veterinário", "dentista", "engenheiro", "piloto",
                     "quando crescer"],
    "tecnologia":   ["computador", "robo", "robô", "celular", "tablet",
                     "videogame", "video game", "programar", "codigo", "código",
                     "internet", "maquina", "máquina", "inventar"],
    "numeros":      ["numero", "número", "matematica", "matemática", "somar",
                     "subtrair", "multiplicar", "dividir", "tabuada", "contar ate",
                     "contar até"],
    "geografia":    ["cidade", "mapa", "mundo", "viaj", "viagem",
                     "brasil", "continente", "capital"],
    "animais":      ["cachorro", "cao", "cão", "gato", "passarinho", "passaro",
                     "pássaro", "peixe", "bicho", "animal", "cavalo", "coelho",
                     "tartaruga", "hamster", "papagaio", "leao", "leão", "elefante",
                     "girafa", "macaco", "cobra", "borboleta", "formiga"],
    "comida":       ["comida", "comer", "pizza", "bolo", "doce", "salgado", "fruta",
                     "banana", "chocolate", "sorvete", "lanche", "almoco", "almoço",
                     "jantar", "pipoca", "suco", "arroz", "feijao", "feijão",
                     "macarrao", "macarrão"],
    "natureza":     ["natureza", "praia", "mar", "rio", "montanha", "floresta",
                     "mato", "arvore", "árvore", "planta", "flor", "folha",
                     "chuva", "semente", "jardim", "horta"],
    "artes":        ["desenh", "pint", "lapis", "lápis",
                     "giz", "tinta", "color"],
    "fotografia":   ["foto", "fotografia", "fotograf", "camera", "câmera",
                     "retrato", "clicar", "fotografo", "fotógrafo"],
    "teatro":       ["teatro", "palco", "ator", "atriz", "atuar", "atuei", "cenario",
                     "cenário", "fantasiar", "fantasia", "apresentacao",
                     "apresentação", "peca de teatro", "peça de teatro"],
    "filmes":       ["filme", "cinema", "heroi", "herói", "super-heroi",
                     "super-herói", "vilao", "vilão", "princesa", "assist"],
    "escola":       ["escola", "colegio", "colégio", "aula", "materia",
                     "matéria", "recreio", "faculdade", "licao", "lição",
                     "prova", "caderno", "estud"],
    "organizar":    ["organiz", "arrum", "guard", "lojinha", "troco",
                     "mesada", "lista", "separar", "caixinha", "dinheiro"],
}

# Ordem: do mais especifico ao mais generico. "fotografia" precisa vir
# antes de "artes", e "teatro" antes de "quebracabeca" nao e necessario
# porque teatro usa "peca de teatro" e nao "peca" solta.
ORDEM_BANCO = ["comemoracoes", "jogos_cartas", "quebracabeca", "espaco",
               "fotografia", "teatro", "filmes", "desenhos", "historias",
               "musica", "esportes", "veiculos", "escola", "profissoes",
               "tecnologia", "numeros", "organizar", "geografia", "animais",
               "comida", "natureza", "artes"]


# Crianca fala no diminutivo o tempo todo, e o diminutivo troca a letra:
# "carta" NAO esta dentro de "cartinha" (cart-i-nha). Sem desfazer isso, o
# banco fica cego pra metade do vocabulario infantil.
_DIMINUTIVO = re.compile(r"(\w{2,})(?:z?inh)([oa]s?)\b")


def sem_diminutivo(t):
    """cartinha->carta, cachorrinho->cachorro, bolinha->bola."""
    return _DIMINUTIVO.sub(lambda m: m.group(1) + m.group(2), t)


_banco_atual = ""
_turnos_no_banco = 0
MAX_TURNOS_MESMO_BANCO = 5



try:
    import simplemma as _simplemma
    _simplemma.lemmatize("teste", lang="pt")
    _TEM_LEMA = True
except Exception:
    _TEM_LEMA = False



# Palavras cujo lema aponta para um verbo que nao tem nada a ver com o
# sentido usado. "nada" vira "nadar" e joga a frase em esportes; "canto"
# vira "cantar" e joga em musica. Para estas, vale so a forma literal.
_LEMA_ENGANOSO = set([
    "nada", "canto", "conta", "casa", "para", "sobre", "como", "era",
    "vale", "mora", "manda", "fica", "sala", "hora", "ponto", "meio",
])


def _regua(p):
    """Corte na regua: tira plural e vogal final de genero."""
    if len(p) > 3:
        if p.endswith("s"):
            p = p[:-1]
        if len(p) > 3 and p[-1] in "aoe":
            p = p[:-1]
    return p


def radicais_antigo(texto):
    """Quebra em palavras e reduz cada uma ao radical.

    Sem isso "cachorra" nao casa com "cachorro" e a crianca fala do
    proprio bicho sem o robo perceber que o assunto e animal.
    """
    t = _sem_acento(sem_diminutivo(texto.lower()))
    saida = []
    for p in re.findall(r"\w+", t):
        if len(p) > 3:
            if p.endswith("s"):
                p = p[:-1]
            if len(p) > 3 and p[-1] in "aoe":
                p = p[:-1]
        saida.append(p)
    return saida


def _contem_radical(radicais_texto, chave):
    """A sequencia de radicais da chave aparece na do texto?

    Compara sequencia de palavras, nao pedaco de texto solto.
    """
    return _casa_formas(radicais_texto, chave, radicais)


def detectar_banco(texto):
    """Devolve o banco que casa com a fala, ou continua no assunto anterior.

    Se a crianca responde algo curto ("ele e branco", "sim"), nenhuma palavra
    casa - mas ela ainda esta falando do cachorro. Trocar de assunto ai e o
    que faz o robo parecer que nao esta ouvindo.
    """
    global _banco_atual, _turnos_no_banco
    if not texto:
        return ""
    t = texto.lower()
    t_base = sem_diminutivo(t)
    rad = radicais(t)
    for nome in ORDEM_BANCO:
        for palavra in PALAVRAS_BANCO.get(nome, []):
            # \b exige inicio de palavra: "chamar" nao casa com "mar",
            # mas "cartinha" ainda casa com "carta" (diminutivo de crianca).
            padrao = r"\b" + re.escape(palavra)
            # Tres camadas: forma literal, sem diminutivo, e por radical.
            # A terceira pega flexao de genero e numero.
            if (re.search(padrao, t) or re.search(padrao, t_base)
                    or _contem_radical(rad, palavra)):
                if nome != _banco_atual:
                    _banco_atual = nome
                    _turnos_no_banco = 1
                else:
                    _turnos_no_banco += 1
                return nome

    # Nada casou: segue no assunto anterior em vez de abandonar a crianca.
    if _banco_atual and _turnos_no_banco < MAX_TURNOS_MESMO_BANCO:
        _turnos_no_banco += 1
        return _banco_atual

    _banco_atual = ""
    _turnos_no_banco = 0
    return ""



def _sem_acento(t):
    """A comparacao nao pode depender de acentuacao da transcricao."""
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFD", t)
                   if unicodedata.category(c) != "Mn")


def resposta_identidade(texto):
    """Crianca diz que e autista, sem sofrimento: acolhe e deixa espaco.

    NUNCA encaminha para a psicologa. Identidade nao e problema a
    encaminhar, e tratar como tal e a moldura de deficit que a literatura
    aponta como prejudicial (Stark, Stacey e Knight, 2025). Sofrimento
    explicito e pego antes, na camada de seguranca do interaction.py.

    Nenhuma resposta aqui faz pergunta: a crianca acabou de contar algo
    sobre ela, e devolver um questionario seria provar que nao foi ouvida.
    """
    if not IDENTIDADE or not texto:
        return ""
    t = _sem_acento(texto.lower())
    for g in IDENTIDADE.get("gatilhos", []):
        if _sem_acento(g.lower()) in t:
            return _saida(_sortear("identidade",
                                   IDENTIDADE.get("respostas", [])))
    return ""


_passo_sobre = [0]


def resposta_sobre_castor(texto):
    """Explica o Castor em sequencia: cada pergunta traz um item novo.

    Evita a repeticao de uma resposta unica e permite aprofundar sem
    inventar nada. Ao chegar no fim, devolve a palavra para a crianca.
    """
    if not SOBRE or not texto:
        return ""
    t = _sem_acento(texto.lower())
    if not any(_sem_acento(g.lower()) in t for g in SOBRE.get("gatilhos", [])):
        return ""
    seq = SOBRE.get("sequencia", [])
    if not seq:
        return ""
    i = min(_passo_sobre[0], len(seq) - 1)
    _passo_sobre[0] = i + 1
    return _saida(seq[i])


def radicais(texto):
    """Cada palavra vira um CONJUNTO de formas possiveis.

    Tres fontes, somadas: a palavra como veio, o lema do simplemma e o
    corte na regua. Basta uma coincidir. O lema erra as vezes
    (amiga -> amigar) e a regua cobre; a regua e grosseira e o lema cobre.
    """
    t = sem_diminutivo(texto.lower())
    saida = []
    for p in _re_mod.findall(r"\w+", t):
        base = _sem_acento(p)
        # Palavra ambigua vale SO na forma literal. Sem isso "nada" ganha
        # o lema "nadar" e a frase "eu nao sei nada" cai em esportes.
        if base in _LEMA_ENGANOSO:
            saida.append(set([base]))
            continue
        lema = ""
        if _TEM_LEMA:
            try:
                lema = _sem_acento(_simplemma.lemmatize(p, lang="pt").lower())
            except Exception:
                lema = ""
        # AQUI o criterio e precisao, nao abrangencia. Mandar a crianca
        # para o assunto errado atrapalha a conversa, entao a regua bruta
        # so entra quando o lematizador nao reconheceu a palavra.
        # Na camada de seguranca (interaction.py) vale o contrario: la as
        # tres formas somam, porque errar para mais custa pouco.
        if lema and lema != base:
            formas = set([base, lema])
        else:
            formas = set([base, _regua(base)])
        saida.append(formas)
    return saida


MAX_LACUNA = 2   # palavras que podem aparecer no meio da expressao


def _casa_formas(formas_texto, chave, fn_formas):
    """A chave aparece no texto, tolerando palavras no meio?

    Sem isso a chave "nao tenho amigos" nao casa com "nao tenho NENHUMA
    amiga", nem "sou burro" com "sou MUITO burro". Crianca fala assim, e
    exigir as palavras coladas perde uma familia inteira de casos.
    """
    ch = fn_formas(chave)
    n = len(ch)
    if n == 0:
        return False
    total = len(formas_texto)
    for inicio in range(total):
        if not (formas_texto[inicio] & ch[0]):
            continue
        pos = inicio + 1
        j = 1
        while j < n:
            achou = False
            limite = min(total, pos + MAX_LACUNA + 1)
            while pos < limite:
                if formas_texto[pos] & ch[j]:
                    achou = True
                    pos += 1
                    break
                pos += 1
            if not achou:
                break
            j += 1
        if j == n:
            return True
    return False

_turno_escuta = [0]
ESCUTA_SEM_PERGUNTA = 3   # a cada N turnos, so um devolve pergunta


def _casa_gatilho(bloco, texto):
    t = _sem_acento(texto.lower())
    for g in bloco.get("gatilhos", []):
        if _sem_acento(g.lower()) in t:
            return True
    return False


def resposta_xingamento(texto):
    """Ofensa dirigida ao Castor: nao retruca, nao se humilha, segue."""
    b = CONVERSA.get("xingamento")
    if not b or not texto or not _casa_gatilho(b, texto):
        return ""
    return _saida(_sortear("xingamento", b.get("respostas", [])))


def resposta_nao_sabe(texto):
    """Pessoa nao sabe o que falar: sugere assunto, nao devolve pergunta."""
    b = CONVERSA.get("nao_sabe")
    if not b or not texto or not _casa_gatilho(b, texto):
        return ""
    return _saida(_sortear("nao_sabe", b.get("respostas", [])))


def resposta_escuta():
    """Fala sem assunto reconhecido: acolhe sem cobrar.

    Devolve '' de tempos em tempos de proposito, para cair no template
    antigo e a conversa nao morrer de tanto so acolher. A maior parte
    dos turnos e so reacao, porque nem todo turno precisa de pergunta.
    """
    if not CONVERSA:
        return ""
    _turno_escuta[0] += 1
    if _turno_escuta[0] % ESCUTA_SEM_PERGUNTA == 0:
        return ""
    partes = [_sortear("escuta:reacoes", CONVERSA.get("reacoes", []))]
    if _turno_escuta[0] % 2 == 0:
        partes.append(_sortear("escuta:convites", CONVERSA.get("convites", [])))
    return _saida(" ".join(p for p in partes if p))
