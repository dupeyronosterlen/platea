#!/usr/bin/env python3
"""
Agente 09 — Investigador de Mercado / Estratega
Platea · El Gorila S2 · jul–sep 2026

Rol dual:
  1. --estrategia   → Analiza S1 + datos S2 acumulados → recomienda mix presupuesto
  2. --venue CIUDAD → Investiga venues y demanda en ciudad para gira potencial
  3. --registrar    → Acumula nuevo punto de datos S2 (semana, CPA, conversiones)
  4. --tendencias   → Muestra evolución del CPA y conversiones durante S2
  5. (default)      → Estado rápido + pendientes estratégicos

DATOS S2: se acumulan en datos_s2.json (mismo directorio).
Cuando hay ≥5 semanas de datos reales, las recomendaciones se basan en S2,
usando S1 solo como referencia histórica.

Uso:
  python agent.py                          → resumen de estado
  python agent.py --estrategia             → análisis completo
  python agent.py --venue "Monterrey"      → estudio de mercado ciudad
  python agent.py --registrar              → agregar datos de la semana
  python agent.py --tendencias             → evolución CPA/conversiones S2
  python agent.py --json                   → output JSON para CEO (Agente 00)
"""

import os
import sys
import json
import datetime
from pathlib import Path
from dotenv import load_dotenv

ENV_PATH = Path(__file__).parent.parent / "03_Media-Buyer" / ".env"
load_dotenv(ENV_PATH)

GCP_PROJECT  = os.getenv("GCP_PROJECT", "agencia-mkt-ia")
GCP_LOCATION = os.getenv("GCP_LOCATION", "us-central1")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-pro")

# Archivo de acumulación S2
DATOS_S2_FILE = Path(__file__).parent / "datos_s2.json"

# ─── DATOS S1 (fuente estática histórica — 178 compradores reales) ────────────
S1_DATA = {
    "temporada": "S1 — El Gorila",
    "total_compradores": 178,
    "cpa_real_mxn": 260,
    "presupuesto_total_s1": 46280,
    "canal_principal": "Meta Ads (FB/IG)",
    "segmentos_ganadores": [
        "Mujeres 35-54 CDMX · intereses teatro + cultura",
        "Lookalike 1% de compradores S1",
        "Retargeting visitantes landing (abandono checkout)",
    ],
    "creativos_ganadores": [
        "Reels verticales con frase de Kafka (alta retención 3s)",
        "Carrusel 'El gorila lleva 37 años sin salir' (social proof + curiosidad)",
        "Story corto con precio y fecha directos (conversión directa)",
    ],
    "notas": "Datos de sesión anterior. CPA $260 real, objetivo S2 es $240.",
}

RECOMENDACION_S2_BASE = {
    "mix_recomendado": {
        "meta_pct": 55,
        "google_pct": 20,
        "otros_pct": 25,
        "razon": "Meta probado en S1 con CPA $260. Google no fue activo en S1 — activar cuando Meta CPA ≤ $350.",
    },
    "budget_warmup": {
        "meta_diario_mxn": 200,
        "google_diario_mxn": 0,
        "total_mxn": 200,
        "duracion_dias": 14,
        "fase": "Warm-up · Semana -4 y -3 (22 jun – 5 jul) — solo awareness/remarketing",
    },
    "budget_conversion": {
        "meta_diario_mxn": 350,
        "google_diario_mxn": 0,
        "total_mxn": 350,
        "fase": "Conversión · Semana -2 (6–12 jul) — activar cuando awareness ok",
    },
    "budget_venta_activa": {
        "meta_diario_mxn": 412,
        "google_diario_mxn": 150,
        "total_mxn": 562,
        "razon": "Activar Google cuando CPA Meta ≤ $350 y ROAS ≥ 1.5",
    },
    "techo_sin_aprobacion_mxn": 1500,
    "cpa_objetivo_mxn": 240,
    "cpa_limite_duro_mxn": 350,
    "circuito_breaker_mxn": 500,
    "segmentos_prioridad": [
        "CA de compradores S1 + Lookalike 1% · Meta · [ARRANCAR DÍA 1]",
        "Retargeting visitantes landing 30 días · Meta · [ARRANCAR DÍA 1]",
        "Brand keywords 'El Gorila teatro' · Google Search · [ACTIVAR cuando Meta ok]",
        "Broad match 'monólogo CDMX' + 'teatro kafka' · Google Search · [ACTIVAR sem -1]",
    ],
}


# ─── MANEJO DE DATOS S2 ───────────────────────────────────────────────────────

def load_datos_s2() -> dict:
    """Carga el archivo de acumulación S2. Si no existe, crea estructura vacía."""
    if DATOS_S2_FILE.exists():
        with open(DATOS_S2_FILE) as f:
            return json.load(f)
    return {
        "_descripcion": "Datos acumulados durante S2. Cada semana se agrega un punto.",
        "_actualizado": None,
        "semanas": [],
    }


def save_datos_s2(data: dict):
    data["_actualizado"] = datetime.datetime.now().isoformat()
    with open(DATOS_S2_FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def calcular_metricas_s2(semanas: list) -> dict:
    """Calcula métricas agregadas de los datos S2 acumulados."""
    if not semanas:
        return {}
    cpas   = [s["cpa_mxn"] for s in semanas if s.get("cpa_mxn")]
    convs  = [s["conversiones"] for s in semanas if s.get("conversiones")]
    gastos = [s.get("gasto_total_mxn", 0) for s in semanas]
    return {
        "semanas_con_datos": len(semanas),
        "cpa_promedio": round(sum(cpas) / len(cpas), 1) if cpas else None,
        "cpa_ultima_semana": cpas[-1] if cpas else None,
        "cpa_tendencia": "bajando" if len(cpas) >= 2 and cpas[-1] < cpas[-2]
                         else ("subiendo" if len(cpas) >= 2 and cpas[-1] > cpas[-2]
                               else "estable"),
        "conversiones_total": sum(convs),
        "gasto_total_mxn": sum(gastos),
        "suficiente_para_optimizar": sum(convs) >= 10,  # umbral de aprendizaje
    }


# ─── MODO --registrar ─────────────────────────────────────────────────────────

def run_registrar() -> str:
    """Agrega un nuevo punto de datos S2 de forma interactiva."""
    hoy = str(datetime.date.today())
    data = load_datos_s2()
    semana_num = len(data["semanas"]) + 1

    print(f"\n📊 REGISTRAR DATOS S2 — Semana {semana_num}")
    print("─────────────────────────────────────────────")
    print("(Enter para omitir un campo)\n")

    def ask(prompt, tipo=float):
        val = input(prompt).strip()
        if not val:
            return None
        try:
            return tipo(val)
        except ValueError:
            return None

    fecha_inicio = input(f"Fecha inicio de semana (YYYY-MM-DD) [{hoy}]: ").strip() or hoy
    gasto_meta   = ask("Gasto Meta esta semana (MXN): ")
    gasto_google = ask("Gasto Google esta semana (MXN): ")
    conversiones = ask("Conversiones (boletos vendidos vía ads): ", int)
    cpa          = ask("CPA real (MXN) — o dejar vacío para calcular: ")
    clics        = ask("Clics totales: ", int)
    impresiones  = ask("Impresiones totales: ", int)
    notas        = input("Notas / contexto (opcional): ").strip() or None

    gasto_total = (gasto_meta or 0) + (gasto_google or 0)
    if not cpa and gasto_total and conversiones:
        cpa = round(gasto_total / conversiones, 1)
        print(f"→ CPA calculado: ${cpa} MXN")

    punto = {
        "semana": semana_num,
        "fecha_inicio": fecha_inicio,
        "registrado_en": datetime.datetime.now().isoformat(),
        "gasto_meta_mxn": gasto_meta,
        "gasto_google_mxn": gasto_google,
        "gasto_total_mxn": gasto_total,
        "conversiones": conversiones,
        "cpa_mxn": cpa,
        "clics": clics,
        "impresiones": impresiones,
        "ctr": round(clics / impresiones * 100, 2) if clics and impresiones else None,
        "notas": notas,
    }

    data["semanas"].append(punto)
    save_datos_s2(data)

    metricas = calcular_metricas_s2(data["semanas"])
    result = f"\n✅ Semana {semana_num} registrada.\n"
    result += f"  CPA esta semana: ${cpa or '?'} MXN\n"
    result += f"  CPA promedio S2: ${metricas.get('cpa_promedio', '?')} MXN\n"
    result += f"  Conversiones S2: {metricas.get('conversiones_total', 0)} total\n"
    if metricas.get("suficiente_para_optimizar"):
        result += "  ✅ Ya hay ≥10 conversiones — suficiente para optimizar audiencias.\n"
    else:
        convs_total = metricas.get("conversiones_total", 0)
        result += f"  ⏳ Aún en aprendizaje ({convs_total}/10 conversiones para optimizar).\n"
    return result


# ─── MODO --tendencias ────────────────────────────────────────────────────────

def run_tendencias() -> str:
    hoy = datetime.date.today()
    data = load_datos_s2()
    semanas = data.get("semanas", [])

    if not semanas:
        return "\nAún no hay datos S2 registrados. Usa: python agent.py --registrar\n"

    metricas = calcular_metricas_s2(semanas)
    lines = [
        f"\n╔══════════════════════════════════════════════════════════════════╗",
        f"║  AGENTE 09 — TENDENCIAS S2 · {hoy}                             ║",
        f"╚══════════════════════════════════════════════════════════════════╝",
        f"",
        f"  Semanas con datos: {metricas['semanas_con_datos']}",
        f"  Conversiones S2:   {metricas.get('conversiones_total', 0)}",
        f"  Gasto total S2:    ${metricas.get('gasto_total_mxn', 0):,.0f} MXN",
        f"  CPA promedio S2:   ${metricas.get('cpa_promedio', '—')} MXN",
        f"  CPA última semana: ${metricas.get('cpa_ultima_semana', '—')} MXN",
        f"  Tendencia CPA:     {metricas.get('cpa_tendencia', '—')}",
        f"",
        f"EVOLUCIÓN SEMANAL",
        f"─────────────────────────────────────────────",
    ]

    for s in semanas:
        cpa_s = s.get('cpa_mxn')
        cpa_txt = f"${cpa_s}" if cpa_s else "—"
        semaforo = "🟢" if cpa_s and cpa_s <= 240 else ("🟡" if cpa_s and cpa_s <= 350 else "🔴")
        conv = s.get('conversiones', '—')
        gasto = s.get('gasto_total_mxn', 0)
        lines.append(f"  Sem {s['semana']} ({s['fecha_inicio']}) | CPA {cpa_txt} {semaforo} | Conv: {conv} | Gasto: ${gasto:,.0f}")
        if s.get("notas"):
            lines.append(f"    ↳ {s['notas']}")

    # Recomendación basada en datos reales
    cpa_ult = metricas.get("cpa_ultima_semana")
    if cpa_ult:
        lines.append("")
        lines.append("ESTADO ACTUAL")
        lines.append("─────────────────────────────────────────────")
        if cpa_ult <= 240:
            lines.append(f"  🟢 CPA óptimo (${cpa_ult} ≤ $240) — considerar escalar budget")
        elif cpa_ult <= 350:
            lines.append(f"  🟡 CPA aceptable (${cpa_ult} ≤ $350) — mantener budget, optimizar creativos")
        else:
            lines.append(f"  🔴 CPA alto (${cpa_ult} > $350) — revisar segmentos antes de escalar")

    lines.append(f"\nÚltima actualización: {data.get('_actualizado', 'nunca')}")
    return "\n".join(lines)


# ─── MODO --estrategia ────────────────────────────────────────────────────────

def run_estrategia() -> str:
    hoy = datetime.date.today()
    estreno = datetime.date(2026, 7, 18)
    dias_estreno = (estreno - hoy).days

    data    = load_datos_s2()
    semanas = data.get("semanas", [])
    metricas = calcular_metricas_s2(semanas)
    tiene_datos_s2 = len(semanas) >= 2

    rec = RECOMENDACION_S2_BASE
    mix = rec["mix_recomendado"]

    # Fuente de datos para CPA
    if tiene_datos_s2 and metricas.get("cpa_promedio"):
        cpa_referencia = metricas["cpa_promedio"]
        fuente_cpa = f"S2 real ({metricas['semanas_con_datos']} semanas · {metricas['conversiones_total']} conv)"
        alerta_aprendizaje = "" if metricas.get("suficiente_para_optimizar") else (
            "⚠️  Aún en fase de aprendizaje (<10 conversiones). No escalar presupuesto todavía.\n"
        )
    else:
        cpa_referencia = S1_DATA["cpa_real_mxn"]
        fuente_cpa = f"S1 histórico (178 compradores · referencia, aún sin datos S2 suficientes)"
        alerta_aprendizaje = "⚠️  Sin datos S2 aún. Recomendaciones basadas en S1. Actualizar con --registrar cada semana.\n"

    segs    = "\n".join(f"  {i+1}. {s}" for i, s in enumerate(rec["segmentos_prioridad"]))
    ganadores = "\n".join(f"  • {c}" for c in S1_DATA["creativos_ganadores"])

    # Determinar fase actual
    if dias_estreno > 21:
        fase_txt = "Semana -4 / -3 → AWARENESS ($200/día Meta, sin conversión)"
        budget_actual = rec["budget_warmup"]
    elif dias_estreno > 7:
        fase_txt = "Semana -2 → CONVERSIÓN ($350/día Meta, evaluar Google)"
        budget_actual = rec["budget_conversion"]
    else:
        fase_txt = "Semana -1 → URGENCIA (máximo budget, creativos directos)"
        budget_actual = rec["budget_venta_activa"]

    return f"""
╔══════════════════════════════════════════════════════════════════╗
║  AGENTE 09 — ESTRATEGIA S2 ({hoy} · {dias_estreno}d al estreno)
╚══════════════════════════════════════════════════════════════════╝

{alerta_aprendizaje}DATOS DE REFERENCIA
────────────────────────────────────────────────
CPA referencia:   ${cpa_referencia} MXN ({fuente_cpa})
CPA objetivo S2:  ${rec['cpa_objetivo_mxn']} MXN
CPA límite duro:  ${rec['cpa_limite_duro_mxn']} MXN
Circuit breaker:  ${rec['circuito_breaker_mxn']} MXN → pausa automática
{'Semanas S2 acumuladas: ' + str(metricas.get('semanas_con_datos', 0)) if semanas else 'S2 sin datos aún — ejecuta --registrar cada semana'}

FASE ACTUAL: {fase_txt}
────────────────────────────────────────────────
Meta:   ${budget_actual.get('meta_diario_mxn', 0)}/día
Google: ${budget_actual.get('google_diario_mxn', 0)}/día
Total:  ${budget_actual.get('total_mxn', 0)}/día
Techo sin aprobación Dirección: ${rec['techo_sin_aprobacion_mxn']}/día

MIX DE PRESUPUESTO OBJETIVO (cuando ambos canales activos)
────────────────────────────────────────────────
Meta Ads:   {mix['meta_pct']}% — canal principal probado
Google Ads: {mix['google_pct']}% — activar cuando CPA Meta ≤ $350 + ≥10 conversiones
Otros:      {mix['otros_pct']}% (orgánico, PR, WhatsApp)

SEGMENTOS EN ORDEN DE PRIORIDAD
────────────────────────────────────────────────
{segs}

CREATIVOS BASE (S1 ganadores — adaptar a narrativa S2 "37 años")
────────────────────────────────────────────────
{ganadores}

SIGUIENTES PASOS
────────────────────────────────────────────────
1. {'✅' if tiene_datos_s2 else '⏳'} Registrar datos semanales → python agent.py --registrar
2. {'✅' if metricas.get('suficiente_para_optimizar') else '⏳'} ≥10 conversiones para optimizar audiencias
3. ⏳ Ver tendencias → python agent.py --tendencias
4. ⏳ Activar Google Ads cuando CPA Meta ≤ $350 con ≥10 conversiones

Generado: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')} | Agente 09 Investigador
"""


# ─── MODO --venue ─────────────────────────────────────────────────────────────

def run_venue_study(ciudad: str) -> str:
    hoy = datetime.date.today()
    return f"""
╔══════════════════════════════════════════════════════════════════╗
║  AGENTE 09 — ESTUDIO DE VENUE: {ciudad.upper():<34}║
║  El Gorila · {hoy}                                              ║
╚══════════════════════════════════════════════════════════════════╝

PROCESO EN CURSO — ciudad: {ciudad}

FASE 1 — DEMANDA (2-4h)
─────────────────────────────────
□ Google Trends: "teatro {ciudad}", "monólogo", "kafka" — 12 meses
□ Meta Audience Insights: tamaño audiencia en {ciudad} (teatro + cultura)
□ Cartelera local: obras activas, precios, venues
□ Historial El Gorila en {ciudad} (si aplica)

FASE 2 — VENUES (2-4h)
─────────────────────────────────
□ Teatros/espacios aforo 100-400 personas
□ Disponibilidad aproximada (post oct 2026)
□ Precio de renta estimado
□ Contacto del programador

FASE 3 — VIABILIDAD FINANCIERA
─────────────────────────────────
  Caché base gira:  $50,000 MXN (sin viáticos)
  Viáticos est:     +$8,000-15,000 MXN
  Traslado escen:   +$3,000-8,000 MXN
  Break-even:       {int(50000 / 350)} boletos a $350 (arranque) / {int(50000 / 400)} a $400 (post-estreno)

→ Este agente requiere web search + Meta Audience Insights para completar.
  Conectar herramientas y correr en modo interactivo con Dirección.

Estado: PENDIENTE DATOS — iniciar investigación manual
"""


# ─── MODO default ─────────────────────────────────────────────────────────────

def run_status() -> str:
    hoy = datetime.date.today()
    estreno = datetime.date(2026, 7, 18)
    dias = (estreno - hoy).days
    data = load_datos_s2()
    semanas = data.get("semanas", [])
    metricas = calcular_metricas_s2(semanas)

    estado_datos = (
        f"✅ {len(semanas)} semanas acumuladas · CPA S2 promedio ${metricas.get('cpa_promedio','?')} MXN"
        if semanas else
        "⏳ Sin datos S2 aún — ejecutar --registrar al final de cada semana de pauta"
    )

    return f"""
╔══════════════════════════════════════════════════════════════════╗
║  AGENTE 09 — INVESTIGADOR DE MERCADO                           ║
╚══════════════════════════════════════════════════════════════════╝

ESTADO — {hoy} · {dias} días para el estreno
  Datos S2: {estado_datos}
  Referencia S1: {S1_DATA['total_compradores']} compradores · CPA ${S1_DATA['cpa_real_mxn']} MXN

COMANDOS
  python agent.py --estrategia        → análisis completo con datos disponibles
  python agent.py --registrar         → agregar datos de esta semana
  python agent.py --tendencias        → evolución CPA/conversiones S2
  python agent.py --venue "Ciudad"    → estudio para gira
  python agent.py --json              → datos para Agente 00
"""


# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    args = sys.argv[1:]

    if "--estrategia" in args:
        print(run_estrategia())
        return

    if "--registrar" in args:
        print(run_registrar())
        return

    if "--tendencias" in args:
        print(run_tendencias())
        return

    if "--venue" in args:
        idx = args.index("--venue")
        ciudad = args[idx + 1] if idx + 1 < len(args) else "Ciudad no especificada"
        print(run_venue_study(ciudad))
        return

    if "--json" in args:
        data = load_datos_s2()
        metricas = calcular_metricas_s2(data.get("semanas", []))
        print(json.dumps({
            "agente": "09_Investigador",
            "s1_data": S1_DATA,
            "s2_datos_acumulados": data,
            "s2_metricas": metricas,
            "recomendacion_base": RECOMENDACION_S2_BASE,
            "timestamp": datetime.datetime.now().isoformat(),
        }, ensure_ascii=False, indent=2))
        return

    print(run_status())


if __name__ == "__main__":
    main()
