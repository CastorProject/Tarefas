#!/usr/bin/env python3

from hashlib import sha256
from pathlib import Path
import os
import subprocess
import unicodedata


BASE_DIR = Path(__file__).resolve().parent.parent
CACHE_DIR = BASE_DIR / "generated_audio" / "cache"

VOICE_VERSION = "pt_BR-castor-medium-legacy-v1"

CONTAINER_NAME = "castor-piper"
PIPER_BIN = "/opt/piper/piper"

MODEL_PATH = (
    "/models/pt_BR-castor-medium/"
    "pt_BR-castor-medium.onnx"
)

CONFIG_PATH = (
    "/models/pt_BR-castor-medium/"
    "pt_BR-castor-medium.legacy.onnx.json"
)

OUTPUT_DIR_CONTAINER = "/output/cache"


def normalize_text(text):
    return unicodedata.normalize(
        "NFC",
        str(text).strip(),
    )


def get_audio_path(text):
    cache_data = "{}\0{}".format(
        VOICE_VERSION,
        text,
    )

    cache_key = sha256(
        cache_data.encode("utf-8")
    ).hexdigest()[:24]

    return CACHE_DIR / "{}.wav".format(
        cache_key
    )


def is_valid_audio(audio_file):
    return (
        audio_file.is_file()
        and audio_file.stat().st_size > 44
    )


def generate_audio(text, audio_file):
    CACHE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary_file = audio_file.with_suffix(
        ".tmp.wav"
    )

    container_output = "{}/{}".format(
        OUTPUT_DIR_CONTAINER,
        temporary_file.name,
    )

    container_user = "{}:{}".format(
        os.getuid(),
        os.getgid(),
    )

    command = [
        "docker",
        "exec",
        "-i",
        "--user",
        container_user,
        CONTAINER_NAME,
        PIPER_BIN,
        "--model",
        MODEL_PATH,
        "--config",
        CONFIG_PATH,
        "--output_file",
        container_output,
    ]

    try:
        subprocess.run(
            command,
            input=text + "\n",
            text=True,
            check=True,
        )

        if not is_valid_audio(temporary_file):
            raise RuntimeError(
                "O Piper não gerou um WAV válido."
            )

        temporary_file.replace(audio_file)

    finally:
        if temporary_file.exists():
            temporary_file.unlink()


def prepare_audio(text):
    """Localiza ou gera qualquer áudio, sem reproduzir."""
    text = normalize_text(text)

    if not text:
        raise ValueError(
            "O texto não pode estar vazio."
        )

    CACHE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    audio_file = get_audio_path(text)

    if is_valid_audio(audio_file):
        print(
            "Áudio encontrado no cache: {}".format(
                audio_file.name
            )
        )
    else:
        print("Áudio não encontrado. Gerando...")
        generate_audio(text, audio_file)

        print(
            "Áudio gerado: {}".format(
                audio_file.name
            )
        )

    return str(audio_file)


def speaker(text):
    """Prepara e reproduz qualquer texto."""
    audio_file = prepare_audio(text)

    subprocess.run(
        [
            "aplay",
            "-q",
            audio_file,
        ],
        check=True,
    )

    return audio_file


def greeting_text(face_name):
    """Cria a saudação utilizada no cadastro facial."""
    name = normalize_text(face_name)

    if not name:
        raise ValueError(
            "O nome não pode estar vazio."
        )

    return "Olá {}, que bom te ver de novo!".format(
        name
    )


def prepare_greeting(face_name):
    """Gera a saudação durante o cadastro, sem reproduzir."""
    return prepare_audio(
        greeting_text(face_name)
    )


def speak_greeting(face_name):
    """Reproduz a saudação quando o rosto é reconhecido."""
    return speaker(
        greeting_text(face_name)
    )