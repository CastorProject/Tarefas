#! /usr/bin/env python
import time
import rospy
import subprocess

from flask import Flask, render_template, request
import threading

from std_msgs.msg import Float64
from std_msgs.msg import String
from std_msgs.msg import Bool

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
######################################
############# MAIN MENU ##############
######################################
app = Flask(__name__)
@app.route("/")
def mainMenu():
	templateData = {
		'title' : 'Main Menu',
	}
	return render_template('mainMenu.html', **templateData)

@app.route("/<action>")
def actionMainMenu(action):
	template = "mainMenu.html"
	if action == "greet":
		pubMovements.publish("wave")
		pubEmotions.publish("happy")
		pubSpeaker.publish("me_chamo_castor")
	elif action == "greet2":
		pubEmotions.publish("talk")
		pubSpeaker.publish("ola_castor")
	elif action == "lets_go":
		pubEmotions.publish("happy")
		pubSpeaker.publish("vamos_brincar")
	elif action == "presentation1":
		pubEmotions.publish("happy")
		pubSpeaker.publish("castor_apresentacao")
	elif action == "presentation2":
		pubEmotions.publish("happy")
		pubSpeaker.publish("Eu_gosto_de")
	elif action == "foto":
		pubEmotions.publish("talk")
		pubSpeaker.publish("foto")


	elif action == "bye":
		pubMovements.publish("wave")
		time.sleep(0.5)
		pubEmotions.publish("talk")
		pubSpeaker.publish("tchau_amigo")
	elif action == "bye2":
		pubMovements.publish("wave")
		time.sleep(0.5)
		pubEmotions.publish("talk")
		pubSpeaker.publish("tchau_amiga")
	elif action == "byeamigos":
		pubMovements.publish("wave")
		time.sleep(0.5)
		pubEmotions.publish("talk")
		pubSpeaker.publish("tchau_amigos")
	
	elif action == "final":
		pubEmotions.publish("talk")
		pubSpeaker.publish("tudo_hoje")
	elif action == "thanks":
		pubEmotions.publish("talk")
		pubSpeaker.publish("obrigado_brincar_hoje")
	elif action == "happyday":
		pubEmotions.publish("talk")
		pubSpeaker.publish("tenha_um_otimo_dia")

	elif action == "hifiveinstruction":
		pubEmotions.publish("talk")
		pubSpeaker.publish("Hi-5")
	elif action == "highfive":
		pubMovements.publish("highfive")
	elif action == "bajar_brazo":
		pubMovements.publish("down_highfive")
		
	elif action == "Activities":
		template = "Actividades.html"
	elif action == "shutdown":
		template = "shutdown.html"
	elif action == "reboot":
		template = "reboot.html"

	templateData = {
		'title' : 'Main Menu',
	}
	return render_template(template, **templateData)

###############################################
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

	templateData = {
		'title' : 'Activities',
	}
	return render_template(template, **templateData)

##############################################
################# Conversacion ###############
##############################################
@app.route("/Activities/A6/<action>")
def Conversacion(action):
	template = "Conversation.html"
	#Bodyparts
	if action == "sayBody":
		pubEmotions.publish("talk")
		pubSpeaker.publish("partes_do_corpo")
	elif action == "pointHead":
		#pubMovements.publish("pointHead")
		time.sleep(0.5)
		pubEmotions.publish("talk")
		pubSpeaker.publish("onde_esta_minha_cabeca")
	elif action == "pointEyes":
		#pubMovements.publish("pointEyes")
		time.sleep(0.5)
		pubEmotions.publish("talk")
		pubSpeaker.publish("onde_estao_meus_olhos")
	elif action == "pointNose":
		#pubMovements.publish("pointNose")
		time.sleep(0.5)
		pubEmotions.publish("talk")
		pubSpeaker.publish("onde_esta_meu_nariz")
	elif action == "pointMouth":
		#pubMovements.publish("pointMouth")
		time.sleep(0.5)
		pubEmotions.publish("talk")
		pubSpeaker.publish("onde_esta_minha_boca")
	elif action == "botones":
		#pubMovements.publish("pointMouth")
		time.sleep(0.5)
		pubEmotions.publish("talk")
		pubSpeaker.publish("toca_botoes")

		
	elif action == "askHead":
		pubEmotions.publish("talk")
		pubSpeaker.publish("aponte_sua_cabeca")
	elif action == "askEyes":
		pubEmotions.publish("talk")
		pubSpeaker.publish("aponte_seus_olhos")
	elif action == "askNose":
		pubEmotions.publish("talk")
		pubSpeaker.publish("aponte_seu_nariz")
	elif action == "askMouth":
		pubEmotions.publish("talk")
		pubSpeaker.publish("aponte_sua_boca")
	#Emotions
	elif action == "howifeel":
		pubEmotions.publish("talk")
		pubSpeaker.publish("como_acha_me_sentindo")
	elif action == "emotion":
		pubEmotions.publish("talk")
		pubSpeaker.publish("adivinha_sentindo")
	elif action == "andnow":
		pubEmotions.publish("talk")
		pubSpeaker.publish("agora_sim_como_me_sinto")
		
	elif action == "happy":
		pubEmotions.publish("happy")
	elif action == "sad":
		pubEmotions.publish("sad")
	elif action == "angry":
		pubEmotions.publish("angry")
	elif action == "surprise":
		pubEmotions.publish("surprise")
	elif action == "neutral":
		pubEmotions.publish("neutral")
		
	elif action == "ifeel_happy":
		#pubEmotions.publish("talk")
		pubSpeaker.publish("me_sinto_feliz")
	elif action == "ifeel_sad":
		#pubEmotions.publish("talk")
		pubSpeaker.publish("me_sinto_triste")
	elif action == "ifeel_angry":
		#pubEmotions.publish("talk")
		pubSpeaker.publish("me_sinto_irritado")
	elif action == "ifeel_surprise":
		#pubEmotions.publish("talk")
		pubSpeaker.publish("estou_surpreso")
	
	#Maths
	elif action == "count":
		pubEmotions.publish("talk")
		pubSpeaker.publish("contar_um_a_dez")
	elif action == "explain":
		pubEmotions.publish("talk")
		pubSpeaker.publish("pode_contar_comigo")
	elif action == "one":
		#pubEmotions.publish("talk")
		pubSpeaker.publish("um")
	elif action == "two":
		#pubEmotions.publish("talk")
		pubSpeaker.publish("dois")
	elif action == "tree":
		#pubEmotions.publish("talk")
		pubSpeaker.publish("tres")
	elif action == "four":
		#pubEmotions.publish("talk")
		pubSpeaker.publish("quatro")
	elif action == "five":
		#pubEmotions.publish("talk")
		pubSpeaker.publish("cinco")
	elif action == "six":
		#pubEmotions.publish("talk")
		pubSpeaker.publish("seis")
	elif action == "seven":
		#pubEmotions.publish("talk")
		pubSpeaker.publish("sete")
	elif action == "eight":
		#pubEmotions.publish("talk")
		pubSpeaker.publish("oito")
	elif action == "nine":
		#pubEmotions.publish("talk")
		pubSpeaker.publish("nove")
	elif action == "ten":
		#pubEmotions.publish("talk")
		pubSpeaker.publish("dez")
	elif action == "sum":
		pubEmotions.publish("talk")
		pubSpeaker.publish("vc_sabe_somar")
	elif action == "substraction":
		pubEmotions.publish("talk")
		pubSpeaker.publish("vc_sabe_subtrair")
	elif action == "howmuch":
		pubEmotions.publish("talk")
		pubSpeaker.publish("quanto_eh")
	elif action == "plus":
		pubEmotions.publish("talk")
		pubSpeaker.publish("mais")
	elif action == "less":
		pubEmotions.publish("talk")
		pubSpeaker.publish("menos")
	#Conversation
	elif action == "your_name":
		pubEmotions.publish("talk")
		pubSpeaker.publish("Como_seu_nome")
	elif action == "your_name2":
		pubEmotions.publish("talk")
		pubSpeaker.publish("Qual_seu_nome")
	elif action == "nicemeet":
		pubEmotions.publish("talk")
		pubSpeaker.publish("prazer")
	elif action == "howRU":
		pubEmotions.publish("talk")
		pubSpeaker.publish("como_estao")
	elif action == "name1":
		pubEmotions.publish("talk")
		pubSpeaker.publish("qual_meu_nome")
	elif action == "color":
		pubEmotions.publish("talk")
		pubSpeaker.publish("qual_sua_cor_preferida")
	elif action == "animalFav":
		pubEmotions.publish("talk")
		pubSpeaker.publish("animal_preferido") 
	elif action == "cancionFav":
		pubEmotions.publish("talk")
		pubSpeaker.publish("musica_preferida")
	elif action == "liketoplay":
		pubEmotions.publish("talk")
		pubSpeaker.publish("gosta_brincar")

	elif action == "imGood":
		pubEmotions.publish("talk")
		pubSpeaker.publish("eu_tambem_estou_bem")
	elif action == "name2":
		pubEmotions.publish("talk")
		pubSpeaker.publish("meu_nome")
	elif action == "Metoo":
		pubEmotions.publish("talk")
		pubSpeaker.publish("eu_tambem")
	elif action == "Likewise":
		pubEmotions.publish("talk")
		pubSpeaker.publish("o_meu_tambem")
	elif action == "Likewise2":
		pubEmotions.publish("talk")
		pubSpeaker.publish("a_minha_tambem")
	elif action == "lo_tendre_en_cuenta":
		pubEmotions.publish("talk")
		pubSpeaker.publish("leve_em_conta")
	elif action=="Hearthat":
		pubEmotions.publish("talk")
		pubSpeaker.publish("fico_feliz_de_ouvir")		 
	elif action == "ColorGreen":
		#pubEmotions.publish("talk")
		pubSpeaker.publish("cor_favorita")
	elif action == "MianimalFav":
		#pubEmotions.publish("talk")
		pubSpeaker.publish("meu_animal_preferido")
	elif action == "DogSound":
		time.sleep(0.5)
		#pubEmotions.publish("talk")
		pubSpeaker.publish("cachorro_faz")
	elif action == "Favthings":
		#pubEmotions.publish("talk")
		pubSpeaker.publish("adoro_brincar_com_voces")
	elif action=="si":
		#pubEmotions.publish("talk")
		pubSpeaker.publish("sim")
	elif action=="no":
		#pubEmotions.publish("talk")
		pubSpeaker.publish("nao")
	elif action=="nose":
		#pubEmotions.publish("talk")
		pubSpeaker.publish("nao_sei")
	elif action=="thanks":
		#pubEmotions.publish("talk")
		pubSpeaker.publish("obrigado")
	elif action=="yourwelcome":
		#pubEmotions.publish("talk")
		pubSpeaker.publish("de_nada")
		
	elif action == "gj1":
		pubEmotions.publish("happy")
		pubSpeaker.publish("muito_bem")
	elif action == "gj2":
		pubEmotions.publish("happy")
		pubSpeaker.publish("parabens_02")
	elif action == "gj3":
		pubEmotions.publish("happy")
		pubSpeaker.publish("que_bom")
	elif action == "gj4":
		pubEmotions.publish("happy")
		pubSpeaker.publish("conseguiu")
	elif action == "gj5":
		pubEmotions.publish("happy")
		pubSpeaker.publish("fez_muito_bem")
	elif action == "gj6":
		pubEmotions.publish("happy")
		pubSpeaker.publish("parabens")
	elif action == "gj7":
		pubEmotions.publish("happy")
		pubSpeaker.publish("excelente")
	elif action == "gj8":
		pubEmotions.publish("happy")
		pubSpeaker.publish("continue_brincando")
	elif action == "nt1":
		pubEmotions.publish("sad")
		pubSpeaker.publish("tente_de_novo")
	elif action == "nt2":
		pubEmotions.publish("sad")
		pubSpeaker.publish("continue_brincando")
	elif action == "nt3":
		pubEmotions.publish("sad")
		pubSpeaker.publish("quase_conseguiu")
	elif action == "nt4":
		pubEmotions.publish("happy")
		pubSpeaker.publish("continue_assim")
	elif action=="nt6":
		pubEmotions.publish("happy")
		pubSpeaker.publish("continue_dancando")
	elif action=="nt7":
		pubEmotions.publish("sad")
		pubSpeaker.publish("nao_consigo_ouvir")
	elif action=="nt9":
		pubEmotions.publish("happy")
		pubSpeaker.publish("com_todo_prazer")
	elif action=="nt10":
		pubEmotions.publish("sad")
		pubSpeaker.publish("sente-se")
	elif action=="nt11":
		pubEmotions.publish("sad")
		pubSpeaker.publish("venha")
	elif action=="nt12":
		pubEmotions.publish("sad")
		pubSpeaker.publish("preste_atencao_em_mim")
	elif action == "me_duele":
		pubSpeaker.publish("assim_nao_voce_Esta_me_machucando")
		time.sleep(0.5)
		pubEmotions.publish("angry")
	elif action == "lastimar":
		pubSpeaker.publish("assim_nao_voce_Esta_me_machucando")
		time.sleep(0.5)
		pubEmotions.publish("sad")
	elif action=="t1":
		#pubEmotions.publish("talk")
		pubSpeaker.publish("esta_tudo_bem")
	elif action=="t2":
		#pubEmotions.publish("talk")
		pubSpeaker.publish("sem_problema")
	elif action=="t4":
		#pubEmotions.publish("talk")
		pubSpeaker.publish("olhe_pra_mim")
	elif action=="t5":
		#pubEmotions.publish("talk")
		pubSpeaker.publish("nao_grite")
	elif action=="t6":
		#pubEmotions.publish("talk")
		pubSpeaker.publish("nao_chore")
	elif action=="t10":
		#pubEmotions.publish("talk")
		pubSpeaker.publish("diga_por_favor")

	templateData = {
		'title' : 'Conversation Menu',
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

	elif action == "indication1":
		pubSpeaker.publish("pule")
	elif action == "indication2":
		pubSpeaker.publish("aplauda_duas_vezes")
	elif action == "indication3":
		pubSpeaker.publish("uma_volta")
	elif action == "indication4":
		pubSpeaker.publish("abaixe_se")
	elif action == "indication5":
		pubSpeaker.publish("faca_uma_cara_surpresa")
	elif action == "indication6":
		pubSpeaker.publish("cara_bravo")
	elif action == "indication7":
		pubSpeaker.publish("cara_feliz")
	elif action == "indication8":
		pubSpeaker.publish("cara_medo")
	elif action == "indication9":
		pubSpeaker.publish("cara_tristeza")
	elif action == "indication10":
		pubSpeaker.publish("toque_boca")
	elif action == "indication11":
		pubSpeaker.publish("toque_cotovelos")
	elif action == "indication12":
		pubSpeaker.publish("toque_nariz")
	elif action == "indication13":
		pubSpeaker.publish("toque_pes")
	elif action == "indication14":
		pubSpeaker.publish("mao_direita")
	elif action == "indication15":
		pubSpeaker.publish("mao_esquerda")
	elif action == "indication16":
		pubSpeaker.publish("pule_um_pe")
	elif action == "indication17":
		pubSpeaker.publish("mostre_lingua")

	elif action == "gj1":
		pubEmotions.publish("happy")
		pubSpeaker.publish("muito_bem")
	elif action == "gj2":
		pubEmotions.publish("happy")
		pubSpeaker.publish("parabens_02")
	elif action == "gj3":
		pubEmotions.publish("happy")
		pubSpeaker.publish("que_bom")
	elif action == "gj4":
		pubEmotions.publish("happy")
		pubSpeaker.publish("conseguiu")
	elif action == "gj5":
		pubEmotions.publish("happy")
		pubSpeaker.publish("fez_muito_bem")
	elif action == "gj6":
		pubEmotions.publish("happy")
		pubSpeaker.publish("parabens")
	elif action == "gj7":
		pubEmotions.publish("happy")
		pubSpeaker.publish("excelente")
	elif action == "gj8":
		pubEmotions.publish("happy")
		pubSpeaker.publish("continue_brincando")
	elif action == "nt1":
		pubEmotions.publish("sad")
		pubSpeaker.publish("tente_de_novo")
	elif action == "nt2":
		pubEmotions.publish("sad")
		pubSpeaker.publish("continue_brincando")
	elif action == "nt3":
		pubEmotions.publish("sad")
		pubSpeaker.publish("quase_conseguiu")
	elif action == "nt4":
		pubEmotions.publish("happy")
		pubSpeaker.publish("continue_assim")
	elif action=="nt6":
		pubEmotions.publish("happy")
		pubSpeaker.publish("continue_dancando")
	elif action=="nt7":
		pubEmotions.publish("sad")
		pubSpeaker.publish("nao_consigo_ouvir")
	elif action=="nt9":
		pubEmotions.publish("happy")
		pubSpeaker.publish("com_todo_prazer")
	elif action=="nt10":
		pubEmotions.publish("sad")
		pubSpeaker.publish("sente-se")
	elif action=="nt11":
		pubEmotions.publish("sad")
		pubSpeaker.publish("venha")
	elif action=="nt12":
		pubEmotions.publish("sad")
		pubSpeaker.publish("preste_atencao_em_mim")
	elif action == "me_duele":
		pubSpeaker.publish("assim_nao_voce_Esta_me_machucando")
		time.sleep(0.5)
		pubEmotions.publish("angry")
	elif action == "lastimar":
		pubSpeaker.publish("assim_nao_voce_Esta_me_machucando")
		time.sleep(0.5)
		pubEmotions.publish("sad")
	elif action=="t1":
		#pubEmotions.publish("talk")
		pubSpeaker.publish("esta_tudo_bem")
	elif action=="t2":
		#pubEmotions.publish("talk")
		pubSpeaker.publish("sem_problema")
	elif action=="t4":
		#pubEmotions.publish("talk")
		pubSpeaker.publish("olhe_pra_mim")
	elif action=="t5":
		#pubEmotions.publish("talk")
		pubSpeaker.publish("nao_grite")
	elif action=="t6":
		#pubEmotions.publish("talk")
		pubSpeaker.publish("nao_chore")
	elif action=="t10":
		#pubEmotions.publish("talk")
		pubSpeaker.publish("diga_por_favor")

	elif action == "happy":
		pubEmotions.publish("happy")
	elif action == "sad":
		pubEmotions.publish("sad")
	elif action == "angry":
		pubEmotions.publish("angry")
	elif action == "surprise":
		pubEmotions.publish("surprise")
	elif action == "neutral":
		pubEmotions.publish("neutral")
	
	
	templateData = {
		'title' : 'A1',
	}
	return render_template(template, **templateData)

###########################################
################### Act 2 #################
###########################################

@app.route("/Activities/A2/<action>")
def actionL1_A2(action):
	template = 'Act2_cuenJose.html'
	if action == "explain2":
		pubSpeaker.publish("ver_escutar_historia")
	elif action == "explain3":
		pubSpeaker.publish("responder_algumas_perguntas")

	elif action == "jose1":
		template = 'level3Memory1.html'
	elif action == "jose2":
		template = 'level3Memory2.html'
	elif action == "jose4":
		template = 'level3Memory4.html'
	elif action == "jose5":
		template = 'level3Memory5.html'

	elif action == "gj1":
		pubEmotions.publish("happy")
		pubSpeaker.publish("muito_bem")
	elif action == "gj2":
		pubEmotions.publish("happy")
		pubSpeaker.publish("parabens_02")
	elif action == "gj3":
		pubEmotions.publish("happy")
		pubSpeaker.publish("que_bom")
	elif action == "gj4":
		pubEmotions.publish("happy")
		pubSpeaker.publish("conseguiu")
	elif action == "gj5":
		pubEmotions.publish("happy")
		pubSpeaker.publish("fez_muito_bem")
	elif action == "gj6":
		pubEmotions.publish("happy")
		pubSpeaker.publish("parabens")
	elif action == "gj7":
		pubEmotions.publish("happy")
		pubSpeaker.publish("excelente")
	elif action == "gj8":
		pubEmotions.publish("happy")
		pubSpeaker.publish("continue_brincando")
	elif action == "nt1":
		pubEmotions.publish("sad")
		pubSpeaker.publish("tente_de_novo")
	elif action == "nt2":
		pubEmotions.publish("sad")
		pubSpeaker.publish("continue_brincando")
	elif action == "nt3":
		pubEmotions.publish("sad")
		pubSpeaker.publish("quase_conseguiu")
	elif action == "nt4":
		pubEmotions.publish("happy")
		pubSpeaker.publish("continue_assim")
	elif action=="nt6":
		pubEmotions.publish("happy")
		pubSpeaker.publish("continue_dancando")
	elif action=="nt7":
		pubEmotions.publish("sad")
		pubSpeaker.publish("nao_consigo_ouvir")
	elif action=="nt9":
		pubEmotions.publish("happy")
		pubSpeaker.publish("com_todo_prazer")
	elif action=="nt10":
		pubEmotions.publish("sad")
		pubSpeaker.publish("sente-se")
	elif action=="nt11":
		pubEmotions.publish("sad")
		pubSpeaker.publish("venha")
	elif action=="nt12":
		pubEmotions.publish("sad")
		pubSpeaker.publish("preste_atencao_em_mim")
	elif action == "me_duele":
		pubSpeaker.publish("assim_nao_voce_Esta_me_machucando")
		time.sleep(0.5)
		pubEmotions.publish("angry")
	elif action == "lastimar":
		pubSpeaker.publish("assim_nao_voce_Esta_me_machucando")
		time.sleep(0.5)
		pubEmotions.publish("sad")
	elif action=="t1":
		#pubEmotions.publish("talk")
		pubSpeaker.publish("esta_tudo_bem")
	elif action=="t2":
		#pubEmotions.publish("talk")
		pubSpeaker.publish("sem_problema")
	elif action=="t4":
		#pubEmotions.publish("talk")
		pubSpeaker.publish("olhe_pra_mim")
	elif action=="t5":
		#pubEmotions.publish("talk")
		pubSpeaker.publish("nao_grite")
	elif action=="t6":
		#pubEmotions.publish("talk")
		pubSpeaker.publish("nao_chore")
	elif action=="t10":
		#pubEmotions.publish("talk")
		pubSpeaker.publish("diga_por_favor")

	elif action == "happy":
		pubEmotions.publish("happy")
	elif action == "sad":
		pubEmotions.publish("sad")
	elif action == "angry":
		pubEmotions.publish("angry")
	elif action == "surprise":
		pubEmotions.publish("surprise")
	elif action == "neutral":
		pubEmotions.publish("neutral")
		
	templateData = {
		'title' : 'A2',
	}
	return render_template(template, **templateData)

#############################################################################
############################# Act2 History 1 ###########################
#############################################################################
@app.route("/Activities/A2/history1/<action>")
def actionL1_A2_1(action):
	template = 'level3Memory1.html'
	if action == "segment1":
		pubSpeaker.publish("jose_esta_na_rua")
	elif action == "segment2":
		pubSpeaker.publish("jose_atravessa_a_rua")
	elif action == "segment3":
		pubSpeaker.publish("jose_rua_3")
	elif action == "segment4":
		pubSpeaker.publish("jose_rua_4")
	elif action == "segment5":
		pubSpeaker.publish("jose_rua_5")
	elif action == "segment6":
		pubSpeaker.publish("jose_rua_6")

	elif action == "stop":
		pubSpeakerAction.publish("stop")
	elif action == "pause":
		pubSpeakerAction.publish("pause")
	elif action == "play":
		pubSpeakerAction.publish("unpause")

	elif action == "question1":
		pubSpeaker.publish("jose_rua_p1")
	elif action == "question2":
		pubSpeaker.publish("jose_rua_p2")
	elif action == "question3":
		pubSpeaker.publish("jose_rua_p3")

	elif action == "gj1":
		pubEmotions.publish("happy")
		pubSpeaker.publish("muito_bem")
	elif action == "gj2":
		pubEmotions.publish("happy")
		pubSpeaker.publish("parabens_02")
	elif action == "gj3":
		pubEmotions.publish("happy")
		pubSpeaker.publish("que_bom")
	elif action == "gj4":
		pubEmotions.publish("happy")
		pubSpeaker.publish("conseguiu")
	elif action == "gj5":
		pubEmotions.publish("happy")
		pubSpeaker.publish("fez_muito_bem")
	elif action == "gj6":
		pubEmotions.publish("happy")
		pubSpeaker.publish("parabens")
	elif action == "gj7":
		pubEmotions.publish("happy")
		pubSpeaker.publish("excelente")
	elif action == "gj8":
		pubEmotions.publish("happy")
		pubSpeaker.publish("continue_brincando")
	elif action == "nt1":
		pubEmotions.publish("sad")
		pubSpeaker.publish("tente_de_novo")
	elif action == "nt2":
		pubEmotions.publish("sad")
		pubSpeaker.publish("continue_brincando")
	elif action == "nt3":
		pubEmotions.publish("sad")
		pubSpeaker.publish("quase_conseguiu")
	elif action == "nt4":
		pubEmotions.publish("happy")
		pubSpeaker.publish("continue_assim")
	elif action=="nt6":
		pubEmotions.publish("happy")
		pubSpeaker.publish("continue_dancando")
	elif action=="nt7":
		pubEmotions.publish("sad")
		pubSpeaker.publish("nao_consigo_ouvir")
	elif action=="nt9":
		pubEmotions.publish("happy")
		pubSpeaker.publish("com_todo_prazer")
	elif action=="nt10":
		pubEmotions.publish("sad")
		pubSpeaker.publish("sente-se")
	elif action=="nt11":
		pubEmotions.publish("sad")
		pubSpeaker.publish("venha")
	elif action=="nt12":
		pubEmotions.publish("sad")
		pubSpeaker.publish("preste_atencao_em_mim")
	elif action == "me_duele":
		pubSpeaker.publish("assim_nao_voce_Esta_me_machucando")
		time.sleep(0.5)
		pubEmotions.publish("angry")
	elif action == "lastimar":
		pubSpeaker.publish("assim_nao_voce_Esta_me_machucando")
		time.sleep(0.5)
		pubEmotions.publish("sad")
	elif action=="t1":
		#pubEmotions.publish("talk")
		pubSpeaker.publish("esta_tudo_bem")
	elif action=="t2":
		#pubEmotions.publish("talk")
		pubSpeaker.publish("sem_problema")
	elif action=="t4":
		#pubEmotions.publish("talk")
		pubSpeaker.publish("olhe_pra_mim")
	elif action=="t5":
		#pubEmotions.publish("talk")
		pubSpeaker.publish("nao_grite")
	elif action=="t6":
		#pubEmotions.publish("talk")
		pubSpeaker.publish("nao_chore")
	elif action=="t10":
		#pubEmotions.publish("talk")
		pubSpeaker.publish("diga_por_favor")

	elif action == "happy":
		pubEmotions.publish("happy")
	elif action == "sad":
		pubEmotions.publish("sad")
	elif action == "angry":
		pubEmotions.publish("angry")
	elif action == "surprise":
		pubEmotions.publish("surprise")
	elif action == "neutral":
		pubEmotions.publish("neutral")
		
	templateData = {
		'title' : 'A2 History 1',
	}
	return render_template(template, **templateData)

#############################################################################
############################# Act 2 History 2 ###########################
#############################################################################
@app.route("/Activities/A2/history2/<action>")
def actionL2_A2_2(action):
	template = 'level3Memory2.html'
	if action == "segment1":
		pubSpeaker.publish("jose_aniversario_1")
	elif action == "segment2":
		pubSpeaker.publish("jose_aniversario_2")
	elif action == "segment3":
		pubSpeaker.publish("jose_aniversario_3")
	elif action == "segment4":
		pubSpeaker.publish("jose_aniversario_4")
	elif action == "segment5":
		pubSpeaker.publish("jose_sopra_vela")
	elif action == "segment6":
		pubSpeaker.publish("jose_abre_presente")
	elif action == "segment7":
		pubSpeaker.publish("jose_ja_tem_tres_anos")

	elif action == "stop":
		pubSpeakerAction.publish("stop")
	elif action == "pause":
		pubSpeakerAction.publish("pause")
	elif action == "play":
		pubSpeakerAction.publish("unpause")

	elif action == "question1":
		pubSpeaker.publish("jose_aniversario_p1")
	elif action == "question2":
		pubSpeaker.publish("jose_aniversario_p2")
	elif action == "question3":
		pubSpeaker.publish("jose_aniversario_p3")

	elif action == "gj1":
		pubEmotions.publish("happy")
		pubSpeaker.publish("muito_bem")
	elif action == "gj2":
		pubEmotions.publish("happy")
		pubSpeaker.publish("parabens_02")
	elif action == "gj3":
		pubEmotions.publish("happy")
		pubSpeaker.publish("que_bom")
	elif action == "gj4":
		pubEmotions.publish("happy")
		pubSpeaker.publish("conseguiu")
	elif action == "gj5":
		pubEmotions.publish("happy")
		pubSpeaker.publish("fez_muito_bem")
	elif action == "gj6":
		pubEmotions.publish("happy")
		pubSpeaker.publish("parabens")
	elif action == "gj7":
		pubEmotions.publish("happy")
		pubSpeaker.publish("excelente")
	elif action == "gj8":
		pubEmotions.publish("happy")
		pubSpeaker.publish("continue_brincando")
	elif action == "nt1":
		pubEmotions.publish("sad")
		pubSpeaker.publish("tente_de_novo")
	elif action == "nt2":
		pubEmotions.publish("sad")
		pubSpeaker.publish("continue_brincando")
	elif action == "nt3":
		pubEmotions.publish("sad")
		pubSpeaker.publish("quase_conseguiu")
	elif action == "nt4":
		pubEmotions.publish("happy")
		pubSpeaker.publish("continue_assim")
	elif action=="nt6":
		pubEmotions.publish("happy")
		pubSpeaker.publish("continue_dancando")
	elif action=="nt7":
		pubEmotions.publish("sad")
		pubSpeaker.publish("nao_consigo_ouvir")
	elif action=="nt9":
		pubEmotions.publish("happy")
		pubSpeaker.publish("com_todo_prazer")
	elif action=="nt10":
		pubEmotions.publish("sad")
		pubSpeaker.publish("sente-se")
	elif action=="nt11":
		pubEmotions.publish("sad")
		pubSpeaker.publish("venha")
	elif action=="nt12":
		pubEmotions.publish("sad")
		pubSpeaker.publish("preste_atencao_em_mim")
	elif action == "me_duele":
		pubSpeaker.publish("assim_nao_voce_Esta_me_machucando")
		time.sleep(0.5)
		pubEmotions.publish("angry")
	elif action == "lastimar":
		pubSpeaker.publish("assim_nao_voce_Esta_me_machucando")
		time.sleep(0.5)
		pubEmotions.publish("sad")
	elif action=="t1":
		#pubEmotions.publish("talk")
		pubSpeaker.publish("esta_tudo_bem")
	elif action=="t2":
		#pubEmotions.publish("talk")
		pubSpeaker.publish("sem_problema")
	elif action=="t4":
		#pubEmotions.publish("talk")
		pubSpeaker.publish("olhe_pra_mim")
	elif action=="t5":
		#pubEmotions.publish("talk")
		pubSpeaker.publish("nao_grite")
	elif action=="t6":
		#pubEmotions.publish("talk")
		pubSpeaker.publish("nao_chore")
	elif action=="t10":
		#pubEmotions.publish("talk")
		pubSpeaker.publish("diga_por_favor")

	elif action == "happy":
		pubEmotions.publish("happy")
	elif action == "sad":
		pubEmotions.publish("sad")
	elif action == "angry":
		pubEmotions.publish("angry")
	elif action == "surprise":
		pubEmotions.publish("surprise")
	elif action == "neutral":
		pubEmotions.publish("neutral")

	templateData = {
		'title' : 'A2 History 2',
	}
	return render_template(template, **templateData)

###############################################
################ Act2 History 4 ###############
###############################################
@app.route("/Activities/A2/history4/<action>")
def actionL1_A2_4(action):
	template = 'level3Memory4.html'
	if action == "segment1":
		pubSpeaker.publish("banheiro_jose")
	elif action == "segment2":
		pubSpeaker.publish("jose_banheiro_2")
	elif action == "segment3":
		pubSpeaker.publish("jose_banheiro_3")
	elif action == "segment4":
		pubSpeaker.publish("jose_banheiro_4")
	elif action == "segment5":
		pubSpeaker.publish("jose_banheiro_5")
	elif action == "segment6":
		pubSpeaker.publish("jose_esta_limpo_coloca_pijama")

	elif action == "stop":
		pubSpeakerAction.publish("stop")
	elif action == "pause":
		pubSpeakerAction.publish("pause")
	elif action == "play":
		pubSpeakerAction.publish("unpause")

	elif action == "question1":
		pubSpeaker.publish("jose_banheiro_p1")
	elif action == "question2":
		pubSpeaker.publish("jose_banheiro_p2")
	elif action == "question3":
		pubSpeaker.publish("jose_banheiro_p3")

	elif action == "gj1":
		pubEmotions.publish("happy")
		pubSpeaker.publish("muito_bem")
	elif action == "gj2":
		pubEmotions.publish("happy")
		pubSpeaker.publish("parabens_02")
	elif action == "gj3":
		pubEmotions.publish("happy")
		pubSpeaker.publish("que_bom")
	elif action == "gj4":
		pubEmotions.publish("happy")
		pubSpeaker.publish("conseguiu")
	elif action == "gj5":
		pubEmotions.publish("happy")
		pubSpeaker.publish("fez_muito_bem")
	elif action == "gj6":
		pubEmotions.publish("happy")
		pubSpeaker.publish("parabens")
	elif action == "gj7":
		pubEmotions.publish("happy")
		pubSpeaker.publish("excelente")
	elif action == "gj8":
		pubEmotions.publish("happy")
		pubSpeaker.publish("continue_brincando")
	elif action == "nt1":
		pubEmotions.publish("sad")
		pubSpeaker.publish("tente_de_novo")
	elif action == "nt2":
		pubEmotions.publish("sad")
		pubSpeaker.publish("continue_brincando")
	elif action == "nt3":
		pubEmotions.publish("sad")
		pubSpeaker.publish("quase_conseguiu")
	elif action == "nt4":
		pubEmotions.publish("happy")
		pubSpeaker.publish("continue_assim")
	elif action=="nt6":
		pubEmotions.publish("happy")
		pubSpeaker.publish("continue_dancando")
	elif action=="nt7":
		pubEmotions.publish("sad")
		pubSpeaker.publish("nao_consigo_ouvir")
	elif action=="nt9":
		pubEmotions.publish("happy")
		pubSpeaker.publish("com_todo_prazer")
	elif action=="nt10":
		pubEmotions.publish("sad")
		pubSpeaker.publish("sente-se")
	elif action=="nt11":
		pubEmotions.publish("sad")
		pubSpeaker.publish("venha")
	elif action=="nt12":
		pubEmotions.publish("sad")
		pubSpeaker.publish("preste_atencao_em_mim")
	elif action == "me_duele":
		pubSpeaker.publish("assim_nao_voce_Esta_me_machucando")
		time.sleep(0.5)
		pubEmotions.publish("angry")
	elif action == "lastimar":
		pubSpeaker.publish("assim_nao_voce_Esta_me_machucando")
		time.sleep(0.5)
		pubEmotions.publish("sad")
	elif action=="t1":
		#pubEmotions.publish("talk")
		pubSpeaker.publish("esta_tudo_bem")
	elif action=="t2":
		#pubEmotions.publish("talk")
		pubSpeaker.publish("sem_problema")
	elif action=="t4":
		#pubEmotions.publish("talk")
		pubSpeaker.publish("olhe_pra_mim")
	elif action=="t5":
		#pubEmotions.publish("talk")
		pubSpeaker.publish("nao_grite")
	elif action=="t6":
		#pubEmotions.publish("talk")
		pubSpeaker.publish("nao_chore")
	elif action=="t10":
		#pubEmotions.publish("talk")
		pubSpeaker.publish("diga_por_favor")

	elif action == "happy":
		pubEmotions.publish("happy")
	elif action == "sad":
		pubEmotions.publish("sad")
	elif action == "angry":
		pubEmotions.publish("angry")
	elif action == "surprise":
		pubEmotions.publish("surprise")
	elif action == "neutral":
		pubEmotions.publish("neutral")
		
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
	if action == "segment1":
		pubSpeaker.publish("jose_assustado_1")
	elif action == "segment2":
		pubSpeaker.publish("jose_assustado_2")
	elif action == "segment3":
		pubSpeaker.publish("jose_treme_medo")
	elif action == "segment4":
		pubSpeaker.publish("jose_assustado_4")
	elif action == "segment5":
		pubSpeaker.publish("jose_grita_socorro")
	elif action == "segment6":
		pubSpeaker.publish("jose_assustado_6")

	elif action == "stop":
		pubSpeakerAction.publish("stop")
	elif action == "pause":
		pubSpeakerAction.publish("pause")
	elif action == "play":
		pubSpeakerAction.publish("unpause")

	elif action == "question1":
		pubSpeaker.publish("jose_assustado_p1")
	elif action == "question2":
		pubSpeaker.publish("jose_assustado_p2")
	elif action == "question3":
		pubSpeaker.publish("jose_assustado_p3")

	elif action == "gj1":
		pubEmotions.publish("happy")
		pubSpeaker.publish("muito_bem")
	elif action == "gj2":
		pubEmotions.publish("happy")
		pubSpeaker.publish("parabens_02")
	elif action == "gj3":
		pubEmotions.publish("happy")
		pubSpeaker.publish("que_bom")
	elif action == "gj4":
		pubEmotions.publish("happy")
		pubSpeaker.publish("conseguiu")
	elif action == "gj5":
		pubEmotions.publish("happy")
		pubSpeaker.publish("fez_muito_bem")
	elif action == "gj6":
		pubEmotions.publish("happy")
		pubSpeaker.publish("parabens")
	elif action == "gj7":
		pubEmotions.publish("happy")
		pubSpeaker.publish("excelente")
	elif action == "gj8":
		pubEmotions.publish("happy")
		pubSpeaker.publish("continue_brincando")
	elif action == "nt1":
		pubEmotions.publish("sad")
		pubSpeaker.publish("tente_de_novo")
	elif action == "nt2":
		pubEmotions.publish("sad")
		pubSpeaker.publish("continue_brincando")
	elif action == "nt3":
		pubEmotions.publish("sad")
		pubSpeaker.publish("quase_conseguiu")
	elif action == "nt4":
		pubEmotions.publish("happy")
		pubSpeaker.publish("continue_assim")
	elif action=="nt6":
		pubEmotions.publish("happy")
		pubSpeaker.publish("continue_dancando")
	elif action=="nt7":
		pubEmotions.publish("sad")
		pubSpeaker.publish("nao_consigo_ouvir")
	elif action=="nt9":
		pubEmotions.publish("happy")
		pubSpeaker.publish("com_todo_prazer")
	elif action=="nt10":
		pubEmotions.publish("sad")
		pubSpeaker.publish("sente-se")
	elif action=="nt11":
		pubEmotions.publish("sad")
		pubSpeaker.publish("venha")
	elif action=="nt12":
		pubEmotions.publish("sad")
		pubSpeaker.publish("preste_atencao_em_mim")
	elif action == "me_duele":
		pubSpeaker.publish("assim_nao_voce_Esta_me_machucando")
		time.sleep(0.5)
		pubEmotions.publish("angry")
	elif action == "lastimar":
		pubSpeaker.publish("assim_nao_voce_Esta_me_machucando")
		time.sleep(0.5)
		pubEmotions.publish("sad")
	elif action=="t1":
		#pubEmotions.publish("talk")
		pubSpeaker.publish("esta_tudo_bem")
	elif action=="t2":
		#pubEmotions.publish("talk")
		pubSpeaker.publish("sem_problema")
	elif action=="t4":
		#pubEmotions.publish("talk")
		pubSpeaker.publish("olhe_pra_mim")
	elif action=="t5":
		#pubEmotions.publish("talk")
		pubSpeaker.publish("nao_grite")
	elif action=="t6":
		#pubEmotions.publish("talk")
		pubSpeaker.publish("nao_chore")
	elif action=="t10":
		#pubEmotions.publish("talk")
		pubSpeaker.publish("diga_por_favor")

	elif action == "happy":
		pubEmotions.publish("happy")
	elif action == "sad":
		pubEmotions.publish("sad")
	elif action == "angry":
		pubEmotions.publish("angry")
	elif action == "surprise":
		pubEmotions.publish("surprise")
	elif action == "neutral":
		pubEmotions.publish("neutral")

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
	elif action == "dance1":
		pubSpeaker.publish("danca_comigo")
	elif action == "dance":
		pubSpeaker.publish("vamos_dancar")

	elif action == "round1":
		pubSpeaker.publish("musica1")
	elif action == "round2":
		pubSpeaker.publish("musica2")
	elif action == "round3":
		pubSpeaker.publish("musica3")
	elif action == "song1":
		pubMovements.publish("dance")
		pubSpeaker.publish("Pista_pop")
	elif action == "song2":
		pubMovements.publish("dance")
		pubSpeaker.publish("Pista_electronica")
	elif action == "song3":
		pubMovements.publish("dance")
		pubSpeaker.publish("pista_mapale")
	elif action == "song4":
		pubMovements.publish("dance")
		pubSpeaker.publish("pista_de_salsa")
	elif action == "song5":
		pubMovements.publish("dance")
		pubSpeaker.publish("pista_de_merengue")
	elif action == "song6":
		pubMovements.publish("dance")
		pubSpeaker.publish("Pista_Reggaeton_1")
	elif action == "song8":
		pubMovements.publish("dance")
		pubSpeaker.publish("Pista_aerobicos")
	elif action == "song13":
		pubMovements.publish("dance")
		pubSpeaker.publish("Pista_Cumbia")
	
	elif action == "stop":
		pubSpeakerAction.publish("stop")
	elif action == "pause":
		pubSpeakerAction.publish("pause")
	elif action == "play":
		pubSpeakerAction.publish("unpause")

	elif action == "gj1":
		pubEmotions.publish("happy")
		pubSpeaker.publish("muito_bem")
	elif action == "gj2":
		pubEmotions.publish("happy")
		pubSpeaker.publish("parabens_02")
	elif action == "gj3":
		pubEmotions.publish("happy")
		pubSpeaker.publish("que_bom")
	elif action == "gj4":
		pubEmotions.publish("happy")
		pubSpeaker.publish("conseguiu")
	elif action == "gj5":
		pubEmotions.publish("happy")
		pubSpeaker.publish("fez_muito_bem")
	elif action == "gj6":
		pubEmotions.publish("happy")
		pubSpeaker.publish("parabens")
	elif action == "gj7":
		pubEmotions.publish("happy")
		pubSpeaker.publish("excelente")
	elif action == "gj8":
		pubEmotions.publish("happy")
		pubSpeaker.publish("continue_brincando")
	elif action == "nt1":
		pubEmotions.publish("sad")
		pubSpeaker.publish("tente_de_novo")
	elif action == "nt2":
		pubEmotions.publish("sad")
		pubSpeaker.publish("continue_brincando")
	elif action == "nt3":
		pubEmotions.publish("sad")
		pubSpeaker.publish("quase_conseguiu")
	elif action == "nt4":
		pubEmotions.publish("happy")
		pubSpeaker.publish("continue_assim")
	elif action=="nt6":
		pubEmotions.publish("happy")
		pubSpeaker.publish("continue_dancando")
	elif action=="nt7":
		pubEmotions.publish("sad")
		pubSpeaker.publish("nao_consigo_ouvir")
	elif action=="nt9":
		pubEmotions.publish("happy")
		pubSpeaker.publish("com_todo_prazer")
	elif action=="nt10":
		pubEmotions.publish("sad")
		pubSpeaker.publish("sente-se")
	elif action=="nt11":
		pubEmotions.publish("sad")
		pubSpeaker.publish("venha")
	elif action=="nt12":
		pubEmotions.publish("sad")
		pubSpeaker.publish("preste_atencao_em_mim")
	elif action == "me_duele":
		pubSpeaker.publish("assim_nao_voce_Esta_me_machucando")
		time.sleep(0.5)
		pubEmotions.publish("angry")
	elif action == "lastimar":
		pubSpeaker.publish("assim_nao_voce_Esta_me_machucando")
		time.sleep(0.5)
		pubEmotions.publish("sad")
	elif action=="t1":
		#pubEmotions.publish("talk")
		pubSpeaker.publish("esta_tudo_bem")
	elif action=="t2":
		#pubEmotions.publish("talk")
		pubSpeaker.publish("sem_problema")
	elif action=="t4":
		#pubEmotions.publish("talk")
		pubSpeaker.publish("olhe_pra_mim")
	elif action=="t5":
		#pubEmotions.publish("talk")
		pubSpeaker.publish("nao_grite")
	elif action=="t6":
		#pubEmotions.publish("talk")
		pubSpeaker.publish("nao_chore")
	elif action=="t10":
		#pubEmotions.publish("talk")
		pubSpeaker.publish("diga_por_favor")


	elif action == "happy":
		pubEmotions.publish("happy")
	elif action == "sad":
		pubEmotions.publish("sad")
	elif action == "angry":
		pubEmotions.publish("angry")
	elif action == "surprise":
		pubEmotions.publish("surprise")
	elif action == "neutral":
		pubEmotions.publish("neutral")

	
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


	elif action == "song1":
		pubSpeaker.publish("canta1")
	elif action == "song2":
		pubSpeaker.publish("canta2")
	elif action == "song3":
		pubSpeaker.publish("canta3")
		
	elif action == "stop":
		pubSpeakerAction.publish("stop")
	elif action == "pause":
		pubSpeakerAction.publish("pause")
	elif action == "play":
		pubSpeakerAction.publish("unpause")

	elif action == "gj1":
		pubEmotions.publish("happy")
		pubSpeaker.publish("muito_bem")
	elif action == "gj2":
		pubEmotions.publish("happy")
		pubSpeaker.publish("parabens_02")
	elif action == "gj3":
		pubEmotions.publish("happy")
		pubSpeaker.publish("que_bom")
	elif action == "gj4":
		pubEmotions.publish("happy")
		pubSpeaker.publish("conseguiu")
	elif action == "gj5":
		pubEmotions.publish("happy")
		pubSpeaker.publish("fez_muito_bem")
	elif action == "gj6":
		pubEmotions.publish("happy")
		pubSpeaker.publish("parabens")
	elif action == "gj7":
		pubEmotions.publish("happy")
		pubSpeaker.publish("excelente")
	elif action == "gj8":
		pubEmotions.publish("happy")
		pubSpeaker.publish("continue_brincando")
	elif action == "nt1":
		pubEmotions.publish("sad")
		pubSpeaker.publish("tente_de_novo")
	elif action == "nt2":
		pubEmotions.publish("sad")
		pubSpeaker.publish("continue_brincando")
	elif action == "nt3":
		pubEmotions.publish("sad")
		pubSpeaker.publish("quase_conseguiu")
	elif action == "nt4":
		pubEmotions.publish("happy")
		pubSpeaker.publish("continue_assim")
	elif action=="nt6":
		pubEmotions.publish("happy")
		pubSpeaker.publish("continue_dancando")
	elif action=="nt7":
		pubEmotions.publish("sad")
		pubSpeaker.publish("nao_consigo_ouvir")
	elif action=="nt9":
		pubEmotions.publish("happy")
		pubSpeaker.publish("com_todo_prazer")
	elif action=="nt10":
		pubEmotions.publish("sad")
		pubSpeaker.publish("sente-se")
	elif action=="nt11":
		pubEmotions.publish("sad")
		pubSpeaker.publish("venha")
	elif action=="nt12":
		pubEmotions.publish("sad")
		pubSpeaker.publish("preste_atencao_em_mim")
	elif action == "me_duele":
		pubSpeaker.publish("assim_nao_voce_Esta_me_machucando")
		time.sleep(0.5)
		pubEmotions.publish("angry")
	elif action == "lastimar":
		pubSpeaker.publish("assim_nao_voce_Esta_me_machucando")
		time.sleep(0.5)
		pubEmotions.publish("sad")
	elif action=="t1":
		#pubEmotions.publish("talk")
		pubSpeaker.publish("esta_tudo_bem")
	elif action=="t2":
		#pubEmotions.publish("talk")
		pubSpeaker.publish("sem_problema")
	elif action=="t4":
		#pubEmotions.publish("talk")
		pubSpeaker.publish("olhe_pra_mim")
	elif action=="t5":
		#pubEmotions.publish("talk")
		pubSpeaker.publish("nao_grite")
	elif action=="t6":
		#pubEmotions.publish("talk")
		pubSpeaker.publish("nao_chore")
	elif action=="t10":
		#pubEmotions.publish("talk")
		pubSpeaker.publish("diga_por_favor")

	elif action == "happy":
		pubEmotions.publish("happy")
	elif action == "sad":
		pubEmotions.publish("sad")
	elif action == "angry":
		pubEmotions.publish("angry")
	elif action == "surprise":
		pubEmotions.publish("surprise")
	elif action == "neutral":
		pubEmotions.publish("neutral")

	
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

	elif action == "story1":
		pubSpeaker.publish("Story1")

	elif action == "question1_1":
		pubSpeaker.publish("story1_p1")
	elif action == "question1_2":
		pubSpeaker.publish("story1_p2")
	elif action == "question1_3":
		pubSpeaker.publish("story1_p3")
	
	elif action == "story2":
		pubSpeaker.publish("Story2")

	elif action == "question2_1":
		pubSpeaker.publish("story2_p1")
	elif action == "question2_2":
		pubSpeaker.publish("story2_p2")
	elif action == "question2_3":
		pubSpeaker.publish("story2_p3")
		
	elif action == "story3":
		pubSpeaker.publish("Story3")

	elif action == "question3_1":
		pubSpeaker.publish("story3_p1")
	elif action == "question3_2":
		pubSpeaker.publish("story3_p2")
	elif action == "question3_3":
		pubSpeaker.publish("story3_p3")
		

	elif action == "stop":
		pubSpeakerAction.publish("stop")
	elif action == "pause":
		pubSpeakerAction.publish("pause")
	elif action == "play":
		pubSpeakerAction.publish("unpause")

	elif action == "gj1":
		pubEmotions.publish("happy")
		pubSpeaker.publish("muito_bem")
	elif action == "gj2":
		pubEmotions.publish("happy")
		pubSpeaker.publish("parabens_02")
	elif action == "gj3":
		pubEmotions.publish("happy")
		pubSpeaker.publish("que_bom")
	elif action == "gj4":
		pubEmotions.publish("happy")
		pubSpeaker.publish("conseguiu")
	elif action == "gj5":
		pubEmotions.publish("happy")
		pubSpeaker.publish("fez_muito_bem")
	elif action == "gj6":
		pubEmotions.publish("happy")
		pubSpeaker.publish("parabens")
	elif action == "gj7":
		pubEmotions.publish("happy")
		pubSpeaker.publish("excelente")
	elif action == "gj8":
		pubEmotions.publish("happy")
		pubSpeaker.publish("continue_brincando")
	elif action == "nt1":
		pubEmotions.publish("sad")
		pubSpeaker.publish("tente_de_novo")
	elif action == "nt2":
		pubEmotions.publish("sad")
		pubSpeaker.publish("continue_brincando")
	elif action == "nt3":
		pubEmotions.publish("sad")
		pubSpeaker.publish("quase_conseguiu")
	elif action == "nt4":
		pubEmotions.publish("happy")
		pubSpeaker.publish("continue_assim")
	elif action=="nt6":
		pubEmotions.publish("happy")
		pubSpeaker.publish("continue_dancando")
	elif action=="nt7":
		pubEmotions.publish("sad")
		pubSpeaker.publish("nao_consigo_ouvir")
	elif action=="nt9":
		pubEmotions.publish("happy")
		pubSpeaker.publish("com_todo_prazer")
	elif action=="nt10":
		pubEmotions.publish("sad")
		pubSpeaker.publish("sente-se")
	elif action=="nt11":
		pubEmotions.publish("sad")
		pubSpeaker.publish("venha")
	elif action=="nt12":
		pubEmotions.publish("sad")
		pubSpeaker.publish("preste_atencao_em_mim")
	elif action == "me_duele":
		pubSpeaker.publish("assim_nao_voce_Esta_me_machucando")
		time.sleep(0.5)
		pubEmotions.publish("angry")
	elif action == "lastimar":
		pubSpeaker.publish("assim_nao_voce_Esta_me_machucando")
		time.sleep(0.5)
		pubEmotions.publish("sad")
	elif action=="t1":
		#pubEmotions.publish("talk")
		pubSpeaker.publish("esta_tudo_bem")
	elif action=="t2":
		#pubEmotions.publish("talk")
		pubSpeaker.publish("sem_problema")
	elif action=="t4":
		#pubEmotions.publish("talk")
		pubSpeaker.publish("olhe_pra_mim")
	elif action=="t5":
		#pubEmotions.publish("talk")
		pubSpeaker.publish("nao_grite")
	elif action=="t6":
		#pubEmotions.publish("talk")
		pubSpeaker.publish("nao_chore")
	elif action=="t10":
		#pubEmotions.publish("talk")
		pubSpeaker.publish("diga_por_favor")

	elif action == "happy":
		pubEmotions.publish("happy")
	elif action == "sad":
		pubEmotions.publish("sad")
	elif action == "angry":
		pubEmotions.publish("angry")
	elif action == "surprise":
		pubEmotions.publish("surprise")
	elif action == "neutral":
		pubEmotions.publish("neutral")

	templateData = {
		'title' : 'A5',
	}
	return render_template(template, **templateData)
	
	
##############################################
################ Action_Hug ###############
##############################################
@app.route("/Activities/A7/<action>")
def Hug(action):
	template = "ActivitiesHug.html"
	if action == "sayHug":		  #Abrazos
		pubSpeaker.publish("da_um_abraco")
	elif action == "hugOpen":
		pubMovements.publish("hugOpen1")
	elif action == "hugClose":
		pubMovements.publish("hugClose")
	elif action == "hugEnd":
		pubMovements.publish("hugNeutral")
	elif action == "thanks":
		pubEmotions.publish("happy")
		pubSpeaker.publish("obrigado")


	templateData = {
		'title' : 'Abrazos',
	}
	return render_template(template, **templateData)


if __name__ == "__main__":
   app.run(host='0.0.0.0', port=5000, debug=True)
