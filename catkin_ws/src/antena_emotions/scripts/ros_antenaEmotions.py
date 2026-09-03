#!/usr/bin/env python3
#CREATED WITH NEOVIM

import rospy
import time
import RPi.GPIO as GPIO  #Importamos el paquete RPi.GPIO y en el código nos refiriremos a el como GPIO
from std_msgs.msg import Float64
from std_msgs.msg import String
from std_msgs.msg import Bool



pin_led_red = 27  #Variable que contiene el pin(GPIO.BCM) al cual conectamos la señal del LED
pin_led_green =18
pin_led_blue = 25


GPIO.setmode(GPIO.BCM)   #Establecemos el modo según el cual nos refiriremos a los GPIO de nuestra RPi            
GPIO.setup(pin_led_red, GPIO.OUT) #Configuramos el GPIO23 como salida
GPIO.setup(pin_led_green, GPIO.OUT)
GPIO.setup(pin_led_blue, GPIO.OUT)


class AntenaEmotionsNode(object):
    def __init__(self, name):
        self.name = name
        rospy.init_node(self.name)
        self.rate = rospy.Rate(10)  #   10Hz
        self.initSubscribers()
        self.initPublishers()
        self.initVariables()

    def initSubscribers(self):
        self.emotionsSub = rospy.Subscriber('/emotions', String, self.callbackEm)
        self.ledControlSub = rospy.Subscriber('/led_control', String, self.callbackLed)
        return

    def initPublishers(self):
        self.antenaemotionsPub = rospy.Publisher('/antena_emotions', String, queue_size = 10)
        return

    def initVariables(self):
        self.new_emotion = False
        self.emotion = String()
        self.antemotion = String()
        return

    #callbacks
    def callbackEm(self, msg):         #solo para tomar los datos del nodo (subscritor)
        self.new_emotion = True
        self.emotion = msg.data 
        return

    def callbackLed(self, msg):         #solo para tomar los datos del nodo (subscritor)
        color = msg.data.lower()        
        if color == 'red':
            self.red()
        elif color == 'green':
            self.green()
        elif color == 'blue':
            self.blue()
        elif color == 'yellow':
            self.yellow()
        else:
            self.off()

    def red(self):
        GPIO.output(pin_led_red,GPIO.HIGH)
        GPIO.output(pin_led_green,GPIO.LOW)
        GPIO.output(pin_led_blue,GPIO.LOW)
    
    def green(self):
        GPIO.output(pin_led_red,GPIO.LOW)
        GPIO.output(pin_led_green,GPIO.HIGH)
        GPIO.output(pin_led_blue,GPIO.LOW)

    def blue(self):
        GPIO.output(pin_led_red,GPIO.LOW)
        GPIO.output(pin_led_green,GPIO.LOW)
        GPIO.output(pin_led_blue,GPIO.HIGH)

    def yellow(self):
        GPIO.output(pin_led_red,GPIO.HIGH)
        GPIO.output(pin_led_green,GPIO.HIGH) 
        GPIO.output(pin_led_blue,GPIO.LOW)

    def off(self):
        GPIO.output(pin_led_red, GPIO.LOW)
        GPIO.output(pin_led_green,GPIO.LOW)
        GPIO.output(pin_led_blue, GPIO.LOW)

    def AntenaEmotion(self):
        if self.emotion == 'happy':
            self.antemotion.data = "green"
            self.green()
            time.sleep(3)
            self.off()
        elif self.emotion == 'angry':
            self.antemotion.data = "red"
            self.red()
            time.sleep(3)
            self.off()
        elif self.emotion == 'sad':
            self.antemotion.data = "blue"
            self.blue()
            time.sleep(3)
            self.off()
        else:
            self.antemotion.data = "yellow"   #neutro y sorprendido
            self.yellow()
            time.sleep(3)
            self.off()

        self.antenaemotionsPub.publish(self.antemotion)
        return

    def main(self):
        rospy.loginfo("[%s] ROS Antena node started ok", self.name)
        while not (rospy.is_shutdown()):
            if self.new_emotion:
                self.new_emotion = False
                self.AntenaEmotion()
            rospy.sleep(0.1)
        return

if __name__=='__main__':
    AntenaEmotions = AntenaEmotionsNode("AntenaEmotions")
    AntenaEmotions.main()
