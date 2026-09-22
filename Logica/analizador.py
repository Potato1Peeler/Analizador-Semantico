import re
tipos_datps_validos= {
    "ETR": "entero",
    "RN": "real",
    "CDNC": "cadena",
}

#Expresion regular de variables
expresion_regular = r"!bar[1-9][0-9]*"

#Expresion regular de una declaracion
declaracion = rf"^(ETR|RN|CDNC)\s+({expresion_regular})\s*=\s*(.+)$"

#Expresion regular de una asignacion
asignacion = rf"^({expresion_regular})\s*=\s*(.+)$"

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
    if tipo_detectado != tipo:
        tabla_errores.error_agregar(
            numero_linea,
            f"Tipo incompatible: La variable '{nombre}' es de tipo {tipo}"
            f"pero el valor '{valor}' no corresponde a ese tipo",
            "tipo_incompatible",
        )
        return
    #En caso que no haya errores agrega todo a la tabla de simbolos
    tabla_simbolos.agregar(nombre, tipo, valor, numero_linea)

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
    #Obtenemos el tipo de dato
    tipo_detectado = tipo_dato(valor)

    #Condicion que nos dice que si el tipo de dato no es el mismo que se detecto agrega a la tabla de errores como incompatible
    if tipo_detectado != simbolo.tipo:
        tabla_errores.agregar(
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





