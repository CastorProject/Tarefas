"""
================================================================================
Módulo de Audição (STT) — CASTOR
================================================================================
PROJETO: CASTOR — LabTEL/UFES
PESQUISADORA: Vitória Gomes Fagundes
================================================================================
"""

import os
import queue
import sys
import sounddevice as sd
from vosk import Model, KaldiRecognizer
import vosk

vosk.SetLogLevel(-1)

PASTA_ATUAL = os.path.dirname(os.path.abspath(__file__))
NOME_MODELO = "vosk-model-small-pt-0.3-castor"
fila_audio  = queue.Queue()


def encontrar_modelo_vosk():
    candidatos = [
        os.path.join(PASTA_ATUAL, NOME_MODELO),
        os.path.join(PASTA_ATUAL, "..", "..", "models", NOME_MODELO),
        os.path.join(PASTA_ATUAL, "..", "models", NOME_MODELO),
        "/home/pi/catkin_ws/src/microphone/scripts/vosk-model-small-pt-0.3-castor",
        "/home/pi/catkin_ws/models/vosk-model-small-pt-0.3-castor",
    ]
    for caminho in candidatos:
        caminho_real = os.path.realpath(caminho)
        if os.path.exists(caminho_real):
            print("  Modelo encontrado: {}".format(caminho_real))
            return caminho_real
    print("  Modelo nao encontrado!")
    return None


def encontrar_microfone_real():
    todos = sd.query_devices()

    # 1. USB Audio direto (Raspberry Pi sem PulseAudio)
    for i, dev in enumerate(todos):
        nome = dev["name"].lower()
        if "usb audio" in nome and dev["max_input_channels"] > 0:
            taxa = int(dev["default_samplerate"])
            print("  Microfone: [{}] {} ({} Hz) [USB]".format(i, dev["name"], taxa))
            return i, taxa

    # 2. PulseAudio (Ubuntu/Linux com pulse ativo)
    for i, dev in enumerate(todos):
        if dev["name"].lower() == "pulse" and dev["max_input_channels"] > 0:
            taxa = int(dev["default_samplerate"])
            print("  Microfone: [{}] {} ({} Hz) [PulseAudio]".format(i, dev["name"], taxa))
            return i, taxa

    # 3. PipeWire
    for i, dev in enumerate(todos):
        if "pipewire" in dev["name"].lower() and dev["max_input_channels"] > 0:
            taxa = int(dev["default_samplerate"])
            print("  Microfone: [{}] {} ({} Hz) [PipeWire]".format(i, dev["name"], taxa))
            return i, taxa

    # 4. Padrao
    info = sd.query_devices(None, "input")
    taxa = int(info["default_samplerate"])
    print("  Microfone padrao ({} Hz)".format(taxa))
    return None, taxa


def callback_audio(indata, frames, time, status):
    fila_audio.put(bytes(indata))


def transcribe_audio(mic_enabled):
    """Compativel com o ros_microphone.py original."""
    try:
        indice_mic, taxa_amostragem = encontrar_microfone_real()
        caminho_modelo = encontrar_modelo_vosk()
        if not caminho_modelo:
            return

        print("  Carregando modelo Vosk...")
        modelo = Model(caminho_modelo)
        print("  Pronto! Pode falar.")

        with sd.RawInputStream(
            device=indice_mic,
            samplerate=taxa_amostragem,
            blocksize=8000,
            dtype="int16",
            channels=1,
            callback=callback_audio
        ):
            reconhecedor = KaldiRecognizer(modelo, taxa_amostragem)

            while True:
                if not mic_enabled:
                    break

                dados = fila_audio.get()

                if reconhecedor.AcceptWaveform(dados):
                    resultado   = reconhecedor.Result()
                    inicio      = resultado.find('"text" : "') + 10
                    fim         = resultado.rfind('"')
                    texto_final = resultado[inicio:fim].strip()

                    if texto_final:
                        yield texto_final

    except Exception as e:
        print("  Erro na audicao: {}".format(e))


# Alias para compatibilidade
def transcrever_audio(mic_ativo):
    return transcribe_audio(mic_ativo)


if __name__ == "__main__":
    print("CASTOR — Teste do Microfone")
    print("Fale algo! (Ctrl+C para parar)\n")
    try:
        for frase in transcribe_audio(True):
            print("  Ouvido: {}".format(frase))
    except KeyboardInterrupt:
        print("\n  Encerrado.")
