import tkinter as tk
from tkinter import ttk, messagebox
import math


def area_tolva_rectangular(h, l1, w1, l2, w2):
    g_largo = math.sqrt(h**2 + ((w1 - w2) / 2) ** 2)
    g_ancho = math.sqrt(h**2 + ((l1 - l2) / 2) ** 2)
    return (l1 + l2) * g_largo + (w1 + w2) * g_ancho


class App(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Cálculo de superficies y masas")
        self.geometry("980x980")
        self.resizable(True, True)

        self.vars = {}
        self.crear_interfaz()

    def crear_interfaz(self):
        titulo = tk.Label(
            self,
            text="Cálculo de superficie lateral y masa",
            font=("Arial", 16, "bold")
        )
        titulo.pack(pady=12)

        contenedor = tk.Frame(self)
        contenedor.pack(padx=15, pady=10, fill="both", expand=True)

        frame_cal = ttk.LabelFrame(contenedor, text="CAL")
        frame_cal.grid(row=0, column=0, padx=10, pady=8, sticky="nsew")

        self.crear_campo(frame_cal, "cal_largo", "Largo [m]", 0)
        self.crear_campo(frame_cal, "cal_ancho", "Ancho [m]", 1)
        self.crear_campo(frame_cal, "cal_alto", "Alto [m]", 2)

        frame_cas = ttk.LabelFrame(contenedor, text="CAS")
        frame_cas.grid(row=0, column=1, padx=10, pady=8, sticky="nsew")

        self.crear_campo(frame_cas, "cas_alto", "Alto [m]", 0)

        tk.Label(
            frame_cas,
            text="Relación usada:\nCAS largo = CAL largo",
            justify="left",
            fg="blue"
        ).grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="w")

        frame_case2 = ttk.LabelFrame(contenedor, text="CAS_E2")
        frame_case2.grid(row=1, column=0, padx=10, pady=8, sticky="nsew")

        self.crear_campo(frame_case2, "case2_largo", "Largo [m]", 0)
        self.crear_campo(frame_case2, "case2_ancho", "Ancho [m]", 1)
        self.crear_campo(frame_case2, "case2_alto", "Alto [m]", 2)

        frame_tolva = ttk.LabelFrame(contenedor, text="TOLVA")
        frame_tolva.grid(row=1, column=1, padx=10, pady=8, sticky="nsew")

        self.crear_campo(frame_tolva, "tolva_alto", "Altura [m]", 0)
        self.crear_campo(frame_tolva, "tolva_boca_desc_largo", "Boca descarga largo [m]", 1)
        self.crear_campo(frame_tolva, "tolva_boca_desc_ancho", "Boca descarga ancho [m]", 2)

        tk.Label(
            frame_tolva,
            text=(
                "Relaciones usadas:\n"
                "Boca sup. largo = CAS_E2 largo\n"
                "Boca sup. ancho = CAS_E2 ancho"
            ),
            justify="left",
            fg="blue"
        ).grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky="w")

        frame_ratios = ttk.LabelFrame(contenedor, text="Ratios de masa")
        frame_ratios.grid(row=2, column=0, padx=10, pady=8, sticky="nsew")

        self.crear_campo(frame_ratios, "ratio_cal", "Ratio CAL [kg/m²]", 0, valor_inicial="55")
        self.crear_campo(frame_ratios, "ratio_cuerpo", "Ratio CUERPO [kg/m²]", 1, valor_inicial="37")

        frame_tubos = ttk.LabelFrame(contenedor, text="Tubos Inyectores Schedule 40 de 1 pulgada")
        frame_tubos.grid(row=2, column=1, padx=10, pady=8, sticky="nsew")

        self.crear_campo(frame_tubos, "tubos_cantidad", "Cantidad", 0)
        self.crear_campo(frame_tubos, "tubos_longitud", "Longitud [m]", 1)

        tk.Label(
            frame_tubos,
            text="Masa tubos = Cantidad × Longitud × 2.45 kg/m",
            justify="left",
            fg="blue"
        ).grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky="w")

        frame_chapas = ttk.LabelFrame(contenedor, text="Chapas especiales")
        frame_chapas.grid(row=3, column=0, columnspan=2, padx=10, pady=8, sticky="nsew")

        self.crear_campo(frame_chapas, "deflectora_ancho", "Chapa deflectora ancho [m]", 0)
        self.crear_campo(frame_chapas, "deflectora_largo", "Chapa deflectora largo [m]", 1)
        self.crear_campo(frame_chapas, "venturi_mangas", "Chapa venturi número de mangas", 2)

        tk.Label(
            frame_chapas,
            text=(
                "Masa chapa deflectora = Ancho × Largo × 24 kg\n"
                "Masa chapa venturi = Nº mangas × 1.5 kg"
            ),
            justify="left",
            fg="blue"
        ).grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky="w")

        frame_areas = ttk.LabelFrame(contenedor, text="Resultados de áreas")
        frame_areas.grid(row=4, column=0, padx=10, pady=8, sticky="nsew")

        self.lbl_area_puertas = tk.Label(frame_areas, text="PUERTAS: -", font=("Arial", 11))
        self.lbl_area_puertas.pack(anchor="w", padx=12, pady=2)

        self.lbl_area_cal = tk.Label(frame_areas, text="CAL: -", font=("Arial", 11))
        self.lbl_area_cal.pack(anchor="w", padx=12, pady=2)

        self.lbl_area_cas = tk.Label(frame_areas, text="CAS: -", font=("Arial", 11))
        self.lbl_area_cas.pack(anchor="w", padx=12, pady=2)

        self.lbl_area_case2 = tk.Label(frame_areas, text="CAS_E2: -", font=("Arial", 11))
        self.lbl_area_case2.pack(anchor="w", padx=12, pady=2)

        self.lbl_area_tolva = tk.Label(frame_areas, text="TOLVA: -", font=("Arial", 11))
        self.lbl_area_tolva.pack(anchor="w", padx=12, pady=2)

        self.lbl_area_total = tk.Label(
            frame_areas,
            text="ÁREA TOTAL: -",
            font=("Arial", 12, "bold")
        )
        self.lbl_area_total.pack(anchor="w", padx=12, pady=6)

        frame_masas = ttk.LabelFrame(contenedor, text="Resultados de masas")
        frame_masas.grid(row=4, column=1, padx=10, pady=8, sticky="nsew")

        self.lbl_masa_puertas = tk.Label(frame_masas, text="PUERTAS: -", font=("Arial", 11))
        self.lbl_masa_puertas.pack(anchor="w", padx=12, pady=2)

        self.lbl_masa_cal = tk.Label(frame_masas, text="CAL: -", font=("Arial", 11))
        self.lbl_masa_cal.pack(anchor="w", padx=12, pady=2)

        self.lbl_masa_cas = tk.Label(frame_masas, text="CAS: -", font=("Arial", 11))
        self.lbl_masa_cas.pack(anchor="w", padx=12, pady=2)

        self.lbl_masa_case2 = tk.Label(frame_masas, text="CAS_E2: -", font=("Arial", 11))
        self.lbl_masa_case2.pack(anchor="w", padx=12, pady=2)

        self.lbl_masa_tolva = tk.Label(frame_masas, text="TOLVA: -", font=("Arial", 11))
        self.lbl_masa_tolva.pack(anchor="w", padx=12, pady=2)

        self.lbl_masa_tubos = tk.Label(frame_masas, text="TUBOS INYECTORES: -", font=("Arial", 11))
        self.lbl_masa_tubos.pack(anchor="w", padx=12, pady=2)

        self.lbl_masa_deflectora = tk.Label(frame_masas, text="CHAPA DEFLECTORA: -", font=("Arial", 11))
        self.lbl_masa_deflectora.pack(anchor="w", padx=12, pady=2)

        self.lbl_masa_venturi = tk.Label(frame_masas, text="CHAPA VENTURI: -", font=("Arial", 11))
        self.lbl_masa_venturi.pack(anchor="w", padx=12, pady=2)

        self.lbl_masa_total = tk.Label(
            frame_masas,
            text="MASA TOTAL: -",
            font=("Arial", 12, "bold")
        )
        self.lbl_masa_total.pack(anchor="w", padx=12, pady=6)

        frame_botones = tk.Frame(contenedor)
        frame_botones.grid(row=5, column=1, padx=10, pady=15, sticky="e")

        btn_limpiar = tk.Button(
            frame_botones,
            text="Limpiar",
            command=self.limpiar,
            bg="#f44336",
            fg="white",
            width=16,
            font=("Arial", 10, "bold")
        )
        btn_limpiar.grid(row=0, column=0, padx=10)

        btn_calcular = tk.Button(
            frame_botones,
            text="Calcular",
            command=self.calcular,
            bg="#4CAF50",
            fg="white",
            width=16,
            font=("Arial", 10, "bold")
        )
        btn_calcular.grid(row=0, column=1, padx=10)

    def crear_campo(self, parent, key, texto, fila, valor_inicial=""):
        lbl = tk.Label(parent, text=texto)
        lbl.grid(row=fila, column=0, padx=5, pady=4, sticky="w")

        var = tk.StringVar(value=valor_inicial)
        ent = tk.Entry(parent, textvariable=var, width=20)
        ent.grid(row=fila, column=1, padx=5, pady=4)

        self.vars[key] = var

    def obtener_float(self, key, nombre):
        valor = self.vars[key].get().strip().replace(",", ".")

        if not valor:
            raise ValueError(f"Falta el valor de: {nombre}")

        try:
            numero = float(valor)
        except ValueError:
            raise ValueError(f"El valor de '{nombre}' no es numérico.")

        if numero <= 0:
            raise ValueError(f"El valor de '{nombre}' debe ser mayor que cero.")

        return numero

    def calcular(self):
        try:
            cal_largo = self.obtener_float("cal_largo", "CAL largo")
            cal_ancho = self.obtener_float("cal_ancho", "CAL ancho")
            cal_alto = self.obtener_float("cal_alto", "CAL alto")

            cas_alto = self.obtener_float("cas_alto", "CAS alto")

            case2_largo = self.obtener_float("case2_largo", "CAS_E2 largo")
            case2_ancho = self.obtener_float("case2_ancho", "CAS_E2 ancho")
            case2_alto = self.obtener_float("case2_alto", "CAS_E2 alto")

            tolva_alto = self.obtener_float("tolva_alto", "TOLVA alto")
            tolva_boca_desc_largo = self.obtener_float("tolva_boca_desc_largo", "TOLVA boca descarga largo")
            tolva_boca_desc_ancho = self.obtener_float("tolva_boca_desc_ancho", "TOLVA boca descarga ancho")

            ratio_cal = self.obtener_float("ratio_cal", "Ratio CAL")
            ratio_cuerpo = self.obtener_float("ratio_cuerpo", "Ratio CUERPO")

            tubos_cantidad = self.obtener_float("tubos_cantidad", "Tubos inyectores cantidad")
            tubos_longitud = self.obtener_float("tubos_longitud", "Tubos inyectores longitud")

            deflectora_ancho = self.obtener_float("deflectora_ancho", "Chapa deflectora ancho")
            deflectora_largo = self.obtener_float("deflectora_largo", "Chapa deflectora largo")
            venturi_mangas = self.obtener_float("venturi_mangas", "Chapa venturi número de mangas")

            area_puertas = cal_largo * cal_ancho
            area_cal = (cal_largo + cal_ancho) * 2 * cal_alto
            area_cas = (cal_largo + cal_ancho) * 2 * cas_alto
            area_case2 = (case2_largo + case2_ancho) * 2 * case2_alto

            area_tolva = area_tolva_rectangular(
                tolva_alto,
                case2_largo,
                case2_ancho,
                tolva_boca_desc_largo,
                tolva_boca_desc_ancho
            )

            area_total = area_puertas + area_cal + area_cas + area_case2 + area_tolva

            masa_puertas = area_puertas * ratio_cuerpo
            masa_cal = area_cal * ratio_cal
            masa_cas = area_cas * ratio_cuerpo
            masa_case2 = area_case2 * ratio_cuerpo
            masa_tolva = area_tolva * ratio_cuerpo
            masa_tubos = tubos_cantidad * tubos_longitud * 2.45
            masa_deflectora = deflectora_ancho * deflectora_largo * 24
            masa_venturi = venturi_mangas * 1.5

            masa_total = (
                masa_puertas
                + masa_cal
                + masa_cas
                + masa_case2
                + masa_tolva
                + masa_tubos
                + masa_deflectora
                + masa_venturi
            )

            self.lbl_area_puertas.config(text=f"PUERTAS: {area_puertas:,.2f} m²")
            self.lbl_area_cal.config(text=f"CAL: {area_cal:,.2f} m²")
            self.lbl_area_cas.config(text=f"CAS: {area_cas:,.2f} m²")
            self.lbl_area_case2.config(text=f"CAS_E2: {area_case2:,.2f} m²")
            self.lbl_area_tolva.config(text=f"TOLVA: {area_tolva:,.2f} m²")
            self.lbl_area_total.config(text=f"ÁREA TOTAL: {area_total:,.2f} m²")

            self.lbl_masa_puertas.config(text=f"PUERTAS: {masa_puertas:,.2f} kg")
            self.lbl_masa_cal.config(text=f"CAL: {masa_cal:,.2f} kg")
            self.lbl_masa_cas.config(text=f"CAS: {masa_cas:,.2f} kg")
            self.lbl_masa_case2.config(text=f"CAS_E2: {masa_case2:,.2f} kg")
            self.lbl_masa_tolva.config(text=f"TOLVA: {masa_tolva:,.2f} kg")
            self.lbl_masa_tubos.config(text=f"TUBOS INYECTORES: {masa_tubos:,.2f} kg")
            self.lbl_masa_deflectora.config(text=f"CHAPA DEFLECTORA: {masa_deflectora:,.2f} kg")
            self.lbl_masa_venturi.config(text=f"CHAPA VENTURI: {masa_venturi:,.2f} kg")
            self.lbl_masa_total.config(text=f"MASA TOTAL: {masa_total:,.2f} kg")

        except ValueError as e:
            messagebox.showerror("Error de datos", str(e))

        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error inesperado:\n{e}")

    def limpiar(self):
        for key, var in self.vars.items():
            if key == "ratio_cal":
                var.set("55")
            elif key == "ratio_cuerpo":
                var.set("37")
            else:
                var.set("")

        self.lbl_area_puertas.config(text="PUERTAS: -")
        self.lbl_area_cal.config(text="CAL: -")
        self.lbl_area_cas.config(text="CAS: -")
        self.lbl_area_case2.config(text="CAS_E2: -")
        self.lbl_area_tolva.config(text="TOLVA: -")
        self.lbl_area_total.config(text="ÁREA TOTAL: -")

        self.lbl_masa_puertas.config(text="PUERTAS: -")
        self.lbl_masa_cal.config(text="CAL: -")
        self.lbl_masa_cas.config(text="CAS: -")
        self.lbl_masa_case2.config(text="CAS_E2: -")
        self.lbl_masa_tolva.config(text="TOLVA: -")
        self.lbl_masa_tubos.config(text="TUBOS INYECTORES: -")
        self.lbl_masa_deflectora.config(text="CHAPA DEFLECTORA: -")
        self.lbl_masa_venturi.config(text="CHAPA VENTURI: -")
        self.lbl_masa_total.config(text="MASA TOTAL: -")


if __name__ == "__main__":
    app = App()
    app.mainloop()