#!/usr/bin/env python3


import time
import subprocess
import json
import unicodedata
import random

import rospy
import os
from datetime import datetime
from flask import Flask, jsonify, redirect, render_template, request, session, url_for

import rps_camera  # adicionado por Adryan

from acciones import Acciones
from get_activities import get_activities
from activity9 import Activity9
from activity9_voice import Activity9Voice

from std_msgs.msg import String


######################################
################ ROS #################
######################################

rospy.init_node('mainMenuHTML', disable_signals=True)

######################################
############# PUBLISHERS #############
######################################

pubEmotions = rospy.Publisher('/emotions', String, queue_size = 10)
pubSpeaker = rospy.Publisher('/speaker', String, queue_size = 10)
pubSpeakerAction = rospy.Publisher('/speakerAction', String, queue_size = 15)
pubMovements = rospy.Publisher('/movements', String, queue_size = 5)
pubCastorSystem = rospy.Publisher('/castor_system', String, queue_size = 5)
pubMicrophone = rospy.Publisher('/mic', String, queue_size = 5)
pubRecord     = rospy.Publisher('/record_data', String, queue_size = 5)
pubChatEstado = rospy.Publisher('/chat_estado', String, queue_size = 5)
#pubText = rospy.Publisher('/microphone', String, queue_size = 5)
pubFaceRegistration = rospy.Publisher(
    '/face_registration/request',
    String,
    queue_size=1,
)

face_registration_status = {
    "state": "starting",
    "message": "Aguardando o reconhecimento facial.",
    "name": "",
}


def callbackFaceRegistrationStatus(message):
    global face_registration_status

    try:
        face_registration_status = json.loads(
            message.data
        )
    except (TypeError, ValueError) as error:
        rospy.logwarn(
            "Status de cadastro inválido: {}".format(
                error
            )
        )


subFaceRegistrationStatus = rospy.Subscriber(
    "/face_registration/status",
    String,
    callbackFaceRegistrationStatus,
    queue_size=10,
)

### Suscribirme al topic de arriba para mostrar el texto
acciones = Acciones()

text = ""

def callbackText(msg):
    new_text = True
    global text
    text = msg.data
    print(text)
    try:
        with open("/tmp/castor_ultima_fala.txt", "w") as fala:
            fala.write(text)
    except:
        pass
    return

subText = rospy.Subscriber('/chat_output', String, callbackText)


# Texto reconhecido pelo microfone na atividade A8
texto_microfone = ""

def callbackMicrophone(msg):
    global texto_microfone

    texto_recebido = msg.data.strip()

    if texto_recebido == "":
        return

    texto_microfone = texto_recebido


subMicrophone = rospy.Subscriber(
    '/microphone',
    String,
    callbackMicrophone,
    queue_size=10
)


# Frase esperada em cada página da história da banheira.
# Escreva as frases em minúsculo e sem pontuação, do mesmo jeito
# que o reconhecimento de voz costuma publicar.
textos_banheira = {
    1: "a banheira de josé",
    2: "bom é hora de tomar banho",
    3: "o shampoo é para lavar o cabelo",
    4: "a esponja é para lavar o corpo",
    5: "a toalha é para se secar",
    6: "bom jose esta limpo e veste o pijama"
}


def normalizar_palavra(palavra):
    """Normaliza só para comparação, preservando a palavra original na tela."""

    palavra = palavra.lower()

    # Remove acentos: "é" -> "e", "josé" -> "jose".
    palavra = "".join(
        caractere
        for caractere in unicodedata.normalize("NFD", palavra)
        if unicodedata.category(caractere) != "Mn"
    )

    # Remove pontuação, mantendo letras e números.
    palavra = "".join(
        caractere
        for caractere in palavra
        if caractere.isalnum()
    )

    return palavra


def calcular_acerto(texto_falado, texto_esperado):
    """Calcula o percentual de palavras corretas mantendo a ordem."""

    falado = [
        normalizar_palavra(palavra)
        for palavra in texto_falado.split()
    ]

    esperado = [
        normalizar_palavra(palavra)
        for palavra in texto_esperado.split()
    ]

    if len(esperado) == 0:
        return 0.0

    dp = [
        [0] * (len(falado) + 1)
        for _ in range(len(esperado) + 1)
    ]

    for i in range(1, len(esperado) + 1):
        for j in range(1, len(falado) + 1):
            if esperado[i - 1] == falado[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(
                    dp[i - 1][j],
                    dp[i][j - 1]
                )

    palavras_corretas = dp[len(esperado)][len(falado)]

    return (palavras_corretas / len(esperado)) * 100.0


def gerar_feedback_palavras(texto_falado, texto_esperado):
    """Mostra exatamente o que o microfone captou e colore cada palavra."""

    # Estas são as palavras que serão realmente exibidas na tela.
    falado_original = texto_falado.split()

    # Cópias normalizadas usadas SOMENTE para comparar.
    falado = [
        normalizar_palavra(palavra)
        for palavra in falado_original
    ]

    esperado = [
        normalizar_palavra(palavra)
        for palavra in texto_esperado.split()
    ]

    n = len(esperado)
    m = len(falado)

    dp = [
        [0] * (m + 1)
        for _ in range(n + 1)
    ]

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if esperado[i - 1] == falado[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(
                    dp[i - 1][j],
                    dp[i][j - 1]
                )

    # Índices das palavras realmente captadas que fizeram parte
    # da sequência correta.
    palavras_corretas_faladas = set()

    i = n
    j = m

    while i > 0 and j > 0:
        if esperado[i - 1] == falado[j - 1]:
            palavras_corretas_faladas.add(j - 1)
            i -= 1
            j -= 1
        elif dp[i - 1][j] >= dp[i][j - 1]:
            i -= 1
        else:
            j -= 1

    feedback = []

    for indice, palavra_original in enumerate(falado_original):
        feedback.append({
            "word": palavra_original,
            "correct": indice in palavras_corretas_faladas
        })

    return feedback

######################################
############# MAIN MENU ##############
######################################

app = Flask(__name__)
app.secret_key = os.environ.get('CASTOR_FLASK_SECRET_KEY') or os.urandom(32)

pubActivity9 = rospy.Publisher('/activity9/request', String, queue_size=10)
activity9_voice = Activity9Voice(rospy.logerr)
activity9 = Activity9(
    lambda command: pubActivity9.publish(json.dumps(command)),
    pubEmotions.publish,
    activity9_voice.say,
    silence=activity9_voice.cancel,
)
app.register_blueprint(activity9.blueprint)
app.before_request(activity9.navigation_cleanup)
rospy.on_shutdown(activity9.shutdown)


def callbackActivity9Status(message):
    try:
        activity9.receive_status(json.loads(message.data))
    except (TypeError, ValueError) as error:
        rospy.logwarn("Status da atividade 9 inválido: %s", error)


subActivity9Status = rospy.Subscriber(
    '/activity9/status', String, callbackActivity9Status, queue_size=1,
)


# Recarrega os templates HTML sempre que forem alterados
app.config['TEMPLATES_AUTO_RELOAD'] = True

# Evita cache dos arquivos da pasta static (CSS, JS, imagens)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

@app.after_request
def disable_cache(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@app.route("/")
def mainMenu():
	templateData = {
		'title' : 'Main Menu',
	}
	return render_template('mainMenu.html', **templateData)

@app.route("/face_registration", methods=["GET", "POST"])
def faceRegistration():
    templateData = {
        'title': 'Cadastro facial',
    }

    if request.method == "POST":
        name = request.form.get("name", "").strip()

        if not name:
            templateData["face_message"] = "Digite o nome da pessoa."
            templateData["face_message_type"] = "error"
            return render_template(
                "faceRegistration.html",
                **templateData
            ), 400

        if len(name) > 40:
            templateData["face_message"] = (
                "O nome deve ter no máximo 40 caracteres."
            )
            templateData["face_message_type"] = "error"
            return render_template(
                "faceRegistration.html",
                **templateData
            ), 400

        if pubFaceRegistration.get_num_connections() == 0:
            templateData["face_message"] = (
                "O reconhecimento facial não está ativo."
            )
            templateData["face_message_type"] = "error"
            return render_template(
                "faceRegistration.html",
                **templateData
            ), 503

        pubFaceRegistration.publish(name)

        templateData["face_message"] = (
            "Cadastro de {} solicitado. "
            "Aproxime a pessoa da câmera.".format(name)
        )
        templateData["face_message_type"] = "success"

    return render_template(
        "faceRegistration.html",
        **templateData
    )


@app.route("/face_registration/status")
def faceRegistrationStatus():
    return jsonify(face_registration_status)

@app.route("/favicon.ico")
def favicon_vazio():
    """O navegador pede /favicon.ico sozinho a cada pagina aberta. Sem esta
    rota o pedido caia na regra /<action>, que executa acciones.Main_Menu e
    disparava acao no robo a cada navegacao entre telas."""
    return ("", 204)


@app.route("/<action>")
def actionMainMenu(action):
    template = "mainMenu.html"

    acciones.Main_Menu(action = action)

    if action == "Activities":
        if session.pop('a9_game', None) is not None:
            pubEmotions.publish("neutral")
        template = "Actividades.html"
    elif action == "shutdown":
        template = "shutdown.html"
    elif action == "reboot":
        template = "reboot.html"
    elif action == "Text":
        template = "Texto.html"
    elif action == "Pseudoprogramacion":
        template = "Pseudoprogramacion.html"
    elif action == "Terapia":
        template = "Terapia.html"
    elif action == "Ativar":
        pubMicrophone.publish("Activo")
    elif action == "Desativar":
        pubMicrophone.publish("Inactivo")
    elif action == "Vitoria":
        return redirect("/Vitoria/tela")
    
    templateData = {
        'title' : 'Main Menu',
        }
    return render_template(template, **templateData)

#########################################
################ Shutdown ###############
#########################################

@app.route("/shutdown/<action>")
def action1(action):
    if action == "yes":
        pubCastorSystem.publish("shutdown")
        time.sleep(0.5)
        subprocess.call(['sudo', 'shutdown', 'now'], shell=False)
        template = "shutdown.html"
    
    elif action == "no":
        print("no")
        template = "mainMenu.html"

    templateData = {
	 	'title' : 'Shutdown',
	 }
    return render_template(template, **templateData)

#########################################
################ Reboot #################
#########################################

@app.route("/reboot/<action>")
def action2(action):
	if action == "yes":
		pubCastorSystem.publish("reboot")
		time.sleep(0.5)
		subprocess.call(['sudo', 'reboot', 'now'], shell=False)
		template = "reboot.html"
	elif action == "no":
		template = "mainMenu.html"
	templateData = {
		'title' : 'Reboot',
	}
	return render_template(template, **templateData)


##############################################
################# Actividades ################
##############################################

@app.route("/Activities/<action>")
def actionAct(action):
    template = 'Actividades.html'
    if action == "A1":
        template = 'Act1_sargento.html'
    elif action == "A2":
        template = 'Act2_cuenJose.html'
    elif action == "A3":
        template = 'Act3_bailar.html'
    elif action == "A4":
        template = 'Act4_cantar.html'
    elif action == "A5":
        template = 'Act5_cuenNarra.html'
    elif action == "A6":
        template = 'Conversation.html'
    elif action == "A7":
        template = 'ActivitiesHug.html'
    elif action == "A8":
        pubSpeaker.publish("Hora_Da_Leitura")
        template = 'LeiaHistoriaMenu.html'
    elif action == "A9":
        return redirect(url_for('a9.explicar'))
    templateData = {
		'title' : 'Activities',
	}
    return render_template(template, **templateData)

#################################################
##################### Act1 ######################
#################################################
@app.route("/Activities/A1/<action>")
def actionL1_A1(action):
    template = 'Act1_sargento.html'
    
    if action == "songBattle":
        pubSpeaker.publish("o_mestre_mandou")
    elif action == "explain":
        pubSpeaker.publish("siga_instrucoes_mestre")

    # Indications
    acciones.IndicacionesAct1(action=action)
    acciones.Frases_objetivo_alcanzado(action=action)
    acciones.Frases_de_incentivo(action=action)
    acciones.emotions(action=action)
        
    templateData = {
 		'title' : 'A1',
 	}
    return render_template(template, **templateData)

#############################################
##################### Act 2 #################
#############################################

@app.route("/Activities/A2/<action>")
def actionL1_A2(action):
    template = 'Act2_cuenJose.html'
    
    acciones.Frases_objetivo_alcanzado(action=action)
    acciones.Frases_de_incentivo(action=action)
    acciones.emotions(action=action)

    if action == "explain2":
        pubSpeaker.publish("ver_escutar_historia")
    elif action == "explain3":
        pubSpeaker.publish("responder_algumas_perguntas")

    
    if action == "jose1":
        template = 'level3Memory1.html'
    elif action == "jose2":
        template = 'level3Memory2.html'
    elif action == "jose4":
        template = 'level3Memory4.html'
    elif action == "jose5":
        template = 'level3Memory5.html'

    templateData = {
 		'title' : 'A2',
   		}
    return render_template(template, **templateData)

###################################################
################# Act 2 History 1 #################
###################################################
@app.route("/Activities/A2/history1/<action>")
def actionL1_A2_1(action):
    template = 'level3Memory1.html'
    
    acciones.SegmentoAct2_History1(action=action)
    acciones.Reproduction(action=action)
    acciones.QuestionAct2_History1(action=action)
    acciones.Frases_objetivo_alcanzado(action=action)
    acciones.Frases_de_incentivo(action=action)
    acciones.emotions(action=action)

    templateData = {
		'title' : 'A2 History 1',
  		}
    return render_template(template, **templateData)

###################################################
################# Act 2 History 2 #################
###################################################
@app.route("/Activities/A2/history2/<action>")
def actionL2_A2_2(action):
    template = 'level3Memory2.html'
    
    acciones.SegmentoAct2_History2(action=action)
    acciones.Reproduction(action=action)
    acciones.QuestionAct2_History2(action=action)
    acciones.Frases_objetivo_alcanzado(action=action)
    acciones.Frases_de_incentivo(action=action)
    acciones.emotions(action=action)

    templateData = {
 		'title' : 'A2 History 2',
 	}
    return render_template(template, **templateData)

# ###############################################
# ################ Act2 History 4 ###############
# ###############################################
@app.route("/Activities/A2/history4/<action>")
def actionL1_A2_4(action):
    template = 'level3Memory4.html'
    
    acciones.SegmentoAct2_History4(action=action)
    acciones.Reproduction(action=action)
    acciones.QuestionAct2_History4(action=action)
    acciones.Frases_objetivo_alcanzado(action=action)
    acciones.Frases_de_incentivo(action=action)
    acciones.emotions(action=action)
    
    templateData = {
		'title' : 'A3 History 4',
	}
    return render_template(template, **templateData)

################################################
################ Act 2 History 5 ###############
################################################
@app.route("/Activities/A2/history5/<action>")
def actionL1_A2_5(action):
    template = 'level3Memory5.html'
    
    acciones.SegmentoAct2_History5(action=action)
    acciones.Reproduction(action=action)
    acciones.QuestionAct2_History5(action=action)
    acciones.Frases_objetivo_alcanzado(action=action)
    acciones.Frases_de_incentivo(action=action)
    acciones.emotions(action=action)

    templateData = {
		'title' : 'A2 History 5',
	}
    return render_template(template, **templateData)

############################################
################## Act 3 ###################
############################################
@app.route("/Activities/A3/<action>")
def actionL2_A2(action):
    template = 'Act3_bailar.html'
    if action == "explain":
        pubSpeaker.publish("siga_instrucoes")

    acciones.Dance(action=action)
    acciones.Reproduction(action=action)
    acciones.Frases_objetivo_alcanzado(action=action)
    acciones.Frases_de_incentivo(action=action)
    acciones.emotions(action=action)
    
    templateData = {
		'title' : 'A3',
	}
    return render_template(template, **templateData)
	
	
############################################
################## Act 4 ###################
############################################
@app.route("/Activities/A4/<action>")
def actionL2_A4(action):
    template = 'Act4_cantar.html'
    if action == "explain2":
        pubSpeaker.publish("canta_comigo")

    acciones.Songs(action=action)
    acciones.Reproduction(action=action)
    acciones.Frases_objetivo_alcanzado(action=action)
    acciones.Frases_de_incentivo(action=action)
    acciones.emotions(action=action)
    
    templateData = {
		'title' : 'A4',
	}
    return render_template(template, **templateData)

	
############################################
################## Act 5 ###################
############################################
@app.route("/Activities/A5/<action>")
def actionL2_A5(action):
    template = 'Act5_cuenNarra.html'
    if action == "explain":
        pubSpeaker.publish("escutar_historia")		

    acciones.Stories(action=action)
    acciones.Reproduction(action=action)
    acciones.Frases_objetivo_alcanzado(action=action)
    acciones.Frases_de_incentivo(action=action)
    acciones.emotions(action=action)

    templateData = {
		'title' : 'A5',
	}
    return render_template(template, **templateData)

##############################################
############# Act6 Conversacion ##############
##############################################
@app.route("/Activities/A6/<action>")
def Conversacion(action):
    template = "Conversation.html"
    #Bodyparts
    acciones.BodyParts(action=action)
    acciones.emotions(action=action)
	#CastorEmotions
    acciones.CastorEmotions(action=action)
	# #Maths
    acciones.Maths(action=action)
	# #Conversation
    acciones.Conversation(action=action)
    acciones.Frases_objetivo_alcanzado(action=action)
    acciones.Frases_de_incentivo(action=action)

    templateData = {
		'title' : 'Conversation Menu',
	}
    return render_template(template, **templateData)
	
###########################################
################ A7 Action_Hug ############
###########################################
@app.route("/Activities/A7/<action>")
def Hug(action):
    template = "ActivitiesHug.html"
    
    acciones.Hugs(action=action)
    
    templateData = {
		'title' : 'Abrazos',
	}
    return render_template(template, **templateData)


#############################################
##################### Act 8 #################
#############################################

@app.route("/Activities/A8/<action>")
def actionA8(action):
    global texto_microfone

    template = 'LeiaHistoria.html'

    if action == "LeiaHistoriaBanheira":
        # Começa uma nova leitura e liga o microfone.
        texto_microfone = ""
        pubMicrophone.publish("Inactivo")
        pubSpeaker.publish("Vamos_comecar")

        #Timer para ligar o mic
        rospy.Timer(
        rospy.Duration(3.2),
        lambda _: pubMicrophone.publish("Activo"),
        oneshot=True
    )
        template = 'LeiaHistoriaBanheira.html'

    elif action == "LeiaHistoria2":
        template = 'LeiaHistoria2.html'

    elif action == "LeiaHistoria3":
        template = 'LeiaHistoria3.html'

    elif action == "LeiaHistoria4":
        template = 'LeiaHistoria4.html'

    templateData = {
 		'title' : 'A2',
   		}
    return render_template(template, **templateData)

#############################################
##################### Act 8 History 1 #################
#############################################

@app.route("/Activities/A8/banheira/<action>")
def actionA8_H1(action):
    global texto_microfone

    # Ao trocar de página, descarta a frase reconhecida na página anterior.
    texto_microfone = ""

    template = 'LeiaHistoriaBanheira.html'

    if action == "pagina2":
        template = 'LeiaHistoriaBanheira2.html'

    elif action == "pagina3":
        template = 'LeiaHistoriaBanheira3.html'

    elif action == "pagina4":
        template = 'LeiaHistoriaBanheira4.html'

    elif action == "pagina5":
        template = 'LeiaHistoriaBanheira5.html'

    elif action == "pagina6":
        template = 'LeiaHistoriaBanheira6.html'

    templateData = {
        'title': 'A8 - Banheira de José',
    }

    return render_template(template, **templateData)


@app.route("/Activities/A8/banheira/verificar/<int:pagina>")
def verificar_banheira(pagina):
    global texto_microfone

    if pagina not in textos_banheira:
        return jsonify({
            "success": False,
            "percentage": 0,
            "heard": texto_microfone,
            "feedback": []
        })

    texto_esperado = textos_banheira[pagina]

    porcentagem = calcular_acerto(
        texto_microfone,
        texto_esperado
    )

    feedback = gerar_feedback_palavras(
        texto_microfone,
        texto_esperado
    )

    return jsonify({
        "success": porcentagem >= 60.0,
        "percentage": round(porcentagem, 1),
        "heard": texto_microfone,
        "feedback": feedback
    })

###########################################
############ Pseudoprogramacion ###########
###########################################

@app.route('/get_activities', methods=['POST'])
def get():
    activities_paths = get_activities()
    return jsonify({'status': 'success', 'activities': activities_paths})

###########################################
############ Texto Interactivo ############
###########################################
'''
@app.route('/get_text')
def get_text():
    global text
    return jsonify({"text": text})

@app.route('/submit_text', methods=['POST'])
def submit_text():
    input_text = request.form['input_text']
    pubText.publish(input_text)
    #print(input_text)
    return jsonify({'status': 'success', 'input_text': input_text})
    '''

###########################################
############ Game Serious Menu ############
###########################################
@app.route('/game_menu')
def game_menu():
     return render_template('gameMenu.html')

@app.route('/play_audio', methods=['POST'])
def play_audio():
    data = request.get_json()
    audio_file = data.get('audio', '')
    
    if audio_file:
        # Publica el archivo de sonido al nodo ROS
        print(audio_file)
        pubSpeaker.publish(audio_file)
        return jsonify({"status": "success", "audio_file": audio_file})
    
    else:
        return jsonify({"status": "error", "message": "No audio file provided"}), 400


###########################################
############ Game Serious 1 ###############
###########################################
@app.route('/game_atac', methods=['GET', 'POST'])
def game():
    template = 'game_atencion_activa.html'

    if request.method == 'POST':
        action = request.form.get('action')
        level = request.form.get('level', 'basic')
        if action == 'button_pressed':
            # Aquí puedes hacer lo que desees cuando se presiona el botón
            pubSpeaker.publish("juego_1")
        return redirect(url_for('game', level=level))
    
    level = request.args.get('level', 'basic')
    return render_template(template, level=level)

@app.route('/results_atac')
def results():
    score = request.args.get('score', 0)
    return render_template('results_atencion_activa.html', score=score)

###########################################
############ Game Serious 2 ###############
###########################################

@app.route('/game_guardianes', methods=['GET', 'POST'])
def game_guardianes():
    template = 'game_guardianes.html'
    if request.method == 'POST':
        action = request.form.get('action')
        level = request.form.get('level', 'basic')
        if action == 'button_pressed':
            # Aquí puedes hacer lo que desees cuando se presiona el botón
            pubSpeaker.publish("juego_2")
        return redirect(url_for('game_guardianes', level=level))
    
    level = request.args.get('level', 'basic')
    return render_template(template, level=level)

###########################################
############ Game Serious 3 ###############
###########################################

@app.route('/game_memoriamagic', methods=['GET', 'POST'])
def game_memoriamagic():
    template = 'game_memoria_magic.html'
    if request.method == 'POST':
        action = request.form.get('action')
        level = request.form.get('level', 'basic')
        if action == 'button_pressed':
            # Aquí puedes hacer lo que desees cuando se presiona el botón
            pubSpeaker.publish("juego_3")
        return redirect(url_for('game_memoriamagic', level=level))
    
    level = request.args.get('level', 'basic')
    return render_template(template, level=level)

###########################################
############ Game Serious 4 ###############
###########################################

# Estado inicial del juego
game_state = {
    'time_left': 180,  # 3 minutos en segundos
    'budget': 100,    # Presupuesto inicial
    'invitations_sent': False,  # Estado de la tarea de enviar invitaciones
    'decorations_bought': False,  # Estado de la tarea de comprar decoraciones
    'food_prepared': False,  # Estado de la tarea de preparar la comida
    'entertainment_planned': False
}

cost_per_activity = {
    'Palhaco': 20,
    'Peliculas': 15,
    'Musica': 10,
    'Magia': 25
}

selected_items = {
    'entertainment': None,
    'food': None,
    'decorations': None,
    'invitations': []
}

@app.route('/game_planificar', methods=['GET', 'POST'])
def game_planificar():
    global game_state
    game_state = {
    'time_left': 180,  # 3 minutos en segundos
    'budget': 100,    # Presupuesto inicial
    'invitations_sent': False,  # Estado de la tarea de enviar invitaciones
    'decorations_bought': False,  # Estado de la tarea de comprar decoraciones
    'food_prepared': False,  # Estado de la tarea de preparar la comida
    'entertainment_planned': False,
    'instruction': False
    }
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'button_pressed':
            # Aquí puedes hacer lo que desees cuando se presiona el botón
            pubSpeaker.publish("juego_4")
            game_state['instruction'] = True
    return render_template('game_planificar.html')

@app.route('/status', methods=['GET'])
def status():
    global game_state
    return jsonify(game_state)

@app.route('/send_invitations', methods=['POST'])
def send_invitations():
    global game_state
    data = request.get_json()
    selected_characters = data.get('characters', [])
    cost_per_invitation = 5
    total_cost = len(selected_characters) * cost_per_invitation
    
    selected_items['invitations'] = selected_characters

    if game_state['budget'] >= total_cost:
        game_state['budget'] -= total_cost
        game_state['invitations_sent'] = True
        return jsonify({'success': True, 'budget': game_state['budget'], 'invitations_sent': game_state['invitations_sent']})
    else:
        return jsonify({'success': False, 'message': 'Presupuesto insuficiente'})

@app.route('/buy_decorations', methods=['POST'])
def buy_decorations():
    global game_state
    data = request.get_json()
    selected_decorations = data.get('decorations', [])
    cost_per_decoration = 10
    total_cost = len(selected_decorations) * cost_per_decoration

    selected_items['decorations'] = selected_decorations
    
    if game_state['budget'] >= total_cost:
        game_state['budget'] -= total_cost
        game_state['decorations_bought'] = True
        return jsonify({'success': True, 'budget': game_state['budget'], 'decorations_bought': game_state['decorations_bought']})
    else:
        return jsonify({'success': False, 'message': 'Presupuesto insuficiente'})

@app.route('/prepare_food', methods=['POST'])
def prepare_food():
    global game_state
    data = request.get_json()
    selected_foods = data.get('foods', [])
    cost_per_food = 15
    total_cost = len(selected_foods) * cost_per_food
    
    selected_items['food'] = selected_foods

    if game_state['budget'] >= total_cost:
        game_state['budget'] -= total_cost
        game_state['food_prepared'] = True
        return jsonify({'success': True, 'budget': game_state['budget'], 'food_prepared': game_state['food_prepared']})
    else:
        return jsonify({'success': False, 'message': 'Presupuesto insuficiente'})
    

@app.route('/plan_entertainment', methods=['POST'])
def plan_entertainment():
    global game_state
    data = request.get_json()
    activities_schedule = data.get('activities_schedule', [])

    total_cost = sum([cost_per_activity[activity] for activity in activities_schedule.values() if activity in cost_per_activity])

    selected_items['entertainment'] = activities_schedule
    
    if game_state['budget'] >= total_cost:
        game_state['budget'] -= total_cost
        game_state['entertainment_planned'] = True
        return jsonify({'success': True, 'budget': game_state['budget'], 'entertainment_planned': game_state['entertainment_planned']})
    else:
        return jsonify({'success': False, 'message': 'Presupuesto insuficiente'})
    

@app.route('/finalize_planning', methods=['POST'])
def finalize_planning():
    try:
        data = request.json
        selected_items.update(data)
        return jsonify(success=True, plan=selected_items)
    except Exception as e:
        return jsonify(success=False, message=str(e))  


###########################################
############ Game Serious 5 ###############
###########################################

@app.route('/game_RPS', methods=['GET'])
def game_rps():
    return render_template('game_RPS.html')


@app.route('/play', methods=['POST'])
def play():
    try:
        # Inicio do jogo
        pubSpeaker.publish("rps_ola_vamos_jogar")
        rospy.sleep(4)

        pubSpeaker.publish("rps_mostre_sua_jogada")

        # Espera a jogada
        result = rps_camera.jogar()

        # Jogada do jogador
        if result["player"] == "PEDRA":
            pubSpeaker.publish("rps_voce_jogou_pedra")

        elif result["player"] == "PAPEL":
            pubSpeaker.publish("rps_voce_jogou_papel")

        elif result["player"] == "TESOURA":
            pubSpeaker.publish("rps_voce_jogou_tesoura")

        rospy.sleep(2)

        # Jogada do Castor
        if result["computer"] == "PEDRA":
            pubSpeaker.publish("rps_eu_joguei_pedra")

        elif result["computer"] == "PAPEL":
            pubSpeaker.publish("rps_eu_joguei_papel")

        elif result["computer"] == "TESOURA":
            pubSpeaker.publish("rps_eu_joguei_tesoura")

        rospy.sleep(2)

        # Resultado da partida
        if result["result"] == "VENCEU":
            pubSpeaker.publish("rps_parabens_voce_ganhou")

        elif result["result"] == "PERDEU":
            pubSpeaker.publish("rps_dessa_vez_eu_ganhei")

        elif result["result"] == "EMPATOU":
            pubSpeaker.publish("rps_nos_empatamos")

        
        rospy.sleep(2)
        pubSpeaker.publish("rps_clique_abaixo_em_jogar_novamente")
        return jsonify(result)
    except Exception as e:
        return jsonify({
            "result": "ERROR",
            "message": str(e)
        })

#@app.route("/reset_game", methods=["POST"])
#def reset_game_route():
    #rps_camera.reset_game()
   # return jsonify({"status": "ok"})



# =============================================================
# === ROTAS DA VITORIA — NAO MEXER ===
# =============================================================

def _ia_esta_ativa():
    r = subprocess.run(["pgrep", "-f", "ros_chat.py"],
                       capture_output=True)
    return r.returncode == 0

@app.route("/ia_vitoria")
def ia_vitoria_painel():
    return render_template("ia_vitoria.html",
                           ia_ativa=_ia_esta_ativa(),
                           mensagem=request.args.get("msg"))

@app.route("/ia_vitoria/iniciar")
def ia_vitoria_iniciar():
    subprocess.Popen(["bash", "/home/pi/start_ia_vitoria.sh"],
                     stdout=open("/home/pi/logs_ia/start.log", "w"),
                     stderr=subprocess.STDOUT)
    return redirect("/ia_vitoria?msg=Iniciando+IA...+aguarde+cerca+de+1+minuto+e+atualize+a+pagina")

@app.route("/ia_vitoria/encerrar")
def ia_vitoria_encerrar():
    pubMicrophone.publish("Inactivo")
    time.sleep(1)
    subprocess.run(["pkill", "-f", "ros_microphone_vitoria.py"])
    subprocess.run(["pkill", "-f", "speaker_vitoria.py"])
    subprocess.run(["pkill", "-f", "ros_chat.py"])
    subprocess.run(["pkill", "-f", "ros_tts.py"])
    subprocess.run(["pkill", "-f", "llama-server"])
    time.sleep(2)
    subprocess.Popen(["python",
                       "/home/pi/catkin_ws/src/speaker/scripts/speaker.py"],
                     stdout=open("/home/pi/logs_ia/speaker_mafe.log", "w"),
                     stderr=subprocess.STDOUT)
    subprocess.Popen(["python",
                       "/home/pi/catkin_ws/src/microphone/scripts/ros_microphone.py"],
                     stdout=open("/home/pi/logs_ia/mic_mafe.log", "w"),
                     stderr=subprocess.STDOUT)
    time.sleep(2)
    return redirect("/ia_vitoria?msg=Sessao+encerrada.+Painel+da+Mafe+restaurado.")



# =============================================================
# === ROTAS NOVAS DA VITORIA (painel bonito) ===
# =============================================================

PASTA_SESSOES    = "/home/pi/catkin_ws/src/chat/sessoes"
ULTIMA_FALA_ARQ  = "/tmp/castor_ultima_fala.txt"
ESTADO_ARQ       = "/tmp/castor_estado.txt"
INICIO_ARQ       = "/tmp/castor_sessao_inicio.txt"

def salvar_estado_vitoria(estado):
    with open(ESTADO_ARQ, "w") as f:
        f.write(estado)

def _chat_vivo():
    """O no do chat esta mesmo rodando?"""
    try:
        with open(os.devnull, "w") as nulo:
            return subprocess.call(["pgrep", "-f", "scripts/ros_chat.py"],
                                   stdout=nulo, stderr=nulo) == 0
    except Exception:
        return False

def ler_estado_vitoria():
    """Estado real da IA.

    O arquivo sozinho mente: reiniciar o castor_start.service derruba o chat
    e o llama-server junto (eles sobem de dentro do painel, no mesmo grupo de
    processos do servico), mas o arquivo continua marcado como ativo. Entao o
    painel mostrava Gravando com a IA morta. Aqui o arquivo so vale se o no
    do chat realmente existir."""
    try:
        with open(ESTADO_ARQ) as f:
            estado = f.read().strip()
    except Exception:
        return "parado"
    if estado in ("ativo", "pausado") and not _chat_vivo():
        return "parado"
    return estado

def gerar_nome_sessao_vitoria():
    data = datetime.now().strftime("%d-%m-%Y")
    pasta_dia = os.path.join(PASTA_SESSOES, "sessao-{}".format(data))
    os.makedirs(pasta_dia, exist_ok=True)
    contador = 1
    while os.path.exists(os.path.join(pasta_dia, "{:02d}".format(contador))):
        contador += 1
    pasta = os.path.join(pasta_dia, "{:02d}".format(contador))
    os.makedirs(pasta)
    with open(os.path.join(pasta, "transcricao.txt"), "w") as f:
        f.write("=" * 60 + "\n")
        f.write("TRANSCRICAO DE SESSAO -- CASTOR / LabTEL / UFES\n")
        f.write("=" * 60 + "\n")
        f.write("Data/Hora : {}\n".format(datetime.now().strftime("%d/%m/%Y %H:%M:%S")))
        f.write("=" * 60 + "\n\n")
    return "{}/{}".format(data, "{:02d}".format(contador))

@app.route("/Vitoria/tela")
def vitoria_tela():
    return render_template('exemplo_vitoria.html', title='IA Vitoria')

@app.route("/Vitoria/iniciar")
def vitoria_iniciar():
    estado = ler_estado_vitoria()
    if estado == "parado":
        subprocess.Popen(["/bin/bash", "/home/pi/start_ia_vitoria.sh"])
        salvar_estado_vitoria("ativo")
        # Quem cria a pasta da sessao e o ros_chat.py. O painel so marca a hora
        # de inicio, para a tela ao vivo nao mostrar conversa de sessao antiga.
        try:
            with open(INICIO_ARQ, "w") as f:
                f.write(str(time.time()))
        except Exception:
            pass
        pubRecord.publish("iniciar")
        return jsonify({"status": "ativo"})
    return jsonify({"status": estado})

@app.route("/Vitoria/pausar")
def vitoria_pausar():
    estado = ler_estado_vitoria()
    if estado == "ativo":
        salvar_estado_vitoria("pausado")
        pubRecord.publish("pausar")
        pubChatEstado.publish("pausar")
        return jsonify({"status": "pausado"})
    elif estado == "pausado":
        salvar_estado_vitoria("ativo")
        pubRecord.publish("retomar")
        pubChatEstado.publish("retomar")
        return jsonify({"status": "ativo"})
    return jsonify({"status": estado})

@app.route("/Vitoria/parar")
def vitoria_parar():
    salvar_estado_vitoria("parado")
    pubRecord.publish("parar")
    subprocess.Popen(["setsid", "bash", "/home/pi/stop_ia_vitoria.sh"],
        stdout=open("/home/pi/logs_ia/stop_vitoria.log", "w"),
        stderr=subprocess.STDOUT)
    return jsonify({"status": "parado"})

@app.route("/Vitoria/ultima_fala")
def vitoria_ultima_fala():
    try:
        with open(ULTIMA_FALA_ARQ) as f:
            return jsonify({"fala": f.read().strip()})
    except:
        return jsonify({"fala": ""})

@app.route("/Vitoria/sessoes")
def vitoria_sessoes():
    """Lista as sessoes agrupadas por dia, do mais recente para o mais antigo.
    O nome da pasta e DD-MM-AAAA, entao ordenar como texto colocava dia 30 na
    frente de dia 02. Aqui a data e convertida antes de ordenar."""
    from datetime import date, timedelta
    grupos = []
    hoje = date.today()
    if os.path.exists(PASTA_SESSOES):
        for pasta_dia in os.listdir(PASTA_SESSOES):
            caminho_dia = os.path.join(PASTA_SESSOES, pasta_dia)
            if not os.path.isdir(caminho_dia):
                continue
            dia = pasta_dia.replace("sessao-", "")
            try:
                d = datetime.strptime(dia, "%d-%m-%Y").date()
            except ValueError:
                continue
            lista = []
            for num in sorted(os.listdir(caminho_dia)):
                txt_path = os.path.join(caminho_dia, num, "transcricao.txt")
                linhas = 0
                if os.path.exists(txt_path):
                    with open(txt_path) as f:
                        linhas = sum(1 for l in f if l.startswith("["))
                if linhas > 0:
                    lista.append({"numero": num, "linhas": linhas})
            if not lista:
                continue
            if d == hoje:
                rotulo = "Hoje"
            elif d == hoje - timedelta(days=1):
                rotulo = "Ontem"
            elif d == hoje - timedelta(days=2):
                rotulo = "Anteontem"
            else:
                rotulo = dia
            grupos.append({"dia": dia, "rotulo": rotulo,
                           "ordem": d.isoformat(), "lista": lista})
    grupos.sort(key=lambda g: g["ordem"], reverse=True)
    return render_template('vitoria_sessoes.html', grupos=grupos, title='Sessoes')

@app.route("/Vitoria/sessoes/<dia>/<numero>")
def vitoria_transcricao(dia, numero):
    txt_path = os.path.join(PASTA_SESSOES, "sessao-{}".format(dia), numero, "transcricao.txt")
    linhas = []
    total_castor  = 0
    total_standby = 0
    if os.path.exists(txt_path):
        with open(txt_path) as f:
            linhas = f.readlines()
        total_castor  = sum(1 for l in linhas if "Castor:" in l)
        total_standby = sum(1 for l in linhas if "[standby]" in l)
    return render_template(
        'vitoria_transcricao.html',
        linhas=[l.rstrip() for l in linhas],
        dia=dia, numero=numero,
        total_turnos=len(linhas),
        total_castor=total_castor,
        total_standby=total_standby,
        title='Transcricao'
    )

@app.route("/Vitoria")
def vitoria_raiz():
    return redirect("/Vitoria/tela")

@app.route("/Vitoria/estado")
def vitoria_estado():
    return jsonify({"status": ler_estado_vitoria()})

def _inicio_sessao():
    try:
        with open(INICIO_ARQ) as f:
            return float(f.read().strip())
    except Exception:
        return 0.0

def _transcricao_atual():
    """Transcricao da sessao atual: so conta o que foi escrito depois do Iniciar."""
    inicio = _inicio_sessao()
    if inicio <= 0:
        return None
    melhor, melhor_m = None, -1
    if os.path.exists(PASTA_SESSOES):
        for raiz, _dirs, arquivos in os.walk(PASTA_SESSOES):
            if "transcricao.txt" in arquivos:
                caminho = os.path.join(raiz, "transcricao.txt")
                try:
                    m = os.path.getmtime(caminho)
                except OSError:
                    continue
                if m >= inicio and m > melhor_m:
                    melhor, melhor_m = caminho, m
    return melhor

@app.route("/Vitoria/ao_vivo")
def vitoria_ao_vivo():
    # Sessao encerrada sai do ao vivo: ela passa a viver em Ver Sessoes.
    estado = ler_estado_vitoria()
    if estado == "parado":
        return jsonify({"turnos": [], "sessao": "", "status": estado})
    caminho = _transcricao_atual()
    turnos = []
    sessao = ""
    if caminho:
        partes = caminho.split(os.sep)
        if len(partes) >= 3:
            sessao = "{}/{}".format(partes[-3].replace("sessao-", ""), partes[-2])
        try:
            with open(caminho) as f:
                for linha in f:
                    linha = linha.rstrip()
                    if not linha.startswith("["):
                        continue
                    fim = linha.find("]")
                    if fim < 0:
                        continue
                    hora  = linha[1:fim]
                    resto = linha[fim + 1:].strip()
                    if ":" not in resto:
                        continue
                    quem, texto = resto.split(":", 1)
                    quem, texto = quem.strip(), texto.strip()
                    if quem == "Sistema":
                        baixo = texto.lower()
                        if ("llm" in baixo
                                or baixo.startswith("tempo de resposta")
                                or "saudacao" in baixo):
                            continue
                    turnos.append({"hora": hora, "quem": quem, "texto": texto})
        except Exception:
            pass
    return jsonify({"turnos": turnos, "sessao": sessao,
                    "status": ler_estado_vitoria()})

@app.route("/Terapia/comando/<action>", methods=["POST"])
def terapia_comando(action):
    expressoes = {
        "happy", "sad", "angry", "surprise", "neutral"
    }

    audios = {
        "explicar_mestre": "siga_instrucoes_mestre",
        "musica_mestre": "o_mestre_mandou",
    }

    if action in expressoes:
        pubEmotions.publish(action)

    elif action in audios:
        pubSpeaker.publish(audios[action])

    else:
        return "Comando de Terapia inválido.", 404

    return redirect("/Terapia")
# === FIM ROTAS NOVAS DA VITORIA ===

if __name__ == "__main__":
   app.run(
      host='0.0.0.0',
      port=5000,
      debug=False,
      use_reloader=False,
   )
