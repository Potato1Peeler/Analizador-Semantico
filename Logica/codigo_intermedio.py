import re
from openpyxl import Workbook
from openpyxl.styles import Font

try:
    from Logica.analizador import (
        reconocimiento, for_header, func_header, patron_return, declaracion_for, asignacion_for, patron_incremento_corto, patron_condicion, operando,
    )
except ImportError:
    from analizador import (
        reconocimiento, for_header, func_header, patron_return, declaracion_for, asignacion_for, patron_incremento_corto, patron_condicion, operando,
    )


PRECEDENCIA= {"*": 2, "/": 2, "+":1, "-":1}
PATRON_TOKEN = re.compile(rf"(?P<OPERANDO>{operando})|(?P<OPERADOR>[+\-*/])|(?P<ESPACIO>\s+)")

class Triplos:
    def __init__(self):
        self.triplos = []
        self.posfijos = []
        self.contador_temporales = 0
    def _nuevo_temporal(self):
        self.contador_temporales +=1
        return f"T{self.contador_temporales}"
    def _emitir(self, objeto, fuente, operador):
        self.triplos.append((objeto, fuente, operador))
    def _tokenizador(self, valor):
        tokens =[]
        pos = 0
        for m in PATRON_TOKEN.finditer(valor):
            if m.start() != pos:
                raise ValueError(f"Expresión invalida: {valor}")
            pos = m.end()
            if m.lastgroup != "ESPACIO":
                tokens.append((m.lastgroup, m.group()))
        if pos != len(valor) or not tokens:
            raise ValueError(f"Expresión invalida: {valor}")
        return tokens

    def _a_posfija(self, tokens):
        salida = []
        pila_ops = []
        for tipo, texto in tokens:
            if tipo == "OPERANDO":
                salida.append((tipo, texto))
            else:
                while pila_ops and PRECEDENCIA[pila_ops[-1]] >= PRECEDENCIA[texto]:
                    salida.append(("OPERADOR", pila_ops.pop()))
                pila_ops.append(texto)
        while pila_ops:
            salida.append(("OPERADOR", pila_ops.pop()))
        return salida

    def _generar_desde_posfija(self, posfija):
        pila =[]
        for tipo, texto in posfija:
            if tipo == "OPERANDO":
                pila.append(texto)
            else:
                derecho = pila.pop()
                izquierdo = pila.pop()
                temporal = self._nuevo_temporal()
                self._emitir(temporal, izquierdo, "=")
                self._emitir(temporal, derecho, texto)
                pila.append(temporal)
        return pila.pop()
    def traducir_asignacion(self, renglon, destino, valor):
        tokens = self._tokenizador(valor)
        posfija = self._a_posfija(tokens)
        resultado = self._generar_desde_posfija(posfija)
        self._emitir(destino, resultado, "=")
        texto_posfijo = " ".join(t for _, t in posfija)
        self.posfijos.append((renglon, f"{destino} = {valor}", f"{destino} {texto_posfijo} ="))
    def traducir_condicion(self, renglon, op1, operador, op2):
        temporal = self._nuevo_temporal()
        self._emitir(temporal, op1, "=")
        self._emitir(temporal, op2, operador)
        self.posfijos.append((renglon, f"{op1} {operador} {op2}", f"{op1} {op2} {operador}"))

def _traducir_for(gen, renglon, m_for):
    init_texto, cond_texto, incr_texto = m_for.group(1), m_for.group(2), m_for.group(3)

    m_init = re.match(declaracion_for, init_texto)
    if m_init:
        gen.traducir_asignacion(renglon, m_init.group(2), m_init.group(3))

    m_cond = re.match(patron_condicion, cond_texto)
    if m_cond:
        gen.traducir_condicion(renglon, m_cond.group(1), m_cond.group(2), m_cond.group(3))

    m_corto = re.match(patron_incremento_corto, incr_texto)
    if m_corto:
        nombre, op =m_corto.group(1), m_corto.group(2)
        gen.traducir_asignacion(renglon, nombre, f"{nombre} {'+' if op == '++' else '-'} 1")
    else:
        m_larga=re.match(asignacion_for, incr_texto)
        if m_larga:
            gen.traducir_asignacion(renglon, m_larga.group(1), m_larga.group(2))

def _escribir_fila(hoja, fila, valores, negrita = False):
    for col, valor in enumerate(valores, start=1):
        celda = hoja.cell(row =fila, column=col, value=valor)
        if isinstance(valor, str):
            celda.data_type ="s"
        if negrita:
            celda.font=Font(bold=True)

def guardar_excel(gen, ruta_excel):
    wb = Workbook()

    hoja = wb.active
    hoja.title= "Tabla de Triplos"
    _escribir_fila(hoja, 1, ["#", "Dato objeto", "Dato fuente", "Operador"], negrita=True)
    for i, (objeto, fuente, operador) in enumerate(gen.triplos, start=1):
        _escribir_fila(hoja, i + 1, [i, objeto, fuente, operador])
    for letra, ancho in zip("ABCD", (6,16,16,10)):
        hoja.column_dimensions[letra].width = ancho

    hoja2 =wb.create_sheet("posfija")
    _escribir_fila(hoja2, 1, ["Renglon", "Instruccion", "Notacion posfija"], negrita=True)
    for i, (renglon, instruccion, posfija) in enumerate(gen.posfijos, start=2):
        _escribir_fila(hoja2, i, [renglon, instruccion, posfija])
    for letra, ancho in zip("ABCD", (9,32,32)):
        hoja2.column_dimensions[letra].width = ancho

    wb.save(ruta_excel)

def generar_codigo_intermedio(codigo, tabla_errores=None, ruta_excel="codigo_intermedio.xlsx", solo_si_sin_errores=True):
    errores = tabla_errores.tabla_err() if tabla_errores else []
    if errores and solo_si_sin_errores:
        return None
    lineas_con_error = {e.linea for e in errores}

    gen= Triplos()
    pila_bloques = []

    for renglon, linea in enumerate(codigo.splitlines(), start=1):
        ls = linea.strip()
        en_funcion = "funcion" in pila_bloques
        traducir = renglon not in lineas_con_error and not en_funcion

        m_for = re.match(for_header, ls)
        if m_for:
            if traducir:
                _traducir_for(gen, renglon, m_for)
            pila_bloques.append("for")
            continue
        if re.match(func_header, ls):
            pila_bloques.append("funcion")
            continue
        if ls == "}":
            if pila_bloques:
                pila_bloques.pop()
            continue

        if re.match(patron_return, ls) or not traducir:
            continue

        resultado = reconocimiento(linea)
        try:
            if resultado[0] == "Declaracion":
                _, _tipo, nombre, valor = resultado
                gen.traducir_asignacion(renglon, nombre, valor)
            elif resultado[0] == "Asignacion":
                _, nombre, valor = resultado
                gen.traducir_asignacion(renglon, nombre, valor)
        except ValueError:
            continue

    guardar_excel(gen, ruta_excel)
    return ruta_excel


                