from estructura import TablaError, TablaSimbolos
from analizador import analizador, obtener_lexemas

codigo_ejemplo = """
ETR !bar1 = 5 
ETR !bar2 
RN !bar3 = 1.1 


!bar1 = 15
!bar2 = !bar1 - 10
"homeless"
"""

ts = TablaSimbolos()
te = TablaError()

analizador(codigo_ejemplo, ts, te)

lexemas = obtener_lexemas(codigo_ejemplo, ts)

print("=== TABLA DE LEXEMAS ===")
print(f'{"lexema":<10} | tipo de dato')
print("-" * 30)
for lexema, tipo in lexemas:
    print(f'{lexema:<10} | {tipo if tipo else ""}')

print()
print("=== TABLA DE ERRORES ===")
for e in te.tabla_err():
    print(e)