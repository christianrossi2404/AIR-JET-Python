#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generador de características técnicas. Python 3.10+ / Windows / Excel instalado.

Instalación (una vez, en PowerShell):
    py -m pip install pywin32 lxml
Ejecución:
    py rellenar_caracteristicas_tecnicas.py

Interfaz gráfica: selecciona uno o varios archivos (Ctrl/Mayús).
Excel solicita la contraseña de cada libro en su propia ventana.
Se genera un único Word, con un bloque de la plantilla por Excel y salto de página.
Un diálogo permite elegir el nombre y la carpeta de salida. El script no recibe ni guarda la contraseña.
El libro se abre de solo lectura, sin actualizar vínculos ni ejecutar macros VBA.
La plantilla y el Excel originales nunca se guardan ni sobrescriben.
La hoja CT debe contener nombres de campo y valores en dos columnas contiguas.
Se detecta la columna que contiene NOF. Si hay varias matrices, se pide elegir.
Si fuera necesario, fija RANGO_MATRIZ, por ejemplo 'A1:B34'.
No requiere ChatGPT, una API ni Microsoft Word para generar el DOCX.
"""
from __future__ import annotations

import os
import posixpath
from copy import deepcopy
import re
import sys
import tempfile
from decimal import Decimal, InvalidOperation
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

CARPETA_WORD = Path(r"Y:\COSTES\PLANTILLAS")
NOMBRE_WORD = "CARACTERISTICAS TECNICAS"
CARPETA_EXCEL = Path(r"Y:\DOCS COMERCIAL\OFERTAS")
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
            if info.filename == "[Content_Types].xml":
                # La entrada es una plantilla DOTX; la salida es un documento DOCX.
                tipos = etree.fromstring(contenido)
                for parte in tipos:
                    if parte.get("PartName") == "/word/document.xml":
                        parte.set("ContentType", "application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml")
                contenido = etree.tostring(tipos, xml_declaration=True, encoding="UTF-8", standalone=True)
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


def unir_documentos(documentos, destino):
    """Une copias de la misma plantilla, conservando sus secciones y cabeceras.

    Las imágenes, estilos y numeraciones proceden de una plantilla común.
    Cada bloque recibe sus propias cabeceras y pies ya rellenados.
    """
    from lxml import etree
    R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
    REL = "http://schemas.openxmlformats.org/package/2006/relationships"
    CT = "http://schemas.openxmlformats.org/package/2006/content-types"
    if not documentos:
        raise ValueError('No hay documentos para unir.')
    with ZipFile(documentos[0]) as z:
        partes = {n: z.read(n) for n in z.namelist()}
    raiz = etree.fromstring(partes['word/document.xml'])
    cuerpo = raiz.find(f'{{{W}}}body')
    if cuerpo is None:
        raise ValueError('La plantilla no contiene un cuerpo Word válido.')
    for hijo in list(cuerpo):
        cuerpo.remove(hijo)
    relaciones = etree.fromstring(partes['word/_rels/document.xml.rels'])
    tipos = etree.fromstring(partes['[Content_Types].xml'])
    ids = {r.get('Id') for r in relaciones}
    siguiente_id = 1
    dibujo_id = 0
    marcador_id = 0
    for indice, ruta in enumerate(documentos, 1):
        with ZipFile(ruta) as z:
            documento = etree.fromstring(z.read('word/document.xml'))
            bloque = documento.find(f'{{{W}}}body')
            rels = etree.fromstring(z.read('word/_rels/document.xml.rels'))
            por_id = {r.get('Id'): r for r in rels}
            referencias = {}
            for referencia in bloque.xpath('.//w:headerReference | .//w:footerReference', namespaces=NS):
                antiguo = referencia.get(f'{{{R}}}id')
                if antiguo not in referencias:
                    relacion = deepcopy(por_id[antiguo])
                    origen = posixpath.normpath(posixpath.join('word', relacion.get('Target')))
                    if origen.startswith('/'):
                        origen = origen.lstrip('/')
                    extension = Path(origen).suffix
                    base = posixpath.basename(origen)[:-len(extension)]
                    nuevo = f'word/{base}_bloque_{indice}{extension}'
                    contador = 1
                    while nuevo in partes:
                        nuevo = f'word/{base}_bloque_{indice}_{contador}{extension}'
                        contador += 1
                    partes[nuevo] = z.read(origen)
                    # Las relaciones siguen apuntando a los recursos de la plantilla.
                    rel_origen = posixpath.join(posixpath.dirname(origen), '_rels', posixpath.basename(origen) + '.rels')
                    if rel_origen in z.namelist():
                        rel_nueva = posixpath.join('word/_rels', posixpath.basename(nuevo) + '.rels')
                        partes[rel_nueva] = z.read(rel_origen)
                    while f'rId{siguiente_id}' in ids:
                        siguiente_id += 1
                    nuevo_id = f'rId{siguiente_id}'
                    ids.add(nuevo_id)
                    relacion.set('Id', nuevo_id)
                    relacion.set('Target', posixpath.basename(nuevo))
                    relaciones.append(relacion)
                    tipo = next((t.get('ContentType') for t in tipos if t.get('PartName') == '/' + origen), None)
                    if tipo is None:
                        raise ValueError('Falta el tipo de contenido de una cabecera o pie.')
                    etree.SubElement(tipos, f'{{{CT}}}Override', PartName='/' + nuevo, ContentType=tipo)
                    referencias[antiguo] = nuevo_id
                referencia.set(f'{{{R}}}id', referencias[antiguo])
            # Evita IDs repetidos de dibujos y marcadores en el documento conjunto.
            marcadores = {}
            for nodo in bloque.iter():
                if etree.QName(nodo).localname == 'docPr':
                    dibujo_id += 1
                    nodo.set('id', str(dibujo_id))
                if nodo.tag == f'{{{W}}}bookmarkStart':
                    marcador_id += 1
                    antiguo = nodo.get(f'{{{W}}}id')
                    marcadores[antiguo] = str(marcador_id)
                    nodo.set(f'{{{W}}}id', str(marcador_id))
                elif nodo.tag == f'{{{W}}}bookmarkEnd':
                    antiguo = nodo.get(f'{{{W}}}id')
                    if antiguo in marcadores:
                        nodo.set(f'{{{W}}}id', marcadores[antiguo])
            seccion = bloque.find(f'{{{W}}}sectPr')
            if seccion is not None:
                bloque.remove(seccion)
            else:
                seccion = etree.Element(f'{{{W}}}sectPr')
            # El bloque siguiente comienza en una página nueva.
            tipo_salto = seccion.find(f'{{{W}}}type')
            if tipo_salto is None:
                tipo_salto = etree.SubElement(seccion, f'{{{W}}}type')
            tipo_salto.set(f'{{{W}}}val', 'nextPage')
            for hijo in list(bloque):
                cuerpo.append(hijo)
            if indice < len(documentos):
                parrafo = etree.SubElement(cuerpo, f'{{{W}}}p')
                propiedades = etree.SubElement(parrafo, f'{{{W}}}pPr')
                propiedades.append(seccion)
            else:
                cuerpo.append(seccion)
    for nombre, xml in [('word/document.xml', raiz),
                        ('word/_rels/document.xml.rels', relaciones),
                        ('[Content_Types].xml', tipos)]:
        partes[nombre] = etree.tostring(xml, xml_declaration=True, encoding='UTF-8', standalone=True)
    with ZipFile(destino, 'x', ZIP_DEFLATED) as z:
        for nombre, contenido in partes.items():
            z.writestr(nombre, contenido)
    with ZipFile(destino) as z:
        if z.testzip() is not None:
            raise ValueError('La comprobación del Word conjunto ha fallado.')


def guardar_resultado(plantilla, destino, registros, confirmar):
    # Todo se prepara antes de sustituir una salida existente.
    with tempfile.TemporaryDirectory(prefix='ct_', dir=destino.parent) as tmp:
        documentos, resultados = [], []
        for indice, datos in enumerate(registros, 1):
            parcial = Path(tmp) / f'bloque_{indice}.docx'
            resultados.append(rellenar_word(plantilla, parcial, datos))
            documentos.append(parcial)
        provisional = Path(tmp) / 'resultado.docx'
        if len(documentos) == 1:
            os.rename(documentos[0], provisional)
        else:
            unir_documentos(documentos, provisional)
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
    return resultados


def main():
    import tkinter as tk
    from tkinter import filedialog, messagebox, simpledialog
    root = tk.Tk()
    root.title('Generador de características técnicas')
    root.geometry('570x150')
    root.resizable(False, False)
    estado = tk.StringVar(value='Selecciona uno o varios archivos Excel para generar un único Word.')
    tk.Label(root, textvariable=estado, wraplength=530, padx=20, pady=25).pack()
    root.update()

    def elegir_matriz(opciones, archivo):
        lista = '\n'.join(f'{i}. NOF en fila {f}, columna {c}' for i, (f, c) in enumerate(opciones, 1))
        return simpledialog.askinteger('Elegir matriz', archivo + '\n\n' + lista + '\n\nNúmero de matriz:',
            parent=root, minvalue=1, maxvalue=len(opciones))

    try:
        if os.name != 'nt':
            raise ValueError('Este script requiere Windows y Microsoft Excel instalado.')
        try:
            import lxml.etree
            import win32com.client
        except ImportError:
            raise ValueError('Faltan dependencias. Ejecuta en PowerShell:\npy -m pip install pywin32 lxml') from None
        seleccion = filedialog.askopenfilenames(parent=root,
            title='Selecciona los Excel con pestaña CT (Ctrl o Mayús para seleccionar varios)',
            initialdir=str(CARPETA_EXCEL if CARPETA_EXCEL.is_dir() else Path.home()),
            filetypes=[('Excel y plantillas', '*.xlsx *.xlsm *.xlsb *.xls *.xltx *.xltm *.xlt'), ('Todos los archivos', '*.*')])
        if not seleccion:
            raise Cancelado()
        archivos = [Path(ruta) for ruta in seleccion]
        extensiones = ('.xlsx', '.xlsm', '.xlsb', '.xls', '.xltx', '.xltm', '.xlt')
        for excel in archivos:
            if excel.suffix.lower() not in extensiones:
                raise ValueError(f'{excel.name}: selecciona un libro o una plantilla de Excel.')
        plantilla = localizar(CARPETA_WORD, NOMBRE_WORD, ('.dotx',))
        marcadores = marcadores_plantilla(plantilla)
        registros, vacios_por_archivo = [], []
        for indice, excel in enumerate(archivos, 1):
            estado.set(f'Leyendo {indice}/{len(archivos)}: {excel.name}. Introduce la contraseña en Excel si la solicita…')
            root.update_idletasks()
            try:
                datos, originales, vacios = leer_excel(excel, CAMPOS | marcadores,
                    lambda opciones, nombre=excel.name: elegir_matriz(opciones, nombre))
                datos = aplicar_reglas(datos, originales)
            except Cancelado:
                raise
            except Exception as error:
                raise ValueError(f'{excel.name}: {error}') from error
            registros.append(datos)
            vacios_por_archivo.append([campo for campo in vacios if campo not in datos])
        sugerido = (ruta_salida(archivos[0], registros[0]['NOF']).name
                    if len(archivos) == 1 else 'CT-CONJUNTO.docx')
        salida = filedialog.asksaveasfilename(parent=root,
            title='Guardar el documento Word conjunto',
            initialdir=str(archivos[0].parent), initialfile=sugerido,
            defaultextension='.docx', filetypes=[('Documento Word', '*.docx')],
            confirmoverwrite=False)
        if not salida:
            raise Cancelado()
        destino = Path(salida)
        if destino.suffix.lower() != '.docx':
            raise ValueError('La salida debe tener extensión .docx.')
        if destino.resolve() in {p.resolve() for p in [plantilla, *archivos]}:
            raise ValueError('La salida coincide con un archivo de origen. Elige otro nombre.')
        estado.set(f'Generando un único Word con {len(archivos)} archivo(s) Excel…')
        root.update_idletasks()
        resultados = guardar_resultado(plantilla, destino, registros,
            lambda ruta: messagebox.askyesno('El Word ya existe',
                f'Ya existe:\n{ruta}\n\n¿Quieres sustituirlo?', parent=root))
        lineas = [f'Documento creado:\n{destino}',
                  f'Archivos Excel incluidos: {len(archivos)}',
                  f'Sustituciones totales: {sum(r[0] for r in resultados)}']
        for indice, (excel, datos, vacios, resultado) in enumerate(
                zip(archivos, registros, vacios_por_archivo, resultados), 1):
            cantidad, usados, pendientes = resultado
            detalle = [f'{indice}. {excel.name} — NOF: {datos["NOF"]}']
            if pendientes:
                detalle.append('Marcadores pendientes: ' + ', '.join(sorted(pendientes)))
            if vacios:
                detalle.append('Campos vacíos en Excel: ' + ', '.join(vacios))
            if set(datos) - usados:
                detalle.append('Sin marcador en la plantilla: ' + ', '.join(sorted(set(datos) - usados)))
            if 'LONG_MANGA' in datos:
                detalle.append('Longitud de manga: ' + datos['LONG_MANGA'] + ' mm')
            lineas.append('\n'.join(detalle))
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
