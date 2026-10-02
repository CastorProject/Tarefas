#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ============================================================
#  speaker.py - CASTOR / LabTEL-UFES
#  No unico de audio: atende o painel padrao e a IA Vitoria.
#
#  Fusao do speaker.py original com o speaker_vitoria.py:
#   - toca com pygame, que abre a placa uma vez e segura.
#     O aplay abria e fechava a cada audio, e a saida
#     analogica da Raspberry chiava nesse abre-fecha.
#   - aceita nome com extensao (CastorSAY.wav do TTS,
#     Maria.mp3 do menu) ou sem extensao (completa .mp3)
#   - marca /tmp/castor_falando.flag enquanto fala, para o
#     microfone descartar a propria voz do Castor
#   - ignora audio novo enquanto ja esta falando
#   - nao morre quando o arquivo nao existe
# ============================================================

import os
import rospy
import pygame
from std_msgs.msg import String
from std_msgs.msg import Bool

PASTA_SONS   = "/home/pi/Sounds/"
FLAG_FALANDO = "/tmp/castor_falando.flag"


class speakerNode(object):

    def __init__(self, name):
        self.name = name
        rospy.init_node(self.name)
        self.rate = rospy.Rate(10)
        self.initSubscribers()
        self.initPublishers()
        self.initVariables()
        self.iniciarMixer()
        return

    def initSubscribers(self):
        self.soundSub = rospy.Subscriber('/speaker', String, self.callbackSound)
        self.actionSpeakerSub = rospy.Subscriber('/speakerAction', String, self.callbackAction)
        return

    def initPublishers(self):
        self.emotionsPub  = rospy.Publisher("/emotions", String, queue_size=10)
        self.movementsPub = rospy.Publisher("/movements", String, queue_size=10)
        self.stopTalkPub  = rospy.Publisher("/stopTalk", Bool, queue_size=10)
        self.stopMovePub  = rospy.Publisher("/stopMove", Bool, queue_size=10)
        return

    def initVariables(self):
        self.newSound = False
        self.playSound = ""
        self.speakerAction = String()
        self.stopTalk = Bool()
        self.stopMove = Bool()
        self.movement = String()
        self.emotion = String()
        self.ocupado = False
        return

    def iniciarMixer(self):
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=8192)
        except Exception as e:
            rospy.logerr("[%s] nao consegui iniciar o mixer: %s", self.name, str(e))
        return

    def callbackSound(self, msg):
        if self.ocupado:
            rospy.logwarn("[%s] ja estou falando, ignorando: %s", self.name, msg.data)
            return
        self.playSound = msg.data
        self.newSound = True
        return

    def callbackAction(self, msg):
        self.speakerAction = msg.data
        if self.speakerAction == "stop":
            self.stopMusic()
        elif self.speakerAction == "pause":
            self.pauseMusic()
        else:
            self.unpauseMusic()
        return

    def resolverCaminho(self, nome):
        nome = str(nome).strip()
        if "." in os.path.basename(nome):
            return PASTA_SONS + nome
        return PASTA_SONS + nome + ".mp3"

    def playMusic(self, soundfile):
        if not os.path.exists(soundfile):
            rospy.logerr("[%s] arquivo nao existe: %s", self.name, soundfile)
            return

        self.emotion.data = "happy"
        self.emotionsPub.publish(self.emotion)

        try:
            open(FLAG_FALANDO, "w").close()
        except Exception:
            pass

        try:
            self.iniciarMixer()
            pygame.mixer.music.load(soundfile)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy() and not rospy.is_shutdown():
                rospy.sleep(0.05)
        except Exception as e:
            rospy.logerr("[%s] falhou ao tocar %s: %s", self.name, soundfile, str(e))
        finally:
            try:
                if os.path.exists(FLAG_FALANDO):
                    os.remove(FLAG_FALANDO)
            except Exception:
                pass

        self.movement.data = "neutral"
        self.movementsPub.publish(self.movement)
        self.emotion.data = "neutral"
        self.emotionsPub.publish(self.emotion)
        return

    def stopMusic(self):
        try:
            if pygame.mixer.get_init():
                pygame.mixer.music.stop()
        except Exception as e:
            rospy.logwarn("[%s] stop falhou: %s", self.name, str(e))
        self.movement.data = "neutral"
        self.movementsPub.publish(self.movement)
        self.stopTalk.data = True
        self.stopTalkPub.publish(self.stopTalk)
        return

    def pauseMusic(self):
        try:
            if pygame.mixer.get_init():
                pygame.mixer.music.pause()
        except Exception as e:
            rospy.logwarn("[%s] pause falhou: %s", self.name, str(e))
        self.stopTalk.data = True
        self.stopTalkPub.publish(self.stopTalk)
        self.stopMove.data = False
        self.stopMovePub.publish(self.stopMove)
        return

    def unpauseMusic(self):
        try:
            if pygame.mixer.get_init():
                pygame.mixer.music.unpause()
        except Exception as e:
            rospy.logwarn("[%s] unpause falhou: %s", self.name, str(e))
        self.stopTalk.data = False
        self.stopTalkPub.publish(self.stopTalk)
        self.stopMove.data = True
        self.stopMovePub.publish(self.stopMove)
        return

    def main(self):
        rospy.loginfo("[%s] speaker iniciado (pygame, pasta %s)", self.name, PASTA_SONS)
        while not rospy.is_shutdown():
            if self.newSound:
                self.newSound = False
                self.ocupado = True
                try:
                    self.playMusic(self.resolverCaminho(self.playSound))
                finally:
                    self.ocupado = False
            rospy.sleep(0.1)
        return


if __name__ == '__main__':
    speaker = speakerNode("speaker")
    speaker.main()
