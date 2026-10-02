#!/usr/bin/env python3
# -*- coding: utf-8 -*-


#CREATED WITH NEOVIM

import microphone_listen

import rospy
import time
from std_msgs.msg import Float64
from std_msgs.msg import String
from std_msgs.msg import Bool

class microphoneNode(object):
    def __init__(self, name):
        self.name = name
        rospy.init_node(self.name)
        self.rate = rospy.Rate(10)  #   10Hz
        self.initSubscribers()
        self.initPublishers()
        self.initVariables()

    def initSubscribers(self):
        self.micSub = rospy.Subscriber('/record_data', String, self.callbackMic)
        return

    def initPublishers(self):
        self.microphonePub = rospy.Publisher('/microphone', String, queue_size = 10)
        # self.speakerPub = rospy.Publisher('/speaker', String, queue_size = 10)
        return

    def initVariables(self):
        self.voice = String()
        self.mic = String()
        self.start_mic = False
        return

#CALLBACKS
    def callbackMic(self, msg):         #solo para tomar los datos del nodo (subscritor)
        self.mic = msg.data
        print(msg.data)
        self.start_mic = True
        return
    '''
    def MicActions(self, textdetected): #NO ESTA EN ESO Para eso es es el nodo CHAT
        if "castor" in textdetected:
            self.speakerPub.publish("castor_apresentacao.mp3")
        elif "hola" in textdetected:
            self.speakerPub.publish("me_chamo_castor.mp3")
        elif "canta" in textdetected:
            self.speakerPub.publish("canta1.mp3")
        elif "perro" in textdetected:
            self.speakerPub.publish("cachorro_faz.mp3")
        elif "chao" in textdetected:
            self.speakerPub.publish("tchau_amiga.mp3")
    '''

    def main(self):
        rospy.loginfo("[%s] ROS Microphone node started ok", self.name)
        while not (rospy.is_shutdown()):
            if self.start_mic == True:
                for listening in microphone_listen.transcribe_audio(self.mic):
                    self.voice = listening
                    self.microphonePub.publish(self.voice)
                    #self.MicActions(self.voice)
                    rospy.sleep(0.1)
        return

if __name__=='__main__':
    microphone = microphoneNode("microphone")
    microphone.main()

