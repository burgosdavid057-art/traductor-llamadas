"""
Motor del traductor: carga los modelos y corre los dos flujos (salida/entrada).
Se comunica por callbacks; lo usan tanto la GUI como el CLI.

  on_texto(quien, original, traduccion)  -> 'tu' | 'ellos'
  on_estado(texto)                       -> mensajes de estado
"""
import threading
import time

import soundcard as sc

import config
from src import dispositivos
from src.audio import segmentos_de_voz, SAMPLE_RATE


class Motor:
    def __init__(self, on_texto=None, on_estado=None):
        self.on_texto = on_texto or (lambda quien, orig, trad: None)
        self.on_estado = on_estado or (lambda e: None)
        self.gate = threading.Event()
        self.parar = threading.Event()
        self.stt = self.trad = self.voz = None
        self._hilos = []
        self._cargado = False

    def cargar(self):
        if self._cargado:
            return
        from src.stt import STT
        from src.traductor import Traductor
        from src.voz import Voz
        self.on_estado("Cargando Whisper...")
        self.stt = STT(config.WHISPER_MODELO, config.WHISPER_DEVICE, config.WHISPER_COMPUTE)
        self.on_estado("Conectando con Ollama...")
        self.trad = Traductor(config.LLM_MODELO, config.LLM_BASE_URL, config.LLM_API_KEY, config.IDIOMAS)
        self.on_estado("Cargando voz (XTTS)...")
        self.voz = Voz(config.XTTS_DEVICE)
        self._cargado = True
        self.on_estado("Modelos listos")

    def _reproducir_stream(self, trozos, speaker):
        self.gate.set()
        try:
            with speaker.player(samplerate=24000) as p:
                for t in trozos:
                    if self.parar.is_set():
                        break
                    if t is not None and len(t):
                        p.play(t)
        finally:
            time.sleep(0.15)
            self.gate.clear()

    def _flujo_salida(self, tu, ellos, mic, salida_virtual, ref_voz):
        with mic.recorder(samplerate=SAMPLE_RATE, channels=1) as rec:
            for seg in segmentos_de_voz(rec, config.VAD_AGRESIVIDAD, config.SILENCIO_MS,
                                        config.MAX_SEGMENTO_S, self.gate, self.parar):
                texto, _ = self.stt.transcribir(seg, idioma=tu)
                if not texto:
                    continue
                traduccion = self.trad.traducir(texto, tu, ellos)
                self.on_texto("tu", texto, traduccion)
                self._reproducir_stream(self.voz.sintetizar_stream(traduccion, ref_voz, ellos),
                                        salida_virtual)

    def _flujo_entrada(self, tu, ellos, escucha, ref_voz, con_voz):
        loop = dispositivos.loopback_de(escucha)
        with loop.recorder(samplerate=SAMPLE_RATE, channels=1) as rec:
            for seg in segmentos_de_voz(rec, config.VAD_AGRESIVIDAD, config.SILENCIO_MS,
                                        config.MAX_SEGMENTO_S, self.gate, self.parar):
                texto, _ = self.stt.transcribir(seg, idioma=ellos)
                if not texto:
                    continue
                traduccion = self.trad.traducir(texto, ellos, tu)
                self.on_texto("ellos", texto, traduccion)
                if con_voz:
                    self._reproducir_stream(self.voz.sintetizar_stream(traduccion, ref_voz, tu),
                                            escucha)

    def iniciar(self, tu, ellos, mic_nombre="", escucha_nombre="", voz_entrante=True):
        """Arranca los dos flujos. Requiere haber llamado cargar() antes."""
        if not self._cargado:
            self.cargar()
        self.parar.clear()
        self.gate.clear()

        mic = dispositivos.microfono(mic_nombre)
        salida_virtual = dispositivos.parlante_por_nombre(config.DISPOSITIVO_VIRTUAL)
        escucha = dispositivos.parlante(escucha_nombre)

        self._hilos = [
            threading.Thread(target=self._flujo_salida, daemon=True,
                             args=(tu, ellos, mic, salida_virtual, config.REF_TU_VOZ)),
            threading.Thread(target=self._flujo_entrada, daemon=True,
                             args=(tu, ellos, escucha, config.REF_VOZ_ELLOS, voz_entrante)),
        ]
        for h in self._hilos:
            h.start()
        self.on_estado("Escuchando")
        return {"mic": mic.name, "escucha": escucha.name, "salida": salida_virtual.name}

    def detener(self):
        self.parar.set()
        for h in self._hilos:
            h.join(timeout=2)
        self._hilos = []
        self.on_estado("Detenido")
