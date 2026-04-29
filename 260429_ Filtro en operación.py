import tkinter as tk
from tkinter import ttk, messagebox

SUPERFICIES_MANGAS = {
    "4 ft": 0.49,
    "6 ft": 0.75,
    "8 ft": 1.00,
    "10 ft": 1.25,
    "12 ft": 1.50,
    "14 ft": 1.80,
}

def calcular():
    try:
        numero_mangas = int(entry_numero_mangas.get())
        longitud = combo_longitud.get()

        espesor_mm = float(entry_espesor.get())
        densidad_kg_m3 = float(entry_densidad.get())
        superficie_puertas_m2 = float(entry_superficie_puertas.get())

        if numero_mangas <= 0:
            raise ValueError

        superficie_manga_m2 = SUPERFICIES_MANGAS[longitud]

        # Conversión mm → m
        espesor_m = espesor_mm / 1000

        # Masa polvo por manga
        masa_polvo_por_manga = superficie_manga_m2 * espesor_m * densidad_kg_m3

        # Masa total en mangas
        masa_total_mangas = masa_polvo_por_manga * numero_mangas

        # Carga operario mantenimiento
        operario_mantenimiento = 150 * superficie_puertas_m2

        # Resultados
        label_superficie_manga.config(
            text=f"Superficie manga: {superficie_manga_m2:.2f} m²"
        )

        label_masa_manga.config(
            text=f"Masa polvo por manga: {masa_polvo_por_manga:.3f} kg"
        )

        label_masa_total.config(
            text=f"Masa total polvo en mangas: {masa_total_mangas:.3f} kg"
        )

        label_operario.config(
            text=f"Carga operario mantenimiento: {operario_mantenimiento:.2f} kg"
        )

    except ValueError:
        messagebox.showerror(
            "Error",
            "Introduce valores numéricos válidos."
        )
    except KeyError:
        messagebox.showerror(
            "Error",
            "Selecciona una longitud válida."
        )


# Ventana
ventana = tk.Tk()
ventana.title("Cálculo Operación Filtro")
ventana.geometry("500x600")
ventana.resizable(True, True)

frame = ttk.Frame(ventana, padding=20)
frame.pack(fill="both", expand=True)

ttk.Label(
    frame,
    text="Cálculo Operación Filtro",
    font=("Arial", 18, "bold")
).pack(pady=(0, 20))

# Entradas
ttk.Label(frame, text="Número de mangas").pack(anchor="w")
entry_numero_mangas = ttk.Entry(frame)
entry_numero_mangas.pack(fill="x", pady=5)

ttk.Label(frame, text="Longitud de mangas").pack(anchor="w")
combo_longitud = ttk.Combobox(
    frame,
    values=list(SUPERFICIES_MANGAS.keys()),
    state="readonly"
)
combo_longitud.pack(fill="x", pady=5)
combo_longitud.current(0)

ttk.Label(frame, text="Espesor polvo [mm]").pack(anchor="w")
entry_espesor = ttk.Entry(frame)
entry_espesor.pack(fill="x", pady=5)

ttk.Label(frame, text="Densidad polvo [kg/m³]").pack(anchor="w")
entry_densidad = ttk.Entry(frame)
entry_densidad.pack(fill="x", pady=5)

ttk.Label(frame, text="Superficie puertas [m²]").pack(anchor="w")
entry_superficie_puertas = ttk.Entry(frame)
entry_superficie_puertas.pack(fill="x", pady=10)

# Botón
ttk.Button(frame, text="CALCULAR", command=calcular).pack(fill="x", pady=15)

ttk.Separator(frame).pack(fill="x", pady=10)

# Resultados
ttk.Label(frame, text="RESULTADOS", font=("Arial", 13, "bold")).pack(anchor="w")

label_superficie_manga = ttk.Label(frame, text="Superficie manga: -")
label_superficie_manga.pack(anchor="w", pady=2)

label_masa_manga = ttk.Label(frame, text="Masa polvo por manga: -")
label_masa_manga.pack(anchor="w", pady=2)

label_masa_total = ttk.Label(frame, text="Masa total polvo en mangas: -")
label_masa_total.pack(anchor="w", pady=2)

label_operario = ttk.Label(frame, text="Carga operario mantenimiento: -")
label_operario.pack(anchor="w", pady=5)

ventana.mainloop()