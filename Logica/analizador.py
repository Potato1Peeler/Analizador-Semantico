import re
tipos_datps_validos= {
    "ETR": "entero",
    "RN": "real",
    "CDNC": "cadena",
}

#Expresion regular de variables
expresion_regular = r"!bar[1-9][0-9]*"

expresion_regular_funcion = r"!func[1-9][0-9]*"

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

llamada_funcion = rf"{expresion_regular_funcion}\s*\(\s*\)"

patron_llamada_statement = rf"^({expresion_regular_funcion})\s*\(\s*\)\s*;$"

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

    m_llamada=re.match(patron_llamada_statement, linea)
    if m_llamada: 
        nombre_funcion = m_llamada.group(1)
        return ("LlamadaFuncion", nombre_funcion)
    
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
  | (?P<IDENTF>!func[1-9][0-9]*)
  | (?P<IDENT>!bar[1-9][0-9]*)
  | (?P<PALABRA>[A-Za-z_]+)
  | (?P<OP>\+\+|--|<=|>=|==|!=|[+\-*/=<>])
  | (?P<DELIM>[(){},;])
  | (?P<ESPACIO>\s+)
  | (?P<OTRO>.)
""", re.VERBOSE)
 
#Funcion para construir la tabla de simbolos
def obtener_lexemas(codigo, tabla_simbolos, tabla_funciones = None, lineas_con_error=None):
    if lineas_con_error is None:
        lineas_con_error = set()
    #Guarda en un diccionario los lexemas ya vistos para no repetir
    vistos = {} 

    #Si hubo un "match" en el patron_lexemas ejecuta por cada match
    for match in PATRON_LEXEMAS.finditer(codigo):
        categoria = match.lastgroup
        texto = match.group()

        numero_linea = codigo.count("\n", 0, match.start()) + 1

        if numero_linea in lineas_con_error:
            continue
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
            if simbolo:
                tipo =simbolo.tipo
            else:
                tipo=tabla_simbolos.tipo_historico(texto)
        elif categoria =="IDENTF":
            tipo = tabla_funciones.obtener_tipo(texto) if tabla_funciones else None

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

operando = rf"(?:{llamada_funcion}|{expresion_regular}|\d+\.\d+|\d+|\".*?\")"

patron_expresion = rf"^({operando})\s*([+\-*/])\s*({operando})$"

def tipo_operando(texto, tabla_simbolos, tabla_funciones = None):
    m_llamada=re.fullmatch(llamada_funcion, texto)
    if m_llamada:
        nombre_funcion = re.match(expresion_regular_funcion, texto).group()
        if tabla_funciones and tabla_funciones.existe(nombre_funcion):
            return tabla_funciones.obtener_tipo(nombre_funcion)
        return None
    
    if re.fullmatch(expresion_regular, texto):
        simbolo = tabla_simbolos.obtener(texto)
        return simbolo.tipo if simbolo else None
    return tipo_dato(texto)

OPERADORES_INVALIDOS = {
    "ETR": {"/"},
    "RN": set(),
    "CDNC": {"*", "/"},
}

def evaluar_expresion(tipo_destino, valor_completo, tabla_simbolos, tabla_funciones=None):
    patron_token = rf"(?P<OPERANDO>{operando})|(?P<OPERADOR>[+\-*/])|(?P<ESPACIO>\s+)"
    tokens = []
    pos = 0

    for m in re.finditer(patron_token, valor_completo):
        if m.start() != pos:
            return [(valor_completo, f"La expresion '{valor_completo}' no tiene una forma valida")]
        pos = m.end()
        if m.lastgroup == "ESPACIO":
            continue
        tokens.append((m.lastgroup, m.group()))

    if pos != len(valor_completo) or not tokens or tokens[0][0] != "OPERANDO":
        return [(valor_completo, f"La expresion '{valor_completo}' no tiene una forma valida")]

    errores = []
    esperado = "OPERANDO"

    for tipo_tok, texto_tok in tokens:
        if tipo_tok != esperado:
            return [(valor_completo, f"La expresion '{valor_completo}' no tiene una forma valida")]
        if tipo_tok =="OPERANDO":
            tipo_op =tipo_operando(texto_tok, tabla_simbolos, tabla_funciones)
            if tipo_op is None:
                if re.fullmatch(llamada_funcion, texto_tok):
                    nombre_func = re.match(expresion_regular_funcion, texto_tok).group()
                    errores.append((texto_tok, f"La funcion '{nombre_func}' no ha sido declarada"))
                else:
                    errores.append((texto_tok, f"El operando '{texto_tok}' no fue declarado o no es un valor valido"))
            elif not tipos_compatibles(tipo_destino, tipo_op):
                errores.append((texto_tok, f"El operando '{texto_tok}' es de tipo {tipo_op}, no compatible con {tipo_destino}"))
            esperado = "OPERADOR"
        else:
            if texto_tok in OPERADORES_INVALIDOS.get(tipo_destino, set()):
                errores.append((texto_tok, f"El operador '{texto_tok}' no es compatible con {tipo_destino}"))
            esperado = "OPERANDO"

    if esperado != "OPERADOR":
        return [(valor_completo, f"La expresion '{valor_completo}' no tiene una forma valida")]
    
    return errores

def tipos_compatibles(tipo_esperado, tipo_valor):
    if tipo_valor is None:
        return False
    if tipo_esperado == tipo_valor:
        return True
    if tipo_esperado == "RN" and tipo_valor == "ETR":
        return True
    return False

for_header = r"^for\s*\(\s*(.+?)\s*;\s*(.+?)\s*;\s*(.+?)\s*\)\s*\{\s*$"
declaracion_for = rf"^(ETR|RN|CDNC)\s+({expresion_regular})\s*=\s*(.+)$"
asignacion_for = rf"^({expresion_regular})\s*=\s*(.+)$"
patron_incremento_corto = rf"^({expresion_regular})\s*(\+\+|--)$"
operador_comparacion = r"<=|>=|==|!=|<|>"
patron_condicion = rf"^({operando})\s*({operador_comparacion})\s*({operando})$"

COMPARADORES_INVALIDOS = {
    "ETR": set(),
    "RN": set(),
    "CDNC": {"<", ">", "<=", ">="},
}

def evaluar_condicion(tipo_destino, operando1, operador, operando2, tabla_simbolos, tabla_funciones=None):
    errores = []

    tipo1 = tipo_operando(operando1, tabla_simbolos, tabla_funciones)
    if tipo1 is None:
        errores.append((operando1, f"El operando '{operando1}' no fue declarado o no es un valor valido"))
    elif not tipos_compatibles(tipo_destino, tipo1):
        errores.append((operando1, f"El operando '{operando1}' es de tipo {tipo1}, no compatible con {tipo_destino}"))

    tipo2 = tipo_operando(operando2, tabla_simbolos, tabla_funciones)
    if tipo2 is None:
        errores.append((operando2, f"El operando '{operando2}' no fue declarado o no es un valor valido"))
    elif not tipos_compatibles(tipo_destino, tipo2):
        errores.append((operando2, f"El operando '{operando2}' es de tipo {tipo2}, no compatible con {tipo_destino}"))

    if operador in COMPARADORES_INVALIDOS.get(tipo_destino, set()):
        errores.append((operador, f"El operador '{operador}' no es compatible con {tipo_destino}"))           

    return errores

def _declarar_variable_local(tipo, nombre, valor, numero_linea, tabla_simbolos, tabla_errores, tabla_funciones=None):


    errores_expresion = evaluar_expresion(tipo, valor, tabla_simbolos, tabla_funciones)

    if errores_expresion:
        for lexema_error, mensaje in errores_expresion:
            tabla_errores.error_agregar(lexema_error, numero_linea, mensaje)
        return False
    tabla_simbolos.agregar(nombre, tipo, valor, numero_linea)
    return True



def _procesar_for_header(m_for, numero_linea, tabla_simbolos, tabla_errores, pila_ambitos, tabla_funciones=None):
    init_texto=m_for.group(1)
    cond_texto=m_for.group(2)
    incr_texto=m_for.group(3)

    ambito = {"tipo": "for", "variables": {}}
    nombre_local = None
    # respaldo = None

    m_decl=re.match(declaracion_for, init_texto)
    if m_decl:
        tipo, nombre, valor = m_decl.group(1), m_decl.group(2), m_decl.group(3)
        respaldo = tabla_simbolos.obtener(nombre)
        exito = _declarar_variable_local(tipo, nombre, valor, numero_linea, tabla_simbolos, tabla_errores, tabla_funciones)  
        if exito:    
            nombre_local=nombre
            ambito["variables"][nombre] = respaldo
    else:
        tabla_errores.error_agregar(
            init_texto, numero_linea,
            f"La inicializacion del for no es una declaracion valida: '{init_texto}'",
        )

    m_cond = re.match(patron_condicion, cond_texto)
    if m_cond:
        if nombre_local and tabla_simbolos.si_existe(nombre_local):
            op1, operador_comp, op2 = m_cond.group(1), m_cond.group(2), m_cond.group(3)
            tipo_var = tabla_simbolos.obtener(nombre_local).tipo
            for lexema_err, mensaje in evaluar_condicion(tipo_var, op1, operador_comp, op2, tabla_simbolos, tabla_funciones):
                tabla_errores.error_agregar(lexema_err, numero_linea, mensaje)
    else:
        tabla_errores.error_agregar(
            cond_texto, numero_linea,
            f"La condicion del for no es valida: {cond_texto}",
        )

    m_incr_corto = re.match(patron_incremento_corto, incr_texto)
    if m_incr_corto:
        nombre_incr, op_incr = m_incr_corto.group(1), m_incr_corto.group(2)
        valor_equivalente = f"{nombre_incr} + 1" if op_incr == "++" else f"{nombre_incr} - 1"
        _procesar_asignacion(nombre_incr, valor_equivalente, numero_linea, tabla_simbolos, tabla_errores, tabla_funciones)
    else:
        m_incr_asig=re.match(asignacion_for, incr_texto)
        if m_incr_asig:
            nombre_incr, valor_incr = m_incr_asig.group(1), m_incr_asig.group(2)
            _procesar_asignacion(nombre_incr, valor_incr, numero_linea, tabla_simbolos, tabla_errores, tabla_funciones)        
        else:
            tabla_errores.error_agregar(
                incr_texto, numero_linea,
                f"El incremento del for no es valido: {incr_texto}",
            )                           

    pila_ambitos.append(ambito)

func_header = rf"^(ETR|RN|CDNC)\s+({expresion_regular_funcion})\s*\(\s*\)\s*\{{\s*$"
patron_return = r"^return\s+(.+?)\s*;$"

def _procesar_func_header(m_func, numero_linea, tabla_funciones, tabla_errores, pila_ambitos):
    tipo_retorno = m_func.group(1)
    nombre_funcion = m_func.group(2)

    if tabla_funciones.existe(nombre_funcion):
        tabla_errores.error_agregar(
            nombre_funcion, numero_linea,
            f"La funcion {nombre_funcion} ya habia sido declarada",
        )
    else:
        tabla_funciones.agregar(nombre_funcion, tipo_retorno)

    ambito = {
        "tipo": "funcion",
        "variables": {},
        "tipo_retorno": tipo_retorno,
        "nombre_funcion": nombre_funcion,
    }
    pila_ambitos.append(ambito)

def _procesar_return(valor_return, numero_linea, tabla_simbolos, tabla_errores, tabla_funciones, ambito_actual):
    if not ambito_actual or ambito_actual["tipo"] != "funcion":
        tabla_errores.error_agregar(
            "return", numero_linea,
            "return usado fuera de una funcion",
        )
        return
    
    tipo_retorno = ambito_actual["tipo_retorno"]
    nombre_funcion = ambito_actual["nombre_funcion"]

    errores_expresion = evaluar_expresion(tipo_retorno, valor_return, tabla_simbolos, tabla_funciones)
    for lexema_err, mensaje in errores_expresion:
        tabla_errores.error_agregar(lexema_err, numero_linea, mensaje)


#Funcion que "procesa" declarraciones en base a si estan bien o mal
# el "_" en el nombre solo representa q la funcion como tal no "hace nada" por lo q no se deberia ejecutar sola (Buena practica)
def _procesar_declaracion(tipo, nombre, valor, numero_linea, tabla_simbolos, tabla_errores, tabla_funciones=None, ambito_local=None):
    if ambito_local is not None:
        if nombre in ambito_local:
            tabla_errores.error_agregar(
                nombre, numero_linea,
                f"La variable {nombre} ya habia sido declarada en este ambito",
            )
            return
        respaldo = tabla_simbolos.obtener(nombre)
        exito = _declarar_variable_local(tipo, nombre, valor, numero_linea, tabla_simbolos, tabla_errores, tabla_funciones)
        if exito:
            ambito_local[nombre] = respaldo
        return
    
    #Condicion que agrega a la tabla de errores como variable duplicada
    if tabla_simbolos.si_existe(nombre):
        tabla_errores.error_agregar(
            nombre,
            numero_linea,
            f"La variable {nombre} ya habia sido declarada",
        )
        return

    errores_expresion = evaluar_expresion(tipo, valor, tabla_simbolos, tabla_funciones)   
    if errores_expresion:
        for lexema_error, mensaje in errores_expresion:
            tabla_errores.error_agregar(lexema_error, numero_linea, mensaje)
        return
    tabla_simbolos.agregar(nombre, tipo, valor, numero_linea)
    

def _procesar_declaracion_multiple(tipo, lista_nombres, numero_linea, tabla_simbolos, tabla_errores, ambito_local=None):
    nombres = [n.strip() for n in lista_nombres.split(",")]

    for nombre in nombres:
        if ambito_local is not None:
            if nombre in ambito_local:
                tabla_errores.error_agregar(
                    nombre, numero_linea,
                    f"La variable {nombre} ya habia sido declarada en este ambito",
                )
                continue
            respaldo = tabla_simbolos.obtener(nombre)
            tabla_simbolos.agregar(nombre, tipo, None, numero_linea)
            ambito_local[nombre] = respaldo
            continue

        if tabla_simbolos.si_existe(nombre):
            tabla_errores.error_agregar(
                nombre,
                numero_linea,
                f"La variable {nombre} ya habia sido delcarada"
            )
            continue
        tabla_simbolos.agregar(nombre, tipo, None, numero_linea)

#Funcion que "procesa" asignaciones en base a si estan bien o mal
# el "_" en el nombre solo representa q la funcion como tal no "hace nada" por lo q no se deberia ejecutar sola (Buena practica)
def _procesar_asignacion(nombre, valor, numero_linea, tabla_simbolos, tabla_errores, tabla_funciones=None):
    if not tabla_simbolos.si_existe(nombre):
        tabla_errores.error_agregar(
            nombre,
            numero_linea,
            f"La variable '{nombre}' no ha sido declarada",
        )
        return

    simbolo = tabla_simbolos.obtener(nombre)
    errores_expresion = evaluar_expresion(simbolo.tipo, valor, tabla_simbolos, tabla_funciones)
    if errores_expresion:
        for lexema_error, mensaje in errores_expresion:
            tabla_errores.error_agregar(lexema_error, numero_linea, mensaje)
        return

    tabla_simbolos.actualizar(nombre, valor)

#Es la funcion que "analiza" el codigo de input
def analizador(codigo, tabla_simbolos, tabla_errores, tabla_funciones = None):
    #Divide las lineas del codigo
    lineas = codigo.splitlines()
    pila_ambitos = []

    #Enumera las lineas y las guarda en "numero_linea" y "linea"
    for numero_linea, linea in enumerate(lineas, start=1):
        linea_stripped=linea.strip()
        m_for = re.match(for_header, linea_stripped)
        if m_for:
            _procesar_for_header(m_for, numero_linea, tabla_simbolos, tabla_errores, pila_ambitos, tabla_funciones)
            continue

        m_func= re.match(func_header, linea_stripped)
        if m_func:
            _procesar_func_header(m_func, numero_linea, tabla_funciones, tabla_errores, pila_ambitos)
            continue

        if linea_stripped == "}":
            if pila_ambitos:
                ambito_cerrado = pila_ambitos.pop()
                for nombre_var, respaldo in ambito_cerrado["variables"].items():
                    if respaldo is not None:
                        tabla_simbolos.restaurar(nombre_var, respaldo)
                    else:
                        tabla_simbolos.eliminar(nombre_var)
            else:
                tabla_errores.error_agregar(
                    "}", numero_linea,
                    "Se encontro '}' sin un bloque abierto correspondiente",                   
                )
            continue
        m_return = re.match(patron_return, linea_stripped)
        if m_return:
            valor_return = m_return.group(1)
            ambito_actual = pila_ambitos[-1] if pila_ambitos else None
            _procesar_return(valor_return, numero_linea, tabla_simbolos, tabla_errores, tabla_funciones, ambito_actual)
            continue

        #Guarda en la variable resultado todo lo hecho en la funcion reconocimiento
        ambito_actual = pila_ambitos[-1]["variables"] if pila_ambitos else None
        resultado = reconocimiento(linea)

        #Condicion que indica linea vacia y la ignora
        if resultado[0] == "Linea vacia":
            continue
        #Condicion que clasifica como "Declaracion" y ejecuta la funcion de esta
        elif resultado[0] == "Declaracion":
            _, tipo, nombre, valor = resultado
            _procesar_declaracion(tipo, nombre, valor, numero_linea, tabla_simbolos, tabla_errores, tabla_funciones, ambito_actual)
        elif resultado[0] == "DeclaracionMultiple":
            _, tipo, lista_nombres = resultado
            _procesar_declaracion_multiple(tipo, lista_nombres, numero_linea, tabla_simbolos, tabla_errores, ambito_actual)
        elif resultado[0] == "LlamadaFuncion":
            _, nombre_funcion = resultado
            if not tabla_funciones or not tabla_funciones.existe(nombre_funcion):
                tabla_errores.error_agregar(
                    nombre_funcion, numero_linea,
                    f"La funcion {nombre_funcion} no ha sido declarada",
                )
        #Condicion que clasifica como "Asignacion" y ejecuta la funcion de esta
        elif resultado[0] == "Asignacion":
            _, nombre, valor = resultado
            _procesar_asignacion(nombre, valor, numero_linea, tabla_simbolos, tabla_errores, tabla_funciones)
    
        #Condicion que nos dice que cualquier otra cosa la toma como error y la mete a la tabla de errores
        elif resultado[0] == "Linea no reconocida":
            tabla_errores.error_agregar(
                linea.strip(),
                numero_linea,
                f"Intruccion no reconocida: {linea.strip()}"
            )





