import tkinter as tk
from tkinter import ttk, messagebox


def actualizar_rev2(valor):
    var_rev2_valor.set(f"{float(valor):.0f} rpm")
    calcular()


def calcular(event=None):
    try:
        q1 = float(entry_q1.get())
        p1 = float(entry_p1.get())
        pot1 = float(entry_pot1.get())
        rev1 = float(entry_rev1.get())
        rev2 = float(scale_rev2.get())
        rev_max = float(entry_revmax.get())
        polos = float(entry_polos.get())

        if rev1 <= 0 or rev2 <= 0 or rev_max <= 0 or polos <= 0:
            return

        # Frecuencias
        f1 = rev1 * polos / 120
        f2 = rev2 * polos / 120
        fmax = rev_max * polos / 120

        # Leyes ventiladores
        ratio = rev2 / rev1

        q2 = q1 * ratio
        p2 = p1 * ratio**2
        pot2 = pot1 * ratio**3

        # Mostrar resultados
        var_f1.set(f"{f1:.2f}")
        var_f2.set(f"{f2:.2f}")
        var_fmax.set(f"{fmax:.2f}")
        var_q2.set(f"{q2:.2f}")
        var_p2.set(f"{p2:.2f}")
        var_pot2.set(f"{pot2:.2f}")

        # Aviso visual
        if rev2 > rev_max:
            label_warning.config(
                text=(
                    f"⚠ CUIDADO: Se supera velocidad máxima\n"
                    f"Frec. máxima permitida: {fmax:.2f} Hz"
                ),
                foreground="red"
            )
        else:
            label_warning.config(
                text="",
                foreground="green"
            )

    except:
        pass


root = tk.Tk()
root.title("Ley de los ventiladores")
root.geometry("560x600")
root.resizable(False, False)

frame = ttk.Frame(root, padding=20)
frame.pack(fill="both", expand=True)

titulo = ttk.Label(
    frame,
    text="Cálculo Ley de los Ventiladores",
    font=("Arial", 14, "bold")
)
titulo.grid(row=0, column=0, columnspan=3, pady=(0, 15))

# Inputs
labels = [
    "Caudal 1 [m³/h]",
    "Presión 1 [mmca]",
    "Potencia 1 [kW]",
    "Rev1 [rpm]",
    "Velocidad máxima ventilador [rpm]",
    "Polos motor"
]

entries = []

for i, text in enumerate(labels, start=1):

    ttk.Label(frame, text=text).grid(
        row=i,
        column=0,
        sticky="w",
        pady=5
    )

    entry = ttk.Entry(frame, width=22)

    entry.grid(
        row=i,
        column=1,
        columnspan=2,
        sticky="w",
        pady=5
    )

    # Recalcular automáticamente al escribir
    entry.bind("<KeyRelease>", calcular)

    entries.append(entry)

(
    entry_q1,
    entry_p1,
    entry_pot1,
    entry_rev1,
    entry_revmax,
    entry_polos
) = entries

# Slider Rev2
ttk.Label(
    frame,
    text="Rev2 [rpm]"
).grid(row=7, column=0, sticky="w", pady=10)

scale_rev2 = tk.Scale(
    frame,
    from_=0,
    to=3600,
    orient="horizontal",
    length=280,
    resolution=1,
    command=actualizar_rev2
)

scale_rev2.set(1500)

scale_rev2.grid(
    row=7,
    column=1,
    sticky="w"
)

var_rev2_valor = tk.StringVar(value="1500 rpm")

ttk.Label(
    frame,
    textvariable=var_rev2_valor,
    font=("Arial", 10, "bold")
).grid(
    row=7,
    column=2,
    sticky="w",
    padx=10
)

# Mensaje warning
label_warning = ttk.Label(
    frame,
    text="",
    font=("Arial", 10, "bold")
)

label_warning.grid(
    row=8,
    column=0,
    columnspan=3,
    pady=10
)

# Separador
ttk.Separator(frame).grid(
    row=9,
    column=0,
    columnspan=3,
    sticky="ew",
    pady=10
)

# Variables resultados
var_f1 = tk.StringVar()
var_f2 = tk.StringVar()
var_fmax = tk.StringVar()
var_q2 = tk.StringVar()
var_p2 = tk.StringVar()
var_pot2 = tk.StringVar()

# Resultados
resultados = [
    ("Frecuencia 1 [Hz]", var_f1),
    ("Frecuencia 2 [Hz]", var_f2),
    ("Frecuencia máxima permitida [Hz]", var_fmax),
    ("Caudal 2 [m³/h]", var_q2),
    ("Presión 2 [mmca]", var_p2),
    ("Potencia 2 [kW]", var_pot2),
]

for i, (texto, variable) in enumerate(resultados, start=10):

    ttk.Label(
        frame,
        text=texto
    ).grid(
        row=i,
        column=0,
        sticky="w",
        pady=5
    )

    ttk.Label(
        frame,
        textvariable=variable,
        font=("Arial", 10, "bold")
    ).grid(
        row=i,
        column=1,
        sticky="w",
        pady=5
    )

root.mainloop()