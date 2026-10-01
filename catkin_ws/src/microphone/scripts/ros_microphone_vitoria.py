#!/usr/bin/env python3

import rospy

from std_msgs.msg import String

import microphone_listen_vitoria as microphone_listen


class MicrophoneNode(object):

    def __init__(self):

        rospy.init_node("microphone_vitoria")

        # Começa desativado
        self.start_mic = False

        # Recebe "Activo" e "Inactivo"
        rospy.Subscriber(
            "/mic",
            String,
            self.mic_callback
        )

        # Publica o texto reconhecido
        self.microphone_pub = rospy.Publisher(
            "/microphone",
            String,
            queue_size=10
        )


    def mic_callback(self, msg):

        estado = msg.data.strip()

        if estado == "Activo":

            self.start_mic = True

            rospy.loginfo(
                "Microphone enabled"
            )


        elif estado == "Inactivo":

            self.start_mic = False

            rospy.loginfo(
                "Microphone disabled"
            )


    def mic_enabled(self):

        return self.start_mic


    def run(self):

        rospy.loginfo(
            "Microphone node started"
        )

        while not rospy.is_shutdown():

            try:

                # transcribe_audio fica aberto continuamente.
                for text in microphone_listen.transcribe_audio(
                    self.mic_enabled
                ):

                    if rospy.is_shutdown():
                        break

                    text = str(text).strip()

                    if text == "":
                        continue

                    # Evita publicar caso o mic tenha sido
                    # desligado enquanto o Vosk finalizava.
                    if not self.start_mic:
                        continue

                    rospy.loginfo(
                        "Detected speech: %s",
                        text
                    )

                    self.microphone_pub.publish(
                        text
                    )

            except Exception as e:

                rospy.logerr(
                    "Microphone error: %s",
                    e
                )

                rospy.sleep(1)


if __name__ == "__main__":

    node = MicrophoneNode()

    node.run()