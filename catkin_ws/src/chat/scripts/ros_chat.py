#!/usr/bin/env python3
# ============================================================
# Nó ROS — Chat
# ============================================================
# PROJETO: CASTOR — LabTEL/UFES
# PESQUISADORA: Vitória Gomes Fagundes
#
# Recebe o texto do Vosk em /microphone e publica a resposta
# em /chat_output.
#
# TURN-TAKING ACESSÍVEL
#   O Vosk entrega a fala em pedaços. Crianças com TEA muitas
#   vezes falam em fragmentos curtos, então nada é descartado
#   por ser curto: os pedaços são acumulados e a resposta sai
#   quando uma destas condições acontece:
#     - algum pedaço casa com palavra-chave de contexto
#     - o acumulado atinge o tamanho mínimo de frase
#     - já se juntaram vários pedaços curtos
#     - passou tempo demais acumulando (aí o Castor convida a
#       criança a falar, sem chamar o LLM)
#   Só é descartada palavra de função isolada (o, a, um, de),
#   que é o que o Vosk devolve para ruído.
#
# ESTADOS (controlados pela interface web via /chat_estado)
#   ativo   — transcreve e responde
#   standby — transcreve sem responder (botão pausar)
#
# SAÍDA EM DISCO
#   ../sessoes/sessao-DD-MM-AAAA/NN/transcricao.txt
# ============================================================

import os
import time
import random
from datetime import datetime

import rospy
from std_msgs.msg import String

from interaction import processar_interacao, resetar_historico, CONTEXTOS


# ============================================================
# CONFIGURAÇÃO
# ============================================================

PASTA_ATUAL   = os.path.dirname(os.path.abspath(__file__))
PASTA_SESSOES = os.path.join(PASTA_ATUAL, "..", "sessoes")

PALAVRAS_STANDBY = ("standby", "pausar", "pausa", "inactivo", "inativo")
PALAVRAS_ATIVO   = ("ativo", "activo", "retomar", "continuar")

# --- Resolucao de identidade ---
# Varias fontes podem dizer com quem o Castor esta falando.
# Uma fonte menos confiavel nunca sobrescreve uma mais confiavel.
# --- Modo de gravacao ---
#   sessao        -> grava a transcricao (atendimento com consentimento)
#   demonstracao  -> nao grava nada (feira, espaco publico)
# O robo se comporta igual nos dois; muda so o registro em disco.
GRAVANDO = True

PALAVRAS_DEMO   = ("demonstracao", "demonstração", "demo", "feira", "off")
PALAVRAS_SESSAO = ("sessao", "sessão", "gravar", "on")

PRIORIDADE_FONTE = {
    "tela":   3,   # terapeuta selecionou o paciente
    "camera": 2,   # reconhecimento facial
    "voz":    1,   # a crianca disse o nome
}

# --- turn-taking ---
TEMPO_FIM_FALA     = 0.6   # o Vosk ja espera silencio; nao repetir a espera
TEMPO_MAX_ACUMULO  = 8.0   # tempo juntando pedaços antes de convidar a falar
MIN_PALAVRAS_FRASE = 2     # a partir daqui já vale como frase
MAX_FRAGMENTOS     = 4     # vários pedaços curtos também valem como frase

# Palavras de função: sozinhas não carregam significado.
# É o que o Vosk costuma devolver para ruído e respiração.
RUIDO = {
    "o", "a", "e", "é", "um", "uma", "uns", "umas",
    "de", "da", "do", "das", "dos", "que", "com", "em",
    "no", "na", "nos", "nas", "os", "as", "ao", "à",
    "se", "por", "para", "pra", "mas", "ou",
}

# Frases usadas quando a criança falou pouco e nada casou.
# Convidam para um tema conhecido, sem custo de LLM.
FRASES_INCENTIVO = [
    "Oi! Eu sou o Castor. Como você se chama?",
    "Me conta, você gosta de brincar?",
    "Quer ouvir uma piada?",
    "Você tem algum bichinho de estimação?",
    "Qual é a sua cor favorita?",
    "O que você mais gosta de fazer?",
    "Você gosta de música?",
    "Me conta uma coisa legal que você fez hoje!",
]


# Saudações de abertura (portadas do main.py do projeto castor-nlp).
# Tocam quando o robô liga, sem passar pelo LLM.
FRASES_BOAS_VINDAS = [
    "Oi! Sou o Castor! Como você gostaria de ser chamado?",
    "Olá! Eu sou o Castor! Qual é o seu nome?",
    "Oi! Que bom te ver! Como posso te chamar?",
    "Olá! Sou o Castor, um robô amigo! Me conta seu nome!",
    "Oi! Adoro fazer amizades! Como você se chama?",
    "Oi! Que alegria! Como você gostaria de ser chamado?",
    "Olá! Sou o Castor! Qual é o seu nome especial?",
    "Oi! Estou animado pra te conhecer! Como você se chama?",
    "Olá! Sou o Castor! Me conta como você quer ser chamado!",
    "Oi! Que legal você estar aqui! Como posso te chamar?",
    "Olá! Eu adoro fazer amigos! Qual é o seu nome?",
    "Oi! Sou o Castor e estou muito feliz! Como você se chama?",
    "Olá! Que dia especial! Como você gostaria de ser chamado?",
    "Oi! Vamos ser amigos! Como eu posso te chamar?",
    "Olá! Sou o Castor, do labtel da ufes! Qual é o seu nome?",
    "Oi! Que maravilha você estar aqui! Como você se chama?",
    "Olá! Adoro quando me chamam! Como você gostaria de ser chamado?",
    "Oi! Você sabia que adoro conhecer gente nova? Qual é o seu nome?",
    "Olá! Sou o Castor! Pode me contar seu nome?",
    "Oi! Chegou alguém novo! Como você se chama?",
    "Olá! Eu sou o Castor e hoje acordei animado! Qual é o seu nome?",
    "Oi! Meu nome é Castor. E o seu, qual é?",
    "Olá! Que bom que você veio! Me conta seu nome!",
    "Oi! Eu estava esperando alguém pra conversar! Como você se chama?",
    "Olá! Sou o Castor, seu novo amigo! Qual é o seu nome?",
    "Oi! Adoro conhecer pessoas! Como posso te chamar?",
    "Olá! Hoje é um bom dia pra fazer amizade! Qual é o seu nome?",
    "Oi! Eu sou o Castor. Quer ser meu amigo? Como você se chama?",
    "Olá! Que legal ter alguém aqui comigo! Me diz seu nome!",
    "Oi! Sou um robô e adoro conversar! Qual é o seu nome?",
    "Olá! Fiquei feliz quando você chegou! Como você se chama?",
    "Oi! Vamos nos conhecer? Eu sou o Castor. E você?",
    "Olá! Estou pronto pra brincar! Antes, me conta seu nome!",
    "Oi! Você chegou! Como você gosta de ser chamado?",
    "Olá! Que alegria te ver aqui! Me conta como você se chama!",
    "Oi! Eu adoro nomes novos! Qual é o seu?",
    "Olá! Sou o Castor e quero muito te conhecer! Como você se chama?",
    "Oi! Chegou a hora de fazer um amigo novo! Qual é o seu nome?",
    "Olá! Meu dia melhorou agora! Qual é o seu nome?",
]


# Guarda qual saudação foi usada por último, para não repetir
# na sessão seguinte. Persiste em disco, então sobrevive a
# desligar o robô.
ARQUIVO_ULTIMA_SAUDACAO = os.path.join(PASTA_ATUAL, "..", ".ultima_saudacao")


def escolher_saudacao():
    anterior = ""
    try:
        with open(ARQUIVO_ULTIMA_SAUDACAO, encoding="utf-8") as f:
            anterior = f.read().strip()
    except Exception:
        pass

    opcoes = [f for f in FRASES_BOAS_VINDAS if f != anterior]
    escolha = random.choice(opcoes if opcoes else FRASES_BOAS_VINDAS)

    try:
        with open(ARQUIVO_ULTIMA_SAUDACAO, "w", encoding="utf-8") as f:
            f.write(escolha)
    except Exception:
        pass

    return escolha


# Todas as palavras-chave dos contextos, para decidir se um
# pedaço curto já é suficiente para responder.
PALAVRAS_CONTEXTO = set()
for _ctx in CONTEXTOS.values():
    for _p in _ctx.get("palavras", []):
        PALAVRAS_CONTEXTO.add(_p.lower())


# ============================================================
# SESSÃO
# ============================================================

def criar_pasta_sessao():
    os.makedirs(PASTA_SESSOES, exist_ok=True)
    data_hoje = datetime.now().strftime("%d-%m-%Y")
    pasta_dia = os.path.join(PASTA_SESSOES, "sessao-{}".format(data_hoje))
    os.makedirs(pasta_dia, exist_ok=True)

    contador = 1
    while True:
        caminho = os.path.join(pasta_dia, "{:02d}".format(contador))
        if not os.path.exists(caminho):
            os.makedirs(caminho)
            break
        contador += 1

    return caminho, os.path.join(caminho, "transcricao.txt")


def iniciar_transcricao(caminho_txt, modo="voz (ROS)"):
    with open(caminho_txt, "w", encoding="utf-8") as f:
        f.write("=" * 60 + "\n")
        f.write("TRANSCRICAO DE SESSAO — CASTOR / labtel / ufes\n")
        f.write("=" * 60 + "\n")
        f.write("Data/Hora : {}\n".format(datetime.now().strftime("%d/%m/%Y %H:%M:%S")))
        f.write("Modo      : {}\n".format(modo.upper()))
        f.write("=" * 60 + "\n\n")


def salvar_turno(caminho_txt, quem, texto):
    if not GRAVANDO:
        return
    hora = datetime.now().strftime("%H:%M:%S")
    with open(caminho_txt, "a", encoding="utf-8") as f:
        f.write("[{}] {}: {}\n".format(hora, quem, texto))


def finalizar_transcricao(caminho_txt, metricas):
    with open(caminho_txt, "a", encoding="utf-8") as f:
        f.write("\n" + "=" * 60 + "\n")
        f.write("Fim da sessao: {}\n".format(datetime.now().strftime("%H:%M:%S")))
        f.write("-" * 60 + "\n")
        f.write("Falas processadas    : {}\n".format(metricas["total"]))
        f.write("Respondidas pelo LLM : {}\n".format(metricas["llm"]))
        f.write("Frases de incentivo  : {}\n".format(metricas["incentivo"]))
        f.write("Ruido descartado     : {}\n".format(metricas["ruido"]))
        f.write("=" * 60 + "\n")


# ============================================================
# NÓ
# ============================================================

class NodoChat(object):

    def __init__(self, nome):
        self.nome = nome
        rospy.init_node(self.nome)
        self.rate = rospy.Rate(10)
        self._inicializar_subscribers()
        self._inicializar_publishers()
        self._inicializar_variaveis()

        self.pasta_sessao, self.caminho_txt = criar_pasta_sessao()
        iniciar_transcricao(self.caminho_txt)
        rospy.loginfo("[%s] Sessão salva em: %s", self.nome, self.pasta_sessao)
        rospy.on_shutdown(self._ao_encerrar)

        resetar_historico()
        rospy.loginfo("[%s] Histórico resetado — nova sessão iniciada.", self.nome)

    def _inicializar_subscribers(self):
        rospy.Subscriber('/microphone', String, self.callback_microphone)
        rospy.Subscriber('/chat_estado', String, self.callback_estado)
        # Publicado pelo no de reconhecimento facial, quando disponivel.
        # Enquanto ninguem publicar, nada acontece.
        rospy.Subscriber('/pessoa_reconhecida', String, self.callback_pessoa)
        # Publicado pela tela quando a terapeuta seleciona o paciente.
        rospy.Subscriber('/chat_paciente', String, self.callback_paciente)
        # Liga/desliga a gravacao da transcricao.
        rospy.Subscriber('/chat_gravacao', String, self.callback_gravacao)

    def _inicializar_publishers(self):
        self.pub_chat_output = rospy.Publisher('/chat_output', String, queue_size=10)

    def _inicializar_variaveis(self):
        self.estado          = "ativo"
        self.fragmentos      = []
        self.ultimo_em       = None
        self.inicio_acumulo  = None
        self.ultimo_incentivo = ""
        self.pessoa_atual     = ""
        self.fonte_nome       = ""
        self.ja_cumprimentou  = False
        self.metricas = {"total": 0, "llm": 0, "incentivo": 0, "ruido": 0}

    # ============================================================
    # CALLBACKS
    # ============================================================

    def callback_microphone(self, msg):
        pedaco = msg.data.lower().strip()
        if not pedaco:
            return

        # descarta apenas palavra de função isolada (ruído do Vosk)
        if len(pedaco.split()) == 1 and pedaco in RUIDO:
            self.metricas["ruido"] += 1
            rospy.loginfo("[%s] ruido descartado: '%s'", self.nome, pedaco)
            return

        if not self.fragmentos:
            self.inicio_acumulo = time.time()
        self.fragmentos.append(pedaco)
        self.ultimo_em = time.time()



    def definir_pessoa(self, nome, fonte):
        """
        Registra com quem o Castor esta falando.
        So aceita se a fonte for igual ou mais confiavel que a atual.
        Devolve True se o nome mudou.
        """
        nome = (nome or "").strip()
        if not nome:
            return False

        peso_novo  = PRIORIDADE_FONTE.get(fonte, 0)
        peso_atual = PRIORIDADE_FONTE.get(self.fonte_nome, 0)

        if self.pessoa_atual and peso_novo < peso_atual:
            rospy.loginfo("[%s] ignorando '%s' (%s) — '%s' (%s) e mais confiavel",
                          self.nome, nome, fonte, self.pessoa_atual, self.fonte_nome)
            return False

        if nome == self.pessoa_atual:
            return False

        self.pessoa_atual = nome
        self.fonte_nome   = fonte

        try:
            import interaction
            interaction.nome_crianca    = nome
            interaction.aguardando_nome = False
        except Exception as e:
            rospy.logwarn("[%s] nao consegui fixar o nome: %s", self.nome, str(e))

        rospy.loginfo("[%s] Falando com: %s (fonte: %s)", self.nome, nome, fonte)
        salvar_turno(self.caminho_txt, "Sistema",
                     "identidade definida: {} (fonte: {})".format(nome, fonte))
        return True


    def callback_gravacao(self, msg):
        """Alterna entre modo sessao (grava) e demonstracao (nao grava)."""
        global GRAVANDO
        valor = msg.data.lower().strip()

        if valor in PALAVRAS_DEMO:
            novo = False
        elif valor in PALAVRAS_SESSAO:
            novo = True
        else:
            rospy.logwarn("[%s] Modo de gravacao desconhecido: '%s'",
                          self.nome, msg.data)
            return

        if novo == GRAVANDO:
            return

        if not novo:
            salvar_turno(self.caminho_txt, "Sistema",
                         "gravacao desligada - modo demonstracao")
        GRAVANDO = novo
        if novo:
            salvar_turno(self.caminho_txt, "Sistema",
                         "gravacao ligada - modo sessao")

        rospy.loginfo("[%s] Modo: %s", self.nome,
                      "sessao (gravando)" if novo else "demonstracao (sem gravar)")

    def callback_paciente(self, msg):
        """Paciente selecionado na tela pela terapeuta."""
        self.definir_pessoa(msg.data, "tela")

    def callback_pessoa(self, msg):
        """
        Nome vindo do reconhecimento facial. Tem prioridade sobre o
        nome dito por voz, porque nao depende do reconhecimento de fala.
        O no da camera ja cumprimenta sozinho, entao aqui nao repetimos
        a saudacao — so registramos quem chegou.
        """
        if self.definir_pessoa(msg.data, "camera"):
            # o no da camera ja cumprimenta sozinho
            self.ja_cumprimentou = True

    def callback_estado(self, msg):
        valor = msg.data.lower().strip()
        if valor in PALAVRAS_STANDBY:
            novo = "standby"
        elif valor in PALAVRAS_ATIVO:
            novo = "ativo"
        else:
            rospy.logwarn("[%s] Estado desconhecido: '%s'", self.nome, msg.data)
            return

        if novo == self.estado:
            return

        self.estado = novo
        if novo == "standby":
            rospy.loginfo("[%s] >>> PAUSADO — gravando sem responder", self.nome)
            salvar_turno(self.caminho_txt, "Sistema", "sessao pausada")
        else:
            rospy.loginfo("[%s] >>> ATIVO — respondendo", self.nome)
            salvar_turno(self.caminho_txt, "Sistema", "sessao retomada")

    # ============================================================
    # DECISÃO
    # ============================================================

    def _casa_contexto(self, frase):
        """True se a frase contém alguma palavra-chave dos contextos."""
        return any(p in frase for p in PALAVRAS_CONTEXTO)

    def _escolher_incentivo(self):
        """Sorteia uma frase de incentivo diferente da anterior."""
        opcoes = [f for f in FRASES_INCENTIVO if f != self.ultimo_incentivo]
        escolha = random.choice(opcoes if opcoes else FRASES_INCENTIVO)
        self.ultimo_incentivo = escolha
        return escolha

    def _limpar_acumulo(self):
        self.fragmentos     = []
        self.ultimo_em      = None
        self.inicio_acumulo = None

    # ============================================================
    # RESPOSTA
    # ============================================================

    def _responder_com_llm(self, frase):
        rospy.loginfo("[%s] Usuário disse: %s", self.nome, frase)
        salvar_turno(self.caminho_txt, "Crianca", frase)

        inicio   = time.time()
        resposta = processar_interacao(frase)
        duracao  = time.time() - inicio

        if resposta:
            rospy.loginfo("[%s] Castor responde: %s  (%.1fs)",
                          self.nome, resposta, duracao)
            self.pub_chat_output.publish(resposta)
            salvar_turno(self.caminho_txt, "Castor", resposta)
            salvar_turno(self.caminho_txt, "Sistema",
                         "tempo de resposta: {:.1f}s".format(duracao))
        self.metricas["llm"] += 1

    def _responder_com_incentivo(self, frase):
        """Criança falou pouco: convida a falar, sem custo de LLM."""
        if frase:
            salvar_turno(self.caminho_txt, "Crianca", frase)
        resposta = self._escolher_incentivo()
        rospy.loginfo("[%s] Castor convida: %s  (instantaneo)", self.nome, resposta)
        self.pub_chat_output.publish(resposta)
        salvar_turno(self.caminho_txt, "Castor", resposta)
        salvar_turno(self.caminho_txt, "Sistema", "resposta de incentivo (sem LLM)")
        self.metricas["incentivo"] += 1

    # ============================================================
    # ENCERRAMENTO
    # ============================================================

    def _ao_encerrar(self):
        if not GRAVANDO:
            # modo demonstracao: nao deixa pasta vazia para tras
            try:
                if os.path.exists(self.caminho_txt):
                    os.remove(self.caminho_txt)
                os.rmdir(self.pasta_sessao)
                rospy.loginfo("[%s] Modo demonstracao - sessao nao gravada", self.nome)
            except Exception:
                pass
            return

        finalizar_transcricao(self.caminho_txt, self.metricas)
        rospy.loginfo("[%s] Transcrição salva em: %s", self.nome, self.caminho_txt)

    # ============================================================
    # LOOP PRINCIPAL
    # ============================================================

    def main(self):
        rospy.loginfo("[%s] Nó chat iniciado com sucesso! (estado: %s)",
                      self.nome, self.estado)

        # Saudação de abertura — instantânea, sem LLM.
        # Dá tempo do TTS e do speaker se conectarem ao tópico.
        # Espera o TTS realmente assinar o topico antes de falar.
        # Publicar antes disso faz a mensagem cair no vazio.
        espera = 0.0
        while (self.pub_chat_output.get_num_connections() == 0
               and espera < 20.0 and not rospy.is_shutdown()):
            rospy.sleep(0.5)
            espera += 0.5
        rospy.loginfo("[%s] TTS conectado em %.1fs", self.nome, espera)
        rospy.sleep(1.0)

        if self.ja_cumprimentou:
            rospy.loginfo("[%s] Camera ja cumprimentou %s — pulando saudacao",
                          self.nome, self.pessoa_atual)
            return

        saudacao = escolher_saudacao()
        rospy.loginfo("[%s] Castor se apresenta: %s", self.nome, saudacao)
        self.pub_chat_output.publish(saudacao)
        salvar_turno(self.caminho_txt, "Castor", saudacao)
        salvar_turno(self.caminho_txt, "Sistema", "saudacao de abertura (sem LLM)")

        while not rospy.is_shutdown():

            if self.fragmentos and self.ultimo_em is not None:
                agora    = time.time()
                silencio = (agora - self.ultimo_em) >= TEMPO_FIM_FALA
                esperou  = (agora - self.inicio_acumulo) >= TEMPO_MAX_ACUMULO

                if silencio or esperou:
                    frase = " ".join(self.fragmentos).strip()

                    if self.estado == "standby":
                        rospy.loginfo("[%s] [standby] %s", self.nome, frase)
                        salvar_turno(self.caminho_txt, "[standby]", frase)
                        self._limpar_acumulo()
                    else:
                        pronto = (self._casa_contexto(frase)
                                  or len(frase.split()) >= MIN_PALAVRAS_FRASE
                                  or len(self.fragmentos) >= MAX_FRAGMENTOS)

                        if pronto:
                            self.metricas["total"] += 1
                            self._limpar_acumulo()
                            self._responder_com_llm(frase)
                        elif esperou:
                            self.metricas["total"] += 1
                            self._limpar_acumulo()
                            self._responder_com_incentivo(frase)
                        else:
                            # ainda não dá para responder: segue acumulando
                            self.ultimo_em = None

            rospy.sleep(0.1)


if __name__ == '__main__':
    NodoChat('chat').main()
