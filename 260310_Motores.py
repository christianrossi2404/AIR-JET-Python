import math
import tkinter as tk
from tkinter import ttk, messagebox


def densidad_aire(temp_c: float, altitud_m: float) -> float:
    """
    Densidad del aire seco usando atmósfera estándar + gas ideal.
    Válido como aproximación de ingeniería.
    """
    temp_k = temp_c + 273.15
    if temp_k <= 0:
        raise ValueError("La temperatura absoluta debe ser mayor que 0 K.")

    # Presión atmosférica aproximada en función de la altitud (troposfera)
    presion_pa = 101325.0 * (1 - 2.25577e-5 * altitud_m) ** 5.25588
    r_aire = 287.05  # J/(kg·K)
    return presion_pa / (r_aire * temp_k)


def potencia_a_temp(p_base_kw: float, temp_base_c: float, temp_objetivo_c: float) -> float:
    """
    Escalado de potencia suponiendo mismo ventilador, mismas rpm,
    mismo caudal volumétrico y potencia proporcional a densidad.
    """
    t_base_k = temp_base_c + 273.15
    t_obj_k = temp_objetivo_c + 273.15
    if t_base_k <= 0 or t_obj_k <= 0:
        raise ValueError("La temperatura absoluta debe ser mayor que 0 K.")
    return p_base_kw * (t_base_k / t_obj_k)


def temperatura_minima_por_potencia(p_base_kw: float, temp_base_c: float, p_instalada_kw: float) -> float:
    """Temperatura mínima teórica limitada por la potencia instalada."""
    if p_base_kw <= 0 or p_instalada_kw <= 0:
        raise ValueError("Las potencias deben ser mayores que 0.")
    t_base_k = temp_base_c + 273.15
    t_lim_k = t_base_k * (p_base_kw / p_instalada_kw)
    return t_lim_k - 273.15


def talla_comercial_motor(p_kw: float) -> str:
    """
    Selección simple de talla comercial IEC habitual.
    Devuelve la inmediata superior.
    """
    tallas = [
        0.37, 0.55, 0.75, 1.1, 1.5, 2.2, 3.0, 4.0, 5.5, 7.5,
        11.0, 15.0, 18.5, 22.0, 30.0, 37.0, 45.0, 55.0, 75.0,
        90.0, 110.0, 132.0, 160.0, 200.0, 250.0
    ]
    for talla in tallas:
        if p_kw <= talla:
            return f"{talla:g} kW"
    return f"> {tallas[-1]:g} kW"


class AplicacionVentilador(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Cálculo de potencia de ventilador vs temperatura")
        self.geometry("980x720")
        self.minsize(900, 620)

        self._crear_estilos()
        self._crear_interfaz()

    def _crear_estilos(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

    def _crear_interfaz(self):
        cont = ttk.Frame(self, padding=12)
        cont.pack(fill="both", expand=True)

        cab = ttk.Label(
            cont,
            text="Tabla de potencia absorbida del ventilador",
            font=("Segoe UI", 16, "bold")
        )
        cab.pack(anchor="w", pady=(0, 10))

        desc = ttk.Label(
            cont,
            text=(
                "Hipótesis: mismo ventilador, mismas rpm y potencia proporcional a la densidad del aire. "
                "Se genera una tabla cada 10 °C."
            ),
            wraplength=900,
            justify="left"
        )
        desc.pack(anchor="w", pady=(0, 12))

        form = ttk.LabelFrame(cont, text="Datos de entrada", padding=12)
        form.pack(fill="x")

        self.vars = {
            "pot_absorbida": tk.StringVar(value="5.94"),
            "altitud": tk.StringVar(value="723"),
            "temp_asp": tk.StringVar(value="180"),
            "pot_instalada": tk.StringVar(value="11"),
            "pot_0": tk.StringVar(value=""),
        }

        campos = [
            ("Potencia absorbida en la condición base (kW)", "pot_absorbida"),
            ("Altitud (m)", "altitud"),
            ("Temperatura de aspiración base (°C)", "temp_asp"),
            ("Potencia instalada (kW)", "pot_instalada"),
            ("Potencia consumida a 0 °C (kW, opcional)", "pot_0"),
        ]

        for i, (texto, clave) in enumerate(campos):
            ttk.Label(form, text=texto).grid(row=i, column=0, sticky="w", padx=(0, 10), pady=6)
            ttk.Entry(form, textvariable=self.vars[clave], width=20).grid(row=i, column=1, sticky="w", pady=6)

        botones = ttk.Frame(form)
        botones.grid(row=len(campos), column=0, columnspan=2, sticky="w", pady=(12, 0))

        ttk.Button(botones, text="Calcular tabla", command=self.calcular).pack(side="left")
        ttk.Button(botones, text="Limpiar", command=self.limpiar).pack(side="left", padx=8)

        resumen_box = ttk.LabelFrame(cont, text="Resumen", padding=12)
        resumen_box.pack(fill="x", pady=12)

        self.resumen = tk.Text(resumen_box, height=8, wrap="word")
        self.resumen.pack(fill="x")
        self.resumen.configure(state="disabled")

        tabla_box = ttk.LabelFrame(cont, text="Tabla cada 10 °C", padding=12)
        tabla_box.pack(fill="both", expand=True)

        columnas = ("temperatura", "densidad", "potencia", "estado")
        self.tree = ttk.Treeview(tabla_box, columns=columnas, show="headings", height=18)
        self.tree.heading("temperatura", text="Temperatura (°C)")
        self.tree.heading("densidad", text="Densidad aprox. (kg/m³)")
        self.tree.heading("potencia", text="Potencia absorbida (kW)")
        self.tree.heading("estado", text="Estado vs potencia instalada")

        self.tree.column("temperatura", width=140, anchor="center")
        self.tree.column("densidad", width=180, anchor="center")
        self.tree.column("potencia", width=180, anchor="center")
        self.tree.column("estado", width=260, anchor="center")

        scroll = ttk.Scrollbar(tabla_box, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

    def limpiar(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self._set_resumen("")

    def _set_resumen(self, texto: str):
        self.resumen.configure(state="normal")
        self.resumen.delete("1.0", tk.END)
        self.resumen.insert("1.0", texto)
        self.resumen.configure(state="disabled")

    def calcular(self):
        try:
            p_base = float(self.vars["pot_absorbida"].get().replace(",", "."))
            altitud = float(self.vars["altitud"].get().replace(",", "."))
            temp_base = float(self.vars["temp_asp"].get().replace(",", "."))
            p_inst = float(self.vars["pot_instalada"].get().replace(",", "."))
            pot_0_txt = self.vars["pot_0"].get().strip().replace(",", ".")
            p0_usuario = float(pot_0_txt) if pot_0_txt else None

            if p_base <= 0 or p_inst <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Revisa los datos introducidos. Las potencias deben ser numéricas y mayores que 0.")
            return

        for item in self.tree.get_children():
            self.tree.delete(item)

        try:
            t_min = temperatura_minima_por_potencia(p_base, temp_base, p_inst)
            p_0_calc = potencia_a_temp(p_base, temp_base, 0)
            dens_base = densidad_aire(temp_base, altitud)
            dens_0 = densidad_aire(0, altitud)
        except ValueError as exc:
            messagebox.showerror("Error", str(exc))
            return

        # Tabla desde la temperatura base hasta el escalón de 10 °C inferior al límite.
        temp_inicio = int(math.floor(temp_base / 10.0) * 10)
        temp_fin = int(math.floor(t_min / 10.0) * 10)

        if temp_fin > temp_inicio:
            temp_fin = temp_inicio

        for temp in range(temp_inicio, temp_fin - 10, -10):
            try:
                dens = densidad_aire(temp, altitud)
                pot = potencia_a_temp(p_base, temp_base, temp)
            except ValueError:
                continue

            estado = "OK"
            if abs(pot - p_inst) < 1e-6:
                estado = "Límite"
            elif pot > p_inst:
                estado = "Supera potencia instalada"

            self.tree.insert(
                "",
                tk.END,
                values=(
                    f"{temp:.0f}",
                    f"{dens:.3f}",
                    f"{pot:.2f}",
                    estado,
                ),
            )

        talla_0 = talla_comercial_motor(p_0_calc)
        talla_recom = talla_comercial_motor(max(p_0_calc, p_inst))

        lineas = [
            f"Condición base: {p_base:.2f} kW a {temp_base:.1f} °C y {altitud:.0f} m.",
            f"Densidad aproximada en condición base: {dens_base:.3f} kg/m³.",
            f"Densidad aproximada a 0 °C: {dens_0:.3f} kg/m³.",
            f"Potencia calculada a 0 °C: {p_0_calc:.2f} kW.",
            f"Temperatura mínima teórica limitada por {p_inst:.2f} kW: {t_min:.1f} °C.",
        ]

        if p0_usuario is not None:
            diferencia = p0_usuario - p_0_calc
            lineas.append(
                f"Potencia a 0 °C introducida por el usuario: {p0_usuario:.2f} kW "
                f"(diferencia respecto al cálculo: {diferencia:+.2f} kW)."
            )

        lineas.append(f"Talla comercial mínima para 0 °C: {talla_0}.")
        lineas.append(f"Talla de motor aconsejada: {talla_recom}.")

        if p_0_calc <= p_inst:
            lineas.append("Mensaje: la potencia instalada cubre el caso de 0 °C.")
        else:
            lineas.append("Mensaje: la potencia instalada NO cubre el caso de 0 °C; conviene subir la talla del motor.")

        self._set_resumen("\n".join(lineas))


if __name__ == "__main__":
    app = AplicacionVentilador()
    app.mainloop()
