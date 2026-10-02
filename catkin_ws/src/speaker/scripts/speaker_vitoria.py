#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ============================================================
#  speaker_vitoria.py - CASTOR / LabTEL-UFES
#  Vitoria Gomes Fagundes
#
#  Toca .wav via aplay (sem engasgo) e cai para pygame
#  quando o arquivo for .mp3 de verdade.
# ============================================================
import os
import rospy
import subprocess
from std_msgs.msg import String
from std_msgs.msg import Bool

# Saida de audio:
#   plughw:1,0 = P2 da Raspberry (em uso - adaptador USB com defeito)
#   plughw:2,0 = adaptador USB de audio
DISPOSITIVO_AUDIO = "plughw:1,0"

# 1s de silencio tocado antes do audio real, para acordar o
# amplificador do P2 da Raspberry (senao o inicio da frase se perde)
SILENCIO = "/home/pi/Sounds/_silencio_DESATIVADO.wav"

PASTA_SONS = "/home/pi/Sounds/"

# Enquanto este arquivo existir, o microfone descarta o que ouve.
# Impede que o Castor escute a propria voz.
FLAG_FALANDO = "/tmp/castor_falando.flag"


class speakerNode(object):

    def __init__(self, name):
        self.name = name
        rospy.init_node(self.name)
        self.initSubscribers()
        self.initPublishers()
        self.initVariables()

    def initSubscribers(self):
        rospy.Subscriber('/speaker', String, self.callbackSound)
        rospy.Subscriber('/speakerAction', String, self.callbackAction)

    def initPublishers(self):
        self.emotionsPub  = rospy.Publisher("/emotions", String, queue_size=10)
        self.movementsPub = rospy.Publisher("/movements", String, queue_size=10)
        self.stopTalkPub  = rospy.Publisher("/stopTalk", Bool, queue_size=10)

    def initVariables(self):
        self.newSound = False
        self.playSound = ""
        self.emotion = String()
        self.movement = String()
        self.stopTalk = Bool()
        self.ocupado = False

    # ---- callbacks --------------------------------------------------
    def callbackSound(self, msg):
        if self.ocupado:
            rospy.logwarn("[%s] ocupado, ignorando: %s", self.name, msg.data)
            return
        self.playSound = msg.data
        self.newSound = True

    def callbackAction(self, msg):
        if msg.data == "stop":
            self.stopMusic()

    # ---- reproducao -------------------------------------------------
    def tocarComAplay(self, soundfile):
        try:
            nulo = open(os.devnull, 'w')
            cmd = ["aplay", "-q", "-D", DISPOSITIVO_AUDIO]
            if os.path.exists(SILENCIO):
                cmd.append(SILENCIO)
            cmd.append(soundfile)
            ret = subprocess.call(cmd, stderr=nulo)
            nulo.close()
            return ret == 0
        except Exception as e:
            rospy.logwarn("[%s] aplay falhou: %s", self.name, str(e))
            return False

    def tocarComPygame(self, soundfile):
        try:
            import pygame
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16,
                                  channels=2, buffer=8192)
            pygame.mixer.music.load(soundfile)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy() and not rospy.is_shutdown():
                rospy.sleep(0.05)
            return True
        except Exception as e:
            rospy.logerr("[%s] pygame falhou em %s: %s",
                         self.name, soundfile, str(e))
            return False

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

        if not self.tocarComAplay(soundfile):
            rospy.loginfo("[%s] aplay recusou, tentando pygame: %s",
                          self.name, soundfile)
            self.tocarComPygame(soundfile)

        try:
            if os.path.exists(FLAG_FALANDO):
                os.remove(FLAG_FALANDO)
        except Exception:
            pass

        self.movement.data = "neutral"
        self.movementsPub.publish(self.movement)
        self.emotion.data = "neutral"
        self.emotionsPub.publish(self.emotion)

    def stopMusic(self):
        self.stopTalk.data = True
        self.stopTalkPub.publish(self.stopTalk)

    # ---- loop principal ---------------------------------------------
    def main(self):
        rospy.loginfo("[%s] speaker_vitoria iniciado - saida %s",
                      self.name, DISPOSITIVO_AUDIO)
        while not rospy.is_shutdown():
            if self.newSound:
                self.newSound = False
                self.ocupado = True
                try:
                    self.playMusic(PASTA_SONS + self.playSound + ".mp3")
                finally:
                    self.ocupado = False
            rospy.sleep(0.1)


if __name__ == '__main__':
    speakerNode("speaker").main()
