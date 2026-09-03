#!/usr/bin/env python3
import rospy
import time

from std_msgs.msg import String
from geometry_msgs.msg import Point
from std_msgs.msg import Bool
from std_msgs.msg import Float32

from adafruit_servokit import ServoKit

#Constants
nbPCAServo = 16

#Parameters
MIN_IMP  =[500, 500, 500, 500, 500, 500, 500, 500, 500, 500, 500, 500, 500, 500, 500, 500]
MAX_IMP  =[2500, 2500, 2500, 2500, 2500, 2500, 2500, 2500, 2500, 2500, 2500, 2500, 2500, 2500, 2500, 2500]
MIN_ANG  =[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
MAX_ANG  =[180, 180, 180, 180, 180, 180, 180, 180, 180, 180, 180, 180, 180, 180, 180, 180]

#Objects
pca = ServoKit(channels = 16)

class FaceMotor(object):
	def __init__(self, name):
		self.name = name
		rospy.init_node(self.name)
		self.rate = rospy.Rate(10) # 10hz
		self.initPublishers()
		self.initSubscribers()
		self.initVariables()
		for i in range(0, nbPCAServo):
			pca.servo[i].set_pulse_width_range(MIN_IMP[i] , MAX_IMP[i])

	def initPublishers(self):
		self.pubEyesBehavior = rospy.Publisher("/enableDefaultEyes", Bool, queue_size = 10)
		self.pubMoveEyes = rospy.Publisher("/moveEyes", Point, queue_size = 10)
		self.pubSizePupils = rospy.Publisher("/size_pupils", Float32, queue_size = 10)

	def initSubscribers(self):
		self.subEmotions = rospy.Subscriber('/emotions', String, self.callbackEmotions)
		self.subStopTalk = rospy.Subscriber('/stopTalk', Bool, self.callbackStopTalk)
		return

	def initVariables(self):
		self.changeEmotions = False
		self.enableEyesBehavior = Bool()
		self.eyesPosition = Point()
		self.stopTalk = Bool()
		self.pupilSize = Float32()
		self.emotionsDict = {
		"happy": self.set_happy,
		"sad": self.set_sad,
		"surprise": self.set_surprise,
		"angry": self.set_angry,
		"neutral": self.set_neutral,
		"talk": self.talk
		}

	def set_servos(self):
		self.eyeled_right = pca.servo[0]	# Motor movement with time
		self.eyeled_left = pca.servo[1]		# Motor movement with time
		self.mouth_right = pca.servo[3]		# Motor movement with time
		self.mouth_center = pca.servo[4]	# Motor movement with time
		self.mouth_left = pca.servo[5]		# Motor movement with angle

		self.eyeled_right_movement = 0		# 0 clockwise, 180 counterclockwise movement
		self.eyeled_left_movement = 0		# 0 clockwise, 180 counterclockwise movement
		self.mouth_right_movement = 0		# 0 clockwise, 180 counterclockwise movement
		self.mouth_center_movement = 0		# 0 clockwise, 180 counterclockwise movement
		self.mouth_left_movement = 0

		self.eyeled_right_time = 0		# Time of movement
		self.eyeled_left_time = 0		# Time of movement
		self.mouth_right_time = 0		# Time of movement
		self.mouth_center_time = 0		# Time of movement

		self.set_neutral()	# Set Origin Position
		
	def eyes(self, x, y, pupilSize):
		self.enableEyesBehavior.data = False
		self.pubEyesBehavior.publish(self.enableEyesBehavior)
		time.sleep(0.5)
		self.eyesPosition.x = x
		self.eyesPosition.y = y
		self.eyesPosition.z = 0
		self.pubMoveEyes.publish(self.eyesPosition)
		time.sleep(0.5)
		self.pupilSize.data = pupilSize
		self.pubSizePupils.publish(self.pupilSize)
		self.rate.sleep()

	# Emotions
	def set_happy(self):
		self.eyes(0, 8, 0.7)
		
		self.eyeled_right_movement = 180
		self.eyeled_right_time = 0.20
		self.eyeled_right.angle = self.eyeled_right_movement
		time.sleep(self.eyeled_right_time)
		self.eyeled_right.angle = None 			# Disable channel

		self.eyeled_left_movement = 0
		self.eyeled_left_time = 0.20
		self.eyeled_left.angle = self.eyeled_left_movement
		time.sleep(self.eyeled_left_time)
		self.eyeled_left.angle = None 			# Disable channel

		self.mouth_right_movement = 180
		self.mouth_right_time = 0.40
		self.mouth_right.angle = self.mouth_right_movement
		time.sleep(self.mouth_right_time)
		self.mouth_right.angle = None 			# Disable channel

		self.mouth_left_movement = 0
		for i in range(90, self.mouth_left_movement, -1):
			self.mouth_left.angle = i
			time.sleep(0.01)

	def set_sad(self):
		self.eyes(0, -20, 0.4)

		self.eyeled_right_movement = 180
		self.eyeled_right_time = 0.20
		self.eyeled_right.angle = self.eyeled_right_movement
		time.sleep(self.eyeled_right_time)
		self.eyeled_right.angle = None 			# Disable channel

		self.eyeled_left_movement = 0
		self.eyeled_left_time = 0.20
		self.eyeled_left.angle = self.eyeled_left_movement
		time.sleep(self.eyeled_left_time)
		self.eyeled_left.angle = None 			# Disable channel

		self.mouth_right_movement = 0
		self.mouth_right_time = 0.40
		self.mouth_right.angle = self.mouth_right_movement
		time.sleep(self.mouth_right_time)
		self.mouth_right.angle = None 			# Disable channel

		self.mouth_left_movement = 180
		for i in range(90, self.mouth_left_movement, 1):
			self.mouth_left.angle = i
			time.sleep(0.01)

	def set_surprise(self):
		self.eyes(0, 15, 0.3)

		self.eyeled_right_movement = 180
		self.eyeled_right_time = 0.20
		self.eyeled_right.angle = self.eyeled_right_movement
		time.sleep(self.eyeled_right_time)
		self.eyeled_right.angle = None 			# Disable channel

		self.eyeled_left_movement = 0
		self.eyeled_left_time = 0.20
		self.eyeled_left.angle = self.eyeled_left_movement
		time.sleep(self.eyeled_left_time)
		self.eyeled_left.angle = None 			# Disable channel

		self.mouth_right_movement = 0
		self.mouth_right_time = 0.40
		self.mouth_right.angle = self.mouth_right_movement
		time.sleep(self.mouth_right_time)
		self.mouth_right.angle = None 			# Disable channel

		self.mouth_left_movement = 180
		for i in range(90, self.mouth_left_movement, 1):
			self.mouth_left.angle = i
			time.sleep(0.01)

	def set_angry(self):
		self.eyes(0, 0, 0.5)

		self.eyeled_right_movement = 0
		self.eyeled_right_time = 0.20
		self.eyeled_right.angle = self.eyeled_right_movement
		time.sleep(self.eyeled_right_time)
		self.eyeled_right.angle = None 			# Disable channel

		self.eyeled_left_movement = 180
		self.eyeled_left_time = 0.20
		self.eyeled_left.angle = self.eyeled_left_movement
		time.sleep(self.eyeled_left_time)
		self.eyeled_left.angle = None 			# Disable channel

		self.mouth_right_movement = 0
		self.mouth_right_time = 0.40
		self.mouth_right.angle = self.mouth_right_movement
		time.sleep(self.mouth_right_time)
		self.mouth_right.angle = None 			# Disable channel

		self.mouth_left_movement = 180
		for i in range(90, self.mouth_left_movement, 1):
			self.mouth_left.angle = i
			time.sleep(0.01)

	def set_neutral(self):
		# Setting eyeled_right motor in neutral
		if self.eyeled_right_movement == 0:
			self.eyeled_right_movement = 180
			self.eyeled_right.angle = self.eyeled_right_movement
			time.sleep(self.eyeled_right_time)
			self.eyeled_right_time = 0
			self.eyeled_right.angle = None				# Disable channel
		else:
			self.eyeled_right_movement = 0
			self.eyeled_right.angle = self.eyeled_right_movement
			time.sleep(self.eyeled_right_time)
			self.eyeled_right_time = 0
			self.eyeled_right.angle = None				# Disable channel

		# Setting eyeled_left motor in origin position
		if self.eyeled_left_movement == 0:
			self.eyeled_left_movement = 180
			self.eyeled_left.angle = self.eyeled_left_movement
			time.sleep(self.eyeled_left_time)
			self.eyeled_left_time = 0
			self.eyeled_left.angle = None				# Disable channel
		else:
			self.eyeled_left_movement = 0
			self.eyeled_left.angle = self.eyeled_left_movement			
			time.sleep(self.eyeled_left_time)
			self.eyeled_left_time = 0
			self.eyeled_left.angle = None				# Disable channel

		# Setting mouth_right motor in origin position
		if self.mouth_right_movement == 0:
			self.mouth_right_movement = 180
			self.mouth_right.angle = self.mouth_right_movement
			time.sleep(self.mouth_right_time)
			self.mouth_right_time = 0
			self.mouth_right.angle = None				# Disable channel
		else:
			self.mouth_right_movement = 0
			self.mouth_right.angle = self.mouth_right_movement
			time.sleep(self.mouth_right_time)
			self.mouth_right_time = 0
			self.mouth_right.angle = None				# Disable channel

		# Setting mouth_center motor in origin position
		if self.mouth_center_movement == 0:
			self.mouth_center_movement = 180
			self.mouth_center.angle = self.mouth_center_movement
			time.sleep(self.mouth_center_time)
			self.mouth_center_time = 0
			self.mouth_center.angle = None				# Disable channel
		else:
			self.mouth_center_movement = 0
			self.mouth_center.angle = self.mouth_center_movement
			time.sleep(self.mouth_center_time)
			self.mouth_center_time = 0
			self.mouth_center.angle = None				# Disable channel

		# Setting mouth_left motor in origin position
		if self.mouth_left_movement < 90:
			for i in range(self.mouth_left_movement, 90, 1):
				self.mouth_left.angle = i
				time.sleep(0.01)
		else:
			for i in range(self.mouth_left_movement, 90, -1):
				self.mouth_left.angle = i
				time.sleep(0.01)
		self.mouth_left_movement = 90

		self.mouth_left.angle = None					# Disable channel

	def talk(self):
		self.eyes(0, 8, 0.7)

		self.eyeled_right_movement = 180
		self.eyeled_right_time = 0.15
		self.eyeled_right.angle = self.eyeled_right_movement
		time.sleep(self.eyeled_right_time)
		self.eyeled_right.angle = None 			# Disable channel

		self.eyeled_left_movement = 0
		self.eyeled_left_time = 0.15
		self.eyeled_left.angle = self.eyeled_left_movement
		time.sleep(self.eyeled_left_time)
		self.eyeled_left.angle = None 			# Disable channel

		self.mouth_right_movement = 180
		self.mouth_right_time = 0.15
		self.mouth_right.angle = self.mouth_right_movement
		time.sleep(self.mouth_right_time)
		self.mouth_right.angle = None 			# Disable channel

		self.mouth_left_movement = 0
		for i in range(90, self.mouth_left_movement, -1):
			self.mouth_left.angle = i
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
