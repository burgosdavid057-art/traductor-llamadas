"""
Configuracion central del traductor de llamadas.
Edita aqui los idiomas, modelos y dispositivos de audio.
"""

IDIOMAS = {
    "es": "español",   "en": "ingles",     "pt": "portugues", "fr": "frances",
    "de": "aleman",    "it": "italiano",   "pl": "polaco",    "tr": "turco",
    "ru": "ruso",      "nl": "neerlandes", "cs": "checo",     "ar": "arabe",
    "zh": "chino",     "ja": "japones",    "ko": "coreano",   "hu": "hungaro",
    "hi": "hindi",
}

TU_IDIOMA    = "es"
IDIOMA_ELLOS = "en"

WHISPER_MODELO  = "small"
WHISPER_DEVICE  = "cuda"
WHISPER_COMPUTE = "int8_float16"
XTTS_DEVICE     = "cuda"

# ─── Backend del LLM (API compatible con OpenAI) ───────────────────
# El mismo codigo funciona con Ollama (local) o vLLM (servidor). Solo cambias esto:
#   Ollama local:   LLM_BASE_URL="http://localhost:11434/v1"  LLM_MODELO="qwen2.5:3b"
#   vLLM servidor:  LLM_BASE_URL="http://TU_SERVIDOR:8000/v1" LLM_MODELO="Qwen/Qwen2.5-3B-Instruct"
LLM_BASE_URL = "http://localhost:11434/v1"
LLM_API_KEY  = "no-auth"          # Ollama la ignora; vLLM usa la que configures
LLM_MODELO   = "qwen2.5:3b"

XTTS_TEMPERATURE   = 0.55
XTTS_REP_PENALTY   = 5.0
XTTS_TOP_K         = 50
XTTS_TOP_P         = 0.85
XTTS_SPEED         = 1.0
XTTS_STREAM_CHUNK  = 12

SAMPLE_RATE     = 16000
VAD_AGRESIVIDAD = 2
SILENCIO_MS     = 350
MAX_SEGMENTO_S  = 15

MIC_NOMBRE = ""
PARLANTE_ESCUCHA = ""

DISPOSITIVO_VIRTUAL = "CABLE Input"

VOZ_ENTRANTE = True
SUBTITULOS   = True

REF_TU_VOZ     = "voces/mi_voz.wav"
REF_VOZ_ELLOS  = "voces/mi_voz.wav"
