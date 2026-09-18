import re
tipos_datps_validos= {
    "ETR": "entero",
    "RN": "real",
    "CDNC": "cadena",
}

#Expresion regular de variables
expresion_regular = r"!bar[1-9]+"

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

#Funcion q nos dice el tipo de dato en base al patron de arriba
def tipo_dato(valor):
    if re.match(entero, valor):
        return "ETR"
    if re.match(real, valor):
        return "RN"
    if re.match(cadena, valor):
        return "CDNC"
    return "Vacio"

#Test
valores_prueba = ['5', '3.14', '\"hola\"', '3.', 'abc', '', '\"\"', '5a']

#Imprime en lista el test y lo comprueba con la funcion de tipo_dato
print(f'{"Lexema"!r:10} | "tipo_dato')
for i in valores_prueba:
    print(f'{i!r:10} -> {tipo_dato(i)}')



