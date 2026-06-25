"""
Captura de audio y segmentacion por voz (VAD).

Expone un generador que entrega frases completas (numpy float32 mono a 16 kHz)
a partir de un recorder de soundcard. Usa webrtcvad para detectar cuando
termino de hablar la persona y cortar segmentos limpios.
"""
import numpy as np
import webrtcvad

SAMPLE_RATE = 16000
FRAME_MS = 30
FRAME_LEN = int(SAMPLE_RATE * FRAME_MS / 1000)


def _a_int16_bytes(frame_f32: np.ndarray) -> bytes:
    clip = np.clip(frame_f32, -1.0, 1.0)
    return (clip * 32767).astype(np.int16).tobytes()


def segmentos_de_voz(recorder, agresividad=2, silencio_ms=700,
                     max_segmento_s=15, gate=None, parar=None):
    """
    Generador de segmentos de voz.

    recorder      : objeto recorder de soundcard (ya dentro de su with).
    agresividad   : 0-3 (que tan estricto es el VAD al decidir si hay voz).
    silencio_ms   : silencio necesario para dar la frase por terminada.
    max_segmento_s: corte de seguridad para frases interminables.
    gate          : threading.Event opcional. Si esta set(), descarta el audio
                    (p.ej. mientras suena una traduccion) para evitar eco.
    parar         : threading.Event opcional. Si esta set(), termina el generador.
    """
    vad = webrtcvad.Vad(agresividad)
    max_silencio = max(1, silencio_ms // FRAME_MS)
    max_frames = int(max_segmento_s * 1000 / FRAME_MS)

    activo = False
    buffer = []
    silencio = 0

    while True:
        if parar is not None and parar.is_set():
            return
        data = recorder.record(numframes=FRAME_LEN)
        mono = data.mean(axis=1) if data.ndim > 1 else data
        if len(mono) < FRAME_LEN:
            continue
        frame = mono[:FRAME_LEN]

        if gate is not None and gate.is_set():
            activo, buffer, silencio = False, [], 0
            continue

        es_voz = vad.is_speech(_a_int16_bytes(frame), SAMPLE_RATE)

        if not activo:
            if es_voz:
                activo = True
                buffer = [frame]
                silencio = 0
        else:
            buffer.append(frame)
            silencio = 0 if es_voz else silencio + 1
            if silencio >= max_silencio or len(buffer) >= max_frames:
                yield np.concatenate(buffer).astype(np.float32)
                activo, buffer, silencio = False, [], 0
