#! /usr/bin/env python3
# -*- coding: utf-8 -*-
import time
from datetime import datetime
import rospy
import subprocess

from flask import Flask, render_template, request, jsonify, redirect, url_for
import threading

from std_msgs.msg import Float64
from std_msgs.msg import String
from std_msgs.msg import Bool

pubEmotions = rospy.Publisher('/emotions', String, queue_size = 10)
pubSpeaker = rospy.Publisher('/speaker', String, queue_size = 10)
pubSpeakerAction = rospy.Publisher('/speakerAction', String, queue_size = 15)
pubMovements = rospy.Publisher('/movements', String, queue_size = 5)
pubCastorSystem = rospy.Publisher('/castor_system', String, queue_size = 5)
#pubText = rospy.Publisher('/text_input', String, queue_size = 5)

class Acciones():
    def Main_Menu(self, action):
        if action == "greet":
            pubMovements.publish("wave")
            pubEmotions.publish("happy")
            pubSpeaker.publish("me_chamo_castor")
            #print(f"Frase: {'me_chamo_castor'}")  # Debugging line
        elif action == "greet2":
            pubSpeaker.publish("ola_castor")
            #print(f"Frase: {'ola_castor'}")  # Debugging line
        elif action == "greet_miguel":
            pubSpeaker.publish("ola_miguel")
            #print(f"Frase: {'ola_miguel'}")  # Debugging line
        elif action == "miguel":
            pubSpeaker.publish("miguel")
            #print(f"Frase: {'miguel'}")  # Debugging line
        elif action == "lets_go":
            pubSpeaker.publish("vamos_brincar")
            #print(f"Frase: {'vamos_brincar'}")  # Debugging line
        elif action == "presentation1":
            pubEmotions.publish("happy")
            pubSpeaker.publish("castor_apresentacao")
            #print(f"Frase: {'castor_apresentacao'}")  # Debugging line
        elif action == "presentation2":
            pubEmotions.publish("happy")
            pubSpeaker.publish("Eu_gosto_de")
            #print(f"Frase: {'Eu_gosto_de'}")  # Debugging line
        elif action == "foto":
            pubSpeaker.publish("foto")
            #print(f"Frase: {'foto'}")  # Debugging line
        elif action == "bye":
            pubMovements.publish("wave")
            time.sleep(0.5)
            pubSpeaker.publish("tchau_amigo")
            #print(f"Frase: {'tchau_amigo'}")  # Debugging line
        elif action == "bye2":
            pubMovements.publish("wave")
            time.sleep(0.5)
            pubSpeaker.publish("tchau_amiga")
            #print(f"Frase: {'tchau_amiga'}")  # Debugging line
        elif action == "byeamigos":
            pubMovements.publish("wave")
            time.sleep(0.5)
            pubSpeaker.publish("tchau_amigos")
            #print(f"Frase: {'tchau_amigos'}")  # Debugging line
        elif action == "final":
            pubSpeaker.publish("tudo_hoje")
            #print(f"Frase: {'tudo_hoje'}")  # Debugging line
        elif action == "thanks":
            pubSpeaker.publish("obrigado_brincar_hoje")
            #print(f"Frase: {'obrigado_brincar_hoje'}")  # Debugging line
        elif action == "happyday":
            pubSpeaker.publish("tenha_um_otimo_dia")
            #print(f"Frase: {'tenha_um_otimo_dia'}")  # Debugging line
        elif action == "hifiveinstruction":
            pubSpeaker.publish("Hi-5")
            #print(f"Frase: {'Hi-5'}")  # Debugging line
        elif action == "highfive":
            pubMovements.publish("highfive")
            #print(f"Frase: {'highfive'}")  # Debugging line
        elif action == "bajar_brazo":
            pubMovements.publish("down_highfive")
            #print(f"Frase: {'down_highfive'}")  # Debugging line
        
    def emotions(self, action):
        if action == "happy":
            #print(f"Emotion: {action}")  # Debugging line

            pubEmotions.publish("happy")
        elif action == "sad":
            #print(f"Emotion: {action}")  # Debugging line
            pubEmotions.publish("sad")
        elif action == "angry":
            #print(f"Emotion: {action}")  # Debugging line
            pubEmotions.publish("angry")
        elif action == "surprise":
            #print(f"Emotion: {action}")  # Debugging line
            pubEmotions.publish("surprise")
        elif action == "neutral":
            #print(f"Emotion: {action}")  # Debugging line
            pubEmotions.publish("neutral")

    def Frases_de_incentivo(self, action):
        if action == "nt1":
            #print(f"Frase: {'tente_de_novo'}")  # Debugging line
            pubEmotions.publish("sad")
            pubSpeaker.publish("tente_de_novo")
        elif action == "nt2":
            pubEmotions.publish("sad")
            pubSpeaker.publish("continue_brincando")
            #print(f"Frase: {'continue_brincando'}")  # Debugging line
        elif action == "nt3":
            pubEmotions.publish("sad")
            pubSpeaker.publish("quase_conseguiu")
            #print(f"Frase: {'quase_conseguiu'}")  # Debugging line
        elif action == "nt4":
            pubEmotions.publish("happy")
            pubSpeaker.publish("continue_assim")
            #print(f"Frase: {'continue_assim'}")  # Debugging line
        elif action=="nt6":
            pubEmotions.publish("happy")
            pubSpeaker.publish("continue_dancando")
            #print(f"Frase: {'continue_dancando'}")  # Debugging line
        elif action=="nt7":
            pubEmotions.publish("sad")
            pubSpeaker.publish("nao_consigo_ouvir")
            #print(f"Frase: {'nao_consigo_ouvir'}")  # Debugging line
        elif action=="nt9":
            pubEmotions.publish("happy")
            pubSpeaker.publish("com_todo_prazer")
            #print(f"Frase: {'com_todo_prazer'}")  # Debugging line        
        elif action=="nt10":
            pubEmotions.publish("sad")
            pubSpeaker.publish("sente-se")
            #print(f"Frase: {'sente-se'}")  # Debugging line
        elif action=="nt11":
            pubEmotions.publish("sad")
            pubSpeaker.publish("venha")
            #print(f"Frase: {'venha'}")  # Debugging line
        elif action=="nt12":
            pubEmotions.publish("sad")
            pubSpeaker.publish("preste_atencao_em_mim")
            #print(f"Frase: {'preste_atencao_em_mim'}")  # Debugging line
        elif action == "me_duele":
            pubSpeaker.publish("assim_nao_voce_Esta_me_machucando")
            time.sleep(0.5)
            pubEmotions.publish("angry")
            #print(f"Frase: {'assim_nao_voce_Esta_me_machucando'}")  # Debugging line
        elif action == "lastimar":
            pubSpeaker.publish("assim_nao_voce_Esta_me_machucando")
            time.sleep(0.5)
            pubEmotions.publish("sad")
            #print(f"Frase: {'assim_nao_voce_Esta_me_machucando'}")  # Debugging line
        elif action=="t1":
            pubEmotions.publish("talk")
            pubSpeaker.publish("esta_tudo_bem")
            #print(f"Frase: {'esta_tudo_bem'}")  # Debugging line
        elif action=="t2":
            pubEmotions.publish("talk")
            pubSpeaker.publish("sem_problema")
            #print(f"Frase: {'sem_problema'}")  # Debugging line
        elif action=="t4":
            pubEmotions.publish("talk")
            pubSpeaker.publish("olhe_pra_mim")
            #print(f"Frase: {'olhe_pra_mim'}")  # Debugging line
        elif action=="t5":
            pubEmotions.publish("talk")
            pubSpeaker.publish("nao_grite")
            #print(f"Frase: {'nao_grite'}")  # Debugging line
        elif action=="t6":
            pubEmotions.publish("talk")
            pubSpeaker.publish("nao_chore")
            #print(f"Frase: {'nao_chore'}")  # Debugging line
        elif action=="t10":
            pubEmotions.publish("talk")
            pubSpeaker.publish("diga_por_favor")
            #print(f"Frase: {'diga_por_favor'}")  # Debugging line     

    def Frases_objetivo_alcanzado(self, action):
        if action == "gj1":
            pubEmotions.publish("happy")
            pubSpeaker.publish("muito_bem")
            #print(f"Frase: {'muito_bem'}")  # Debugging line
        elif action == "gj2":
            pubEmotions.publish("happy")
            pubSpeaker.publish("parabens_02")
            #print(f"Frase: {'parabens_02'}")  # Debugging line
        elif action == "gj3":
            pubEmotions.publish("happy")
            pubSpeaker.publish("que_bom")
            #print(f"Frase: {'que_bom'}")  # Debugging line
        elif action == "gj4":
            pubEmotions.publish("happy")
            pubSpeaker.publish("conseguiu")
            #print(f"Frase: {'conseguiu'}")  # Debugging line 
        elif action == "gj5":
            pubEmotions.publish("happy")
            pubSpeaker.publish("fez_muito_bem")
            #print(f"Frase: {'fez_muito_bem'}")  # Debugging line
        elif action == "gj6":
            pubEmotions.publish("happy")
            pubSpeaker.publish("parabens")
            #print(f"Frase: {'parabens'}")  # Debugging line
        elif action == "gj7":
            pubEmotions.publish("happy")
            pubSpeaker.publish("excelente")
            #print(f"Frase: {'excelente'}")  # Debugging line
        elif action == "gj8":
            pubEmotions.publish("happy")
            pubSpeaker.publish("continue_brincando")
            #print(f"Frase: {'continue_brincando'}")  # Debugging line
            
    def BodyParts(self, action):
        if action == "sayBody":
            pubSpeaker.publish("partes_do_corpo")
            #print(f"Frase: {'partes_do_corpo'}")  # Debugging line
        elif action == "pointHead":
            pubMovements.publish("pointHead")
            time.sleep(0.5)
            pubSpeaker.publish("onde_esta_minha_cabeca")
            #print(f"Frase: {'onde_esta_minha_cabeca'}")  # Debugging line
        elif action == "pointEyes":
            pubMovements.publish("pointEyes")
            time.sleep(0.5)
            pubSpeaker.publish("onde_estao_meus_olhos")
            #print(f"Frase: {'onde_estao_meus_olhos'}")  # Debugging line
        elif action == "pointNose":
            pubMovements.publish("pointNose")
            time.sleep(0.5)
            pubSpeaker.publish("onde_esta_meu_nariz")
            #print(f"Frase: {'onde_esta_meu_nariz'}")  # Debugging line
        elif action == "pointMouth":
            pubMovements.publish("pointMouth")
            time.sleep(0.5)
            pubSpeaker.publish("onde_esta_minha_boca")
            #print(f"Frase: {'onde_esta_minha_boca'}")  # Debugging line
        elif action == "botones":
            pubMovements.publish("pointMouth")
            time.sleep(0.5)
            pubSpeaker.publish("toca_botoes")
            #print(f"Frase: {'toca_botoes'}")  # Debugging line

        elif action == "askHead":
            pubSpeaker.publish("aponte_sua_cabeca")
            #print(f"Frase: {'aponte_sua_cabeca'}")  # Debugging line
        elif action == "askEyes":
            pubSpeaker.publish("aponte_seus_olhos")
            #print(f"Frase: {'aponte_seus_olhos'}")  # Debugging line
        elif action == "askNose":
            pubSpeaker.publish("aponte_seu_nariz")
            #print(f"Frase: {'aponte_seu_nariz'}")  # Debugging line
        elif action == "askMouth":
            pubSpeaker.publish("aponte_sua_boca")
            #print(f"Frase: {'aponte_sua_boca'}")  # Debugging line

    def CastorEmotions(self, action):
        if action == "ifeel_happy":
            pubEmotions.publish("talk")
            pubSpeaker.publish("me_sinto_feliz")
            #print(f"Frase: {'me_sinto_feliz'}")  # Debugging line
        elif action == "ifeel_sad":
            pubEmotions.publish("talk")
            pubSpeaker.publish("me_sinto_triste")
            #print(f"Frase: {'me_sinto_triste'}")  # Debugging line
        elif action == "ifeel_angry":
            pubEmotions.publish("talk")
            pubSpeaker.publish("me_sinto_irritado")
            #print(f"Frase: {'me_sinto_irritado'}")  # Debugging line
        elif action == "ifeel_surprise":
            pubEmotions.publish("talk")
            pubSpeaker.publish("estou_surpreso")
            #print(f"Frase: {'estou_surpreso'}")  # Debugging line
        elif action == "howifeel":
            pubSpeaker.publish("como_acha_me_sentindo")
            #print(f"Frase: {'como_acha_me_sentindo'}")  # Debugging line
        elif action == "emotion":
            pubSpeaker.publish("adivinha_sentindo")
            #print(f"Frase: {'adivinha_sentindo'}")  # Debugging line
        elif action == "andnow":
            pubSpeaker.publish("agora_sim_como_me_sinto")
            #print(f"Frase: {'agora_sim_como_me_sinto'}")  # Debugging line

    def Maths(self, action):
        if action == "count":
            pubEmotions.publish("talk")
            pubSpeaker.publish("contar_um_a_dez")
            #print(f"Frase: {'contar_um_a_dez'}")  # Debugging line
        elif action == "explain":
            pubEmotions.publish("talk")
            pubSpeaker.publish("pode_contar_comigo")
            #print(f"Frase: {'pode_contar_comigo'}")  # Debugging line
        elif action == "one":
            #pubEmotions.publish("talk")
            pubSpeaker.publish("um")
            #print(f"Frase: {'um'}")  # Debugging line
        elif action == "two":
            #pubEmotions.publish("talk")
            pubSpeaker.publish("dois")
            #print(f"Frase: {'dois'}")  # Debugging line
        elif action == "tree":
            #pubEmotions.publish("talk")
            pubSpeaker.publish("tres")
            #print(f"Frase: {'tres'}")  # Debugging line
        elif action == "four":
            #pubEmotions.publish("talk")
            pubSpeaker.publish("quatro")
            #print(f"Frase: {'quatro'}")  # Debugging line
        elif action == "five":
            #pubEmotions.publish("talk")
            pubSpeaker.publish("cinco")
            #print(f"Frase: {'cinco'}")  # Debugging line
        elif action == "six":
            #pubEmotions.publish("talk")
            pubSpeaker.publish("seis")
            #print(f"Frase: {'seis'}")  # Debugging line
        elif action == "seven":
            #pubEmotions.publish("talk")
            pubSpeaker.publish("sete")
            #print(f"Frase: {'sete'}")  # Debugging line
        elif action == "eight":
            #pubEmotions.publish("talk")
            pubSpeaker.publish("oito")
            #print(f"Frase: {'oito'}")  # Debugging line
        elif action == "nine":
            #pubEmotions.publish("talk")
            pubSpeaker.publish("nove")
            #print(f"Frase: {'nove'}")  # Debugging line
        elif action == "ten":
            #pubEmotions.publish("talk")
            pubSpeaker.publish("dez")
            #print(f"Frase: {'dez'}")  # Debugging line
        elif action == "sum":
            pubEmotions.publish("talk")
            pubSpeaker.publish("vc_sabe_somar")
            #print(f"Frase: {'vc_sabe_somar'}")  # Debugging line
        elif action == "substraction":
            pubEmotions.publish("talk")
            pubSpeaker.publish("vc_sabe_subtrair")
            #print(f"Frase: {'vc_sabe_subtrair'}")  # Debugging line
        elif action == "howmuch":
            pubEmotions.publish("talk")
            pubSpeaker.publish("quanto_eh")
            #print(f"Frase: {'quanto_eh'}")  # Debugging line
        elif action == "plus":
            pubEmotions.publish("talk")
            pubSpeaker.publish("mais")
            #print(f"Frase: {'mais'}")  # Debugging line
        elif action == "less":
            pubEmotions.publish("talk")
            pubSpeaker.publish("menos")
            #print(f"Frase: {'menos'}")  # Debugging line

    def Conversation(self, action):
        if action == "your_name":
            pubEmotions.publish("talk")
            pubSpeaker.publish("Como_seu_nome")
            #print(f"Frase: {'Como_seu_nome'}")  # Debugging line
        elif action == "your_name2":
            pubEmotions.publish("talk")
            pubSpeaker.publish("Qual_seu_nome")
            #print(f"Frase: {'Qual_seu_nome'}")  # Debugging line
        elif action == "nicemeet":
            pubEmotions.publish("talk")
            pubSpeaker.publish("prazer")
            #print(f"Frase: {'prazer'}")  # Debugging line
        elif action == "howRU":
            pubEmotions.publish("talk")
            pubSpeaker.publish("como_estao")
            #print(f"Frase: {'como_estao'}")  # Debugging line
        elif action == "name1":
            pubEmotions.publish("talk")
            pubSpeaker.publish("qual_meu_nome")
            #print(f"Frase: {'qual_meu_nome'}")  # Debugging line
        elif action == "color":
            pubEmotions.publish("talk")
            pubSpeaker.publish("qual_sua_cor_preferida")
            #print(f"Frase: {'qual_sua_cor_preferida'}")  # Debugging line
        elif action == "animalFav":
            pubEmotions.publish("talk")
            pubSpeaker.publish("animal_preferido") 
            #print(f"Frase: {'animal_preferido'}")  # Debugging line
        elif action == "cancionFav":
            pubEmotions.publish("talk")
            pubSpeaker.publish("musica_preferida")
            #print(f"Frase: {'musica_preferida'}")  # Debugging line
        elif action == "liketoplay":
            pubEmotions.publish("talk")
            pubSpeaker.publish("gosta_brincar")   
            #print(f"Frase: {'gosta_brincar'}")  # Debugging line
        elif action == "imGood":
            pubEmotions.publish("talk")
            pubSpeaker.publish("eu_tambem_estou_bem")
            #print(f"Frase: {'eu_tambem_estou_bem'}")  # Debugging line
        elif action == "name2":
            #pubEmotions.publish("talk")
            pubSpeaker.publish("meu_nome")
            #print(f"Frase: {'meu_nome'}")  # Debugging line
        elif action == "Metoo":
            #pubEmotions.publish("talk")
            pubSpeaker.publish("eu_tambem")
            #print(f"Frase: {'eu_tambem'}")  # Debugging line
        elif action == "Likewise":
            #pubEmotions.publish("talk")
            pubSpeaker.publish("o_meu_tambem")
            #print(f"Frase: {'o_meu_tambem'}")  # Debugging line
        elif action == "Likewise2":
            #pubEmotions.publish("talk")
            pubSpeaker.publish("a_minha_tambem")
            #print(f"Frase: {'a_minha_tambem'}")  # Debugging line
        elif action == "lo_tendre_en_cuenta":
            #pubEmotions.publish("talk")
            pubSpeaker.publish("leve_em_conta")
            #print(f"Frase: {'leve_em_conta'}")  # Debugging line
        elif action=="Hearthat":
            #pubEmotions.publish("talk")
            pubSpeaker.publish("fico_feliz_de_ouvir")	
            #print(f"Frase: {'fico_feliz_de_ouvir'}")  # Debugging line	 
        elif action == "ColorGreen":
            #pubEmotions.publish("talk")
            pubSpeaker.publish("cor_favorita")
            #print(f"Frase: {'cor_favorita'}")  # Debugging line
        elif action == "MianimalFav":
            #pubEmotions.publish("talk")
            pubSpeaker.publish("meu_animal_preferido")
            #print(f"Frase: {'meu_animal_preferido'}")  # Debugging line
        elif action == "DogSound":
            time.sleep(0.5)
            #pubEmotions.publish("talk")
            pubSpeaker.publish("cachorro_faz")
            #print(f"Frase: {'cachorro_faz'}")  # Debugging line
        elif action == "Favthings":
            #pubEmotions.publish("talk")
            pubSpeaker.publish("adoro_brincar_com_voces")    
            #print(f"Frase: {'adoro_brincar_com_voces'}")  # Debugging line
        elif action=="si":
            #pubEmotions.publish("talk")
            pubSpeaker.publish("sim")
            #print(f"Frase: {'sim'}")  # Debugging line
        elif action=="no":
            #pubEmotions.publish("talk")
            pubSpeaker.publish("nao")
            #print(f"Frase: {'nao'}")  # Debugging line
        elif action=="nose":
            #pubEmotions.publish("talk")
            pubSpeaker.publish("nao_sei")
            #print(f"Frase: {'nao_sei'}")  # Debugging line
        elif action=="thanks":
            #pubEmotions.publish("talk")
            pubSpeaker.publish("obrigado")
            #print(f"Frase: {'obrigado'}")  # Debugging line
        elif action=="yourwelcome":
            #pubEmotions.publish("talk")
            pubSpeaker.publish("de_nada")
            #print(f"Frase: {'de_nada'}")  # Debugging line

    def IndicacionesAct1(self, action):
        if action == "indication1":
            pubSpeaker.publish("pule")
            #print(f"Frase: {'pule'}")  # Debugging line
        elif action == "indication2":
            pubSpeaker.publish("aplauda_duas_vezes")
            #print(f"Frase: {'aplauda_duas_vezes'}")  # Debugging line
        elif action == "indication3":
            pubSpeaker.publish("uma_volta")
            #print(f"Frase: {'uma_volta'}")  # Debugging line
        elif action == "indication4":
            pubSpeaker.publish("abaixe_se")
            #print(f"Frase: {'abaixe_se'}")  # Debugging line
        elif action == "indication5":
            pubSpeaker.publish("faca_uma_cara_surpresa")
            #print(f"Frase: {'faca_uma_cara_surpresa'}")  # Debugging line
        elif action == "indication6":
            pubSpeaker.publish("cara_bravo")
            #print(f"Frase: {'cara_bravo'}")  # Debugging line
        elif action == "indication7":
            pubSpeaker.publish("cara_feliz")
            #print(f"Frase: {'cara_feliz'}")  # Debugging line
        elif action == "indication8":
            pubSpeaker.publish("cara_medo")
            #print(f"Frase: {'cara_medo'}")  # Debugging line
        elif action == "indication9":
            pubSpeaker.publish("cara_tristeza")
            #print(f"Frase: {'cara_tristeza'}")  # Debugging line
        elif action == "indication10":
            pubSpeaker.publish("toque_boca")
            #print(f"Frase: {'toque_boca'}")  # Debugging line
        elif action == "indication11":
            pubSpeaker.publish("toque_cotovelos")
            #print(f"Frase: {'toque_cotovelos'}")  # Debugging line
        elif action == "indication12":
            pubSpeaker.publish("toque_nariz")
            #print(f"Frase: {'toque_nariz'}")  # Debugging line
        elif action == "indication13":
            pubSpeaker.publish("toque_pes")
            #print(f"Frase: {'toque_pes'}")  # Debugging line
        elif action == "indication14":
            pubSpeaker.publish("mao_direita")
            #print(f"Frase: {'mao_direita'}")  # Debugging line
        elif action == "indication15":
            pubSpeaker.publish("mao_esquerda")
            #print(f"Frase: {'mao_esquerda'}")  # Debugging line
        elif action == "indication16":
            pubSpeaker.publish("pule_um_pe")
            #print(f"Frase: {'pule_um_pe'}")  # Debugging line
        elif action == "indication17":
            pubSpeaker.publish("mostre_lingua")
            #print(f"Frase: {'mostre_lingua'}")  # Debugging line

    def Reproduction(self, action):
        if action == "stop":
            pubSpeakerAction.publish("stop")
            #print(f"Frase: {'stop'}")  # Debugging line
        elif action == "pause":
            pubSpeakerAction.publish("pause")
            #print(f"Frase: {'pause'}")  # Debugging line
        elif action == "play":
            pubSpeakerAction.publish("unpause")
            #print(f"Frase: {'unpause'}")  # Debugging line

    def SegmentoAct2_History1(self, action):
        if action == "segment1":
            pubSpeaker.publish("jose_esta_na_rua")
            #print(f"Frase: {'jose_esta_na_rua'}")  # Debugging line
        elif action == "segment2":
            pubSpeaker.publish("jose_atravessa_a_rua")
            #print(f"Frase: {'jose_atravessa_a_rua'}")  # Debugging line
        elif action == "segment3":
            pubSpeaker.publish("jose_rua_3")
            #print(f"Frase: {'jose_rua_3'}")  # Debugging line
        elif action == "segment4":
            pubSpeaker.publish("jose_rua_4")
            #print(f"Frase: {'jose_rua_4'}")  # Debugging line
        elif action == "segment5":
            pubSpeaker.publish("jose_rua_5")
            #print(f"Frase: {'jose_rua_5'}")  # Debugging line
        elif action == "segment6":
            pubSpeaker.publish("jose_rua_6")
            #print(f"Frase: {'jose_rua_6'}")  # Debugging line

    def QuestionAct2_History1(self, action):
        if action == "question1":
            pubSpeaker.publish("jose_rua_p1")
            #print(f"Frase: {'jose_rua_p1'}")  # Debugging line
        elif action == "question2":
            pubSpeaker.publish("jose_rua_p2")
            #print(f"Frase: {'jose_rua_p2'}")  # Debugging line
        elif action == "question3":
            pubSpeaker.publish("jose_rua_p3")
            #print(f"Frase: {'jose_rua_p3'}")  # Debugging line
            
    def SegmentoAct2_History2(self, action):
        if action == "segment1":
            pubSpeaker.publish("jose_aniversario_1")
            #print(f"Frase: {'jose_aniversario_1'}")  # Debugging line
        elif action == "segment2":
            pubSpeaker.publish("jose_aniversario_2")
            #print(f"Frase: {'jose_aniversario_2'}")  # Debugging line
        elif action == "segment3":
            pubSpeaker.publish("jose_aniversario_3")
            #print(f"Frase: {'jose_aniversario_3'}")  # Debugging line
        elif action == "segment4":
            pubSpeaker.publish("jose_aniversario_4")
            #print(f"Frase: {'jose_aniversario_4'}")  # Debugging line
        elif action == "segment5":
            pubSpeaker.publish("jose_sopra_vela")
            #print(f"Frase: {'jose_sopra_vela'}")  # Debugging line
        elif action == "segment6":
            pubSpeaker.publish("jose_abre_presente")
            #print(f"Frase: {'jose_abre_presente'}")  # Debugging line
        elif action == "segment7":
            pubSpeaker.publish("jose_ja_tem_tres_anos")
            #print(f"Frase: {'jose_ja_tem_tres_anos'}")  # Debugging line
            
    def QuestionAct2_History2(self, action):       
        if action == "question1":
            pubSpeaker.publish("jose_aniversario_p1")
            #print(f"Frase: {'jose_aniversario_p1'}")  # Debugging line
        elif action == "question2":
            pubSpeaker.publish("jose_aniversario_p2")
            #print(f"Frase: {'jose_aniversario_p2'}")  # Debugging line
        elif action == "question3":
            pubSpeaker.publish("jose_aniversario_p3")
            #print(f"Frase: {'jose_aniversario_p3'}")  # Debugging line
            
    def SegmentoAct2_History4(self, action):
        if action == "segment1":
            pubSpeaker.publish("banheiro_jose")
            #print(f"Frase: {'banheiro_jose'}")  # Debugging line
        elif action == "segment2":
            pubSpeaker.publish("jose_banheiro_2")
            #print(f"Frase: {'jose_banheiro_2'}")  # Debugging line
        elif action == "segment3":
            pubSpeaker.publish("jose_banheiro_3")
            #print(f"Frase: {'jose_banheiro_3'}")  # Debugging line
        elif action == "segment4":
            pubSpeaker.publish("jose_banheiro_4")
            #print(f"Frase: {'jose_banheiro_4'}")  # Debugging line
        elif action == "segment5":
            pubSpeaker.publish("jose_banheiro_5")
            #print(f"Frase: {'jose_banheiro_5'}")  # Debugging line
        elif action == "segment6":
            pubSpeaker.publish("jose_esta_limpo_coloca_pijama")
            #print(f"Frase: {'jose_esta_limpo_coloca_pijama'}")  # Debugging line

    def QuestionAct2_History4(self, action):
        if action == "question1":
            pubSpeaker.publish("jose_banheiro_p1")
            #print(f"Frase: {'jose_banheiro_p1'}")  # Debugging line
        elif action == "question2":
            pubSpeaker.publish("jose_banheiro_p2")
            #print(f"Frase: {'jose_banheiro_p2'}")  # Debugging line
        elif action == "question3":
            pubSpeaker.publish("jose_banheiro_p3")
            #print(f"Frase: {'jose_banheiro_p3'}")  # Debugging line
            
    def SegmentoAct2_History5(self, action):
        if action == "segment1":
            pubSpeaker.publish("jose_assustado_1")
            #print(f"Frase: {'jose_assustado_1'}")  # Debugging line
        elif action == "segment2":
            pubSpeaker.publish("jose_assustado_2")
            #print(f"Frase: {'jose_assustado_2'}")  # Debugging line
        elif action == "segment3":
            pubSpeaker.publish("jose_treme_medo")
            #print(f"Frase: {'jose_treme_medo'}")  # Debugging line
        elif action == "segment4":
            pubSpeaker.publish("jose_assustado_4")
            #print(f"Frase: {'jose_assustado_4'}")  # Debugging line
        elif action == "segment5":
            pubSpeaker.publish("jose_grita_socorro")
            #print(f"Frase: {'jose_grita_socorro'}")  # Debugging line
        elif action == "segment6":
            pubSpeaker.publish("jose_assustado_6")
            #print(f"Frase: {'jose_assustado_6'}")  # Debugging line

    def QuestionAct2_History5(self, action):
        if action == "question1":
            pubSpeaker.publish("jose_assustado_p1")
            #print(f"Frase: {'jose_assustado_p1'}")  # Debugging line
        elif action == "question2":
            pubSpeaker.publish("jose_assustado_p2")
            #print(f"Frase: {'jose_assustado_p2'}")  # Debugging line
        elif action == "question3":
            pubSpeaker.publish("jose_assustado_p3")
            #print(f"Frase: {'jose_assustado_p3'}")  # Debugging line
            
    def Dance(self, action):
        if action == "dance1":
            pubSpeaker.publish("danca_comigo")
            #print(f"Frase: {'danca_comigo'}")  # Debugging line
        elif action == "dance":
            pubSpeaker.publish("vamos_dancar")   
            #print(f"Frase: {'vamos_dancar'}")  # Debugging line
        elif action == "round1":
            pubSpeaker.publish("musica1")
            #print(f"Frase: {'musica1'}")  # Debugging line
        elif action == "round2":
            pubSpeaker.publish("musica2")
            #print(f"Frase: {'musica2'}")  # Debugging line
        elif action == "round3":
            pubSpeaker.publish("musica3")
            #print(f"Frase: {'musica3'}")  # Debugging line
        elif action == "song1":
            pubMovements.publish("dance")
            pubSpeaker.publish("Pista_pop")
            #print(f"Frase: {'Pista_pop'}")  # Debugging line
        elif action == "song2":
            pubMovements.publish("dance")
            pubSpeaker.publish("Pista_electronica")
            #print(f"Frase: {'Pista_electronica'}")  # Debugging line
        elif action == "song3":
            pubMovements.publish("dance")
            pubSpeaker.publish("pista_mapale")
            #print(f"Frase: {'pista_mapale'}")  # Debugging line
        elif action == "song4":
            pubMovements.publish("dance")
            pubSpeaker.publish("pista_de_salsa")
            #print(f"Frase: {'pista_de_salsa'}")  # Debugging line
        elif action == "song5":
            pubMovements.publish("dance")
            pubSpeaker.publish("pista_de_merengue")
            #print(f"Frase: {'pista_de_merengue'}")  # Debugging line
        elif action == "song6":
            pubMovements.publish("dance")
            pubSpeaker.publish("Pista_Reggaeton_1")
            #print(f"Frase: {'Pista_Reggaeton_1'}")  # Debugging line
        elif action == "song8":
            pubMovements.publish("dance")
            pubSpeaker.publish("Pista_aerobicos")
            #print(f"Frase: {'Pista_aerobicos'}")  # Debugging line
        elif action == "song13":
            pubMovements.publish("dance")
            pubSpeaker.publish("Pista_Cumbia")
            #print(f"Frase: {'Pista_Cumbia'}")  # Debugging line

    def Songs(self, action):
        if action == "song1":
            pubSpeaker.publish("canta1")
            #print(f"Frase: {'canta1'}")  # Debugging line
        elif action == "song2":
            pubSpeaker.publish("canta2")
            #print(f"Frase: {'canta2'}")  # Debugging line
        elif action == "song3":
            pubSpeaker.publish("canta3")
            #print(f"Frase: {'canta3'}")  # Debugging line

    def Stories(self, action):
        if action == "story1":
            pubSpeaker.publish("Story1")
            #print(f"Frase: {'Story1'}")  # Debugging line
        elif action == "question1_1":
            pubSpeaker.publish("story1_p1")
            #print(f"Frase: {'story1_p1'}")  # Debugging line        
        elif action == "question1_2":
            pubSpeaker.publish("story1_p2")
            #print(f"Frase: {'story1_p2'}")  # Debugging line
        elif action == "question1_3":
            pubSpeaker.publish("story1_p3")
            #print(f"Frase: {'story1_p3'}")  # Debugging line

        elif action == "story2":
            pubSpeaker.publish("Story2")
            #print(f"Frase: {'Story2'}")  # Debugging line
        elif action == "question2_1":
            pubSpeaker.publish("story2_p1")
            #print(f"Frase: {'story2_p1'}")  # Debugging line
        elif action == "question2_2":
            pubSpeaker.publish("story2_p2")
            #print(f"Frase: {'story2_p2'}")  # Debugging line
        elif action == "question2_3":
            pubSpeaker.publish("story2_p3")
            #print(f"Frase: {'story2_p3'}")  # Debugging line
        
        elif action == "story3":
            pubSpeaker.publish("Story3")
            #print(f"Frase: {'Story3'}")  # Debugging line
        elif action == "question3_1":
            pubSpeaker.publish("story3_p1")
            #print(f"Frase: {'story3_p1'}")  # Debugging line
        elif action == "question3_2":
            pubSpeaker.publish("story3_p2")
            #print(f"Frase: {'story3_p2'}")  # Debugging line
        elif action == "question3_3":
            pubSpeaker.publish("story3_p3")
            #print(f"Frase: {'story3_p3'}")  # Debugging line

    def Hugs(self, action):
        if action == "sayHug":		  
            pubSpeaker.publish("da_um_abraco")
            #print(f"Frase: {'da_um_abraco'}")  # Debugging line
        elif action == "hugOpen":
            pubMovements.publish("hugOpen1")
            #print(f"Frase: {'hugOpen1'}")  # Debugging line
        elif action == "hugClose":
            pubMovements.publish("hugClose")
            #print(f"Frase: {'hugClose'}")  # Debugging line
        elif action == "hugEnd":
            pubMovements.publish("hugNeutral")
            #print(f"Frase: {'hugNeutral'}")  # Debugging line
        elif action == "thanks":
            pubEmotions.publish("happy")
            pubSpeaker.publish("obrigado")
            #print(f"Frase: {'obrigado'}")  # Debugging line
