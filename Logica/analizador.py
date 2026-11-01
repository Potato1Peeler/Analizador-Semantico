import re
tipos_datps_validos= {
    "ETR": "entero",
    "RN": "real",
    "CDNC": "cadena",
}

#Expresion regular de variables
expresion_regular = r"!bar[1-9][0-9]*"

expresion_regular_funcion = r"!bar[1-9][0-9]*"

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

llamada_funcion = rf"{expresion_regular_funcion}\s*\(.*?\)"

patron_llamada_statement = rf"^({expresion_regular_funcion})\s*\(\s*\)\s*;$"

patron_return = r"^return\s+(.+?)\s*;$"

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
        args_str = m_llamada.group(2)
        return ("LlamadaFuncion", nombre_funcion, args_str)
    
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
  | (?P<OP>\+\+|--|<=|>=|==|!=|&&|\|\||[+\-*/=<>%])
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
        if categoria in ("ESPACIO", "OP", "DELIM", "OTRO", "PALARBA"):
            continue  

        #Si esta en el diccionario se ignora
        if texto in vistos:
            continue  # este lexema ya fue agregado antes, no se repite

        #Condicion para categorizar a si mismas ETR, RN o CDNC
        if categoria == "TIPO":
            tipo = texto 

        #Condicion para identificar si una variable ya fue declarada, si no se le pone none
        elif categoria == "IDENT":
            if tabla_funciones and tabla_funciones.existe(texto):
                tipo = tabla_funciones.obtener_tipo(texto)
            else:
                simbolo = tabla_simbolos.obtener(texto)
                if simbolo:
                    tipo = simbolo.tipo
                else:
                    tipo = tabla_simbolos.tipo_historico(texto)

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
    "CDNC": {"*", "/", "%"},
}

patron_token_expr = re.compile(
    rf"(?P<OPERANDO>{operando})|(?P<OPERADOR>[+\-*/%])|(?P<PAREN>[()])|(?P<ESPACIO>\s+)"
)

def tokenizar_expresion(valor):
    tokens = []
    pos = 0
    for m in patron_token_expr.finditer(valor):
        if m.start() != pos:
            return None
        pos = m.end()
        if m.lastgroup != "ESPACIO":
            tokens.append((m.lastgroup, m.group()))
    if pos != len(valor) or not tokens:
        return None
    return tokens

def validar_estructura_expresion(tokens):
    errores = []
    pila_parentesis = []
    esperando_operando = True
    anterior = None

    for i, (tipo, texto) in enumerate(tokens):
        if esperando_operando:
            if tipo == "OPERANDO":
                esperando_operando = False
            elif texto == "(":
                pila_parentesis.append(i)
            elif tipo == "OPERADOR":
                errores.append((i, texto, f"El operador '{texto}' no tiene operando a su izquierda"))
            else:
                if anterior == "(":
                    errores.append((i, "()", "Parentesis vacios, falta una expresion dentro"))
                else:
                    errores.append((i, ")", "Falta un operando antes de ')'"))
                if pila_parentesis:
                    pila_parentesis.pop()
                else:
                    errores.append((i, ")", "Parentesis ')' sin su '(' de apertura"))
                esperando_operando = False
        else:
            if tipo == "OPERADOR":
                esperando_operando = True
            elif texto == ")":
                if pila_parentesis:
                    pila_parentesis.pop()
                else:
                    errores.append((i, ")", "Parentesis ')' sin su '(' de apertura"))
            elif tipo == "OPERANDO":
                errores.append((i, texto, f"Falta un operador antes de '{texto}'"))
            else:
                errores.append((i, "(", "Falta un operador antes de '('"))
                pila_parentesis.append(i)
                esperando_operando = True
        anterior = texto

    if esperando_operando and tokens and tokens[-1][1] != "(":
        ultimo = tokens[-1][1]
        errores.append((len(tokens), ultimo, f"Falta un operando despues de '{ultimo}'"))

    for i in pila_parentesis:
        errores.append((i, "(", "Parentesis '(' sin su ')' de cierre"))

    return errores

def evaluar_expresion(tipo_destino, valor_completo, tabla_simbolos, tabla_funciones=None):
    tokens = tokenizar_expresion(valor_completo)
    if tokens is None:
        return [(valor_completo, f"La expresion '{valor_completo}' no tiene una forma valida")]
    errores = [(i, 0, lexema, mensaje) for i, lexema, mensaje in validar_estructura_expresion(tokens)]

    for i, (tipo_tok, texto_tok) in enumerate(tokens):
        if tipo_tok == "OPERANDO":
            tipo_op = tipo_operando(texto_tok, tabla_simbolos, tabla_funciones)
            if tipo_op is None:
                if re.fullmatch(llamada_funcion, texto_tok):
                    nombre_func = re.match(expresion_regular_funcion, texto_tok).group()
                    errores.append((i, 1, texto_tok, f"La funcion '{nombre_func}' no ha sido declarada"))
                else:
                    errores.append((i, 1, texto_tok, f"El operando '{texto_tok}' no fue declarado o no es un valor valido"))
            elif not tipos_compatibles(tipo_destino, tipo_op):
                errores.append((i, 1, texto_tok, f"El operando '{texto_tok}' es de tipo {tipo_op}, no compatible con {tipo_destino}"))

            if re.fullmatch(llamada_funcion, texto_tok) and tipo_op is not None:
                m = re.match(rf"({expresion_regular_funcion})\s*\((.*?)\)", texto_tok)    
                nombre_func = m.group(1)
                args_str = m.group(2).strip()
                info = tabla_funciones.funciones[nombre_func]
                args = [a.strip() for a in args_str.split(",")] if args_str else []
                if len(args) != len(info["parametros"]):
                    errores.append((i, 1, texto_tok, f"La funcion '{nombre_func}' espera {len(info['parametros'])} argumentos, se pasaron {len(args)}"))
                else:
                    for arg, tipo_p in zip(args, info["tipos_parametros"]):
                        errs = evaluar_expresion(tipo_p, arg, tabla_simbolos, tabla_funciones)
                        for err_lex, err_msg in errs:
                            errores.append((i, 1, err_lex, err_msg))

        elif tipo_tok == "OPERADOR":
            if texto_tok in OPERADORES_INVALIDOS.get(tipo_destino, set()):
                errores.append((i, 1, texto_tok, f"El operador '{texto_tok}' no es compatible con {tipo_destino}"))

    errores.sort(key=lambda e: (e[0], e[1]))
    return [(lexema, mensaje) for _, _, lexema, mensaje in errores]

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

patron_token_cond = re.compile(
    rf"(?P<OPERANDO>{operando})|(?P<COMP>{operador_comparacion})|(?P<LOGICO>&&|\|\|)"
    rf"|(?P<PAREN>[()])|(?P<ESPACIO>\s+)|(?P<DESCONOCIDO>\S)"
)

def tokenizar_condicion(valor):
    tokens = []
    for m in patron_token_cond.finditer(valor):
        if m.lastgroup != "ESPACIO":
            tokens.append((m.lastgroup, m.group()))
    return tokens

def validar_estructura_condicion(tokens):
    errores = []
    pila = []
    estado = "IZQ"
    anterior = None
    idx_anterior = -1
    def cerrar(i):
        if pila:
            pila.pop()
        else:
            errores.append((i, ")", "Parentesis ')' sin su '(' de apertura"))

    for i, (tipo, texto) in enumerate(tokens):
        if tipo == "DESCONOCIDO":
            errores.append((i, texto, f"Simbolo no reconocido '{texto}' en la condicion"))
            continue

        if estado == "IZQ":
            if tipo == "OPERANDO":
                estado = "COMP"
            elif texto == "(":
                pila.append(i)
            elif tipo == "COMP":
                errores.append((i, texto, f"El comparador '{texto}' no tiene operando a su izquierda"))
                estado = "DER"
            elif tipo == "LOGICO":
                errores.append((i, texto, f"El operador '{texto}' no tiene una condicion a su izquierda"))
            else:
                if anterior == "(":
                    errores.append((i, "()", "Parentesis vacios, falta una condicion dentro"))
                else:
                    errores.append((i, ")", "Falta una condicion antes de ')'"))
                cerrar(i)
                estado = "FIN"
        elif estado == "COMP":
            if tipo == "COMP":
                estado = "DER"
            else: 
                errores.append((idx_anterior, anterior, f"Falta un comparador despues de '{anterior}'"))
                if tipo == "LOGICO":
                    estado = "IZQ"
                elif texto == "(":
                    pila.append(i)
                    estado = "IZQ"
                elif texto == ")":
                    cerrar(i)
                    estado = "FIN"

        elif estado == "DER":
            if tipo == "OPERANDO":
                estado = "FIN"
            elif texto == "(":
                errores.append((i, "(", f"Despues de '{anterior}' debe ir un operando, no un parentesis"))
                pila.append(i)
            else:
                errores.append((idx_anterior, anterior, f"Falta un operando despues de '{anterior}'"))
                if tipo == "LOGICO":
                    estado = "IZQ"
                elif texto == ")":
                    cerrar(i)
                    estado = "FIN"

        else:
            if tipo == "LOGICO":
                estado = "IZQ"
            elif texto == ")":
                cerrar(i)
            elif tipo == "COMP":
                errores.append((i, texto, f"No se pueden encadenar comparaciones con '{texto}', use && o ||"))
                estado = "DER"
            elif tipo == "OPERANDO":
                errores.append((i, texto, f"Falta && o || antes de '{texto}'"))
                estado = "COMP"
            else:
                errores.append((i, "(", "Falta && o || antes de '('"))
                pila.append(i)
                estado = "IZQ"
        anterior = texto
        idx_anterior = i

    if anterior is not None:
        if estado == "COMP":
            errores.append((idx_anterior, anterior, f"Falta un comparador despues de '{anterior}'"))
        elif estado == "DER":
            errores.append((idx_anterior, anterior, f"Falta un operando despues de '{anterior}'"))
        elif estado == "IZQ" and anterior != "(":
            errores.append((idx_anterior, anterior, f"Falta una condicion despues de '{anterior}'"))

    for i in pila:
        errores.append((i, "(", "Parentesis '(' sin su ')' de cierre"))

    return errores

def _error_operando_desconocido(texto):
    if re.fullmatch(llamada_funcion, texto):
        nombre = re.match(expresion_regular_funcion, texto).group()
        return f"La funcion '{nombre}' no ha sido declarada"
    return f"El operando '{texto}' no fue declarado o no es un valor valido"

def evaluar_condicion_compuesta(valor, tabla_simbolos, tabla_funciones=None, validar_tipos=True):
    tokens = tokenizar_condicion(valor)
    errores = [(i, 0, lex, msg) for i, lex, msg in validar_estructura_condicion(tokens)]

    if validar_tipos:
        for i, (tipo_tok, texto_tok) in enumerate(tokens):
            if tipo_tok != "COMP" or i == 0 or i == len(tokens) -1:
                continue
            if tokens[i - 1][0] != "OPERANDO" or tokens[i+1][0] != "OPERANDO":
                continue
            op1, op2 = tokens[i-1][1], tokens[i+1][1]
            tipo1 = tipo_operando(op1, tabla_simbolos, tabla_funciones)
            tipo2 = tipo_operando(op2, tabla_simbolos, tabla_funciones)

            if tipo1 is None:
                errores.append((i - 1, 1, op1, _error_operando_desconocido(op1)))
            if tipo2 is None:
                errores.append((i + 1, 1, op2, _error_operando_desconocido(op2)))
            if tipo1 is not None:
                if tipo2 is not None and not tipos_compatibles(tipo1, tipo2):
                    errores.append((i + 1, 1, op2, f"El operando '{op2}' es de tipo {tipo2}, no compatible con {tipo1}"))
                if texto_tok in COMPARADORES_INVALIDOS.get(tipo1, set()):
                    errores.append((i, 1, texto_tok, f"El operador '{texto_tok}' no es compatible con {tipo1}"))

    errores.sort(key=lambda e: (e[0], e[1]))
    return [(lexema, mensaje) for _, _, lexema, mensaje in errores]



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
        if tabla_funciones is not None and tabla_funciones.existe(nombre):
            tabla_errores.error_agregar(
                nombre, numero_linea,
                f"El nombre {nombre} ya esta en uso como funcion, no puede ser una variable",
            )
            exito = False
        else:
            exito = _declarar_variable_local(tipo, nombre, valor, numero_linea, tabla_simbolos, tabla_errores, tabla_funciones)            
        if exito:    
            nombre_local=nombre
            ambito["variables"][nombre] = respaldo
    else:
        tabla_errores.error_agregar(
            init_texto, numero_linea,
            f"La inicializacion del for no es una declaracion valida: '{init_texto}'",
        )

    variable_valida = bool(nombre_local and tabla_simbolos.si_existe(nombre_local))
    for lexema_err, mensaje in evaluar_condicion_compuesta(cond_texto, tabla_simbolos, tabla_funciones, validar_tipos=variable_valida):
        tabla_errores.error_agregar(lexema_err, numero_linea, mensaje)

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

func_header = rf"^(ETR|RN|CDNC)\s+({expresion_regular_funcion})\s*\((.*?)\)\s*\{{\s*$"
llamada_funcion = rf"{expresion_regular_funcion}\s*\(.*?\)"
patron_llamada_statement = rf"^({expresion_regular_funcion})\s*\((.*?)\)\s*;$"

def _procesar_func_header(m_func, numero_linea, tabla_funciones, tabla_errores, pila_ambitos, tabla_simbolos=None):    
    tipo_retorno = m_func.group(1)
    nombre_funcion = m_func.group(2)
    params_str = m_func.group(3).strip()

    params_nombres = []
    params_tipos = []
    if params_str:
        for p in params_str.split(","):
            m_p = re.match(rf"^(ETR|RN|CDNC)\s+({expresion_regular})$", p.strip())
            if m_p:
                params_nombres.append(m_p.group(2))
                params_tipos.append(m_p.group(1))

    if tabla_funciones.existe(nombre_funcion):
        tabla_errores.error_agregar(
            nombre_funcion, numero_linea,
            f"La funcion {nombre_funcion} ya habia sido declarada",
        )
    elif tabla_simbolos is not None and tabla_simbolos.si_existe(nombre_funcion):
        tabla_errores.error_agregar(
            nombre_funcion, numero_linea,
            f"El nombre {nombre_funcion} ya esta en uso como variable, no puede ser una funcion",
        )
    else:
        tabla_funciones.agregar(nombre_funcion, tipo_retorno, params_nombres, params_tipos)

    ambito = {
        "tipo": "funcion",
        "variables": {},
        "tipo_retorno": tipo_retorno,
        "nombre_funcion": nombre_funcion,
    }

    for p_nombre, p_tipo in zip(params_nombres, params_tipos):
        if tabla_simbolos is not None:
            respaldo = tabla_simbolos.obtener(p_nombre)
            tabla_simbolos.agregar(p_nombre, p_tipo, None, numero_linea)
            ambito["variables"][p_nombre] = respaldo
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
    if tabla_funciones is not None and tabla_funciones.existe(nombre):
        tabla_errores.error_agregar(
            nombre, numero_linea,
            f"El nombre {nombre} ya esta en uso como funcion, no puede ser una variable",
        )
        return
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
    

def _procesar_declaracion_multiple(tipo, lista_nombres, numero_linea, tabla_simbolos, tabla_errores, ambito_local=None, tabla_funciones=None):
    nombres = [n.strip() for n in lista_nombres.split(",")]

    for nombre in nombres:
        if tabla_funciones is not None and tabla_funciones.existe(nombre):
            tabla_errores.error_agregar(
                nombre, numero_linea,
                f"El nombre {nombre} ya esta en uso como funcion, no puede ser una variable",
            )
            continue
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
            _procesar_func_header(m_func, numero_linea, tabla_funciones, tabla_errores, pila_ambitos, tabla_simbolos)            
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
            _procesar_declaracion_multiple(tipo, lista_nombres, numero_linea, tabla_simbolos, tabla_errores, ambito_actual, tabla_funciones)            
        elif resultado[0] == "LlamadaFuncion":
            _, nombre_funcion, args_str = resultado
            if not tabla_funciones or not tabla_funciones.existe(nombre_funcion):
                tabla_errores.error_agregar(
                    nombre_funcion, numero_linea,
                    f"La funcion {nombre_funcion} no ha sido declarada",
                )
            else:
                info = tabla_funciones.funciones[nombre_funcion]
                args = [a.strip() for a in args_str.split(",")] if args_str.strip() else []
                if len(args) != len(info["parametros"]):
                    tabla_errores.error_agregar(nombre_funcion, numero_linea, f"La funcion '{nombre_funcion}' espera {len(info['parametros'])} argumentos, se pasaron {len(args)}")
                else:
                    for arg, tipo_p in zip(args, info["tipos_parametros"]):
                        errs = evaluar_expresion(tipo_p, arg, tabla_simbolos, tabla_funciones)
                        for err_lex, err_msg in errs:
                            tabla_errores.error_agregar(err_lex, numero_linea, err_msg)

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





