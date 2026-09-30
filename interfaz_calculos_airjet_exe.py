"""
AIR JET - Interfaz de cálculos empaquetable en un único .exe

Este lanzador está preparado para PyInstaller --onefile.
Los scripts se incluyen dentro del .exe como archivos de datos y se ejecutan
desde el propio ejecutable.

Uso en desarrollo:
    python interfaz_calculos_airjet_exe.py

Uso interno al .exe:
    AIRJET_Calculos.exe --run-script "Peso filtros"
"""

import os
import sys
import runpy
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox


CALCULOS = {
    "Peso filtros": {
        "archivo": "260507_Calculo peso filtros.py",
        "descripcion": "Superficies, masas, tubos, chapas, calorifugado, PDF y gráfico 3D."
    },
    "Filtro en operación": {
        "archivo": "260429_ Filtro en operación.py",
        "descripcion": "Carga total del filtro en operación y carga por pata."
    },
    "Can Velocity": {
        "archivo": "260429_ Can Velocity.py",
        "descripcion": "Velocidad ascensional / can velocity del filtro de mangas."
    },
    "Tuberías": {
        "archivo": "260126_ Tuberias.py",
        "descripcion": "Dimensionado múltiple de tuberías y exportación a Excel."
    },
    "Tolva": {
        "archivo": "260202_ Tolva.py",
        "descripcion": "Volumen, superficies, masa de chapa y masa de tolva llena."
    },
    "Ley Ventiladores": {
        "archivo": "260506_ Ley Ventiladores.py",
        "descripcion": "Cálculo por leyes de ventiladores: caudal, presión, potencia y frecuencia."
    },
    "Motores": {
        "archivo": "260310_ Motores.py",
        "descripcion": "Potencia de ventilador vs temperatura y recomendación de talla de motor."
    },
}


def base_path():
    """
    En desarrollo devuelve la carpeta del .py.
    En PyInstaller --onefile devuelve la carpeta temporal _MEIPASS.
    """
    if getattr(sys, "frozen", False):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))


def ruta_script(nombre_calculo):
    info = CALCULOS[nombre_calculo]
    return os.path.join(base_path(), info["archivo"])


def ejecutar_script_embebido(nombre_calculo):
    ruta = ruta_script(nombre_calculo)

    if not os.path.exists(ruta):
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "Archivo no encontrado",
            f"No encuentro el script embebido:\n\n{ruta}"
        )
        root.destroy()
        return

    carpeta_trabajo = os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else os.path.dirname(ruta)
    os.chdir(carpeta_trabajo)

    runpy.run_path(ruta, run_name="__main__")


class LanzadorCalculos(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("AIR JET - Interfaz de cálculos")
        self.geometry("780x470")
        self.minsize(720, 430)
        self.configure(padx=18, pady=18)

        self.calculo_var = tk.StringVar(value=list(CALCULOS.keys())[0])
        self.descripcion_var = tk.StringVar()
        self.estado_var = tk.StringVar(value="Selecciona un cálculo y pulsa Abrir cálculo.")

        self.crear_interfaz()
        self.actualizar_descripcion()

    def crear_interfaz(self):
        ttk.Label(
            self,
            text="Interfaz general de cálculos",
            font=("Segoe UI", 18, "bold")
        ).pack(anchor="w", pady=(0, 8))

        ttk.Label(
            self,
            text="Elige qué cálculo quieres hacer. Esta ventana abrirá el módulo correspondiente.",
            font=("Segoe UI", 10)
        ).pack(anchor="w", pady=(0, 18))

        panel = ttk.LabelFrame(self, text="Selección de cálculo", padding=14)
        panel.pack(fill="x", pady=(0, 14))

        ttk.Label(panel, text="Cálculo:").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=4)

        combo = ttk.Combobox(
            panel,
            textvariable=self.calculo_var,
            values=list(CALCULOS.keys()),
            state="readonly",
            width=38
        )
        combo.grid(row=0, column=1, sticky="ew", pady=4)
        combo.bind("<<ComboboxSelected>>", lambda _event: self.actualizar_descripcion())

        ttk.Label(panel, text="Descripción:").grid(row=1, column=0, sticky="nw", padx=(0, 8), pady=(10, 4))

        ttk.Label(
            panel,
            textvariable=self.descripcion_var,
            wraplength=590
        ).grid(row=1, column=1, sticky="w", pady=(10, 4))

        panel.columnconfigure(1, weight=1)

        botones = ttk.Frame(self)
        botones.pack(fill="x", pady=(0, 14))

        ttk.Button(botones, text="Abrir cálculo", command=self.abrir_calculo).pack(side="left", padx=(0, 8))
        ttk.Button(botones, text="Salir", command=self.destroy).pack(side="right")

        lista_panel = ttk.LabelFrame(self, text="Códigos incluidos", padding=10)
        lista_panel.pack(fill="both", expand=True)

        columnas = ("calculo", "archivo")
        self.tree = ttk.Treeview(lista_panel, columns=columnas, show="headings", height=9)

        self.tree.heading("calculo", text="Cálculo")
        self.tree.heading("archivo", text="Archivo incluido")

        self.tree.column("calculo", width=230, anchor="w")
        self.tree.column("archivo", width=480, anchor="w")

        self.tree.pack(fill="both", expand=True)

        for nombre, info in CALCULOS.items():
            self.tree.insert("", "end", values=(nombre, info["archivo"]))

        self.tree.bind("<Double-1>", self.seleccionar_desde_tabla)

        ttk.Label(
            self,
            textvariable=self.estado_var,
            foreground="blue",
            wraplength=720
        ).pack(anchor="w", pady=(10, 0))

    def seleccionar_desde_tabla(self, _event):
        seleccionado = self.tree.selection()
        if not seleccionado:
            return

        valores = self.tree.item(seleccionado[0], "values")
        if valores:
            self.calculo_var.set(valores[0])
            self.actualizar_descripcion()

    def actualizar_descripcion(self):
        self.descripcion_var.set(CALCULOS[self.calculo_var.get()]["descripcion"])

    def abrir_calculo(self):
        nombre = self.calculo_var.get()

        try:
            if getattr(sys, "frozen", False):
                subprocess.Popen([sys.executable, "--run-script", nombre])
            else:
                subprocess.Popen([sys.executable, os.path.abspath(__file__), "--run-script", nombre])
            self.estado_var.set(f"Abierto: {nombre}")
        except Exception as exc:
            messagebox.showerror("Error al abrir", f"No se pudo abrir el cálculo:\n{exc}")


def main():
    if len(sys.argv) >= 3 and sys.argv[1] == "--run-script":
        nombre = sys.argv[2]
        if nombre not in CALCULOS:
            raise SystemExit(f"Cálculo no reconocido: {nombre}")
        ejecutar_script_embebido(nombre)
        return

    app = LanzadorCalculos()
    app.mainloop()


if __name__ == "__main__":
    main()
