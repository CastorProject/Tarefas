#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import subprocess
import sys
import json
import threading
import queue
import time
import os

import rospy

from vosk import Model, KaldiRecognizer

# Flag criada pelo speaker enquanto o Castor esta falando.
# Enquanto ela existir o audio capturado e descartado, para
# que o robo nao escute a propria voz (realimentacao).
FLAG_FALANDO = "/tmp/castor_falando.flag"


def castor_esta_falando():
    return os.path.exists(FLAG_FALANDO)


_cached_model = None


# ============================================================
# MODELO VOSK
# ============================================================

CAMINHO_MODELO_CASTOR = "/home/pi/catkin_ws/src/microphone_novo/scripts/vosk-model-small-pt-0.3-castor"


def get_model(model_lang):

    global _cached_model

    if _cached_model is None:

        rospy.loginfo(
            "Carregando modelo Vosk customizado (Castor)..."
        )

        _cached_model = Model(
            model_path=CAMINHO_MODELO_CASTOR
        )

        rospy.loginfo(
            "Modelo Vosk carregado."
        )

    return _cached_model


# ============================================================
# RESULTADO FINAL
# ============================================================

def extract_text(vosk_result):

    try:

        result = json.loads(
            vosk_result
        )

        return result.get(
            "text",
            ""
        ).strip()

    except Exception:

        return ""


# ============================================================
# RESULTADO PARCIAL
# ============================================================

def extract_partial(vosk_result):

    try:

        result = json.loads(
            vosk_result
        )

        return result.get(
            "partial",
            ""
        ).strip()

    except Exception:

        return ""


# ============================================================
# ARECORD
# ============================================================

def start_arecord(
    device,
    samplerate
):

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

        # Buffer ALSA de 500 ms
        "-B",
        "500000",

        # Periodo ALSA de 100 ms
        "-F",
        "100000",

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

        # Mantém mensagens do ALSA visíveis
        stderr=None,

        bufsize=0
    )


# ============================================================
# LIMPAR FILA
# ============================================================

def limpar_fila(
    audio_queue
):

    quantidade = 0

    while True:

        try:

            audio_queue.get_nowait()

            quantidade += 1

        except queue.Empty:

            break


    if quantidade > 0:

        rospy.loginfo(
            "Fila limpa: %d blocos descartados na mudanca de estado.",
            quantidade
        )


# ============================================================
# THREAD DE CAPTURA
# ============================================================

def captura_audio(
    process,
    audio_queue,
    stop_event,
    chunk_size
):

    """
    Thread exclusiva para capturar o audio.

    Ela não executa o Vosk.

    Portanto, mesmo que o reconhecimento demore,
    continuamos lendo o arecord.
    """

    rospy.loginfo(
        "Thread de captura de audio iniciada."
    )


    while not stop_event.is_set():

        try:

            data = process.stdout.read(
                chunk_size
            )

        except Exception as e:

            rospy.logerr(
                "Erro ao ler audio: %s",
                e
            )

            break


        if not data:

            rospy.logerr(
                "arecord parou de fornecer audio."
            )

            break


        # IMPORTANTE:
        #
        # A fila é ilimitada.
        #
        # Não descartamos nenhum bloco de
        # áudio durante a fala.
        audio_queue.put(
            data
        )


# ============================================================
# RECONHECEDOR
# ============================================================

def criar_reconhecedor(
    model,
    samplerate
):

    # Usa o comportamento PADRÃO do Vosk.
    #
    # Não alteramos o endpointer neste teste.
    return KaldiRecognizer(
        model,
        samplerate
    )


# ============================================================
# TRANSCRIÇÃO
# ============================================================

def transcribe_audio(
    mic_enabled_func
):

    parser = argparse.ArgumentParser(
        description=(
            "CASTOR microphone listener "
            "using arecord + Vosk"
        )
    )


    # --------------------------------------------------------
    # DISPOSITIVO
    # --------------------------------------------------------

    parser.add_argument(
        "-d",
        "--device",

        type=str,

        default="plughw:2,0",

        help="ALSA input device"
    )


    # --------------------------------------------------------
    # SAMPLE RATE
    # --------------------------------------------------------

    parser.add_argument(
        "-r",
        "--samplerate",

        type=int,

        # Mantemos 44.1 kHz porque foi melhor
        # no seu conjunto microfone + Raspberry.
        default=16000,

        help="sample rate"
    )


    # --------------------------------------------------------
    # MODELO
    # --------------------------------------------------------

    parser.add_argument(
        "-m",
        "--model",

        type=str,

        default=None,

        help="Vosk model language; default pt"
    )


    args = parser.parse_args(
        rospy.myargv(
            argv=sys.argv
        )[1:]
    )


    rospy.loginfo(
        "Using ALSA input device: %s",
        args.device
    )


    rospy.loginfo(
        "Using sample rate: %d Hz",
        args.samplerate
    )


    # ========================================================
    # MODELO VOSK
    # ========================================================

    model = get_model(
        args.model
    )


    rec = criar_reconhecedor(
        model,
        args.samplerate
    )


    # ========================================================
    # ARECORD
    # ========================================================

    process = start_arecord(
        args.device,
        args.samplerate
    )


    # ========================================================
    # TAMANHO DO BLOCO
    # ========================================================

    # 4096 bytes
    #
    # 16 bits = 2 bytes por amostra
    #
    # 4096 / 2 = 2048 amostras
    #
    # 2048 / 16000 = aproximadamente 0.128 s
    #
    # Portanto cada bloco representa
    # aproximadamente 46 ms de audio.
    chunk_size = 4096


    # ========================================================
    # FILA DE AUDIO
    # ========================================================

    # SEM maxsize.
    #
    # Dessa forma nenhum áudio é descartado
    # durante este teste.
    audio_queue = queue.Queue()


    # ========================================================
    # THREAD
    # ========================================================

    stop_event = threading.Event()


    thread_captura = threading.Thread(
        target=captura_audio,

        args=(
            process,
            audio_queue,
            stop_event,
            chunk_size
        )
    )


    thread_captura.daemon = True

    thread_captura.start()


    # ========================================================
    # ESTADOS
    # ========================================================

    estado_anterior = False

    ultimo_partial = ""

    ultimo_log_fila = time.time()


    try:

        while not rospy.is_shutdown():

            # =================================================
            # PEGA AUDIO DA FILA
            # =================================================

            try:

                data = audio_queue.get(
                    timeout=0.2
                )

                if castor_esta_falando():
                    continue

            except queue.Empty:

                # Verifica se o arecord morreu
                if process.poll() is not None:

                    raise RuntimeError(
                        "arecord stopped"
                    )

                continue


            # =================================================
            # ESTADO DO MICROFONE
            # =================================================

            ativo = mic_enabled_func()


            # =================================================
            # DIAGNOSTICO DA FILA
            # =================================================

            agora = time.time()


            if (
                ativo
                and agora - ultimo_log_fila >= 2.0
            ):

                tamanho_fila = (
                    audio_queue.qsize()
                )


                # Cada amostra possui 2 bytes
                #
                # atraso =
                # bytes acumulados /
                # bytes por segundo
                atraso_estimado = (
                    tamanho_fila
                    * chunk_size
                    / (
                        args.samplerate
                        * 2.0
                    )
                )


                rospy.loginfo(
                    "Fila audio: %d blocos | "
                    "atraso aproximado: %.2f s",
                    tamanho_fila,
                    atraso_estimado
                )


                ultimo_log_fila = agora


            # =================================================
            # MUDANÇA ACTIVO / INACTIVO
            # =================================================

            if ativo != estado_anterior:

                # Reconhecedor novo para evitar
                # restos da frase anterior.
                rec = criar_reconhecedor(
                    model,
                    args.samplerate
                )


                # Descarta apenas o áudio que ficou
                # antes da mudança de estado.
                limpar_fila(
                    audio_queue
                )


                ultimo_partial = ""

                estado_anterior = ativo


                if ativo:

                    rospy.loginfo(
                        "Vosk pronto para reconhecer."
                    )

                else:

                    rospy.loginfo(
                        "Vosk desativado. "
                        "Audio sendo descartado."
                    )


                continue


            # =================================================
            # MICROFONE DESATIVADO
            # =================================================

            if not ativo:

                # O áudio continua sendo capturado
                # e consumido, mas não entra no Vosk.
                continue


            # =================================================
            # MICROFONE ATIVADO
            # =================================================

            if rec.AcceptWaveform(
                data
            ):

                # ---------------------------------------------
                # RESULTADO FINAL
                # ---------------------------------------------

                text_detected = extract_text(
                    rec.Result()
                )


                ultimo_partial = ""


                if text_detected != "":

                    yield text_detected


            else:

                # ---------------------------------------------
                # RESULTADO PARCIAL
                # ---------------------------------------------

                partial = extract_partial(
                    rec.PartialResult()
                )


                if (
                    partial != ""
                    and partial != ultimo_partial
                ):

                    rospy.loginfo(
                        "Partial speech: %s",
                        partial
                    )


                    ultimo_partial = partial


    finally:

        # =====================================================
        # ENCERRAMENTO
        # =====================================================

        stop_event.set()


        try:

            process.terminate()

        except Exception:

            pass


        try:

            thread_captura.join(
                timeout=1.0
            )

        except Exception:

            pass