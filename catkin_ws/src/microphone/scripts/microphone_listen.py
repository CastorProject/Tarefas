#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import argparse
import subprocess
import sys
import json
import threading
import queue

import rospy

from vosk import Model, KaldiRecognizer


CAMINHO_MODELO_CASTOR = "/home/pi/catkin_ws/src/microphone_novo/scripts/vosk-model-small-pt-0.3-castor"

_cached_model = None



# ============================================================
# MODELO VOSK
# ============================================================

def get_model(model_lang):

    global _cached_model


    if _cached_model is None:

        rospy.loginfo("Carregando modelo Vosk...")


        if model_lang is None and os.path.isdir(CAMINHO_MODELO_CASTOR):

            rospy.loginfo("Modelo do Castor: %s", CAMINHO_MODELO_CASTOR)

            _cached_model = Model(model_path=CAMINHO_MODELO_CASTOR)

        elif model_lang is None:

            _cached_model = Model(lang="pt")

        else:

            _cached_model = Model(lang=model_lang)



        rospy.loginfo("Modelo Vosk carregado.")



    return _cached_model




# ============================================================
# RESULTADO VOSK
# ============================================================

def extract_text(result):

    try:

        data = json.loads(result)

        return data.get("text", "").strip()


    except:

        return ""




# ============================================================
# ARECORD
# ============================================================

def start_arecord(device, samplerate):


    cmd = [

        "arecord",

        "-D",
        device,

        "-f",
        "S16_LE",

        "-r",
        str(samplerate),

        "-c",
        "1",

        "-t",
        "raw"

    ]


    rospy.loginfo(
        "Starting arecord: %s",
        " ".join(cmd)
    )



    return subprocess.Popen(

        cmd,

        stdout=subprocess.PIPE,

        stderr=None,

        bufsize=0

    )





# ============================================================
# THREAD DE CAPTURA
# ============================================================

def capture_audio(process, audio_queue, stop_event, chunk_size):


    rospy.loginfo(
        "Audio capture thread started."
    )



    while not stop_event.is_set():


        data = process.stdout.read(chunk_size)



        if not data:

            rospy.logerr(
                "arecord stopped."
            )

            break



        audio_queue.put(data)





# ============================================================
# LIMPA BUFFER
# ============================================================

def clear_queue(audio_queue):


    while True:

        try:

            audio_queue.get_nowait()


        except queue.Empty:

            break





# ============================================================
# RECONHECEDOR
# ============================================================

def create_recognizer(model, samplerate):


    return KaldiRecognizer(

        model,

        samplerate

    )





# ============================================================
# TRANSCRIÇÃO
# ============================================================

def transcribe_audio(

        mic_enabled_func,

        should_process_audio_func,

        should_reset_func):



    parser = argparse.ArgumentParser()



    parser.add_argument(

        "-d",

        "--device",

        default="plughw:2,0"

    )



    parser.add_argument(

        "-r",

        "--samplerate",

        type=int,

        default=44100

    )



    parser.add_argument(

        "-m",

        "--model",

        default=None

    )




    args = parser.parse_args(

        rospy.myargv(argv=sys.argv)[1:]

    )




    model = get_model(args.model)



    rec = create_recognizer(

        model,

        args.samplerate

    )




    process = start_arecord(

        args.device,

        args.samplerate

    )



    chunk_size = 4096



    audio_queue = queue.Queue()



    stop_event = threading.Event()



    thread = threading.Thread(

        target=capture_audio,

        args=(

            process,

            audio_queue,

            stop_event,

            chunk_size

        )

    )



    thread.daemon = True

    thread.start()




    last_state = False




    try:


        while not rospy.is_shutdown():



            try:

                data = audio_queue.get(
                    timeout=0.2
                )


            except queue.Empty:

                continue




            active = mic_enabled_func()





            # mudou estado do botão

            if active != last_state:



                rec = create_recognizer(

                    model,

                    args.samplerate

                )


                clear_queue(
                    audio_queue
                )


                last_state = active



                if active:

                    rospy.loginfo(
                        "Vosk ready."
                    )

                else:

                    rospy.loginfo(
                        "Microphone disabled."
                    )


                continue





            # microfone desligado

            if not active:

                continue




            # robô falando

            if not should_process_audio_func():

                continue





            # reset solicitado

            if should_reset_func():

                rec = create_recognizer(

                    model,

                    args.samplerate

                )

                continue





            if rec.AcceptWaveform(data):


                text = extract_text(

                    rec.Result()

                )


                if text != "":

                    yield text




    finally:


        stop_event.set()



        try:

            process.terminate()

        except:

            pass