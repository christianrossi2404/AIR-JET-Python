import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import math
import openpyxl
from openpyxl.styles import Font
from tkinter import filedialog

def round_to_nearest_multiple(value, base=0.01):
    return math.ceil(value / base) * base

def solicitar_num_casos():
    try:
        num = simpledialog.askinteger("Número de casos", "¿Cuántos casos desea evaluar?", minvalue=1)
        if num is not None:
            generar_campos(num)
    except Exception as e:
        messagebox.showerror("Error", f"Ocurrió un error: {e}")

def generar_campos(num_casos):
    for widget in frame_campos.winfo_children():
        widget.destroy()
    campos.clear()

    # Encabezados (Sin velocidad aquí)
    ttk.Label(frame_campos, text="Caso", font=("Arial", 10, "bold")).grid(row=0, column=0)
    ttk.Label(frame_campos, text="Caudal (m³/h)").grid(row=0, column=1)
    ttk.Label(frame_campos, text="Longitud (m)").grid(row=0, column=2)

    for i in range(num_casos):
        ttk.Label(frame_campos, text=f"{i+1}").grid(row=i+1, column=0)
        caudal = ttk.Entry(frame_campos, width=15)
        longitud = ttk.Entry(frame_campos, width=15)

        caudal.grid(row=i+1, column=1, padx=5, pady=2)
        longitud.grid(row=i+1, column=2, padx=5, pady=2)

        campos.append((caudal, longitud)) # Ahora solo guardamos estos dos

def limpiar_campos():
    for caudal_entry, longitud_entry in campos:
        caudal_entry.delete(0, tk.END)
        longitud_entry.delete(0, tk.END)
    
    entry_velocidad.delete(0, tk.END)
    entry_velocidad.insert(0, "15")
    entry_espesor.delete(0, tk.END)
    entry_espesor.insert(0, "3")
    material_combo.current(0)

    for item in tree.get_children():
        tree.delete(item)

def calcular_todos():
    for row in tree.get_children():
        tree.delete(row)

    try:
        espesor = float(entry_espesor.get()) / 1000
        velocidad_global = float(entry_velocidad.get()) # Velocidad tomada de la cabecera
        if espesor <= 0 or velocidad_global <= 0:
            raise ValueError("Espesor y Velocidad deben ser positivos.")
    except ValueError:
        messagebox.showerror("Error", "Verifique que Espesor y Velocidad sean valores numéricos.")
        return

    material = material_var.get()
    densidad = 8000

    suma_masa = 0
    suma_masa_20 = 0
    suma_longitud = 0

    for i, (caudal_entry, longitud_entry) in enumerate(campos, start=1):
        try:
            caudal = float(caudal_entry.get())
            longitud = float(longitud_entry.get())

            if caudal <= 0 or longitud <= 0:
                raise ValueError("Caudal y Longitud deben ser positivos.")

            caudal_seg = caudal / 3600
            seccion_tuberia = caudal_seg / velocidad_global
            diametro_real = math.sqrt(seccion_tuberia / math.pi) * 2
            diametro_ajustado = round_to_nearest_multiple(diametro_real)
            circunferencia = diametro_ajustado * math.pi
            volumen = circunferencia * espesor * longitud
            masa = volumen * densidad
            masa_20 = masa * 1.20

            suma_masa += masa
            suma_masa_20 += masa_20
            suma_longitud += longitud

            tree.insert("", "end", values=(
                f"{caudal:.2f}",
                f"{diametro_ajustado:.3f}",
                f"{diametro_real:.4f}",
                f"{longitud:.2f}",
                f"{masa:.2f}",
                f"{masa_20:.2f}",
                material
            ))

        except ValueError as ve:
            messagebox.showerror("Error", f"Error en el caso {i}: {ve}")

    tree.insert("", "end", values=(
        "TOTAL", "", "", f"{suma_longitud:.2f}",
        f"{suma_masa:.2f}", f"{suma_masa_20:.2f}", ""
    ), tags=("total",))
    tree.tag_configure("total", font=("Arial", 10, "bold"))

def exportar_a_excel():
    if not tree.get_children():
        messagebox.showwarning("Sin datos", "No hay resultados para exportar.")
        return

    carpeta_destino = filedialog.askdirectory(title="Selecciona carpeta de destino")
    if not carpeta_destino:
        return 

    ruta_completa = f"{carpeta_destino}/resultados_tuberias.xlsx"

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Resultados Tuberías"

    encabezados = (
        "Caudal (m³/h)", "Ø Ajustado (m)", "Ø Real (m)",
        "Longitud (m)", "Masa (kg)", "Masa +20% (kg)", "Material"
    )
    ws.append(encabezados)

    for col in range(1, len(encabezados) + 1):
        ws.cell(row=1, column=col).font = Font(bold=True)

    for item in tree.get_children():
        valores = tree.item(item)["values"]
        fila = []
        for i, valor in enumerate(valores):
            if i == 6 or valor == "TOTAL":
                fila.append(valor)
            else:
                try:
                    fila.append(float(valor))
                except:
                    fila.append(valor)
        ws.append(fila)

    try:
        wb.save(ruta_completa)
        messagebox.showinfo("Éxito", f"Archivo exportado como:\n{ruta_completa}")
    except Exception as e:
        messagebox.showerror("Error al guardar", f"No se pudo guardar el archivo:\n{e}")

# --- Interfaz ---
ventana = tk.Tk()
ventana.title("Evaluador Múltiple de Tuberías")
ventana.geometry("1050x650")

campos = []

frame_superior = ttk.Frame(ventana)
frame_superior.pack(pady=10)

# Fila de configuración global
ttk.Label(frame_superior, text="Material:").grid(row=0, column=0, padx=5)
material_var = tk.StringVar()
material_combo = ttk.Combobox(frame_superior, textvariable=material_var, state="readonly")
material_combo['values'] = ("S2355JR", "AISI304", "AISI316")
material_combo.current(0)
material_combo.grid(row=0, column=1, padx=5)

ttk.Label(frame_superior, text="Espesor (mm):").grid(row=0, column=2, padx=5)
entry_espesor = ttk.Entry(frame_superior, width=10)
entry_espesor.grid(row=0, column=3, padx=5)
entry_espesor.insert(0, "3")

ttk.Label(frame_superior, text="Velocidad (m/s):").grid(row=0, column=4, padx=5)
entry_velocidad = ttk.Entry(frame_superior, width=10)
entry_velocidad.grid(row=0, column=5, padx=5)
entry_velocidad.insert(0, "15")

ttk.Button(ventana, text="Ingresar número de casos", command=solicitar_num_casos).pack(pady=10)
frame_campos = ttk.Frame(ventana)
frame_campos.pack(padx=10, pady=5, fill="x")

ttk.Button(ventana, text="Calcular todos", command=calcular_todos).pack(pady=10)
ttk.Button(ventana, text="Exportar a Excel", command=exportar_a_excel).pack(pady=5)
ttk.Button(ventana, text="Limpiar entradas", command=limpiar_campos).pack(pady=5)

columnas = (
    "Caudal (m³/h)", "Ø Ajustado (m)", "Ø Real (m)",
    "Longitud (m)", "Masa (kg)", "Masa +20% (kg)", "Material"
)
tree = ttk.Treeview(ventana, columns=columnas, show="headings", height=12)
for col in columnas:
    tree.heading(col, text=col)
    tree.column(col, width=120, anchor="center")
tree.pack(padx=10, pady=10, fill="both", expand=True)

ventana.mainloop()