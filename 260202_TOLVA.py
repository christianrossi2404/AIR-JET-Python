import tkinter as tk
from tkinter import ttk, messagebox
import math

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d.art3d import Poly3DCollection


# =========================================================
#     CÁLCULOS GEOMÉTRICOS
# =========================================================

def volumen_tronco(a1: float, b1: float, a2: float, b2: float, h: float) -> float:
    """Volumen del tronco de pirámide rectangular."""
    A1 = a1 * b1
    A2 = a2 * b2
    return (h / 3.0) * (A1 + A2 + math.sqrt(A1 * A2))


def superficie_lateral(a1: float, b1: float, a2: float, b2: float, h: float) -> float:
    """Superficie lateral (4 caras) del tronco de pirámide rectangular."""
    s_a = math.sqrt(h**2 + ((a2 - a1) / 2.0)**2)  # generatriz asociada a lados 'b'
    s_b = math.sqrt(h**2 + ((b2 - b1) / 2.0)**2)  # generatriz asociada a lados 'a'
    return (a1 + a2) * s_b + (b1 + b2) * s_a


def superficie_total(a1: float, b1: float, a2: float, b2: float, h: float) -> float:
    """Superficie total (bases + lateral)."""
    A1 = a1 * b1
    A2 = a2 * b2
    SL = superficie_lateral(a1, b1, a2, b2, h)
    return A1 + A2 + SL


# =========================================================
#     FUNCIÓN PARA GRAFICAR EL TRONCO DE PIRÁMIDE
# =========================================================

def dibujar_tronco(a1: float, b1: float, a2: float, b2: float, h: float, canvas_frame: ttk.Frame) -> None:
    fig = Figure(figsize=(6, 4.5), dpi=100)
    ax = fig.add_subplot(111, projection="3d")

    # Base inferior (z=0)
    p0 = [0, 0, 0]
    p1 = [a2, 0, 0]
    p2 = [a2, b2, 0]
    p3 = [0, b2, 0]

    # Base superior (z=h) centrada
    offset_x = (a2 - a1) / 2.0
    offset_y = (b2 - b1) / 2.0

    p4 = [offset_x, offset_y, h]
    p5 = [offset_x + a1, offset_y, h]
    p6 = [offset_x + a1, offset_y + b1, h]
    p7 = [offset_x, offset_y + b1, h]

    caras = [
        [p0, p1, p2, p3],  # base inferior
        [p4, p5, p6, p7],  # base superior
        [p0, p1, p5, p4],  # laterales
        [p1, p2, p6, p5],
        [p2, p3, p7, p6],
        [p3, p0, p4, p7],
    ]

    for cara in caras:
        poly = Poly3DCollection([cara], alpha=0.5)
        poly.set_edgecolor("black")
        ax.add_collection3d(poly)

    ax.set_xlabel("X [m]")
    ax.set_ylabel("Y [m]")
    ax.set_zlabel("Z [m]")

    # Límites para que no se deforme ni se corte
    max_x = max(a2, offset_x + a1)
    max_y = max(b2, offset_y + b1)
    ax.set_xlim(0, max_x)
    ax.set_ylim(0, max_y)
    ax.set_zlim(0, h)

    # Aspect ratio aproximado
    ax.set_box_aspect([max_x if max_x else 1, max_y if max_y else 1, h if h else 1])

    canvas = FigureCanvasTkAgg(fig, master=canvas_frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)


# =========================================================
#               INTERFAZ TKINTER
# =========================================================

root = tk.Tk()
root.title("Cálculo Tronco de Pirámide / Tolva")
root.minsize(950, 520)

# Layout principal
frame_inputs = ttk.Frame(root, padding=12)
frame_inputs.pack(side=tk.LEFT, fill=tk.Y)

frame_right = ttk.Frame(root, padding=12)
frame_right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

frame_results = ttk.Frame(frame_right)
frame_results.pack(side=tk.TOP, fill=tk.X)

frame_canvas = ttk.Frame(frame_right, borderwidth=2, relief="sunken")
frame_canvas.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True, pady=(10, 0))


# =========================
# Entradas
# =========================
def add_labeled_entry(parent, label_text, default=""):
    ttk.Label(parent, text=label_text).pack(anchor="w")
    e = ttk.Entry(parent)
    e.pack(fill=tk.X, pady=(0, 8))
    if default != "":
        e.insert(0, default)
    return e


ttk.Label(frame_inputs, text="Dimensiones", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 10))

entry_a1 = add_labeled_entry(frame_inputs, "Base Superior (a1) [m]:", "0.6")
entry_b1 = add_labeled_entry(frame_inputs, "Base Superior (b1) [m]:", "0.6")
entry_a2 = add_labeled_entry(frame_inputs, "Base Inferior (a2) [m]:", "1.0")
entry_b2 = add_labeled_entry(frame_inputs, "Base Inferior (b2) [m]:", "1.0")
entry_h  = add_labeled_entry(frame_inputs, "Altura (h) [m]:", "1.2")

ttk.Separator(frame_inputs).pack(fill=tk.X, pady=8)

ttk.Label(frame_inputs, text="Chapa (estructura)", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 10))

entry_densidad_acero = add_labeled_entry(frame_inputs, "Densidad acero [kg/m³]:", "7850")
entry_extra_fijo = add_labeled_entry(frame_inputs, "Extra fijo [kg] (opcional):", "13")

ttk.Separator(frame_inputs).pack(fill=tk.X, pady=8)

ttk.Label(frame_inputs, text="Material (tolva llena)", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 10))

entry_densidad_producto = add_labeled_entry(frame_inputs, "Densidad producto [kg/m³]:", "1000")


# =========================
# Resultados
# =========================
ttk.Label(frame_results, text="Resultados", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 6))

label_volumen = ttk.Label(frame_results, text="Volumen: —")
label_volumen.pack(anchor="w")

label_superficie_lateral = ttk.Label(frame_results, text="Superficie Lateral: —")
label_superficie_lateral.pack(anchor="w")

label_superficie_total = ttk.Label(frame_results, text="Superficie Total: —")
label_superficie_total.pack(anchor="w")

label_masa_3mm = ttk.Label(frame_results, text="Masa chapa 3 mm: —")
label_masa_3mm.pack(anchor="w")

label_masa_4mm = ttk.Label(frame_results, text="Masa chapa 4 mm: —")
label_masa_4mm.pack(anchor="w")

label_masa_material = ttk.Label(frame_results, text="Masa tolva llena (material): —")
label_masa_material.pack(anchor="w")


# =========================================================
#       FUNCIÓN PRINCIPAL DEL BOTÓN CALCULAR
# =========================================================

def calcular():
    # Leer y validar datos
    try:
        a1 = float(entry_a1.get())
        b1 = float(entry_b1.get())
        a2 = float(entry_a2.get())
        b2 = float(entry_b2.get())
        h = float(entry_h.get())

        densidad_acero = float(entry_densidad_acero.get())
        extra_fijo = float(entry_extra_fijo.get() or 0.0)

        densidad_producto = float(entry_densidad_producto.get())
    except ValueError:
        messagebox.showerror("Error", "Revisa los campos: deben ser números.")
        return

    if any(v <= 0 for v in (a1, b1, a2, b2, h, densidad_acero, densidad_producto)):
        messagebox.showerror("Error", "Todas las dimensiones y densidades deben ser > 0.")
        return

    # NOTA: Geometría asumida: base inferior (a2,b2) >= base superior (a1,b1)
    if a1 < a2 or b1 < b2:
        messagebox.showerror(
            "Error",
            "La base superior (a1,b1) debe ser mayor o igual que la base inferior (a2,b2)."
        )
        return

    # Cálculos geométricos
    V = volumen_tronco(a1, b1, a2, b2, h)
    SL = superficie_lateral(a1, b1, a2, b2, h)
    ST = superficie_total(a1, b1, a2, b2, h)

    # Masa chapa: Masa = Superficie_lateral * espesor * densidad + extra_fijo
    masa_3mm = SL * (0.003 * densidad_acero + extra_fijo)
    masa_4mm = SL * (0.004 * densidad_acero + extra_fijo)

    # Tolva llena de material
    masa_material = densidad_producto * V  # kg

    # Mostrar resultados
    label_volumen.config(text=f"Volumen: {V:.4f} m³")
    label_superficie_lateral.config(text=f"Superficie Lateral: {SL:.4f} m²")
    label_superficie_total.config(text=f"Superficie Total: {ST:.4f} m²")
    label_masa_3mm.config(text=f"Masa chapa 3 mm: {masa_3mm:.2f} kg")
    label_masa_4mm.config(text=f"Masa chapa 4 mm: {masa_4mm:.2f} kg")
    label_masa_material.config(text=f"Masa tolva llena (material): {masa_material:.2f} kg")

    # Borrar gráfico anterior
    for widget in frame_canvas.winfo_children():
        widget.destroy()

    # Dibujar tronco
    dibujar_tronco(a1, b1, a2, b2, h, frame_canvas)


ttk.Button(frame_inputs, text="CALCULAR", command=calcular).pack(pady=12, fill=tk.X)

root.mainloop()
