import math
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import docx
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.shared import Inches, Pt, RGBColor

RATIO_MINIMO = 2.5
RATIO_MAXIMO = 3.0


def calcular_resultados(datos):
    """Devuelve los resultados geométricos del silo y del consumo de reactivo."""
    diametro = datos["diametro"]
    altura_cilindro = datos["altura_cilindro"]
    angulo_cono = datos["angulo_cono"]
    consumo_hora = datos["consumo_hora"]
    densidad = datos["densidad"]
    semanas = datos["semanas_funcionamiento"]
    volumen_cisterna = datos["volumen_cisterna"]
    factor_efectivo = datos["aprovechamiento"] / 100.0

    radio = diametro / 2.0
    ratio = altura_cilindro / diametro

    # Altura del cono basada en el ángulo respecto a la horizontal
    angulo_rad = math.radians(angulo_cono)
    altura_cono = radio * math.tan(angulo_rad)

    volumen_cilindro = math.pi * (radio**2) * altura_cilindro
    volumen_cono = (math.pi * (radio**2) * altura_cono) / 3.0
    volumen_total = volumen_cilindro + volumen_cono
    volumen_efectivo = volumen_total * factor_efectivo

    # Consumo total en el período indicado
    horas_totales = 24 * 7 * semanas
    consumo_kg_periodo = consumo_hora * horas_totales
    consumo_m3_periodo = consumo_kg_periodo / densidad

    # Consumo semanal base (168 h) para el cálculo de autonomías
    consumo_m3_semana = (consumo_hora * 24 * 7) / densidad

    autonomia_silo = volumen_efectivo / consumo_m3_semana
    autonomia_cisterna = volumen_cisterna / consumo_m3_semana

    # Reserva disponible cuando cabe una cisterna completa en el silo
    semanas_reserva = autonomia_silo - autonomia_cisterna

    return {
        "ratio": ratio,
        "altura_cono": altura_cono,
        "volumen_total": volumen_total,
        "volumen_efectivo": volumen_efectivo,
        "consumo_kg_semana": consumo_kg_periodo,
        "consumo_m3_semana": consumo_m3_periodo,
        "autonomia_silo": autonomia_silo,
        "autonomia_cisterna": autonomia_cisterna,
        "semanas_reserva": semanas_reserva,
    }


# --- FUNCIONES AUXILIARES DE FORMATO DOCX ---
def _set_cell_background(cell, fill_hex):
    """Aplica sombreado de color de fondo a una celda de tabla."""
    tcPr = cell._element.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)


def _set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    """Establece los márgenes internos de una celda."""
    tcPr = cell._element.get_or_add_tcPr()
    tcMar = OxmlElement("w:tcMar")
    for m, val in [
        ("top", top),
        ("bottom", bottom),
        ("left", left),
        ("right", right),
    ]:
        node = OxmlElement(f"w:{m}")
        node.set(qn("w:w"), str(val))
        node.set(qn("w:type"), "dxa")
        tcMar.append(node)
    tcPr.append(tcMar)


def generar_documento_word(datos, resultados, ruta_guardado):
    """Genera el reporte técnico en Word con formato ejecutivo y conclusiones personalizadas."""
    doc = docx.Document()

    # Configuración de márgenes estándar (1 pulgada / 2,54 cm)
    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)

    # Estilo Normal
    normal_style = doc.styles["Normal"]
    normal_style.font.name = "Calibri"
    normal_style.font.size = Pt(11)
    normal_style.font.color.rgb = RGBColor(51, 51, 51)

    # Título principal
    title = doc.add_paragraph()
    run_title = title.add_run(
        "INFORME TÉCNICO DE DIMENSIONAMIENTO DE SILO Y REACTIVO"
    )
    run_title.font.name = "Arial"
    run_title.font.size = Pt(18)
    run_title.font.bold = True
    run_title.font.color.rgb = RGBColor(31, 78, 121)  # Azul primario
    title.paragraph_format.space_after = Pt(2)

    subtitle = doc.add_paragraph()
    run_sub = subtitle.add_run(
        "Memoria de cálculo, consideraciones técnicas e indicadores de autonomía"
    )
    run_sub.font.name = "Arial"
    run_sub.font.size = Pt(12)
    run_sub.font.italic = True
    run_sub.font.color.rgb = RGBColor(89, 89, 89)
    subtitle.paragraph_format.space_after = Pt(14)

    # Línea divisoria decorativa
    p_line = doc.add_paragraph()
    p_line.paragraph_format.space_after = Pt(16)
    p_line_border = parse_xml(
        f'<w:pBdr {nsdecls("w")}><w:bottom w:val="single" w:sz="12" w:space="1" w:color="1F4E79"/></w:pBdr>'
    )
    p_line._element.get_or_add_pPr().append(p_line_border)

    def _seccion(texto):
        h = doc.add_paragraph()
        h.paragraph_format.space_before = Pt(14)
        h.paragraph_format.space_after = Pt(6)
        h.paragraph_format.keep_with_next = True
        run = h.add_run(texto)
        run.font.name = "Arial"
        run.font.size = Pt(13)
        run.font.bold = True
        run.font.color.rgb = RGBColor(31, 78, 121)
        return h

    # 1. Introducción
    _seccion("1. Introducción y Objetivos")
    p1 = doc.add_paragraph(
        "El presente documento recoge la memoria de cálculo y verificación operativa para el silo "
        "de almacenamiento de reactivo. El objetivo es determinar la capacidad útil disponible, "
        "comprobar los márgenes de seguridad para la recepción de camiones cisterna y calcular la "
        "autonomía operativa bajo el régimen de consumo indicado."
    )
    p1.paragraph_format.space_after = Pt(10)
    p1.paragraph_format.line_spacing = 1.15

    # 2. Datos de Entrada
    _seccion("2. Datos de Entrada y Parámetros del Proceso")

    input_data_rows = [
        (
            "Diámetro del silo (D)",
            f"{datos['diametro']:.2f}".replace(".", ","),
            "m",
        ),
        (
            "Altura de la virola cilíndrica (H_cil)",
            f"{datos['altura_cilindro']:.2f}".replace(".", ","),
            "m",
        ),
        (
            "Ángulo de inclinación del cono (α)",
            f"{datos['angulo_cono']:.1f}".replace(".", ","),
            "°",
        ),
        (
            "Aprovechamiento efectivo volumétrico",
            f"{datos['aprovechamiento']:.1f}".replace(".", ","),
            "%",
        ),
        (
            "Consumo horario de reactivo",
            f"{datos['consumo_hora']:.2f}".replace(".", ","),
            "kg/h",
        ),
        (
            "Densidad aparente del reactivo",
            f"{datos['densidad']:.1f}".replace(".", ","),
            "kg/m³",
        ),
        (
            "Período de cálculo considerado",
            f"{datos['semanas_funcionamiento']:.1f}".replace(".", ","),
            "semanas",
        ),
        (
            "Volumen de carga por cisterna",
            f"{datos['volumen_cisterna']:.2f}".replace(".", ","),
            "m³",
        ),
    ]

    widths = [Inches(3.4), Inches(1.8), Inches(1.0)]
    tbl_input = doc.add_table(rows=len(input_data_rows) + 1, cols=3)
    tbl_input.alignment = WD_TABLE_ALIGNMENT.CENTER

    hdr = tbl_input.rows[0]
    for i, title_text in enumerate(["Parámetro / Variable", "Valor", "Unidad"]):
        cell = hdr.cells[i]
        cell.width = widths[i]
        _set_cell_background(cell, "1F4E79")
        _set_cell_margins(cell, top=100, bottom=100, left=120, right=120)
        p = cell.paragraphs[0]
        p.alignment = (
            WD_ALIGN_PARAGRAPH.LEFT if i == 0 else WD_ALIGN_PARAGRAPH.RIGHT
        )
        r = p.add_run(title_text)
        r.font.name = "Arial"
        r.font.bold = True
        r.font.size = Pt(10)
        r.font.color.rgb = RGBColor(255, 255, 255)

    for row_idx, data_tuple in enumerate(input_data_rows, start=1):
        row = tbl_input.rows[row_idx]
        bg_color = "F8F9FA" if row_idx % 2 == 1 else "FFFFFF"
        for col_idx, val in enumerate(data_tuple):
            cell = row.cells[col_idx]
            cell.width = widths[col_idx]
            _set_cell_background(cell, bg_color)
            _set_cell_margins(cell, top=70, bottom=70, left=120, right=120)
            p = cell.paragraphs[0]
            p.alignment = (
                WD_ALIGN_PARAGRAPH.LEFT
                if col_idx == 0
                else WD_ALIGN_PARAGRAPH.RIGHT
            )
            r = p.add_run(val)
            r.font.size = Pt(10)

    doc.add_paragraph().paragraph_format.space_after = Pt(8)

    # 3. Fórmulas
    _seccion("3. Criterios de Diseño y Fórmulas Aplicadas")

    formulas = [
        (
            "Relación de Aspecto (Ratio):",
            "Ratio = H_cil / D  [Rango recomendado: 2.5 a 3.0]",
        ),
        ("Altura del Cono:", "H_cono = (D / 2) · tan(α)"),
        ("Volumen del Cilindro:", "V_cilindro = π · (D / 2)² · H_cil"),
        ("Volumen de la Tolva Cónica:", "V_cono = [π · (D / 2)² · H_cono] / 3"),
        ("Volumen Total Geométrico:", "V_total = V_cilindro + V_cono"),
        (
            "Volumen Efectivo Operativo:",
            "V_efectivo = V_total · (% Aprovechamiento / 100)",
        ),
        (
            "Consumo Volumétrico Semanal:",
            "Consumo_m³ = (Consumo_kg/h · 168 h) / Densidad",
        ),
        ("Autonomía Total del Silo:", "Autonomía = V_efectivo / Consumo_m³_sem"),
        (
            "Reserva de Seguridad post-cisterna:",
            "Reserva = Autonomía_silo - Autonomía_cisterna",
        ),
    ]

    for title_f, expr_f in formulas:
        p_f = doc.add_paragraph()
        p_f.paragraph_format.space_after = Pt(3)
        p_f.paragraph_format.left_indent = Inches(0.2)
        r_lbl = p_f.add_run(f"• {title_f} ")
        r_lbl.font.bold = True
        r_lbl.font.size = Pt(10)
        r_lbl.font.color.rgb = RGBColor(31, 78, 121)
        r_exp = p_f.add_run(expr_f)
        r_exp.font.size = Pt(10)
        r_exp.font.italic = True

    # 4. Resultados
    _seccion("4. Resultados Obtenidos")

    output_data_rows = [
        (
            "Ratio Altura / Diámetro (H_cil / D)",
            f"{resultados['ratio']:.3f}".replace(".", ","),
            "—",
        ),
        (
            "Altura calculada del cono (H_cono)",
            f"{resultados['altura_cono']:.2f}".replace(".", ","),
            "m",
        ),
        (
            "Volumen total geométrico",
            f"{resultados['volumen_total']:.3f}".replace(".", ","),
            "m³",
        ),
        (
            "Volumen efectivo útil",
            f"{resultados['volumen_efectivo']:.3f}".replace(".", ","),
            "m³",
        ),
        (
            "Consumo masivo en período",
            f"{resultados['consumo_kg_semana']:.2f}".replace(".", ","),
            "kg",
        ),
        (
            "Consumo volumétrico en período",
            f"{resultados['consumo_m3_semana']:.3f}".replace(".", ","),
            "m³",
        ),
        (
            "Autonomía total del silo (100% útil)",
            f"{resultados['autonomia_silo']:.2f}".replace(".", ","),
            "semanas",
        ),
        (
            "Autonomía provista por 1 cisterna",
            f"{resultados['autonomia_cisterna']:.2f}".replace(".", ","),
            "semanas",
        ),
        (
            "Autonomía de reserva disponible",
            f"{resultados['semanas_reserva']:.1f}".replace(".", ","),
            "semanas",
        ),
    ]

    tbl_out = doc.add_table(rows=len(output_data_rows) + 1, cols=3)
    tbl_out.alignment = WD_TABLE_ALIGNMENT.CENTER

    hdr_out = tbl_out.rows[0]
    for i, title_text in enumerate(
        ["Resultado / Indicador", "Valor Calculado", "Unidad"]
    ):
        cell = hdr_out.cells[i]
        cell.width = widths[i]
        _set_cell_background(cell, "2E75B6")
        _set_cell_margins(cell, top=100, bottom=100, left=120, right=120)
        p = cell.paragraphs[0]
        p.alignment = (
            WD_ALIGN_PARAGRAPH.LEFT if i == 0 else WD_ALIGN_PARAGRAPH.RIGHT
        )
        r = p.add_run(title_text)
        r.font.name = "Arial"
        r.font.bold = True
        r.font.size = Pt(10)
        r.font.color.rgb = RGBColor(255, 255, 255)

    for row_idx, data_tuple in enumerate(output_data_rows, start=1):
        row = tbl_out.rows[row_idx]
        bg_color = "F8F9FA" if row_idx % 2 == 1 else "FFFFFF"
        for col_idx, val in enumerate(data_tuple):
            cell = row.cells[col_idx]
            cell.width = widths[col_idx]
            _set_cell_background(cell, bg_color)
            _set_cell_margins(cell, top=70, bottom=70, left=120, right=120)
            p = cell.paragraphs[0]
            p.alignment = (
                WD_ALIGN_PARAGRAPH.LEFT
                if col_idx == 0
                else WD_ALIGN_PARAGRAPH.RIGHT
            )
            r = p.add_run(val)
            r.font.size = Pt(10)
            if row_idx in [4, 7, 9]:
                r.font.bold = True

    doc.add_paragraph().paragraph_format.space_after = Pt(8)

    # 5. Conclusiones Técnicas según el nuevo criterio
    _seccion("5. Conclusiones Técnicas")

    p_conc1 = doc.add_paragraph()
    p_conc1.paragraph_format.space_after = Pt(5)
    p_conc1.paragraph_format.line_spacing = 1.15
    r_c1 = p_conc1.add_run("• Recarga Silo: ")
    r_c1.font.bold = True
    p_conc1.add_run(
        f"El volumen útil calculado ({resultados['volumen_efectivo']:.2f} m³) "
        f"del silo es suficiente para suministrar los reactivos durante "
        f"{resultados['autonomia_silo']:.2f} semanas. Pasadas "
        f"{resultados['autonomia_cisterna']:.2f} semanas en operación continua, "
        f"el silo dispondrá de una autonomía de reserva disponible de "
        f"{resultados['semanas_reserva']:.1f} semanas y se podrá rellenar el silo "
        f"mediante camión cisterna con capacidad de {datos['volumen_cisterna']:.2f} m³ "
        f"cargado al 100% de reactivos."
    )

    p_conc2 = doc.add_paragraph()
    p_conc2.paragraph_format.space_after = Pt(14)
    p_conc2.paragraph_format.line_spacing = 1.15
    r_c2 = p_conc2.add_run("• Estrategia de Reaprovisionamiento: ")
    r_c2.font.bold = True
    p_conc2.add_run(
        f"La reserva operativa restante equivale a {resultados['semanas_reserva']:.1f} "
        f"semanas de funcionamiento. Se recomienda fijar el punto de pedido de camión "
        f"cuando el nivel del silo descienda a dicho umbral para garantizar continuidad."
    )

    # Pie
    p_foot = doc.add_paragraph()
    p_foot.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_foot.paragraph_format.space_before = Pt(16)
    r_ft = p_foot.add_run(
        "— Documento generado automáticamente por la Calculadora de Silos —"
    )
    r_ft.font.size = Pt(9)
    r_ft.font.italic = True
    r_ft.font.color.rgb = RGBColor(128, 128, 128)

    doc.save(ruta_guardado)


# --- CLASE PRINCIPAL DE INTERFAZ TKINTER ---
class CalculadoraSilo(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Calculadora de Silo y Reactivo · Con exportación Word")
        self.resizable(False, False)

        self.entradas = {}
        self.salidas = {}
        self.datos_calculados = None
        self.resultados_calculados = None

        self.estado = tk.StringVar(
            value="Introduce los datos y pulsa Calcular."
        )

        self._crear_interfaz()

    def _campo(self, marco, fila, etiqueta, clave, valor_inicial, unidad):
        ttk.Label(marco, text=etiqueta).grid(
            row=fila, column=0, sticky="w", padx=8, pady=5
        )

        variable = tk.StringVar(value=valor_inicial)
        self.entradas[clave] = variable

        ttk.Entry(marco, textvariable=variable, width=15).grid(
            row=fila, column=1, padx=8, pady=5
        )
        ttk.Label(marco, text=unidad).grid(
            row=fila, column=2, sticky="w", padx=(0, 8), pady=5
        )

    def _resultado(self, marco, fila, etiqueta, clave, unidad=""):
        ttk.Label(marco, text=etiqueta).grid(
            row=fila, column=0, sticky="w", padx=8, pady=4
        )

        variable = tk.StringVar(value="—")
        self.salidas[clave] = variable

        ttk.Label(
            marco,
            textvariable=variable,
            font=("TkDefaultFont", 10, "bold"),
        ).grid(row=fila, column=1, sticky="e", padx=8, pady=4)

        ttk.Label(marco, text=unidad).grid(
            row=fila, column=2, sticky="w", padx=(0, 8), pady=4
        )

    def _crear_interfaz(self):
        contenedor = ttk.Frame(self, padding=14)
        contenedor.grid(row=0, column=0)

        # Entradas
        marco_silo = ttk.LabelFrame(contenedor, text="INPUT · SILO", padding=8)
        marco_silo.grid(
            row=0, column=0, sticky="nsew", padx=(0, 8), pady=(0, 8)
        )

        self._campo(marco_silo, 0, "Diámetro del silo", "diametro", "3", "m")
        self._campo(
            marco_silo, 1, "Altura del cilindro", "altura_cilindro", "8", "m"
        )
        self._campo(
            marco_silo,
            2,
            "Ángulo del cono (horizontal)",
            "angulo_cono",
            "60",
            "°",
        )
        self._campo(
            marco_silo,
            3,
            "Aprovechamiento efectivo",
            "aprovechamiento",
            "85",
            "%",
        )

        marco_reactivo = ttk.LabelFrame(
            contenedor, text="INPUT · REACTIVO", padding=8
        )
        marco_reactivo.grid(row=0, column=1, sticky="nsew", pady=(0, 8))

        self._campo(
            marco_reactivo,
            0,
            "Consumo de reactivo",
            "consumo_hora",
            "15",
            "kg/h",
        )
        self._campo(marco_reactivo, 1, "Densidad", "densidad", "400", "kg/m³")
        self._campo(
            marco_reactivo,
            2,
            "Semanas de funcionamiento",
            "semanas_funcionamiento",
            "1",
            "semanas",
        )
        self._campo(
            marco_reactivo,
            3,
            "Volumen carga cisterna",
            "volumen_cisterna",
            "35",
            "m³",
        )

        # Marco de Botones
        marco_botones = ttk.Frame(contenedor)
        marco_botones.grid(row=1, column=0, columnspan=2, pady=(2, 10))

        ttk.Button(
            marco_botones, text="Calcular", command=self.calcular
        ).pack(side="left", padx=6, ipadx=16, ipady=3)

        self.btn_exportar = ttk.Button(
            marco_botones,
            text="Exportar Reporte (Word)",
            command=self.exportar_word,
            state="disabled",
        )
        self.btn_exportar.pack(side="left", padx=6, ipadx=16, ipady=3)

        # Salidas
        salida_silo = ttk.LabelFrame(
            contenedor, text="OUTPUT · SILO", padding=8
        )
        salida_silo.grid(
            row=2, column=0, sticky="nsew", padx=(0, 8), pady=(0, 8)
        )

        self._resultado(salida_silo, 0, "Ratio altura/diámetro", "ratio")
        self._resultado(
            salida_silo, 1, "Altura cono calculada", "altura_cono", "m"
        )
        self._resultado(salida_silo, 2, "Volumen total", "volumen_total", "m³")
        self._resultado(
            salida_silo, 3, "Volumen efectivo", "volumen_efectivo", "m³"
        )

        salida_reactivo = ttk.LabelFrame(
            contenedor, text="OUTPUT · REACTIVO", padding=8
        )
        salida_reactivo.grid(row=2, column=1, sticky="nsew", pady=(0, 8))

        self._resultado(
            salida_reactivo, 0, "Consumo período", "consumo_kg_semana", "kg"
        )
        self._resultado(
            salida_reactivo, 1, "Consumo período", "consumo_m3_semana", "m³"
        )

        salida_autonomia = ttk.LabelFrame(
            contenedor, text="OUTPUT · AUTONOMÍA TOTAL", padding=8
        )
        salida_autonomia.grid(row=3, column=0, columnspan=2, sticky="ew")

        self._resultado(
            salida_autonomia,
            0,
            "Autonomía total · volumen efectivo SILO",
            "autonomia_silo",
            "semanas",
        )
        self._resultado(
            salida_autonomia,
            1,
            "Autonomía total · CARGA CISTERNA",
            "autonomia_cisterna",
            "semanas",
        )
        self._resultado(
            salida_autonomia,
            2,
            "AUTONOMÍA DE RESERVA",
            "semanas_reserva",
            "semanas",
        )

        ttk.Label(
            contenedor, textvariable=self.estado, foreground="#555555"
        ).grid(row=4, column=0, columnspan=2, sticky="w", pady=(8, 0))

    @staticmethod
    def _convertir_numero(texto, nombre):
        try:
            return float(texto.strip().replace(",", "."))
        except ValueError as error:
            raise ValueError(
                f"{nombre} debe ser un número válido."
            ) from error

    def _leer_entradas(self):
        nombres = {
            "diametro": "El diámetro del silo",
            "altura_cilindro": "La altura del cilindro",
            "angulo_cono": "El ángulo del cono",
            "aprovechamiento": "El aprovechamiento efectivo",
            "consumo_hora": "El consumo de reactivo",
            "densidad": "La densidad",
            "semanas_funcionamiento": "Las semanas de funcionamiento",
            "volumen_cisterna": "El volumen de la carga cisterna",
        }

        return {
            clave: self._convertir_numero(variable.get(), nombres[clave])
            for clave, variable in self.entradas.items()
        }

    @staticmethod
    def _validar_entradas(datos):
        campos_positivos = (
            "diametro",
            "altura_cilindro",
            "consumo_hora",
            "densidad",
            "semanas_funcionamiento",
            "volumen_cisterna",
        )
        if any(datos[campo] <= 0 for campo in campos_positivos):
            raise ValueError(
                "Las dimensiones, el consumo, la densidad, las semanas y la "
                "carga de la cisterna deben ser mayores que cero."
            )

        if not 0 < datos["angulo_cono"] < 90:
            raise ValueError("El ángulo del cono debe estar entre 0° y 90°.")

        if not 0 < datos["aprovechamiento"] <= 100:
            raise ValueError(
                "El aprovechamiento efectivo debe estar entre 0 % y 100 %."
            )

        ratio = datos["altura_cilindro"] / datos["diametro"]
        if not RATIO_MINIMO <= ratio <= RATIO_MAXIMO:
            raise ValueError(
                f"El ratio altura/diámetro es {ratio:.3f}; debe estar "
                f"comprendido entre {RATIO_MINIMO:.1f} y {RATIO_MAXIMO:.1f}."
            )

    @staticmethod
    def _formatear(numero, decimales):
        return f"{numero:.{decimales}f}".replace(".", ",")

    def calcular(self):
        try:
            datos = self._leer_entradas()
            self._validar_entradas(datos)
            resultados = calcular_resultados(datos)

            if datos["volumen_cisterna"] > resultados["volumen_efectivo"]:
                raise ValueError(
                    "La carga de la cisterna no puede superar el volumen "
                    "efectivo del silo."
                )

            decimales = {
                "ratio": 3,
                "altura_cono": 2,
                "volumen_total": 3,
                "volumen_efectivo": 3,
                "consumo_kg_semana": 2,
                "consumo_m3_semana": 3,
                "autonomia_silo": 2,
                "autonomia_cisterna": 2,
                "semanas_reserva": 1,
            }

            for clave, valor in resultados.items():
                self.salidas[clave].set(
                    self._formatear(valor, decimales[clave])
                )

            self.datos_calculados = datos
            self.resultados_calculados = resultados
            self.btn_exportar.config(state="normal")

            self.estado.set(
                "Cálculo completado correctamente. Ya puedes exportar el informe."
            )

        except ValueError as error:
            self.datos_calculados = None
            self.resultados_calculados = None
            self.btn_exportar.config(state="disabled")
            self.estado.set("Revisa los datos de entrada.")
            messagebox.showerror("Datos no válidos", str(error))

    def exportar_word(self):
        """Muestra el cuadro de diálogo para guardar y genera el archivo .docx."""
        if not self.datos_calculados or not self.resultados_calculados:
            messagebox.showwarning(
                "Atención", "Realiza primero un cálculo válido."
            )
            return

        ruta_archivo = filedialog.asksaveasfilename(
            title="Guardar informe de cálculo",
            defaultextension=".docx",
            filetypes=[
                ("Documento de Microsoft Word", "*.docx"),
                ("Todos los archivos", "*.*"),
            ],
            initialfile="Informe_Calculo_Silo.docx",
        )

        if not ruta_archivo:
            return

        try:
            generar_documento_word(
                self.datos_calculados,
                self.resultados_calculados,
                ruta_archivo,
            )
            messagebox.showinfo(
                "Exportación exitosa",
                f"El informe ha sido guardado correctamente en:\n\n{ruta_archivo}",
            )
            self.estado.set("Informe Word exportado con éxito.")
        except Exception as err:
            messagebox.showerror(
                "Error al exportar",
                f"No se pudo guardar el documento:\n{str(err)}",
            )


if __name__ == "__main__":
    aplicacion = CalculadoraSilo()
    aplicacion.mainloop()