"""
Test de entorno: valida que cada pieza funcione en tu PC antes de usar el traductor.
Ejecuta:   python test_entorno.py
"""
import sys
import time

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

OK, FAIL = "[OK]", "[FAIL]"


def check_torch_cuda():
    print("\n[1/5] PyTorch + CUDA")
    try:
        import torch
        print(f"   torch {torch.__version__}")
        if torch.cuda.is_available():
            n = torch.cuda.get_device_name(0)
            vram = torch.cuda.get_device_properties(0).total_memory / 1e9
            print(f"   {OK} CUDA disponible - {n} ({vram:.1f} GB)")
            return True
        print(f"   {FAIL} CUDA NO disponible.")
        return False
    except Exception as e:
        print(f"   {FAIL} {e}")
        return False


def check_whisper():
    print("\n[2/5] faster-whisper (STT)")
    try:
        import config
        from faster_whisper import WhisperModel
        t = time.time()
        m = WhisperModel(config.WHISPER_MODELO, device=config.WHISPER_DEVICE,
                         compute_type=config.WHISPER_COMPUTE)
        print(f"   {OK} modelo '{config.WHISPER_MODELO}' cargado en {time.time()-t:.1f}s")
        del m
        return True
    except Exception as e:
        print(f"   {FAIL} {e}")
        print("      Si menciona cuDNN/cublas: faltan librerias CUDA (ver README).")
        return False


def check_ollama():
    print("\n[3/5] LLM traduccion (backend OpenAI-compatible)")
    try:
        import config
        from src.traductor import Traductor
        print(f"   backend: {config.LLM_BASE_URL}  modelo: {config.LLM_MODELO}")
        trad = Traductor(config.LLM_MODELO, config.LLM_BASE_URL, config.LLM_API_KEY, config.IDIOMAS)
        r = trad.traducir("Hola, mucho gusto.", "es", "en")
        print(f"   {OK} responde: {r[:50]}")
        return True
    except Exception as e:
        print(f"   {FAIL} {e}")
        print("      Backend caido? Con Ollama: abre la app / 'ollama serve'.")
        print(f"      Con vLLM: verifica que el servidor este en {config.LLM_BASE_URL}")
        return False


def check_audio():
    print("\n[4/5] Dispositivos de audio")
    try:
        import config
        import soundcard as sc
        mic = sc.default_microphone()
        spk = sc.default_speaker()
        print(f"   {OK} microfono: {mic.name}")
        print(f"   {OK} parlantes: {spk.name}")
        nombres = [s.name for s in sc.all_speakers()]
        if any(config.DISPOSITIVO_VIRTUAL.lower() in n.lower() for n in nombres):
            print(f"   {OK} VB-Cable detectado ('{config.DISPOSITIVO_VIRTUAL}')")
        else:
            print(f"   {FAIL} no se detecta '{config.DISPOSITIVO_VIRTUAL}'. Instala VB-Audio Cable.")
            print(f"      salidas disponibles: {nombres}")
        return True
    except Exception as e:
        print(f"   {FAIL} {e}")
        return False


def check_xtts():
    print("\n[5/5] XTTS-v2 (clonacion de voz) - puede tardar/descargar ~2 GB la primera vez")
    try:
        import config
        from src.voz import Voz
        t = time.time()
        Voz(config.XTTS_DEVICE)
        print(f"   {OK} XTTS cargado en {time.time()-t:.1f}s")
        return True
    except Exception as e:
        print(f"   {FAIL} {e}")
        return False


if __name__ == "__main__":
    print("=== Test de entorno - Traductor de llamadas ===")
    resultados = [
        check_torch_cuda(),
        check_whisper(),
        check_ollama(),
        check_audio(),
        check_xtts(),
    ]
    print("\n" + "=" * 46)
    print(f"Resultado: {sum(resultados)}/{len(resultados)} pruebas OK")
    sys.exit(0 if all(resultados) else 1)
