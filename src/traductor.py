"""
Traduccion texto -> texto usando Ollama local.
"""
import ollama

_SISTEMA = (
    "Eres un traductor profesional simultaneo. Traduce el mensaje del usuario "
    "de {origen} a {destino}. Mantén el tono natural y coloquial de una "
    "conversacion hablada. Devuelve EXCLUSIVAMENTE la traduccion: sin comillas, "
    "sin explicaciones, sin notas, sin el texto original."
)


class Traductor:
    def __init__(self, modelo="qwen2.5:3b", idiomas=None):
        self.modelo = modelo
        self.idiomas = idiomas or {}

    def _nombre(self, codigo):
        return self.idiomas.get(codigo, codigo)

    def traducir(self, texto, origen, destino):
        texto = (texto or "").strip()
        if not texto:
            return ""
        r = ollama.chat(
            model=self.modelo,
            messages=[
                {"role": "system", "content": _SISTEMA.format(
                    origen=self._nombre(origen), destino=self._nombre(destino))},
                {"role": "user", "content": texto},
            ],
            options={"temperature": 0.2, "num_predict": 200},
            keep_alive="30m",
        )
        return r["message"]["content"].strip()
