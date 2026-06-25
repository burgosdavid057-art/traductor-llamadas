"""
Punto de entrada de la interfaz grafica.

    python app.py

Abre la ventana del traductor: elige idiomas y dispositivos, pulsa Iniciar.
(El CLI sigue disponible en main.py para uso por terminal.)
"""
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from src.gui import main

if __name__ == "__main__":
    main()
