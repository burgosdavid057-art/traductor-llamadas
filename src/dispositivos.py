"""
Seleccion de dispositivos de audio.
Elige explicitamente el microfono real y el parlante donde oyes la llamada,
ignorando el cable virtual como entrada.
"""
import soundcard as sc


def _match(nombre, sub):
    return sub.lower() in nombre.lower()


def microfono(preferencia=""):
    """Tu microfono REAL. Si no se especifica, toma el primero que NO sea CABLE."""
    mics = sc.all_microphones()
    if preferencia:
        for m in mics:
            if _match(m.name, preferencia):
                return m
        print(f"[audio] aviso: no encontre microfono '{preferencia}', uso automatico.")
    for m in mics:
        if "cable" not in m.name.lower():
            return m
    return sc.default_microphone()


def parlante(preferencia="", excluir_cable=True):
    """Parlante donde ESCUCHAS la llamada."""
    spks = sc.all_speakers()
    if preferencia:
        for s in spks:
            if _match(s.name, preferencia):
                return s
        print(f"[audio] aviso: no encontre parlante '{preferencia}', uso automatico.")
    for s in spks:
        if not (excluir_cable and "cable" in s.name.lower()):
            return s
    return sc.default_speaker()


def parlante_por_nombre(nombre):
    """Parlante exacto por nombre (p.ej. 'CABLE Input' para enviar tu voz a Zoom)."""
    return sc.get_speaker(nombre)


def loopback_de(parlante_obj):
    """Microfono-loopback del parlante dado (captura lo que suena ahi)."""
    return sc.get_microphone(parlante_obj.name, include_loopback=True)


def listar():
    print("=== Dispositivos de audio ===")
    print("MICROFONOS (entradas):")
    for m in sc.all_microphones():
        print(f"   - {m.name}")
    print("PARLANTES (salidas):")
    for s in sc.all_speakers():
        print(f"   - {s.name}")
