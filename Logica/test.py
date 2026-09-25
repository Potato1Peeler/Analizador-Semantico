from estructura import TablaError, TablaSimbolos
from analizador import analizador, obtener_lexemas

codigo_ejemplo = '''ETR !bar1 = 5;
RN !bar2 = 3.5;
CDNC !bar3 = "hola";

for(ETR !bar4 = 0; !bar4<5; !bar4++){
!bar1 = !bar1 + 1;
}

for(RN !bar5 = 0.0; !bar5<=10.0; !bar5 = !bar5 + 2.5){
for(ETR !bar6 = 0; !bar6<!bar1; !bar6++){
!bar2 = !bar2 + 1.0;
}
}

!bar4 = 1;
!bar6 = 1;

for(CDNC !bar7 = "a"; !bar7<"z"; !bar7++){
}

for(ETR !bar8 = 10; !bar8>0; !bar8--){
}
'''


ts = TablaSimbolos()
te = TablaError()

analizador(codigo_ejemplo, ts, te)
lineas_con_error = {error.linea for error in te.tabla_err()}
lexemas = obtener_lexemas(codigo_ejemplo, ts, lineas_con_error)


print("=== TABLA DE LEXEMAS ===")
print(f'{"lexema":<10} | tipo de dato')
print("-" * 30)
for lexema, tipo in lexemas:
    print(f'{lexema:<10} | {tipo if tipo else ""}')

print()
print("=== TABLA DE ERRORES ===")
for e in te.tabla_err():
    print(e)