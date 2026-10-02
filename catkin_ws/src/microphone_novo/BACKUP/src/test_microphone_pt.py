#!/usr/bin/env python3

# prerequisites: as described in https://alphacephei.com/vosk/install and also python module `sounddevice` (simply run command `pip install sounddevice`)
# Example usage using Dutch (nl) recognition model: `python test_microphone.py -m nl`
# For more help run: `python test_microphone.py -h`

import argparse
import queue
import sys
import sounddevice as sd
import rospy
import time
from std_msgs.msg import Float64
from std_msgs.msg import String
from std_msgs.msg import Bool

from vosk import Model, KaldiRecognizer

q = queue.Queue()

######################################
################ ROS #################
######################################
rospy.init_node('microphone')
rospy.Rate(10)
######################################
############# PUBLISHERS #############
######################################
#pubEmotions = rospy.Publisher('/emotions', String, queue_size = 10)
pubSpeaker = rospy.Publisher('/speaker', String, queue_size = 10)
pubMicrophone = rospy.Publisher('/microphone', String, queue_size = 10)
pubSpeakerAction = rospy.Publisher('/speakerAction', String, queue_size = 15)
#pubMovements = rospy.Publisher('/movements', String, queue_size = 5)
######################################
######################################
######################################

def MicrophoneNode(textdetected):
	if "castor" in textdetected:
		#pubEmotions.publish("talk")
		#pubMovements.publish("wave")
		#time.sleep(0.5)
		pubSpeaker.publish("castor_apresentacao")

	elif "ola" in textdetected:
		#pubEmotions.publish("talk")
		#pubMovements.publish("wave")
		#time.sleep(0.5)
		pubSpeaker.publish("me_chamo_castor")

	elif "canta" in textdetected:
		#pubEmotions.publish("talk")
		#pubMovements.publish("wave")
		#time.sleep(0.5)
		pubSpeaker.publish("canta1")
	elif "cachorro" in textdetected:
		#pubEmotions.publish("talk")
		#pubMovements.publish("wave")
		#time.sleep(0.5)
		pubSpeaker.publish("cachorro_faz")
	elif "tchau" in textdetected:
		#pubEmotions.publish("talk")
		#pubMovements.publish("wave")
		#time.sleep(0.5)
		pubSpeaker.publish("tchau_amiga")





def int_or_str(text):
    """Helper function for argument parsing."""
    try:
        return int(text)
    except ValueError:
        return text

def callback(indata, frames, time, status):
    """This is called (from a separate thread) for each audio block."""
    if status:
        print(status, file=sys.stderr)
    q.put(bytes(indata))

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument(
    "-l", "--list-devices", action="store_true",
    help="show list of audio devices and exit")
args, remaining = parser.parse_known_args()
if args.list_devices:
    print(sd.query_devices())
    parser.exit(0)
parser = argparse.ArgumentParser(
    description=__doc__,
    formatter_class=argparse.RawDescriptionHelpFormatter,
    parents=[parser])
parser.add_argument(
    "-f", "--filename", type=str, metavar="FILENAME",
    help="audio file to store recording to")
parser.add_argument(
    "-d", "--device", type=int_or_str,
    help="input device (numeric ID or substring)")
parser.add_argument(
    "-r", "--samplerate", type=int, help="sampling rate")
parser.add_argument(
    "-m", "--model", type=str, help="language model; e.g. pt, fr, nl; default is pt")
args = parser.parse_args(remaining)

try:
    if args.samplerate is None:
        device_info = sd.query_devices(args.device, "input")
        # soundfile expects an int, sounddevice provides a float:
        args.samplerate = int(device_info["default_samplerate"])
        
    if args.model is None:
        model = Model(lang="pt")
    else:
        model = Model(lang=args.model)

    if args.filename:
        dump_fn = open(args.filename, "wb")
    else:
        dump_fn = None

    with sd.RawInputStream(samplerate=args.samplerate, blocksize = 8000, device=args.device,
            dtype="int16", channels=1, callback=callback):
        print("#" * 80)
        print("Press Ctrl+C to stop the recording")
        print("#" * 80)

        rec = KaldiRecognizer(model, args.samplerate)
        while True:
            data = q.get()
            if rec.AcceptWaveform(data):
                textdetected=rec.Result()
                print(rec.Result())
                pubMicrophone.publish("Publishing %s"%textdetected)
                MicrophoneNode(textdetected)

            else:
                print(rec.PartialResult())
            if dump_fn is not None:
                dump_fn.write(data)

except KeyboardInterrupt:
    print("\nDone")
    parser.exit(0)
except Exception as e:
    parser.exit(type(e).__name__ + ": " + str(e))
