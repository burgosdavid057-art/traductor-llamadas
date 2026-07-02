"""
Interfaz grafica del traductor de llamadas (customtkinter).
Panel de control (idiomas, dispositivos, opciones) + historial de conversacion.
"""
import queue
import threading

import customtkinter as ctk
import soundcard as sc

import config
from src.motor import Motor

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

AZUL = "#60a5fa"
VERDE = "#4ade80"
GRIS = "#8a8a8a"


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("EchoLingua - Traductor de llamadas")
        self.geometry("860x640")
        self.minsize(720, 560)

        self.cola = queue.Queue()
        self.motor = Motor(on_texto=self._on_texto, on_estado=self._on_estado)
        self.corriendo = False

        self.nombre_a_codigo = {v: k for k, v in config.IDIOMAS.items()}
        nombres = list(config.IDIOMAS.values())

        mics = [m.name for m in sc.all_microphones() if "cable" not in m.name.lower()]
        spks = [s.name for s in sc.all_speakers() if "cable" not in s.name.lower()]

        self._construir(nombres, mics, spks)
        self.protocol("WM_DELETE_WINDOW", self._cerrar)
        self.after(80, self._poll)

    def _construir(self, nombres, mics, spks):
        cab = ctk.CTkFrame(self)
        cab.pack(fill="x", padx=16, pady=(16, 8))
        titulo = ctk.CTkFrame(cab, fg_color="transparent")
        titulo.pack(side="left", padx=12, pady=6)
        ctk.CTkLabel(titulo, text="EchoLingua",
                     font=ctk.CTkFont(size=22, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(titulo, text="Traductor de llamadas en tiempo real",
                     text_color=GRIS, font=ctk.CTkFont(size=12)).pack(anchor="w")
        self.lbl_estado = ctk.CTkLabel(cab, text="Detenido", text_color=GRIS,
                                       font=ctk.CTkFont(size=14, weight="bold"))
        self.lbl_estado.pack(side="right", padx=12)

        ctrl = ctk.CTkFrame(self)
        ctrl.pack(fill="x", padx=16, pady=8)
        ctrl.grid_columnconfigure((1, 3), weight=1)

        ctk.CTkLabel(ctrl, text="Tu hablas:").grid(row=0, column=0, padx=(12, 6), pady=10, sticky="e")
        self.tu_var = ctk.StringVar(value=config.IDIOMAS.get(config.TU_IDIOMA, "espanol"))
        ctk.CTkOptionMenu(ctrl, values=nombres, variable=self.tu_var).grid(row=0, column=1, padx=6, pady=10, sticky="ew")

        ctk.CTkLabel(ctrl, text="Ellos hablan:").grid(row=0, column=2, padx=(12, 6), pady=10, sticky="e")
        self.ellos_var = ctk.StringVar(value=config.IDIOMAS.get(config.IDIOMA_ELLOS, "ingles"))
        ctk.CTkOptionMenu(ctrl, values=nombres, variable=self.ellos_var).grid(row=0, column=3, padx=(6, 12), pady=10, sticky="ew")

        ctk.CTkLabel(ctrl, text="Tu microfono:").grid(row=1, column=0, padx=(12, 6), pady=10, sticky="e")
        self.mic_var = ctk.StringVar(value=mics[0] if mics else "")
        ctk.CTkOptionMenu(ctrl, values=mics or ["(sin microfono)"], variable=self.mic_var).grid(
            row=1, column=1, columnspan=3, padx=6, pady=10, sticky="ew")

        ctk.CTkLabel(ctrl, text="Oyes la llamada en:").grid(row=2, column=0, padx=(12, 6), pady=10, sticky="e")
        self.esc_var = ctk.StringVar(value=spks[0] if spks else "")
        ctk.CTkOptionMenu(ctrl, values=spks or ["(sin parlante)"], variable=self.esc_var).grid(
            row=2, column=1, columnspan=3, padx=6, pady=10, sticky="ew")

        fila = ctk.CTkFrame(self, fg_color="transparent")
        fila.pack(fill="x", padx=16, pady=(0, 8))
        self.voz_var = ctk.BooleanVar(value=config.VOZ_ENTRANTE)
        ctk.CTkCheckBox(fila, text="Escuchar voz traducida entrante",
                        variable=self.voz_var).pack(side="left", padx=12, pady=8)

        self.btn_detener = ctk.CTkButton(fila, text="Detener", width=130,
                                         fg_color="#b91c1c", hover_color="#7f1d1d",
                                         command=self._detener, state="disabled")
        self.btn_detener.pack(side="right", padx=(6, 12), pady=8)
        self.btn_iniciar = ctk.CTkButton(fila, text="Iniciar", width=130,
                                         command=self._iniciar)
        self.btn_iniciar.pack(side="right", padx=6, pady=8)

        self.log = ctk.CTkTextbox(self, font=ctk.CTkFont(size=15), wrap="word")
        self.log.pack(fill="both", expand=True, padx=16, pady=8)
        tb = self.log._textbox
        tb.tag_config("tu", foreground=AZUL, font=("Segoe UI", 12, "bold"))
        tb.tag_config("ellos", foreground=VERDE, font=("Segoe UI", 12, "bold"))
        tb.tag_config("trad", foreground="#f5f5f5", font=("Segoe UI", 15))
        tb.tag_config("orig", foreground=GRIS, font=("Segoe UI", 11, "italic"))
        self.log.configure(state="disabled")

        self.lbl_info = ctk.CTkLabel(
            self, text="En Zoom/Meet -> Microfono: CABLE Output   |   Altavoz: tu parlante normal",
            text_color=GRIS, font=ctk.CTkFont(size=12))
        self.lbl_info.pack(pady=(0, 12))

    def _on_texto(self, quien, orig, trad):
        self.cola.put(("texto", (quien, orig, trad)))

    def _on_estado(self, txt):
        self.cola.put(("estado", (txt, None)))

    def _iniciar(self):
        if self.corriendo:
            return
        tu = self.nombre_a_codigo.get(self.tu_var.get(), "es")
        ellos = self.nombre_a_codigo.get(self.ellos_var.get(), "en")
        mic, escucha, voz_ent = self.mic_var.get(), self.esc_var.get(), self.voz_var.get()
        self.btn_iniciar.configure(state="disabled")
        self._set_estado("Cargando modelos...", "#f59e0b")

        def trabajo():
            try:
                self.motor.cargar()
                info = self.motor.iniciar(tu, ellos, mic, escucha, voz_ent)
                self.corriendo = True
                self.cola.put(("estado", ("Escuchando", "#4ade80")))
                self.cola.put(("botones", "corriendo"))
                self.cola.put(("info", f"Mic: {info['mic']}  ->  Salida: {info['salida']}   |   Escucha: {info['escucha']}"))
            except Exception as e:
                self.cola.put(("estado", (f"Error: {e}", "#ef4444")))
                self.cola.put(("botones", "detenido"))

        threading.Thread(target=trabajo, daemon=True).start()

    def _detener(self):
        self.btn_detener.configure(state="disabled")
        self._set_estado("Deteniendo...", "#f59e0b")

        def trabajo():
            self.motor.detener()
            self.corriendo = False
            self.cola.put(("estado", ("Detenido", GRIS)))
            self.cola.put(("botones", "detenido"))

        threading.Thread(target=trabajo, daemon=True).start()

    def _set_estado(self, txt, color):
        self.lbl_estado.configure(text=txt, text_color=color or GRIS)

    def _append(self, quien, orig, trad):
        etiqueta = "TU" if quien == "tu" else "ELLOS"
        tag = "tu" if quien == "tu" else "ellos"
        self.log.configure(state="normal")
        tb = self.log._textbox
        tb.insert("end", f"{etiqueta}\n", tag)
        tb.insert("end", f"{trad}\n", "trad")
        tb.insert("end", f"   -> {orig}\n\n", "orig")
        tb.see("end")
        self.log.configure(state="disabled")

    def _poll(self):
        try:
            while True:
                tipo, datos = self.cola.get_nowait()
                if tipo == "texto":
                    self._append(*datos)
                elif tipo == "estado":
                    self._set_estado(*datos)
                elif tipo == "info":
                    self.lbl_info.configure(text=datos)
                elif tipo == "botones":
                    if datos == "corriendo":
                        self.btn_iniciar.configure(state="disabled")
                        self.btn_detener.configure(state="normal")
                    else:
                        self.btn_iniciar.configure(state="normal")
                        self.btn_detener.configure(state="disabled")
        except queue.Empty:
            pass
        self.after(80, self._poll)

    def _cerrar(self):
        try:
            self.motor.parar.set()
        except Exception:
            pass
        self.destroy()


def main():
    App().mainloop()


if __name__ == "__main__":
    main()
