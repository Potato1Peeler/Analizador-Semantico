from estructura import TablaError, TablaSimbolos
from analizador import analizador, obtener_lexemas

codigo_ejemplo =  """
ETR !bar1 = 10;
RN !bar2 = 2.5;
CDNC !bar3 = "hola";
ETR !bar4, !bar5, !bar6;
RN !bar7;

!bar4 = 20;
!bar7 = 8;
!bar5 = !bar1 + !bar4;
!bar3 = !bar3 + " mundo";
!bar6 = !bar1 / 2;
!bar2 = !bar1 + !bar7;
!bar9 = 5;
ETR !bar1 = 99;
"Homeless"
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