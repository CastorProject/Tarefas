#! /usr/bin/env python
import time
import rospy
import subprocess

from flask import Flask, render_template, request
import threading

from std_msgs.msg import Float64
from std_msgs.msg import String
from std_msgs.msg import Bool

######################################
################ ROS #################
######################################
threading.Thread(target=lambda: rospy.init_node('mainMenuHTML', disable_signals=True)).start()
######################################
############# PUBLISHERS #############
######################################
pubEmotions = rospy.Publisher('/emotions', String, queue_size = 10)
pubSpeaker = rospy.Publisher('/speaker', String, queue_size = 10)
pubSpeakerAction = rospy.Publisher('/speakerAction', String, queue_size = 15)
pubMovements = rospy.Publisher('/movements', String, queue_size = 5)
pubCastorSystem = rospy.Publisher('/castor_system', String, queue_size = 5)
######################################
############# MAIN MENU ##############
######################################
app = Flask(__name__)
@app.route("/")
def mainMenu():
    templateData = {
        'title' : 'Main Menu',
    }
    return render_template('mainMenu.html', **templateData)

@app.route("/<action>")
def actionMainMenu(action):
    if action == "greet1":
        pubEmotions.publish("talk")
        pubMovements.publish("wave")
        time.sleep(0.5)
        pubSpeaker.publish("1")
        template = "mainMenu.html"

    elif action == "greet2":
        pubEmotions.publish("talk")
        pubMovements.publish("wave")
        time.sleep(0.5)
        pubSpeaker.publish("2")
        template = "mainMenu.html"

    elif action == "happy":
        pubEmotions.publish("happy")
        template = "mainMenu.html"

    elif action == "sad":
        pubEmotions.publish("sad")
        template = "mainMenu.html"

    elif action == "angry":
        pubEmotions.publish("angry")
        template = "mainMenu.html"

    elif action == "surprise":
        pubEmotions.publish("surprise")
        template = "mainMenu.html"

    elif action == "neutral":
        pubEmotions.publish("neutral")
        template = "mainMenu.html"

    elif action == "highfive":
        pubMovements.publish("highfive")
        template = "mainMenu.html"

    elif action == "point_head":
        pubMovements.publish("pointHead")
        template = "mainMenu.html"

    elif action == "point_eyes":
        pubMovements.publish("pointEyes")
        template = "mainMenu.html"

    elif action == "point_nose":
        pubMovements.publish("pointNose")
        template = "mainMenu.html"

    elif action == "Baile_gorila":
        pubEmotions.publish("talk")
        time.sleep(0.5)
        pubSpeaker.publish("Baile_gorila")
        template = "mainMenu.html"

    elif action == "Baile_animales":
        pubEmotions.publish("talk")
        time.sleep(0.5)
        pubSpeaker.publish("Baile_animales")
        template = "mainMenu.html"

    elif action == "ambulancia":
        pubEmotions.publish("talk")
        time.sleep(0.5)
        pubSpeaker.publish("ambulancia")
        template = "mainMenu.html"

    elif action == "A_mi_burro":
        pubEmotions.publish("talk")
        time.sleep(0.5)
        pubSpeaker.publish("A_mi_burro")
        template = "mainMenu.html"

    elif action == "play":
        pubSpeakerAction.publish("unpause")
        template = "mainMenu.html"

    elif action == "pause":
        pubSpeakerAction.publish("pause")
        template = "mainMenu.html"

    elif action == "stop":
        pubSpeakerAction.publish("stop")
        template = "mainMenu.html"

    elif action == "shutdown":
        template = "shutdown.html"

    elif action == "reboot":
        template = "reboot.html"

    templateData = {
        'title' : 'Main Menu',
    }
    return render_template(template, **templateData)

#########################################
################ Shutdown ###############
#########################################
@app.route("/shutdown/<action>")
def action1(action):
    if action == "yes":
        pubCastorSystem.publish("shutdown")
        time.sleep(0.5)
        subprocess.call(['sudo', 'shutdown', 'now'], shell=False)
        template = "shutdown.html"

    elif action == "no":
        print("no")
        template = "mainMenu.html"

    templateData = {
        'title' : 'Shutdown',
    }
    return render_template(template, **templateData)

#########################################
################ Reboot ###############
#########################################
@app.route("/reboot/<action>")
def action2(action):
    if action == "yes":
        pubCastorSystem.publish("reboot")
        time.sleep(0.5)
        subprocess.call(['sudo', 'reboot', 'now'], shell=False)
        template = "reboot.html"

    elif action == "no":
        template = "mainMenu.html"

    templateData = {
        'title' : 'Reboot',
    }
    return render_template(template, **templateData)

if __name__ == "__main__":
   app.run(host='0.0.0.0', port=5000, debug=True)
