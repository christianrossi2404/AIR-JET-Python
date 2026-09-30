import tkinter as tk
from tkinter import ttk, messagebox


# Superficie filtrante aproximada por manga según su longitud
SUPERFICIES_MANGAS = {
    "4 ft": 0.49,
    "6 ft": 0.75,
    "8 ft": 1.00,
    "10 ft": 1.25,
    "12 ft": 1.50,
    "14 ft": 1.80,
}


def leer_float(entry, nombre_campo, minimo=0.0, permitir_cero=True):
    """
    Lee y valida un número decimal desde un Entry.
    Admite coma o punto como separador decimal.
    """
    texto = entry.get().strip().replace(",", ".")

    if not texto:
        raise ValueError(f"El campo «{nombre_campo}» está vacío.")

    try:
        valor = float(texto)
    except ValueError:
        raise ValueError(
            f"El campo «{nombre_campo}» debe contener un número válido."
        )

    if permitir_cero:
        if valor < minimo:
            raise ValueError(
                f"El campo «{nombre_campo}» debe ser igual o mayor que {minimo}."
            )
    else:
        if valor <= minimo:
            raise ValueError(
                f"El campo «{nombre_campo}» debe ser mayor que {minimo}."
            )

    return valor


def leer_entero(entry, nombre_campo, minimo=0):
    """
    Lee y valida un número entero desde un Entry.
    """
    texto = entry.get().strip()

    if not texto:
        raise ValueError(f"El campo «{nombre_campo}» está vacío.")

    try:
        valor = int(texto)
    except ValueError:
        raise ValueError(
            f"El campo «{nombre_campo}» debe contener un número entero."
        )

    if valor <= minimo:
        raise ValueError(
            f"El campo «{nombre_campo}» debe ser mayor que {minimo}."
        )

    return valor


def calcular():
    try:
        numero_mangas = leer_entero(
            entry_numero_mangas,
            "Número de mangas"
        )

        longitud = combo_longitud.get()

        if longitud not in SUPERFICIES_MANGAS:
            raise ValueError("Selecciona una longitud de manga válida.")

        espesor_mm = leer_float(
            entry_espesor,
            "Espesor de polvo",
            minimo=0.0
        )

        densidad_kg_m3 = leer_float(
            entry_densidad,
            "Densidad del producto",
            minimo=0.0,
            permitir_cero=False
        )

        superficie_puertas_m2 = leer_float(
            entry_superficie_puertas,
            "Superficie de puertas",
            minimo=0.0
        )

        peso_filtro_kg = leer_float(
            entry_peso_filtro,
            "Peso del filtro y accesorios",
            minimo=0.0
        )

        volumen_tolva_m3 = leer_float(
            entry_volumen_tolva,
            "Volumen de la tolva",
            minimo=0.0
        )

        numero_patas = leer_entero(
            entry_numero_patas,
            "Número de patas"
        )

        superficie_manga_m2 = SUPERFICIES_MANGAS[longitud]

        # Conversión de milímetros a metros
        espesor_m = espesor_mm / 1000.0

        # Masa de polvo depositada en una manga
        masa_polvo_por_manga_kg = (
            superficie_manga_m2
            * espesor_m
            * densidad_kg_m3
        )

        # Masa total de polvo depositada en todas las mangas
        masa_total_mangas_kg = (
            masa_polvo_por_manga_kg
            * numero_mangas
        )

        # Carga estimada del operario de mantenimiento
        carga_operario_kg = 150.0 * superficie_puertas_m2

        # Masa de producto contenida en la tolva llena
        carga_tolva_kg = volumen_tolva_m3 * densidad_kg_m3

        # Carga total soportada por la estructura
        carga_total_filtro_kg = (
            peso_filtro_kg
            + masa_total_mangas_kg
            + carga_operario_kg
            + carga_tolva_kg
        )

        # Carga distribuida por pata
        carga_por_pata_kg = carga_total_filtro_kg / numero_patas

        # Conversión aproximada de masa equivalente a fuerza
        carga_total_kn = carga_total_filtro_kg * 9.80665 / 1000.0
        carga_por_pata_kn = carga_por_pata_kg * 9.80665 / 1000.0

        label_superficie_manga.config(
            text=f"{superficie_manga_m2:.2f} m²"
        )

        label_masa_manga.config(
            text=f"{masa_polvo_por_manga_kg:.3f} kg"
        )

        label_masa_total.config(
            text=f"{masa_total_mangas_kg:.3f} kg"
        )

        label_operario.config(
            text=f"{carga_operario_kg:.2f} kg"
        )

        label_peso_filtro.config(
            text=f"{peso_filtro_kg:.2f} kg"
        )

        label_carga_tolva.config(
            text=f"{carga_tolva_kg:.2f} kg"
        )

        label_carga_total.config(
            text=(
                f"{carga_total_filtro_kg:.2f} kg "
                f"≈ {carga_total_kn:.2f} kN"
            )
        )

        label_carga_pata.config(
            text=(
                f"{carga_por_pata_kg:.2f} kg/pata "
                f"≈ {carga_por_pata_kn:.2f} kN/pata"
            )
        )

        label_estado.config(
            text="Cálculo realizado correctamente."
        )

    except ValueError as error:
        label_estado.config(text="")
        messagebox.showerror("Datos incorrectos", str(error))


def limpiar():
    """
    Limpia todos los campos y reinicia los resultados.
    """
    for entry in entradas:
        entry.delete(0, tk.END)

    combo_longitud.current(0)

    label_superficie_manga.config(text="-")
    label_masa_manga.config(text="-")
    label_masa_total.config(text="-")
    label_operario.config(text="-")
    label_peso_filtro.config(text="-")
    label_carga_tolva.config(text="-")
    label_carga_total.config(text="-")
    label_carga_pata.config(text="-")
    label_estado.config(text="")

    entry_numero_mangas.focus_set()


def crear_campo(parent, texto, fila):
    """
    Crea una etiqueta y un Entry dentro de una cuadrícula.
    """
    ttk.Label(
        parent,
        text=texto
    ).grid(
        row=fila,
        column=0,
        sticky="w",
        padx=(0, 15),
        pady=6
    )

    entry = ttk.Entry(parent)

    entry.grid(
        row=fila,
        column=1,
        sticky="ew",
        pady=6
    )

    return entry


def crear_resultado(parent, texto, fila, destacado=False):
    """
    Crea una fila para mostrar un resultado.
    """
    fuente = (
        "Arial",
        11 if destacado else 10,
        "bold" if destacado else "normal"
    )

    ttk.Label(
        parent,
        text=texto,
        font=fuente
    ).grid(
        row=fila,
        column=0,
        sticky="w",
        padx=(0, 15),
        pady=5
    )

    label_valor = ttk.Label(
        parent,
        text="-",
        font=fuente
    )

    label_valor.grid(
        row=fila,
        column=1,
        sticky="e",
        pady=5
    )

    return label_valor


# -------------------------------------------------------------------
# Ventana principal
# -------------------------------------------------------------------

ventana = tk.Tk()
ventana.title("Cálculo de operación del filtro")
ventana.geometry("680x760")
ventana.minsize(620, 700)

ventana.columnconfigure(0, weight=1)
ventana.rowconfigure(0, weight=1)

estilo = ttk.Style()

try:
    estilo.theme_use("clam")
except tk.TclError:
    pass

estilo.configure(
    "Titulo.TLabel",
    font=("Arial", 18, "bold")
)

estilo.configure(
    "Seccion.TLabel",
    font=("Arial", 12, "bold")
)

estilo.configure(
    "Calcular.TButton",
    font=("Arial", 11, "bold")
)

contenedor = ttk.Frame(
    ventana,
    padding=20
)

contenedor.grid(
    row=0,
    column=0,
    sticky="nsew"
)

contenedor.columnconfigure(0, weight=1)

ttk.Label(
    contenedor,
    text="Cálculo de operación del filtro",
    style="Titulo.TLabel"
).grid(
    row=0,
    column=0,
    sticky="w",
    pady=(0, 15)
)

ttk.Label(
    contenedor,
    text=(
        "Introduce los datos del filtro para calcular la masa total "
        "y la carga distribuida por pata."
    ),
    wraplength=620
).grid(
    row=1,
    column=0,
    sticky="w",
    pady=(0, 15)
)

# -------------------------------------------------------------------
# Datos de entrada
# -------------------------------------------------------------------

frame_entradas = ttk.LabelFrame(
    contenedor,
    text="Datos de entrada",
    padding=15
)

frame_entradas.grid(
    row=2,
    column=0,
    sticky="ew"
)

frame_entradas.columnconfigure(1, weight=1)

entry_numero_mangas = crear_campo(
    frame_entradas,
    "Número de mangas",
    0
)

ttk.Label(
    frame_entradas,
    text="Longitud de las mangas"
).grid(
    row=1,
    column=0,
    sticky="w",
    padx=(0, 15),
    pady=6
)

combo_longitud = ttk.Combobox(
    frame_entradas,
    values=list(SUPERFICIES_MANGAS.keys()),
    state="readonly"
)

combo_longitud.grid(
    row=1,
    column=1,
    sticky="ew",
    pady=6
)

combo_longitud.current(0)

entry_espesor = crear_campo(
    frame_entradas,
    "Espesor de polvo [mm]",
    2
)

entry_densidad = crear_campo(
    frame_entradas,
    "Densidad del producto [kg/m³]",
    3
)

entry_superficie_puertas = crear_campo(
    frame_entradas,
    "Superficie de puertas [m²]",
    4
)

entry_peso_filtro = crear_campo(
    frame_entradas,
    "Peso del filtro y accesorios [kg]",
    5
)

entry_volumen_tolva = crear_campo(
    frame_entradas,
    "Volumen de la tolva [m³]",
    6
)

entry_numero_patas = crear_campo(
    frame_entradas,
    "Número de patas de la estructura",
    7
)

entradas = [
    entry_numero_mangas,
    entry_espesor,
    entry_densidad,
    entry_superficie_puertas,
    entry_peso_filtro,
    entry_volumen_tolva,
    entry_numero_patas,
]

# -------------------------------------------------------------------
# Botones
# -------------------------------------------------------------------

frame_botones = ttk.Frame(contenedor)

frame_botones.grid(
    row=3,
    column=0,
    sticky="ew",
    pady=15
)

frame_botones.columnconfigure(0, weight=1)
frame_botones.columnconfigure(1, weight=1)

ttk.Button(
    frame_botones,
    text="CALCULAR",
    command=calcular,
    style="Calcular.TButton"
).grid(
    row=0,
    column=0,
    sticky="ew",
    padx=(0, 5)
)

ttk.Button(
    frame_botones,
    text="LIMPIAR",
    command=limpiar
).grid(
    row=0,
    column=1,
    sticky="ew",
    padx=(5, 0)
)

# -------------------------------------------------------------------
# Resultados
# -------------------------------------------------------------------

frame_resultados = ttk.LabelFrame(
    contenedor,
    text="Resultados",
    padding=15
)

frame_resultados.grid(
    row=4,
    column=0,
    sticky="ew"
)

frame_resultados.columnconfigure(1, weight=1)

label_superficie_manga = crear_resultado(
    frame_resultados,
    "Superficie por manga",
    0
)

label_masa_manga = crear_resultado(
    frame_resultados,
    "Masa de polvo por manga",
    1
)

label_masa_total = crear_resultado(
    frame_resultados,
    "Masa total de polvo en mangas",
    2
)

label_operario = crear_resultado(
    frame_resultados,
    "Carga de mantenimiento",
    3
)

label_peso_filtro = crear_resultado(
    frame_resultados,
    "Peso del filtro y accesorios",
    4
)

label_carga_tolva = crear_resultado(
    frame_resultados,
    "Carga de la tolva llena",
    5
)

ttk.Separator(
    frame_resultados,
    orient="horizontal"
).grid(
    row=6,
    column=0,
    columnspan=2,
    sticky="ew",
    pady=10
)

label_carga_total = crear_resultado(
    frame_resultados,
    "Carga total del filtro",
    7,
    destacado=True
)

label_carga_pata = crear_resultado(
    frame_resultados,
    "Carga por pata",
    8,
    destacado=True
)

label_estado = ttk.Label(
    contenedor,
    text="",
    font=("Arial", 10, "italic")
)

label_estado.grid(
    row=5,
    column=0,
    sticky="w",
    pady=(10, 0)
)

ttk.Label(
    contenedor,
    text=(
        "Nota: los valores en kN representan la fuerza equivalente "
        "calculada con g = 9,80665 m/s². No incluyen coeficientes "
        "de seguridad ni combinaciones de carga."
    ),
    wraplength=620,
    font=("Arial", 9, "italic")
).grid(
    row=6,
    column=0,
    sticky="w",
    pady=(10, 0)
)

# Permite ejecutar el cálculo pulsando Enter
ventana.bind("<Return>", lambda event: calcular())

entry_numero_mangas.focus_set()

ventana.mainloop()