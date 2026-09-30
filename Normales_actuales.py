import tkinter as tk
from tkinter import ttk, messagebox
import math


# ============================================================
# CONSTANTES
# ============================================================

T_N = 273.15  # Temperatura normal [K]


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def leer_numero(entrada):
    """
    Lee números escritos en formato español.

    Ejemplos aceptados:
        1250
        1250,5
        1.250,5
        -25,5

    El punto se interpreta como separador de miles
    y la coma como separador decimal.
    """

    texto = entrada.get().strip()

    if texto == "":
        raise ValueError("Todos los campos deben contener un valor.")

    # Eliminar separador de miles
    texto = texto.replace(".", "")

    # Convertir coma decimal a punto para Python
    texto = texto.replace(",", ".")

    return float(texto)


def formato_espanol(numero, decimales=2):
    """
    Formatea números usando:
        "." como separador de miles
        "," como separador decimal

    Para números cuyo valor absoluto es menor que 1,
    muestra 3 cifras significativas.

    Ejemplos:
        1234.56      -> 1.234,56
        0.123456     -> 0,123
        0.0123456    -> 0,0123
        0.00123456   -> 0,00123
        -0.00123456  -> -0,00123
    """

    if numero == 0:
        return "0,000"

    # --------------------------------------------------------
    # VALORES MENORES QUE 1
    # 3 cifras significativas
    # --------------------------------------------------------

    if abs(numero) < 1:

        orden = math.floor(
            math.log10(abs(numero))
        )

        decimales_necesarios = max(
            0,
            3 - orden - 1
        )

        texto = f"{numero:.{decimales_necesarios}f}"

    # --------------------------------------------------------
    # VALORES >= 1
    # --------------------------------------------------------

    else:

        texto = f"{numero:,.{decimales}f}"

    # --------------------------------------------------------
    # CONVERTIR FORMATO INGLÉS A ESPAÑOL
    #
    # 12,345.67 --> 12.345,67
    # --------------------------------------------------------

    texto = texto.replace(",", "TEMP")
    texto = texto.replace(".", ",")
    texto = texto.replace("TEMP", ".")

    return texto


# ============================================================
# CÁLCULO DE DENSIDAD DEL GAS
# ============================================================

def calcular_densidad_gas(
    temperatura_C,
    altitud,
    presion_proceso
):
    """
    Fórmula utilizada:

    =(10332,3129/(29,27*(273,15+Temperatura)))
    *(EXP((53050/7997,5)-(altitud/7997,5))/760)
    *((10332,3129+(presión de proceso*10))/10332,3129)

    La presión de proceso puede ser positiva o negativa.
    """

    densidad_gas = (
        (
            10332.3129
            /
            (
                29.27
                *
                (273.15 + temperatura_C)
            )
        )
        *
        (
            math.exp(
                (53050 / 7997.5)
                -
                (altitud / 7997.5)
            )
            /
            760
        )
        *
        (
            (
                10332.3129
                +
                (presion_proceso * 10)
            )
            /
            10332.3129
        )
    )

    return densidad_gas


# ============================================================
# FUNCIÓN PRINCIPAL DE CÁLCULO
# ============================================================

def calcular():

    try:

        # ====================================================
        # DATOS DE ENTRADA
        # ====================================================

        concentracion_N = leer_numero(
            entrada_concentracion
        )

        caudal_N = leer_numero(
            entrada_caudal
        )

        densidad_producto = leer_numero(
            entrada_densidad_producto
        )

        altitud = leer_numero(
            entrada_altitud
        )

        temperatura_C = leer_numero(
            entrada_temperatura
        )

        presion_proceso = leer_numero(
            entrada_presion
        )


        # ====================================================
        # VALIDACIONES
        # ====================================================

        if concentracion_N < 0:

            raise ValueError(
                "La concentración no puede ser negativa."
            )

        if caudal_N <= 0:

            raise ValueError(
                "El caudal debe ser mayor que cero."
            )

        if densidad_producto <= 0:

            raise ValueError(
                "La densidad del producto debe ser mayor que cero."
            )

        if temperatura_C <= -273.15:

            raise ValueError(
                "La temperatura debe ser superior a -273,15 °C."
            )


        # ====================================================
        # PRESIÓN ABSOLUTA SEGÚN LA FÓRMULA
        # ====================================================

        presion_abs_formula = (
            10332.3129
            +
            presion_proceso * 10
        )

        if presion_abs_formula <= 0:

            raise ValueError(
                "La presión de proceso introducida genera "
                "una presión absoluta igual o inferior a cero."
            )


        # ====================================================
        # DENSIDAD DEL GAS
        # ====================================================

        densidad_gas = calcular_densidad_gas(
            temperatura_C,
            altitud,
            presion_proceso
        )

        if densidad_gas <= 0:

            raise ValueError(
                "La combinación de temperatura, altitud y presión "
                "produce una densidad del gas igual o inferior a cero."
            )


        # ====================================================
        # TEMPERATURA ABSOLUTA
        # ====================================================

        temperatura_K = (
            temperatura_C + 273.15
        )


        # ====================================================
        # FACTOR DE TEMPERATURA
        # ====================================================

        factor_temperatura = (
            temperatura_K / T_N
        )


        # ====================================================
        # FACTOR DE ALTITUD
        # ====================================================

        factor_altitud = math.exp(
            altitud / 7997.5
        )


        # ====================================================
        # FACTOR DE PRESIÓN
        # ====================================================

        factor_presion = (
            10332.3129
            /
            presion_abs_formula
        )


        # ====================================================
        # FACTOR TOTAL
        # ====================================================

        factor = (
            factor_temperatura
            *
            factor_altitud
            *
            factor_presion
        )


        # ====================================================
        # CAUDAL EN CONDICIONES ACTUALES
        # ====================================================

        caudal_actual = (
            caudal_N
            *
            factor
        )


        # ====================================================
        # CONCENTRACIÓN EN CONDICIONES ACTUALES
        # ====================================================

        concentracion_actual = (
            concentracion_N
            /
            factor
        )


        # ====================================================
        # CAUDAL MÁSICO DEL PRODUCTO
        #
        # g/Nm³ × Nm³/h = g/h
        #
        # después:
        #
        # g/h / 1000 = kg/h
        # ====================================================

        caudal_masico_g_h = (
            concentracion_N
            *
            caudal_N
        )

        caudal_masico_kg_h = (
            caudal_masico_g_h
            /
            1000
        )


        # ====================================================
        # PRODUCCIÓN VOLUMÉTRICA
        #
        # kg/h
        # -------- = m³/h
        # kg/m³
        # ====================================================

        produccion_volumetrica = (
            caudal_masico_kg_h
            /
            densidad_producto
        )


        # ====================================================
        # MOSTRAR RESULTADOS
        # ====================================================

        resultado_densidad_gas.config(
            text=(
                f"{formato_espanol(densidad_gas, 4)} "
                f"kg/m³"
            )
        )

        resultado_factor.config(
            text=formato_espanol(
                factor,
                5
            )
        )

        resultado_caudal_actual.config(
            text=(
                f"{formato_espanol(caudal_actual, 2)} "
                f"m³/h"
            )
        )

        resultado_concentracion_actual.config(
            text=(
                f"{formato_espanol(concentracion_actual, 4)} "
                f"g/m³"
            )
        )

        resultado_masico.config(
            text=(
                f"{formato_espanol(caudal_masico_kg_h, 3)} "
                f"kg/h"
            )
        )

        resultado_produccion_volumetrica.config(
            text=(
                f"{formato_espanol(produccion_volumetrica, 3)} "
                f"m³/h"
            )
        )


    except ValueError as error:

        messagebox.showerror(
            "Error en los datos",
            str(error)
        )

    except Exception as error:

        messagebox.showerror(
            "Error",
            f"Se ha producido un error:\n{error}"
        )


# ============================================================
# LIMPIAR DATOS
# ============================================================

def limpiar():

    entrada_concentracion.delete(
        0,
        tk.END
    )

    entrada_caudal.delete(
        0,
        tk.END
    )

    entrada_densidad_producto.delete(
        0,
        tk.END
    )

    entrada_altitud.delete(
        0,
        tk.END
    )

    entrada_temperatura.delete(
        0,
        tk.END
    )

    entrada_presion.delete(
        0,
        tk.END
    )

    resultado_densidad_gas.config(
        text="--"
    )

    resultado_factor.config(
        text="--"
    )

    resultado_caudal_actual.config(
        text="--"
    )

    resultado_concentracion_actual.config(
        text="--"
    )

    resultado_masico.config(
        text="--"
    )

    resultado_produccion_volumetrica.config(
        text="--"
    )

    entrada_concentracion.focus()


# ============================================================
# VENTANA PRINCIPAL
# ============================================================

ventana = tk.Tk()

ventana.title(
    "Conversión de caudal y concentración"
)

ventana.geometry(
    "720x680"
)

ventana.resizable(
    False,
    False
)


# ============================================================
# TÍTULO
# ============================================================

titulo = ttk.Label(
    ventana,
    text="Conversión de condiciones normales a actuales",
    font=(
        "Arial",
        16,
        "bold"
    )
)

titulo.pack(
    pady=(15, 5)
)


subtitulo = ttk.Label(
    ventana,
    text=(
        "Cálculo de densidad, caudal, "
        "concentración y producción"
    ),
    font=(
        "Arial",
        10
    )
)

subtitulo.pack(
    pady=(0, 15)
)


# ============================================================
# FRAME DATOS DE ENTRADA
# ============================================================

frame_datos = ttk.LabelFrame(
    ventana,
    text="Datos de entrada",
    padding=15
)

frame_datos.pack(
    padx=20,
    fill="x"
)


# ============================================================
# CONCENTRACIÓN
# ============================================================

ttk.Label(
    frame_datos,
    text="Concentración:"
).grid(
    row=0,
    column=0,
    sticky="w",
    pady=6
)

entrada_concentracion = ttk.Entry(
    frame_datos,
    width=20
)

entrada_concentracion.grid(
    row=0,
    column=1,
    padx=10
)

ttk.Label(
    frame_datos,
    text="g/Nm³"
).grid(
    row=0,
    column=2,
    sticky="w"
)


# ============================================================
# CAUDAL
# ============================================================

ttk.Label(
    frame_datos,
    text="Caudal:"
).grid(
    row=1,
    column=0,
    sticky="w",
    pady=6
)

entrada_caudal = ttk.Entry(
    frame_datos,
    width=20
)

entrada_caudal.grid(
    row=1,
    column=1,
    padx=10
)

ttk.Label(
    frame_datos,
    text="Nm³/h"
).grid(
    row=1,
    column=2,
    sticky="w"
)


# ============================================================
# DENSIDAD DEL PRODUCTO
# ============================================================

ttk.Label(
    frame_datos,
    text="Densidad del producto:"
).grid(
    row=2,
    column=0,
    sticky="w",
    pady=6
)

entrada_densidad_producto = ttk.Entry(
    frame_datos,
    width=20
)

entrada_densidad_producto.grid(
    row=2,
    column=1,
    padx=10
)

ttk.Label(
    frame_datos,
    text="kg/m³"
).grid(
    row=2,
    column=2,
    sticky="w"
)


# ============================================================
# ALTITUD
# ============================================================

ttk.Label(
    frame_datos,
    text="Altitud:"
).grid(
    row=3,
    column=0,
    sticky="w",
    pady=6
)

entrada_altitud = ttk.Entry(
    frame_datos,
    width=20
)

entrada_altitud.grid(
    row=3,
    column=1,
    padx=10
)

ttk.Label(
    frame_datos,
    text="m"
).grid(
    row=3,
    column=2,
    sticky="w"
)


# ============================================================
# TEMPERATURA DE PROCESO
# ============================================================

ttk.Label(
    frame_datos,
    text="Temperatura de proceso:"
).grid(
    row=4,
    column=0,
    sticky="w",
    pady=6
)

entrada_temperatura = ttk.Entry(
    frame_datos,
    width=20
)

entrada_temperatura.grid(
    row=4,
    column=1,
    padx=10
)

ttk.Label(
    frame_datos,
    text="°C"
).grid(
    row=4,
    column=2,
    sticky="w"
)


# ============================================================
# PRESIÓN DE PROCESO
# ============================================================

ttk.Label(
    frame_datos,
    text="Presión de proceso:"
).grid(
    row=5,
    column=0,
    sticky="w",
    pady=6
)

entrada_presion = ttk.Entry(
    frame_datos,
    width=20
)

entrada_presion.grid(
    row=5,
    column=1,
    padx=10
)

ttk.Label(
    frame_datos,
    text="puede ser + / -"
).grid(
    row=5,
    column=2,
    sticky="w"
)


# ============================================================
# BOTONES
# ============================================================

frame_botones = ttk.Frame(
    ventana
)

frame_botones.pack(
    pady=15
)


boton_calcular = ttk.Button(
    frame_botones,
    text="CALCULAR",
    command=calcular
)

boton_calcular.grid(
    row=0,
    column=0,
    padx=10
)


boton_limpiar = ttk.Button(
    frame_botones,
    text="LIMPIAR",
    command=limpiar
)

boton_limpiar.grid(
    row=0,
    column=1,
    padx=10
)


# ============================================================
# FRAME RESULTADOS
# ============================================================

frame_resultados = ttk.LabelFrame(
    ventana,
    text="Resultados",
    padding=15
)

frame_resultados.pack(
    padx=20,
    fill="x"
)


# ============================================================
# FUNCIÓN AUXILIAR RESULTADOS
# ============================================================

def crear_resultado(
    fila,
    descripcion
):

    ttk.Label(
        frame_resultados,
        text=descripcion
    ).grid(
        row=fila,
        column=0,
        sticky="w",
        pady=5
    )

    etiqueta = ttk.Label(
        frame_resultados,
        text="--",
        font=(
            "Arial",
            10,
            "bold"
        )
    )

    etiqueta.grid(
        row=fila,
        column=1,
        sticky="w",
        padx=20
    )

    return etiqueta


# ============================================================
# RESULTADOS
# ============================================================

resultado_densidad_gas = crear_resultado(
    0,
    "Densidad del gas:"
)

resultado_factor = crear_resultado(
    1,
    "Factor de conversión:"
)

resultado_caudal_actual = crear_resultado(
    2,
    "Caudal actual:"
)

resultado_concentracion_actual = crear_resultado(
    3,
    "Concentración actual:"
)

resultado_masico = crear_resultado(
    4,
    "Caudal másico del producto:"
)

resultado_produccion_volumetrica = crear_resultado(
    5,
    "Producción volumétrica:"
)


# ============================================================
# NOTA INFORMATIVA
# ============================================================

nota = ttk.Label(
    ventana,
    text=(
        "Densidad del gas calculada a partir de temperatura, "
        "altitud y presión de proceso.\n"
        "Producción volumétrica = caudal másico / "
        "densidad del producto."
    ),
    justify="center",
    font=(
        "Arial",
        9
    )
)

nota.pack(
    pady=15
)


# ============================================================
# PULSAR ENTER = CALCULAR
# ============================================================

ventana.bind(
    "<Return>",
    lambda event: calcular()
)


entrada_concentracion.focus()


# ============================================================
# INICIAR PROGRAMA
# ============================================================

ventana.mainloop()