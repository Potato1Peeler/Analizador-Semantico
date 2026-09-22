class Lexema:
    #Se inicializa el constructor que nos permite ejecutarlo cada q se crea un objeto e inicia autmaticamente los datos
    def __init__(self, nombre, tipo, valor, linea):
        self.nombre = nombre
        self.tipo = tipo
        self.valor = valor
        self.linea = linea
    #La forma en la que imprimimos el texto en un formato en especifico
    def __repr__(self):
        return f"Nombre: {self.nombre}, Tipo: {self.tipo}"

#Clase que define los atributos de los errores
class ErrorSem:
    #Constructor que inicaliza los atributos de la clase
    def __init__(self, linea, tipo_error, descripcion):
        self.linea = linea
        self.tipo_error = tipo_error
        self.descripcion = descripcion
    #Formato de impresion de error
    def __repr__(self):
        return f"linea = {self.linea}, tipo = {self.tipo_error}, '{self.descripcion}')"

#Clase que dfine las acciones de la tabla de simbolos
class TablaSimbolos:
    #Inicializa el diccionario que se va a utilizar
    def __init__(self):
        self.simbolos = {}

    #Se asegura si el lexema esta en el deccionario devolviendo true o false
    def si_existe(self, nombre):
        return nombre in self.simbolos 

    #Agrega al diccionario en base el nombre y los atributos declarados en la clase lexema
    def agregar(self, nombre, tipo, valor, linea):
        self.simbolos[nombre] = Lexema(nombre, tipo, valor, linea)

    #obtiene el nombre asociado al simbolo
    def obtener(self, nombre):
        return self.simbolos.get(nombre)

    #Actualiza el nombre del lexema en base a uno nuevo siempre y cuando el lexema exista
    def actualizar(self, nombre, new_valor):
        if self.si_existe(nombre):
            self.simbolos[nombre].valor = new_valor

    #Muestra la tabla en una lista
    def tabla(self):
        return list(self.simbolos.values())

#Clase que define la tabla de errores
class TablaError:

    #Constructor que inicia un array
    def __init__(self):
        self.error = []
    #Agrega al array en base alos atributos definidos en la clase ErrorSem
    def error_agregar(self, linea, descripcion, tipo_error):
        self.error.append(ErrorSem(linea, tipo_error, descripcion))
    #Define si exsiten errores en base al tamaño del arreglo
    def si_existe_error(self):
        return len(self.error) > 0
    #Devuelve en lista los errores
    def tabla_err(self):
        return list(self.error)



    
