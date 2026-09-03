#!/usr/bin/env python3


import time
import subprocess
import json
import threading

import rospy
from flask import Flask, jsonify, redirect, render_template, request, url_for

import rps_camera  # adicionado por Adryan

from acciones import Acciones
from get_activities import get_activities

from std_msgs.msg import String


######################################
################ ROS #################
######################################

threading.Thread(target=lambda: rospy.init_node('mainMenuHTML', disable_signals=True)).start()

######################################
############# PUBLISHERS #############
######################################

pubEmotions = rospy.Publisher('/emotions', String, queue_size = 10)
pubSpeaker = rospy.Publisher('/speaker', String, queue_size = 10)
pubSpeakerAction = rospy.Publisher('/speakerAction', String, queue_size = 15)
pubMovements = rospy.Publisher('/movements', String, queue_size = 5)
pubCastorSystem = rospy.Publisher('/castor_system', String, queue_size = 5)
pubMicrophone = rospy.Publisher('/mic', String, queue_size = 5)
pubText = rospy.Publisher('/microphone', String, queue_size = 5)
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
    return

subText = rospy.Subscriber('/chat_output', String, callbackText)


# Texto reconhecido pelo microfone na atividade A8
texto_microfone = ""

def callbackMicrophone(msg):
    global texto_microfone

    texto_recebido = msg.data.lower().strip()

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


def calcular_acerto(texto_falado, texto_esperado):
    """Calcula o percentual de palavras corretas mantendo a ordem.

    Usa a maior subsequência comum (LCS). Palavras fora de ordem
    não recebem o mesmo crédito que palavras ditas na ordem correta.
    """

    falado = texto_falado.lower().split()
    esperado = texto_esperado.lower().split()

    if len(esperado) == 0:
        return 0.0

    # Matriz da maior subsequência comum entre as duas listas de palavras.
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

######################################
############# MAIN MENU ##############
######################################

app = Flask(__name__)

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

@app.route("/<action>")
def actionMainMenu(action):
    template = "mainMenu.html"

    acciones.Main_Menu(action = action)

    if action == "Activities":
        template = "Actividades.html"
    elif action == "shutdown":
        template = "shutdown.html"
    elif action == "reboot":
        template = "reboot.html"
    elif action == "Text":
        template = "Texto.html"
    elif action == "Pseudoprogramacion":
        template = "Pseudoprogramacion.html"
    elif action == "Ativar":
        pubMicrophone.publish("Activo")
    elif action == "Desativar":
        pubMicrophone.publish("Inactivo")
    
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
        template = 'LeiaHistoriaMenu.html'
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
        pubMicrophone.publish("Activo")
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
            "heard": texto_microfone
        })

    texto_esperado = textos_banheira[pagina]

    porcentagem = calcular_acerto(
        texto_microfone,
        texto_esperado
    )

    return jsonify({
        "success": porcentagem >= 60.0,
        "percentage": round(porcentagem, 1),
        "heard": texto_microfone
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
        pubSpeaker.publish("rps_ola_vamos_jogar.mp3")
        rospy.sleep(4)

        pubSpeaker.publish("rps_mostre_sua_jogada.mp3")

        # Espera a jogada
        result = rps_camera.jogar()

        # Jogada do jogador
        if result["player"] == "PEDRA":
            pubSpeaker.publish("rps_voce_jogou_pedra.mp3")

        elif result["player"] == "PAPEL":
            pubSpeaker.publish("rps_voce_jogou_papel.mp3")

        elif result["player"] == "TESOURA":
            pubSpeaker.publish("rps_voce_jogou_tesoura.mp3")

        rospy.sleep(2)

        # Jogada do Castor
        if result["computer"] == "PEDRA":
            pubSpeaker.publish("rps_eu_joguei_pedra.mp3")

        elif result["computer"] == "PAPEL":
            pubSpeaker.publish("rps_eu_joguei_papel.mp3")

        elif result["computer"] == "TESOURA":
            pubSpeaker.publish("rps_eu_joguei_tesoura.mp3")

        rospy.sleep(2)

        # Resultado da partida
        if result["result"] == "VENCEU":
            pubSpeaker.publish("rps_parabens_voce_ganhou.mp3")

        elif result["result"] == "PERDEU":
            pubSpeaker.publish("rps_dessa_vez_eu_ganhei.mp3")

        elif result["result"] == "EMPATOU":
            pubSpeaker.publish("rps_nos_empatamos.mp3")

        
        rospy.sleep(2)
        pubSpeaker.publish("rps_clique_abaixo_em_jogar_novamente.mp3")
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


if __name__ == "__main__":
   app.run(
      host='0.0.0.0',
      port=5000,
      debug=False,
      use_reloader=False,
   )
