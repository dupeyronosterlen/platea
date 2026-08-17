#!/usr/bin/env python3
"""
Registro central de piezas gráficas generadas — el archivo que Ag-14 describe
en su playbook.md como "Bitácora de aprendizaje: frase → registro → reacción"
pero que nunca se había implementado (existía solo como idea, no como archivo).

Por qué existe: sin esto, cada script de cartel genera imágenes "sueltas" — no
hay forma de saber después CUÁL frase/foto/tono estaba en cada pieza publicada,
así que cuando llegan las métricas (CTR, guardados, conversiones) no se pueden
atribuir a nada. Este módulo hace que CADA script de 08_Productor-Audiovisual
deje un rastro: qué se generó, con qué copy, con qué tono/registro, para qué
canal — y deja columnas vacías para que Ag-06 (o Dirección a mano) rellene métricas
después de publicar.

Uso desde cualquier script generador:

    from registro_piezas import registrar_pieza
    registrar_pieza(
        script="generar_cartel_accion.py",
        archivo="carteles-s2/accion/accion-IMG_7451-square.png",
        foto_fuente="IMG_7451.jpg",
        formato="square",
        tono_visual="Drama",              # Drama / Archivo / Invitación (tonos-visuales.md)
        categoria="A",                     # A/B/C/D (carteleria-workflow-agentes.md)
        copy_titulo="EL GORILA",
        copy_secundario="con Humberto Dupeyrón · basado en Informe para una Academia",
        registro="DRAMA",                  # DRAMA / HUMOR / EXPERIMENTO (vocabulario de Ag-14)
        canal_destino="Google Ads",
        notas="",
    )

Para rellenar métricas después de publicar (Ag-06 o a mano):

    from registro_piezas import actualizar_metricas
    actualizar_metricas("carteles-s2/accion/accion-IMG_7451-square.png",
                         ctr=2.3, guardados=14, conversiones=0, notas="probado 20-27 jul")
"""

import csv
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
REGISTRO_CSV = REPO / "05_Activos/el-gorila/carteles-s2/registro-piezas.csv"

CAMPOS = [
    "fecha", "script", "archivo", "foto_fuente", "formato", "tono_visual",
    "categoria", "copy_titulo", "copy_secundario", "registro", "canal_destino",
    "estado", "ctr", "guardados", "conversiones", "notas",
]


def _asegurar_csv():
    if not REGISTRO_CSV.exists():
        REGISTRO_CSV.parent.mkdir(parents=True, exist_ok=True)
        with open(REGISTRO_CSV, "w", newline="", encoding="utf-8") as fh:
            csv.DictWriter(fh, fieldnames=CAMPOS).writeheader()


def registrar_pieza(
    script, archivo, foto_fuente="", formato="", tono_visual="", categoria="",
    copy_titulo="", copy_secundario="", registro="", canal_destino="",
    estado="generado", notas="",
):
    """Agrega una fila nueva. No falla si el CSV no existe — lo crea."""
    _asegurar_csv()
    fila = {
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "script": script,
        "archivo": str(archivo),
        "foto_fuente": foto_fuente,
        "formato": formato,
        "tono_visual": tono_visual,
        "categoria": categoria,
        "copy_titulo": copy_titulo,
        "copy_secundario": copy_secundario,
        "registro": registro,
        "canal_destino": canal_destino,
        "estado": estado,
        "ctr": "",
        "guardados": "",
        "conversiones": "",
        "notas": notas,
    }
    with open(REGISTRO_CSV, "a", newline="", encoding="utf-8") as fh:
        csv.DictWriter(fh, fieldnames=CAMPOS).writerow(fila)


def actualizar_metricas(archivo, ctr=None, guardados=None, conversiones=None, estado=None, notas=None):
    """Reescribe la fila de `archivo` (match exacto de ruta) con las métricas
    dadas. Si hay más de una fila con el mismo archivo, actualiza la última."""
    _asegurar_csv()
    with open(REGISTRO_CSV, newline="", encoding="utf-8") as fh:
        filas = list(csv.DictReader(fh))

    idx = None
    for i, fila in enumerate(filas):
        if fila["archivo"] == str(archivo):
            idx = i
    if idx is None:
        raise ValueError(f"No se encontró '{archivo}' en {REGISTRO_CSV}")

    if ctr is not None:
        filas[idx]["ctr"] = ctr
    if guardados is not None:
        filas[idx]["guardados"] = guardados
    if conversiones is not None:
        filas[idx]["conversiones"] = conversiones
    if estado is not None:
        filas[idx]["estado"] = estado
    if notas is not None:
        filas[idx]["notas"] = notas

    with open(REGISTRO_CSV, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=CAMPOS)
        writer.writeheader()
        writer.writerows(filas)


def resumen_por_registro():
    """Devuelve qué 'registro' (DRAMA/HUMOR/EXPERIMENTO) tiene mejor CTR
    promedio — lo que pide el KPI de Ag-14 ('qué registro gana semana a
    semana'). Ignora filas sin CTR todavía."""
    _asegurar_csv()
    with open(REGISTRO_CSV, newline="", encoding="utf-8") as fh:
        filas = [f for f in csv.DictReader(fh) if f.get("ctr")]

    por_registro = {}
    for f in filas:
        r = f["registro"] or "(sin etiquetar)"
        por_registro.setdefault(r, []).append(float(f["ctr"]))

    return {r: sum(v) / len(v) for r, v in por_registro.items()}


if __name__ == "__main__":
    _asegurar_csv()
    resumen = resumen_por_registro()
    if not resumen:
        print(f"Registro en {REGISTRO_CSV.relative_to(REPO)} — sin métricas cargadas todavía.")
    else:
        print("CTR promedio por registro:")
        for r, ctr in sorted(resumen.items(), key=lambda x: -x[1]):
            print(f"  {r}: {ctr:.2f}%")
