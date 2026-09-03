#!/usr/bin/python3
#CREATED WITH NEOVIM

import language_processor

import rospy
import time
from std_msgs.msg import Float64
from std_msgs.msg import String
from std_msgs.msg import Bool

class chatNode(object):
    def __init__(self, name):
        self.name = name
        rospy.init_node(self.name)
        self.rate = rospy.Rate(10)  #   10Hz
        self.initSubscribers()
        self.initPublishers()
        self.initVariables()

    def initSubscribers(self):
        self.microphoneSub = rospy.Subscriber('/microphone', String, self.callbackMic)
        return
    def initPublishers(self):
        self.chat_output_Pub = rospy.Publisher('/chat_output', String, queue_size = 10)
        return

    def initVariables(self):
        self.new_voice = False
        self.voice = String()
        self.intent = String()      #intencion "greeting_3"
        self.response = String()    #respuesta "estas listo para una nueva aventura"
        return
    #callbacks
    def callbackMic(self, msg):
        self.new_voice = True
        self.voice = msg.data.lower()   #minusculas 
        return
    #Funciones
    def talk(self):
        self.intent, self.response = language_processor.output(self.voice)
        if (self.intent or self.response) != None:      #si retorna None es porque no hay match
            self.chat_output_Pub.publish(self.response)
        return

    def main(self):
        rospy.loginfo("[%s] ROS Eyes node started ok", self.name)
        while not (rospy.is_shutdown()):
            if self.new_voice:
                self.new_voice = False
                self.talk()
            rospy.sleep(0.1)
        return

if __name__=='__main__':
    chat = chatNode("chat")
    chat.main()

