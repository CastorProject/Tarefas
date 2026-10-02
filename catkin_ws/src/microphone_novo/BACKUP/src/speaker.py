#!/usr/bin/env python

import rospy
import time
import pygame
import subprocess

from std_msgs.msg import Float64
from std_msgs.msg import String
from std_msgs.msg import Bool

######################################
################ ROS #################
######################################
rospy.init_node('microphone')
######################################
############# PUBLISHERS #############
######################################
pubEmotions = rospy.Publisher('/emotions', String, queue_size = 10)
pubSpeaker = rospy.Publisher('/speaker', String, queue_size = 10)
pubSpeakerAction = rospy.Publisher('/speakerAction', String, queue_size = 15)
pubMovements = rospy.Publisher('/movements', String, queue_size = 5)
######################################
######################################
######################################
def MicrophoneNode(name):
    if textdetected == "castor":
        pubEmotions.publish("talk")
        pubMovements.publish("wave")
        time.sleep(0.5)
        pubSpeaker.publish("castor_apresentacao")

    elif textdetected == "hola":
        pubEmotions.publish("talk")
        pubMovements.publish("wave")
        time.sleep(0.5)
        pubSpeaker.publish("hola")


if __name__=='__main__':
	Microphone= MicrophoneNode("speaker")
	speaker.main()