from estructura import TablaError, TablaSimbolos, TablaFunciones
from analizador import analizador, obtener_lexemas

codigo_ejemplo = """
ETR !bar1 = 10;
RN !bar2 = 2.5;
CDNC !bar3 = "hola";
ETR !bar4, !bar5;

ETR !func1() {
ETR !bar1 = 100;
ETR !bar6 = !bar1 + 5;
return !bar6;
}

RN !func2() {
return 3.14;
}

CDNC !func3() {
return 5;
}

for(ETR !bar7 = 0; !bar7<5; !bar7++){
!bar4 = !func1() + 1;
for(ETR !bar8 = 0; !bar8<3; !bar8++){
!bar5 = !bar7 + !bar8;
}
}

!bar2 = !func2() * 2.0;
!func1();
!func9();
!bar4 = !func3();
!bar7 = 1;
CDNC !bar9 = "a" + 5;
"""



ts = TablaSimbolos()
te = TablaError()
tf = TablaFunciones()

analizador(codigo_ejemplo, ts, te, tf)
lineas_con_error = {error.linea for error in te.tabla_err()}
lexemas = obtener_lexemas(codigo_ejemplo, ts, tf, lineas_con_error)


print("=== TABLA DE LEXEMAS ===")
print(f'{"lexema":<10} | tipo de dato')
print("-" * 30)
for lexema, tipo in lexemas:
    print(f'{lexema:<10} | {tipo if tipo else ""}')

print()
print("=== TABLA DE ERRORES ===")
for e in te.tabla_err():
    print(e)