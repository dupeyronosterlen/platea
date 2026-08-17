#!/usr/bin/env python3
"""
Calculadora de Deal — Agente 11 · Booking (El Gorila)
=====================================================
Calcula el PISO de negociación de una función vendida (bolo) a partir del
tarifario interno del playbook + costos variables del movimiento.

USO INTERNO. El output es para Dirección — el agente NUNCA revela precios al tercero.
La calculadora propone; Dirección fija y cierra.

Ejemplos:
  python calculadora_deal.py --escenario cdmx
  python calculadora_deal.py --escenario interior --viaticos-noches 2 --personas 4 --km 460
  python calculadora_deal.py --escenario internacional --personas 4 --viaticos-noches 3 \
      --vuelo-persona 6500 --carga-escenografia 25000
  python calculadora_deal.py --escenario interior --modo taquilla --aforo 800 --precio-boleto 350

Tarifario base (playbook Ag-11, INTERNO):
  CDMX          $25,000 (incl. 1 técnico) · rango ±$3k · piso duro $17k
  Interior      $50,000 + viáticos + traslado escenografía
  Grande/complejo  ×3 adhoc
  Internacional    sin tarifa definida → base interior ×3 + logística internacional completa
"""

import argparse

MXN = "${:,.0f} MXN".format

TARIFAS = {
    "cdmx":          {"base": 25_000, "nota": "incluye 1 técnico; rango ±$3k; piso duro $17k (escuelas/casos especiales)"},
    "interior":      {"base": 50_000, "nota": "todo menos viáticos; sumar viáticos + traslado escenografía"},
    "grande":        {"base": 75_000, "nota": "×3 adhoc — ajustar según complejidad y staff real"},
    "internacional": {"base": 75_000, "nota": "SIN tarifa oficial: base ×3 como punto de partida + logística internacional COMPLETA a cargo del comprador (o desglosada en precio). Dirección decide."},
}

# Defaults de viáticos (editar con datos reales al cotizar)
HOSPEDAJE_NOCHE_PERSONA = 1_500   # MXN
PER_DIEM_PERSONA_DIA = 600        # MXN comidas
COSTO_KM = 18                     # MXN/km camioneta+escenografía ida y vuelta (interior)


def calcular(args):
    t = TARIFAS[args.escenario]
    base = t["base"]

    lineas = [("Fee base (" + args.escenario + ")", base)]

    viaticos = 0
    if args.escenario != "cdmx":
        noches = args.viaticos_noches
        dias = noches + 1
        hospedaje = noches * args.personas * HOSPEDAJE_NOCHE_PERSONA
        per_diem = dias * args.personas * PER_DIEM_PERSONA_DIA
        viaticos = hospedaje + per_diem
        lineas.append((f"Hospedaje ({args.personas}p × {noches} noches)", hospedaje))
        lineas.append((f"Per diem ({args.personas}p × {dias} días)", per_diem))

    transporte = 0
    if args.escenario == "internacional":
        transporte = args.personas * args.vuelo_persona + args.carga_escenografia
        lineas.append((f"Vuelos ({args.personas}p × {MXN(args.vuelo_persona)})", args.personas * args.vuelo_persona))
        lineas.append(("Carga/traslado escenografía (aéreo o alt.)", args.carga_escenografia))
    elif args.escenario in ("interior", "grande") and args.km:
        transporte = args.km * 2 * COSTO_KM
        lineas.append((f"Traslado terrestre ({args.km} km × 2 × ${COSTO_KM}/km)", transporte))

    costos_movimiento = viaticos + transporte
    piso = base + costos_movimiento
    recomendado = round(piso * (1 + args.margen / 100), -3)  # redondeo a miles

    print("=" * 62)
    print("[11 · Booking] CALCULADORA DE DEAL — uso interno, solo para Dirección")
    print("=" * 62)
    for concepto, monto in lineas:
        print(f"  {concepto:<48}{MXN(monto):>12}")
    print("-" * 62)
    print(f"  {'PISO (no bajar de aquí)':<48}{MXN(piso):>12}")
    print(f"  {'PRECIO RECOMENDADO (piso + ' + str(args.margen) + '% margen)':<48}{MXN(recomendado):>12}")
    print(f"\n  Nota tarifario: {t['nota']}")

    if args.modo == "taquilla":
        if not (args.aforo and args.precio_boleto):
            print("\n  ⚠️ Modo taquilla requiere --aforo y --precio-boleto")
        else:
            print("\n  --- Escenario TAQUILLA COMPARTIDA (si el comprador no paga fee fijo) ---")
            for pct in (100, 80, 70, 60, 50):
                ingreso = args.aforo * args.precio_boleto * pct / 100
                boletos_be = -(-piso * 100 // (args.precio_boleto * pct))  # ceil
                ocup = boletos_be / args.aforo * 100
                marca = " ← inviable" if ocup > 100 else ""
                print(f"  Con {pct}% de taquilla para nosotros: break-even = "
                      f"{boletos_be:,} boletos ({ocup:.0f}% del aforo){marca}")
            print("  Regla: si el break-even pide >60% de ocupación en plaza nueva, pedir fee fijo o garantía mínima.")

    if args.escenario == "internacional":
        print("\n  ⚠️ INTERNACIONAL — checklist antes de cotizar:")
        print("     · Retención de impuestos a artistas extranjeros en destino (VERIFICAR %, cotizar NETO)")
        print("     · Permiso de trabajo remunerado (turismo ≠ trabajo)")
        print("     · Escenografía: ¿carga aérea, reconstrucción local o versión reducida?")
        print("     · INTEGRIDAD DEL ACTOR: mínimo 3 noches, día de descanso post-vuelo, acompañamiento completo")

    print("\n  Recordatorio: esta cifra NO se revela al tercero. Dirección fija y cierra.")
    print("=" * 62)


def main():
    p = argparse.ArgumentParser(description="Calculadora de deal para bolos de El Gorila (uso interno)")
    p.add_argument("--escenario", choices=list(TARIFAS), required=True)
    p.add_argument("--personas", type=int, default=4, help="viajeros: actor + técnico + producción + acompañante (default 4)")
    p.add_argument("--viaticos-noches", type=int, default=2, help="noches de hospedaje (default 2; internacional usar ≥3)")
    p.add_argument("--km", type=int, default=0, help="km de distancia (solo interior/grande, terrestre)")
    p.add_argument("--vuelo-persona", type=int, default=6_500, help="costo vuelo redondo por persona MXN (default 6,500)")
    p.add_argument("--carga-escenografia", type=int, default=25_000, help="traslado escenografía internacional MXN (default 25,000)")
    p.add_argument("--margen", type=int, default=25, help="%% de margen sobre el piso para el precio recomendado (default 25)")
    p.add_argument("--modo", choices=["fee", "taquilla"], default="fee")
    p.add_argument("--aforo", type=int, default=0)
    p.add_argument("--precio-boleto", type=int, default=0, help="precio boleto local en MXN equivalente")
    args = p.parse_args()

    if args.escenario == "internacional" and args.viaticos_noches < 3:
        args.viaticos_noches = 3  # integridad del actor: mínimo 3 noches en internacional

    calcular(args)


if __name__ == "__main__":
    main()
