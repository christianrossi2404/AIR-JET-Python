import math
import re
import tkinter as tk
from tkinter import messagebox, ttk

# ============================================================
# CONSTANTES
# ============================================================

T_N = 273.15  # Temperatura normal [K]
P_N_MMCAA = (
    10332.3129  # Presión normal en mm.c.a. (1 atm = 10,3323129 m.c.a. = 760 mmHg)
)

# ============================================================
# FUNCIONES AUXILIARES
# ============================================================


def leer_numero(entrada):
    """Acepta coma o punto decimal, sin separadores de miles.

    Rechaza formatos ambiguos como 1.234 o 1,234. Para expresar ese decimal se
    puede escribir 1.2340 o 1,2340; para miles, 1234.
    """
    texto = entrada.get().strip()
    if not texto:
        raise ValueError("Todos los campos deben contener un valor.")

    if not re.fullmatch(r"[+-]?(?:[0-9]+(?:[.,][0-9]+)?|[.,][0-9]+)", texto):
        raise ValueError(
            f"Valor no válido: {texto!r}.\n"
            "Use coma o punto decimal y no utilice separadores de miles.\n"
            "Ejemplos: 15806; 0,1; 0.1."
        )

    if re.fullmatch(r"[+-]?[1-9][0-9]{0,2}[.,][0-9]{3}", texto):
        sin_separador = texto.replace(".", "").replace(",", "")
        raise ValueError(
            f"El valor {texto!r} es ambiguo.\n"
            f"Si representa miles, escriba {sin_separador}.\n"
            f"Si representa un decimal, escriba {texto}0."
        )

    numero = float(texto.replace(",", "."))
    if not math.isfinite(numero):
        raise ValueError(
            "El valor debe ser un número finito dentro del rango permitido."
        )
    return numero


def formato_espanol(numero, decimales=2):
    """Formatea números usando:

    "." como separador de miles "," como separador decimal
    """
    if numero == 0:
        return "0," + "0" * decimales

    if abs(numero) < 1:
        orden = math.floor(math.log10(abs(numero)))
        decimales_necesarios = max(0, 3 - orden - 1)
        texto = f"{numero:.{decimales_necesarios}f}"
    else:
        texto = f"{numero:,.{decimales}f}"

    texto = texto.replace(",", "TEMP")
    texto = texto.replace(".", ",")
    texto = texto.replace("TEMP", ".")

    return texto


# ============================================================
# CÁLCULO DE DENSIDAD DEL GAS Y PRESIÓN ABSOLUTA
# ============================================================


def calcular_parametros_gas(temperatura_C, altitud, presion_proceso):
    """Calcula la presión barométrica, la presión absoluta total y la densidad

    del gas en condiciones de proceso (Am³).
    """
    # Presión atmosférica según la altitud (mm.c.a.)
    presion_barometrica_mmca = P_N_MMCAA * math.exp(-altitud / 7997.5)

    # Presión absoluta en la tubería/proceso (mm.c.a.)
    presion_abs_total_mmca = presion_barometrica_mmca + presion_proceso

    if presion_abs_total_mmca <= 0:
        raise ValueError(
            "La presión absoluta resultante del proceso es menor o igual a"
            " cero."
        )

    # Cálculo de la densidad en condiciones de proceso
    densidad_gas = (
        (P_N_MMCAA / (29.27 * (T_N + temperatura_C)))
        * math.exp(-altitud / 7997.5)
        * (presion_abs_total_mmca / presion_barometrica_mmca)
    )

    return densidad_gas, presion_abs_total_mmca


# ============================================================
# FUNCIÓN PRINCIPAL DE CÁLCULO
# ============================================================


def calcular():
    try:
        # DATOS DE ENTRADA
        concentracion_N = leer_numero(entrada_concentracion)
        caudal_N = leer_numero(entrada_caudal)
        densidad_producto = leer_numero(entrada_densidad_producto)
        altitud = leer_numero(entrada_altitud)
        temperatura_C = leer_numero(entrada_temperatura)
        presion_proceso = leer_numero(entrada_presion)

        # VALIDACIONES DE RANGO
        if concentracion_N < 0:
            raise ValueError("La concentración no puede ser negativa.")
        if caudal_N <= 0:
            raise ValueError("El caudal debe ser mayor que cero.")
        if densidad_producto <= 0:
            raise ValueError(
                "La densidad del producto debe ser mayor que cero."
            )
        if temperatura_C <= -273.15:
            raise ValueError("La temperatura debe ser superior a -273,15 °C.")

        # PROCESAMIENTO FÍSICO
        densidad_gas, presion_abs_total_mmca = calcular_parametros_gas(
            temperatura_C, altitud, presion_proceso
        )

        temperatura_K = temperatura_C + T_N

        # Factor de corrección de volumen (V_actual / V_normal)
        # Factor = (T_actual / T_normal) * (P_normal / P_absoluta_actual)
        factor = (temperatura_K / T_N) * (P_N_MMCAA / presion_abs_total_mmca)

        # CAUDAL Y CONCENTRACIÓN ACTUALES
        caudal_actual = caudal_N * factor
        concentracion_actual = concentracion_N / factor

        # CAUDAL MÁSICO Y PRODUCCIÓN VOLUMÉTRICA
        caudal_masico_kg_h = (concentracion_N * caudal_N) / 1000.0
        produccion_volumetrica = caudal_masico_kg_h / densidad_producto

        # ACTUALIZACIÓN DE LA INTERFAZ CON RESULTADOS
        resultado_densidad_gas.config(
            text=f"{formato_espanol(densidad_gas, 4)} kg/Am³"
        )
        resultado_factor.config(text=formato_espanol(factor, 5))
        resultado_caudal_actual.config(
            text=f"{formato_espanol(caudal_actual, 2)} Am³/h"
        )
        resultado_concentracion_actual.config(
            text=f"{formato_espanol(concentracion_actual, 4)} g/Am³"
        )
        resultado_masico.config(
            text=f"{formato_espanol(caudal_masico_kg_h, 3)} kg/h"
        )
        resultado_produccion_volumetrica.config(
            text=f"{formato_espanol(produccion_volumetrica, 3)} m³/h"
        )

    except ValueError as error:
        messagebox.showerror("Error en los datos", str(error))
    except Exception as error:
        messagebox.showerror("Error", f"Se ha producido un error:\n{error}")


# ============================================================
# LIMPIAR DATOS
# ============================================================


def limpiar():
    entrada_concentracion.delete(0, tk.END)
    entrada_caudal.delete(0, tk.END)
    entrada_densidad_producto.delete(0, tk.END)
    entrada_altitud.delete(0, tk.END)
    entrada_temperatura.delete(0, tk.END)
    entrada_presion.delete(0, tk.END)

    resultado_densidad_gas.config(text="--")
    resultado_factor.config(text="--")
    resultado_caudal_actual.config(text="--")
    resultado_concentracion_actual.config(text="--")
    resultado_masico.config(text="--")
    resultado_produccion_volumetrica.config(text="--")

    entrada_concentracion.focus()


# ============================================================
# INTERFAZ GRÁFICA CON SCROLL
# ============================================================

ventana = tk.Tk()
ventana.title("Conversión de caudal y concentración")
ventana.geometry("780x700")
ventana.minsize(650, 500)

# Contenedor principal con Scrollbar para pantallas pequeñas
canvas = tk.Canvas(ventana, borderwidth=0, highlightthickness=0)
scrollbar = ttk.Scrollbar(ventana, orient="vertical", command=canvas.yview)
scrollable_frame = ttk.Frame(canvas)

scrollable_frame.bind(
    "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
)

canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
canvas.configure(yscrollcommand=scrollbar.set)

canvas.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

# Soporte para rueda del ratón
def _on_mousewheel(event):
    canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

canvas.bind_all("<MouseWheel>", _on_mousewheel)

# ============================================================
# SECCIÓN TÍTULOS
# ============================================================

titulo = ttk.Label(
    scrollable_frame,
    text="Conversión de condiciones normales a actuales",
    font=("Arial", 16, "bold"),
)
titulo.pack(pady=(15, 5), padx=20)

subtitulo = ttk.Label(
    scrollable_frame,
    text=(
        "Cálculo de densidad, caudal, concentración y producción\n"
        "Entrada: coma o punto decimal, sin separadores de miles (15806; 0,1;"
        " 0.1)."
    ),
    font=("Arial", 10),
    justify="center",
)
subtitulo.pack(pady=(0, 15), padx=20)

# ============================================================
# FRAME DATOS DE ENTRADA
# ============================================================

frame_datos = ttk.LabelFrame(
    scrollable_frame, text="Datos de entrada", padding=15
)
frame_datos.pack(padx=20, fill="x", expand=True)

# Entrada Concentración
ttk.Label(frame_datos, text="Concentración:").grid(
    row=0, column=0, sticky="w", pady=6
)
entrada_concentracion = ttk.Entry(frame_datos, width=20)
entrada_concentracion.grid(row=0, column=1, padx=10)
ttk.Label(frame_datos, text="g/Nm³").grid(row=0, column=2, sticky="w")

# Entrada Caudal
ttk.Label(frame_datos, text="Caudal:").grid(row=1, column=0, sticky="w", pady=6)
entrada_caudal = ttk.Entry(frame_datos, width=20)
entrada_caudal.grid(row=1, column=1, padx=10)
ttk.Label(frame_datos, text="Nm³/h").grid(row=1, column=2, sticky="w")

# Entrada Densidad del producto
ttk.Label(frame_datos, text="Densidad del producto:").grid(
    row=2, column=0, sticky="w", pady=6
)
entrada_densidad_producto = ttk.Entry(frame_datos, width=20)
entrada_densidad_producto.grid(row=2, column=1, padx=10)
ttk.Label(frame_datos, text="kg/m³").grid(row=2, column=2, sticky="w")

# Entrada Altitud
ttk.Label(frame_datos, text="Altitud:").grid(row=3, column=0, sticky="w", pady=6)
entrada_altitud = ttk.Entry(frame_datos, width=20)
entrada_altitud.grid(row=3, column=1, padx=10)
ttk.Label(frame_datos, text="m").grid(row=3, column=2, sticky="w")

# Entrada Temperatura de proceso
ttk.Label(frame_datos, text="Temperatura de proceso:").grid(
    row=4, column=0, sticky="w", pady=6
)
entrada_temperatura = ttk.Entry(frame_datos, width=20)
entrada_temperatura.grid(row=4, column=1, padx=10)
ttk.Label(frame_datos, text="°C").grid(row=4, column=2, sticky="w")

# Entrada Presión de proceso
ttk.Label(frame_datos, text="Presión de proceso:").grid(
    row=5, column=0, sticky="w", pady=6
)
entrada_presion = ttk.Entry(frame_datos, width=20)
entrada_presion.grid(row=5, column=1, padx=10)
ttk.Label(frame_datos, text="mm.c.a. (+ / -)").grid(
    row=5, column=2, sticky="w"
)

# ============================================================
# BOTONES DE ACCIÓN
# ============================================================

frame_botones = ttk.Frame(scrollable_frame)
frame_botones.pack(pady=15)

boton_calcular = ttk.Button(frame_botones, text="CALCULAR", command=calcular)
boton_calcular.grid(row=0, column=0, padx=10)

boton_limpiar = ttk.Button(frame_botones, text="LIMPIAR", command=limpiar)
boton_limpiar.grid(row=0, column=1, padx=10)

# ============================================================
# FRAME RESULTADOS
# ============================================================

frame_resultados = ttk.LabelFrame(
    scrollable_frame, text="Resultados", padding=15
)
frame_resultados.pack(padx=20, fill="x", expand=True)


def crear_resultado(fila, descripcion):
    ttk.Label(frame_resultados, text=descripcion).grid(
        row=fila, column=0, sticky="w", pady=5
    )
    etiqueta = ttk.Label(frame_resultados, text="--", font=("Arial", 10, "bold"))
    etiqueta.grid(row=fila, column=1, sticky="w", padx=20)
    return etiqueta


resultado_densidad_gas = crear_resultado(0, "Densidad del gas:")
resultado_factor = crear_resultado(1, "Factor de conversión:")
resultado_caudal_actual = crear_resultado(2, "Caudal actual:")
resultado_concentracion_actual = crear_resultado(3, "Concentración actual:")
resultado_masico = crear_resultado(4, "Caudal másico del producto:")
resultado_produccion_volumetrica = crear_resultado(5, "Producción volumétrica:")

# ============================================================
# NOTA INFORMATIVA
# ============================================================

nota = ttk.Label(
    scrollable_frame,
    text=(
        "Densidad del gas calculada a partir de temperatura, altitud y presión"
        " de proceso en mm.c.a.\nProducción volumétrica = caudal másico /"
        " densidad del producto."
    ),
    justify="center",
    font=("Arial", 9),
)
nota.pack(pady=15, padx=20)

# ============================================================
# CONFIGURACIÓN FINAL
# ============================================================

ventana.bind("<Return>", lambda event: calcular())
entrada_concentracion.focus()

ventana.mainloop()