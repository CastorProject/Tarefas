#!/usr/bin/env python3

import argparse
import queue
import sys
import sounddevice as sd
from vosk import Model, KaldiRecognizer

q = queue.Queue()

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

def transcribe_audio(mic_enabled):
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
            "-m", "--model", type=str, help="language model; e.g. es, fr, nl; default is es")
    args = parser.parse_args(remaining)

    try:
        if args.samplerate is None:
            device_info = sd.query_devices(args.device, "input")
            args.samplerate = int(device_info["default_samplerate"])
                    
        if args.model is None:
            model = Model(lang="pt")
        else:
            model = Model(lang=args.model)

        if args.filename:
            dump_fn = open(args.filename, "wb")
        else:
            dump_fn = None

        with sd.RawInputStream(samplerate=args.samplerate, blocksize=8000, device=args.device,
                        dtype="int16", channels=1, callback=callback):
            rec = KaldiRecognizer(model, args.samplerate)
            while True:
                if not(mic_enabled):
                    # parser.exit(0)
                    break
                data = q.get()
                if rec.AcceptWaveform(data):
                    text_detected = rec.Result()
                    find_start = text_detected.find(":") + 3
                    find_last = text_detected.rfind('"')
                    text_detected = text_detected[find_start:find_last]
                    yield text_detected

    except Exception as e:
        parser.exit(type(e).__name__ + ": " + str(e))
