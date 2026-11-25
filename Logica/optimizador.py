import re

COMPARADORES = {"<", ">", "<=", ">=", "==", "!="}
_LITERAL = re.compile(r"""^(\d+(\.\d+)?|".*"|'.*')$""")


def es_temporal(texto):
    return bool(re.fullmatch(r"T\d+", str(texto)))


def _es_id(x):
    """True si x es una variable/temporal (algo que se lee o escribe)."""
    return (isinstance(x, str) and x.strip() != ""
            and x not in ("TRUE", "FALSE")
            and not _LITERAL.match(x.strip()))


def _es_cond(t):
    return t[1] in ("TRUE", "FALSE")


def _destino(t):
    """Destino (índice base 0) de un salto con destino numérico, o None."""
    obj, fuente, op, _ = t
    if op == "JMP" and isinstance(fuente, int):
        return fuente - 1
    if _es_cond(t) and isinstance(op, int):
        return op - 1
    return None


def _usos_defs(t):
    obj, fuente, op, _ = t
    if op == "JMP":
        return ({fuente} if _es_id(fuente) else set()), set()
    if _es_cond(t):
        return set(), set()
    usos = set()
    if _es_id(fuente):
        usos.add(fuente)
    if op != "=" and _es_id(obj):
        usos.add(obj)
    return usos, ({obj} if _es_id(obj) else set())


def _esencial(t, idx, ultimo):
    obj, fuente, op, _ = t
    return (op == "JMP" or _es_cond(t) or op in COMPARADORES or idx == ultimo)


def _vivas_salida(triplos, vivo):
    n = len(triplos)
    sig = [None] * (n + 1)
    for i in range(n - 1, -1, -1):
        sig[i] = i if vivo[i] else sig[i + 1]

    def siguiente(i):
        return sig[i] if 0 <= i <= n else None

    activos = [i for i in range(n) if vivo[i]]
    suc = {}
    for i in activos:
        t = triplos[i]
        d = _destino(t)
        if t[2] == "JMP" and isinstance(t[1], str):
            s = set(activos)
        elif d is not None and t[2] == "JMP":
            s = {siguiente(d)}
        elif d is not None and t[1] == "TRUE":
            s = {siguiente(d), siguiente(i + 1)}
        elif d is not None: 
            s = {siguiente(d)}
        else:
            s = {siguiente(i + 1)}
        suc[i] = {x for x in s if x is not None}

    live_in = {i: set() for i in activos}
    live_out = {i: set() for i in activos}
    cambio = True
    while cambio:
        cambio = False
        for i in reversed(activos):
            out = set()
            for s in suc[i]:
                out |= live_in[s]
            usos, defs = _usos_defs(triplos[i])
            nuevo_in = usos | (out - defs)
            if out != live_out[i] or nuevo_in != live_in[i]:
                live_out[i], live_in[i] = out, nuevo_in
                cambio = True
    return live_out


def optimizar_codigo_muerto(triplos):
    if not triplos:
        return []

    n = len(triplos)
    ultimo = n - 1
    vivo = [True] * n

    while True:
        live_out = _vivas_salida(triplos, vivo)
        eliminadas = False
        for i in range(n):
            if not vivo[i] or _esencial(triplos[i], i, ultimo):
                continue
            _, defs = _usos_defs(triplos[i])
            if defs and not (defs & live_out[i]):
                vivo[i] = False
                eliminadas = True
        if not eliminadas:
            break

    prefijo = [0] * (n + 1)
    for i in range(n):
        prefijo[i + 1] = prefijo[i] + (1 if vivo[i] else 0)

    def nueva_linea(linea_vieja):
        idx = max(0, min(linea_vieja - 1, n))
        return prefijo[idx] + 1

    final = []
    for i, t in enumerate(triplos):
        if not vivo[i]:
            continue
        obj, fuente, op, renglon = t
        if op == "JMP" and isinstance(fuente, int):
            fuente = nueva_linea(fuente)
        elif _es_cond(t) and isinstance(op, int):
            op = nueva_linea(op)
        elif (op == "=" and isinstance(fuente, str) and fuente.isdigit()
              and i + 1 < n and str(triplos[i + 1][0]).startswith("ret_")
              and triplos[i + 1][1] == obj):
            fuente = str(nueva_linea(int(fuente)))
        final.append((obj, fuente, op, renglon))
    return final