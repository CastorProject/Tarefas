#!/usr/bin/env python3
import rospy
import time
from std_msgs.msg import Float64
from std_msgs.msg import String
from std_msgs.msg import Bool
from dynamixel_workbench_msgs.srv import DynamixelCommand, DynamixelCommandRequest

from adafruit_servokit import ServoKit

#Constants

#Parameters
MIN_IMP  = 500
MAX_IMP  = 2500
MIN_ANG  = 0
MAX_ANG  = 180

#Objects
pca = ServoKit(channels = 16)
servo_number_elbow_left = 14
servo_number_elbow_right = 15


class dynamixelManagerNode(object):
	def __init__(self, name):
		self.name = name
		rospy.init_node(self.name)
		self.rate = rospy.Rate(10)
		self.initSubscribers()
		self.initPublishers()
		self.initVariables()
		return

	def initSubscribers(self):
		self.movementSub = rospy.Subscriber('/movements', String, self.callbackMovements)
		self.stopMoveSub = rospy.Subscriber('/stopMove', Bool, self.callbackStopMove)
		return

	def initPublishers(self):
		return

	def initVariables(self):
		self.servo_motor_elbow_right = pca.servo[servo_number_elbow_right]	# Motor movement with time
		self.servo_motor_elbow_right.set_pulse_width_range(MIN_IMP , MAX_IMP)
		self.servo_motor_elbow_left = pca.servo[servo_number_elbow_left]	# Motor movement with time
		self.servo_motor_elbow_left.set_pulse_width_range(MIN_IMP , MAX_IMP)

		self.servo_motor_elbow_right_movement = 0				# Angle
		self.servo_motor_elbow_left_movement = 0				# Angle

		self.motorPosition = Float64()
		self.stopMove = Bool()
		self.movement = String()
		self.emotion = String()
		self.changeMovement = False
		self.mainMovementsDict = {
			"neutral": self.setNeutralPosition,
			"wave": self.wave,
			"highfive": self.highfive,
			"down_highfive": self.down_highfive,
			"dance": self.dance,
			"hugOpen1": self.hugOpen1,
			"hugClose": self.hugClose,
			"hugNeutral": self.hugNeutral
		}

		self.setNeutralPosition()						# Set Origin Position
		return

	#Callbacks
	def callbackMovements(self, msg):
		self.movement = msg.data
		self.changeMovement = True
		return

	def callbackStopMove(self, msg):
		self.changeMovement = msg.data
		return
		
	#Services
	def motor_service(self):
		rospy.wait_for_service('/dynamixel_workbench/dynamixel_command')
		return

	#Main Movements
	def setNeutralPosition(self):
		self.changeMovement = False
		
		# Setting motor elbow right in origin position
		if self.servo_motor_elbow_right_movement < 90:
			for i in range(self.servo_motor_elbow_right_movement, 90, 1):
				self.servo_motor_elbow_right.angle = i
				time.sleep(0.005)
		else:
			for i in range(self.servoMotor_movement, 90, -1):
				self.servo_motor_elbow_right.angle = i
				time.sleep(0.005)

		self.servo_motor_elbow_right_movement = 90
		self.servo_motor_elbow_right.angle = None		# Disable channel

		# Setting motor elbow left in origin position
		if self.servo_motor_elbow_left_movement < 90:
			for i in range(self.servo_motor_elbow_right_movement, 90, 1):
				self.servo_motor_elbow_left.angle = i
				time.sleep(0.005)
		else:
			for i in range(self.servo_motor_elbow_left_movement, 90, -1):
				self.servo_motor_elbow_left.angle = i
				time.sleep(0.005)
		self.servo_motor_elbow_left_movement = 90
		self.servo_motor_elbow_left.angle = None		# Disable channel

		# Create a ROS service proxy
		service_proxy = rospy.ServiceProxy('/dynamixel_workbench/dynamixel_command', DynamixelCommand)
		# Create a service request message
		service_request = DynamixelCommandRequest() 

		service_request.command = ''
		service_request.id = 1
		service_request.addr_name = 'Goal_Position'
		service_request.value = 300
		# Call the service
		service_response = service_proxy(service_request)		  
		time.sleep(0.5)

		service_request.command = ''
		service_request.id = 2
		service_request.addr_name = 'Goal_Position'
		service_request.value = 3500
		# Call the service
		service_response = service_proxy(service_request)		  
		time.sleep(0.5)

		service_request.command = ''
		service_request.id = 5
		service_request.addr_name = 'Goal_Position'
		service_request.value = 1500
		# Call the service
		service_response = service_proxy(service_request)		  
		time.sleep(0.5)

		service_request.command = ''
		service_request.id = 1
		service_request.addr_name = 'Torque_Enable'
		service_request.value = False
		# Call the service
		service_response = service_proxy(service_request)
		time.sleep(0.5)

		service_request.command = ''
		service_request.id = 2
		service_request.addr_name = 'Torque_Enable'
		service_request.value = False
		# Call the service
		service_response = service_proxy(service_request)
		time.sleep(0.5)

		service_request.command = ''
		service_request.id = 5
		service_request.addr_name = 'Torque_Enable'
		service_request.value = False
		# Call the service
		service_response = service_proxy(service_request)
		time.sleep(0.5)
		return

	def wave(self): # left arm
		try:
			# Create a ROS service proxy
			service_proxy = rospy.ServiceProxy('/dynamixel_workbench/dynamixel_command', DynamixelCommand)
			# Create a service request message
			service_request = DynamixelCommandRequest() 
			
			self.servo_motor_elbow_right_movement = 0
			for i in range(90, self.servo_motor_elbow_right_movement, -1):
				self.servo_motor_elbow_right.angle = i
				time.sleep(0.008)

			service_request.command = ''
			service_request.id = 2
			service_request.addr_name = 'Goal_Position'
			service_request.value = 1200
			# Call the service
			service_response = service_proxy(service_request)		  
			time.sleep(0.5)
			
			service_request.command = ''
			service_request.id = 2
			service_request.addr_name = 'Goal_Position'
			service_request.value = 3500
			# Call the service
			service_response = service_proxy(service_request)	 
			time.sleep(0.5)
			
			service_request.command = ''
			service_request.id = 2
			service_request.addr_name = 'Goal_Position'
			service_request.value = 1200
			# Call the service
			service_response = service_proxy(service_request)		  
			time.sleep(0.5)
			
			service_request.command = ''
			service_request.id = 2
			service_request.addr_name = 'Goal_Position'
			service_request.value = 3500
			# Call the service
			service_response = service_proxy(service_request)	 
			time.sleep(0.5)

			service_request.command = ''
			service_request.id = 2
			service_request.addr_name = 'Torque_Enable'
			service_request.value = False
			# Call the service
			service_response = service_proxy(service_request)

			for i in range(self.servo_motor_elbow_right_movement, 90, 1):
				self.servo_motor_elbow_right.angle = i
				time.sleep(0.01)
			self.servo_motor_elbow_right.angle = None 		# Disable channel

		except rospy.ServiceException as exc:
			rospy.logwarn("[%s] Service did not process request: " + str(exc), self.name)
			
		self.setNeutralPosition()
		return

	def highfive(self):		#left arm
		self.changeMovement = False
		# Create a ROS service proxy
		service_proxy = rospy.ServiceProxy('/dynamixel_workbench/dynamixel_command', DynamixelCommand)
		# Create a service request message
		service_request = DynamixelCommandRequest()

		service_request.command = ''
		service_request.id = 5
		service_request.addr_name = 'Goal_Position'
		service_request.value = 2800
		# Call the service
		service_response = service_proxy(service_request)	 
		time.sleep(0.5)

		self.servo_motor_elbow_left_movement = 180
		for i in range(90, self.servo_motor_elbow_left_movement, 1):
			self.servo_motor_elbow_left.angle = i
			time.sleep(0.008)
		return
		
	def down_highfive(self):		#left arm
		self.changeMovement = False
		# Create a ROS service proxy
		service_proxy = rospy.ServiceProxy('/dynamixel_workbench/dynamixel_command', DynamixelCommand)
		# Create a service request message
		service_request = DynamixelCommandRequest()

		service_request.command = ''
		service_request.id = 5
		service_request.addr_name = 'Goal_Position'
		service_request.value = 1500
		# Call the service
		service_response = service_proxy(service_request)	 
		time.sleep(0.5)

		for i in range(self.servo_motor_elbow_left_movement, 90, -1):
			self.servo_motor_elbow_left.angle = i
			time.sleep(0.008)
		self.setNeutralPosition()
		return

	def dance(self):
		try:
			# Create a ROS service proxy
			service_proxy = rospy.ServiceProxy('/dynamixel_workbench/dynamixel_command', DynamixelCommand)
			# Create a service request message
			service_request = DynamixelCommandRequest() 
			
			service_request.command = ''
			service_request.id = 2
			service_request.addr_name = 'Goal_Position'
			service_request.value = 1200
			# Call the service
			service_response = service_proxy(service_request)
			time.sleep(0.3)
			
			self.servo_motor_elbow_right_movement = 0
			for i in range(90, self.servo_motor_elbow_right_movement, -1):
				self.servo_motor_elbow_right.angle = i
				time.sleep(0.005)
			
			service_request.command = ''
			service_request.id = 1
			service_request.addr_name = 'Goal_Position'
			service_request.value = 150
			# Call the service
			service_response = service_proxy(service_request)
			time.sleep(0.3)			  
			
			for i in range(self.servo_motor_elbow_right_movement, 90, 1):
				self.servo_motor_elbow_right.angle = i
				time.sleep(0.005)

			service_request.command = ''
			service_request.id = 2
			service_request.addr_name = 'Goal_Position'
			service_request.value = 3500
			# Call the service
			service_response = service_proxy(service_request)
			time.sleep(0.3)
			
			service_request.command = ''
			service_request.id = 5
			service_request.addr_name = 'Goal_Position'
			service_request.value = 2800
			# Call the service
			service_response = service_proxy(service_request)
			time.sleep(0.3)
			
			self.servo_motor_elbow_left_movement = 180
			for i in range(90, self.servo_motor_elbow_left_movement, 1):
				self.servo_motor_elbow_left.angle = i
				time.sleep(0.005)

			service_request.command = ''
			service_request.id = 1
			service_request.addr_name = 'Goal_Position'
			service_request.value = 538
			# Call the service
			service_response = service_proxy(service_request)
			time.sleep(0.3) 
			
			for i in range(self.servo_motor_elbow_left_movement, 90, -1):
				self.servo_motor_elbow_left.angle = i
				time.sleep(0.005)

			service_request.command = ''
			service_request.id = 5
			service_request.addr_name = 'Goal_Position'
			service_request.value = 1500
			# Call the service
			service_response = service_proxy(service_request)
			time.sleep(0.3)
			
			service_request.command = ''
			service_request.id = 1
			service_request.addr_name = 'Goal_Position'
			service_request.value = 315
			# Call the service
			service_response = service_proxy(service_request)
			time.sleep(0.3)
			
		except rospy.ServiceException as exc:
			rospy.logwarn("[%s] Service did not process request: " + str(exc), self.name)	 
		return

	def hugOpen1(self):
		self.changeMovement = False
		try:
			# Create a ROS service proxy
			service_proxy = rospy.ServiceProxy('/dynamixel_workbench/dynamixel_command', DynamixelCommand)
			# Create a service request message
			service_request = DynamixelCommandRequest() 
			
			service_request.command = ''
			service_request.id = 2
			service_request.addr_name = 'Goal_Position'
			service_request.value = 1500
			# Call the service
			service_response = service_proxy(service_request)
			time.sleep(0.5)
			
			service_request.command = ''
			service_request.id = 5
			service_request.addr_name = 'Goal_Position'
			service_request.value = 2800
			# Call the service
			service_response = service_proxy(service_request)
			time.sleep(0.5)
			
			self.servo_motor_elbow_right_movement = 180
			for i in range(90, self.servo_motor_elbow_right_movement, 1):
				self.servo_motor_elbow_right.angle = i
				time.sleep(0.005)

			self.servo_motor_elbow_left_movement = 0
			for i in range(90, self.servo_motor_elbow_left_movement, -1):
				self.servo_motor_elbow_left.angle = i
				time.sleep(0.005)

		except rospy.ServiceException as exc:
			rospy.logwarn("[%s] Service did not process request: " + str(exc), self.name)
		return

	def hugClose(self):
		self.changeMovement = False
		self.servo_motor_elbow_right_movement = 0
		for i in range(180, self.servo_motor_elbow_right_movement, -1):
			self.servo_motor_elbow_right.angle = i
			time.sleep(0.005)

		self.servo_motor_elbow_left_movement = 180
		for i in range(0, self.servo_motor_elbow_left_movement, 1):
			self.servo_motor_elbow_left.angle = i
			time.sleep(0.005)
		return
		
	def hugNeutral(self):
		self.setNeutralPosition()
		return		  

	#Main
	def main(self):
		rospy.loginfo("[%s] dynamixel motor manager node started ok", self.name)
		motor_srv = self.motor_service()
		while not (rospy.is_shutdown()):
			if self.changeMovement:
				try:
					self.mainMovementsDict[self.movement]()
				except:
					pass
		return

if __name__=='__main__':
	dynamixelManager = dynamixelManagerNode("dynamixelManager")
	dynamixelManager.main()