#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generador de características técnicas. Python 3.10+ / Windows / Excel instalado.

Instalación (una vez, en PowerShell):
    py -m pip install pywin32 lxml
Ejecución:
    py rellenar_caracteristicas_tecnicas.py

Interfaz gráfica: selecciona el archivo; Excel solicita la contraseña en su propia ventana.
La salida se guarda junto al Excel como CT-NOF.docx. El script no recibe ni guarda la contraseña.
El libro se abre de solo lectura, sin actualizar vínculos ni ejecutar macros VBA.
La plantilla y el Excel originales nunca se guardan ni sobrescriben.
La hoja CT debe contener nombres de campo y valores en dos columnas contiguas.
Se detecta la columna que contiene NOF. Si hay varias matrices, se pide elegir.
Si fuera necesario, fija RANGO_MATRIZ, por ejemplo 'A1:B34'.
No requiere ChatGPT, una API ni Microsoft Word para generar el DOCX.
"""
from __future__ import annotations

import os
import re
import sys
import tempfile
from decimal import Decimal, InvalidOperation
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

CARPETA_WORD = Path(r"Y:\COSTES\PLANTILLAS")
NOMBRE_WORD = "CARACTERISTICAS TECNICAS"
CARPETA_EXCEL = Path(r"C:\Users\Christian Rossi\Desktop\feina\SPEC_TECNICAS_FILTROS")
HOJA = "CT"
RANGO_MATRIZ = ""  # Opcional: 'A1:B34'; exactamente dos columnas.

LONGITUDES = {4: "1.261", 6: "1.870", 8: "2.479", 10: "3.088", 12: "3.697", 14: "4.410"}
W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W}
PATRON = re.compile(r"\{\{\s*([^{}]+?)\s*\}\}")
CAMPOS = set("NOF ATEX CAUDAL TEMPERATURA PRODUCT CONC DENS FILTRO SUP_FILTRANTE RATIO_F CONSUMO_AIRE P_T P_D ESP_CAL ESP_VENT ESP_CAS ESP_TOLVA MATER_CAL MATER_CHV MATER_CAS MATER_TLV ANG MAT_MANGA NUM_MANGAS LONG_MANGA MAT_JAULA DIAM_COL NUM_VALV DIAM_ELE TIMER_MAN_CT MAN_CT BAR 00".split()) | {"ENTRADA FILTRO"}


def normalizar(valor):
    return " ".join(str(valor or "").replace("\xa0", " ").strip().split())


def localizar(carpeta, nombre, extensiones):
    if not carpeta.is_dir():
        raise ValueError(f"No se puede acceder a {carpeta}. Comprueba la ruta y, para Y:, la conexión a la unidad de red.")
    archivos = [p for p in carpeta.iterdir() if p.is_file() and p.stem.casefold() == nombre.casefold() and p.suffix.lower() in extensiones]
    if len(archivos) != 1:
        raise ValueError(f"Se esperaba un único archivo '{nombre}' en {carpeta}, con extensión {', '.join(extensiones)}. Encontrados: {len(archivos)}.")
    return archivos[0]


def numero(valor, campo):
    if isinstance(valor, bool):
        raise ValueError(f"{campo}: se esperaba un número, no un valor lógico.")
    try:
        n = Decimal(str(valor).strip().replace(",", "."))
        if not n.is_finite():
            raise InvalidOperation
        return n
    except (InvalidOperation, ValueError):
        raise ValueError(f"{campo}: valor numérico no válido ({valor!r}).") from None


def aplicar_reglas(datos, originales):
    resultado = dict(datos)
    if "LONG_MANGA" in originales:
        n = numero(originales["LONG_MANGA"], "LONG_MANGA")
        if n not in LONGITUDES:
            raise ValueError(f"LONG_MANGA={n}: no hay equivalencia. Valores admitidos: 4, 6, 8, 10, 12, 14.")
        resultado["LONG_MANGA"] = LONGITUDES[n]
    if "TIMER_MAN_CT" in originales:
        n = numero(originales["TIMER_MAN_CT"], "TIMER_MAN_CT")
        especial = n in (2, 3, 4)
        resultado["TIMER_MAN_CT"] = "Timer-manómetro. 220 Vac / IP56 / 50 Hz" + ("" if especial else " / signal 4-20 mA")
        resultado["MAN_CT"] = "Esfera 0-300 mmca" if especial else "-"
    # Las reglas del modelo prevalecen sobre los valores de la matriz.
    filtro = normalizar(datos.get("FILTRO", "")).upper()
    if filtro.endswith("PL"):
        campos_no_aplicables = ("ESP_CAS", "MATER_CAS", "ESP_TOLVA", "MATER_TLV")
    elif filtro.endswith(("A", "AE")):
        campos_no_aplicables = ("ESP_TOLVA", "MATER_TLV")
    else:
        campos_no_aplicables = ()
    for campo in campos_no_aplicables:
        resultado[campo] = "-"
    return resultado


def texto_celda(excel, celda):
    valor = celda.Value2
    if valor is None:
        return ""
    if bool(excel.WorksheetFunction.IsError(celda)):
        raise ValueError(f"La celda {celda.Address} contiene un error de Excel. Corrígelo antes de continuar.")
    if isinstance(valor, bool):
        return "VERDADERO" if valor else "FALSO"
    if isinstance(valor, str):
        return valor.strip()
    formato = str(celda.NumberFormat)
    # General: evitar notación científica y redondeo debido al ancho de columna.
    if formato.casefold() == "general":
        texto = format(Decimal(str(valor)), "f")
        if "." in texto:
            texto = texto.rstrip("0").rstrip(".")
        return texto.replace(".", ",")
    texto = str(celda.Text)
    if not texto.strip() or re.fullmatch(r"#+", texto.strip()) or re.search(r"\d[Ee][+-]\d", texto):
        texto = str(excel.WorksheetFunction.Text(valor, formato))
    if not texto.strip() or re.fullmatch(r"#+", texto.strip()):
        raise ValueError(f"No se puede leer el formato de {celda.Address}. Revisa esa celda en Excel.")
    return texto.strip()


def leer_excel(ruta, campos, elegir_matriz):
    import pythoncom
    import win32com.client
    pythoncom.CoInitialize()
    excel = libro = hoja = celda = area = None
    try:
        excel = win32com.client.DispatchEx("Excel.Application")
        excel.Visible = True
        excel.DisplayAlerts = True
        excel.EnableEvents = False
        excel.AskToUpdateLinks = False
        excel.AutomationSecurity = 3  # msoAutomationSecurityForceDisable
        # Evita recalcular o refrescar vínculos: se usan los valores guardados.
        # Algunos Excel no permiten cambiar Calculation sin un libro abierto.
        try:
            excel.Calculation = -4135  # xlCalculationManual
        except Exception:
            pass
        # Omitir Password permite que Excel muestre su diálogo nativo.
        # El script espera hasta que el usuario complete o cancele la apertura.
        try:
            libro = excel.Workbooks.Open(
                Filename=str(ruta), UpdateLinks=0, ReadOnly=True,
                WriteResPassword="", IgnoreReadOnlyRecommended=True,
                Notify=False, AddToMru=False, Local=True,
            )
        except Exception:
            raise ValueError(
                "Excel no abrió el archivo. La apertura pudo haberse cancelado, "
                "la contraseña ser incorrecta o el archivo no estar disponible. "
                "Vuelve a ejecutar el script para intentarlo de nuevo."
            ) from None
        if libro is None:
            raise Cancelado()
        excel.DisplayAlerts = False
        try:
            hoja = libro.Worksheets(HOJA)
        except Exception:
            raise ValueError(f"El libro no contiene una pestaña llamada {HOJA!r}.") from None
        area = hoja.Range(RANGO_MATRIZ) if RANGO_MATRIZ else hoja.UsedRange
        if RANGO_MATRIZ and int(area.Columns.Count) != 2:
            raise ValueError("RANGO_MATRIZ debe tener exactamente dos columnas: campo y valor.")
        filas, columnas = int(area.Rows.Count), int(area.Columns.Count)
        if filas * columnas > 2_000_000:
            raise ValueError("La zona usada de CT es demasiado grande. Especifica RANGO_MATRIZ al principio del script.")
        inicio_f, inicio_c = int(area.Row), int(area.Column)
        valores = area.Value2
        if filas == 1 and columnas == 1:
            valores = ((valores,),)
        opciones = []
        for i, fila in enumerate(valores):
            for j, valor in enumerate(fila[:-1]):
                if normalizar(valor) == "NOF":
                    opciones.append((inicio_f + i, inicio_c + j))
        if not opciones:
            raise ValueError("No se encontró NOF con una columna de valores a su derecha en CT. Revisa la matriz o RANGO_MATRIZ.")
        if len(opciones) > 1:
            eleccion = elegir_matriz(opciones)
            if eleccion is None:
                raise Cancelado()
            if not 1 <= eleccion <= len(opciones):
                raise ValueError("Selección no válida.")
            primera, columna = opciones[eleccion - 1]
        else:
            primera, columna = opciones[0]
        ultima = inicio_f + filas - 1
        datos, originales, vacios = {}, {}, []
        for f in range(primera, ultima + 1):
            clave = normalizar(valores[f-inicio_f][columna-inicio_c])
            if f != primera and clave == "NOF":
                break
            if clave not in campos:
                continue
            if clave in datos or clave in vacios:
                raise ValueError(f"Campo duplicado {clave!r} en CT. Delimita la matriz con RANGO_MATRIZ.")
            celda = hoja.Cells(f, columna + 1)
            valor = texto_celda(excel, celda)
            if valor == "":
                vacios.append(clave)
                continue
            datos[clave] = valor
            originales[clave] = celda.Value2
        if "NOF" not in datos:
            raise ValueError("NOF está vacío. No se puede identificar el documento.")
        if len(datos) < 3:
            raise ValueError("No se encontró una matriz válida de campos y valores en columnas contiguas.")
        return datos, originales, vacios
    finally:
        celda = area = hoja = None
        if libro is not None:
            try:
                libro.Close(SaveChanges=False)
            except Exception:
                pass
        libro = None
        if excel is not None:
            try:
                excel.Quit()
            except Exception:
                pass
        excel = None
        pythoncom.CoUninitialize()


def xml_word(nombre):
    return nombre.startswith("word/") and nombre.endswith(".xml")


def marcadores_plantilla(ruta):
    from lxml import etree
    encontrados = set()
    with ZipFile(ruta) as z:
        for nombre in z.namelist():
            if xml_word(nombre):
                raiz = etree.fromstring(z.read(nombre))
                for p in raiz.xpath("//w:p", namespaces=NS):
                    texto = "".join(p.xpath(".//w:t/text()", namespaces=NS))
                    encontrados.update(normalizar(m.group(1)) for m in PATRON.finditer(texto))
    return encontrados


def fijar_campo_filename(parrafo):
    """Materializa solo campos FILENAME; conserva PAGE y otros campos."""
    for simple in list(parrafo.xpath(".//w:fldSimple", namespaces=NS)):
        if re.match(r"\s*FILENAME\b", simple.get(f"{{{W}}}instr", ""), re.I):
            padre = simple.getparent()
            posicion = padre.index(simple)
            for hijo in list(simple):
                padre.insert(posicion, hijo)
                posicion += 1
            padre.remove(simple)
    pila = []
    borrar = []
    for nodo in parrafo.iter():
        if nodo.tag == f"{{{W}}}fldChar":
            tipo = nodo.get(f"{{{W}}}fldCharType")
            if tipo == "begin":
                pila.append({"nodos": [nodo], "codigo": ""})
            elif pila:
                pila[-1]["nodos"].append(nodo)
                if tipo == "end":
                    campo = pila.pop()
                    if re.match(r"\s*FILENAME\b", campo["codigo"], re.I):
                        borrar.extend(campo["nodos"])
        elif nodo.tag == f"{{{W}}}instrText" and pila:
            pila[-1]["nodos"].append(nodo)
            pila[-1]["codigo"] += nodo.text or ""
    for nodo in borrar:
        nodo.getparent().remove(nodo)


def rellenar_word(origen, destino, datos):
    from lxml import etree
    usados, pendientes = set(), set()
    cantidad = 0
    # Modo x: jamás sobrescribe una salida existente.
    with ZipFile(origen) as src, ZipFile(destino, "x", ZIP_DEFLATED) as dst:
        for info in src.infolist():
            contenido = src.read(info.filename)
            if xml_word(info.filename):
                raiz = etree.fromstring(contenido)
                modificado = False
                for p in raiz.xpath("//w:p", namespaces=NS):
                    nodos = p.xpath(".//w:t", namespaces=NS)
                    texto = "".join(n.text or "" for n in nodos)
                    coincidencias = list(PATRON.finditer(texto))
                    posiciones, pos = [], 0
                    for n in nodos:
                        posiciones.append(pos)
                        pos += len(n.text or "")
                    for m in reversed(coincidencias):
                        clave = normalizar(m.group(1))
                        if clave not in datos:
                            pendientes.add(clave)
                            continue
                        a = next(i for i, n in enumerate(nodos) if posiciones[i] <= m.start() < posiciones[i] + len(n.text or ""))
                        b = next(i for i, n in enumerate(nodos) if posiciones[i] < m.end() <= posiciones[i] + len(n.text or ""))
                        antes = (nodos[a].text or "")[:m.start()-posiciones[a]]
                        despues = (nodos[b].text or "")[m.end()-posiciones[b]:]
                        nodos[a].text = antes + datos[clave] + (despues if a == b else "")
                        nodos[a].set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
                        if a != b:
                            for j in range(a+1, b):
                                nodos[j].text = ""
                            nodos[b].text = despues
                            nodos[b].set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
                        usados.add(clave)
                        cantidad += 1
                        modificado = True
                    if "NOF" in datos and any(normalizar(m.group(1)) == "NOF" for m in coincidencias):
                        fijar_campo_filename(p)
                if modificado:
                    contenido = etree.tostring(raiz, xml_declaration=True, encoding="UTF-8", standalone=True)
            dst.writestr(info, contenido)
    with ZipFile(destino) as z:
        if z.testzip() is not None:
            raise ValueError("La comprobación del DOCX generado ha fallado.")
    restantes = marcadores_plantilla(destino)
    if restantes != pendientes:
        raise ValueError("Quedan marcadores inesperados en el documento; revisa los valores de la matriz.")
    return cantidad, usados, pendientes

class Cancelado(Exception):
    """El usuario ha cancelado un diálogo."""


def ruta_salida(excel, nof):
    if (not nof or nof != nof.strip() or nof.endswith('.')
            or re.search(r'[<>:"/\\|?*\x00-\x1f]', nof)
            or re.match(r'^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\.|$)', nof, re.I)):
        raise ValueError('El NOF no es un nombre válido de archivo en Windows. Corrige el valor en CT.')
    return excel.parent / ('CT-' + nof + '.docx')


def guardar_resultado(plantilla, destino, datos, confirmar):
    # Generación provisional: un fallo o cancelación conserva la salida anterior.
    with tempfile.TemporaryDirectory(prefix='ct_', dir=destino.parent) as tmp:
        provisional = Path(tmp) / 'resultado.docx'
        resultado = rellenar_word(plantilla, provisional, datos)
        existe = destino.exists()
        if existe and not confirmar(destino):
            raise Cancelado()
        try:
            if existe:
                os.replace(provisional, destino)
            else:
                # En Windows rename falla si aparece una salida concurrente.
                os.rename(provisional, destino)
        except PermissionError:
            raise ValueError('No se puede guardar el Word. Ciérralo si está abierto y comprueba los permisos de la carpeta.') from None
    return resultado


def main():
    import tkinter as tk
    from tkinter import filedialog, messagebox, simpledialog
    root = tk.Tk()
    root.title('Generador de características técnicas')
    root.geometry('570x150')
    root.resizable(False, False)
    estado = tk.StringVar(value='Selecciona el archivo Excel para generar el Word.')
    tk.Label(root, textvariable=estado, wraplength=530, padx=20, pady=25).pack()
    root.update()

    def elegir_matriz(opciones):
        lista = '\n'.join(f'{i}. NOF en fila {f}, columna {c}' for i, (f, c) in enumerate(opciones, 1))
        return simpledialog.askinteger('Elegir matriz', lista + '\n\nNúmero de matriz:',
            parent=root, minvalue=1, maxvalue=len(opciones))

    try:
        if os.name != 'nt':
            raise ValueError('Este script requiere Windows y Microsoft Excel instalado.')
        try:
            import lxml.etree
            import win32com.client
        except ImportError:
            raise ValueError('Faltan dependencias. Ejecuta en PowerShell:\npy -m pip install pywin32 lxml') from None
        seleccion = filedialog.askopenfilename(parent=root,
            title='Selecciona el Excel que contiene la pestaña CT',
            initialdir=str(CARPETA_EXCEL if CARPETA_EXCEL.is_dir() else Path.home()),
            filetypes=[('Excel y plantillas', '*.xlsx *.xlsm *.xlsb *.xls *.xltx *.xltm *.xlt'), ('Todos los archivos', '*.*')])
        if not seleccion:
            raise Cancelado()
        excel = Path(seleccion)
        if excel.suffix.lower() not in ('.xlsx', '.xlsm', '.xlsb', '.xls', '.xltx', '.xltm', '.xlt'):
            raise ValueError('Selecciona un libro o una plantilla de Excel.')
        plantilla = localizar(CARPETA_WORD, NOMBRE_WORD, ('.docx',))
        estado.set('Se abrirá Excel. Introduce la contraseña en la ventana de Excel si la solicita…')
        root.update_idletasks()
        marcadores = marcadores_plantilla(plantilla)
        datos, originales, vacios = leer_excel(excel, CAMPOS | marcadores, elegir_matriz)
        datos = aplicar_reglas(datos, originales)
        vacios = [campo for campo in vacios if campo not in datos]
        destino = ruta_salida(excel, datos['NOF'])
        if destino.resolve() in (plantilla.resolve(), excel.resolve()):
            raise ValueError('La salida coincide con un archivo de origen. Cambia el NOF o la ubicación del Excel.')
        estado.set('Generando el documento Word…')
        root.update_idletasks()
        cantidad, usados, pendientes = guardar_resultado(plantilla, destino, datos,
            lambda ruta: messagebox.askyesno('El Word ya existe',
                f'Ya existe:\n{ruta}\n\n¿Quieres sustituirlo?', parent=root))
        lineas = [f'Documento creado:\n{destino}', f'Sustituciones: {cantidad}']
        if pendientes:
            lineas.append('Marcadores pendientes: ' + ', '.join(sorted(pendientes)))
        if vacios:
            lineas.append('Campos vacíos en Excel: ' + ', '.join(vacios))
        if set(datos) - usados:
            lineas.append('Sin marcador en la plantilla: ' + ', '.join(sorted(set(datos) - usados)))
        if 'LONG_MANGA' in datos:
            lineas.append('Longitud de manga: ' + datos['LONG_MANGA'] + ' mm')
        lineas.append('Revisa el formato y los saltos de página del Word antes de distribuirlo.')
        estado.set('Documento terminado.')
        messagebox.showinfo('Word generado', '\n\n'.join(lineas), parent=root)
        if messagebox.askyesno('Abrir carpeta', '¿Quieres abrir la carpeta del documento?', parent=root):
            os.startfile(str(destino.parent))
    except (Cancelado, KeyboardInterrupt, EOFError):
        pass
    except Exception as error:
        messagebox.showerror('No se pudo generar el Word', str(error), parent=root)
    finally:
        root.destroy()


if __name__ == '__main__':
    main()
