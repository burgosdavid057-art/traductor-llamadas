"""
TTS con clonacion de voz (XTTS-v2 de Coqui).

Dos modos:
  - sintetizar()        -> genera todo el audio y lo devuelve.
  - sintetizar_stream() -> generador que va entregando trozos a medida que los
                           genera (baja latencia percibida).

Cachea los latentes de cada voz de referencia para no recalcularlos en cada frase.
"""
import os
import threading
import numpy as np

import config

os.environ.setdefault("COQUI_TOS_AGREED", "1")

XTTS_SR = 24000


class Voz:
    def __init__(self, device="cuda"):
        from TTS.api import TTS
        self.tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)
        self.model = self.tts.synthesizer.tts_model
        self._lock = threading.Lock()
        self._cache = {}

    def _latentes(self, ref_wav):
        if ref_wav not in self._cache:
            gpt, spk = self.model.get_conditioning_latents(audio_path=[ref_wav])
            self._cache[ref_wav] = (gpt, spk)
        return self._cache[ref_wav]

    def _params(self):
        return dict(
            temperature=config.XTTS_TEMPERATURE,
            repetition_penalty=config.XTTS_REP_PENALTY,
            top_k=config.XTTS_TOP_K,
            top_p=config.XTTS_TOP_P,
            speed=config.XTTS_SPEED,
            enable_text_splitting=True,
        )

    def sintetizar(self, texto, ref_wav, idioma):
        """Genera todo el audio de una vez. Devuelve numpy float32 24 kHz."""
        texto = (texto or "").strip()
        if not texto:
            return np.zeros(0, dtype=np.float32)
        with self._lock:
            wav = self.tts.tts(text=texto, speaker_wav=ref_wav, language=idioma, **self._params())
        return np.asarray(wav, dtype=np.float32)

    def sintetizar_stream(self, texto, ref_wav, idioma):
        """
        Generador de audio por trozos.

        texto   : texto a sintetizar.
        ref_wav : ruta al archivo WAV de referencia de voz.
        idioma  : codigo ISO del idioma de salida.
        Yields  : numpy float32 24 kHz por cada trozo generado.
        """
        texto = (texto or "").strip()
        if not texto:
            return
        gpt, spk = self._latentes(ref_wav)
        with self._lock:
            for trozo in self.model.inference_stream(
                texto, idioma, gpt, spk,
                stream_chunk_size=config.XTTS_STREAM_CHUNK,
                **self._params(),
            ):
                yield trozo.squeeze().detach().cpu().numpy().astype(np.float32)
