#!/usr/bin/env python3
#CREATED WITH NEOVIM

import interpretation
import translate_API
from nrclex import NRCLex

import rospy
import time
from std_msgs.msg import Float64
from std_msgs.msg import String
from std_msgs.msg import Bool

class micEmotionsNode(object):
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
        self.emotionsPub = rospy.Publisher('/emotions', String, queue_size = 10)
        return

    def initVariables(self):
        self.new_voice = False
        self.voice = String()
        self.answer = String()
        self.emotion = String()
        return
    #callbacks
    def callbackMic(self, msg):         #solo para tomar los datos del nodo (subscritor)
        self.new_voice = True
        self.voice = msg.data.lower()   #minusculas 
        return

    def Emotion(self):
        self.voice = translate_API.es_en(self.voice)
        emotion = NRCLex(self.voice)    # no definida como variable de objeto
        self.answer = interpretation.solve_emotion(emotion.raw_emotion_scores)
        if self.answer == 'positive' or self.answer == 'trust' or self.answer == 'joy':
            self.emotion.data = "happy"
        elif self.answer == 'negative' or self.answer == 'sadness':
            self.emotion.data = "sad"
        elif self.answer == 'surprise' or self.answer == 'fear':
            self.emotion.data = "surprise"
        elif self.answer == 'disgust' or self.answer == 'anger':
            self.emotion.data = "angry"
        else:
            self.emotion.data = "neutral"   #neutre y anticipation
        self.emotionsPub.publish(self.emotion)
        return

    def main(self):
        rospy.loginfo("[%s] ROS Eyes node started ok", self.name)
        while not (rospy.is_shutdown()):
            if self.new_voice:
                self.new_voice = False
                self.Emotion()
            rospy.sleep(0.1)
        return

if __name__=='__main__':
    micEmotions = micEmotionsNode("micEmotions")
    micEmotions.main()

