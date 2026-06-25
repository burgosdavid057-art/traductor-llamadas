"""
STT (voz -> texto) con faster-whisper.
Un solo modelo cargado en GPU; protegido con un lock para uso desde 2 hilos.
"""
import threading
import torch  # noqa: F401
from faster_whisper import WhisperModel


class STT:
    def __init__(self, modelo="small", device="cuda", compute_type="int8_float16"):
        self.model = WhisperModel(modelo, device=device, compute_type=compute_type)
        self._lock = threading.Lock()

    def transcribir(self, audio_f32, idioma=None):
        """
        Transcribe audio a texto.

        audio_f32 : numpy float32 mono 16 kHz.
        idioma    : codigo ISO del idioma (p.ej. 'es'). None = deteccion automatica.
        Devuelve  : (texto, idioma_detectado).
        """
        with self._lock:
            segments, info = self.model.transcribe(
                audio_f32,
                language=idioma,
                beam_size=1,
                vad_filter=False,
            )
            texto = " ".join(s.text.strip() for s in segments).strip()
        return texto, info.language
