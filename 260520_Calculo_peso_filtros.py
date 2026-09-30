import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import math
import json

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

from PIL import Image, ImageTk


#PESO_TUBO_SCH40_1_PULGADA = 2.45
#########      peso de 1½" (4.05 kg/m)
PESO_TUBO_SCH40_1_PULGADA = 4.05
PESO_CHAPA_DEFLECTORA = 24
PESO_CHAPA_VENTURI_POR_MANGA = 1.5
DENSIDAD_CHAPA_CALORIFUGADO = 8000


SUPERFICIES_MANGAS = {
    "4 ft": 0.49,
    "6 ft": 0.75,
    "8 ft": 1.00,
    "10 ft": 1.25,
    "12 ft": 1.50,
    "14 ft": 1.80,
}


def area_tolva_rectangular(h, l1, w1, l2, w2):
    g_largo = math.sqrt(h**2 + ((w1 - w2) / 2) ** 2)
    g_ancho = math.sqrt(h**2 + ((l1 - l2) / 2) ** 2)
    return (l1 + l2) * g_largo + (w1 + w2) * g_ancho


def dibujar_placa(ax, x, y, z, largo, ancho, color, etiqueta):
    placa = [[
        (x, y, z),
        (x + largo, y, z),
        (x + largo, y + ancho, z),
        (x, y + ancho, z)
    ]]
    poly = Poly3DCollection(placa, alpha=0.85, facecolor=color, edgecolor="black", linewidths=1.2)
    ax.add_collection3d(poly)
    ax.text(x, y - ancho * 0.25, z, etiqueta, fontsize=11, fontweight="bold", color=color)


def dibujar_prisma_abierto(ax, x, y, z, largo, ancho, alto, color, etiqueta):
    caras = [
        [(x, y, z), (x + largo, y, z), (x + largo, y, z + alto), (x, y, z + alto)],
        [(x + largo, y, z), (x + largo, y + ancho, z), (x + largo, y + ancho, z + alto), (x + largo, y, z + alto)],
        [(x + largo, y + ancho, z), (x, y + ancho, z), (x, y + ancho, z + alto), (x + largo, y + ancho, z + alto)],
        [(x, y + ancho, z), (x, y, z), (x, y, z + alto), (x, y + ancho, z + alto)],
    ]

    poly = Poly3DCollection(caras, alpha=0.62, facecolor=color, edgecolor="black", linewidths=1.2)
    ax.add_collection3d(poly)

    borde_superior = [[
        (x, y, z + alto),
        (x + largo, y, z + alto),
        (x + largo, y + ancho, z + alto),
        (x, y + ancho, z + alto)
    ]]
    borde = Poly3DCollection(borde_superior, alpha=0.08, facecolor=color, edgecolor="black", linewidths=2.0)
    ax.add_collection3d(borde)

    ax.text(x, y - ancho * 0.25, z + max(alto, 0.1) / 2, etiqueta, fontsize=11, fontweight="bold", color=color)


def dibujar_tolva(ax, x, y, z, largo_sup, ancho_sup, largo_inf, ancho_inf, alto, color):
    dx = (largo_sup - largo_inf) / 2
    dy = (ancho_sup - ancho_inf) / 2

    sup = [
        (x, y, z + alto),
        (x + largo_sup, y, z + alto),
        (x + largo_sup, y + ancho_sup, z + alto),
        (x, y + ancho_sup, z + alto)
    ]

    inf = [
        (x + dx, y + dy, z),
        (x + dx + largo_inf, y + dy, z),
        (x + dx + largo_inf, y + dy + ancho_inf, z),
        (x + dx, y + dy + ancho_inf, z)
    ]

    caras = [
        [sup[0], sup[1], inf[1], inf[0]],
        [sup[1], sup[2], inf[2], inf[1]],
        [sup[2], sup[3], inf[3], inf[2]],
        [sup[3], sup[0], inf[0], inf[3]],
    ]

    poly = Poly3DCollection(caras, alpha=0.72, facecolor=color, edgecolor="black", linewidths=1.2)
    ax.add_collection3d(poly)

    borde_superior = Poly3DCollection([sup], alpha=0.08, facecolor=color, edgecolor="black", linewidths=2.0)
    ax.add_collection3d(borde_superior)

    ax.text(x, y - ancho_sup * 0.25, z + max(alto, 0.1) / 2, "TOLVA", fontsize=11, fontweight="bold", color=color)


def dibujar_lineas_alineacion(ax, x, y, z_min, z_max, largo, ancho):
    vertices_xy = [
        (x, y),
        (x + largo, y),
        (x + largo, y + ancho),
        (x, y + ancho)
    ]

    for vx, vy in vertices_xy:
        ax.plot([vx, vx], [vy, vy], [z_min, z_max], linestyle="--", color="black", linewidth=0.8, alpha=0.55)


def normal_triangulo(p1, p2, p3):
    ux, uy, uz = (p2[0] - p1[0], p2[1] - p1[1], p2[2] - p1[2])
    vx, vy, vz = (p3[0] - p1[0], p3[1] - p1[1], p3[2] - p1[2])

    nx = uy * vz - uz * vy
    ny = uz * vx - ux * vz
    nz = ux * vy - uy * vx

    modulo = math.sqrt(nx**2 + ny**2 + nz**2)
    if modulo == 0:
        return (0.0, 0.0, 0.0)

    return (nx / modulo, ny / modulo, nz / modulo)


def triangulos_desde_cara(cara):
    if len(cara) < 3:
        return []

    triangulos = []
    for i in range(1, len(cara) - 1):
        triangulos.append((cara[0], cara[i], cara[i + 1]))
    return triangulos


def escribir_stl_ascii(ruta_archivo, nombre_solido, triangulos):
    nombre_limpio = "".join(c if c.isalnum() or c in ("_", "-") else "_" for c in nombre_solido) or "filtro"

    with open(ruta_archivo, "w", encoding="utf-8") as f:
        f.write(f"solid {nombre_limpio}\n")

        for p1, p2, p3 in triangulos:
            nx, ny, nz = normal_triangulo(p1, p2, p3)
            f.write(f"  facet normal {nx:.9e} {ny:.9e} {nz:.9e}\n")
            f.write("    outer loop\n")
            f.write(f"      vertex {p1[0]:.9e} {p1[1]:.9e} {p1[2]:.9e}\n")
            f.write(f"      vertex {p2[0]:.9e} {p2[1]:.9e} {p2[2]:.9e}\n")
            f.write(f"      vertex {p3[0]:.9e} {p3[1]:.9e} {p3[2]:.9e}\n")
            f.write("    endloop\n")
            f.write("  endfacet\n")

        f.write(f"endsolid {nombre_limpio}\n")


def crear_caras_prisma_abierto(x, y, z, largo, ancho, alto):
    if alto <= 0:
        return []

    return [
        [(x, y, z), (x + largo, y, z), (x + largo, y, z + alto), (x, y, z + alto)],
        [(x + largo, y, z), (x + largo, y + ancho, z), (x + largo, y + ancho, z + alto), (x + largo, y, z + alto)],
        [(x + largo, y + ancho, z), (x, y + ancho, z), (x, y + ancho, z + alto), (x + largo, y + ancho, z + alto)],
        [(x, y + ancho, z), (x, y, z), (x, y, z + alto), (x, y + ancho, z + alto)],
    ]


def crear_cara_placa(x, y, z, largo, ancho):
    return [[
        (x, y, z),
        (x + largo, y, z),
        (x + largo, y + ancho, z),
        (x, y + ancho, z)
    ]]


def crear_caras_tolva(x, y, z, largo_sup, ancho_sup, largo_inf, ancho_inf, alto):
    if alto <= 0:
        return []

    dx = (largo_sup - largo_inf) / 2
    dy = (ancho_sup - ancho_inf) / 2

    sup = [
        (x, y, z + alto),
        (x + largo_sup, y, z + alto),
        (x + largo_sup, y + ancho_sup, z + alto),
        (x, y + ancho_sup, z + alto)
    ]

    inf = [
        (x + dx, y + dy, z),
        (x + dx + largo_inf, y + dy, z),
        (x + dx + largo_inf, y + dy + ancho_inf, z),
        (x + dx, y + dy + ancho_inf, z)
    ]

    return [
        [sup[0], sup[1], inf[1], inf[0]],
        [sup[1], sup[2], inf[2], inf[1]],
        [sup[2], sup[3], inf[3], inf[2]],
        [sup[3], sup[0], inf[0], inf[3]],
    ]


def crear_triangulos_filtro(d):
    x0 = 0
    y0 = 0

    z_tolva = 0
    z_case2 = z_tolva + d["tolva_alto"]
    z_cas = z_case2 + d["case2_alto"]
    z_cal = z_cas + d["cas_alto"]
    z_puertas = z_cal + d["cal_alto"]

    caras = []
    caras.extend(crear_caras_tolva(
        x0,
        y0,
        z_tolva,
        d["case2_largo"],
        d["case2_ancho"],
        d["tolva_boca_desc_largo"],
        d["tolva_boca_desc_ancho"],
        d["tolva_alto"]
    ))
    caras.extend(crear_caras_prisma_abierto(x0, y0, z_case2, d["case2_largo"], d["case2_ancho"], d["case2_alto"]))
    caras.extend(crear_caras_prisma_abierto(x0, y0, z_cas, d["cal_largo"], d["cal_ancho"], d["cas_alto"]))
    caras.extend(crear_caras_prisma_abierto(x0, y0, z_cal, d["cal_largo"], d["cal_ancho"], d["cal_alto"]))
    caras.extend(crear_cara_placa(x0, y0, z_puertas, d["cal_largo"], d["cal_ancho"]))

    triangulos = []
    for cara in caras:
        triangulos.extend(triangulos_desde_cara(cara))

    return triangulos


class App(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Cálculo de superficies y masas")
        self.geometry("1200x850")
        self.resizable(True, True)

        self.vars = {}
        self.resultados = {}

        self.crear_interfaz()

    def crear_interfaz(self):
        titulo = tk.Label(
            self,
            text="Cálculo de superficie lateral y masa",
            font=("Arial", 16, "bold")
        )
        titulo.pack(pady=10)

        barra_botones = tk.Frame(self)
        barra_botones.pack(fill="x", padx=15, pady=5)

        tk.Button(barra_botones, text="Limpiar", command=self.limpiar, bg="#f44336", fg="white",
                  width=18, font=("Arial", 10, "bold")).pack(side="right", padx=4)


        tk.Button(barra_botones, text="Exportar STL", command=self.exportar_stl, bg="#FF9800", fg="white",
                  width=18, font=("Arial", 10, "bold")).pack(side="left", padx=4)


        tk.Button(barra_botones, text="Guardar configuración", command=self.guardar_configuracion,
                  bg="#607D8B", fg="white", width=22, font=("Arial", 10, "bold")).pack(side="left", padx=4)

        tk.Button(barra_botones, text="Cargar configuración", command=self.cargar_configuracion,
                  bg="#795548", fg="white", width=22, font=("Arial", 10, "bold")).pack(side="left", padx=4)
        #tk.Button(barra_botones, text="Limpiar", command=self.limpiar, bg="#f44336", fg="white", width=18, font=("Arial", 10, "bold")).pack(side="left", padx=4)

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=15, pady=10)

        tab_geometria = ttk.Frame(notebook)
        tab_filtro_operacion = ttk.Frame(notebook)
        tab_tolva = ttk.Frame(notebook)
        tab_resultados = ttk.Frame(notebook)

        notebook.add(tab_geometria, text="Geometría")
        notebook.add(tab_filtro_operacion, text="Filtro en operación")
        notebook.add(tab_tolva, text="Tolva")
        notebook.add(tab_resultados, text="Resultados")

        for tab in [tab_geometria, tab_filtro_operacion, tab_tolva, tab_resultados]:
            tab.grid_columnconfigure(0, weight=1)
            tab.grid_columnconfigure(1, weight=1)

        # =========================
        # AREA CON SCROLL VERTICAL PARA GEOMETRIA
        # =========================
        tab_geometria.grid_rowconfigure(0, weight=1)
        tab_geometria.grid_columnconfigure(0, weight=1)

        canvas_geometria = tk.Canvas(tab_geometria, highlightthickness=0)
        scrollbar_geometria = ttk.Scrollbar(
            tab_geometria,
            orient="vertical",
            command=canvas_geometria.yview
        )

        geometria_contenido = ttk.Frame(canvas_geometria)
        ventana_geometria = canvas_geometria.create_window(
            (0, 0),
            window=geometria_contenido,
            anchor="nw"
        )

        canvas_geometria.configure(yscrollcommand=scrollbar_geometria.set)
        canvas_geometria.grid(row=0, column=0, sticky="nsew")
        scrollbar_geometria.grid(row=0, column=1, sticky="ns")

        def actualizar_scroll_geometria(event=None):
            canvas_geometria.configure(scrollregion=canvas_geometria.bbox("all"))

        def ajustar_ancho_geometria(event):
            canvas_geometria.itemconfigure(ventana_geometria, width=event.width)

        def mover_rueda_geometria(event):
            canvas_geometria.yview_scroll(int(-1 * (event.delta / 120)), "units")

        geometria_contenido.bind("<Configure>", actualizar_scroll_geometria)
        canvas_geometria.bind("<Configure>", ajustar_ancho_geometria)
        canvas_geometria.bind_all("<MouseWheel>", mover_rueda_geometria)

        geometria_contenido.grid_columnconfigure(0, weight=3)
        geometria_contenido.grid_columnconfigure(1, weight=2)

        frame_datos = ttk.LabelFrame(geometria_contenido, text="Datos generales")
        frame_datos.grid(row=0, column=0, padx=10, pady=8, sticky="nsew")
        self.crear_campo(frame_datos, "nombre_filtro", "Nombre filtro", 0)

        frame_botones_geometria = ttk.Frame(frame_datos)
        frame_botones_geometria.grid(row=1, column=0, columnspan=2, padx=5, pady=10, sticky="w")

        tk.Button(
            frame_botones_geometria,
            text="Calcular",
            command=self.calcular,
            bg="#4CAF50",
            fg="white",
            width=18,
            font=("Arial", 10, "bold")
        ).pack(side="left", padx=(0, 6))

        tk.Button(
            frame_botones_geometria,
            text="Exportar PDF",
            command=self.exportar_pdf,
            bg="#2196F3",
            fg="white",
            width=18,
            font=("Arial", 10, "bold")
        ).pack(side="left", padx=6)

        tk.Button(
            frame_botones_geometria,
            text="Ver gráfico 3D",
            command=self.mostrar_grafico_3d,
            bg="#9C27B0",
            fg="white",
            width=18,
            font=("Arial", 10, "bold")
        ).pack(side="left", padx=6)

        
        # =========================
        # IMAGEN EXPLICATIVA
        # =========================
        frame_imagen = ttk.LabelFrame(geometria_contenido, text="Esquema geométrico")
        frame_imagen.grid(row=0, column=1, rowspan=8, padx=10, pady=8, sticky="nsew")

        try:
            ruta_imagen = r"C:\Users\Christian Rossi\Desktop\feina\IMAGEN.jpg"

            imagen = Image.open(ruta_imagen)

            ancho_max = 420
            alto_max = 420

            imagen.thumbnail((ancho_max, alto_max))

            self.img_tk = ImageTk.PhotoImage(imagen)

            lbl_imagen = tk.Label(frame_imagen, image=self.img_tk)
            lbl_imagen.pack(padx=10, pady=10)

        except Exception as e:
            tk.Label(
                frame_imagen,
                text=f"No se pudo cargar la imagen:\n{e}",
                fg="red"
            ).pack(padx=10, pady=10)


        frame_cal = ttk.LabelFrame(geometria_contenido, text="CAL")
        frame_cal.grid(row=1, column=0, padx=10, pady=8, sticky="nsew")
        self.crear_campo(frame_cal, "cal_largo", "(A) Largo [m]", 0)
        self.crear_campo(frame_cal, "cal_ancho", "(B) Ancho [m]", 1)
        self.crear_campo(frame_cal, "cal_alto", "(C) Alto [m]", 2)

        frame_cas = ttk.LabelFrame(geometria_contenido, text="CAS")
        frame_cas.grid(row=2, column=0, padx=10, pady=8, sticky="nsew")
        self.crear_campo(frame_cas, "cas_alto", "(P) Alto [m]", 0)

        tk.Label(
            frame_cas,
            text="Relación usada:\nCAS largo = CAL largo\nCAS ancho = CAL ancho",
            justify="left",
            fg="blue"
        ).grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="w")

        frame_case2 = ttk.LabelFrame(geometria_contenido, text="CAS_E2")
        frame_case2.grid(row=3, column=0, padx=10, pady=8, sticky="nsew")
        self.crear_campo(frame_case2, "case2_largo", "(F) Largo [m]", 0)
        #self.crear_campo(frame_case2, "case2_ancho", "Ancho [m]", 1)
        self.crear_campo(frame_case2, "case2_alto", "(H) Alto [m]", 2, "0")

        tk.Label(
            frame_case2,
            text="CAS_E2 alto es opcional y puede ser 0.",
            justify="left",
            fg="blue"
        ).grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky="w")

        frame_tolva = ttk.LabelFrame(geometria_contenido, text="TOLVA")
        frame_tolva.grid(row=4, column=0, padx=10, pady=8, sticky="nsew")
        self.crear_campo(frame_tolva, "tolva_alto", "(L) Altura [m]", 0, "0")
        self.crear_campo(frame_tolva, "tolva_boca_desc_largo", "(M) Boca descarga largo [m]", 1)
        self.crear_campo(frame_tolva, "tolva_boca_desc_ancho", "(N) Boca descarga ancho [m]", 2)

        tk.Label(
            frame_tolva,
            text=(
                "Relaciones usadas:\n"
                "Boca superior largo = CAS_E2 largo\n"
                "Boca superior ancho = CAS_E2 ancho\n"
                "La altura de TOLVA puede ser 0."
            ),
            justify="left",
            fg="blue"
        ).grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky="w")

        frame_ratios = ttk.LabelFrame(geometria_contenido, text="Ratios de masa")
        frame_ratios.grid(row=5, column=0, padx=10, pady=8, sticky="nsew")
        self.crear_campo(frame_ratios, "ratio_cal", "Ratio CAL [kg/m²]", 0, "55")
        self.crear_campo(frame_ratios, "ratio_cuerpo", "Ratio CUERPO [kg/m²]", 1, "37")

        frame_tubos = ttk.LabelFrame(geometria_contenido, text="Tubos Inyectores Schedule 40")
        frame_tubos.grid(row=6, column=0, padx=10, pady=8, sticky="nsew")
        self.crear_campo(frame_tubos, "tubos_cantidad", "Cantidad", 0, "0")
        self.crear_campo(frame_tubos, "tubos_longitud", "Longitud [m]", 1, "0")

        tk.Label(
            frame_tubos,
            text=f"Masa tubos = Cantidad × Longitud × {PESO_TUBO_SCH40_1_PULGADA} kg/m\nValores opcionales: pueden ser 0.",
            justify="left",
            fg="blue"
        ).grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky="w")

        frame_calorifugado = ttk.LabelFrame(geometria_contenido, text="Calorifugado")
        frame_calorifugado.grid(row=7, column=0, padx=10, pady=8, sticky="nsew")
        self.crear_campo(frame_calorifugado, "densidad_calorifugado", "Densidad calorifugado [kg/m³]", 0, "0")
        self.crear_campo(frame_calorifugado, "espesor_calorifugado", "Espesor calorifugado [m]", 1, "0")
        self.crear_campo(frame_calorifugado, "espesor_chapa_calorifugado", "Espesor chapa calorifugado [m]", 2, "0")

        tk.Label(
            frame_calorifugado,
            text=(
                "Masa calorifugado = Área total × Densidad × Espesor\n"
                f"Masa chapa calorifugado = Área total × Espesor chapa × {DENSIDAD_CHAPA_CALORIFUGADO} kg/m³\n"
                "Valores opcionales: pueden ser 0."
            ),
            justify="left",
            fg="blue"
        ).grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky="w")

        frame_chapas = ttk.LabelFrame(geometria_contenido, text="Chapas especiales")
        frame_chapas.grid(row=8, column=0, padx=10, pady=8, sticky="nsew")
        self.crear_campo(frame_chapas, "deflectora_ancho", "Chapa deflectora ancho [m]", 0, "0")
        self.crear_campo(frame_chapas, "deflectora_largo", "Chapa deflectora largo [m]", 1, "0")
        self.crear_campo(frame_chapas, "venturi_mangas", "Chapa venturi número de mangas", 2, "0")

        tk.Label(
            frame_chapas,
            text=(
                f"Masa chapa deflectora = Ancho × Largo × {PESO_CHAPA_DEFLECTORA} kg/m²\n"
                f"Masa chapa venturi = Nº mangas × {PESO_CHAPA_VENTURI_POR_MANGA} kg\n"
                "Valores opcionales: pueden ser 0."
            ),
            justify="left",
            fg="blue"
        ).grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky="w")

        self.crear_pestana_filtro_operacion(tab_filtro_operacion)
        self.crear_pestana_tolva(tab_tolva)

        frame_areas = ttk.LabelFrame(tab_resultados, text="Resultados de áreas")
        frame_areas.grid(row=0, column=0, padx=10, pady=8, sticky="nsew")

        self.lbl_area_puertas = self.crear_label_resultado(frame_areas, "PUERTAS: -")
        self.lbl_area_cal = self.crear_label_resultado(frame_areas, "CAL: -")
        self.lbl_area_cas = self.crear_label_resultado(frame_areas, "CAS: -")
        self.lbl_area_case2 = self.crear_label_resultado(frame_areas, "CAS_E2: -")
        self.lbl_area_tolva = self.crear_label_resultado(frame_areas, "TOLVA: -")

        self.lbl_area_total = tk.Label(frame_areas, text="ÁREA TOTAL: -", font=("Arial", 12, "bold"))
        self.lbl_area_total.pack(anchor="w", padx=12, pady=6)

        frame_masas = ttk.LabelFrame(tab_resultados, text="Resultados de masas")
        frame_masas.grid(row=0, column=1, padx=10, pady=8, sticky="nsew")

        self.lbl_masa_puertas = self.crear_label_resultado(frame_masas, "PUERTAS: -")
        self.lbl_masa_tubos = self.crear_label_resultado(frame_masas, "TUBOS INYECTORES: -")
        self.lbl_masa_cal = self.crear_label_resultado(frame_masas, "CAL: -")
        self.lbl_masa_cas = self.crear_label_resultado(frame_masas, "CAS: -")
        self.lbl_masa_case2 = self.crear_label_resultado(frame_masas, "CAS_E2: -")
        self.lbl_masa_tolva = self.crear_label_resultado(frame_masas, "TOLVA: -")
        self.lbl_masa_deflectora = self.crear_label_resultado(frame_masas, "CHAPA DEFLECTORA: -")
        self.lbl_masa_venturi = self.crear_label_resultado(frame_masas, "CHAPA VENTURI: -")
        self.lbl_masa_calorifugado = self.crear_label_resultado(frame_masas, "CALORIFUGADO: -")
        self.lbl_masa_chapa_calorifugado = self.crear_label_resultado(frame_masas, "CHAPA CALORIFUGADO: -")

        self.lbl_masa_total = tk.Label(frame_masas, text="MASA TOTAL: -", font=("Arial", 12, "bold"))
        self.lbl_masa_total.pack(anchor="w", padx=12, pady=6)



    def crear_pestana_tolva(self, tab):
        contenedor = ttk.Frame(tab, padding=12)
        contenedor.pack(fill="both", expand=True)

        frame_inputs = ttk.Frame(contenedor)
        frame_inputs.pack(side=tk.LEFT, fill=tk.Y)

        frame_right = ttk.Frame(contenedor)
        frame_right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        frame_results = ttk.Frame(frame_right)
        frame_results.pack(side=tk.TOP, fill=tk.X)

        self.frame_tolva_canvas = ttk.Frame(frame_right, borderwidth=2, relief="sunken")
        self.frame_tolva_canvas.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True, pady=(10, 0))

        ttk.Label(
            frame_inputs,
            text="Tolva - Tronco de pirámide",
            font=("Arial", 15, "bold")
        ).pack(anchor="w", pady=(0, 15))

        # =========================
        # IMAGEN TOLVA
        # =========================
        try:
            ruta_imagen_tolva = r"C:\Users\Christian Rossi\Desktop\feina\TOLVA.jpg"

            imagen_tolva = Image.open(ruta_imagen_tolva)

            ancho_max = 420
            alto_max = 220

            imagen_tolva.thumbnail((ancho_max, alto_max))

            self.img_tolva_tk = ImageTk.PhotoImage(imagen_tolva)

            lbl_imagen_tolva = tk.Label(frame_inputs, image=self.img_tolva_tk)
            lbl_imagen_tolva.pack(padx=5, pady=(0, 15))

        except Exception as e:
            tk.Label(
                frame_inputs,
                text=f"No se pudo cargar la imagen TOLVA:\n{e}",
                fg="red"
            ).pack(padx=5, pady=(0, 15))

        self.crear_entry_tolva(frame_inputs, "tolva_a1", "Base Superior (A) [m]:", "1.0")
        self.crear_entry_tolva(frame_inputs, "tolva_b1", "Base Superior (B) [m]:", "1.0")
        self.crear_entry_tolva(frame_inputs, "tolva_a2", "Base Inferior (a) [m]:", "0.6")
        self.crear_entry_tolva(frame_inputs, "tolva_b2", "Base Inferior (b) [m]:", "0.6")
        self.crear_entry_tolva(frame_inputs, "tolva_h", "Altura (H) [m]:", "1.2")

        ttk.Separator(frame_inputs).pack(fill=tk.X, pady=8)

        self.crear_entry_tolva(frame_inputs, "tolva_ratio_kg_m3", "Ratio kg/m³:", "37")
        self.crear_entry_tolva(frame_inputs, "tolva_densidad_producto", "Densidad producto [kg/m³]:", "1000")

        tk.Button(
            frame_inputs,
            text="CALCULAR TOLVA",
            command=self.calcular_tolva,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 10, "bold")
        ).pack(fill="x", pady=(15, 6))

        tk.Button(
            frame_inputs,
            text="INFORME TOLVA PDF",
            command=self.exportar_pdf_tolva,
            bg="#2196F3",
            fg="white",
            font=("Arial", 10, "bold")
        ).pack(fill="x", pady=(0, 15))

        ttk.Label(frame_results, text="Resultados", font=("Arial", 12, "bold")).pack(anchor="w")

        self.lbl_tolva_volumen = self.crear_label_resultado(frame_results, "Volumen: -")
        self.lbl_tolva_sl = self.crear_label_resultado(frame_results, "Superficie lateral: -")
        self.lbl_tolva_masa_chapa = self.crear_label_resultado(frame_results, "Masa chapa tolva: -")
        self.lbl_tolva_material = self.crear_label_resultado(frame_results, "Masa tolva llena: -")
        self.lbl_tolva_beta = self.crear_label_resultado(frame_results, "Angulo Beta: -")
        self.lbl_tolva_alpha = self.crear_label_resultado(frame_results, "Angulo Alpha: -")

    def crear_entry_tolva(self, parent, key, texto, valor=""):
        ttk.Label(parent, text=texto).pack(anchor="w")
        var = tk.StringVar(value=valor)
        entry = ttk.Entry(parent, textvariable=var)
        entry.pack(fill=tk.X, pady=(0, 8))
        self.vars[key] = var

    def volumen_tronco(self, a1, b1, a2, b2, h):
        A1 = a1 * b1
        A2 = a2 * b2
        return (h / 3.0) * (A1 + A2 + math.sqrt(A1 * A2))

    def superficie_lateral_tolva(self, a1, b1, a2, b2, h):
        s_a = math.sqrt(h**2 + ((a2 - a1) / 2.0)**2)
        s_b = math.sqrt(h**2 + ((b2 - b1) / 2.0)**2)
        return (a1 + a2) * s_b + (b1 + b2) * s_a

    def superficie_total_tolva(self, a1, b1, a2, b2, h):
        A1 = a1 * b1
        A2 = a2 * b2
        SL = self.superficie_lateral_tolva(a1, b1, a2, b2, h)
        return A1 + A2 + SL

    def angulos_tolva(self, a1, b1, a2, b2, h):
        """
        Calcula los ángulos de inclinación de las caras de la tolva.

        Convención usada:
        - Angulo Beta: caras largas respecto a la horizontal.
          Depende de la reducción en el ancho B-b.
        - Angulo Alpha: caras cortas respecto a la horizontal.
          Depende de la reducción en el largo A-a.

        Devuelve los ángulos en grados.
        """
        delta_a = (a1 - a2) / 2.0
        delta_b = (b1 - b2) / 2.0

        angulo_largo_vertical = math.degrees(math.atan(delta_b / h))
        angulo_ancho_vertical = math.degrees(math.atan(delta_a / h))

        angulo_beta = 90.0 - angulo_largo_vertical
        angulo_alpha = 90.0 - angulo_ancho_vertical

        return angulo_beta, angulo_alpha

    def dibujar_tronco_tolva(self, a1, b1, a2, b2, h):
        for widget in self.frame_tolva_canvas.winfo_children():
            widget.destroy()

        fig = Figure(figsize=(6, 4.5), dpi=100)
        ax = fig.add_subplot(111, projection="3d")

        p0 = [0, 0, 0]
        p1 = [a2, 0, 0]
        p2 = [a2, b2, 0]
        p3 = [0, b2, 0]

        offset_x = (a2 - a1) / 2.0
        offset_y = (b2 - b1) / 2.0

        p4 = [offset_x, offset_y, h]
        p5 = [offset_x + a1, offset_y, h]
        p6 = [offset_x + a1, offset_y + b1, h]
        p7 = [offset_x, offset_y + b1, h]

        caras = [
            [p0, p1, p2, p3],
            [p4, p5, p6, p7],
            [p0, p1, p5, p4],
            [p1, p2, p6, p5],
            [p2, p3, p7, p6],
            [p3, p0, p4, p7],
        ]

        for cara in caras:
            poly = Poly3DCollection([cara], alpha=0.5)
            poly.set_edgecolor("black")
            ax.add_collection3d(poly)

        max_dim = max(a1, b1, a2, b2, h)

        ax.set_xlim(0, max_dim)
        ax.set_ylim(0, max_dim)
        ax.set_zlim(0, max_dim)

        ax.set_box_aspect((1, 1, 1))
        ax.set_proj_type("ortho")

        ax.set_xlabel("X [m]")
        ax.set_ylabel("Y [m]")
        ax.set_zlabel("Z [m]")

        canvas = FigureCanvasTkAgg(fig, master=self.frame_tolva_canvas)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def calcular_tolva(self):
        try:
            r = self.calcular_resultados_tolva()

            self.lbl_tolva_volumen.config(text=f"Volumen: {r['V']:.4f} m³")
            self.lbl_tolva_sl.config(text=f"Superficie lateral: {r['SL']:.4f} m²")
            self.lbl_tolva_masa_chapa.config(text=f"Masa chapa tolva: {r['masa_chapa_tolva']:.2f} kg")
            self.lbl_tolva_material.config(text=f"Masa tolva llena: {r['masa_material']:.2f} kg")
            self.lbl_tolva_beta.config(text=f"Angulo Beta: {r['angulo_beta']:.2f}°")
            self.lbl_tolva_alpha.config(text=f"Angulo Alpha: {r['angulo_alpha']:.2f}°")

            self.dibujar_tronco_tolva(r['a1'], r['b1'], r['a2'], r['b2'], r['h'])

        except ValueError as e:
            mensaje = str(e) if str(e) else "Revisa los campos numéricos."
            messagebox.showerror("Error", mensaje)


    def leer_datos_tolva(self):
        a1 = float(self.vars["tolva_a1"].get().replace(",", "."))
        b1 = float(self.vars["tolva_b1"].get().replace(",", "."))
        a2 = float(self.vars["tolva_a2"].get().replace(",", "."))
        b2 = float(self.vars["tolva_b2"].get().replace(",", "."))
        h = float(self.vars["tolva_h"].get().replace(",", "."))
        ratio_kg_m3 = float(self.vars["tolva_ratio_kg_m3"].get().replace(",", "."))
        densidad_producto = float(self.vars["tolva_densidad_producto"].get().replace(",", "."))

        if any(v <= 0 for v in (a1, b1, a2, b2, h, ratio_kg_m3, densidad_producto)):
            raise ValueError

        if a1 < a2 or b1 < b2:
            raise ValueError("La base superior debe ser mayor o igual que la inferior.")

        return a1, b1, a2, b2, h, ratio_kg_m3, densidad_producto

    def calcular_resultados_tolva(self):
        a1, b1, a2, b2, h, ratio_kg_m3, densidad_producto = self.leer_datos_tolva()

        A1 = a1 * b1
        A2 = a2 * b2
        delta_a = (a1 - a2) / 2.0
        delta_b = (b1 - b2) / 2.0
        s_a = math.sqrt(h**2 + delta_a**2)
        s_b = math.sqrt(h**2 + delta_b**2)

        V = self.volumen_tronco(a1, b1, a2, b2, h)
        SL = self.superficie_lateral_tolva(a1, b1, a2, b2, h)
        masa_chapa_tolva = SL * ratio_kg_m3
        masa_material = densidad_producto * V
        angulo_beta, angulo_alpha = self.angulos_tolva(a1, b1, a2, b2, h)

        return {
            "a1": a1,
            "b1": b1,
            "a2": a2,
            "b2": b2,
            "h": h,
            "ratio_kg_m3": ratio_kg_m3,
            "densidad_producto": densidad_producto,
            "A1": A1,
            "A2": A2,
            "delta_a": delta_a,
            "delta_b": delta_b,
            "s_a": s_a,
            "s_b": s_b,
            "V": V,
            "SL": SL,
            "masa_chapa_tolva": masa_chapa_tolva,
            "masa_material": masa_material,
            "angulo_beta": angulo_beta,
            "angulo_alpha": angulo_alpha,
        }

    def exportar_pdf_tolva(self):
        try:
            r = self.calcular_resultados_tolva()

            archivo = filedialog.asksaveasfilename(
                title="Guardar informe de tolva",
                defaultextension=".pdf",
                initialfile="informe_tolva.pdf",
                filetypes=[("Archivo PDF", "*.pdf")]
            )

            if not archivo:
                return

            doc = SimpleDocTemplate(
                archivo,
                pagesize=A4,
                rightMargin=35,
                leftMargin=35,
                topMargin=35,
                bottomMargin=35
            )

            styles = getSampleStyleSheet()
            elementos = []

            elementos.append(Paragraph("Informe de cálculo de tolva", styles["Title"]))
            elementos.append(Spacer(1, 10))

            elementos.append(Paragraph("1. Medidas utilizadas", styles["Heading2"]))
            datos_entrada = [
                ["Parámetro", "Valor"],
                ["Base superior A [m]", f"{r['a1']:.4f}"],
                ["Base superior B [m]", f"{r['b1']:.4f}"],
                ["Base inferior a [m]", f"{r['a2']:.4f}"],
                ["Base inferior b [m]", f"{r['b2']:.4f}"],
                ["Altura H [m]", f"{r['h']:.4f}"],
                ["Ratio chapa tolva [kg/m²]", f"{r['ratio_kg_m3']:.4f}"],
                ["Densidad producto [kg/m³]", f"{r['densidad_producto']:.4f}"],
            ]
            elementos.append(self.crear_tabla_pdf(datos_entrada))
            elementos.append(Spacer(1, 10))

            elementos.append(Paragraph("2. Resultados", styles["Heading2"]))
            resultados = [
                ["Concepto", "Resultado"],
                ["Área base superior A1", f"{r['A1']:.4f} m²"],
                ["Área base inferior A2", f"{r['A2']:.4f} m²"],
                ["Superficie lateral", f"{r['SL']:.4f} m²"],
                ["Volumen", f"{r['V']:.4f} m³"],
                ["Masa chapa tolva", f"{r['masa_chapa_tolva']:.2f} kg"],
                ["Masa tolva llena", f"{r['masa_material']:.2f} kg"],
                ["Angulo Beta", f"{r['angulo_beta']:.2f}°"],
                ["Angulo Alpha", f"{r['angulo_alpha']:.2f}°"],
            ]
            elementos.append(self.crear_tabla_pdf(resultados))
            elementos.append(Spacer(1, 10))

            elementos.append(Paragraph("3. Fórmulas utilizadas", styles["Heading2"]))
            formulas = [
                ("Área base superior", "A1 = A × B"),
                ("Área base inferior", "A2 = a × b"),
                ("Volumen tronco de pirámide", "V = H / 3 × (A1 + A2 + raíz(A1 × A2))"),
                ("Diferencia lateral largo", "Delta A = (A - a) / 2"),
                ("Diferencia lateral ancho", "Delta B = (B - b) / 2"),
                ("Generatriz asociada al largo", "sB = raíz(H² + Delta B²)"),
                ("Generatriz asociada al ancho", "sA = raíz(H² + Delta A²)"),
                ("Superficie lateral", "SL = (A + a) × sB + (B + b) × sA"),
                ("Masa chapa tolva", "Masa chapa = SL × ratio kg/m²"),
                ("Masa tolva llena", "Masa llena = V × densidad producto"),
                ("Angulo Beta", "Beta = 90° - atan(Delta B / H)"),
                ("Angulo Alpha", "Alpha = 90° - atan(Delta A / H)"),
            ]

            for titulo, formula in formulas:
                elementos.append(Paragraph(f"<b>{titulo}</b>: {formula}", styles["BodyText"]))
                elementos.append(Spacer(1, 4))

            elementos.append(Spacer(1, 8))
            elementos.append(Paragraph("4. Cálculo numérico", styles["Heading2"]))
            calculos = [
                f"A1 = {r['a1']:.4f} × {r['b1']:.4f} = {r['A1']:.4f} m²",
                f"A2 = {r['a2']:.4f} × {r['b2']:.4f} = {r['A2']:.4f} m²",
                f"Delta A = ({r['a1']:.4f} - {r['a2']:.4f}) / 2 = {r['delta_a']:.4f} m",
                f"Delta B = ({r['b1']:.4f} - {r['b2']:.4f}) / 2 = {r['delta_b']:.4f} m",
                f"sA = raíz({r['h']:.4f}² + {r['delta_a']:.4f}²) = {r['s_a']:.4f} m",
                f"sB = raíz({r['h']:.4f}² + {r['delta_b']:.4f}²) = {r['s_b']:.4f} m",
                f"SL = ({r['a1']:.4f} + {r['a2']:.4f}) × {r['s_b']:.4f} + ({r['b1']:.4f} + {r['b2']:.4f}) × {r['s_a']:.4f} = {r['SL']:.4f} m²",
                f"V = {r['h']:.4f} / 3 × ({r['A1']:.4f} + {r['A2']:.4f} + raíz({r['A1']:.4f} × {r['A2']:.4f})) = {r['V']:.4f} m³",
                f"Masa chapa = {r['SL']:.4f} × {r['ratio_kg_m3']:.4f} = {r['masa_chapa_tolva']:.2f} kg",
                f"Masa llena = {r['V']:.4f} × {r['densidad_producto']:.4f} = {r['masa_material']:.2f} kg",
                f"Beta = 90° - atan({r['delta_b']:.4f} / {r['h']:.4f}) = {r['angulo_beta']:.2f}°",
                f"Alpha = 90° - atan({r['delta_a']:.4f} / {r['h']:.4f}) = {r['angulo_alpha']:.2f}°",
            ]

            for calculo in calculos:
                elementos.append(Paragraph(calculo, styles["BodyText"]))
                elementos.append(Spacer(1, 4))

            doc.build(elementos)
            messagebox.showinfo("PDF exportado", f"Informe de tolva creado correctamente:\n{archivo}")

        except ValueError as e:
            mensaje = str(e) if str(e) else "Revisa los campos numéricos de la tolva."
            messagebox.showerror("Error de datos", mensaje)

        except Exception as e:
            messagebox.showerror("Error al exportar PDF", str(e))

    def crear_pestana_filtro_operacion(self, tab):
        contenedor = ttk.Frame(tab, padding=20)
        contenedor.pack(fill="both", expand=True)

        ttk.Label(
            contenedor,
            text="Filtro en operación",
            font=("Arial", 16, "bold")
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 15))

        frame_entradas = ttk.LabelFrame(contenedor, text="Datos de operación")
        frame_entradas.grid(row=1, column=0, padx=10, pady=8, sticky="nsew")

        frame_resultados = ttk.LabelFrame(contenedor, text="Resultados operación")
        frame_resultados.grid(row=1, column=1, padx=10, pady=8, sticky="nsew")

        contenedor.grid_columnconfigure(0, weight=1)
        contenedor.grid_columnconfigure(1, weight=1)

        self.crear_campo(frame_entradas, "op_numero_mangas", "Número de mangas", 0)
        self.crear_combo(frame_entradas, "op_longitud_mangas", "Longitud de mangas", 1, list(SUPERFICIES_MANGAS.keys()))
        self.crear_campo(frame_entradas, "op_espesor_polvo", "Espesor polvo [mm]", 2)
        self.crear_campo(frame_entradas, "op_densidad_producto", "Densidad producto [kg/m³]", 3)
        self.crear_campo(frame_entradas, "op_superficie_puertas", "Superficie puertas [m²]", 4)
        self.crear_campo(frame_entradas, "op_peso_filtro", "Peso filtro + accesorios [kg]", 5)
        self.crear_campo(frame_entradas, "op_volumen_tolva", "Volumen tolva [m³]", 6)

        tk.Button(
            frame_entradas,
            text="Calcular filtro en operación",
            command=self.calcular_filtro_operacion,
            bg="#4CAF50",
            fg="white",
            width=28,
            font=("Arial", 10, "bold")
        ).grid(row=8, column=0, columnspan=2, padx=5, pady=15, sticky="ew")

        self.lbl_op_superficie_manga = self.crear_label_resultado(frame_resultados, "Superficie manga: -")
        self.lbl_op_masa_manga = self.crear_label_resultado(frame_resultados, "Masa polvo por manga: -")
        self.lbl_op_masa_total = self.crear_label_resultado(frame_resultados, "Masa total polvo en mangas: -")
        self.lbl_op_operario = self.crear_label_resultado(frame_resultados, "Carga operario mantenimiento: -")
        self.lbl_op_peso_filtro = self.crear_label_resultado(frame_resultados, "Peso filtro + accesorios: -")
        self.lbl_op_carga_tolva = self.crear_label_resultado(frame_resultados, "Carga tolva llena: -")

        self.lbl_op_carga_total = tk.Label(
            frame_resultados,
            text="Carga total filtro: -",
            font=("Arial", 12, "bold")
        )
        self.lbl_op_carga_total.pack(anchor="w", padx=12, pady=6)

    def crear_combo(self, parent, key, texto, fila, valores):
        lbl = tk.Label(parent, text=texto)
        lbl.grid(row=fila, column=0, padx=5, pady=4, sticky="w")

        var = tk.StringVar(value=valores[0] if valores else "")
        combo = ttk.Combobox(parent, textvariable=var, values=valores, state="readonly", width=18)
        combo.grid(row=fila, column=1, padx=5, pady=4, sticky="ew")

        self.vars[key] = var

    def calcular_filtro_operacion(self):
        try:
            numero_mangas = int(self.vars["op_numero_mangas"].get().strip())
            longitud = self.vars["op_longitud_mangas"].get().strip()

            espesor_mm = float(self.vars["op_espesor_polvo"].get().strip().replace(",", "."))
            densidad_kg_m3 = float(self.vars["op_densidad_producto"].get().strip().replace(",", "."))
            superficie_puertas_m2 = float(self.vars["op_superficie_puertas"].get().strip().replace(",", "."))

            peso_filtro_kg = float(self.vars["op_peso_filtro"].get().strip().replace(",", "."))
            volumen_tolva_m3 = float(self.vars["op_volumen_tolva"].get().strip().replace(",", "."))

            if numero_mangas <= 0:
                raise ValueError

            superficie_manga_m2 = SUPERFICIES_MANGAS[longitud]

            espesor_m = espesor_mm / 1000
            masa_polvo_por_manga = superficie_manga_m2 * espesor_m * densidad_kg_m3
            masa_total_mangas = masa_polvo_por_manga * numero_mangas
            operario_mantenimiento = 150 * superficie_puertas_m2
            carga_tolva_llena = volumen_tolva_m3 * densidad_kg_m3

            carga_total_filtro = (
                peso_filtro_kg
                + masa_total_mangas
                + operario_mantenimiento
                + carga_tolva_llena
            )


            self.lbl_op_superficie_manga.config(text=f"Superficie manga: {superficie_manga_m2:.2f} m²")
            self.lbl_op_masa_manga.config(text=f"Masa polvo por manga: {masa_polvo_por_manga:.3f} kg")
            self.lbl_op_masa_total.config(text=f"Masa total polvo en mangas: {masa_total_mangas:.3f} kg")
            self.lbl_op_operario.config(
                text=f"Carga operario mantenimiento: {operario_mantenimiento:.2f} kg"
            )
            self.lbl_op_peso_filtro.config(text=f"Peso filtro + accesorios: {peso_filtro_kg:.2f} kg")
            self.lbl_op_carga_tolva.config(text=f"Carga tolva llena: {carga_tolva_llena:.2f} kg")
            self.lbl_op_carga_total.config(text=f"Carga total filtro: {carga_total_filtro:.2f} kg")

        except ValueError:
            messagebox.showerror(
                "Error",
                "Introduce valores numéricos válidos. El número de mangas debe ser mayor que cero."
            )

        except KeyError:
            messagebox.showerror(
                "Error",
                "Selecciona una longitud válida."
            )


    def crear_campo(self, parent, key, texto, fila, valor_inicial=""):
        lbl = tk.Label(parent, text=texto)
        lbl.grid(row=fila, column=0, padx=5, pady=4, sticky="w")

        var = tk.StringVar(value=valor_inicial)
        ent = tk.Entry(parent, textvariable=var, width=20)
        ent.grid(row=fila, column=1, padx=5, pady=4)

        self.vars[key] = var

    def crear_label_resultado(self, parent, texto):
        label = tk.Label(parent, text=texto, font=("Arial", 11))
        label.pack(anchor="w", padx=12, pady=2)
        return label

    def obtener_float(self, key, nombre):
        valor = self.vars[key].get().strip().replace(",", ".")

        if not valor:
            raise ValueError(f"Falta el valor de: {nombre}")

        try:
            numero = float(valor)
        except ValueError:
            raise ValueError(f"El valor de '{nombre}' no es numérico.")

        if numero <= 0:
            raise ValueError(f"El valor de '{nombre}' debe ser mayor que cero.")

        return numero

    def obtener_float_cero_o_positivo(self, key, nombre):
        valor = self.vars[key].get().strip().replace(",", ".")

        if not valor:
            return 0.0

        try:
            numero = float(valor)
        except ValueError:
            raise ValueError(f"El valor de '{nombre}' no es numérico.")

        if numero < 0:
            raise ValueError(f"El valor de '{nombre}' debe ser cero o mayor que cero.")

        return numero

    def obtener_float_opcional(self, key, nombre):
        return self.obtener_float_cero_o_positivo(key, nombre)

    def obtener_texto(self, key, nombre):
        valor = self.vars[key].get().strip()

        if not valor:
            raise ValueError(f"Falta el valor de: {nombre}")

        return valor

    def leer_datos(self):
        return {
            "cal_largo": self.obtener_float("cal_largo", "CAL largo"),
            "cal_ancho": self.obtener_float("cal_ancho", "CAL ancho"),
            "cal_alto": self.obtener_float("cal_alto", "CAL alto"),
            "cas_alto": self.obtener_float("cas_alto", "CAS alto"),

            "case2_largo": self.obtener_float("case2_largo", "CAS_E2 largo"),
            #"case2_ancho": self.obtener_float("case2_ancho", "CAS_E2 ancho"),
            "case2_ancho": self.obtener_float("cal_ancho", "CAL ancho"),
            "case2_alto": self.obtener_float_opcional("case2_alto", "CAS_E2 alto"),

            "tolva_alto": self.obtener_float_opcional("tolva_alto", "TOLVA alto"),
            "tolva_boca_desc_largo": self.obtener_float("tolva_boca_desc_largo", "TOLVA boca descarga largo"),
            "tolva_boca_desc_ancho": self.obtener_float("tolva_boca_desc_ancho", "TOLVA boca descarga ancho"),

            "ratio_cal": self.obtener_float("ratio_cal", "Ratio CAL"),
            "ratio_cuerpo": self.obtener_float("ratio_cuerpo", "Ratio CUERPO"),

            "tubos_cantidad": self.obtener_float_opcional("tubos_cantidad", "Tubos inyectores cantidad"),
            "tubos_longitud": self.obtener_float_opcional("tubos_longitud", "Tubos inyectores longitud"),

            "deflectora_ancho": self.obtener_float_opcional("deflectora_ancho", "Chapa deflectora ancho"),
            "deflectora_largo": self.obtener_float_opcional("deflectora_largo", "Chapa deflectora largo"),

            "venturi_mangas": self.obtener_float_opcional("venturi_mangas", "Chapa venturi número de mangas"),

            "densidad_calorifugado": self.obtener_float_opcional("densidad_calorifugado", "Densidad calorifugado"),
            "espesor_calorifugado": self.obtener_float_opcional("espesor_calorifugado", "Espesor calorifugado"),
            "espesor_chapa_calorifugado": self.obtener_float_opcional(
                "espesor_chapa_calorifugado",
                "Espesor chapa calorifugado"
            ),
        }

    def calcular(self):
        try:
            d = self.leer_datos()

            area_puertas = d["cal_largo"] * d["cal_ancho"]
            area_cal = 2 * (d["cal_largo"] + d["cal_ancho"]) * d["cal_alto"]
            area_cas = 2 * (d["cal_largo"] + d["cal_ancho"]) * d["cas_alto"]
            area_case2 = 2 * (d["case2_largo"] + d["case2_ancho"]) * d["case2_alto"]

            area_tolva = area_tolva_rectangular(
                d["tolva_alto"],
                d["case2_largo"],
                d["case2_ancho"],
                d["tolva_boca_desc_largo"],
                d["tolva_boca_desc_ancho"]
            )

            area_total = area_puertas + area_cal + area_cas + area_case2 + area_tolva

            masa_puertas = area_puertas * d["ratio_cal"]
            masa_cal = area_cal * d["ratio_cal"]
            masa_cas = area_cas * d["ratio_cuerpo"]
            masa_case2 = area_case2 * d["ratio_cuerpo"]
            masa_tolva = area_tolva * d["ratio_cuerpo"]
            masa_tubos = d["tubos_cantidad"] * d["tubos_longitud"] * PESO_TUBO_SCH40_1_PULGADA
            masa_deflectora = d["deflectora_ancho"] * d["deflectora_largo"] * PESO_CHAPA_DEFLECTORA
            masa_venturi = d["venturi_mangas"] * PESO_CHAPA_VENTURI_POR_MANGA
            masa_calorifugado = area_total * d["densidad_calorifugado"] * d["espesor_calorifugado"]
            masa_chapa_calorifugado = area_total * d["espesor_chapa_calorifugado"] * DENSIDAD_CHAPA_CALORIFUGADO

            masa_total = (
                masa_puertas
                + masa_cal
                + masa_cas
                + masa_case2
                + masa_tolva
                + masa_tubos
                + masa_deflectora
                + masa_venturi
                + masa_calorifugado
                + masa_chapa_calorifugado
            )

            self.resultados = {
                "area_puertas": area_puertas,
                "area_cal": area_cal,
                "area_cas": area_cas,
                "area_case2": area_case2,
                "area_tolva": area_tolva,
                "area_total": area_total,
                "masa_puertas": masa_puertas,
                "masa_cal": masa_cal,
                "masa_cas": masa_cas,
                "masa_case2": masa_case2,
                "masa_tolva": masa_tolva,
                "masa_tubos": masa_tubos,
                "masa_deflectora": masa_deflectora,
                "masa_venturi": masa_venturi,
                "masa_calorifugado": masa_calorifugado,
                "masa_chapa_calorifugado": masa_chapa_calorifugado,
                "masa_total": masa_total,
            }

            self.actualizar_resultados()
            return True

        except ValueError as e:
            messagebox.showerror("Error de datos", str(e))
            return False

        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error inesperado:\n{e}")
            return False

    def actualizar_resultados(self):
        r = self.resultados

        self.lbl_area_puertas.config(text=f"PUERTAS: {r['area_puertas']:,.2f} m²")
        self.lbl_area_cal.config(text=f"CAL: {r['area_cal']:,.2f} m²")
        self.lbl_area_cas.config(text=f"CAS: {r['area_cas']:,.2f} m²")
        self.lbl_area_case2.config(text=f"CAS_E2: {r['area_case2']:,.2f} m²")
        self.lbl_area_tolva.config(text=f"TOLVA: {r['area_tolva']:,.2f} m²")
        self.lbl_area_total.config(text=f"ÁREA TOTAL: {r['area_total']:,.2f} m²")

        self.lbl_masa_puertas.config(text=f"PUERTAS: {r['masa_puertas']:,.2f} kg")
        self.lbl_masa_cal.config(text=f"CAL: {r['masa_cal']:,.2f} kg")
        self.lbl_masa_cas.config(text=f"CAS: {r['masa_cas']:,.2f} kg")
        self.lbl_masa_case2.config(text=f"CAS_E2: {r['masa_case2']:,.2f} kg")
        self.lbl_masa_tolva.config(text=f"TOLVA: {r['masa_tolva']:,.2f} kg")
        self.lbl_masa_tubos.config(text=f"TUBOS INYECTORES: {r['masa_tubos']:,.2f} kg")
        self.lbl_masa_deflectora.config(text=f"CHAPA DEFLECTORA: {r['masa_deflectora']:,.2f} kg")
        self.lbl_masa_venturi.config(text=f"CHAPA VENTURI: {r['masa_venturi']:,.2f} kg")
        self.lbl_masa_calorifugado.config(text=f"CALORIFUGADO: {r['masa_calorifugado']:,.2f} kg")
        self.lbl_masa_chapa_calorifugado.config(text=f"CHAPA CALORIFUGADO: {r['masa_chapa_calorifugado']:,.2f} kg")
        self.lbl_masa_total.config(text=f"MASA TOTAL: {r['masa_total']:,.2f} kg")

    def mostrar_grafico_3d(self):
        try:
            d = self.leer_datos()
        except ValueError as e:
            messagebox.showerror("Error de datos", str(e))
            return

        if d["tolva_boca_desc_largo"] >= d["case2_largo"] or d["tolva_boca_desc_ancho"] >= d["case2_ancho"]:
            messagebox.showwarning(
                "Aviso TOLVA",
                "La boca de descarga de la TOLVA debería ser menor que la boca superior CAS_E2."
            )

        fig = plt.figure(figsize=(11, 8))
        ax = fig.add_subplot(111, projection="3d")

        x0 = 0
        y0 = 0

        z_tolva = 0
        z_case2 = z_tolva + d["tolva_alto"]
        z_cas = z_case2 + d["case2_alto"]
        z_cal = z_cas + d["cas_alto"]
        z_puertas = z_cal + d["cal_alto"]

        dibujar_tolva(
            ax,
            x0,
            y0,
            z_tolva,
            d["case2_largo"],
            d["case2_ancho"],
            d["tolva_boca_desc_largo"],
            d["tolva_boca_desc_ancho"],
            d["tolva_alto"],
            "gold"
        )

        dibujar_prisma_abierto(ax, x0, y0, z_case2, d["case2_largo"], d["case2_ancho"], d["case2_alto"], "mediumpurple", "CAS_E2")
        dibujar_prisma_abierto(ax, x0, y0, z_cas, d["cal_largo"], d["cal_ancho"], d["cas_alto"], "limegreen", "CAS")
        dibujar_prisma_abierto(ax, x0, y0, z_cal, d["cal_largo"], d["cal_ancho"], d["cal_alto"], "dodgerblue", "CAL")
        dibujar_placa(ax, x0, y0, z_puertas, d["cal_largo"], d["cal_ancho"], "darkorange", "PUERTAS")

        dibujar_lineas_alineacion(ax, x0, y0, z_case2, z_puertas, d["cal_largo"], d["cal_ancho"])
        dibujar_lineas_alineacion(ax, x0, y0, z_tolva, z_case2 + d["case2_alto"], d["case2_largo"], d["case2_ancho"])

        ax.set_xlabel("X - Largo [m]")
        ax.set_ylabel("Y - Ancho [m]")
        ax.set_zlabel("Z - Altura [m]")
        ax.set_title("Vista 3D de superficies alineadas")

        max_largo = max(d["cal_largo"], d["case2_largo"])
        max_ancho = max(d["cal_ancho"], d["case2_ancho"])
        max_altura = max(z_puertas, 0.1)

        dimension_maxima = max(max_largo, max_ancho, max_altura)

        ax.set_xlim(0, dimension_maxima)
        ax.set_ylim(0, dimension_maxima)
        ax.set_zlim(0, dimension_maxima)

        ax.set_box_aspect((1, 1, 1))        

        ax.view_init(elev=24, azim=-58)
        ax.set_box_aspect((1, 1, 1))
        ax.set_proj_type("ortho")
        ax.grid(True)
        plt.tight_layout()
        plt.show()

    def exportar_stl(self):
        try:
            d = self.leer_datos()
            nombre_filtro = self.obtener_texto("nombre_filtro", "Nombre filtro")

            if d["tolva_boca_desc_largo"] >= d["case2_largo"] or d["tolva_boca_desc_ancho"] >= d["case2_ancho"]:
                continuar = messagebox.askyesno(
                    "Aviso TOLVA",
                    "La boca de descarga de la TOLVA debería ser menor que la boca superior CAS_E2.\n\n"
                    "¿Quieres exportar el STL igualmente?"
                )
                if not continuar:
                    return

            triangulos = crear_triangulos_filtro(d)

            if not triangulos:
                messagebox.showerror("Error STL", "No hay geometría suficiente para generar el STL.")
                return

            nombre_archivo = f"{nombre_filtro}.stl"
            archivo = filedialog.asksaveasfilename(
                title="Guardar modelo STL",
                defaultextension=".stl",
                initialfile=nombre_archivo,
                filetypes=[("Archivo STL", "*.stl")]
            )

            if not archivo:
                return

            escribir_stl_ascii(archivo, nombre_filtro, triangulos)

            messagebox.showinfo(
                "STL exportado",
                f"Modelo STL creado correctamente:\n{archivo}\n\n"
                f"Triángulos exportados: {len(triangulos)}"
            )

        except ValueError as e:
            messagebox.showerror("Error de datos", str(e))

        except Exception as e:
            messagebox.showerror("Error al exportar STL", str(e))


    def exportar_pdf(self):
        calculo_ok = self.calcular()

        if not calculo_ok:
            return

        try:
            nombre_filtro = self.obtener_texto("nombre_filtro", "Nombre filtro")
            nombre_archivo = f"{nombre_filtro}_informe_calculo_superficies_masas.pdf"

            archivo = filedialog.asksaveasfilename(
                title="Guardar informe PDF",
                defaultextension=".pdf",
                initialfile=nombre_archivo,
                filetypes=[("Archivo PDF", "*.pdf")]
            )

            if not archivo:
                return

            d = self.leer_datos()
            r = self.resultados

            doc = SimpleDocTemplate(
                archivo,
                pagesize=A4,
                rightMargin=35,
                leftMargin=35,
                topMargin=35,
                bottomMargin=35
            )

            styles = getSampleStyleSheet()
            elementos = []

            g_largo = math.sqrt(d["tolva_alto"]**2 + ((d["case2_ancho"] - d["tolva_boca_desc_ancho"]) / 2) ** 2)
            g_ancho = math.sqrt(d["tolva_alto"]**2 + ((d["case2_largo"] - d["tolva_boca_desc_largo"]) / 2) ** 2)

            elementos.append(Paragraph("Informe de cálculo de superficies y masas", styles["Title"]))
            elementos.append(Spacer(1, 8))
            elementos.append(Paragraph(f"<b>Nombre filtro:</b> {nombre_filtro}", styles["Heading2"]))
            elementos.append(Spacer(1, 12))

            elementos.append(Paragraph("1. Suposiciones de cálculo", styles["Heading2"]))

            supuestos = [
                "CAL se considera como un cuerpo rectangular abierto, calculando únicamente su superficie lateral.",
                "CAS utiliza el mismo largo y ancho que CAL.",
                "CAS_E2 se considera como un cuerpo rectangular abierto, calculando su superficie lateral.",
                "CAS_E2 alto puede ser 0.",
                "PUERTAS se estima como una superficie plana igual a CAL largo por CAL ancho.",
                "La TOLVA se considera como una tolva rectangular troncopiramidal.",
                "La boca superior de la TOLVA coincide con las dimensiones de CAS_E2.",
                "La altura de TOLVA puede ser 0.",
                f"Ratio CAL adoptado: {self.vars['ratio_cal'].get()} kg/m².",
                f"Ratio CUERPO adoptado: {self.vars['ratio_cuerpo'].get()} kg/m².",
                f"Los tubos inyectores Schedule 40 se calculan con {PESO_TUBO_SCH40_1_PULGADA} kg/m.",
                f"La chapa deflectora se calcula con {PESO_CHAPA_DEFLECTORA} kg/m².",
                f"La chapa venturi se calcula con {PESO_CHAPA_VENTURI_POR_MANGA} kg por manga.",
                "Los campos opcionales pueden ser 0.",
            ]

            for supuesto in supuestos:
                elementos.append(Paragraph(f"- {supuesto}", styles["BodyText"]))

            elementos.append(Spacer(1, 12))
            elementos.append(Paragraph("2. Datos de entrada", styles["Heading2"]))

            datos_entrada = [
                ["Parámetro", "Valor"],
                ["Nombre filtro", nombre_filtro],
                ["CAL largo [m]", self.vars["cal_largo"].get()],
                ["CAL ancho [m]", self.vars["cal_ancho"].get()],
                ["CAL alto [m]", self.vars["cal_alto"].get()],
                ["CAS alto [m]", self.vars["cas_alto"].get()],
                ["CAS_E2 largo [m]", self.vars["case2_largo"].get()],
                ["CAS_E2 ancho [m]", self.vars["cal_ancho"].get() + "  (igual a CAL ancho)"],
                ["CAS_E2 alto [m]", self.vars["case2_alto"].get()],
                ["TOLVA altura [m]", self.vars["tolva_alto"].get()],
                ["TOLVA boca descarga largo [m]", self.vars["tolva_boca_desc_largo"].get()],
                ["TOLVA boca descarga ancho [m]", self.vars["tolva_boca_desc_ancho"].get()],
                ["Ratio CAL [kg/m²]", self.vars["ratio_cal"].get()],
                ["Ratio CUERPO [kg/m²]", self.vars["ratio_cuerpo"].get()],
                ["Densidad calorifugado [kg/m³]", self.vars["densidad_calorifugado"].get()],
                ["Espesor calorifugado [m]", self.vars["espesor_calorifugado"].get()],
                ["Espesor chapa calorifugado [m]", self.vars["espesor_chapa_calorifugado"].get()],
                ["Tubos cantidad", self.vars["tubos_cantidad"].get()],
                ["Tubos longitud [m]", self.vars["tubos_longitud"].get()],
                ["Chapa deflectora ancho [m]", self.vars["deflectora_ancho"].get()],
                ["Chapa deflectora largo [m]", self.vars["deflectora_largo"].get()],
                ["Chapa venturi nº mangas", self.vars["venturi_mangas"].get()],
            ]

            elementos.append(self.crear_tabla_pdf(datos_entrada))

            elementos.append(Spacer(1, 12))
            elementos.append(Paragraph("3. Resultados de áreas", styles["Heading2"]))

            resultados_areas = [
                ["Concepto", "Área"],
                ["PUERTAS", f"{r['area_puertas']:,.2f} m²"],
                ["CAL", f"{r['area_cal']:,.2f} m²"],
                ["CAS", f"{r['area_cas']:,.2f} m²"],
                ["CAS_E2", f"{r['area_case2']:,.2f} m²"],
                ["TOLVA", f"{r['area_tolva']:,.2f} m²"],
                ["ÁREA TOTAL", f"{r['area_total']:,.2f} m²"],
            ]

            elementos.append(self.crear_tabla_pdf(resultados_areas))

            elementos.append(Spacer(1, 12))
            elementos.append(Paragraph("4. Resultados de masas", styles["Heading2"]))

            resultados_masas = [
                ["Concepto", "Masa"],
                ["PUERTAS", f"{r['masa_puertas']:,.2f} kg"],
                ["CAL", f"{r['masa_cal']:,.2f} kg"],
                ["CAS", f"{r['masa_cas']:,.2f} kg"],
                ["CAS_E2", f"{r['masa_case2']:,.2f} kg"],
                ["TOLVA", f"{r['masa_tolva']:,.2f} kg"],
                ["TUBOS INYECTORES", f"{r['masa_tubos']:,.2f} kg"],
                ["CHAPA DEFLECTORA", f"{r['masa_deflectora']:,.2f} kg"],
                ["CHAPA VENTURI", f"{r['masa_venturi']:,.2f} kg"],
                ["CALORIFUGADO", f"{r['masa_calorifugado']:,.2f} kg"],
                ["CHAPA CALORIFUGADO", f"{r['masa_chapa_calorifugado']:,.2f} kg"],
                ["MASA TOTAL", f"{r['masa_total']:,.2f} kg"],
            ]

            elementos.append(self.crear_tabla_pdf(resultados_masas))

            elementos.append(Spacer(1, 12))
            elementos.append(Paragraph("5. Fórmulas utilizadas", styles["Heading2"]))

            formulas = [
                (
                    "Área PUERTAS = CAL largo × CAL ancho",
                    f"Área PUERTAS = {d['cal_largo']:.2f} × {d['cal_ancho']:.2f} = {r['area_puertas']:,.2f} m²"
                ),
                (
                    "Área CAL = 2 × (CAL largo + CAL ancho) × CAL alto",
                    f"Área CAL = 2 × ({d['cal_largo']:.2f} + {d['cal_ancho']:.2f}) × {d['cal_alto']:.2f} = {r['area_cal']:,.2f} m²"
                ),
                (
                    "Área CAS = 2 × (CAL largo + CAL ancho) × CAS alto",
                    f"Área CAS = 2 × ({d['cal_largo']:.2f} + {d['cal_ancho']:.2f}) × {d['cas_alto']:.2f} = {r['area_cas']:,.2f} m²"
                ),
                (
                    "Área CAS_E2 = 2 × (CAS_E2 largo + CAS_E2 ancho) × CAS_E2 alto",
                    f"Área CAS_E2 = 2 × ({d['case2_largo']:.2f} + {d['case2_ancho']:.2f}) × {d['case2_alto']:.2f} = {r['area_case2']:,.2f} m²"
                ),
                (
                    "g_largo = raíz cuadrada de [h² + ((W1 - W2) / 2)²]",
                    f"g_largo = raíz cuadrada de [{d['tolva_alto']:.2f}² + (({d['case2_ancho']:.2f} - {d['tolva_boca_desc_ancho']:.2f}) / 2)²] = {g_largo:.2f} m"
                ),
                (
                    "g_ancho = raíz cuadrada de [h² + ((L1 - L2) / 2)²]",
                    f"g_ancho = raíz cuadrada de [{d['tolva_alto']:.2f}² + (({d['case2_largo']:.2f} - {d['tolva_boca_desc_largo']:.2f}) / 2)²] = {g_ancho:.2f} m"
                ),
                (
                    "Área TOLVA = (L1 + L2) × g_largo + (W1 + W2) × g_ancho",
                    f"Área TOLVA = ({d['case2_largo']:.2f} + {d['tolva_boca_desc_largo']:.2f}) × {g_largo:.2f} + "
                    f"({d['case2_ancho']:.2f} + {d['tolva_boca_desc_ancho']:.2f}) × {g_ancho:.2f} = {r['area_tolva']:,.2f} m²"
                ),
                (
                    "Masa total = suma de todas las masas calculadas",
                    f"Masa total = {r['masa_total']:,.2f} kg"
                ),
            ]

            for formula, calculo in formulas:
                elementos.append(Paragraph(f"<b>{formula}</b>", styles["BodyText"]))
                elementos.append(Paragraph(calculo, styles["BodyText"]))
                elementos.append(Spacer(1, 6))

            doc.build(elementos)

            messagebox.showinfo("PDF exportado", f"Documento creado correctamente:\n{archivo}")

        except Exception as e:
            messagebox.showerror("Error al exportar PDF", str(e))

    def crear_tabla_pdf(self, datos):
        tabla = Table(datos, colWidths=[260, 210])
        tabla.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("PADDING", (0, 0), (-1, -1), 6),
        ]))
        return tabla

    def guardar_configuracion(self):
        archivo = filedialog.asksaveasfilename(
            title="Guardar configuración",
            defaultextension=".json",
            filetypes=[("Archivo JSON", "*.json")]
        )

        if not archivo:
            return

        datos = {key: var.get() for key, var in self.vars.items()}

        try:
            with open(archivo, "w", encoding="utf-8") as f:
                json.dump(datos, f, indent=4, ensure_ascii=False)

            messagebox.showinfo("Configuración guardada", "La configuración se guardó correctamente.")

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar la configuración:\n{e}")

    def cargar_configuracion(self):
        archivo = filedialog.askopenfilename(
            title="Cargar configuración",
            filetypes=[("Archivo JSON", "*.json")]
        )

        if not archivo:
            return

        try:
            with open(archivo, "r", encoding="utf-8") as f:
                datos = json.load(f)

            for key, value in datos.items():
                if key in self.vars:
                    self.vars[key].set(value)

            messagebox.showinfo("Configuración cargada", "La configuración se cargó correctamente.")

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar la configuración:\n{e}")

    def limpiar(self):
        valores_defecto = {
            "ratio_cal": "55",
            "ratio_cuerpo": "37",
            "case2_alto": "0",
            "tolva_alto": "0",
            "tubos_cantidad": "0",
            "tubos_longitud": "0",
            "densidad_calorifugado": "0",
            "espesor_calorifugado": "0",
            "espesor_chapa_calorifugado": "0",
            "deflectora_ancho": "0",
            "deflectora_largo": "0",
            "venturi_mangas": "0",
            "tolva_ratio_kg_m3": "37",
            "tolva_densidad_producto": "1000",
        }

        for key, var in self.vars.items():
            var.set(valores_defecto.get(key, ""))

        self.resultados = {}

        self.lbl_area_puertas.config(text="PUERTAS: -")
        self.lbl_area_cal.config(text="CAL: -")
        self.lbl_area_cas.config(text="CAS: -")
        self.lbl_area_case2.config(text="CAS_E2: -")
        self.lbl_area_tolva.config(text="TOLVA: -")
        self.lbl_area_total.config(text="ÁREA TOTAL: -")

        self.lbl_masa_puertas.config(text="PUERTAS: -")
        self.lbl_masa_cal.config(text="CAL: -")
        self.lbl_masa_cas.config(text="CAS: -")
        self.lbl_masa_case2.config(text="CAS_E2: -")
        self.lbl_masa_tolva.config(text="TOLVA: -")
        self.lbl_masa_tubos.config(text="TUBOS INYECTORES: -")
        self.lbl_masa_deflectora.config(text="CHAPA DEFLECTORA: -")
        self.lbl_masa_venturi.config(text="CHAPA VENTURI: -")
        self.lbl_masa_calorifugado.config(text="CALORIFUGADO: -")
        self.lbl_masa_chapa_calorifugado.config(text="CHAPA CALORIFUGADO: -")
        self.lbl_masa_total.config(text="MASA TOTAL: -")

        self.lbl_tolva_volumen.config(text="Volumen: -")
        self.lbl_tolva_sl.config(text="Superficie lateral: -")
        self.lbl_tolva_masa_chapa.config(text="Masa chapa tolva: -")
        self.lbl_tolva_material.config(text="Masa tolva llena: -")
        self.lbl_tolva_beta.config(text="Angulo Beta: -")
        self.lbl_tolva_alpha.config(text="Angulo Alpha: -")


if __name__ == "__main__":
    app = App()
    app.mainloop()