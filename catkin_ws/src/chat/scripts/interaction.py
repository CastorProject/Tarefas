"""
================================================================================
Módulo CORE de Cognição — CASTOR
================================================================================
PROJETO: CASTOR — labtel/ufes
DESCRIÇÃO: Processa o texto recebido pelo Vosk e gera a resposta do CASTOR
           usando o Ollama rodando localmente (offline, sem API key).

SISTEMA DE CONTEXTO (baseado em Li et al. 2025 — MiRo-E):
  Cada tipo de interação tem um prompt específico em src/prompts/contextos/
  O sistema detecta automaticamente o contexto pela mensagem da criança
  e carrega o prompt certo — respostas mais precisas com modelo pequeno.

PARA ADICIONAR NOVO CONTEXTO:
  1. Crie src/prompts/contextos/instrucoes_NOVOCONTEXTO.txt
  2. Adicione as palavras-chave em CONTEXTOS abaixo
  3. Pronto! O sistema detecta e usa automaticamente.

PARÂMETROS LLM:
  Qwen3 Technical Report (2025) — temperature=0.7, top_p=0.8, top_k=20
  para modo non-thinking (diálogo eficiente e natural)
================================================================================
"""

import os
import re
import random
import difflib
import requests
import bancos
bancos.carregar()

import os as _os
import json as _json
import random as _random
import unicodedata as _unicodedata


def _sem_acento(t):
    """Remove acento. A seguranca nao pode depender de acentuacao correta:
    basta o reconhecedor devolver 'ninguem' em vez de 'ninguem' com acento
    para uma frase de sofrimento passar batido."""
    return "".join(c for c in _unicodedata.normalize("NFD", t)
                   if _unicodedata.category(c) != "Mn")


import re as _re
import re as _re_mod

_DIMIN_RE = _re.compile(r"(\w{2,})(?:z?inh)([oa]s?)\b")



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


def _radicais_antigo(texto):
    """Quebra em palavras e reduz cada uma ao radical.

    O portugues flexiona demais: cachorro/cachorra/cachorrinho,
    amigo/amiga/amigos. Comparar forma exata perde tudo isso, e quando a
    perda acontece numa frase de sofrimento o custo e alto. Ja aconteceu
    tres vezes: acento, conjugacao e plural.
    """
    t = _sem_acento(texto.lower())
    t = _DIMIN_RE.sub(lambda m: m.group(1) + m.group(2), t)
    saida = []
    for p in _re.findall(r"\w+", t):
        if len(p) > 3:
            if p.endswith("s"):
                p = p[:-1]
            if len(p) > 3 and p[-1] in "aoe":
                p = p[:-1]
        saida.append(p)
    return saida


def _contem_radical(radicais_texto, chave):
    """A sequencia de radicais da chave aparece na do texto?

    Compara sequencia de palavras, nao pedaco de texto: evita que
    'mar' case dentro de 'chamar'.
    """
    return _casa_formas(radicais_texto, chave, _radicais)


def _carregar_psicologa():
    caminho = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)),
                            "..", "respostas", "psicologa.json")
    try:
        with open(caminho, encoding="utf-8") as arq:
            return _json.load(arq)["respostas"]
    except Exception as erro:
        print("[PSICOLOGA] nao carregou (%s), usando frase unica" % erro)
        return []


RESPOSTAS_PSICOLOGA = _carregar_psicologa()
_ultima_psicologa = [""]
print("[PSICOLOGA] %d respostas carregadas" % len(RESPOSTAS_PSICOLOGA))


def redirecionar():
    """Resposta de seguranca: conteudo invariante, formulacao variada.

    O que nao muda: acolher sem julgar e apontar para a psicologa.
    O que muda: as palavras, para a crianca nao ouvir a mesma sentenca
    cada vez que desabafa."""
    if not RESPOSTAS_PSICOLOGA:
        return RESPOSTA_REDIRECIONAR
    livres = [r for r in RESPOSTAS_PSICOLOGA if r != _ultima_psicologa[0]]
    escolha = _random.choice(livres or RESPOSTAS_PSICOLOGA)
    _ultima_psicologa[0] = escolha
    return escolha

PASTA_ATUAL     = os.path.dirname(os.path.abspath(__file__))
PASTA_CONTEXTOS = os.path.join(PASTA_ATUAL, "..", "prompts", "contextos")
CAMINHO_BASE    = os.path.join(PASTA_ATUAL, "..", "prompts", "instrucoes_base.txt")

# --- CONFIGURAÇÃO DO OLLAMA ---
# llama-server usa /v1/chat/completions (compatível com OpenAI API)
URL_OLLAMA    = "http://localhost:11434/v1/chat/completions"
MODELO        = "qwen2.5-0.5b-instruct"  # modelo carregado no llama-server
TEMPERATURA   = 0.7
TOP_P         = 0.8
TOP_K         = 20
MAX_HISTORICO = 2
MIN_PALAVRAS  = 1

# Similaridade mínima para considerar resposta repetida (0.0 a 1.0)
# 0.7 = 70% similar já considera repetição
LIMIAR_REPETICAO = 0.7

WAKE_WORD = "castor"

INSTRUCAO_PADRAO = "Você é o robô Castor, um amigo carinhoso de crianças. Responda em 1 frase curta em português."

# ============================================================
# MAPEAMENTO DE CONTEXTOS
# ============================================================
# PARA ADICIONAR NOVO CONTEXTO:
#   Adicione uma nova entrada aqui e crie o arquivo correspondente.
#   Exemplo:
#   "musica": {
#       "arquivo": "instrucoes_musica.txt",
#       "palavras": ["música", "cantar", "dançar", "funk", "sertanejo"]
#   },
# ============================================================

CONTEXTOS = {

    "nome": {
        "arquivo": "instrucoes_nome.txt",
        "palavras": [
            "me chamo", "pode me chamar", "me chamam",
            "pode chamar", "quero ser chamado", "quero ser chamada",
            "quero mudar meu nome", "errou meu nome",
        ]
    },

    "brincar": {
        "arquivo": "instrucoes_brincar.txt",
        "palavras": [
            "brincar", "jogar", "jogo", "animal", "cachorro", "gato",
            "música", "desenho", "dançar", "cantar", "videogame",
            "super-herói", "personagem", "filme", "série", "cor preferida",
            "comida", "pizza", "chocolate", "esporte", "futebol", "basquete",
            "natação", "dança", "teatro", "pintar", "colorir"
        ]
    },

    "sentimento": {
        "arquivo": "instrucoes_sentimento.txt",
        "palavras": [
            "estou triste", "tô triste", "to triste", "estou chorando",
            "estou com medo", "tô com medo", "estou com raiva", "tô com raiva",
            "estou feliz", "tô feliz", "to feliz", "que legal", "adorei",
            "estou ansioso", "estou nervoso", "estou mal", "não estou bem",
            "me sinto", "sinto muito", "tô bem", "estou bem"
        ]
    },

    "estudos": {
        "arquivo": "instrucoes_estudos.txt",
        "palavras": [
            "escola", "colégio", "professor", "aula", "matéria",
            "prova", "nota", "dever", "estudar", "aprender",
            "turma", "colega", "recreio", "lição", "tarefa"
        ]
    },

    "psicologa": {
        "arquivo": "instrucoes_psicologa.txt",
        "palavras": [
            "meus pais brigam", "minha família briga", "ninguém gosta de mim",
            "me batem", "me xingam", "não tenho amigos", "todo mundo me odeia",
            "fui excluído", "odeio ter autismo", "não quero ser autista",
            "me machucar", "quero morrer", "não quero viver",
            "sofro bullying",
            "nao gosto de ser autista", "nao gosto do meu autismo",
            "quer sentar comigo", "quer brincar comigo", "quer falar comigo",
            "medo de ir", "medo da escola", "medo de voltar",
            "nomes feios", "apelido ruim", "me chamam de nome",
            "sou muito burro", "sou muito ruim", "sou muito chato",
            "sofro violencia", "sofro agressao", "violencia", "violento",
            "apanho", "apanhei", "apanhava", "me bateram", "me bate",
            "me bateu", "me machucam", "me machucaram", "me maltratam",
            "maltrata", "abusam de mim", "me ameacam", "tenho medo em casa",
            "sofro agressoes", "sou agredido", "sou agredida", "me chamam de",
            "zoam de mim", "zoam comigo", "zoaram de mim", "riem de mim",
            "cacoam de mim", "debocham de mim", "desdenham", "bulling",
            "me excluem", "nao me deixam brincar", "me deixam de fora",
            "me empurram", "implicam comigo", "mexem comigo",
            "sou burro", "sou burra", "sou idiota", "sou chato", "sou chata",
            "sou estranho", "sou estranha", "sou ruim", "sou feio", "sou feia",
            "nao sirvo", "nao presto", "me odeio", "sou um lixo",
            "sou horrivel", "sou anormal", "sou doente", "sou defeituoso",
            "tem algo errado comigo", "ninguem quer brincar",
            "ninguem brinca comigo", "fico sozinho", "fico sozinha",
            "ninguem me chama", "ninguem fala comigo",
            "odeio meu autismo", "autismo e ruim", "queria nao ser autista",
            "tenho vergonha", "quero sumir", "queria sumir",
            "nao quero ir pra escola", "fico chorando", "choro muito", 
        ]
    },

    # Detecta quando a criança quer piada ou momento divertido
    "piada": {
        "arquivo": "instrucoes_piada.txt",
        "palavras": [
            "piada", "piadas", "conta uma piada", "me faz rir",
            "algo engraçado", "faz uma graça", "me divirta",
            "me conta uma", "conta uma historia", "brincadeira de palavras"
        ]
    },

    "padrao": {
        "arquivo": "instrucoes_padrao.txt",
        "palavras": []
    },
}

# ============================================================
# PERGUNTAS SOBRE NOME — tratadas diretamente no código
# ============================================================
PERGUNTAS_NOME_PROPRIO = [
    "qual meu nome", "você lembra meu nome", "como me chamo",
    "qual é meu nome", "sabe meu nome", "lembra meu nome",
    "qual o meu nome", "meu nome é qual",
    "qual a nome", "qual nome",
]

# ============================================================
# FILTRO DE SEGURANÇA
# ============================================================

TEMAS_BLOQUEAR = [
    "sexo", "sexual", "transar", "fazer amor", "nudez", "pornô", "porno",
    "corpo nu", "pelado", "pelada", "beijar na boca",
    "droga", "drogas", "maconha", "cigarro", "álcool", "beber", "fumar",
    "matar", "faca", "arma", "tiro", "sangue",
]
RESPOSTA_BLOQUEAR = "Hmm, não sei falar sobre isso! Quer me contar algo legal que você fez hoje?"

TEMAS_REDIRECIONAR = [
    "quero morrer", "não quero viver", "odeio minha vida",
    "me machucar", "se machucar", "cortar",
    "muito medo", "não consigo parar", "entrar em pânico",
    "meus pais brigam", "minha família briga", "meus pais vão se separar",
    "ninguém me quer", "ninguém gosta de mim",
    "me batem", "me xingam", "não tenho amigos", "todo mundo me odeia",
    "odeio ter autismo", "não quero ser autista",
    "me bateu", "me machucou",
]
RESPOSTA_REDIRECIONAR = "Fico feliz que você me contou. A psicóloga pode te ajudar com isso, ela se importa muito com você!"

# ============================================================
# CAMADA 3 — VALIDAÇÃO DA SAÍDA
# ============================================================
# O modelo gera, mas não fala direto com a criança: toda resposta
# passa por aqui antes de ir para o TTS.
#
# Referências:
#   Azeem et al. (2025) Int. J. Social Robotics — LLMs falham em
#     avaliações de segurança em interação humano-robô
#   Ravichandran et al. (2026) IEEE RA-L — arquitetura de guardrails
#     em duas etapas reduz execução insegura de >92% para <3%
# ============================================================

import re as _re

MAX_PALAVRAS_RESPOSTA = 25

# Marcadores de quebra de personagem observados nos testes
MARCADORES_QUEBRA = [
    "aqui está", "aqui esta", "aqui vai uma pergunta",
    "estou aqui para ajudar", "estou aqui para te ajudar",
    "como assistente", "sou uma ia", "sou uma inteligência",
    "modelo de linguagem", "posso ajudar com", "em que posso",
    "você é o castor", "voce e o castor",
    "a criança que você mencionou", "conversar com a criança",
]

# Resposta segura por contexto, usada quando a validação rejeita
RESPOSTA_SEGURA = {
    "nome":       "Que nome legal! Fico feliz em te conhecer!",
    "piada":      "Por que o livro foi ao médico? Porque estava com dor de cabeça!",
    "psicologa":  RESPOSTA_REDIRECIONAR,
    "sentimento": "Estou aqui com você! Quer me contar mais?",
    "brincar":    "Que legal! Do que você mais gosta de brincar?",
    "estudos":    "Legal! O que você mais gosta na escola?",
    "padrao":     "Me conta uma coisa que você gosta!",
}

# Português de Portugal -> português do Brasil
_TROCAS_PT = [
    (r"\btu\b", "você"), (r"\bés\b", "é"), (r"\btens\b", "tem"),
    (r"\bpodes\b", "pode"), (r"\bqueres\b", "quer"),
    (r"\bgostas\b", "gosta"), (r"\bprecisas\b", "precisa"),
    (r"\bfazes\b", "faz"), (r"\bestás\b", "está"),
    (r"\bsabes\b", "sabe"), (r"\bvais\b", "vai"),
    (r"\bteu\b", "seu"), (r"\btua\b", "sua"),
    (r"\bteus\b", "seus"), (r"\btuas\b", "suas"),
    (r"\bcontigo\b", "com você"),
    (r"\bgostarás\b", "vai gostar"), (r"\bfarás\b", "vai fazer"),
    (r"\bterás\b", "vai ter"), (r"\bserás\b", "vai ser"),
    (r"\bpoderás\b", "vai poder"), (r"\bquererás\b", "vai querer"),
    (r"\brapariga\b", "menina"), (r"\bcomboio\b", "trem"),
    (r"\bautocarro\b", "ônibus"), (r"\btelemóvel\b", "celular"),
    (r"\becrã\b", "tela"), (r"\bcasa de banho\b", "banheiro"),
    (r"\bfixe\b", "legal"), (r"\bsandes\b", "sanduíche"),
]

_GERUNDIO = {"ar": "ando", "er": "endo", "ir": "indo"}


def _corrigir_gerundio(texto):
    """'estou a falar' -> 'estou falando' (construção europeia)."""
    def troca(m):
        aux, raiz, term = m.group(1), m.group(2), m.group(3)
        return "{} {}{}".format(aux, raiz, _GERUNDIO[term])
    return _re.sub(r"\b(estou|está|estamos|estão|estava) a (\w+?)(ar|er|ir)\b",
                   troca, texto, flags=_re.IGNORECASE)


def abrasileirar(texto):
    """Converte marcadores de português europeu para o brasileiro."""
    resultado = _corrigir_gerundio(texto)
    for padrao, troca in _TROCAS_PT:
        resultado = _re.sub(padrao, troca, resultado, flags=_re.IGNORECASE)
    return resultado


def _degenerada(texto):
    """Detecta repetição em loop: 'de piadas, piadas' / 'Lá, lá, lá, lá'."""
    palavras = [p.strip(".,!?;:").lower() for p in texto.split() if p.strip(".,!?;:")]
    if len(palavras) < 3:
        return False
    return len(set(palavras)) <= max(1, len(palavras) // 3)


def validar_resposta(texto, contexto="padrao"):
    """
    Valida a resposta do LLM antes de ela chegar na criança.
    Devolve (texto_final, motivo_da_rejeicao_ou_None).
    """
    seguro = RESPOSTA_SEGURA.get(contexto, RESPOSTA_SEGURA["padrao"])

    if not texto or not texto.strip():
        return seguro, "vazia"

    texto = abrasileirar(texto.strip())
    baixo = texto.lower()

    for tema in TEMAS_BLOQUEAR:
        if tema in baixo:
            return RESPOSTA_BLOQUEAR, "tema bloqueado: {}".format(tema)

    for marcador in MARCADORES_QUEBRA:
        if marcador in baixo:
            return seguro, "quebra de personagem: {}".format(marcador)

    if _degenerada(texto):
        return seguro, "repeticao degenerada"

    if len(texto.split()) > MAX_PALAVRAS_RESPOSTA:
        primeira = _re.split(r"(?<=[.!?])\s+", texto)[0]
        if len(primeira.split()) <= MAX_PALAVRAS_RESPOSTA:
            return primeira, None
        return seguro, "resposta longa demais"

    return texto, None



def verificar_seguranca(texto: str):
    texto_lower = texto.lower()
    if any(tema in texto_lower for tema in TEMAS_BLOQUEAR):
        return RESPOSTA_BLOQUEAR
    if any(tema in texto_lower for tema in TEMAS_REDIRECIONAR):
        return redirecionar()
    return None




# ============================================================
# RESPOSTAS DETERMINÍSTICAS
# ============================================================
# Contextos cuja resposta já está definida nos arquivos de
# instrução não passam pelo LLM. Dois motivos:
#
#   1. Latência — a literatura aponta 2,5 a 3,0 s como limite
#      de tolerância em conversa com robô (Miller et al., 2025).
#      O LLM local leva 20 a 70 s; o template leva milissegundos.
#
#   2. Segurança — em temas sensíveis (sofrimento, bullying,
#      autismo) a resposta precisa ser auditável e sempre
#      adequada. Modelos pequenos falham em avaliações de
#      segurança em interação humano-robô (Azeem et al., 2025).
# ============================================================

MARCADORES_NOME = [
    "meu nome é", "meu nome e", "me chamo", "me chamam",
    "pode me chamar de", "pode me chamar", "pode chamar de",
    "quero ser chamado de", "quero ser chamada de",
    "sou o", "sou a", "eu sou o", "eu sou a",
]

PALAVRAS_NAO_NOME = {
    "castor", "robo", "robô", "amigo", "amiga", "menino", "menina",
    "crianca", "criança", "eu", "voce", "você", "ele", "ela",
}

PIADAS = [
    "Por que o livro foi ao médico? Porque estava com dor de cabeça!",
    "O que o zero disse para o oito? Que cinto bonito!",
    "Por que o esqueleto não briga? Porque não tem estômago pra isso!",
    "O que o mar disse para a praia? Nada, só deu uma onda!",
    "Por que o computador foi ao médico? Porque estava com vírus!",
    "O que o pato disse para a pata? Vem quá!",
    "Por que a abelha não vai à escola? Porque ela já é uma abelhinha!",
]

SENTIMENTOS = [
    (("triste", "tristeza", "chateado", "chateada", "chorar", "chorando",
      "sozinho", "sozinha"),
     "Que pena! Vamos brincar juntos para animar?"),
    (("medo", "assustado", "assustada", "com medo", "pesadelo"),
     "Não precisa ter medo, estou aqui com você!"),
    (("raiva", "bravo", "brava", "nervoso", "nervosa", "irritado", "irritada"),
     "Respira fundo! Quer me contar o que aconteceu?"),
    (("feliz", "alegre", "contente", "animado", "animada", "legal demais"),
     "Que maravilha! Me conta mais!"),
]

_ultima_piada = ""
nome_crianca = ""


def extrair_nome(texto):
    """Pega o nome logo depois de um marcador ('me chamo joao' -> 'Joao')."""
    baixo = texto.lower()
    for marcador in MARCADORES_NOME:
        if marcador in baixo:
            depois = baixo.split(marcador, 1)[1].strip()
            if not depois:
                continue
            candidato = depois.split()[0].strip(".,!?;:")
            if candidato and candidato not in PALAVRAS_NAO_NOME and len(candidato) > 1:
                return candidato.capitalize()
    return ""


def sortear_piada():
    global _ultima_piada
    opcoes = [p for p in PIADAS if p != _ultima_piada]
    escolha = random.choice(opcoes if opcoes else PIADAS)
    _ultima_piada = escolha
    return escolha


def resposta_deterministica(texto, contexto):
    """
    Devolve a resposta pronta quando o contexto já a define,
    ou None quando a conversa precisa mesmo do LLM.
    """
    global nome_crianca
    baixo = texto.lower()

    if contexto == "nome":
        nome = extrair_nome_robusto(texto)
        if nome:
            nome_crianca = nome
            return "Que nome legal, {}! Fico feliz em te conhecer!".format(nome)
        return None

    if contexto == "psicologa":
        return redirecionar()

    if contexto == "sentimento":
        for chaves, resposta in SENTIMENTOS:
            if any(c in baixo for c in chaves):
                return resposta
        return None

    if contexto == "piada":
        return sortear_piada()

    # Demais contextos: template com variação, se existir
    # --- bancos de resposta ---------------------------------------
    # Persona: perguntas sobre o proprio Castor (fato fixo, frase varia).
    # Banco:   so responde se o contexto for um arquivo de respostas/.
    # Se nenhum casar, cai no template de sempre logo abaixo.
    # Ofensa ao Castor: responde calmo e segue.
    _xing = bancos.resposta_xingamento(texto)
    if _xing:
        print("  [XINGAMENTO] resposta calma")
        return _xing

    # Nao sabe o que falar: sugere assunto em vez de devolver pergunta.
    _ajuda = bancos.resposta_nao_sabe(texto)
    if _ajuda:
        print("  [AJUDA] sugere assunto")
        return _ajuda

    # Sequencia sobre o proprio Castor: cada pergunta traz um item novo.
    _sobre = bancos.resposta_sobre_castor(texto)
    if _sobre:
        print("  [SOBRE] sequencia sobre o Castor")
        return _sobre

    # Identidade dita sem sofrimento: acolhe e nao encaminha.
    # Sofrimento explicito ja foi pego pela camada de seguranca acima.
    _identidade = bancos.resposta_identidade(texto)
    if _identidade:
        print("  [IDENTIDADE] acolhe sem encaminhar")
        return _identidade

    _persona = bancos.resposta_persona(texto)
    if _persona:
        print("  [PERSONA] pergunta sobre o Castor")
        return _persona
    _nome_banco = bancos.detectar_banco(texto)
    _banco = bancos.resposta_do_banco(_nome_banco, texto)
    if _banco:
        print("  [BANCO] %s" % _nome_banco)
        return _banco
    # ---------------------------------------------------------------
    # Nada casou: acolhe sem interrogar. So cai no template antigo de
    # tempos em tempos, para a conversa nao virar so "entendi".
    _escuta = bancos.resposta_escuta()
    if _escuta:
        print("  [ESCUTA] acolhe sem pergunta")
        return _escuta

    modelo = sortear_template(contexto)
    if modelo:
        if nome_crianca and random.random() < 0.4:
            return "{}, {}".format(nome_crianca, modelo[0].lower() + modelo[1:])
        return modelo

    return None




# ============================================================
# TEMPLATES POR CONTEXTO
# ============================================================
# Respostas prontas com variação, para os contextos que antes
# dependiam do LLM. Mantêm o tempo abaixo do limite perceptual
# de 2,5-3,0 s apontado por Miller et al. (2025).
# ============================================================

TEMPLATES = {
    "brincar": [
        "Que legal! Do que você mais gosta de brincar?",
        "Adoro brincar também! Você brinca com seus amigos?",
        "Que divertido! Me conta como é essa brincadeira!",
        "Eu também queria brincar disso! Qual a parte mais legal?",
        "Que bacana! Você brinca disso todo dia?",
        "Isso parece muito divertido! Quem brinca com você?",
    ],
    "estudos": [
        "Legal! O que você mais gosta na escola?",
        "Que bom! Me conta o que você aprendeu hoje!",
        "A escola tem coisas legais! Qual a sua matéria favorita?",
        "Que interessante! Você gosta da sua professora?",
        "Me conta mais! O que você faz no recreio?",
        "Que legal! Você tem amigos na sua sala?",
    ],
    "padrao": [
        "Me conta uma coisa que você gosta!",
        "Que legal! Me fala mais sobre isso!",
        "Adorei saber! O que mais você gosta de fazer?",
        "Interessante! Me conta outra coisa sobre você!",
        "Que bom conversar com você! O que você gosta de fazer?",
        "Me conta, você prefere brincar, desenhar ou ouvir música?",
    ],
}

_ultimo_template = {}


def sortear_template(contexto):
    """Sorteia um template do contexto, evitando repetir o anterior."""
    opcoes = TEMPLATES.get(contexto)
    if not opcoes:
        return None
    anterior = _ultimo_template.get(contexto, "")
    disponiveis = [t for t in opcoes if t != anterior]
    escolha = random.choice(disponiveis if disponiveis else opcoes)
    _ultimo_template[contexto] = escolha
    return escolha


def limpar_repeticoes(texto):
    """'vitoria vitoria vitoria chamo' -> 'vitoria chamo'."""
    palavras = texto.split()
    limpo = []
    for p in palavras:
        if not limpo or p != limpo[-1]:
            limpo.append(p)
    return " ".join(limpo)


def extrair_nome_robusto(texto):
    """
    Procura o nome depois de um marcador. Se não achar, pega a
    palavra mais provável de ser nome na frase (fala picada pelo
    Vosk costuma perder a ordem).
    """
    texto = limpar_repeticoes(texto.lower())

    # 1) depois de um marcador
    for marcador in MARCADORES_NOME:
        if marcador in texto:
            depois = texto.split(marcador, 1)[1].strip()
            if depois:
                cand = depois.split()[0].strip(".,!?;:")
                if cand and cand not in PALAVRAS_NAO_NOME and len(cand) > 2:
                    return cand.capitalize()

    # Sem marcador explícito, NAO adivinha.
    # Chamar a criança pelo nome errado é pior que não chamar pelo nome —
    # e com criança autista a correção espontânea nem sempre acontece.
    return ""


# ============================================================
# SISTEMA DE CONTEXTO
# ============================================================

def detectar_contexto(texto: str) -> str:
    texto_lower = texto.lower()
    texto_base = _sem_acento(texto_lower)
    radicais_texto = _radicais(texto_lower)
    # Seguranca e SEMPRE o primeiro teste. Com "nome" na frente, a frase
    # "me chamam de nomes feios" caia no reconhecimento de nome.
    ordem = ["psicologa", "nome", "sentimento", "estudos", "piada", "brincar", "padrao"]

    for nome_contexto in ordem:
        if nome_contexto == "padrao":
            return "padrao"
        palavras = CONTEXTOS[nome_contexto]["palavras"]
        # Compara com e sem acento: se a transcricao perder um acento, a
        # camada de seguranca nao pode falhar em silencio.
        # Tres formas de casar, da mais literal para a mais tolerante.
        # Nenhuma substitui a anterior: sao camadas.
        if any(palavra in texto_lower or _sem_acento(palavra) in texto_base
               or _contem_radical(radicais_texto, palavra)
               for palavra in palavras):
            return nome_contexto

    return "padrao"


def carregar_prompt_contexto(nome_contexto: str) -> str:
    base = ""
    if os.path.exists(CAMINHO_BASE):
        with open(CAMINHO_BASE, "r", encoding="utf-8") as f:
            base = f.read()
    else:
        base = INSTRUCAO_PADRAO

    arquivo = CONTEXTOS[nome_contexto]["arquivo"]
    caminho = os.path.join(PASTA_CONTEXTOS, arquivo)

    if os.path.exists(caminho):
        with open(caminho, "r", encoding="utf-8") as f:
            contexto = f.read()
        return f"{base}\n\n{contexto}"

    return base


def extrair_nome_do_historico() -> str:
    padroes = [
        r"me chamo (\w+)",
        r"meu nome [eé] (\w+)",
        r"pode me chamar de (\w+)",
        r"pode chamar de (\w+)",
        r"me chamam de (\w+)",
    ]
    for msg in historico:
        if msg["role"] == "user":
            texto = msg["content"].lower()
            for padrao in padroes:
                match = re.search(padrao, texto)
                if match:
                    return match.group(1).capitalize()
    return None


def similaridade(a: str, b: str) -> float:
    """Retorna similaridade entre duas strings (0.0 a 1.0)."""
    if not a or not b:
        return 0.0
    return difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio()


def gerar_mudanca_assunto() -> str:
    """
    Chama o Ollama com contexto padrao e alta temperatura
    para gerar uma pergunta completamente diferente.
    """
    prompt_padrao = carregar_prompt_contexto("padrao")
    try:
        r = requests.post(URL_OLLAMA, json={
            "model": MODELO,
            "messages": [
                {"role": "system", "content": prompt_padrao},
                {"role": "user", "content": "pergunta algo diferente e divertido sobre um tema novo"}
            ],
            "stream": False,
            "temperature": 0.95,
            "top_p": 0.9,
        }, timeout=30)
        novo = limpar_resposta(r.json()["choices"][0]["message"]["content"])
        return novo if novo else None
    except Exception:
        return None


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def frase_valida(texto: str) -> bool:
    if not texto or not texto.strip():
        return False
    if len(texto.strip().split()) < MIN_PALAVRAS:
        return False
    return True


def tem_wake_word(texto: str) -> bool:
    return WAKE_WORD in texto.lower()


def limpar_wake_word(texto: str) -> str:
    return texto.lower().replace(WAKE_WORD, "").strip()


def limpar_resposta(texto: str) -> str:
    texto = re.sub(r'<think>.*?</think>', '', texto, flags=re.DOTALL).strip()
    texto = re.sub(r'\*{1,2}(.*?)\*{1,2}', r'\1', texto)
    texto = re.sub(r'[^\w\s\.,!?;:\-\(\)àáâãéêíóôõúüçÀÁÂÃÉÊÍÓÔÕÚÜÇ]', '', texto).strip()
    return texto


# Memória da conversa
historico      = []
ultima_resposta = ""


# ============================================================
# FUNÇÃO PRINCIPAL
# ============================================================

def processar_interacao(mensagem: str, usar_wake_word: bool = False) -> str:
    """
    Recebe o texto transcrito pelo Vosk e retorna a resposta do CASTOR.
    Detecta o contexto automaticamente e carrega o prompt adequado.
    Usa difflib para detectar respostas repetidas e gera mudança de assunto.
    """
    global historico, ultima_resposta

    if not frase_valida(mensagem):
        return None

    if usar_wake_word and not tem_wake_word(mensagem):
        return None

    mensagem_limpa = limpar_wake_word(mensagem) if usar_wake_word else mensagem

    # Filtro de segurança
    resposta_seguranca = verificar_seguranca(mensagem_limpa)
    if resposta_seguranca:
        return resposta_seguranca

    # Detecção direta de perguntas sobre o próprio nome
    texto_lower = mensagem_limpa.lower()
    if any(p in texto_lower for p in PERGUNTAS_NOME_PROPRIO):
        nome = extrair_nome_do_historico()
        if nome:
            return f"Claro! Você me disse que se chama {nome}!"
        else:
            return "Ainda não me contou seu nome! Como posso te chamar?"

    # "meu nome é" sem nada depois — Vosk cortou
    if "meu nome é" in texto_lower:
        partes = texto_lower.split("meu nome é")
        if not partes[-1].strip():
            return "Não entendi! Pode me dizer seu nome de novo?"
        contexto = "nome"
        prompt   = carregar_prompt_contexto(contexto)
    else:
        contexto = detectar_contexto(mensagem_limpa)
        prompt   = carregar_prompt_contexto(contexto)

    # Resposta pronta? Não gasta o LLM.
    direta = resposta_deterministica(mensagem_limpa, contexto)
    if direta:
        print("  [DIRETA] contexto '{}' respondido sem LLM".format(contexto))
        ultima_resposta = direta
        historico.append({"role": "user", "content": mensagem_limpa})
        historico.append({"role": "assistant", "content": direta})
        return direta

    # Monta histórico
    mensagens = [{"role": "system", "content": prompt}]
    historico.append({"role": "user", "content": mensagem_limpa})
    if len(historico) > MAX_HISTORICO:
        historico = historico[-MAX_HISTORICO:]
    mensagens += historico

    try:
        resposta = requests.post(
            URL_OLLAMA,
            json={
                "model": MODELO,
                "messages": mensagens,
                "stream": False,
                "temperature": TEMPERATURA,
                "top_p": TOP_P,
                "max_tokens": 80,
                "cache_prompt": True,
                "repeat_penalty": 1.1,
                "top_k": 20,
            },
            timeout=150
        )
        dados = resposta.json()

        if "choices" not in dados or not dados["choices"]:
            print(f"  [ERRO llama-server] Resposta inesperada: {dados}")
            return "Tive um probleminha aqui..."

        texto = limpar_resposta(dados["choices"][0]["message"]["content"])

        if not texto:
            return "Pode repetir? Não entendi bem!"

        # Detecta repetição usando difflib — mais preciso que comparação exata
        if ultima_resposta and similaridade(texto, ultima_resposta) >= LIMIAR_REPETICAO:
            novo = gerar_mudanca_assunto()
            if novo and similaridade(novo, ultima_resposta) < LIMIAR_REPETICAO:
                texto = novo

        texto, motivo = validar_resposta(texto, contexto)
        if motivo:
            print("  [VALIDADOR] resposta rejeitada ({}) — usando frase segura".format(motivo))

        ultima_resposta = texto
        historico.append({"role": "assistant", "content": texto})
        return texto

    except requests.exceptions.ConnectionError:
        return "Estou com problema de conexão. O Ollama está rodando?"
    except requests.exceptions.Timeout:
        return "Demorei demais para pensar. Pode repetir?"
    except Exception as e:
        print(f"  [ERRO] {type(e).__name__}: {e}")
        return "Tive um probleminha, pode repetir?"


def resetar_historico():
    """Limpa a memória — usar ao iniciar nova sessão."""
    global historico, ultima_resposta
    historico       = []
    ultima_resposta = ""
    print("  Histórico resetado — nova sessão iniciada.")


# ============================================================
# TESTE MANUAL
# ============================================================

if __name__ == "__main__":
    print("=== Teste do módulo interaction ===")
    print(f"Modelo : {MODELO}\n")

    testes = [
        "oi",
        "me chamo vix",
        "qual meu nome",
        "gosto de cachorro",
        "estou triste",
        "meus pais brigam muito",
        "você lembra meu nome",
    ]

    for frase in testes:
        contexto = detectar_contexto(frase)
        resposta = processar_interacao(frase)
        print(f"[{contexto}] '{frase}'")
        print(f"  Castor: {resposta}\n")


def _radicais(texto):
    """Cada palavra vira um CONJUNTO de formas possiveis.

    Tres fontes, somadas: a palavra como veio, o lema do simplemma e o
    corte na regua. Basta uma coincidir. O lema erra as vezes
    (amiga -> amigar) e a regua cobre; a regua e grosseira e o lema cobre.
    """
    t = _sem_dimin_txt(texto.lower())
    saida = []
    for p in _re_mod.findall(r"\w+", t):
        base = _sem_acento(p)
        lema = ""
        if _TEM_LEMA:
            try:
                lema = _sem_acento(_simplemma.lemmatize(p, lang="pt").lower())
            except Exception:
                lema = ""
        # As TRES formas sempre: literal, lema e regua.
        # Dispensar a regua quando o lema muda parecia limpo, mas o lema
        # erra as vezes ("amiga" vira "amigar") e ai nada casa com
        # "amigos". A colisao conta/conto, que motivou tirar a regua, ja
        # e resolvida pela lista de palavras ambiguas acima.
        formas = set([base, _regua(base)])
        if lema:
            formas.add(lema)
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

def _sem_dimin_txt(t):
    return _DIMIN_RE.sub(lambda m: m.group(1) + m.group(2), t)
