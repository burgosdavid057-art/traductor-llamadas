"""
Graba una muestra de tu voz para que XTTS la clone.

    python grabar_voz.py                 # graba 20 s a voces/mi_voz.wav
    python grabar_voz.py voces/otra.wav 25

Mejora la muestra automaticamente: recorta silencios, normaliza el volumen
y avisa si quedo demasiado baja o ruidosa para clonar bien.
"""
import os
import sys
import time
import numpy as np
import soundcard as sc
import soundfile as sf

import config
from src import dispositivos

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

SR = 24000
BLOQUE = 0.1


def recortar_silencio(x, sr, margen=0.2):
    """
    Quita silencio al inicio y final.

    x      : array numpy float32 mono.
    sr     : sample rate.
    margen : segundos de margen a dejar alrededor de la voz detectada.
    """
    pico = float(np.abs(x).max())
    if pico <= 0:
        return x
    umbral = max(0.015, pico * 0.06)
    activos = np.where(np.abs(x) > umbral)[0]
    if len(activos) == 0:
        return x
    ini = max(0, activos[0] - int(margen * sr))
    fin = min(len(x), activos[-1] + int(margen * sr))
    recortado = x[ini:fin]
    if len(recortado) < 4 * sr and len(x) >= 4 * sr:
        return x
    return recortado


def main():
    destino = sys.argv[1] if len(sys.argv) > 1 else "voces/mi_voz.wav"
    segundos = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    os.makedirs(os.path.dirname(destino) or ".", exist_ok=True)

    mic = dispositivos.microfono(config.MIC_NOMBRE)
    print(f"Microfono REAL: {mic.name}")
    if "cable" in mic.name.lower():
        print("AVISO: estas usando el CABLE virtual. Edita MIC_NOMBRE en config.py.")
    print("\nVas a grabar tu voz. Consejos:")
    print("  - Acercate al microfono (20-30 cm).")
    print("  - Habla con energia y naturalidad, sin gritar.")
    print("  - Lugar silencioso, sin musica ni ventiladores.\n")
    input("Pulsa ENTER para empezar...")

    for n in (3, 2, 1):
        print(f"  {n}...", end="", flush=True)
        time.sleep(1)
    print("  HABLA AHORA!")

    bloques = []
    n_bloques = int(segundos / BLOQUE)
    picos = []
    with mic.recorder(samplerate=SR, channels=1) as rec:
        for i in range(n_bloques):
            data = rec.record(numframes=int(SR * BLOQUE))
            mono = data.mean(axis=1) if data.ndim > 1 else data
            bloques.append(mono)
            pico = float(np.abs(mono).max())
            picos.append(pico)
            barras = int(min(1.0, pico * 3) * 30)
            seg_rest = segundos - i * BLOQUE
            print(f"\r  [{'#'*barras}{' '*(30-barras)}] {seg_rest:4.1f}s ", end="", flush=True)
    print("\n  Listo.")

    audio = np.concatenate(bloques).astype(np.float32)
    rms_bruto = float(np.sqrt((audio ** 2).mean()))
    pico_bruto = float(np.abs(audio).max())

    raw = os.path.splitext(destino)[0] + "_raw.wav"
    sf.write(raw, audio, SR)

    audio = recortar_silencio(audio, SR)
    if pico_bruto > 0:
        audio = (audio / pico_bruto * 0.95).astype(np.float32)

    sf.write(destino, audio, SR)
    dur = len(audio) / SR
    print(f"   (respaldo crudo: {raw}, {len(np.concatenate(bloques))/SR:.1f}s)")
    print(f"\nGuardado en {destino}  ({dur:.1f}s utiles)")
    print(f"   Nivel grabado: pico {pico_bruto:.3f} | RMS {rms_bruto:.4f}")

    if pico_bruto < 0.05:
        print("\nAVISO: MUY BAJO. Tu microfono casi no capto senal.")
        print("   -> Sube el volumen del microfono en Windows y regraba.")
    elif rms_bruto < 0.01:
        print("\nAVISO: Volumen bajo. Funcionara pero podria sonar con algo de ruido.")
        print("   -> Para mejor calidad: sube el micro en Windows y/o acercate y regraba.")
    elif pico_bruto > 0.99:
        print("\nAVISO: Saturado (clipping). Habla un poco mas lejos o baja el micro y regraba.")
    else:
        print("\nBuen nivel. Deberia clonar bien.")

    print("\nComo subir el microfono en Windows:")
    print("  Configuracion -> Sistema -> Sonido -> (Entrada) tu microfono ->")
    print("  Propiedades -> Nivel de entrada al 100. Si hay 'Boost', subelo.")


if __name__ == "__main__":
    main()
