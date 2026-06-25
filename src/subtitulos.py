"""
Ventana flotante de subtitulos (tkinter, sin dependencias extra).
Siempre encima, semitransparente y arrastrable. Dos lineas: TU y ELLOS.

tkinter debe vivir en el hilo principal; los hilos de trabajo llaman a
actualizar() (thread-safe via cola) y la ventana se refresca sola.
"""
import queue
import tkinter as tk


class Subtitulos:
    def __init__(self):
        self.q = queue.Queue()
        self.root = tk.Tk()
        self.root.title("Traductor")
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.85)
        self.root.overrideredirect(True)
        self.root.configure(bg="#0b0b0b")
        self.root.geometry("760x140+60+60")

        self.lbl_ellos = tk.Label(self.root, text="ELLOS -> ...", fg="#4ade80",
                                  bg="#0b0b0b", font=("Segoe UI", 15, "bold"),
                                  wraplength=730, justify="left", anchor="w")
        self.lbl_ellos.pack(fill="x", padx=14, pady=(12, 4))

        self.lbl_tu = tk.Label(self.root, text="TU -> ...", fg="#60a5fa",
                               bg="#0b0b0b", font=("Segoe UI", 15, "bold"),
                               wraplength=730, justify="left", anchor="w")
        self.lbl_tu.pack(fill="x", padx=14, pady=(4, 12))

        for w in (self.root, self.lbl_tu, self.lbl_ellos):
            w.bind("<Button-1>", self._click)
            w.bind("<B1-Motion>", self._arrastrar)
        self.root.bind("<Escape>", lambda e: self.root.destroy())

    def _click(self, e):
        self._dx, self._dy = e.x, e.y

    def _arrastrar(self, e):
        x = self.root.winfo_x() + e.x - self._dx
        y = self.root.winfo_y() + e.y - self._dy
        self.root.geometry(f"+{x}+{y}")

    def actualizar(self, quien, texto):
        """Llamable desde cualquier hilo. quien = 'tu' | 'ellos'."""
        self.q.put((quien, texto))

    def _poll(self):
        try:
            while True:
                quien, texto = self.q.get_nowait()
                if quien == "tu":
                    self.lbl_tu.config(text=f"TU -> {texto}")
                else:
                    self.lbl_ellos.config(text=f"ELLOS -> {texto}")
        except queue.Empty:
            pass
        self.root.after(80, self._poll)

    def iniciar(self):
        self._poll()
        self.root.mainloop()
