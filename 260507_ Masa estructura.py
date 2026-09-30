import tkinter as tk
from tkinter import ttk, messagebox, filedialog

import pandas as pd


PESOS_PERFILES = {
    "IPE 80": 6.0,
    "IPE 100": 8.1,
    "IPE 120": 10.4,
    "IPE 140": 12.9,
    "IPE 160": 15.8,
    "IPE 180": 18.8,
    "IPE 200": 22.4,
    "IPE 220": 26.2,
    "IPE 240": 30.7,
    "IPE 270": 36.1,
    "IPE 300": 42.2,
    "IPE 330": 49.1,
    "IPE 360": 57.1,
    "IPE 400": 66.3,
    "IPE 450": 77.6,
    "IPE 500": 90.7,
    "IPE 550": 106.0,
    "IPE 600": 122.0,

    "HEA 100": 16.7,
    "HEA 120": 19.9,
    "HEA 140": 24.7,
    "HEA 160": 30.4,
    "HEA 180": 35.5,
    "HEA 200": 42.3,
    "HEA 220": 50.5,
    "HEA 240": 60.3,
    "HEA 260": 68.2,
    "HEA 280": 76.4,
    "HEA 300": 88.3,
    "HEA 320": 97.6,
    "HEA 340": 105.0,
    "HEA 360": 112.0,
    "HEA 400": 125.0,
    "HEA 450": 140.0,
    "HEA 500": 155.0,
    "HEA 550": 166.0,
    "HEA 600": 178.0,

    "HEB 100": 20.4,
    "HEB 120": 26.7,
    "HEB 140": 33.7,
    "HEB 160": 42.6,
    "HEB 180": 51.2,
    "HEB 200": 61.3,
    "HEB 220": 71.5,
    "HEB 240": 83.2,
    "HEB 260": 93.0,
    "HEB 280": 103.0,
    "HEB 300": 117.0,
    "HEB 320": 127.0,
    "HEB 340": 134.0,
    "HEB 360": 142.0,
    "HEB 400": 155.0,
    "HEB 450": 171.0,
    "HEB 500": 187.0,
    "HEB 550": 199.0,
    "HEB 600": 212.0,

    "UPN 80": 8.6,
    "UPN 100": 10.6,
    "UPN 120": 13.4,
    "UPN 140": 16.0,
    "UPN 160": 18.8,
    "UPN 180": 22.0,
    "UPN 200": 25.3,
    "UPN 220": 29.4,
    "UPN 240": 33.2,
    "UPN 260": 37.9,
    "UPN 280": 41.8,
    "UPN 300": 46.2,

    "Tubo cuadrado 40x40x2": 2.4,
    "Tubo cuadrado 50x50x2": 3.0,
    "Tubo cuadrado 60x60x2": 3.6,
    "Tubo cuadrado 80x80x3": 7.1,
    "Tubo cuadrado 100x100x3": 8.9,
    "Tubo cuadrado 120x120x4": 14.2,
    "Tubo cuadrado 140x140x5": 20.8,
    "Tubo cuadrado 160x160x5": 24.0,
    "Tubo cuadrado 200x200x6": 35.9,

    "Tubo rectangular 60x40x2": 3.0,
    "Tubo rectangular 80x40x2": 3.6,
    "Tubo rectangular 100x50x3": 6.9,
    "Tubo rectangular 120x60x3": 8.3,
    "Tubo rectangular 140x80x4": 13.2,
    "Tubo rectangular 160x80x4": 14.5,
    "Tubo rectangular 200x100x5": 22.6,

    "Tubo redondo Ø33.7x2": 1.6,
    "Tubo redondo Ø42.4x2": 2.1,
    "Tubo redondo Ø48.3x2.5": 2.9,
    "Tubo redondo Ø60.3x2.5": 3.7,
    "Tubo redondo Ø76.1x3": 5.4,
    "Tubo redondo Ø88.9x3": 6.4,
    "Tubo redondo Ø114.3x4": 10.9,
    "Tubo redondo Ø139.7x5": 16.6,
    "Tubo redondo Ø168.3x5": 20.1,

    "L 30x30x3": 1.3,
    "L 40x40x4": 2.4,
    "L 50x50x5": 3.8,
    "L 60x60x6": 5.4,
    "L 80x80x8": 8.6,
    "L 100x100x10": 15.0,

    "Pletina 40x5": 1.6,
    "Pletina 50x5": 2.0,
    "Pletina 60x6": 2.8,
    "Pletina 80x8": 5.0,
    "Pletina 100x10": 7.9,
    "Pletina 150x12": 14.1,

    "Redondo Ø10": 0.62,
    "Redondo Ø12": 0.89,
    "Redondo Ø16": 1.58,
    "Redondo Ø20": 2.47,
    "Redondo Ø25": 3.85,
    "Redondo Ø32": 6.31,
    "Redondo Ø40": 9.87,
}


def actualizar_total():
    total = 0.0

    for item in tabla.get_children():
        valores = tabla.item(item, "values")
        total += float(valores[4])

    label_total.config(text=f"Masa total estructura: {total:.2f} kg")


def agregar_perfil():
    try:
        perfil = combo_perfil.get()
        metros = float(entry_metros.get().replace(",", "."))
        unidades = int(entry_unidades.get())

        if perfil not in PESOS_PERFILES:
            messagebox.showerror("Error", "Selecciona un perfil válido.")
            return

        if metros <= 0 or unidades <= 0:
            messagebox.showerror("Error", "Los metros y las unidades deben ser mayores que cero.")
            return

        kg_m = PESOS_PERFILES[perfil]
        masa_total = kg_m * metros * unidades

        tabla.insert(
            "",
            "end",
            values=(
                perfil,
                f"{kg_m:.2f}",
                f"{metros:.2f}",
                unidades,
                f"{masa_total:.2f}"
            )
        )

        actualizar_total()

    except ValueError:
        messagebox.showerror("Error", "Introduce metros y unidades válidos.")


def eliminar_seleccionado():
    seleccionado = tabla.selection()

    if not seleccionado:
        messagebox.showwarning("Aviso", "Selecciona una línea para eliminar.")
        return

    for item in seleccionado:
        tabla.delete(item)

    actualizar_total()


def limpiar_todo():
    for item in tabla.get_children():
        tabla.delete(item)

    actualizar_total()


def exportar_excel():
    if not tabla.get_children():
        messagebox.showwarning("Aviso", "No hay datos para exportar.")
        return

    datos = []
    total_general = 0.0

    for item in tabla.get_children():
        valores = tabla.item(item, "values")

        perfil = valores[0]
        kg_m = float(valores[1])
        metros = float(valores[2])
        unidades = int(valores[3])
        masa = float(valores[4])

        total_general += masa

        datos.append({
            "Perfil": perfil,
            
            
            
            "kg/m": kg_m,
            "Metros por unidad": metros,
            "Unidades": unidades,
            "Masa total (kg)": masa,
        })

    datos.append({
        "Perfil": "",
        "kg/m": "",
        "Metros por unidad": "",
        "Unidades": "TOTAL",
        "Masa total (kg)": round(total_general, 2),
    })

    archivo = filedialog.asksaveasfilename(
        defaultextension=".xlsx",
        filetypes=[("Archivo Excel", "*.xlsx")],
        title="Guardar resultados en Excel"
    )

    if not archivo:
        return

    try:
        with pd.ExcelWriter(archivo, engine="openpyxl") as writer:
            df = pd.DataFrame(datos)
            df.to_excel(writer, index=False, sheet_name="Perfiles")

            hoja = writer.sheets["Perfiles"]

            for columna in hoja.columns:
                ancho = max(len(str(celda.value)) if celda.value is not None else 0 for celda in columna)
                hoja.column_dimensions[columna[0].column_letter].width = ancho + 4

        messagebox.showinfo("Éxito", "Excel exportado correctamente.")

    except Exception as e:
        messagebox.showerror("Error", f"No se pudo exportar el Excel:\n{e}")


ventana = tk.Tk()
ventana.title("Calculadora de masa de perfiles estructurales")
ventana.geometry("850x540")
ventana.resizable(False, False)

titulo = tk.Label(
    ventana,
    text="Calculadora de masa de perfiles estructurales",
    font=("Arial", 16, "bold")
)
titulo.pack(pady=12)

frame_entrada = tk.Frame(ventana)
frame_entrada.pack(pady=8)

tk.Label(frame_entrada, text="Tipo de perfil:").grid(row=0, column=0, padx=6, pady=5)

combo_perfil = ttk.Combobox(
    frame_entrada,
    values=list(PESOS_PERFILES.keys()),
    state="readonly",
    width=35
)
combo_perfil.grid(row=0, column=1, padx=6, pady=5)
combo_perfil.current(0)

tk.Label(frame_entrada, text="Metros/unidad:").grid(row=0, column=2, padx=6, pady=5)

entry_metros = tk.Entry(frame_entrada, width=12)
entry_metros.grid(row=0, column=3, padx=6, pady=5)
entry_metros.insert(0, "6")

tk.Label(frame_entrada, text="Unidades:").grid(row=0, column=4, padx=6, pady=5)

entry_unidades = tk.Entry(frame_entrada, width=12)
entry_unidades.grid(row=0, column=5, padx=6, pady=5)
entry_unidades.insert(0, "1")

boton_agregar = tk.Button(
    ventana,
    text="Añadir perfil",
    command=agregar_perfil,
    width=22,
    height=2
)
boton_agregar.pack(pady=8)

columnas = ("perfil", "kg_m", "metros", "unidades", "masa")

tabla = ttk.Treeview(
    ventana,
    columns=columnas,
    show="headings",
    height=12
)

tabla.heading("perfil", text="Perfil")
tabla.heading("kg_m", text="kg/m")
tabla.heading("metros", text="Metros/unidad")
tabla.heading("unidades", text="Unidades")
tabla.heading("masa", text="Masa total kg")

tabla.column("perfil", width=260)
tabla.column("kg_m", width=90, anchor="center")
tabla.column("metros", width=130, anchor="center")
tabla.column("unidades", width=100, anchor="center")
tabla.column("masa", width=140, anchor="center")

tabla.pack(pady=10)

frame_botones = tk.Frame(ventana)
frame_botones.pack(pady=8)

tk.Button(
    frame_botones,
    text="Eliminar seleccionado",
    command=eliminar_seleccionado,
    width=20
).grid(row=0, column=0, padx=8)

tk.Button(
    frame_botones,
    text="Limpiar todo",
    command=limpiar_todo,
    width=20
).grid(row=0, column=1, padx=8)

tk.Button(
    frame_botones,
    text="Exportar Excel",
    command=exportar_excel,
    width=20,
    bg="lightgreen"
).grid(row=0, column=2, padx=8)

label_total = tk.Label(
    ventana,
    text="Masa total estructura: 0.00 kg",
    font=("Arial", 15, "bold"),
    fg="blue"
)
label_total.pack(pady=12)

ventana.mainloop()