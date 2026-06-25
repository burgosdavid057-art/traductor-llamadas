"""
Traductor de llamadas en tiempo real (local).

Dos flujos simultaneos:
  - SALIDA  : tu microfono -> Whisper -> Ollama -> XTTS (tu voz) -> VB-Cable -> ellos
  - ENTRADA : audio de la llamada (loopback) -> Whisper -> Ollama -> XTTS -> tus parlantes

Uso:
    python main.py                       # usa los idiomas de config.py
    python main.py --tu es --ellos en    # tu hablas español, ellos ingles
    python main.py --sin-voz-entrante    # ellos solo en subtitulos (evita eco)

Ctrl+C en la terminal o Esc en la ventana para salir.
"""
import argparse
import sys
import threading
import time

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import numpy as np
import soundcard as sc

import config
from src import dispositivos
from src.audio import segmentos_de_voz, SAMPLE_RATE
from src.stt import STT
from src.traductor import Traductor
from src.voz import Voz, XTTS_SR
from src.subtitulos import Subtitulos

GATE = threading.Event()


def reproducir(wave, speaker, sr=XTTS_SR):
    """Reproduce un numpy float32 en el parlante dado (objeto soundcard)."""
    if wave is None or len(wave) == 0:
        return
    GATE.set()
    try:
        with speaker.player(samplerate=sr) as p:
            p.play(wave)
    finally:
        time.sleep(0.15)
        GATE.clear()


def reproducir_stream(trozos, speaker, sr=XTTS_SR):
    """Reproduce trozos de audio a medida que llegan."""
    GATE.set()
    try:
        with speaker.player(samplerate=sr) as p:
            for t in trozos:
                if t is not None and len(t):
                    p.play(t)
    finally:
        time.sleep(0.15)
        GATE.clear()


def flujo_salida(stt, trad, voz, subt, tu_idioma, idioma_ellos, ref_voz, mic, salida_virtual):
    """TU hablas -> traduccion con tu voz hacia VB-Cable."""
    with mic.recorder(samplerate=SAMPLE_RATE, channels=1) as rec:
        print(f"[SALIDA] tu microfono: {mic.name}  ->  envio a: {salida_virtual.name}")
        for seg in segmentos_de_voz(rec, config.VAD_AGRESIVIDAD,
                                    config.SILENCIO_MS, config.MAX_SEGMENTO_S, GATE):
            texto, _ = stt.transcribir(seg, idioma=tu_idioma)
            if not texto:
                continue
            print(f"[TU] {texto}")
            traduccion = trad.traducir(texto, tu_idioma, idioma_ellos)
            subt and subt.actualizar("tu", traduccion)
            print(f"[TU->ellos] {traduccion}")
            reproducir_stream(voz.sintetizar_stream(traduccion, ref_voz, idioma_ellos),
                              salida_virtual)


def flujo_entrada(stt, trad, voz, subt, tu_idioma, idioma_ellos, ref_voz, con_voz, escucha):
    """ELLOS hablan -> traduccion a tu idioma en subtitulos (+ voz opcional)."""
    loop = dispositivos.loopback_de(escucha)
    with loop.recorder(samplerate=SAMPLE_RATE, channels=1) as rec:
        print(f"[ENTRADA] capturo la llamada desde: {escucha.name} (loopback)")
        for seg in segmentos_de_voz(rec, config.VAD_AGRESIVIDAD,
                                    config.SILENCIO_MS, config.MAX_SEGMENTO_S, GATE):
            texto, _ = stt.transcribir(seg, idioma=idioma_ellos)
            if not texto:
                continue
            print(f"[ELLOS] {texto}")
            traduccion = trad.traducir(texto, idioma_ellos, tu_idioma)
            subt and subt.actualizar("ellos", traduccion)
            print(f"[ellos->TU] {traduccion}")
            if con_voz:
                reproducir_stream(voz.sintetizar_stream(traduccion, ref_voz, tu_idioma),
                                  escucha)


def main():
    ap = argparse.ArgumentParser(description="Traductor de llamadas local")
    ap.add_argument("--tu", default=config.TU_IDIOMA, help="tu idioma (es, en, pt...)")
    ap.add_argument("--ellos", default=config.IDIOMA_ELLOS, help="idioma de la otra persona")
    ap.add_argument("--sin-voz-entrante", action="store_true",
                    help="no reproducir la voz de ellos (solo subtitulos)")
    ap.add_argument("--sin-subtitulos", action="store_true")
    ap.add_argument("--mic", default=config.MIC_NOMBRE, help="nombre (parcial) de tu microfono real")
    ap.add_argument("--escucha", default=config.PARLANTE_ESCUCHA,
                    help="nombre (parcial) del parlante donde oyes la llamada")
    ap.add_argument("--listar", action="store_true", help="listar dispositivos de audio y salir")
    args = ap.parse_args()

    if args.listar:
        dispositivos.listar()
        return

    tu, ellos = args.tu, args.ellos
    con_voz_entrante = config.VOZ_ENTRANTE and not args.sin_voz_entrante
    usar_subt = config.SUBTITULOS and not args.sin_subtitulos

    mic = dispositivos.microfono(args.mic)
    salida_virtual = dispositivos.parlante_por_nombre(config.DISPOSITIVO_VIRTUAL)
    escucha = dispositivos.parlante(args.escucha)

    print("Cargando modelos... (la primera vez XTTS descarga ~2 GB)")
    stt = STT(config.WHISPER_MODELO, config.WHISPER_DEVICE, config.WHISPER_COMPUTE)
    trad = Traductor(config.OLLAMA_MODELO, config.IDIOMAS)
    voz = Voz(config.XTTS_DEVICE)
    subt = Subtitulos() if usar_subt else None

    print(f"\n  TU hablas: {config.IDIOMAS.get(tu, tu)}  ->  ELLOS oyen: {config.IDIOMAS.get(ellos, ellos)}")
    print(f"  Microfono real : {mic.name}")
    print(f"  Hacia la llamada: {salida_virtual.name}")
    print(f"  Escucho llamada : {escucha.name}")
    print(f"  Voz entrante: {'si' if con_voz_entrante else 'no (solo subtitulos)'}\n")

    hilos = [
        threading.Thread(target=flujo_salida, daemon=True,
                         args=(stt, trad, voz, subt, tu, ellos, config.REF_TU_VOZ, mic, salida_virtual)),
        threading.Thread(target=flujo_entrada, daemon=True,
                         args=(stt, trad, voz, subt, tu, ellos, config.REF_VOZ_ELLOS, con_voz_entrante, escucha)),
    ]
    for h in hilos:
        h.start()

    if subt:
        subt.iniciar()
    else:
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nSaliendo...")


if __name__ == "__main__":
    main()
