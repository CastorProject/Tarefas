#!/usr/bin/env python
import rospy
import time

from std_msgs.msg import String
from geometry_msgs.msg import Point
from std_msgs.msg import Bool
from std_msgs.msg import Float32

import Adafruit_PCA9685


class FaceMotor(object):
	def __init__(self, name, Channel, ZeroOffset):
		self.name = name
		rospy.init_node(self.name)
		self.rate = rospy.Rate(10) # 10hz
		self.initPublishers()
		self.initSubscribers()
		self.initVariables()
        
        self.Channel = Channel
        self.ZeroOffset = ZeroOffset

        #Initialize Adafruit_PCA9685
		#Aqui depende del read I2C (0x40)
        self.pwm = Adafruit_PCA9685.PCA9685(address=0x40)
        self.pwm.set_pwm_freq(int(60))

	def initPublishers(self):
		self.pubMoveEyes = rospy.Publisher("/moveEyes", Point, queue_size = 10)
		self.pubSizePupils = rospy.Publisher("/size_pupils", Float32, queue_size = 10)

	def initSubscribers(self):
		self.subEmotions = rospy.Subscriber('/emotions', String, self.callbackEmotions)
		self.subStopTalk = rospy.Subscriber('/stopTalk', Bool, self.callbackStopTalk)
		return

	def initVariables(self):
		self.changeEmotions = False
		self.eyesPosition = Point()
		self.stopTalk = Bool()
		self.pupilSize = Float32()
		self.emotionsDict = {
		"happy": self.set_happy,
		"sad": self.set_sad,
		"surprise": self.set_surprise,
		"angry": self.set_angry,
		"neutral": self.set_neutral,
		"demo": self.demo,
		"talk": self.talk
		}

	def set_servos(self):
		#mouth motors
		self.eyeled1 = servo_Class(Channel=3, ZeroOffset=0)
		self.eyeled2 = servo_Class(Channel=4, ZeroOffset=0)
		self.mouth1 = servo_Class(Channel=0, ZeroOffset=0)
		self.mouth2 = servo_Class(Channel=1, ZeroOffset=0)
		self.mouth3 = servo_Class(Channel=2, ZeroOffset=0)

		#set actuation ranges
		self.mouth1.set_actuation_range(min =1099, max = 1331, origin =1261)
		self.mouth2.set_actuation_range(min =799, max = 1301, origin =950)
		self.mouth3.set_actuation_range(min =899, max = 1501 , origin =1280)
		self.eyeled2.set_actuation_range(min = 1199, max = 1851, origin =1450)
		self.eyeled1.set_actuation_range(min = 1049, max = 1651, origin =1420)

		#set origin position
		self.set_neutral()

	def eyes(self, x, y, pupilSize):
		time.sleep(0.5)
		self.eyesPosition.x = x
		self.eyesPosition.y = y
		self.eyesPosition.z = 0
		self.pubMoveEyes.publish(self.eyesPosition)
		time.sleep(0.5)
		self.pupilSize.data = pupilSize
		self.pubSizePupils.publish(self.pupilSize)
		self.rate.sleep()

	#expressions
	def set_happy(self):
		self.eyes(0, 8, 0.7)
		self.mouth1.set_position(command ={'value':1300})
		self.mouth2.set_position(command ={'value':1200})
		self.mouth3.set_position(command ={'value':900})
		self.eyeled2.set_position(command ={'value':1300})
		self.eyeled1.set_position(command ={'value':1530})

	def set_sad(self):
		self.eyes(0, -20, 0.4)
		self.mouth1.set_position(command ={'value':1100})
		self.mouth2.set_position(command ={'value':800})
		self.mouth3.set_position(command ={'value':1500})
		self.eyeled2.set_position(command ={'value':1300})
		self.eyeled1.set_position(command ={'value':1530})

	def set_surprise(self):
		self.eyes(0, 15, 0.3)
		self.mouth1.set_position(command ={'value':1330})
		self.mouth2.set_position(command ={'value':800})
		self.mouth3.set_position(command ={'value':1500})
		self.eyeled2.set_position(command ={'value':1300})
		self.eyeled1.set_position(command ={'value':1530})

	def set_angry(self):
		self.eyes(0, 0, 0.5)
		self.mouth1.set_position(command ={'value':1150})
		self.mouth2.set_position(command ={'value':800})
		self.mouth3.set_position(command ={'value':1500})
		self.eyeled2.set_position(command ={'value':1800})
		self.eyeled1.set_position(command ={'value':1100})

	def set_neutral(self):
        #self.mouth1.Cleanup()
        #self.mouth2.Cleanup()
        #self.mouth3.Cleanup()
        #self.eyeled1.Cleanup()
        #self.eyeled2.Cleanup()
		self.mouth1.set_origin_position()
		self.mouth2.set_origin_position()
		self.mouth3.set_origin_position()
		self.eyeled2.set_origin_position()
		self.eyeled1.set_origin_position()

	def talk(self):
		self.eyes(0, 8, 0.7)
		self.mouth2.set_position(command ={'value':950})
		self.mouth3.set_position(command ={'value':1300})
		while not self.stopTalk:
			self.mouth1.set_position(command ={'value':1330})
			time.sleep(0.2)
			self.mouth1.set_position(command ={'value':1300})
			time.sleep(0.2)

	def demo(self):
		print("demo")
		time.sleep(2)
		self.set_happy()
		time.sleep(2)
		self.set_sad()
		time.sleep(2)
		self.set_angry()
		time.sleep(2)
		self.set_surprise()
		time.sleep(2)
		self.set_neutral()
		time.sleep(2)
		self.talk()
        
    def SetPos(self,pos):
        #PCA9685 controls angles with pulses, 150~650 of pulses correspond to 0~180° of angle
        pulse = int((483-150)/120*pos+150+self.ZeroOffset)
        self.pwm.set_pwm(self.Channel, 0, pulse)

    # End processing
    def Cleanup(self):
        #The servo motor is set at 60°.
        self.SetPos(int(60))
        print('60')

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
				if self.emotion == "talk":
					self.stopTalk = False
				self.emotionsDict[self.emotion]()
				self.changeEmotions = False
        self.rate.sleep()
		return



if __name__ == '__main__':
	rospy.init_node("servo")
	
	rate = rospy.Rate(10) # 10hz
    
	fm = FaceMotor("motor_face_handler")
	fm.set_servos()
	fm.main()
	

	#degs son los grados de cada emocion
    #evaluar los grados a mano
    
    #mouth1.SetPos(int(deg))
    #mouth2.SetPos(int(deg))
    #mouth3.SetPos(int(deg))
    #eyeled1.SetPos(int(deg))
    #eyeled2.SetPos(int(deg))
    
	#mouth1.set_position(command ={'value':801}) 