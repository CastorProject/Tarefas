"""
================================================================================
Módulo de Audição (STT)
================================================================================
PROJETO: CASTOR — LabTEL/UFES
DESCRIÇÃO: Transforma voz em texto usando o motor Vosk.
           Funciona no notebook, na Raspberry Pi e no Windows sem configuração.
           Encontra o modelo Vosk automaticamente em qualquer estrutura de pasta.
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

fila_audio = queue.Queue()


def encontrar_modelo_vosk() -> str:
    """
    Procura o modelo Vosk em vários lugares possíveis.
    Funciona no notebook, na Raspberry e em qualquer estrutura de pasta.
    Retorna o caminho se encontrar, None se não encontrar.
    """
    # Lista de lugares para procurar — do mais específico ao mais geral
    candidatos = [
        # Mesma pasta do script (Raspberry com estrutura simples)
        os.path.join(PASTA_ATUAL, NOME_MODELO),
        # Dois níveis acima em models/ (estrutura do PC com catkin_ws)
        os.path.join(PASTA_ATUAL, "..", "..", "models", NOME_MODELO),
        # Um nível acima em models/
        os.path.join(PASTA_ATUAL, "..", "models", NOME_MODELO),
        # Três níveis acima em models/
        os.path.join(PASTA_ATUAL, "..", "..", "..", "models", NOME_MODELO),
        # Caminhos absolutos comuns na Raspberry Pi
        f"/home/pi/catkin_ws/models/{NOME_MODELO}",
        f"/home/pi/catkin_ws/src/microphone/scripts/{NOME_MODELO}",
        # Caminho absoluto comum no notebook
        os.path.join(os.path.expanduser("~"), "models", NOME_MODELO),
    ]

    for caminho in candidatos:
        caminho_real = os.path.realpath(caminho)  # resolve ../ e links simbólicos
        if os.path.exists(caminho_real):
            print(f"  📁 Modelo encontrado: {caminho_real}")
            return caminho_real

    # Não achou em nenhum lugar — mostra onde procurou para facilitar debug
    print(f"  ❌ Modelo '{NOME_MODELO}' não encontrado!")
    print("  Lugares procurados:")
    for c in candidatos:
        print(f"    {os.path.realpath(c)}")
    print("  Baixe em: https://alphacephei.com/vosk/models")
    return None


def encontrar_microfone_real() -> tuple:
    """
    Encontra automaticamente o melhor microfone disponível.

    Prioridade:
      1. pulse  → Ubuntu/Linux com PulseAudio (mais comum)
      2. pipewire → Ubuntu mais novo
      3. hw:    → dispositivo físico direto (fallback Linux)
      4. padrão → último recurso

    Retorna (indice_dispositivo, taxa_amostragem)
    """
    todos = sd.query_devices()

    # --- Estratégia 1: pulse (Ubuntu/Linux) ---
    for i, dev in enumerate(todos):
        if dev["name"].lower() == "pulse" and dev["max_input_channels"] > 0:
            taxa = int(dev["default_samplerate"])
            print(f"  🎤 Microfone: [{i}] {dev['name']} ({taxa} Hz) [PulseAudio]")
            return i, taxa

    # --- Estratégia 2: pipewire (Ubuntu mais novo) ---
    for i, dev in enumerate(todos):
        if dev["name"].lower() == "pipewire" and dev["max_input_channels"] > 0:
            taxa = int(dev["default_samplerate"])
            print(f"  🎤 Microfone: [{i}] {dev['name']} ({taxa} Hz) [PipeWire]")
            return i, taxa

    # --- Estratégia 3: dispositivo físico hw: ---
    PREFERIR = [
        # Linux / Raspberry Pi
        "analog", "cs42", "cs8409", "alc", "bcm2835",
        "seeed", "respeaker", "usb audio",
        # Windows
        "realtek", "array", "microphone", "headset", "mic",
    ]
    for i, dev in enumerate(todos):
        nome = dev["name"].lower()
        if "hw:" in nome and dev["max_input_channels"] > 0:
            if any(bom in nome for bom in PREFERIR):
                taxa = int(dev["default_samplerate"])
                print(f"  🎤 Microfone: [{i}] {dev['name']} ({taxa} Hz) [hardware]")
                return i, taxa

    # --- Estratégia 4: padrão do sistema ---
    info = sd.query_devices(None, "input")
    taxa = int(info["default_samplerate"])
    print(f"  🎤 Microfone: padrão do sistema ({taxa} Hz)")
    return None, taxa


def selecionar_modo_interacao():
    """Pergunta ao usuário como quer interagir com o robô."""
    print("\n--- Menu de Interação do CASTOR ---")
    print("1. 🎤 Modo Voz (Ouvir)")
    print("2. ⌨️  Modo Texto (Teclado)")
    escolha = input("Selecione (1 ou 2): ").strip()
    return "voz" if escolha == "1" else "texto"


def callback_audio(indata, frames, time, status):
    """Captura áudio do microfone e coloca na fila."""
    if status:
        print(status, file=sys.stderr)
    fila_audio.put(bytes(indata))


def transcrever_audio(mic_ativo):
    """
    Ouve o microfone e transforma em texto usando Vosk.
    Usa yield para entregar cada frase reconhecida sem travar o programa.
    """
    try:
        # Encontra o microfone certo automaticamente
        indice_mic, taxa_amostragem = encontrar_microfone_real()

        # Encontra o modelo Vosk automaticamente
        caminho_modelo = encontrar_modelo_vosk()
        if not caminho_modelo:
            return  # encerra se não encontrar o modelo

        print("  📦 Carregando modelo Vosk...")
        modelo = Model(caminho_modelo)
        print("  ✅ Pronto! Pode falar.\n")

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
                if not mic_ativo:
                    break

                dados = fila_audio.get()

                if reconhecedor.AcceptWaveform(dados):
                    resultado   = reconhecedor.Result()
                    inicio      = resultado.find('"text" : "') + 10
                    fim         = resultado.rfind('"')
                    texto_final = resultado[inicio:fim]

                    if texto_final.strip():
                        yield texto_final

    except Exception as e:
        print(f"  ❌ Erro crítico na audição: {e}")


# Teste manual — rode: python3 microphone_listen.py
if __name__ == "__main__":
    print("\n=====================================")
    print("  CASTOR — Teste do Módulo de Audição")
    print("=====================================")
    print("Fale algo! (Ctrl+C para parar)\n")

    try:
        for frase in transcrever_audio(mic_ativo=True):
            print(f"  Ouvido: {frase}")
    except KeyboardInterrupt:
        print("\n  Audição encerrada.")