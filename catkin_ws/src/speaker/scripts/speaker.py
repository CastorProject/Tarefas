#!/usr/bin/env python

import rospy
import time
import pygame
from std_msgs.msg import Float64
from std_msgs.msg import String
from std_msgs.msg import Bool

class speakerNode(object):
	def __init__(self, name):
		self.name = name
		rospy.init_node(self.name)
		self.rate = rospy.Rate(10)
		self.initSubscribers()
		self.initPublishers()
		self.initVariables()
		pygame.mixer.init()
		return

	def initSubscribers(self):
		self.soundSub = rospy.Subscriber('/speaker', String, self.callbackSound)
		self.actionSpeakerSub = rospy.Subscriber('/speakerAction', String, self.callbackAction)
		return

	def initPublishers(self):
		self.emotionsPub = rospy.Publisher("/emotions", String, queue_size = 10)
		self.movementsPub = rospy.Publisher("/movements", String, queue_size = 10)
		self.stopTalkPub = rospy.Publisher("/stopTalk", Bool, queue_size=10)
		return

	def initVariables(self):
		self.newSound = False
		self.playSound = String()
		self.speakerAction = String()
		self.stopTalk = Bool()
		self.stopMove = Bool()
		self.movement = String()
		self.emotion = String()
		return

	#Callbacks
	def callbackSound(self, msg):
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

	#Functions
	def playMusic(self, soundfile):
		pygame.mixer.init()
		clock = pygame.time.Clock()
		self.emotion.data = "happy"
		self.emotionsPub .publish(self.emotion)
		pygame.mixer.music.load(soundfile)
		pygame.mixer.music.play()
		while pygame.mixer.music.get_busy():
			clock.tick(1000)
		self.movement.data = "neutral"
		self.movementsPub.publish(self.movement)
		self.emotion.data = "neutral"
		self.emotionsPub .publish(self.emotion)
		return

	def stopMusic(self):
		pygame.mixer.music.stop()
		self.movement.data = "neutral"
		self.movementsPub.publish(self.movement)
		self.stopTalk.data = True
		self.stopTalkPub.publish(self.stopTalk)

	def pauseMusic(self):
		pygame.mixer.music.pause()
		self.stopTalk.data = True
		self.stopTalkPub.publish(self.stopTalk)
		self.stopMove.data = False
		self.stopMovePub.publish(self.stopMove)

	def unpauseMusic(self):
		pygame.mixer.music.unpause()
		self.stopTalk.data = False
		self.stopTalkPub.publish(self.stopTalk)
		self.stopMove.data = True
		self.stopMovePub.publish(self.stopMove)

	#Main
	def main(self):
		rospy.loginfo("[%s] speaker node started ok", self.name)
		while not (rospy.is_shutdown()):
			if self.newSound:
					self.playMusic("/home/pi/Sounds/" + (self.playSound if self.playSound.endswith(".mp3") else self.playSound + ".mp3"))
					self.newSound = False
                        rospy.sleep(0.1)
		return

if __name__=='__main__':
	speaker = speakerNode("speaker")
	speaker.main()
