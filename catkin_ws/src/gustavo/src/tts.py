#!/usr/bin/env python3
# CREATED WITH NEOVIM

import rospy
import subprocess
from std_msgs.msg import String
from std_msgs.msg import Bool

class ttsNode(object):
    def __init__(self, name):
        self.name = name
        rospy.init_node(self.name)
        subprocess.run(["docker", "start", "Raspbian12"], check=True)
        self.rate = rospy.Rate(10)
        self.initSubscribers()
        self.initPublishers()
        self.initVariables()

    def initSubscribers(self):
        self.chat_output_Sub = rospy.Subscriber('/chat_output', String, self.callback_chat_output)
        self.persona = rospy.Subscriber('/persona', String, self.callback_persona)
        return

    def initPublishers(self):
        self.speakerPub = rospy.Publisher('/speaker', String, queue_size=10)
        return

    def initVariables(self):
        self.new_text = False
        self.new_persona = False
        self.p = []
        self.text = String()
        self.persona = String()
        return

    # CALLBACKS
    def callback_chat_output(self, msg):
        self.new_text = True
        self.text = msg.data
        return

    def callback_persona(self, msg):
        self.new_persona = True
        self.persona = msg.data
        return

    # FUNCIONES
    def tts(self, language, texto):
        subprocess.run(["docker", "exec", "Raspbian12", "/home/Raspbian12/piper/tts.sh", f"{language}", f"{texto}"], check=True)
        self.speakerPub.publish('CastorSAY.wav')  # pide reproducir el archivo
        return

    def main(self):
        rospy.loginfo("[%s] ROS TTS node started ok", self.name)
        while not rospy.is_shutdown():
            if self.new_text:
                self.new_text = False
                self.tts('portuguese', self.text)  # english, spanish, portuguese

            elif (self.persona == "1") and (self.persona not in self.p):
                self.p.append(self.persona)
                self.speakerPub.publish('Maria.mp3')

            elif (self.persona == "2") and (self.persona not in self.p):
                self.p.append(self.persona)
                self.speakerPub.publish('Elizabeth.mp3')

            elif (self.persona == "3") and (self.persona not in self.p):
                self.p.append(self.persona)
                self.speakerPub.publish('Juan.mp3')

            elif (self.persona == "4") and (self.persona not in self.p):
                self.p.append(self.persona)
                self.speakerPub.publish('Daniel.mp3')

            elif (self.persona == "6") and (self.persona not in self.p):
                self.p.append(self.persona)
                self.speakerPub.publish('Camilo.mp3')

            elif (self.persona == "0") and (self.persona not in self.p):
                self.p.append(self.persona)
                self.speakerPub.publish('desconocido.mp3')

            elif (self.persona == "7") and (self.persona not in self.p):
                self.p.append(self.persona)
                self.speakerPub.publish('Rosita.mp3')

            elif (self.persona == "8") and (self.persona not in self.p):
                self.p.append(self.persona)
                self.speakerPub.publish('Joao.mp3')

            elif (self.persona == "9") and (self.persona not in self.p):
                self.p.append(self.persona)
                self.speakerPub.publish('Benicio.mp3')

            elif (self.persona == "10") and (self.persona not in self.p):
                self.p.append(self.persona)
                self.speakerPub.publish('Laura.mp3')

            rospy.sleep(0.2)
        return

if __name__ == '__main__':
    text_to_speech = ttsNode("ttsNode")
    text_to_speech.main()