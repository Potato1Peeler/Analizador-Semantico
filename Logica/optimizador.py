import re

def es_temporal(texto):
    return bool(re.fullmatch(r"T\d+", str(texto)))

def optimizar_codigo_muerto(triplos):
    if not triplos:
        return []
    vivos = set()
    conservados = []
    ultimo_idx = len(triplos) - 1

    for idx in range(len(triplos) - 1, -1, -1):
        obj, fuente, op, renglon = triplos[idx]

        if op in ("JMP", "TRUE", "FALSE"):
            conservados.append((obj, fuente, op, renglon))
            if fuente and isinstance(fuente, str) and str(fuente) not in ("TRUE", "FALSE"):
                vivos.add(fuente)
            if obj: vivos.add(obj)
            continue

        if idx == ultimo_idx:
            conservados.append((obj, fuente, op, renglon))
            if obj: vivos.add(obj)
            if fuente and isinstance(fuente, str) and str(fuente) not in ("TRUE", "FALSE"):
                vivos.add(fuente)
            continue

        if obj not in vivos:
            continue # Se elimina

        conservados.append((obj, fuente, op, renglon))
        
        if op == "=":
            vivos.discard(obj)
        
        if fuente and isinstance(fuente, str) and str(fuente) not in ("TRUE", "FALSE"):
            vivos.add(fuente)

    triplos_opt = list(reversed(conservados))

    mapa_lineas = {}
    nueva_linea = 1
    for idx, t in enumerate(triplos):
        if t in triplos_opt:
            mapa_lineas[idx + 1] = nueva_linea
            nueva_linea += 1

    final_triplos = []
    for obj, fuente, op, renglon in triplos_opt:
        if op in ("JMP", "TRUE", "FALSE") and (isinstance(fuente, int) or str(fuente).isdigit()):
            viejo_destino = int(fuente)
            nuevo_destino = mapa_lineas.get(viejo_destino, nueva_linea)
            final_triplos.append((obj, nuevo_destino, op, renglon))
        else:
            final_triplos.append((obj, fuente, op, renglon))

    return final_triplos