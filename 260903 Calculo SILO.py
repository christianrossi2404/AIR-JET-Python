import math
import tkinter as tk
from tkinter import messagebox, ttk


HORAS_POR_SEMANA = 24 * 7
RATIO_MINIMO = 2.5
RATIO_MAXIMO = 3.0


def calcular_resultados(datos):
    """Devuelve los resultados del silo y del consumo de reactivo."""
    diametro = datos["diametro"]
    altura_cilindro = datos["altura_cilindro"]
    altura_cono = datos["altura_cono"]
    consumo_hora = datos["consumo_hora"]
    densidad = datos["densidad"]
    volumen_cisterna = datos["volumen_cisterna"]
    factor_efectivo = datos["aprovechamiento"] / 100

    radio = diametro / 2
    ratio = altura_cilindro / diametro

    volumen_cilindro = math.pi * radio**2 * altura_cilindro
    volumen_cono = math.pi * radio**2 * altura_cono / 3
    volumen_total = volumen_cilindro + volumen_cono
    volumen_efectivo = volumen_total * factor_efectivo

    consumo_kg_semana = consumo_hora * HORAS_POR_SEMANA
    consumo_m3_semana = consumo_kg_semana / densidad

    autonomia_silo = volumen_efectivo / consumo_m3_semana
    autonomia_cisterna = volumen_cisterna / consumo_m3_semana

    # Reserva disponible cuando ya cabe una cisterna completa en el silo.
    semanas_reserva = autonomia_silo - autonomia_cisterna

    return {
        "ratio": ratio,
        "volumen_total": volumen_total,
        "volumen_efectivo": volumen_efectivo,
        "consumo_kg_semana": consumo_kg_semana,
        "consumo_m3_semana": consumo_m3_semana,
        "autonomia_silo": autonomia_silo,
        "autonomia_cisterna": autonomia_cisterna,
        "semanas_reserva": semanas_reserva,
    }


class CalculadoraSilo(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Calculadora de silo y reactivo · versión actualizada")
        self.resizable(False, False)

        self.entradas = {}
        self.salidas = {}
        self.estado = tk.StringVar(value="Introduce los datos y pulsa Calcular.")

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

        marco_silo = ttk.LabelFrame(contenedor, text="INPUT · SILO", padding=8)
        marco_silo.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=(0, 8))

        self._campo(marco_silo, 0, "Diámetro del silo", "diametro", "3", "m")
        self._campo(
            marco_silo, 1, "Altura del cilindro", "altura_cilindro", "8", "m"
        )
        self._campo(marco_silo, 2, "Ángulo del cono", "angulo_cono", "60", "°")
        self._campo(marco_silo, 3, "Altura del cono", "altura_cono", "3", "m")
        self._campo(
            marco_silo,
            4,
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
            marco_reactivo, 0, "Consumo de reactivo", "consumo_hora", "15", "kg/h"
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

        ttk.Button(contenedor, text="Calcular", command=self.calcular).grid(
            row=1, column=0, columnspan=2, pady=(2, 10), ipadx=24, ipady=4
        )

        salida_silo = ttk.LabelFrame(contenedor, text="OUTPUT · SILO", padding=8)
        salida_silo.grid(
            row=2, column=0, sticky="nsew", padx=(0, 8), pady=(0, 8)
        )

        self._resultado(salida_silo, 0, "Ratio altura/diámetro", "ratio")
        self._resultado(salida_silo, 1, "Volumen total", "volumen_total", "m³")
        self._resultado(
            salida_silo, 2, "Volumen efectivo", "volumen_efectivo", "m³"
        )

        salida_reactivo = ttk.LabelFrame(
            contenedor, text="OUTPUT · REACTIVO", padding=8
        )
        salida_reactivo.grid(row=2, column=1, sticky="nsew", pady=(0, 8))

        self._resultado(
            salida_reactivo,
            0,
            "Consumo semanal",
            "consumo_kg_semana",
            "kg/sem",
        )
        self._resultado(
            salida_reactivo,
            1,
            "Consumo semanal",
            "consumo_m3_semana",
            "m³/sem",
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

        ttk.Label(contenedor, textvariable=self.estado, foreground="#555555").grid(
            row=4, column=0, columnspan=2, sticky="w", pady=(8, 0)
        )

    @staticmethod
    def _convertir_numero(texto, nombre):
        try:
            return float(texto.strip().replace(",", "."))
        except ValueError as error:
            raise ValueError(f"{nombre} debe ser un número válido.") from error

    def _leer_entradas(self):
        nombres = {
            "diametro": "El diámetro del silo",
            "altura_cilindro": "La altura del cilindro",
            "angulo_cono": "El ángulo del cono",
            "altura_cono": "La altura del cono",
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
            "altura_cono",
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
                "volumen_total": 3,
                "volumen_efectivo": 3,
                "consumo_kg_semana": 2,
                "consumo_m3_semana": 3,
                "autonomia_silo": 2,
                "autonomia_cisterna": 2,
                "semanas_reserva": 1,
            }

            for clave, valor in resultados.items():
                self.salidas[clave].set(self._formatear(valor, decimales[clave]))

            self.estado.set("Cálculo completado correctamente.")

        except ValueError as error:
            self.estado.set("Revisa los datos de entrada.")
            messagebox.showerror("Datos no válidos", str(error))


if __name__ == "__main__":
    aplicacion = CalculadoraSilo()
    aplicacion.mainloop()