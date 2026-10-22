#!/usr/bin/env python3

from hashlib import sha256
from pathlib import Path
from datetime import datetime
import json
import logging
import os
import random
import re
import shutil
import subprocess
import threading
import unicodedata
import uuid


BASE_DIR = Path(__file__).resolve().parent.parent
CACHE_DIR = BASE_DIR / "generated_audio" / "cache"
AUDIO_DIR = Path(os.environ.get("CASTOR_AUDIO_DIR", str(BASE_DIR.parents[4] / "audios"))).expanduser().resolve()
GREETING_DIR = AUDIO_DIR / "saudacoes"
REGISTRATION_DIR = AUDIO_DIR / "cadastro_facial"

_PREPARATION_LOCK = threading.RLock()
_PLAYBACK_LOCK = threading.Lock()

GREETINGS = (
    ("01_que_bom_ver_voce", "Olá, {nome}! Que bom ver você!"),
    ("02_alegria_ter_sua_companhia", "Oi, {nome}! É uma alegria ter sua companhia!"),
    ("03_felicidade_encontrar_voce", "Olá, {nome}! Que felicidade encontrar você!"),
    ("04_que_bom_ter_voce_aqui", "Que bom ter você por aqui, {nome}!"),
    ("05_bom_dia", "Bom dia, {nome}!"),
    ("06_boa_tarde", "Boa tarde, {nome}!"),
    ("07_boa_noite", "Boa noite, {nome}!"),
    ("08_bom_estar_com_voce", "É bom estar com você, {nome}!"),
)

REGISTRATION_PROMPTS = {
    "inicio": ("01_inicio", "Vamos começar o cadastro facial. Olhe para a câmera, por favor."),
    "captura": ("02_captura", "Isso! Continue olhando para a câmera por mais um instante."),
    "processamento": ("03_processamento", "Estou processando as imagens para preparar seu cadastro."),
    "aguarde": ("04_aguarde", "Só mais um momento. Ainda estou processando as imagens."),
    "concluido": ("05_concluido", "Pronto! Seu cadastro facial foi concluído com sucesso."),
    "nova_tentativa": ("06_nova_tentativa", "Não consegui capturar seu rosto com nitidez. Olhe para a câmera para tentarmos novamente."),
}

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
    audio_file = Path(audio_file)
    audio_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary_file = audio_file.with_name(
        "{}.{}.tmp.wav".format(audio_file.stem, uuid.uuid4().hex)
    )
    # Both paths are bind mounts in compose.yaml. Keep nested ID folders.
    try:
        relative_path = temporary_file.resolve().relative_to(AUDIO_DIR.resolve())
        container_output = "/audios/" + relative_path.as_posix()
    except ValueError:
        relative_path = temporary_file.resolve().relative_to(CACHE_DIR.resolve())
        container_output = OUTPUT_DIR_CONTAINER + "/" + relative_path.as_posix()

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
            timeout=120,
        )

        if not is_valid_audio(temporary_file):
            raise RuntimeError(
                "O Piper não gerou um WAV válido."
            )

        temporary_file.replace(audio_file)

    finally:
        if temporary_file.exists():
            temporary_file.unlink()


def _prepare_audio(text):
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


def prepare_audio(text):
    """Preserva o cache genérico usado pelas outras atividades."""
    with _PREPARATION_LOCK:
        return _prepare_audio(text)


def playback_command(audio_file):
    audio_file = Path(audio_file)
    if audio_file.suffix.lower() == ".wav":
        return ["aplay", "-q", str(audio_file)]
    if audio_file.suffix.lower() == ".mp3":
        if shutil.which("mpg123"):
            return ["mpg123", "-q", str(audio_file)]
        if shutil.which("ffplay"):
            return ["ffplay", "-nodisp", "-autoexit", "-loglevel", "error", str(audio_file)]
        raise RuntimeError("Para reproduzir MP3, instale mpg123: sudo apt install mpg123")
    raise ValueError("Formato de áudio não suportado: {}".format(audio_file.suffix))


def play_audio(audio_file, cancel_event=None):
    """Reproduz WAV/MP3, serializando as falas deste processo."""
    cancel_event = cancel_event or threading.Event()
    with _PLAYBACK_LOCK:
        if cancel_event.is_set():
            return False
        command = playback_command(audio_file)
        process = subprocess.Popen(command)
        try:
            while process.poll() is None:
                if cancel_event.wait(0.1):
                    process.terminate()
                    try:
                        process.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()
                    return False
            if process.returncode:
                raise subprocess.CalledProcessError(process.returncode, command)
        finally:
            if process.poll() is None:
                process.kill()
                process.wait()
    return True


def speaker(text):
    """Prepara e reproduz qualquer texto."""
    audio_file = prepare_audio(text)

    play_audio(audio_file)

    return audio_file


def greeting_text(face_name, variant=0):
    """Mantém a grafia original do nome na fala."""
    name = normalize_text(face_name)

    if not name:
        raise ValueError(
            "O nome não pode estar vazio."
        )

    return GREETINGS[variant][1].format(nome=name)


def person_audio_dir(face_name, face_id):
    """Usa ID estável e nome legível; acompanha correções de nome."""
    name = normalize_text(face_name)
    if not name or isinstance(face_id, bool) or int(face_id) <= 0:
        raise ValueError("Informe nome e ID facial positivo.")
    slug = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "_", slug.lower()).strip("_")[:80] or "pessoa"
    prefix = "{:04d}_".format(int(face_id))
    folder = GREETING_DIR / (prefix + slug)
    GREETING_DIR.mkdir(parents=True, exist_ok=True)
    previous = [path for path in GREETING_DIR.glob(prefix + "*") if path.is_dir()]
    if len(previous) > 1:
        raise RuntimeError("Há mais de uma pasta de áudio para o ID {}.".format(face_id))
    if not folder.exists() and previous:
        # Verifica os dois caminhos antes de mover uma pasta existente.
        folder.resolve().relative_to(GREETING_DIR.resolve())
        previous[0].resolve().relative_to(GREETING_DIR.resolve())
        previous[0].rename(folder)
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def _read_manifest(folder):
    try:
        value = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError):
        return {}


def _write_manifest(folder, manifest):
    temporary = folder / "manifest.tmp.json"
    temporary.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(folder / "manifest.json")


def _prepare_named_audio(folder, stem, text, manifest):
    audio = folder / (stem + ".wav")
    expected = {"text": text, "voice_version": VOICE_VERSION}
    entries = manifest.setdefault("audios", {})
    if entries.get(stem) != expected or not is_valid_audio(audio):
        generate_audio(text, audio)
        entries[stem] = expected
        _write_manifest(folder, manifest)
    return str(audio)


def prepare_greetings(face_name, face_id):
    """Prepara as oito falas no cadastro, sem reproduzi-las."""
    with _PREPARATION_LOCK:
        folder = person_audio_dir(face_name, face_id)
        manifest = _read_manifest(folder)
        manifest.update(face_id=int(face_id), name=normalize_text(face_name))
        audios = {}
        for variant, (stem, _) in enumerate(GREETINGS):
            audios[stem] = _prepare_named_audio(folder, stem, greeting_text(face_name, variant), manifest)
        _write_manifest(folder, manifest)
        return audios


def prepare_greeting(face_name, face_id):
    """Prepara a primeira variação; o cadastro usa prepare_greetings."""
    with _PREPARATION_LOCK:
        folder = person_audio_dir(face_name, face_id)
        manifest = _read_manifest(folder)
        return _prepare_named_audio(folder, GREETINGS[0][0], greeting_text(face_name), manifest)


def eligible_greetings(hour):
    """05–11: manhã; 12–17: tarde; 18–04: noite, no fuso do sistema."""
    period = 4 if 5 <= hour < 12 else 5 if 12 <= hour < 18 else 6
    return [stem for index, (stem, _) in enumerate(GREETINGS) if index not in (4, 5, 6) or index == period]


def speak_greeting(face_name, face_id):
    """Sorteia sem reposição e persiste a última fala por ID."""
    with _PREPARATION_LOCK:
        # Também completa as oito falas de pessoas cadastradas antes da atualização.
        prepare_greetings(face_name, face_id)
        folder = person_audio_dir(face_name, face_id)
        manifest = _read_manifest(folder)
        manifest.update(face_id=int(face_id), name=normalize_text(face_name))
        eligible = eligible_greetings(datetime.now().hour)
        remaining = manifest.get("remaining_greetings", [stem for stem, _ in GREETINGS])
        if not isinstance(remaining, list):
            remaining = []
        candidates = [stem for stem in eligible if stem in remaining and stem != manifest.get("last_greeting")]
        if not candidates:
            remaining = [stem for stem, _ in GREETINGS]
            candidates = [stem for stem in eligible if stem != manifest.get("last_greeting")]
        stem = random.choice(candidates)
        variant = next(index for index, item in enumerate(GREETINGS) if item[0] == stem)
        audio = _prepare_named_audio(folder, stem, greeting_text(face_name, variant), manifest)
        play_audio(audio)
        manifest["last_greeting"] = stem
        manifest["remaining_greetings"] = [item for item in remaining if item != stem]
        _write_manifest(folder, manifest)
        return audio


def prepare_registration_audio(stage):
    """Prioriza o MP3 fornecido; gera WAV pelo Piper se estiver ausente."""
    stem, text = REGISTRATION_PROMPTS[stage]
    mp3 = REGISTRATION_DIR / (stem + ".mp3")
    if is_valid_audio(mp3):
        return str(mp3)
    with _PREPARATION_LOCK:
        REGISTRATION_DIR.mkdir(parents=True, exist_ok=True)
        manifest = _read_manifest(REGISTRATION_DIR)
        return _prepare_named_audio(REGISTRATION_DIR, stem, text, manifest)


def prepare_registration_audios():
    """Prepara antes de aceitar cadastros, para não atrasar as instruções."""
    for stage in REGISTRATION_PROMPTS:
        try:
            prepare_registration_audio(stage)
        except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as error:
            logging.getLogger(__name__).warning("Áudio de cadastro %s indisponível: %s", stage, error)
