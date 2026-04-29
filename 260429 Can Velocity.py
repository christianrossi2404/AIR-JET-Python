import math
import tkinter as tk
from tkinter import messagebox

# Parámetros fijos
DIAMETRO_MANGA_MM = 130
ENTREPUERTA_M = 0.042  # 42 mm


def calcular():
    try:
        largo = float(entry_largo.get())
        ancho = float(entry_ancho.get())
        numero_mangas = int(entry_mangas.get())
        caudal_m3h = float(entry_caudal.get())
        numero_entrepuertas = int(entry_entrepuertas.get())

        # Ajuste de largo
        largo_efectivo = largo + (numero_entrepuertas * ENTREPUERTA_M)

        # Área del compartimento
        area_compartimento = largo_efectivo * ancho

        # Conversión caudal
        caudal_m3s = caudal_m3h / 3600

        # Área mangas
        diametro_m = DIAMETRO_MANGA_MM / 1000
        area_una_manga = math.pi * (diametro_m ** 2) / 4
        area_total_mangas = area_una_manga * numero_mangas

        # Área libre
        area_libre = area_compartimento - area_total_mangas

        if area_libre <= 0:
            messagebox.showerror("Error", "El área libre es ≤ 0. Revisa datos.")
            return

        # Can velocity
        can_velocity = caudal_m3s / area_libre

        resultado.set(
            f"Largo efectivo: {largo_efectivo:.2f} m\n"
            f"Área filtro: {area_compartimento:.2f} m²\n"
            f"Área una manga: {area_una_manga:.4f} m²\n"
            f"Área libre: {area_libre:.2f} m²\n"
            f"Can velocity: {can_velocity:.2f} m/s"
        )

        # Evaluación
        if can_velocity < 1.0:
            estado.set("OK")
        elif can_velocity < 1.5:
            estado.set("Algo alta")
        else:
            estado.set("Alta ⚠")

    except ValueError:
        messagebox.showerror("Error", "Introduce valores numéricos válidos.")


# Ventana
ventana = tk.Tk()
ventana.title("Can Velocity - Filtro de Mangas")
ventana.geometry("400x360")

tk.Label(ventana, text="Cálculo Can Velocity", font=("Arial", 14, "bold")).pack(pady=10)

frame = tk.Frame(ventana)
frame.pack(pady=10)

# Inputs
tk.Label(frame, text="Largo filtro (m):").grid(row=0, column=0, sticky="e", padx=5, pady=5)
entry_largo = tk.Entry(frame)
entry_largo.grid(row=0, column=1)

tk.Label(frame, text="Ancho filtro (m):").grid(row=1, column=0, sticky="e", padx=5, pady=5)
entry_ancho = tk.Entry(frame)
entry_ancho.grid(row=1, column=1)

tk.Label(frame, text="Número de mangas:").grid(row=2, column=0, sticky="e", padx=5, pady=5)
entry_mangas = tk.Entry(frame)
entry_mangas.grid(row=2, column=1)

tk.Label(frame, text="Caudal (m³/h):").grid(row=3, column=0, sticky="e", padx=5, pady=5)
entry_caudal = tk.Entry(frame)
entry_caudal.grid(row=3, column=1)

tk.Label(frame, text="Nº entrepuertas (42 mm):").grid(row=4, column=0, sticky="e", padx=5, pady=5)
entry_entrepuertas = tk.Entry(frame)
entry_entrepuertas.grid(row=4, column=1)

# Botón
tk.Button(ventana, text="Calcular", command=calcular, width=15).pack(pady=10)

# Resultados
resultado = tk.StringVar()
estado = tk.StringVar()

tk.Label(ventana, textvariable=resultado, font=("Arial", 11)).pack(pady=5)
tk.Label(ventana, textvariable=estado, font=("Arial", 12, "bold")).pack(pady=5)

ventana.mainloop()