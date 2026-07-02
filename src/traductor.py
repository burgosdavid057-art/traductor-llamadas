"""
Traducción texto -> texto vía un backend LLM **compatible con OpenAI**.

El mismo código funciona con distintos backends sin tocar nada más que la
configuración (LLM_BASE_URL en config.py):

  • Ollama (local, dev)      ->  http://localhost:11434/v1
  • vLLM (servidor GPU, prod)->  http://TU_SERVIDOR:8000/v1
  • cualquier otro OpenAI-compatible (LM Studio, llama.cpp server, OpenAI, …)

Así el proyecto soporta vLLM de verdad (para despliegue en servidor) y sigue
corriendo en una laptop con Ollama, sin duplicar lógica.
"""
from openai import OpenAI

_SISTEMA = (
    "Eres un traductor profesional simultáneo. Traduce el mensaje del usuario "
    "de {origen} a {destino}. Mantén el tono natural y coloquial de una "
    "conversación hablada. Devuelve EXCLUSIVAMENTE la traducción: sin comillas, "
    "sin explicaciones, sin notas, sin el texto original."
)


class Traductor:
    def __init__(self, modelo, base_url, api_key="no-auth", idiomas=None):
        self.modelo = modelo
        self.idiomas = idiomas or {}
        # timeout corto: en traducción en vivo preferimos fallar rápido que colgarnos
        self.client = OpenAI(base_url=base_url, api_key=api_key or "no-auth", timeout=30.0)

    def _nombre(self, codigo):
        return self.idiomas.get(codigo, codigo)

    def traducir(self, texto, origen, destino):
        texto = (texto or "").strip()
        if not texto:
            return ""
        r = self.client.chat.completions.create(
            model=self.modelo,
            messages=[
                {"role": "system", "content": _SISTEMA.format(
                    origen=self._nombre(origen), destino=self._nombre(destino))},
                {"role": "user", "content": texto},
            ],
            temperature=0.2,
            max_tokens=200,
        )
        return (r.choices[0].message.content or "").strip()
