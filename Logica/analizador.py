import re
tipos_datps_validos= {
    "ETR": "entero",
    "RN": "real",
    "CDNC": "cadena",
}

#Expresion regular de variables
expresion_regular = r"!bar[1-9][0-9]*"

lista_identificadores = rf"{expresion_regular}(?:\s*,\s*{expresion_regular})*"

#Expresion regular de una declaracion
declaracion = rf"^(ETR|RN|CDNC)\s+({expresion_regular})\s*=\s*(.+?)\s*;$"

declaracion_multiple = rf"^(ETR|RN|CDNC)\s+({lista_identificadores})\s*;$"

#Expresion regular de una asignacion
asignacion = rf"^({expresion_regular})\s*=\s*(.+?)\s*;$"

#Patron de match, entero
entero = r"^\d+$"

#Patron de match, real
real = r"^\d+\.\d+$"

#Patron de match, cadena
cadena = r'^".*"$'

#Funcion para reconocer las lineas del codigo
def reconocimiento(linea):
    #Las separa usando .strip
    linea = linea.strip()
    #Condicion de linea vacia devuelve linea vacia
    if linea == "":
        return ( "Linea vacia",)

    #variable q usa el .match para ver si se complio la expresion regular de declaracion
    decla = re.match(declaracion, linea)
    #Si hay match entonces separa por variables la expresion
    if decla:
        tipo = decla.group(1)
        nombre =decla.group(2)
        valor = decla.group(3)
        return ("Declaracion", tipo, nombre, valor)
    
    decla_multi = re.match(declaracion_multiple, linea)
    if decla_multi:
        tipo = decla_multi.group(1)
        lista_nombres = decla_multi.group(2)
        return("DeclaracionMultiple", tipo, lista_nombres)
    
    #variable q usa el .match para ver si se cumplio la expresion regular de asignacion
    asig = re.match(asignacion, linea)
    #si hay match separa por variables la expresion
    if asig:
        nombre = asig.group(1)
        valor = asig.group(2)
        return ("Asignacion", nombre, valor)
    #Si no entiende nada en base a la expresion regular arroja linea no reconocida
    return ("Linea no reconocida",)


#Funcion q nos dice el tipo de dato en base al patron de arriba
def tipo_dato(valor):
    if re.match(entero, valor):
        return "ETR"
    if re.match(real, valor):
        return "RN"
    if re.match(cadena, valor):
        return "CDNC"
    return None

#patrones que usan .compile y .verbose para hacer la tabla de simbolos
PATRON_LEXEMAS = re.compile(r"""
    (?P<TIPO>ETR|RN|CDNC)
  | (?P<CADENA>"[^"]*")
  | (?P<REAL>\d+\.\d+)
  | (?P<ENTERO>\d+)
  | (?P<IDENT>!bar[1-9][0-9]*)
  | (?P<PALABRA>[A-Za-z_]+)
  | (?P<OP>[+\-*/=])
  | (?P<ESPACIO>\s+)
  | (?P<OTRO>.)
""", re.VERBOSE)
 
#Funcion para construir la tabla de simbolos
def obtener_lexemas(codigo, tabla_simbolos):
    #Guarda en un diccionario los lexemas ya vistos para no repetir
    vistos = {} 

    #Si hubo un "match" en el patron_lexemas ejecuta por cada match
    for match in PATRON_LEXEMAS.finditer(codigo):
        categoria = match.lastgroup
        texto = match.group()

        #No consideramos los espacios vacios como lexemas asi q los ignora
        if categoria == "ESPACIO":
            continue  

        #Si esta en el diccionario se ignora
        if texto in vistos:
            continue  # este lexema ya fue agregado antes, no se repite

        #Condicion para categorizar a si mismas ETR, RN o CDNC
        if categoria == "TIPO":
            tipo = texto 

        #Condicion para identificar si una variable ya fue declarada, si no se le pone none
        elif categoria == "IDENT":
            simbolo = tabla_simbolos.obtener(texto)
            tipo = simbolo.tipo if simbolo else None

        #Si el lexema es un dato en sí, usamos la misma categoria que las variables
        elif categoria in ("ENTERO", "REAL", "CADENA"):
            tipo = tipo_dato(texto)

        #Cualquier otra cosa las deja como none
        else: 
            tipo = None

        #
        vistos[texto] = tipo

    #Nos da return los .items del diccionario en lista
    return list(vistos.items())

operando = rf"(?:{expresion_regular}|\d+\.\d+|\d+|\".*?\")"

patron_expresion = rf"^({operando})\s*([+\-*/])\s*({operando})$"

def tipo_operando(texto, tabla_simbolos):
    if re.fullmatch(expresion_regular, texto):
        simbolo = tabla_simbolos.obtener(texto)
        return simbolo.tipo if simbolo else None
    return tipo_dato(texto)

def evaluar_expresion(operando1, operador, operando2, tabla_simbolos):
    tipo1 = tipo_operando(operando1, tabla_simbolos)
    tipo2 = tipo_operando(operando2, tabla_simbolos)

    if tipo1 is None:
        return None, f"El operando {operando1} no fue declarado o noes un valor valido"
    if tipo2 is None:
        return None, f"El operando {operando2} no fue declarado o no es un valor valido"

    if tipo1 == "ETR" and tipo2 == "ETR":
        if operador =="/":
            return None, "El operador / no es valido en ETR"
        return "ETR", None

    if tipo1 == "RN" and tipo2 == "RN":
        return "RN", None

    if tipo1 == "CDNC" and tipo2 == "CDNC":
        if operador in ("+", "-"):
            return "CDNC", None
        return None, f"El operador {operador} no es compatible con CDNC"
        
    return None, f"Tipos incompatibles en la expresion"

def tipos_compatibles(tipo_esperado, tipo_valor):
    if tipo_valor is None:
        return False
    if tipo_esperado == tipo_valor:
        return True
    if tipo_esperado == "RN" and tipo_valor == "ETR":
        return True
    return False

#Funcion que "procesa" declarraciones en base a si estan bien o mal
# el "_" en el nombre solo representa q la funcion como tal no "hace nada" por lo q no se deberia ejecutar sola (Buena practica)
def _procesar_declaracion(tipo, nombre, valor, numero_linea, tabla_simbolos, tabla_errores):
    #Condicion que agrega a la tabla de errores como variable duplicada
    if tabla_simbolos.si_existe(nombre):
        tabla_errores.error_agregar(
            numero_linea,
            f"La variable '{nombre}' ya habia sido declarada",
            "duplicado",
        )
        return
    #Guarda el tipo de dato
    tipo_detectado = tipo_dato(valor)
    #Utiliza como tipo de dato y lo condiciona en base not y lo agrega como error en caso de incopatibildiad de tipos
    if not tipos_compatibles(tipo, tipo_detectado):
        tabla_errores.error_agregar(
            numero_linea,
            f"Tipo incompatible: La variable '{nombre}' es de tipo {tipo}"
            f"pero el valor '{valor}' no corresponde a ese tipo",
            "tipo_incompatible",
        )
        return
    #En caso que no haya errores agrega todo a la tabla de simbolos
    tabla_simbolos.agregar(nombre, tipo, valor, numero_linea)

def _procesar_declaracion_multiple(tipo, lista_nombres, numero_linea, tabla_simbolos, tabla_errores):
    nombres = [n.strip() for n in lista_nombres.split(",")]

    for nombre in nombres:
        if tabla_simbolos.si_existe(nombre):
            tabla_errores.error_agregar(
                numero_linea,
                f"La variable {nombre} ya habia sido declarada",
                "duplicado",
            )
            continue
        tabla_simbolos.agregar(nombre, tipo, None, numero_linea)

#Funcion que "procesa" asignaciones en base a si estan bien o mal
# el "_" en el nombre solo representa q la funcion como tal no "hace nada" por lo q no se deberia ejecutar sola (Buena practica)
def _procesar_asignacion(nombre, valor, numero_linea, tabla_simbolos, tabla_errores):
    #Condicion que agerga a la tabla de errores como error de declaracion
    if not tabla_simbolos.si_existe(nombre):
        tabla_errores.error_agregar(
            numero_linea,
            f"La variable '{nombre}' no ha sido declarada",
            "no_declarada",
        )
        return

    #Dado el nombre en la tabla de simbolos
    simbolo = tabla_simbolos.obtener(nombre)
    m_expr = re.match(patron_expresion, valor)
    if m_expr:
        operando1 = m_expr.group(1)
        operador = m_expr.group(2)
        operando2 = m_expr.group(3)

        tipo_resultado, mensaje_error = evaluar_expresion(operando1, operador, operando2, tabla_simbolos)

        if mensaje_error:
            tabla_errores.error_agregar(numero_linea, mensaje_error, "tipo_incompatible")
            return
        if tipo_resultado!= simbolo.tipo:
            tabla_errores.error_agregar(
                numero_linea, 
                f"Tipo incompatible: {nombre} es de tipo {simbolo.tipo}"
                f"pero la expresion {valor} da como resultado {tipo_resultado}",
                "tipo_incompatible",
            )
            return
        tabla_simbolos.actualizar(nombre, valor)
        return
    
    #Obtenemos el tipo de dato
    tipo_detectado = tipo_dato(valor)

    #Condicion que nos dice que si el tipo de dato no es el mismo que se detecto agrega a la tabla de errores como incompatible
    if not tipos_compatibles(simbolo.tipo, tipo_detectado):
        tabla_errores.error_agregar(
            numero_linea,
            f"Tipo incompatible: '{nombre}' es de tipo {simbolo.tipo}"
            f"pero se intento asignar el valor de '{valor}'",
            "tipo_incompatible",
        )

        return
    #Si todo esta bien utiliza la funcion de actualizar para actualizar la tabla de simbolos
    tabla_simbolos.actualizar(nombre, valor)

#Es la funcion que "analiza" el codigo de input
def analizador(codigo, tabla_simbolos, tabla_errores):
    #Divide las lineas del codigo
    lineas = codigo.splitlines()

    #Enumera las lineas y las guarda en "numero_linea" y "linea"
    for numero_linea, linea in enumerate(lineas, start=1):
        #Guarda en la variable resultado todo lo hecho en la funcion reconocimiento
        resultado = reconocimiento(linea)

        #Condicion que indica linea vacia y la ignora
        if resultado[0] == "Linea vacia":
            continue
        #Condicion que clasifica como "Declaracion" y ejecuta la funcion de esta
        elif resultado[0] == "Declaracion":
            _, tipo, nombre, valor = resultado
            _procesar_declaracion(tipo, nombre, valor, numero_linea, tabla_simbolos, tabla_errores)
        elif resultado[0] == "DeclaracionMultiple":
            _, tipo, lista_nombres = resultado
            _procesar_declaracion_multiple(tipo, lista_nombres, numero_linea, tabla_simbolos, tabla_errores)
        #Condicion que clasifica como "Asignacion" y ejecuta la funcion de esta
        elif resultado[0] == "Asignacion":
            _, nombre, valor = resultado
            _procesar_asignacion(nombre, valor, numero_linea, tabla_simbolos, tabla_errores)

        #Condicion que nos dice que cualquier otra cosa la toma como error y la mete a la tabla de errores
        elif resultado[0] == "Linea no reconocida":
            tabla_errores.error_agregar(
                numero_linea,
                f"Instrucción no reconocida: '{linea.strip()}'",
                "sintaxis",
            )





