# 🎙️ Traductor de llamadas en tiempo real (100% local)

Traduce en vivo lo que **tú hablas** y lo que **escuchas** en una llamada
(Zoom / Meet / Discord / Teams), usando tu PC. La traducción de tu voz sale
**clonada con tu propia voz** (XTTS-v2). Todo corre local: Whisper + Ollama + XTTS.

```
TÚ ──→ micrófono → Whisper → Ollama → XTTS (TU voz) → VB-Cable → Zoom → ellos
ELLOS ──→ loopback → Whisper → Ollama → 📺 subtítulos (+ 🔊 voz opcional) → tú
```

## ⚙️ Requisitos
- Windows + Python 3.11 ✅ (ya lo tienes)
- GPU NVIDIA (RTX 4050, ~6 GB) ✅
- Ollama instalado ✅ — **debe estar corriendo** al usar la app
- **VB-Audio Cable** (gratis) → el "micrófono falso" que oirá Zoom

---

## 📦 Instalación (una sola vez)

> Orden importante: **torch con CUDA va primero**, antes que el resto.

```powershell
cd "C:\Users\USER\OneDrive\Documentos\Desarrollo\ia\traductor-llamadas"

# 1) Entorno virtual
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2) PyTorch + torchaudio CON CUDA (cu121)
pip install torch==2.5.1 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cu121

# 3) El resto de dependencias
pip install -r requirements.txt

# 4) Modelo de traducción en Ollama
ollama pull qwen2.5:3b
```

### VB-Audio Cable
Descarga e instala desde https://vb-audio.com/Cable/ (gratis). Reinicia.
Aparecerán dos dispositivos nuevos: **CABLE Input** (salida) y **CABLE Output** (entrada).

---

## ✅ Paso 1 — Probar el entorno
```powershell
python test_entorno.py
```
Debe dar 5/5. Si algo falla, el propio test te dice qué arreglar.

> **Error típico de cuDNN/cuBLAS en Whisper:** faster-whisper necesita las
> librerías CUDA. Suele resolverse con:
> `pip install nvidia-cublas-cu12 nvidia-cudnn-cu12`

## ✅ Paso 2 — Grabar tu voz (para clonarla)
```powershell
python grabar_voz.py
```
Habla con naturalidad ~12 s. Se guarda en `voces/mi_voz.wav`.

## ✅ Paso 3 — Ejecutar

### Opción A — Interfaz gráfica (recomendada)
```powershell
python app.py
```
Abre una ventana donde eliges idiomas y dispositivos, activas/desactivas la voz
del gringo y controlas todo con **▶ Iniciar / ⏹ Detener**. La conversación
aparece traducida en pantalla (TÚ en azul, ELLOS en verde).

### Opción B — Por terminal (CLI)
```powershell
python main.py --tu es --ellos en
```
- `--tu` = tu idioma · `--ellos` = idioma de la otra persona
- Idiomas: es, en, pt, fr, de, it, ru, zh, ja, ko, ar, hi… (ver `config.py`)
- `--sin-voz-entrante` → ellos solo en subtítulos (evita eco)
- `--listar` → ver dispositivos de audio

---

## 🎧 Configurar Zoom / Meet / Discord
Para que **te oigan traducido**, en la app de la llamada:

- **Micrófono → `CABLE Output`** (así reciben tu voz clonada, no la real)
- **Altavoz → tus parlantes/audífonos normales**

> El programa captura el *loopback* de tus parlantes para traducir lo que dicen ellos,
> y envía tu voz traducida a `CABLE Input` (que Zoom ve como `CABLE Output`).

---

## ⏱️ Qué esperar
- Latencia ~2-4 s por frase (no es simultáneo perfecto).
- Funciona por turnos: mientras suena una traducción, se pausa la captura para evitar eco.
- Acentos fuertes, ruido o varias voces a la vez bajan la precisión.

## 🔧 Ajustes en `config.py`
| Si quieres… | Cambia |
|---|---|
| Más precisión (más VRAM) | `WHISPER_MODELO = "medium"` o `OLLAMA_MODELO = "qwen2.5:7b"` |
| Menos latencia | `SILENCIO_MS` más bajo (p.ej. 500) |
| Liberar VRAM | `XTTS_DEVICE = "cpu"` (más lento) |
| Otra voz para la traducción entrante | `REF_VOZ_ELLOS` a otro .wav |

## 🗂️ Estructura
```
traductor-llamadas/
├─ app.py              # interfaz gráfica (entrada recomendada)
├─ main.py             # CLI (terminal)
├─ config.py           # idiomas, modelos, dispositivos, calidad/latencia
├─ grabar_voz.py       # graba tu muestra de voz
├─ test_entorno.py     # valida que todo funcione
├─ requirements.txt
└─ src/
   ├─ motor.py         # núcleo: modelos + 2 flujos (iniciar/detener)
   ├─ gui.py           # ventana customtkinter
   ├─ dispositivos.py  # selección de mic/parlantes (ignora el cable)
   ├─ audio.py         # captura + VAD (segmentación por voz)
   ├─ stt.py           # Whisper (voz→texto)
   ├─ traductor.py     # Ollama (texto→texto)
   ├─ voz.py           # XTTS-v2 (texto→voz clonada, con streaming)
   └─ subtitulos.py    # overlay flotante (solo para el CLI)
```
