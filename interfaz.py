import tkinter as tk
from tkinter import ttk
from Logica.analizador import obtener_lexemas
from Logica.analizador import analizador as ejecutar_analisis
from Logica.estructura import TablaSimbolos, TablaError, TablaFunciones

class compilador:
  def __init__(self, root):
    # definiendo tamaño de la ventana
    self.root = root
    self.root.title("Compilador")
    self.root.state('zoomed')

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
    self.numeros = tk.Canvas(
        contenedor_compi,
        width=40,
        background="#f0f0f0",
        highlightthickness=0,
        border=0
    )
    self.numeros.pack(side="left", fill="y")

    # scrollbar
    self.scrollbar = tk.Scrollbar(contenedor_compi, orient = "vertical")
    self.scrollbar.pack(side = "right", fill = "y")

    # área principal para el código
    self.codigo_compi = tk.Text(contenedor_compi, wrap = "none", undo = True, font = ("Consolas", 11), yscrollcommand = self.on_code_scroll, highlightthickness=0, spacing1=0, spacing2=0, spacing3=0)
    self.codigo_compi.pack(side = "left", fill = "both", expand = True)

    # se configura el scrollbar para que se mueva todo el contenido de nuestro contenedor

    self.scrollbar.config(command = self.codigo_compi.yview)

    # escucha cuando el texto es modificado
    self.codigo_compi.bind('<<Modified>>', self.on_modif)
    self.codigo_compi.bind('<KeyRelease>', self.actualizar)

    self.codigo_compi.bind('<MouseWheel>', self.scroll_rueda)
    self.numeros.bind('<MouseWheel>', self.scroll_rueda)

    # boton para compilar
    self.boton = tk.Button(self.pantalla_compi, text = "Compilar", width = 15, font = ("Helvetica", 10), pady = 5, command = self.compilar)
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

    self.scroll_vertical_sim = tk.Scrollbar(self.tabla_simbolos, orient="vertical", command=self.columnas_simbolos.yview)
    self.scroll_vertical_sim.pack(side="right", fill="y")

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

    self.columnas_errores.column("Token error", width = 80, anchor = "center", stretch = False)
    self.columnas_errores.column("Línea error", width = 80, anchor = "center", stretch = False)
    self.columnas_errores.column("Lexema", width = 80, anchor = "center", stretch = False)
    self.columnas_errores.column("Descripción", width = 450, anchor = "center", stretch = False)

    self.scroll_vertical_error = tk.Scrollbar(self.tabla_errores, orient = "vertical", command = self.columnas_errores.yview)
    self.scroll_vertical_error.pack(side = "right", fill = "y")

    self.scroll_horizontal_error = tk.Scrollbar(self.tabla_errores, orient = "horizontal", command = self.columnas_errores.xview)
    self.scroll_horizontal_error.pack(side = "bottom", fill = "x")

    self.columnas_errores.configure(
        yscrollcommand = self.scroll_vertical_error.set,
        xscrollcommand = self.scroll_horizontal_error.set
    )

    self.columnas_errores.pack(fill = "both", expand = True, padx = 10, pady = 10)

  def on_modif(self, event):
      if self.codigo_compi.edit_modified():
         self.actualizar()

         self.codigo_compi.edit_modified(False)

  def actualizar(self, event=None):
    # Limpiar el canvas
    self.numeros.delete("all")

    # Obtener la primera y última línea visibles
    primera = self.codigo_compi.index("@0,0")
    linea_ini = int(primera.split(".")[0])

    altura = self.codigo_compi.winfo_height()
    ultima = self.codigo_compi.index(f"@0,{altura}")
    linea_fin = int(ultima.split(".")[0])

    for i in range(linea_ini, linea_fin + 2):
        info = self.codigo_compi.dlineinfo(f"{i}.0")
        if info:
            x, y, ancho, alto, baseline = info
            self.numeros.create_text(
                35, y + 1,
                text=str(i),
                anchor="ne",
                font=("Consolas", 11),
                fill="#555"
            )

  def compilar(self):

    codigo = self.codigo_compi.get("1.0", "end-1c")

    for item in self.columnas_simbolos.get_children():
        self.columnas_simbolos.delete(item)
    for item in self.columnas_errores.get_children():
        self.columnas_errores.delete(item)

    tabla_simbolos = TablaSimbolos()
    tabla_errores = TablaError()
    tabla_funciones = TablaFunciones()

    ejecutar_analisis(codigo, tabla_simbolos, tabla_errores, tabla_funciones)

    lexemas = obtener_lexemas(codigo, tabla_simbolos, tabla_funciones)

    for texto, tipo in lexemas:
       tipo_mostrar = tipo if tipo else "-"
       self.columnas_simbolos.insert(
          "", "end",
          values = (texto, tipo_mostrar)
       )

    for error in tabla_errores.tabla_err():
       self.columnas_errores.insert(
          "", "end",
          values = (error.token, error.linea, error.lexema, error.descripcion)
       )

  def scroll_rueda(self, event):
     delta = int(-1 * (event.delta / 120))
     self.codigo_compi.yview_scroll(delta, "units")
     return "break"

  def on_code_scroll(self, *args):
    self.scrollbar.set(*args)
    self.actualizar()

if __name__ == "__main__":
  root = tk.Tk ()
  app = compilador(root)
  root.mainloop()