#!/usr/bin/env python3

import rospy

from std_msgs.msg import String
from std_msgs.msg import Bool

import microphone_listen



class MicrophoneNode(object):

    def __init__(self):

        rospy.init_node("microphone")


        # ==================================================
        # VARIÁVEIS
        # ==================================================

        # começa desligado igual ao seu
        self.start_mic = False


        # controla se o robô está falando
        self.speaker_busy = False


        # força reset do Vosk após fala do robô
        self.reset_after_speaker = False



        # ==================================================
        # SUBSCRIBERS
        # ==================================================

        rospy.Subscriber(
            "/mic",
            String,
            self.mic_callback
        )


        rospy.Subscriber(
            "/stopTalk",
            Bool,
            self.stop_talk_callback
        )



        # ==================================================
        # PUBLISHER
        # ==================================================

        self.microphone_pub = rospy.Publisher(
            "/microphone",
            String,
            queue_size=10
        )





    # ==================================================
    # CONTROLE DO MICROFONE
    # ==================================================

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





    # ==================================================
    # CONTROLE DO SPEAKER
    # ==================================================

    def stop_talk_callback(self, msg):


        estava_falando = self.speaker_busy


        self.speaker_busy = msg.data




        if self.speaker_busy:


            rospy.loginfo(
                "Speaker active. Ignoring microphone."
            )



        elif estava_falando:


            self.reset_after_speaker = True


            rospy.loginfo(
                "Speaker finished. Resetting Vosk."
            )







    # ==================================================
    # FUNÇÕES PASSADAS PARA microphone_listen
    # ==================================================

    def mic_enabled(self):

        return self.start_mic





    def should_process_audio(self):


        # botão desligado

        if not self.start_mic:

            return False



        # robô falando

        if self.speaker_busy:

            return False



        return True





    def should_reset_audio(self):


        if self.reset_after_speaker:


            self.reset_after_speaker = False


            return True



        return False





    # ==================================================
    # LOOP PRINCIPAL
    # ==================================================

    def run(self):


        rospy.loginfo(
            "Microphone node started"
        )



        while not rospy.is_shutdown():



            try:


                for text in microphone_listen.transcribe_audio(


                    self.mic_enabled,

                    self.should_process_audio,

                    self.should_reset_audio


                ):



                    if rospy.is_shutdown():

                        break




                    text = str(text).strip()




                    if text == "":

                        continue





                    # evita publicar se desligou no meio

                    if not self.should_process_audio():

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