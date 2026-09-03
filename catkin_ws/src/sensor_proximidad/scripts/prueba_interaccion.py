#!/usr/bin/env python
import rospy
import subprocess
import numpy as np
import time
import random
from collections import deque

from std_msgs.msg import Float64
from std_msgs.msg import String
from std_msgs.msg import Bool

class FiltroMediana:
    def __init__(self, ventana=2):
        self.ventana = deque(maxlen=ventana)

    def filtrar(self, nuevo_valor):
        self.ventana.append(nuevo_valor)
        return np.median(self.ventana)

class proximityNode(object):
    def __init__(self, name):
        self.name = name
        rospy.init_node(self.name)
        self.rate = rospy.Rate(10)
        self.initSubscribers()
        self.initPublishers()
        self.initVariables()

    def initSubscribers(self):
        self.subSensor_rfid = rospy.Subscriber('/sensor_rfid', String, self.callbackrfid)
        self.subSensor_laser = rospy.Subscriber('/sensor_prox_laser', String, self.callbacklaser)
        return

    def initPublishers(self):
        self.ledPub = rospy.Publisher('/led_control', String, queue_size = 10)
        self.speakerPub = rospy.Publisher('/speaker', String, queue_size = 10)
        self.pubEmotions = rospy.Publisher('/emotions', String, queue_size = 10)
        return

    def initVariables(self):
        self.new_laser = False
        self.new_rfid = False
        self.laser = 0.0
        self.rfid = 0.0
        self.emotion = String()
        self.interaction_sequence = []
        self.far_call_count = 0
        self.midzone_call_count = 0


        #self.filtro_laser = FiltroMediana(ventana=5)
        #self.filtro_rfid = FiltroMediana(ventana=5)
        return

#CALLBACKS
    def callbackrfid(self, msg):
        try:
            valor = float(msg.data)
            self.rfid = self.filtro_rfid.filtrar(valor)
            self.new_rfid = True
        except ValueError:
            rospy.logwarn("Dato RFID invalido: %s", msg.data)

    def callbacklaser(self, msg):
        try:
            valor = float(msg.data)
            #self.laser = self.filtro_laser.filtrar(valor)
            self.laser = valor
            self.new_laser = True
        except ValueError:
            rospy.logwarn("Dato laser invalido: %s", msg.data)

    def main(self):
        rospy.loginfo("[%s] ROS Proximity node started ok", self.name)
        self.state = "AWAITING_STABLE_DISTANCE"
        self.interaction_step = 0
        self.interaction_started = False

        # Variables para esperar estabilidad
        stable_start_time = None
        last_distance = None
        t_espera = 3.0  # segundos de estabilidad
        delta = 5.0     # variacion aceptable

        frases_tristeza = [
            "estou_sozinho",
            "volte_para_mim",
            "esperando_voce"
        ]

        while not rospy.is_shutdown():
            if self.new_laser or self.new_rfid:
                rospy.loginfo("Laser filtrado: %.2f", self.laser)
                self.new_laser = False
                #self.new_rfid = False

            distance = self.laser
            
            if self.state == "AWAITING_STABLE_DISTANCE":
                if last_distance is None:
                    last_distance = distance
                    stable_start_time = time.time()
                elif abs(distance - last_distance) <= delta:
                    if time.time() - stable_start_time >= t_espera:
                        rospy.loginfo("Distancia estable detectada: %.2f", distance)
                        # Decidir zona y estado segun distancia establecida
                        if distance <= 45:
                            self.state = "INTERACTION_STARTED"
                            self.interaction_step = 0
                            self.interaction_started = True
                            self.ledPub.publish("green")
                            rospy.loginfo("Inicio de interaccion")
                            self.emotion.data = "happy"
                            self.pubEmotions.publish(self.emotion)

                            saludo_y_preguntas = [
                                "me_chamo_castor", "como_estao", "qual_sua_cor_preferida", "cor_favorita",
                                "animal_preferido", "meu_animal_preferido", "meu_animal_preferido"
                            ]
                            instruccion_mestre = ["siga_instrucoes_mestre"]
                            cancion_mestre = ["mestre_mandou"]
                            acciones = [
                                "pule", "aplauda_duas_vezes", "uma_volta",
                                "abaixe_se", "faca_uma_cara_surpresa"
                            ]
                            frases_realimentacion = [
                                "muito_bem", "parabens_02", "conseguiu"
                            ]
                            despedida = ["tudo_hoje", "tchau_amigo"]

                            self.interaction_sequence = (
                                saludo_y_preguntas +
                                instruccion_mestre +
                                cancion_mestre +
                                acciones +
                                [random.choice(frases_realimentacion)] +
                                despedida
                            )

                        elif distance <= 120:
                            self.state = "MIDZONE_PROMPT"
                            self.ledPub.publish("yellow")
                            self.speakerPub.publish("acercate")
                            rospy.loginfo("Zona media estable detectada")
                        else:
                            self.state = "USER_FAR_AWAY"
                            self.ledPub.publish("blue")
                            frase = random.choice(frases_tristeza)
                            self.speakerPub.publish(frase)
                            rospy.loginfo("Zona lejana estable detectada")
                    # No ha pasado suficiente tiempo aun
                else:
                    stable_start_time = time.time()
                    last_distance = distance
            # Zona 1: Cercana (Interaccion)
            elif distance <= 45:
                if self.state in ["IDLE", "FAR_IDLE", "USER_FAR_AWAY"]:
                    self.state = "INTERACTION_STARTED"
                    self.interaction_step = 0
                    self.interaction_started = True
                    rospy.loginfo("Interaccion iniciada")
                    self.ledPub.publish("green")
                    self.emotion.data = "happy"
                    self.pubEmotions.publish(self.emotion)

                    # Generar la secuencia completa en ese momento
                    saludo_y_preguntas = [
                        "me_chamo_castor", "como_estao", "qual_sua_cor_preferida", "cor_favorita",
                        "animal_preferido", "meu_animal_preferido", "meu_animal_preferido"
                    ]
                    instruccion_mestre = ["siga_instrucoes_mestre"]
                    cancion_mestre = ["mestre_mandou"]
                    acciones = [
                        "pule", "aplauda_duas_vezes", "uma_volta",
                        "abaixe_se", "faca_uma_cara_surpresa"
                    ]
                    frases_realimentacion = [
                        "muito_bem", "parabens_02", "conseguiu"
                    ]
                    despedida = ["tudo_hoje", "tchau_amigo"]

                    self.interaction_sequence = (
                        saludo_y_preguntas +
                        instruccion_mestre +
                        cancion_mestre +
                        acciones +
                        [random.choice(frases_realimentacion)] +
                        despedida
                    )

                elif self.state == "INTERACTION_INTERRUPTED":
                    self.state = "INTERACTION_IN_PROGRESS"
                    self.ledPub.publish("green")
                    self.speakerPub.publish("legal_que_voce_voltou")
                    rospy.loginfo("Interaccion retomada con mensaje emocional")
                    self.emotion.data = "happy"
                    self.pubEmotions.publish(self.emotion)


                if self.state in ["INTERACTION_STARTED", "INTERACTION_IN_PROGRESS"]:
                    if self.interaction_step < len(self.interaction_sequence):
                        self.speakerPub.publish(self.interaction_sequence[self.interaction_step])
                        self.interaction_step += 1
                        time.sleep(5)
                    else:
                        self.state = "INTERACTION_ENDED"
                        self.ledPub.publish("blue")
                        self.emotion.data = "sad"
                        self.pubEmotions.publish(self.emotion)
                        rospy.loginfo("Interaccion finalizada exitosamente")
                        rospy.signal_shutdown("Fin de intento de interaccion en zona inicial.")

            # Zona 2: Media (interrumpida o invitacion)
            elif 45 < distance <= 120:
                if self.state in ["INTERACTION_STARTED", "INTERACTION_IN_PROGRESS"]:
                    self.state = "INTERACTION_INTERRUPTED"
                    self.ledPub.publish("yellow")
                    self.emotion.data = "neutral" 
                    self.pubEmotions.publish(self.emotion)  
                    self.speakerPub.publish("onde_voce_vai")
                    time.sleep(3)
                    self.speakerPub.publish("volte_para_jogar")
                    rospy.loginfo("Usuario se alejo en medio de la interaccion")
                    time.sleep(5)

                elif self.state == "INTERACTION_INTERRUPTED":
                    self.state = "MIDZONE_PROMPT"
                    rospy.loginfo("Usuario no regreso tras interrupcion. Cambiando a MIDZONE_PROMPT.")

                elif self.state in ["IDLE", "MIDZONE_PROMPT"]:
                    self.midzone_call_count += 1
                    self.state = "MIDZONE_PROMPT"
                    self.emotion.data = "neutral" 
                    self.pubEmotions.publish(self.emotion)  
                    self.ledPub.publish("yellow")
                    self.speakerPub.publish("acercate")
                    rospy.loginfo("Usuario en zona media. Llamado %d", self.midzone_call_count)
                    time.sleep(5)

                    if self.midzone_call_count >= 2:
                        self.ledPub.publish("blue")
                        self.emotion.data = "sad" 
                    	self.pubEmotions.publish(self.emotion)  
                        self.speakerPub.publish("a_gente_se_ve_outro")
                        rospy.loginfo("Usuario no se acerco. Finalizando intento de interaccion.")
                        self.midzone_call_count = 0
                        rospy.signal_shutdown("Fin de intento de interaccion en zona media.")


            elif distance > 120:
                if self.state in ["IDLE", "USER_FAR_AWAY"]:
                    self.far_call_count += 1
                    self.state = "FAR_IDLE"
                    self.ledPub.publish("red")
                    self.emotion.data = "angry" 
                    self.pubEmotions.publish(self.emotion)  
                    frase = random.choice(frases_tristeza)
                    self.speakerPub.publish(frase)
                    rospy.loginfo("Usuario en zona lejana. Llamado %d", self.midzone_call_count)
                    time.sleep(5)

                elif self.state == "FAR_IDLE":
                    self.far_call_count += 1
                    if self.far_call_count >= 2:
                        self.ledPub.publish("blue")
                        self.emotion.data = "sad" 
                        self.pubEmotions.publish(self.emotion)  
                        self.speakerPub.publish("no_te_noto_bem_hoje")
                        time.sleep(5)
                        rospy.loginfo("Usuario no respondio al segundo llamado. Interaccion finalizada.")
                        self.far_call_count = 0
                        rospy.signal_shutdown("Usuario no respondio a llamados. Terminando sesion.")

                    else:
                        frase = random.choice(frases_tristeza)
                        self.speakerPub.publish(frase)
                        rospy.loginfo("Segundo llamado triste en zona lejana.")
                        time.sleep(5)

                elif self.state in ["INTERACTION_STARTED", "INTERACTION_IN_PROGRESS", "INTERACTION_INTERRUPTED"]:
                    self.state = "INTERACTION_ENDED"
                    self.ledPub.publish("blue")
                    self.emotion.data = "sad" 
                    self.pubEmotions.publish(self.emotion)  

                    self.speakerPub.publish("tchau_amigo")
                    rospy.loginfo("Usuario se alejo al final de la interaccion. Finalizando con despedida.")
                    self.far_call_count = 0
                    rospy.signal_shutdown("Interaccion finalizada con despedida final.")

            self.rate.sleep()
        return
if __name__=='__main__':
    proximity = proximityNode("Proximity_Node")
    proximity.main()
    