#!/usr/bin/env python
import rospy
import time
import subprocess
from std_msgs.msg import Float64
from std_msgs.msg import String
from std_msgs.msg import Bool


class system_manager_node(object):
    def __init__(self, name):
        self.name = name
        rospy.init_node(self.name)
        self.rate = rospy.Rate(0.5)
        self.initSubscribers()
        self.initPublishers()
        self.initVariables()
        return

    def initSubscribers(self):
        self.movementSub = rospy.Subscriber('/castor_system', String, self.callback_system_action)
        return

    def initPublishers(self):
        return

    def initVariables(self):
        self.system_action = String()
        self.newAction = False
        self.mainActionsDict = {
            "shutdown": self.shutdown,
            "reboot": self.reboot
        }
        return

	#Callbacks
    def callback_system_action(self, msg):
        self.system_action = msg.data
        self.newAction = True
        return

    def shutdown(self):
        subprocess.call(['sudo', 'shutdown', 'now'], shell=False)
        return

    def reboot(self):
        subprocess.call(['sudo', 'reboot', 'now'], shell=False)
        return

	#Main
    def main(self):
        rospy.loginfo("[%s] castor system manager node started ok", self.name)
        while not (rospy.is_shutdown()):
            if self.newAction:
                try:
                    self.mainActionsDict[self.system_action]()
                    self.newAction = False
                except:
                    pass
            rospy.sleep(0.1)
        return

if __name__=='__main__':
    systemManager = system_manager_node("systemManager")
    systemManager.main()
