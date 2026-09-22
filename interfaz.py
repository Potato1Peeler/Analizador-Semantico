import tkinter as tk
from tkinter import ttk

class compilador:
  def __init__(self, root):
    # definiendo tamaño de la ventana
    self.root = root
    self.root.title("Compilador")
    self.root.geometry("1200x600")

    # configuración de la ventana con la clase frame, ya que es reutilizable
    pantalla_inicio = tk.Frame(root, padx=10, pady=10)
    pantalla_inicio.pack(fill="both", expand=True)

    # distribución de la pantalla

    pantalla_inicio.columnconfigure(0, weight = 0)
    pantalla_inicio.columnconfigure(1, weight = 1)
    pantalla_inicio.rowconfigure(0, weight= 1)

    # distribucion del input del compilador

    self.pantalla_compi = tk.Frame(pantalla_inicio, bd = 2, relief = "solid")
    self.pantalla_compi.grid(row = 0, column= 0, sticky= "nsew", padx=(0, 10)) # uso del grid, pero como sólo va a ser el mero input no hay necesidad de crearlo en formato de tabla

    # nombre del apartado del compilador
    nombre_compi = tk.Label(self.pantalla_compi, text="Compilador", font=("Helvetica", 11))
    nombre_compi.pack(pady=10)

    contenedor_compi = tk.Frame(self.pantalla_compi, bd = 2, relief = "sunken")
    contenedor_compi.pack(fill = "both", expand = True, padx = 20, pady = 10)

    # creación del apartado donde irán los números de línea
    self.numeros = tk.Text(contenedor_compi, width = 4, padx = 4, takefocus = 0, border = 0, background = "#f0f0f0", state = 'disabled')
    self.numeros.pack(side = "left", fill = "y")

    # scrollbar
    self.scrollbar = tk.Scrollbar(contenedor_compi, orient = "vertical")
    self.scrollbar.pack(side = "right", fill = "y")

    # área principal para el código
    self.codigo_compi = tk.Text(contenedor_compi, wrap = "none", undo = True, font = ("Consolas", 11), yscrollcommand = self.scrollbar.set)
    self.codigo_compi.pack(side = "left", fill = "both", expand = True)

    # se configura el scrollbar para que se mueva todo el contenido de nuestro contenedor

    self.scrollbar.config(command = self.sincronizar_scroll)

    # escucha cuando el texto es modificado
    self.codigo_compi.bind('<<Modified>>', self.on_modif)
    self.codigo_compi.bind('<KeyRelease>', self.actualizar)

    # boton para compilar
    self.boton = tk.Button(self.pantalla_compi, text = "Compilar", width = 15, font = ("Helvetica", 10), pady = 5)
    self.boton.pack(pady = 20)

    # parte derecha de la ventana

    self.pantalla_derecha = tk.Frame(pantalla_inicio)
    self.pantalla_derecha.grid(row = 0, column = 1, sticky = "nsew")
    self.pantalla_derecha.rowconfigure(0, weight = 1)
    self.pantalla_derecha.rowconfigure(1, weight = 1)
    self.pantalla_derecha.columnconfigure(0, weight = 1)

    # apartado tabla de símbolos

    self.tabla_simbolos = tk.Frame(self.pantalla_derecha, bd = 2, relief = "solid")
    self.tabla_simbolos.grid(row = 0, column = 0, sticky = "nsew", pady = (0, 10))

    # titulo del apartado
    titulo_simbolo = tk.Label(self.tabla_simbolos, text = "Tabla de símbolos", font = ("Helvetica", 11))
    titulo_simbolo.pack(pady = 5)

    # creacion de las columnas de la tabla de símbolos
    def_columnas = ("Lexema", "Tipo de dato")
    self.columnas_simbolos = ttk.Treeview(self.tabla_simbolos, columns = def_columnas, show = "headings", height =5)
    self.columnas_simbolos.heading("Lexema", text = "Lexema")
    self.columnas_simbolos.heading("Tipo de dato", text = "Tipo de dato")
    self.columnas_simbolos.column("Lexema", width = 150, anchor = "center")
    self.columnas_simbolos.column("Tipo de dato", width = 150, anchor = "center")
    self.columnas_simbolos.pack(fill = "both", expand = True, padx = 10, pady = 10)

    # apartado tabla de errores

    self.tabla_errores = tk.Frame(self.pantalla_derecha, bd = 2, relief = "solid")
    self.tabla_errores.grid(row = 1, column = 0, sticky = "nsew")

    # titulo tabla de errores
    titulo_errores = tk.Label(self.tabla_errores, text = "Tabla de errores", font = ("Helvetica", 11))
    titulo_errores.pack(pady = 5)

    # creación de las columnas de la tabla de errores
    def_colum_error = ("Token error", "Línea error", "Lexema", "Descripción")
    self.columnas_errores = ttk.Treeview(self.tabla_errores, columns = def_colum_error, show = "headings", height = 5)
    self.columnas_errores.heading("Token error", text = "Token error")
    self.columnas_errores.heading("Línea error", text = "Línea error")
    self.columnas_errores.heading("Lexema", text = "Lexema")
    self.columnas_errores.heading("Descripción", text = "Descripción")
    self.columnas_errores.column("Token error", width = 50, anchor = "center")
    self.columnas_errores.column("Línea error", width = 50, anchor = "center")
    self.columnas_errores.column("Lexema", width = 50, anchor = "center")
    self.columnas_errores.column("Descripción", width = 200, anchor = "center")
    self.columnas_errores.pack(fill = "both", expand = True, padx = 10, pady = 10)

    #luego agrego la lógica de esto teehee
  def sincronizar_scroll(self, *args):
      pass

  def on_modif(self, event):
      pass

  def actualizar(self, event = None):
      pass

if __name__ == "__main__":
  root = tk.Tk ()
  app = compilador(root)
  root.mainloop()