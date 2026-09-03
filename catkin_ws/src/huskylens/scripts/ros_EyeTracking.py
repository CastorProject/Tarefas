#!/usr/bin/env python3

#CREATED WITH NEOVIM

import eye_position

import rospy
import time
from geometry_msgs.msg import Point
from std_msgs.msg import String
from std_msgs.msg import Bool

class EyeTrackingNode(object):
    def __init__(self, name):
        self.name = name
        rospy.init_node(self.name)
        self.rate = rospy.Rate(10)  #   10Hz
        self.initPublishers()
        self.initVariables()

    def initPublishers(self):
        self.moveEyesPub = rospy.Publisher('/moveEyes', Point, queue_size = 10)
        self.persona = rospy.Publisher('/persona', String)
        self.moveEyesEmotionsPub = rospy.Publisher('/emotions', String, queue_size = 10)

        return

    def initVariables(self):
        self.id = String()
        self.eyesPosition = Point()
        return

    def main(self):
        rospy.loginfo("[%s] ROS Eyes node started ok", self.name)
        while not (rospy.is_shutdown()):
            self.eyesPosition.x, self.eyesPosition.y, self.eyesPosition.z, self.id = eye_position.eye_tracking()
            self.persona.publish(self.id)
            self.moveEyesPub.publish(self.eyesPosition)
            self.moveEyesEmotionsPub.publish("husky")
            rospy.loginfo(self.eyesPosition.x, self.id)
            rospy.sleep(0.9)
        return

if __name__=='__main__':
    eyeTracking= EyeTrackingNode("eyeTrackingNode")
    eyeTracking.main()

