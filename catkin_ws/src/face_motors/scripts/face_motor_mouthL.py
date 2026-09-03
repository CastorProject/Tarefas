#!/usr/bin/env python3
import rospy
import time

from std_msgs.msg import String
from std_msgs.msg import Bool

from adafruit_servokit import ServoKit

#Constants

#Parameters
MIN_IMP  = 500
MAX_IMP  = 2500
MIN_ANG  = 0
MAX_ANG  = 180

#Objects
pca = ServoKit(channels = 16)
servoNumber = 5

class FaceMotor(object):
	def __init__(self, name):
		self.name = name
		rospy.init_node(self.name)
		self.rate = rospy.Rate(10) # 10hz
		self.initSubscribers()
		self.initVariables()

	def initSubscribers(self):
		self.subEmotions = rospy.Subscriber('/emotions', String, self.callbackEmotions)
		self.subStopTalk = rospy.Subscriber('/stopTalk', Bool, self.callbackStopTalk)
		return

	def initVariables(self):
		self.changeEmotions = False
		self.stopTalk = Bool()
		self.emotionsDict = {
		"happy": self.set_happy,
		"sad": self.set_sad,
		"surprise": self.set_surprise,
		"angry": self.set_angry,
		"neutral": self.set_neutral,
		"talk": self.talk
		}

	def set_servos(self):
		self.servoMotor = pca.servo[servoNumber]			# Motor movement with time
		self.servoMotor.set_pulse_width_range(MIN_IMP , MAX_IMP)
		self.servoMotor_movement = 0					# 0 clockwise, 180 counterclockwise movement
		self.servoMotor_time = 0					# Time of movement
		self.set_neutral()						# Set Origin Position
		
	# Emotions
	def set_happy(self):
		self.servoMotor_movement = 0
		for i in range(90, self.servoMotor_movement, -1):
			self.servoMotor.angle = i
			time.sleep(0.01)

	def set_sad(self):
		self.servoMotor_movement = 180
		for i in range(90, self.servoMotor_movement, 1):
			self.servoMotor.angle = i
			time.sleep(0.01)

	def set_surprise(self):
		self.servoMotor_movement = 180
		for i in range(90, self.servoMotor_movement, 1):
			self.servoMotor.angle = i
			time.sleep(0.01)

	def set_angry(self):
		self.servoMotor_movement = 180
		for i in range(90, self.servoMotor_movement, 1):
			self.servoMotor.angle = i
			time.sleep(0.01)

	def set_neutral(self):
		# Setting motor in origin position
		if self.servoMotor_movement < 90:
			for i in range(self.servoMotor_movement, 90, 1):
				self.servoMotor.angle = i
				time.sleep(0.001)
		else:
			for i in range(self.servoMotor_movement, 90, -1):
				self.servoMotor.angle = i
				time.sleep(0.001)
		self.servoMotor_movement = 90
		self.servoMotor.angle = None		# Disable channel

	def talk(self):
		self.servoMotor_movement = 0
		for i in range(90, self.servoMotor_movement, -1):
			self.servoMotor.angle = i
			time.sleep(0.01)

	def callbackEmotions(self, msg):
		self.emotion = msg.data
		self.changeEmotions = True
		return

	def callbackStopTalk(self, msg):
		self.stopTalk = msg.data
		return

	def main(self):
		rospy.loginfo("[%s] Facemotor node started ok", self.name)
		while not (rospy.is_shutdown()):
			if self.changeEmotions:
				self.set_neutral()
				if self.emotion == "talk":
					self.stopTalk = False
				self.emotionsDict[self.emotion]()
				self.changeEmotions = False
			self.rate.sleep()
		return

if __name__ == '__main__':
	fm = FaceMotor("motor_face_handler")
	fm.set_servos()
	fm.main()
