#!/usr/bin/env python3
"""
Audit de taquilla por función — para liquidación con el teatro.

Genera, por cada función, un audit escrito listo para enviar al administrador del
venue (hoy: Camilo Contreras, Teatro Wilberto Cantón) con:
  - boletos pagados reales, desglosados por tipo y por canal de venta
  - detalle transacción por transacción con fecha y hora
  - cortesías reportadas aparte (no generan taquilla)
  - base de cálculo de la renta del coproductor
  - cheque al teatro: $6,500 menos Ticketmaster (técnicos al corte, fuera)
    ver 04_Operaciones/liquidaciones/pagos-teatro/MODELO-PAGO.md

Fuente de los datos:
  - Boletera propia  -> Stripe Checkout Sessions (metadata trae función, tipo y hora).
                        El KV / worker de reporte NO sirve: devuelve ingresos 0 y por_tipo {}.
  - Canales externos -> 04_Operaciones/liquidaciones/canales-externos.json (captura manual;
                        Teatrando y Cartelera de Teatro no escriben en nuestro inventario).

Uso:
    python3 audit_liquidacion.py                      # última función ya ocurrida
    python3 audit_liquidacion.py --funcion 2026-08-01
    python3 audit_liquidacion.py --desde 2026-07-25 --hasta 2026-08-01
    python3 audit_liquidacion.py --email              # solo imprime el cuerpo del correo

Corre los domingos 8:20 vía launchd (com.platea.audit-liquidacion) para que el audit
de la función del sábado esté listo el lunes por la mañana.
"""

import argparse
import csv
import datetime as dt
import json
import os
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SALIDA = ROOT / "04_Operaciones" / "liquidaciones"
CANALES_JSON = SALIDA / "canales-externos.json"
CORTESIAS_JSON = ROOT / "04_Operaciones" / "cortesias-conocidas.json"

TZ = dt.timezone(dt.timedelta(hours=-6))  # CDMX

CANAL_ETIQUETA = {
    "Boletera propia": "Venta directa",
    "Venta en taquilla": "Taquilla",
    "Ticketmaster": "Ticketmaster",
    "Cartelera de Teatro": "Cartelera de Teatro",
    "Teatrando": "Teatrando",
}

_CAT_SUFIJOS = (
    " (Ticketmaster)",
    " (Cartelera de Teatro)",
    " (Teatrando)",
)


def _etiqueta_canal(nombre):
    return CANAL_ETIQUETA.get(nombre, nombre)


def _categoria_export(cat):
    out = cat or ""
    for suf in _CAT_SUFIJOS:
        if out.endswith(suf):
            out = out[: -len(suf)]
    for trozo in (
        ", reprogramado del 18 jul",
        ", reprogramado del 8 ago",
        ", reprogramado al 25 jul",
        ", reprogramado al 1 ago",
    ):
        out = out.replace(trozo, "")
    return out


def _fecha_anexo(fecha_hora):
    """Solo fecha, sin hora (el corte no debe verse como un checkout en línea)."""
    if not fecha_hora:
        return "—"
    return fecha_hora.split()[0]


def _lugares(filas, cortesias):
    ocup = {"platea": 0, "galeria": 0}
    for r in filas or []:
        n = int(r.get("boletos") or 0)
        sec = (r.get("seccion") or "platea").lower().replace("í", "i")
        if "galer" in sec:
            ocup["galeria"] += n
        else:
            ocup["platea"] += n
    ocup["platea"] += int(cortesias or 0)
    return {
        "platea": {
            "aforo": AFORO_PLATEA,
            "ocupados": ocup["platea"],
            "disponibles": max(0, AFORO_PLATEA - ocup["platea"]),
        },
        "galeria": {
            "aforo": AFORO_GALERIA,
            "ocupados": ocup["galeria"],
            "disponibles": max(0, AFORO_GALERIA - ocup["galeria"]),
        },
    }

# Compras internas que nunca deben aparecer en un audit hacia el teatro.
CUPONES_PRUEBA = {"PRUEBA99"}
EMAILS_INTERNOS = {
    "dupeyronosterlen@gmail.com",
    "osterdupeyron@gmail.com",
    "elgorilateatro@gmail.com",
}

# Funciones que por acuerdo quedan fuera del esquema ordinario de liquidación.
# Se siguen reportando (para que el venue vea el movimiento completo), pero con nota
# y sin renta aplicable. Vaciar el dict si alguna vuelve al esquema ordinario.
FUNCIONES_EXCLUIDAS = {}

# Nota que se imprime en el reporte de una función con circunstancias particulares.
NOTAS_FUNCION = {
    "2026-07-18": [
        "Función privada de prensa e invitación. Renta del recinto al 50 %, según lo convenido.",
    ],
}

# Funciones sin renta aplicable (no entran al esquema ordinario de liquidación).
SIN_RENTA = set()

# Funciones que se reportan solo con asistencia, sin desglose de ingresos.
SOLO_ASISTENCIA = set()

# Funciones con arreglo distinto al ordinario: (renta al teatro, técnicos, motivo).
RENTA_ESPECIAL = {
    "2026-07-18": (3250.0, 1650.0,
                   "Renta del recinto al 50 %, función de prensa e invitación."),
}

# Mínimo garantizado por función, y cómo se compone: parte se paga directo al
# personal técnico y el resto al teatro (confirmado por Dirección, 2026-08-05).
RENTA_PISO = 8150.0
RENTA_TEATRO = 6500.0
RENTA_TECNICOS = 1650.0
TECNICO_DIRECTO = "Miguel Ángel Fernández (tramoya)"
RENTA_PCT = 0.20

OBRA = "EL GORILA — Monólogo con Humberto Dupeyrón"
VENUE = "Teatro Wilberto Cantón (SOGEM)"
DIRECCION = "José María Velasco 59, Col. San José Insurgentes, C.P. 03900, Benito Juárez, CDMX"
HORARIO = "18:00"
AFORO = 325
AFORO_PLATEA = 250
AFORO_GALERIA = 75
EMISOR = "Producciones Dupeyrón"
EMISOR_FIRMA = "Dirección Dupeyrón — Dirección de Producción"

# Folio del reporte: EG-S2-### en el orden de las funciones de la temporada.
FOLIO_PREFIJO = "EG-S2"

# Tarifas vigentes por fecha de COMPRA. La preventa cerró el 25 jul 2026 inclusive.
# Se usan para repartir el importe de una orden mixta entre sus tipos de boleto; si la
# suma no cuadra contra lo cobrado (cupón, promoción), se cae a un reparto proporcional.
TARIFAS = [
    ("2026-07-25", {"general": 350.0, "estudiante": 245.0}),   # preventa, hasta esta fecha
    ("9999-12-31", {"general": 400.0, "estudiante": 280.0}),   # regular
]


def _tarifa(fecha_compra):
    for corte, precios in TARIFAS:
        if fecha_compra <= corte:
            return precios
    return TARIFAS[-1][1]


def _repartir(items, total, fecha_compra):
    """Importe por línea. Usa la tarifa vigente si cuadra; si no, prorratea."""
    precios = _tarifa(fecha_compra)
    esperado = sum(precios.get(i["tipo"], 0) * i["cantidad"] for i in items)
    if esperado and abs(esperado - total) < 0.01:
        return [precios[i["tipo"]] * i["cantidad"] for i in items]
    n = sum(i["cantidad"] for i in items)
    return [round(total * i["cantidad"] / n, 2) for i in items]


# Nombre comercial de cada tarifa, para el reporte formal. La norma de espectáculos
# públicos pide distinguir preventa / taquilla / cortesía, así que la categoría se
# arma con el precio unitario efectivamente cobrado.
BASE_TIPO = {"general": "General", "estudiante": "Estudiante / INAPAM / Maestro"}


def _categoria(tipo, pu, fecha_compra):
    base = BASE_TIPO.get(tipo, tipo.title())
    precios = _tarifa(fecha_compra)
    if abs(pu - precios.get(tipo, -1)) < 0.01:
        return f"{base}, preventa" if fecha_compra <= TARIFAS[0][0] else base
    return f"{base}, promoción"


# ----------------------------------------------------------------- utilidades

def _env(nombre, *rutas):
    """Lee una variable de los .env de los agentes sin ejecutarlos."""
    if os.environ.get(nombre):
        return os.environ[nombre]
    for r in rutas:
        p = ROOT / r
        if not p.exists():
            continue
        for linea in p.read_text(encoding="utf-8", errors="ignore").splitlines():
            linea = linea.strip()
            if linea.startswith(nombre + "="):
                return linea.split("=", 1)[1].strip().strip('"').strip("'")
    return None


def _stripe(path):
    """GET a la API de Stripe vía curl.

    Se usa curl y no urllib a propósito: el Python del sistema no resuelve la
    cadena de certificados de api.stripe.com y truena con CERTIFICATE_VERIFY_FAILED.
    """
    key = _env("STRIPE_RESTRICTED_KEY", "01_Agentes/03_Media-Buyer/.env")
    if not key:
        sys.exit("ERROR: falta STRIPE_RESTRICTED_KEY en 01_Agentes/03_Media-Buyer/.env")
    out = subprocess.run(
        ["curl", "-sS", "-u", f"{key}:", f"https://api.stripe.com/v1/{path}"],
        capture_output=True, text=True, timeout=60,
    )
    if out.returncode != 0:
        sys.exit(f"ERROR curl: {out.stderr.strip()}")
    data = json.loads(out.stdout)
    if "error" in data:
        sys.exit(f"ERROR Stripe: {data['error'].get('message')}")
    return data


def _paginar(recurso):
    items, after = [], None
    while True:
        q = f"{recurso}?limit=100"
        if after:
            q += f"&starting_after={after}"
        d = _stripe(q)
        items += d["data"]
        if not d.get("has_more") or not d["data"]:
            return items
        after = d["data"][-1]["id"]


def _money(x):
    return f"${x:,.2f}"


# ----------------------------------------------------------------- extracción

def ventas_boletera(funciones):
    """Boletos pagados reales por función, desde Stripe. Netea reembolsos y pruebas."""
    sesiones = _paginar("checkout/sessions")
    reembolsados = {r["payment_intent"] for r in _paginar("refunds")}

    tx = defaultdict(list)
    for s in sesiones:
        if s.get("payment_status") != "paid":
            continue
        m = s.get("metadata", {})
        f = m.get("fecha")
        if f not in funciones:
            continue
        if s.get("payment_intent") in reembolsados:
            continue
        email = (m.get("email") or s.get("customer_details", {}).get("email") or "").strip().lower()
        if email in EMAILS_INTERNOS or m.get("codigoCupon") in CUPONES_PRUEBA:
            continue

        items = json.loads(m["items"])
        total = s["amount_total"] / 100
        cuando = dt.datetime.fromtimestamp(s["created"], TZ)
        importes = _repartir(items, total, cuando.strftime("%Y-%m-%d"))
        for i, importe in zip(items, importes):
            pu = round(importe / i["cantidad"], 2)
            tx[f].append({
                "fecha_hora": cuando.strftime("%Y-%m-%d %H:%M"),
                "canal": "Boletera propia",
                "tipo": i["tipo"],
                "categoria": _categoria(i["tipo"], pu, cuando.strftime("%Y-%m-%d")),
                "pu": pu,
                "seccion": i["seccion"],
                "boletos": i["cantidad"],
                "importe": importe,
                "comprador": (m.get("nombre") or s.get("customer_details", {}).get("name") or "").strip(),
                "referencia": s["id"],
            })
    for f in tx:
        tx[f].sort(key=lambda r: r["fecha_hora"])
    return tx


def ventas_externas(funcion):
    """Venta en taquilla y por plataformas promotoras. Captura manual.

    Cada canal trae una lista de partidas con su precio unitario real: en una misma
    función un canal puede haber vendido a varias tarifas (Ticketmaster el 25 jul
    vendió a $400, $350 y $1).
    """
    if not CANALES_JSON.exists():
        return []
    cfg = json.loads(CANALES_JSON.read_text(encoding="utf-8"))
    filas = []
    for canal, partidas in cfg.get("por_funcion", {}).get(funcion, {}).items():
        if canal.startswith("_") or not isinstance(partidas, list):
            continue
        for p in partidas:
            n, pu = int(p["cantidad"]), float(p["pu"])
            if n <= 0:
                continue
            sufijo = "" if canal == "Venta en taquilla" else f" ({canal})"
            filas.append({
                "fecha_hora": "", "canal": canal, "tipo": "general",
                "categoria": f"{p.get('categoria', 'General')}{sufijo}", "pu": pu,
                "seccion": "platea", "boletos": n, "importe": round(pu * n, 2),
                "comprador": "(corte de canal)", "referencia": f"corte {canal}",
            })
    return filas


REAGENDAS_JSON = SALIDA / "reagendas.json"


def reagendas(funcion):
    """Boletos que cambiaron de función.

    Regla del sistema (campo `fechaContable` del log de auditoría): la persona asiste
    a la función destino, pero el importe queda contabilizado en la función de origen.
    Devuelve (salen, llegan) para poder reportar asistencia e ingreso por separado.
    """
    if not REAGENDAS_JSON.exists():
        return [], []
    rs = json.loads(REAGENDAS_JSON.read_text(encoding="utf-8")).get("reagendas", [])
    return ([r for r in rs if r["de"] == funcion],
            [r for r in rs if r["a"] == funcion])


def cortesias(funcion):
    """(otorgadas, asistieron). No toda cortesía se presenta — el teatro cuenta
    cuerpos en sala, así que el reporte distingue las dos cifras."""
    if not CORTESIAS_JSON.exists():
        return 0, 0
    d = json.loads(CORTESIAS_JSON.read_text(encoding="utf-8")).get("por_funcion", {}).get(funcion, {})
    otorgadas = d.get("cortesias", 0)
    return otorgadas, d.get("asistieron", otorgadas)


# ------------------------------------------------------------------- reportes

def armar(funcion, filas_boletera):
    filas = list(filas_boletera) + ventas_externas(funcion)
    # Criterio de atribución: la función se liquida por las personas que estuvieron en
    # sala esa noche, así que el importe de un boleto reprogramado viaja con su titular.
    salen_, llegan_ = reagendas(funcion)
    for r in llegan_:
        if r["total"] > 0:
            filas.append({
                "fecha_hora": "", "canal": "Boletera propia", "tipo": "general",
                "categoria": f"General, reprogramado del {_fecha_corta(r['de'])}",
                "pu": round(r["total"] / r["boletos"], 2), "seccion": "platea",
                "boletos": r["boletos"], "importe": float(r["total"]),
                "comprador": "(boleto reprogramado)", "referencia": r["codigo"],
            })
    for r in salen_:
        if r["total"] > 0:
            filas.append({
                "fecha_hora": "", "canal": "Boletera propia", "tipo": "general",
                "categoria": f"General, reprogramado al {_fecha_corta(r['a'])}",
                "pu": round(r["total"] / r["boletos"], 2), "seccion": "platea",
                "boletos": -r["boletos"], "importe": -float(r["total"]),
                "comprador": "(boleto reprogramado)", "referencia": r["codigo"],
            })
    tot_b = sum(r["boletos"] for r in filas)
    tot_i = sum(r["importe"] for r in filas)
    por_cat, por_canal = defaultdict(lambda: [0, 0.0, 0.0]), defaultdict(lambda: [0, 0.0])
    for r in filas:
        c = por_cat[(r["categoria"], r["pu"])]
        c[0] += r["boletos"]
        c[1] += r["importe"]
        c[2] = r["pu"]
        por_canal[r["canal"]][0] += r["boletos"]
        por_canal[r["canal"]][1] += r["importe"]
    cort_otorg, cort_asist = cortesias(funcion)
    salen, llegan = reagendas(funcion)
    # Los reprogramados ya vienen sumados/restados en `filas`.
    pag = tot_b
    # Las cortesías reprogramadas ya vienen contadas en el manifiesto de cada función.
    cort_presentes = cort_asist
    asistencia = pag + cort_presentes
    a = {
        "reagendas_salen": salen, "reagendas_llegan": llegan,
        "asistencia_pagada": pag, "cortesias_otorgadas": cort_otorg,
        "funcion": funcion, "filas": filas, "boletos": tot_b, "taquilla": tot_i,
        "por_categoria": {f"{k[0]}|{k[1]}": v for k, v in por_cat.items()},
        "_cat": por_cat, "por_canal": dict(por_canal),
        "cortesias": cort_presentes, "aforo": AFORO,
        "asistencia": asistencia, "ocupacion": round(asistencia / AFORO * 100, 1),
        "especial": RENTA_ESPECIAL.get(funcion),
        "renta": (sum(RENTA_ESPECIAL[funcion][:2]) if funcion in RENTA_ESPECIAL
                  else None if funcion in SIN_RENTA
                  else max(RENTA_PISO, tot_i * RENTA_PCT)),
        "veinte_pct": tot_i * RENTA_PCT,
        "tecnicos": (RENTA_ESPECIAL[funcion][1] if funcion in RENTA_ESPECIAL
                     else 0.0 if funcion in SIN_RENTA else RENTA_TECNICOS),
        "nota": NOTAS_FUNCION.get(funcion),
        "lugares": _lugares(filas, cort_presentes),
    }
    a.update(_pago_teatro(a))
    return a


def ticketmaster_teatro(a):
    """Importe Ticketmaster: entra al teatro, se descuenta del cheque."""
    total = 0.0
    for nombre, vals in (a.get("por_canal") or {}).items():
        if "ticketmaster" in str(nombre).lower():
            total += float(vals[1])
    return total


def _pago_teatro(a):
    """Cheque al teatro. Técnicos se pagan al corte — no entran aquí."""
    tm = ticketmaster_teatro(a)
    tecnicos = float(a.get("tecnicos") or 0)
    if a.get("especial"):
        renta_teatro = float(a["especial"][0])
    elif a.get("renta") is None:
        renta_teatro = 0.0
    else:
        renta_teatro = float(a["renta"]) - tecnicos
    return {
        "renta_teatro": renta_teatro,
        "ticketmaster_teatro": tm,
        "cheque": max(0.0, renta_teatro - tm),
    }


MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
W = 62


def _fecha_larga(iso):
    d = dt.date.fromisoformat(iso)
    return f"{DIAS[d.weekday()]} {d.day} de {MESES[d.month - 1]} de {d.year}"


def _fecha_corta(iso):
    d = dt.date.fromisoformat(iso)
    return f"{d.day} {MESES[d.month - 1][:3]}"


def _sec(titulo):
    return ["", "─" * W, titulo, "─" * W]


def _envolver(txt, ancho):
    """Parte un párrafo en líneas de ancho fijo."""
    linea, out = "", []
    for pal in txt.split():
        if len(linea) + len(pal) + 1 > ancho:
            out.append(linea); linea = pal
        else:
            linea = f"{linea} {pal}".strip()
    if linea:
        out.append(linea)
    return out


def texto(a, verboso=True):
    """Reporte de taquilla listo para enviar al teatro. Sin datos de checkout en línea."""
    L = []
    L.append("REPORTE DE TAQUILLA")
    L.append("")
    L.append(f"{OBRA}")
    L.append(f"{VENUE}")
    L.append(f"{DIRECCION}")
    L.append("")
    L.append(f"{'Función:':22s}{_fecha_larga(a['funcion']).capitalize()}, {HORARIO} h")
    L.append(f"{'Reporte núm.:':22s}{a.get('folio', '—')}")
    L.append(f"{'Fecha de emisión:':22s}{_fecha_larga(a.get('fecha_emision') or dt.date.today().isoformat()).capitalize()}")
    L.append(f"{'Emite:':22s}{EMISOR}")

    if a.get("nota"):
        L += _sec("NOTA SOBRE ESTA FUNCIÓN")
        for linea in a["nota"]:
            L.append(f"  {linea}")

    solo_asist = a["funcion"] in SOLO_ASISTENCIA
    if not solo_asist:
        L += _sec("I. BOLETOS PAGADOS, POR CATEGORÍA")
        L.append(f"  {'Categoría':36s}{'P. unitario':>12}{'Lugares':>9}{'Importe':>14}")
        L.append("  " + "·" * (W - 2))
        for (cat, pu), (n, imp, _) in sorted(a["_cat"].items(), key=lambda x: (-x[1][0], x[0][0])):
            L.append(f"  {_categoria_export(cat)[:36]:36s}{_money(pu):>12}{n:>9}{_money(imp):>14}")
        L.append("  " + "·" * (W - 2))
        L.append(f"  {'TOTAL BOLETOS PAGADOS':36s}{'':>12}{a['boletos']:>9}"
                 f"{_money(a['taquilla']):>14}")

        L += _sec("II. BOLETOS PAGADOS, POR CANAL")
        L.append(f"  {'Canal':36s}{'Lugares':>9}{'Importe':>16}")
        L.append("  " + "·" * (W - 2))
        orden = sorted(a["por_canal"].items(), key=lambda x: (x[0] != "Boletera propia", x[0]))
        for c, (n, imp) in orden:
            L.append(f"  {_etiqueta_canal(c):36s}{n:>9}{_money(imp):>16}")
        L.append("  " + "·" * (W - 2))
        L.append(f"  {'TOTAL':36s}{a['boletos']:>9}{_money(a['taquilla']):>16}")

    L += _sec(("I." if solo_asist else "III.") + " CORTESÍAS E INVITACIONES")
    if a["cortesias"]:
        L.append(f"  {a['cortesias']} lugares sin costo. No generan ingreso de taquilla.")
    else:
        L.append("  Ninguna.")

    if a["reagendas_salen"] or a["reagendas_llegan"]:
        L += _sec(("II." if solo_asist else "IV.") + " BOLETOS REAGENDADOS")
        for r in a["reagendas_salen"]:
            tipo = "cortesías" if r["total"] == 0 else "boletos"
            imp = f", por {_money(r['total'])}." if r["total"] else "."
            L.append(f"  {r['boletos']} {tipo} de esta función, asistieron el "
                     f"{_fecha_larga(r['a'])}{imp}")
        for r in a["reagendas_llegan"]:
            tipo = "cortesías" if r["total"] == 0 else "boletos"
            imp = f", por {_money(r['total'])}." if r["total"] else "."
            L.append(f"  {r['boletos']} {tipo} del {_fecha_larga(r['de'])}, "
                     f"asistieron a esta función{imp}")
        if verboso and not solo_asist:
            L.append("")
            L.append("  El importe se atribuye a la función en que el titular asistió.")
        num = ["III.", "IV."] if solo_asist else ["V.", "VI."]
    else:
        num = ["II.", "III."] if solo_asist else ["IV.", "V."]

    L += _sec(f"{num[0]} LUGARES")
    lug = a.get("lugares") or _lugares(a.get("filas"), a.get("cortesias"))
    L.append(f"  {'Sección':20s}{'Aforo':>10}{'Ocupados':>12}{'Disponibles':>14}")
    L.append("  " + "·" * (W - 2))
    for clave, nombre in (("platea", "Platea"), ("galeria", "Galería")):
        s = lug[clave]
        L.append(f"  {nombre:20s}{s['aforo']:>10}{s['ocupados']:>12}{s['disponibles']:>14}")
    L.append("  " + "·" * (W - 2))
    L.append(f"  {'TOTAL':20s}{a['aforo']:>10}{a['asistencia']:>12}"
             f"{a['aforo'] - a['asistencia']:>14}")
    L.append("")
    L.append(f"  {'Asistencia con boleto pagado':40s}{a['asistencia_pagada']:>22}")
    L.append(f"  {'Cortesías':40s}{a['cortesias']:>22}")
    L.append(f"  {'ASISTENCIA TOTAL':40s}{a['asistencia']:>22}")
    L.append(f"  {'Ocupación':40s}{str(a['ocupacion']) + ' %':>22}")
    if not solo_asist:
        L.append("")
        L.append(f"  {'INGRESO BRUTO DE TAQUILLA':40s}{_money(a['taquilla']):>22}")

    L += _sec(f"{num[1]} LIQUIDACIÓN")
    tm = float(a.get("ticketmaster_teatro") or 0)
    renta_t = float(a.get("renta_teatro") or 0)
    cheque = float(a.get("cheque") or 0)
    if a["especial"]:
        teatro, _tecnicos, motivo = a["especial"]
        L.append(f"  {'Renta del recinto (50 %)':40s}{_money(teatro):>22}")
        if verboso:
            L.append("")
            for linea in _envolver(motivo, W - 4):
                L.append(f"  {linea}")
        L.append("  Personal técnico: pagado al corte. No forma parte de este importe.")
    elif a["renta"] is None:
        L.append("  Sin renta aplicable.")
    else:
        L.append(f"  {'20 % sobre ingreso bruto':40s}{_money(a['veinte_pct']):>22}")
        L.append(f"  {'Garantía mínima por función':40s}{_money(RENTA_PISO):>22}")
        L.append("  " + "·" * (W - 2))
        cual = "la garantía mínima" if a["renta"] == RENTA_PISO else "el 20 % de taquilla"
        L.append(f"  {'Base de liquidación':40s}{_money(a['renta']):>22}")
        if verboso:
            L.append(f"  Aplica {cual}.")
        L.append(f"  {'Renta del recinto':40s}{_money(renta_t):>22}")
        L.append("  Personal técnico: pagado al corte. No forma parte de este importe.")
    if a["renta"] is not None:
        if tm:
            L.append(f"  {'Ticketmaster (ya percibido por el teatro)':40s}{_money(-tm):>22}")
        L.append("  " + "·" * (W - 2))
        L.append(f"  {'IMPORTE A CUBRIR':40s}{_money(cheque):>22}")

    L.append("")
    L.append("─" * W)
    if verboso:
        L.append("El presente se emite con base en los registros de taquilla de la producción")
        L.append("y las remisiones de las promotoras autorizadas.")
        L.append("")
    L.append("")
    L.append(f"{EMISOR_FIRMA}")
    L.append(f"{EMISOR}")
    return "\n".join(L)


def texto_detalle(a):
    """Anexo de movimientos. Fechas y lugares; sin referencias de pago en línea."""
    L = [
        f"ANEXO — MOVIMIENTOS DE TAQUILLA · {_fecha_larga(a['funcion'])}",
        "─" * 78,
        f"  {'Fecha':12s} {'Canal':22s} {'Categoría':28s} {'Lug.':>5} {'Importe':>11}",
        "  " + "·" * 76,
    ]
    for r in a["filas"]:
        L.append(
            f"  {_fecha_anexo(r.get('fecha_hora')):12s} "
            f"{_etiqueta_canal(r['canal']):22s} "
            f"{_categoria_export(r['categoria'])[:28]:28s} "
            f"{r['boletos']:>5} {_money(r['importe']):>11}"
        )
    L.append("  " + "·" * 76)
    L.append(f"  {'TOTAL':12s} {'':22s} {'':28s} {a['boletos']:>5} {_money(a['taquilla']):>11}")
    return "\n".join(L)


def guardar(a, verboso=True):
    d = SALIDA / a["funcion"]
    d.mkdir(parents=True, exist_ok=True)
    (d / "audit.txt").write_text(texto(a, verboso) + "\n\n" + texto_detalle(a) + "\n",
                                encoding="utf-8")
    with open(d / "transacciones.csv", "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=["fecha_hora", "canal", "categoria", "tipo", "pu",
                                           "seccion", "boletos", "importe", "comprador",
                                           "referencia"])
        w.writeheader()
        w.writerows(a["filas"])
    (d / "resumen.json").write_text(json.dumps({
        k: v for k, v in a.items() if k not in ("filas", "_cat")
    }, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return d


# ----------------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--funcion", help="YYYY-MM-DD de una función específica")
    ap.add_argument("--desde")
    ap.add_argument("--hasta")
    ap.add_argument("--email", action="store_true", help="imprime solo el cuerpo del correo")
    ap.add_argument("--incluir-excluidas", action="store_true",
                    help="incluye funciones marcadas como fuera del esquema de liquidación")
    args = ap.parse_args()

    prod = ROOT / "03_Producciones" / (ROOT / "config" / "produccion-activa.txt").read_text().strip() / "produccion.yaml"
    todas = []
    if prod.exists():
        for l in prod.read_text(encoding="utf-8").splitlines():
            l = l.strip()
            if l.startswith('- "2026-') or l.startswith("- '2026-"):
                todas.append(l[3:13])

    if args.funcion:
        objetivo = [args.funcion]
    elif args.desde or args.hasta:
        d, h = args.desde or "0000-00-00", args.hasta or "9999-99-99"
        objetivo = [f for f in todas if d <= f <= h]
    else:
        hoy = dt.date.today().isoformat()
        pasadas = [f for f in todas if f < hoy]
        objetivo = pasadas[-1:] if pasadas else []

    if not args.incluir_excluidas:
        objetivo = [f for f in objetivo if f not in FUNCIONES_EXCLUIDAS]
    if not objetivo:
        print("Sin funciones que auditar.")
        return

    tx = ventas_boletera(set(objetivo))
    bloques = []
    for f in objetivo:
        a = armar(f, tx.get(f, []))
        liquidables = [x for x in todas if x not in FUNCIONES_EXCLUIDAS]
        a["folio"] = (f"{FOLIO_PREFIJO}-{liquidables.index(f) + 1:03d}"
                      if f in liquidables else f"{FOLIO_PREFIJO}-S/N")
        verboso = not bloques          # solo el primero lleva las glosas
        d = guardar(a, verboso)
        bloques.append((a, verboso))
        if not args.email:
            print(texto(a, verboso))
            print()
            print(texto_detalle(a))
            print(f"\n[guardado en {d}]\n")

    if args.email:
        for a, verboso in bloques:
            print(texto(a, verboso))
            print()

    if len(bloques) > 1 and not args.email:
        tb = sum(a["boletos"] for a, _ in bloques)
        tt = sum(a["taquilla"] for a, _ in bloques)
        tr = sum(a["renta"] or 0 for a, _ in bloques)
        print("=" * 58)
        print(f"TOTAL {len(bloques)} funciones: {tb} boletos · taquilla {_money(tt)} · renta {_money(tr)}")


if __name__ == "__main__":
    main()
