"""Calculadora de pesos de filtros circulares. Python 3 + Tkinter.

Ejecutar: python Calculadora_filtros.py
Comprobar fórmulas sin abrir ventanas: python Calculadora_filtros.py --test
Para exportar Excel con dibujo: python -m pip install openpyxl pillow

Fuente: Cálculo de pesos.xls aportado por el usuario.
Geometría en mm, resultados en kg, densidad conservada: 8.000 kg/m³.
Se usa math.pi y la tolva se mide desde la vertical.
Los coeficientes empíricos y pesos fijos del original se conservan.
Ambas cámaras usan cilindro completo y su propio espesor independiente.
No descuenta aberturas ni añade elementos que no estaban en el archivo.
"""
import json
import math
import re
import sys

DENSIDAD = 8000.0
# Secciones, claves, etiquetas, valor inicial y unidad de la tabla solicitada.
SECCIONES = [
    ('CAL', [
        ('valvulas', 'CANTIDAD VALVULAS', 18, ''),
        ('diametro', 'DIAMETRO CUERPO', 3800, 'mm'),
        ('fondo', 'ESPESOR FONDO', 10, 'mm'),
        ('altura_cal', 'ALTURA C.A.L', 2976, 'mm'),
        ('espesor_cal', 'ESPESOR C.A.L', 6, 'mm'),
        ('salida', 'DIAMETRO BOCA SALIDA', 800, 'mm'),
        ('hileras', 'CANTIDAD HILERAS MANGAS', 18, ''),
        ('bridas', 'PASAMANOS BRIDAS', 2400, 'AxB mm'),
    ]),
    ('CAS', [
        ('altura_cas', 'ALTURA C.A.S', 3680, 'mm'),
        ('espesor_cas', 'ESPESOR C.A.S', 6, 'mm'),
    ]),
    ('TOLVA', [
        ('diametro_tolva', 'DIAMETRO TOLVA', 3800, 'mm'),
        ('angulo', 'INCLINACION TOLVA (20-30º)', 20, '° desde vertical'),
        ('espesor_tolva', 'ESPESOR TOLVA', 5, 'mm'),
        ('entrada', 'DIAMETRO BOCA ENTRADA', 800, 'mm'),
        ('descarga', 'DIAMETRO BOCA DESCARGA', 250, 'mm'),
        ('pescante', 'PESCANTE FONDO', 0, 'cant.'),
        ('registro', 'REGISTRO CONVENCIONAL', 1, 'cant.'),
        ('registro_pescante', 'REGISTRO CON PESCANTE', 0, 'cant.'),
        ('reja', 'REJA CAIDA MANGAS', 0, 'cant.'),
        ('plataforma', 'SOPORTES PLATAFORMA', 0, 'cant.'),
        ('marcos', 'MARCOS PUERTAS EXPLOS.', 4, 'cant.'),
    ]),
    ('CUERPO CICLÓNICO', [
        ('altura_ciclonica', 'ALTURA CUERPO CICLÓNICO', 0, 'mm'),
    ]),
]
CAMPOS = {clave: (etiqueta, valor, unidad)
          for _, filas in SECCIONES for clave, etiqueta, valor, unidad in filas}
ENTEROS = {'valvulas', 'hileras', 'pescante', 'registro', 'registro_pescante',
           'reja', 'plataforma', 'marcos'}
POSITIVOS = {'diametro', 'fondo', 'altura_cal', 'espesor_cal', 'altura_cas',
             'espesor_cas', 'diametro_tolva', 'espesor_tolva', 'descarga', 'bridas'}


def numero(texto):
    """Acepta 3.800, 3.800,5 y 3800.5. Un punto seguido de 3 cifras es millar."""
    s = str(texto).strip().replace(' ', '').replace('\u00a0', '')
    if not s:
        raise ValueError('Introduce un número.')
    if ',' in s:
        if not re.fullmatch(r'[+-]?(?:\d+|\d{1,3}(?:\.\d{3})+)(?:,\d+)?', s):
            raise ValueError('Formato incorrecto. Ejemplo: 3.800,5.')
        s = s.replace('.', '').replace(',', '.')
    elif re.fullmatch(r'[+-]?\d{1,3}(?:\.\d{3})+', s):
        s = s.replace('.', '')
    elif not re.fullmatch(r'[+-]?\d+(?:\.\d+)?', s):
        raise ValueError('Formato incorrecto. Ejemplo: 3800 o 3.800,5.')
    valor = float(s)
    if not math.isfinite(valor):
        raise ValueError('El número debe ser finito.')
    return valor


def formato(valor, decimales=2):
    return f'{valor:,.{decimales}f}'.replace(',', '_').replace('.', ',').replace('_', '.')


def validar(p):
    for clave, (etiqueta, _, _) in CAMPOS.items():
        v = p[clave]
        if not math.isfinite(v) or v < 0:
            raise ValueError(f'{etiqueta}: introduce un número no negativo.')
        if clave in POSITIVOS and v <= 0:
            raise ValueError(f'{etiqueta}: debe ser mayor que cero.')
        if clave in ENTEROS and not v.is_integer():
            raise ValueError(f'{etiqueta}: debe ser un número entero.')
    if not 0 < p['angulo'] < 90:
        raise ValueError('INCLINACION TOLVA: debe estar entre 0° y 90°, sin incluir extremos.')
    if p['descarga'] >= p['diametro_tolva']:
        raise ValueError('La boca de descarga debe ser menor que el diámetro de la tolva.')


FORMULAS = [('CAL-01', 'CAL', 'Fondo (coeficiente original)', 'diametro / 700 * 0.006 * diametro * fondo'), ('CAL-02', 'CAL', 'Cuerpo cilíndrico C.A.L.', 'pi * (diametro / 1000) * (altura_cal / 1000) * (espesor_cal / 1000) * DENSIDAD'), ('CAL-03', 'CAL', 'Boca salida', 'salida / 1000 * pi * 0.15 * (DENSIDAD / 1000) * espesor_cal * 1.75'), ('CAL-04', 'CAL', 'Orejetas', 'diametro * 0.018'), ('CAL-05', 'CAL', 'Brida', 'diametro / 1000 * pi * DENSIDAD * bridas * 1e-06'), ('CAL-06', 'CAL', 'Tubos inyectores', 'hileras * (diametro / 1000 + 0.27) * 2.22'), ('CAL-07', 'CAL', 'Soportes tubos', 'valvulas'), ('CAL-08', 'CAL', 'Soportes colector', 'valvulas / 6 * 4'), ('CAL-09', 'CAL', 'Casquillos tubos', 'valvulas * 0.4'), ('CAL-10', 'CAL', 'Pescante fondo', 'pescante * 110'), ('CAL-11', 'CAL', 'Conexión manómetro', '0.6'), ('CAS-01', 'CAS', 'Cuerpo cilíndrico C.A.S. (F15 original)', 'pi * (diametro / 1000) * (altura_cas / 1000) * (espesor_cas / 1000) * DENSIDAD'), ('CAS-02', 'CAS', 'Brida', 'diametro / 1000 * pi * DENSIDAD * bridas * 1e-06'), ('CAS-03', 'CAS', 'Cartelas apoyo', 'diametro * 0.05'), ('CAS-04', 'CAS', 'Registro convencional', 'registro * 130'), ('CAS-05', 'CAS', 'Registro con pescante', 'registro_pescante * 120'), ('CAS-06', 'CAS', 'Conexión manómetro', '0.6'), ('CAS-07', 'CAS', 'Reja caída mangas', '(diametro / 1000 / 2) ** 2 * pi * 15 * reja'), ('CAS-08', 'CAS', 'Soportes plataforma', 'diametro * 0.065 * plataforma'), ('CAS-09', 'CAS', 'Marcos puertas explosión', 'marcos * 40'), ('CAS-10', 'CAS', 'Cuerpo ciclónico', 'diametro_tolva / 1000 * pi * altura_ciclonica / 1000 * espesor_tolva * (DENSIDAD / 1000)'), ('CAS-11', 'CAS', 'Tapa cuerpo ciclónico', 'abs((diametro_tolva / 1000 / 2) ** 2 - (diametro / 1000 / 2) ** 2) * pi * espesor_tolva * (DENSIDAD / 1000)'), ('CAS-12', 'CAS', 'Anilla seguridad', 'reja * 0.3'), ('CAS-13', 'CAS', 'Cartelas refuerzo tolva', 'altura_ciclonica / 1000 * abs(diametro_tolva / 1000 - diametro / 1000) / 2 * 6 * (DENSIDAD / 1000) * 8'), ('TOLVA-01', 'TOLVA', 'Cuerpo cónico', 'pi * (diametro_tolva / 1000 + descarga / 1000) / 2 * ((diametro_tolva / 1000 - descarga / 1000) / 2 / sin(radians(angulo))) * espesor_tolva * (DENSIDAD / 1000)'), ('TOLVA-02', 'TOLVA', 'Cuello descarga (coeficiente original)', 'descarga / 1000 * pi * 0.06 * espesor_tolva * (DENSIDAD / 1000) * 2.5'), ('TOLVA-03', 'TOLVA', 'Boca entrada (coeficiente original)', 'entrada / 1000 * pi * 0.5 * espesor_tolva * (DENSIDAD / 1000) * 1.5')]

def evaluar_formula(texto, variables):
    """Intérprete aritmético limitado: nunca ejecuta código Python del usuario."""
    import ast
    import operator
    operaciones = {ast.Add: operator.add, ast.Sub: operator.sub,
                   ast.Mult: operator.mul, ast.Div: operator.truediv, ast.Pow: operator.pow}
    funciones = {'abs': abs, 'sin': math.sin, 'radians': math.radians}
    if not isinstance(texto, str) or len(texto) > 2000:
        raise ValueError('Fórmula demasiado larga o no válida.')
    def visitar(n):
        if isinstance(n, ast.Constant) and type(n.value) in (int, float):
            v = float(n.value)
        elif isinstance(n, ast.Name) and n.id in variables:
            v = variables[n.id]
        elif isinstance(n, ast.UnaryOp) and isinstance(n.op, (ast.USub, ast.UAdd)):
            v = visitar(n.operand) * (-1 if isinstance(n.op, ast.USub) else 1)
        elif isinstance(n, ast.BinOp) and type(n.op) in operaciones:
            a, b = visitar(n.left), visitar(n.right)
            if isinstance(n.op, ast.Pow) and abs(b) > 12:
                raise ValueError('El exponente debe estar entre -12 y 12.')
            v = operaciones[type(n.op)](a, b)
        elif (isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
              and n.func.id in funciones and len(n.args) == 1 and not n.keywords):
            v = funciones[n.func.id](visitar(n.args[0]))
        else:
            raise ValueError('Usa variables conocidas, números, + - * / **, abs, sin y radians.')
        if isinstance(v, complex) or not math.isfinite(v) or abs(v) > 1e100:
            raise ValueError('Resultado fuera de límites.')
        return v
    try:
        nodo = ast.parse(texto.strip(), mode='eval')
        if sum(1 for _ in ast.walk(nodo)) > 400:
            raise ValueError('Fórmula demasiado compleja.')
        return visitar(nodo.body)
    except (SyntaxError, ArithmeticError, RecursionError, TypeError) as exc:
        raise ValueError('Fórmula no válida: revisa sintaxis, divisores y valores.') from exc


def calcular(p, formulas=None):
    p = {k: float(p[k]) for k in CAMPOS}
    validar(p)
    formulas = {} if formulas is None else formulas
    if not isinstance(formulas, dict) or set(formulas) - {r[0] for r in FORMULAS}:
        raise ValueError('Lista de fórmulas no compatible.')
    variables = dict(p, DENSIDAD=DENSIDAD, pi=math.pi, diametro_ciclonico=p['diametro_tolva'])
    resultado = {'CAL': [], 'CAS': [], 'TOLVA': []}
    for clave, seccion, nombre, original in FORMULAS:
        try:
            valor = evaluar_formula(formulas.get(clave, original), variables)
            if valor < 0:
                raise ValueError('El peso no puede ser negativo.')
        except ValueError as exc:
            raise ValueError(f'{clave} · {nombre}: {exc}') from exc
        resultado[seccion].append((nombre, valor))
    return resultado


def dibujo_informe(p):
    """PNG en memoria para el Excel; alzado con una única escala geométrica."""
    from io import BytesIO
    from PIL import Image, ImageDraw, ImageFont
    imagen = Image.new('RGB', (1000, 1380), 'white')
    trazo = ImageDraw.Draw(imagen)
    def fuente(tamano):
        for nombre in ('DejaVuSans.ttf', 'Arial.ttf', 'arial.ttf'):
            try:
                return ImageFont.truetype(nombre, tamano)
            except OSError:
                pass
        return ImageFont.load_default()
    normal, titulo = fuente(22), fuente(24)
    d, dc, dt, dd = (p[k] for k in ('diametro', 'diametro_tolva', 'diametro_tolva', 'descarga'))
    hc, hs, hy = (p[k] for k in ('altura_cal', 'altura_cas', 'altura_ciclonica'))
    ht = (dt-dd)/2/math.tan(math.radians(p['angulo']))
    escala = min(430/max(d, dc, dt), 1050/(hc+hs+hy+ht))
    x, y0 = 250, 110
    y1, y2 = y0+hc*escala, y0+(hc+hs)*escala
    y3, y4 = y2+hy*escala, y2+(hy+ht)*escala
    r, rc, rt, rd = [n*escala/2 for n in (d, dc, dt, dd)]
    borde = '#233d59'
    trazo.text((30, 20), 'ALZADO DEL FILTRO', font=titulo, fill=borde)
    trazo.line((x, 75, x, y4+35), fill='#c0cbd6', width=2)
    trazo.rectangle((x-r, y0-5, x+r, y0), fill='#6d8198', outline=borde, width=3)
    trazo.rectangle((x-r, y0, x+r, y1), fill='#dce9f8', outline=borde, width=3)
    trazo.rectangle((x-r, y1, x+r, y2), fill='#b9d3ec', outline=borde, width=3)
    trazo.line((x-r, y2, x-rc, y2), fill=borde, width=3)
    trazo.line((x+r, y2, x+rc, y2), fill=borde, width=3)
    if hy>0:
        trazo.rectangle((x-rc, y2, x+rc, y3), fill='#c1dfd8', outline=borde, width=3)
    trazo.polygon([(x-rt,y3),(x+rt,y3),(x+rd,y4),(x-rd,y4)], fill='#f7dfb5', outline=borde, width=3)
    if dc!=dt:
        for signo in (-1,1):
            trazo.line((x+signo*rc,y3,x+signo*rt,y3), fill='#c67922', width=5)
    datos = [
        (y0, r, 'FONDO', f'e = {formato(p["fondo"],1)} mm'),
        ((y0+y1)/2, r, 'CILINDRO CAL', f'Ø {formato(d,0)} · H {formato(hc,0)} mm'),
        ((y1+y2)/2, r, 'CILINDRO CAS', f'Ø {formato(d,0)} · H {formato(hs,0)} mm'),
        ((y2+y3)/2, rc, 'CUERPO CICLÓNICO', f'Ø {formato(dc,0)} · H {formato(hy,0)} mm'),
        ((y3+y4)/2, (rt+rd)/2, 'CUERPO CÓNICO', f'H {formato(ht,0)} mm · {formato(p["angulo"],1)}°'),
    ]
    anterior = -100
    for ancla, radio, nombre, detalle in datos:
        pos = max(ancla, anterior+95)
        anterior = pos
        trazo.line((x+radio,ancla,520,pos), fill='#8293a6', width=2)
        trazo.text((540,pos-20),nombre,font=titulo,fill=borde)
        trazo.text((540,pos+18),detalle,font=normal,fill='#435267')
    trazo.text((35,1200),f'Descarga Ø {formato(dd,0)} mm. Ángulo desde la vertical.',font=normal,fill=borde)
    trazo.text((35,1240),'Diámetros y alturas a escala. Espesores exagerados.',font=normal,fill='#435267')
    trazo.text((35,1280),'Sin bocas laterales, bridas ni accesorios.',font=normal,fill='#435267')
    if dc!=dt:
        trazo.text((35,1320),'Unión naranja pendiente de definir. Peso no incluido.',font=normal,fill='#9a5913')
    contenido = BytesIO()
    imagen.save(contenido, format='PNG')
    contenido.seek(0)
    return contenido


def exportar_excel(ruta, p, modelo='', formulas=None):
    """Informe XLSX de los resultados calculados; el dibujo es una captura del caso exportado."""
    from datetime import datetime
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.drawing.image import Image
    from openpyxl.worksheet.pagebreak import Break
    resultado = calcular(p, formulas)
    libro = Workbook()
    hoja = libro.active
    hoja.title = 'Informe'
    entradas = libro.create_sheet('Datos del filtro')
    azul, claro, gris = '233D59', 'E8EEF5', '53657A'
    def celda(sh, fila, col, valor, fondo=None, negrita=False, color='243247'):
        c = sh.cell(fila,col,valor)
        c.font = Font(name='Calibri',size=11,bold=negrita,color=color)
        c.alignment = Alignment(vertical='center',wrap_text=isinstance(valor,str))
        if fondo:
            c.fill = PatternFill('solid',fgColor=fondo)
        if isinstance(valor,(int,float)):
            c.number_format = '#,##0.00'
            c.alignment = Alignment(horizontal='right',vertical='center')
        return c
    for sh in (hoja,entradas):
        sh.sheet_view.showGridLines = False
        sh.sheet_properties.pageSetUpPr.fitToPage = True
        sh.page_setup.orientation = 'landscape'
        sh.page_setup.paperSize = sh.PAPERSIZE_A3
        sh.page_setup.fitToWidth = 1
        sh.page_setup.fitToHeight = 1
        sh.oddFooter.center.text = 'Página &P de &N'
        sh.oddFooter.right.text = 'Cálculo de pesos'
        sh.sheet_properties.outlinePr.summaryRight = False
        sh.sheet_properties.pageSetUpPr.fitToPage = True
    hoja.sheet_properties.tabColor = azul
    hoja.column_dimensions['A'].width = 51
    hoja.column_dimensions['B'].width = 17
    hoja.column_dimensions['C'].width = 4
    for col in 'DEFGHI':
        hoja.column_dimensions[col].width = 13
    hoja.merge_cells('A2:I2')
    celda(hoja,2,1,'CÁLCULO DE PESOS DEL FILTRO',negrita=True).font = Font(name='Calibri',size=19,bold=True,color=azul)
    hoja.row_dimensions[2].height = 32
    hoja.merge_cells('A3:I3')
    celda(hoja,3,1,f'Modelo: {modelo or "Sin especificar"}     Fecha: {datetime.now():%d/%m/%Y %H:%M}',color=gris)
    hoja.merge_cells('A4:I4')
    celda(hoja,4,1,'Informe de los valores exportados. Datos de partida en la segunda hoja.',color=gris)
    for col, valor in [(1,'SECCIÓN / COMPONENTE'),(2,'PESO (kg)')]:
        celda(hoja,6,col,valor,azul,True,'FFFFFF')
    fila=7
    colores={'CAL':'DCE9F8','CAS':'B9D3EC','TOLVA':'F7DFB5'}
    for seccion,items in resultado.items():
        celda(hoja,fila,1,seccion,colores[seccion],True)
        celda(hoja,fila,2,sum(v for _,v in items),colores[seccion],True)
        fila+=1
        for n,(nombre,peso) in enumerate(items):
            fondo='F4F7FA' if n%2==0 else 'FFFFFF'
            celda(hoja,fila,1,nombre,fondo)
            celda(hoja,fila,2,peso,fondo)
            fila+=1
    fila+=1
    celda(hoja,fila,1,'TOTAL PESO FILTRO (SIN CV)',azul,True,'FFFFFF')
    celda(hoja,fila,2,sum(v for items in resultado.values() for _,v in items),azul,True,'FFFFFF')
    hoja.row_dimensions[fila].height=32
    for r in range(6,fila):
        hoja.row_dimensions[r].height=24
    dibujo = Image(dibujo_informe(p))
    dibujo.width, dibujo.height = 590, 814
    hoja.add_image(dibujo,'D6')
    pie=max(fila+3,45)
    notas = [
        'Densidad: 8.000 kg/m³. CAL y CAS usan sus propios espesores. Cilindros completos.',
        'La tolva usa el ángulo respecto a la vertical. Se conservan los coeficientes empíricos del archivo original.',
        'No se descuentan aberturas. El dibujo representa las dimensiones del caso exportado.',
    ]
    for texto in notas:
        hoja.merge_cells(start_row=pie,start_column=1,end_row=pie,end_column=9)
        celda(hoja,pie,1,texto,color=gris)
        hoja.row_dimensions[pie].height=23
        pie+=1
    hoja.print_area=f'A1:I{pie}'
    hoja.freeze_panes='A7'
    entradas.sheet_properties.tabColor='D6A847'
    entradas.column_dimensions['A'].width=45
    entradas.column_dimensions['B'].width=20
    entradas.column_dimensions['C'].width=23
    entradas.merge_cells('A2:C2')
    celda(entradas,2,1,'DATOS DEL FILTRO',negrita=True).font=Font(name='Calibri',size=17,bold=True,color=azul)
    entradas.row_dimensions[2].height=30
    celda(entradas,4,1,'FILTRO MODELO',negrita=True)
    celda(entradas,4,2,modelo or 'Sin especificar','FFF2CC')
    for col,txt in enumerate(['PARÁMETRO','VALOR','UNIDAD'],1):
        celda(entradas,6,col,txt,azul,True,'FFFFFF')
    f=7
    for seccion,campos in SECCIONES:
        entradas.merge_cells(start_row=f,start_column=1,end_row=f,end_column=3)
        celda(entradas,f,1,seccion,claro,True)
        f+=1
        for clave,etiqueta,_,unidad in campos:
            celda(entradas,f,1,etiqueta)
            celda(entradas,f,2,p[clave],'FFF2CC')
            celda(entradas,f,3,'° desde vertical' if clave=='angulo' else 'mm² (A × B)' if clave=='bridas' else unidad)
            f+=1
    celda(entradas,f+1,1,'DENSIDAD DEL MATERIAL',negrita=True)
    celda(entradas,f+1,2,DENSIDAD)
    celda(entradas,f+1,3,'kg/m³')
    entradas.merge_cells(start_row=f+3,start_column=1,end_row=f+3,end_column=3)
    celda(entradas,f+3,1,'Valores de referencia del informe. Recalcula en la aplicación y exporta de nuevo para actualizar.',color=gris)
    entradas.row_dimensions[f+3].height=40
    for r in range(6,f+2):
        entradas.row_dimensions[r].height=24
    entradas.freeze_panes='B7'
    entradas.print_area=f'A1:C{f+3}'
    entradas.page_setup.paperSize=entradas.PAPERSIZE_A4
    entradas.page_setup.orientation='portrait'
    detalle = libro.create_sheet('Fórmulas por posición')
    detalle.append(['Posición', 'Sección', 'Componente', 'Fórmula aplicada', 'Peso (kg)'])
    pesos = iter(v for items in resultado.values() for _, v in items)
    for clave, seccion, nombre, original in FORMULAS:
        detalle.append([clave, seccion, nombre, (formulas or {}).get(clave, original), next(pesos)])
    for col, ancho in [('A', 14), ('B', 12), ('C', 48), ('D', 110), ('E', 18)]:
        detalle.column_dimensions[col].width = ancho
    detalle.freeze_panes = 'D2'
    detalle.auto_filter.ref = detalle.dimensions
    for row in detalle:
        for cell in row:
            cell.alignment = Alignment(vertical='top', wrap_text=True)
        detalle.row_dimensions[row[0].row].height = 42
    for cell in detalle[1]:
        cell.font = Font(bold=True, color='FFFFFF')
        cell.fill = PatternFill('solid', fgColor=azul)
    detalle.append(['Nota', 'Editar fórmulas en la aplicación y volver a exportar.'])
    libro.save(ruta)


def pruebas():
    import unittest

    class CalculosTest(unittest.TestCase):
        def setUp(self):
            self.p = {k: float(v[1]) for k, v in CAMPOS.items()}

        def test_resultados_verificados(self):
            r = calcular(self.p)
            self.assertAlmostEqual(r['CAS'][0][1], 2108.7375200543843)
            self.assertAlmostEqual(sum(v for _, v in r['TOLVA']), 1400.7418461894856)
            self.assertAlmostEqual(sum(v for items in r.values() for _, v in items), 7692.046169962144)

        def test_geometria_y_espesores_independientes(self):
            r = calcular(self.p)
            self.p['espesor_cas'] = 12
            nuevo = calcular(self.p)
            self.assertAlmostEqual(nuevo['CAS'][0][1], 2*r['CAS'][0][1])
            self.assertEqual(nuevo['CAL'], r['CAL'])
            self.assertEqual(nuevo['TOLVA'], r['TOLVA'])
            self.p['espesor_cas'] = 6
            self.p['espesor_cal'] = 12
            nuevo = calcular(self.p)
            self.assertAlmostEqual(nuevo['CAL'][1][1], 2*r['CAL'][1][1])
            self.assertEqual(nuevo['CAS'], r['CAS'])
            self.assertEqual(nuevo['TOLVA'], r['TOLVA'])
            self.assertAlmostEqual(r['CAL'][1][1], 1705.326864043982)

        def test_formato_y_limites(self):
            for s, v in [('3.800', 3800), ('3.800,5', 3800.5), ('3800.5', 3800.5), ('0,3491', .3491)]:
                self.assertEqual(numero(s), v)
            for s in ['', 'NaN', 'inf', '1.2.3']:
                with self.assertRaises(ValueError):
                    numero(s)
            for k, v in [('angulo', 0), ('angulo', 90), ('valvulas', 1.5), ('fondo', -1), ('descarga', 3800)]:
                with self.assertRaises(ValueError):
                    calcular(dict(self.p, **{k: v}))

        def test_altura_ciclonica_independiente(self):
            inicial = calcular(self.p)
            self.p['altura_ciclonica'] = 1000
            nuevo = calcular(self.p)
            cuerpo = dict(nuevo['CAS'])['Cuerpo ciclónico']
            self.assertAlmostEqual(cuerpo, math.pi*3.8*1*.005*8000)
            self.assertEqual(nuevo['CAL'], inicial['CAL'])
            self.assertEqual(nuevo['TOLVA'], inicial['TOLVA'])
            self.assertEqual(nuevo['CAS'][0], inicial['CAS'][0])

        def test_diametro_ciclonico_vinculado(self):
            self.assertNotIn('diametro_ciclonico', CAMPOS)
            self.p['altura_ciclonica'] = 1000
            for diametro in (4500, 3000):
                self.p['diametro_tolva'] = diametro
                self.p['diametro_ciclonico'] = 9999  # Dato antiguo ignorado.
                nuevo = calcular(self.p)
                self.assertAlmostEqual(dict(nuevo['CAS'])['Cuerpo ciclónico'], math.pi*diametro/1000*.005*8000)
                antiguo = calcular(self.p, {'CAS-10': 'diametro_ciclonico / 1000 * pi * altura_ciclonica / 1000 * espesor_tolva * 8'})
                self.assertEqual(nuevo, antiguo)

    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(CalculosTest))
    return 0 if result.wasSuccessful() else 1


def iniciar():
    try:
        import tkinter as tk
        from tkinter import ttk, filedialog, messagebox
    except ImportError as exc:
        raise SystemExit('Esta aplicación necesita Python con Tkinter. En Windows instala Python con Tcl/Tk. '
                         'En Linux instala el paquete python3-tk de tu distribución.\nDetalle: '+str(exc))

    class Aplicacion(tk.Tk):
        def __init__(self):
            super().__init__()
            self.title('Cálculo de pesos · Filtros circulares')
            self.geometry('1280x880')
            self.minsize(1000, 650)
            self.configure(background='#edf1f6')
            style = ttk.Style(self)
            style.theme_use('clam')
            style.configure('.', font=('Arial', 10))
            style.configure('Titulo.TLabel', font=('Arial', 17, 'bold'), foreground='#233d59')
            style.configure('Seccion.TLabel', background='#233d59', foreground='white', padding=(10, 6), font=('Arial', 10, 'bold'))
            style.configure('Dato.TEntry', fieldbackground='#fff2cc', padding=4)
            style.configure('Total.TLabel', font=('Arial', 18, 'bold'), foreground='#233d59')
            style.configure('Treeview', rowheight=26)
            self.variables = {}
            self.entradas = {}
            self.modelo = tk.StringVar()
            self.estado = tk.StringVar(value='')
            self.total = tk.StringVar(value='')
            self.radianes = tk.StringVar(value='')
            self.resultado = None
            cabecera = ttk.Frame(self, padding=14)
            cabecera.pack(fill='x')
            ttk.Label(cabecera, text='Cálculo de pesos del filtro', style='Titulo.TLabel').pack(side='left')
            ttk.Button(cabecera, text='Cargar proyecto', command=self.cargar).pack(side='right', padx=4)
            ttk.Button(cabecera, text='Guardar proyecto', command=self.guardar).pack(side='right', padx=4)
            self.formulas = {}
            self.pesos_formula = {}
            self.pestanas = ttk.Notebook(self)
            self.pestanas.pack(fill='both', expand=True)
            calculadora = ttk.Frame(self.pestanas)
            self.pestanas.add(calculadora, text='Datos y resultados')
            paneles = ttk.Panedwindow(calculadora, orient='horizontal')
            paneles.pack(fill='both', expand=True, padx=14)
            izquierda = ttk.Frame(paneles)
            derecha = ttk.Frame(paneles, padding=(14, 0))
            paneles.add(izquierda, weight=1)
            paneles.add(derecha, weight=1)
            canvas = tk.Canvas(izquierda, highlightthickness=0, background='#ffffff')
            scroll = ttk.Scrollbar(izquierda, orient='vertical', command=canvas.yview)
            canvas.configure(yscrollcommand=scroll.set)
            scroll.pack(side='right', fill='y')
            canvas.pack(side='left', fill='both', expand=True)
            formulario = ttk.Frame(canvas, padding=10)
            ventana = canvas.create_window((0, 0), window=formulario, anchor='nw')
            formulario.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
            canvas.bind('<Configure>', lambda e: canvas.itemconfigure(ventana, width=e.width))
            def rueda(event):
                if self.pestanas.index(self.pestanas.select()) != 0:
                    self.canvas_formulas.yview_scroll(-1 if (getattr(event, "num", 0) == 4 or getattr(event, "delta", 0) > 0) else 1, "units")
                    return
                if event.num == 4:
                    canvas.yview_scroll(-1, 'units')
                elif event.num == 5:
                    canvas.yview_scroll(1, 'units')
                else:
                    canvas.yview_scroll(-int(event.delta/120) if abs(event.delta)>=120 else (-1 if event.delta>0 else 1), 'units')
            self.bind_all('<MouseWheel>', rueda)
            canvas.bind('<Button-4>', rueda)
            canvas.bind('<Button-5>', rueda)
            formulario.columnconfigure(1, weight=1)
            ttk.Label(formulario, text='FILTRO MODELO').grid(row=0, column=0, sticky='w', pady=6)
            ttk.Entry(formulario, textvariable=self.modelo, style='Dato.TEntry').grid(row=0, column=1, columnspan=2, sticky='ew')
            fila = 1
            for seccion, campos in SECCIONES:
                ttk.Label(formulario, text=seccion, style='Seccion.TLabel').grid(row=fila, column=0, columnspan=3, sticky='ew', pady=(12, 5))
                fila += 1
                for clave, etiqueta, valor, unidad in campos:
                    ttk.Label(formulario, text=etiqueta).grid(row=fila, column=0, sticky='w', padx=(0, 10), pady=3)
                    variable = tk.StringVar(value=formato(valor, 0))
                    self.variables[clave] = variable
                    entrada = ttk.Entry(formulario, width=13, textvariable=variable, justify='right', style='Dato.TEntry')
                    entrada.grid(row=fila, column=1, sticky='ew', pady=3)
                    self.entradas[clave] = entrada
                    ttk.Label(formulario, textvariable=self.radianes if clave=='angulo' else None, text='' if clave=='angulo' else unidad).grid(row=fila, column=2, sticky='w', padx=8)
                    variable.trace_add('write', self.modificado)
                    fila += 1
            self.modelo.trace_add('write', self.modificado)
            ttk.Label(formulario, text='C.A.L. y C.A.S.: espesores independientes. Diámetro ciclónico = diámetro tolva.').grid(row=fila, column=0, columnspan=3, sticky='w', pady=12)
            ttk.Label(derecha, text='Resultados', style='Titulo.TLabel').pack(anchor='w', pady=(4, 8))
            contenedor = ttk.Frame(derecha)
            contenedor.pack(fill='both', expand=True)
            self.tabla = ttk.Treeview(contenedor, columns=('kg',), show='tree headings', selectmode='browse')
            self.tabla.heading('#0', text='Sección / componente')
            self.tabla.heading('kg', text='Peso (kg)')
            self.tabla.column('#0', width=335, minwidth=200)
            self.tabla.column('kg', width=115, minwidth=100, anchor='e', stretch=False)
            barra = ttk.Scrollbar(contenedor, orient='vertical', command=self.tabla.yview)
            self.tabla.configure(yscrollcommand=barra.set)
            self.tabla.pack(side='left', fill='both', expand=True)
            barra.pack(side='right', fill='y')
            self.tabla.tag_configure('seccion', background='#e5ecf4', font=('Arial', 10, 'bold'))
            ttk.Label(derecha, textvariable=self.total, style='Total.TLabel', wraplength=480).pack(anchor='w', pady=(12, 8))
            ttk.Label(derecha, text='Densidad de referencia: 8.000 kg/m³. Ángulo desde la vertical.\nPasamanos: introducir el producto A × B en mm².\nSe conservan los coeficientes de accesorios del XLS.\nPesos sin descontar aberturas. Total sin CV.', wraplength=480, justify='left').pack(anchor='w', pady=10)
            botones = ttk.Frame(self, padding=14)
            botones.pack(fill='x')
            ttk.Button(botones, text='Calcular pesos', command=self.actualizar).pack(side='left')
            ttk.Button(botones, text='Restablecer datos', command=self.restablecer).pack(side='left', padx=8)
            ttk.Button(botones, text='Exportar Excel con dibujo', command=self.exportar).pack(side='left')
            ttk.Button(botones, text='Dibujar filtro', command=self.dibujar).pack(side='left', padx=8)
            ttk.Label(self, textvariable=self.estado, wraplength=1100, padding=(14, 0, 14, 12)).pack(fill='x')
            self.crear_pestana_formulas()
            self.bind('<Return>', lambda e: self.actualizar())
            self.actualizar()

        def leer_formulas(self):
            return {clave: variable.get() for clave, variable in self.formulas.items()}

        def restaurar_formulas(self):
            for clave, _, _, original in FORMULAS:
                self.formulas[clave].set(original)
            self.actualizar()

        def crear_pestana_formulas(self):
            pagina = ttk.Frame(self.pestanas, padding=12)
            self.pestanas.add(pagina, text='Fórmulas y valores')
            ttk.Label(pagina, text='Fórmulas por posición · resultados en kg', style='Titulo.TLabel').pack(anchor='w')
            ttk.Label(pagina, text='Modifica los valores o los coeficientes de cada fórmula y pulsa Calcular pesos. '
                      'Diámetro ciclónico = diámetro tolva. Las fórmulas usan mm, DENSIDAD = 8000 kg/m³ y pi. Decimales en fórmulas: punto (0.15). '
                      'Operadores: + - * / **; funciones: abs, sin, radians.', wraplength=1000).pack(fill='x', pady=8)
            ttk.Button(pagina, text='Restaurar fórmulas originales', command=self.restaurar_formulas).pack(anchor='w', pady=4)
            canvas = tk.Canvas(pagina, highlightthickness=0)
            barra = ttk.Scrollbar(pagina, orient='vertical', command=canvas.yview)
            barra.pack(side='right', fill='y')
            canvas.pack(fill='both', expand=True)
            canvas.configure(yscrollcommand=barra.set)
            self.canvas_formulas = canvas
            canvas.bind("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
            canvas.bind("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))
            contenido = ttk.Frame(canvas, padding=6)
            ventana = canvas.create_window((0, 0), window=contenido, anchor='nw')
            contenido.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
            canvas.bind('<Configure>', lambda e: canvas.itemconfigure(ventana, width=e.width))
            contenido.columnconfigure(1, weight=1)
            fila = 0
            ttk.Label(contenido, text='Valores compartidos con Datos y resultados', style='Seccion.TLabel').grid(row=fila, column=0, columnspan=3, sticky='ew')
            fila += 1
            for clave, (etiqueta, inicial, unidad) in CAMPOS.items():
                ttk.Label(contenido, text=f'{clave} · {etiqueta}').grid(row=fila, column=0, sticky='w', pady=2)
                ttk.Entry(contenido, textvariable=self.variables[clave], style='Dato.TEntry').grid(row=fila, column=1, sticky='ew')
                ttk.Label(contenido, text=f'{unidad} · Inicial: {formato(inicial, 0)}').grid(row=fila, column=2, padx=8)
                fila += 1
            for clave, seccion, nombre, original in FORMULAS:
                ttk.Label(contenido, text=f'{clave} · {nombre}', style='Seccion.TLabel').grid(row=fila, column=0, columnspan=3, sticky='ew', pady=(12, 3))
                fila += 1
                var = tk.StringVar(value=original)
                self.formulas[clave] = var
                var.trace_add('write', self.modificado)
                ttk.Label(contenido, text='Fórmula editable').grid(row=fila, column=0, sticky='w')
                ttk.Entry(contenido, textvariable=var, style='Dato.TEntry').grid(row=fila, column=1, sticky='ew')
                peso = tk.StringVar(value='Pendiente')
                self.pesos_formula[clave] = peso
                ttk.Label(contenido, textvariable=peso, width=18, anchor='e').grid(row=fila, column=2)
                fila += 1
                ttk.Label(contenido, text='Original: ' + original, wraplength=950, foreground='#53657a').grid(row=fila, column=0, columnspan=3, sticky='w')
                fila += 1

        def modificado(self, *_):
            self.resultado = None
            for variable in self.pesos_formula.values():
                variable.set('Pendiente')
            self.total.set('Datos modificados: pulsa Calcular')
            self.tabla.delete(*self.tabla.get_children())
            self.estado.set('Introduce decimales con coma. Ejemplo: 3.800,5. Enter para calcular.')
            try:
                self.radianes.set(f'{formato(math.radians(numero(self.variables["angulo"].get())), 4)} rad')
            except ValueError:
                self.radianes.set('° desde vertical')

        def leer(self):
            datos = {}
            for clave, variable in self.variables.items():
                try:
                    datos[clave] = numero(variable.get())
                except ValueError as exc:
                    self.entradas[clave].focus_set()
                    raise ValueError(f'{CAMPOS[clave][0]}: {exc}') from exc
            validar(datos)
            return datos

        def actualizar(self):
            try:
                datos = self.leer()
                resultado = calcular(datos, self.leer_formulas())
            except ValueError as exc:
                self.modificado()
                self.estado.set(str(exc))
                messagebox.showerror('Revisa los datos', str(exc), parent=self)
                return False
            for (clave, _, _, _), peso in zip(FORMULAS, (v for items in resultado.values() for _, v in items)):
                self.pesos_formula[clave].set(formato(peso))
            self.resultado = resultado
            self.tabla.delete(*self.tabla.get_children())
            for nombre, items in resultado.items():
                padre = self.tabla.insert('', 'end', text=nombre, values=(formato(sum(v for _, v in items)),), open=True, tags=('seccion',))
                for etiqueta, valor in items:
                    self.tabla.insert(padre, 'end', text=etiqueta, values=(formato(valor),))
            total = sum(v for items in resultado.values() for _, v in items)
            self.total.set(f'Total sin CV: {formato(total)} kg')
            self.radianes.set(f'{formato(math.radians(datos["angulo"]), 4)} rad')
            self.estado.set('Cálculo actualizado.' + (' El ángulo está fuera del intervalo orientativo de 20–30°.' if not 20<=datos['angulo']<=30 else ''))
            return True

        def dibujar(self):
            try:
                datos = self.leer()
            except ValueError as exc:
                messagebox.showerror('Revisa los datos', str(exc), parent=self)
                return
            ventana = tk.Toplevel(self)
            ventana.title('Alzado del filtro' + (' · '+self.modelo.get() if self.modelo.get() else ''))
            ventana.geometry('1000x850')
            ventana.minsize(760, 620)
            ttk.Label(ventana, text='Fondo · CAL · CAS · Cuerpo ciclónico · Cuerpo cónico', style='Titulo.TLabel', wraplength=930, padding=12).pack(fill='x')
            ttk.Label(ventana, text='Dimensiones capturadas al abrir el dibujo. Modifica los datos y vuelve a pulsar Dibujar filtro para actualizar.', wraplength=930, padding=(12, 0, 12, 8)).pack(fill='x')
            lienzo = tk.Canvas(ventana, background='#ffffff', highlightthickness=0)
            lienzo.pack(fill='both', expand=True)
            ttk.Label(ventana, text='Alzado exterior. Diámetros y alturas a escala uniforme. Espesores y líneas de unión exagerados para su lectura.\nNo se representan bocas laterales, bridas, soportes ni accesorios.', wraplength=930, padding=12).pack(fill='x')

            def pintar(event):
                w, h = event.width, event.height
                lienzo.delete('all')
                d = datos['diametro']
                dt = datos['diametro_tolva']
                dc = datos['diametro_tolva']
                dd = datos['descarga']
                hc = datos['altura_cal']
                hs = datos['altura_cas']
                hy = datos['altura_ciclonica']
                ht = (dt-dd)/2/math.tan(math.radians(datos['angulo']))
                altura = hc+hs+hy+ht
                escala = min((w-370)/max(d, dt, dc), (h-105)/altura)
                centro = (w-300)/2
                y0 = 48
                y1 = y0+hc*escala
                y2 = y1+hs*escala
                y3 = y2+hy*escala
                y4 = y3+ht*escala
                r, rt, rd = d*escala/2, dt*escala/2, dd*escala/2
                rc = dc*escala/2
                etiquetas_x = centro+max(r, rt, rc)+30
                borde = '#233d59'
                lienzo.create_line(centro, y0-25, centro, y4+25, fill='#9aaabd', dash=(6, 5))
                # Fondo superior: representación de chapa con espesor visual mínimo.
                fondo_visual = max(3, datos['fondo']*escala)
                lienzo.create_rectangle(centro-r, y0-fondo_visual, centro+r, y0, fill='#6d8198', outline=borde, width=2)
                lienzo.create_rectangle(centro-r, y0, centro+r, y1, fill='#dce9f8', outline=borde, width=2)
                lienzo.create_rectangle(centro-r, y1, centro+r, y2, fill='#b9d3ec', outline=borde, width=2)
                # La tapa anular enlaza el diámetro del CAS con el cuerpo ciclónico.
                lienzo.create_line(centro-r, y2, centro-rc, y2, fill=borde, width=2)
                lienzo.create_line(centro+r, y2, centro+rc, y2, fill=borde, width=2)
                if hy > 0:
                    lienzo.create_rectangle(centro-rc, y2, centro+rc, y3, fill='#c1dfd8', outline=borde, width=2)
                lienzo.create_polygon(centro-rt, y3, centro+rt, y3, centro+rd, y4, centro-rd, y4, fill='#f7dfb5', outline=borde, width=2)
                if dc != dt:
                    lienzo.create_line(centro-rc, y3, centro-rt, y3, fill='#c67922', width=3, dash=(4, 3))
                    lienzo.create_line(centro+rc, y3, centro+rt, y3, fill='#c67922', width=3, dash=(4, 3))
                    lienzo.create_text(12, h-12, text='Unión ciclónico–tolva pendiente de definir (naranja). Peso de la unión no incluido.', anchor='sw', fill='#9a5913', font=('Arial', 9), width=w-24)
                # Etiquetas en orden vertical con separación mínima para tramos muy cortos.
                segmentos = [
                    (y0-fondo_visual/2, 'FONDO', f'Espesor {formato(datos["fondo"], 1)} mm'),
                    ((y0+y1)/2, 'CUERPO CILÍNDRICO CAL', f'Ø {formato(d, 0)} · H {formato(hc, 0)} · e {formato(datos["espesor_cal"], 1)} mm'),
                    ((y1+y2)/2, 'CUERPO CILÍNDRICO CAS', f'Ø {formato(d, 0)} · H {formato(hs, 0)} · e {formato(datos["espesor_cas"], 1)} mm'),
                    ((y2+y3)/2, 'CUERPO CICLÓNICO', f'Ø {formato(dc, 0)} · H {formato(hy, 0)} mm' if hy>0 else f'Ø {formato(dc, 0)} mm · H = 0: tramo sin altura'),
                    ((y3+y4)/2, 'CUERPO CÓNICO', f'H {formato(ht, 0)} mm · {formato(datos["angulo"], 1)}° desde vertical'),
                ]
                anterior = -30
                for i, (anclaje, titulo, detalle) in enumerate(segmentos):
                    posicion = max(anclaje, anterior+48)
                    anterior = posicion
                    radio = r if i<3 else (rc if i==3 else (rt+rd)/2)
                    lienzo.create_line(centro+radio, anclaje, etiquetas_x-10, posicion, fill='#718399')
                    lienzo.create_text(etiquetas_x, posicion-8, text=titulo, anchor='w', font=('Arial', 10, 'bold'), fill=borde)
                    lienzo.create_text(etiquetas_x, posicion+12, text=detalle, anchor='w', font=('Arial', 9), fill='#435267', width=285)
                lienzo.create_text(centro, y4+25, text=f'Descarga Ø {formato(dd, 0)} mm', font=('Arial', 10), fill=borde)
            lienzo.bind('<Configure>', pintar)

        def restablecer(self):
            if not messagebox.askyesno('Restablecer', '¿Recuperar los datos iniciales?', parent=self):
                return
            for clave, (_, valor, _) in CAMPOS.items():
                self.variables[clave].set(formato(valor, 0))
            self.modelo.set('')
            self.actualizar()

        def guardar(self):
            try:
                datos = self.leer()
                calcular(datos, self.leer_formulas())
            except ValueError as exc:
                messagebox.showerror('Revisa los datos', str(exc), parent=self)
                return
            ruta = filedialog.asksaveasfilename(parent=self, defaultextension='.json', filetypes=[('Proyecto de filtro', '*.json')])
            if not ruta:
                return
            try:
                with open(ruta, 'w', encoding='utf-8') as f:
                    json.dump({'version': 1, 'modelo': self.modelo.get(), 'cilindro_completo': True, 'datos': datos, 'formulas': self.leer_formulas()}, f, ensure_ascii=False, indent=2)
                self.estado.set('Proyecto guardado.')
            except OSError as exc:
                messagebox.showerror('No se pudo guardar', str(exc), parent=self)

        def cargar(self):
            ruta = filedialog.askopenfilename(parent=self, filetypes=[('Proyecto de filtro', '*.json')])
            if not ruta:
                return
            try:
                with open(ruta, encoding='utf-8') as f:
                    proyecto = json.load(f)
                if proyecto.get('version') != 1:
                    raise ValueError('Formato de proyecto no compatible.')
                valores = dict(proyecto['datos'])
                datos = {k: float(valores[k]) for k in CAMPOS}
                validar(datos)
                formulas = proyecto.get('formulas', {})
                if isinstance(formulas, dict):
                    formulas = {k: re.sub(r'\bdiametro_ciclonico\b', 'diametro_tolva', v) if isinstance(v, str) else v for k, v in formulas.items()}
                calcular(datos, formulas)
                for clave, _, _, original in FORMULAS:
                    self.formulas[clave].set(formulas.get(clave, original))
                for clave, valor in datos.items():
                    self.variables[clave].set(formato(valor, 8).rstrip('0').rstrip(','))
                self.modelo.set(str(proyecto.get('modelo', '')))
                self.actualizar()
                if proyecto.get('cilindro_completo') is False:
                    self.estado.set('Proyecto antiguo recalculado: C.A.L. usa ahora un cilindro completo.')
            except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
                messagebox.showerror('No se pudo cargar', str(exc), parent=self)

        def exportar(self):
            if not self.actualizar():
                return
            ruta = filedialog.asksaveasfilename(parent=self, defaultextension='.xlsx', filetypes=[('Libro Excel', '*.xlsx')])
            if not ruta:
                return
            try:
                exportar_excel(ruta, self.leer(), self.modelo.get(), self.leer_formulas())
                self.estado.set('Excel exportado con formato y dibujo del filtro.')
            except ImportError:
                messagebox.showerror('Instalar exportación Excel', 'Ejecuta en una terminal: python -m pip install openpyxl pillow', parent=self)
            except (OSError, ValueError) as exc:
                messagebox.showerror('No se pudo exportar', str(exc), parent=self)

    Aplicacion().mainloop()


if __name__ == '__main__':
    if '--test' in sys.argv:
        sys.exit(pruebas())
    iniciar()
