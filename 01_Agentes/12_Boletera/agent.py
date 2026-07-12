#!/usr/bin/env python3
"""
Agente 12 — Boletera Sync
Platea · El Gorila S2 · jul–sep 2026

Qué hace:
  1. Lee /api/funciones y /api/disponibilidad de la boletera propia (elgorila-api)
  2. Calcula % de ocupación por función
  3. Detecta funciones con ocupación < 50% a 5 días o menos → email urgente a Dirección
  4. Detecta boletera caída → email urgente
  5. Genera resumen de estado del inventario para consumo de otros agentes

Restricciones:
  - READ ONLY — nunca modifica nada en la boletera
  - /api/reporte PENDIENTE (Agente 13 lo debe crear); fallback a estimados
  - No actúa solo — solo detecta y alerta

Uso:
  python agent.py              → check completo + email si hay alertas
  python agent.py --silent     → solo imprime, sin email
  python agent.py --json       → output JSON para consumo de otros agentes

Env (.env):
  BOLETERA_URL       → https://elgorila-api.dupeyronosterlen.workers.dev
  BOLETERA_READ_TOKEN → token read-only /api/reporte (cuando Agente 13 lo cree)
  RESEND_API_KEY     → para envío de email
  ALERT_EMAIL        → elgorilateatro@gmail.com
"""

import os
import sys
import json
import datetime
import requests
from dotenv import load_dotenv

load_dotenv()

# ─── CONFIG ──────────────────────────────────────────────────────────────────
BOLETERA_URL         = os.getenv("BOLETERA_URL", "https://elgorila-api.dupeyronosterlen.workers.dev")
BOLETERA_REPORTE_URL = os.getenv("BOLETERA_REPORTE_URL", "https://elgorila-api.dupeyronosterlen.workers.dev")
BOLETERA_TOKEN       = os.getenv("BOLETERA_READ_TOKEN", "")
TEATRO_ID            = os.getenv("TEATRO_ID", "gorila")  # tid del worker — fix 2026-07-01
RESEND_API_KEY  = os.getenv("RESEND_API_KEY")
ALERT_EMAIL     = os.getenv("ALERT_EMAIL", "elgorilateatro@gmail.com")

# Parámetros de El Gorila S2
AFORO_TOTAL     = 325
AFORO_VENDIBLE  = 280
PRECIO_GENERAL  = 350   # MXN
ESTRENO         = datetime.date(2026, 7, 18)   # ACTUALIZADO 17 jun 2026: sábados 18:00h
HORARIO         = "18:00h"
FIN_TEMPORADA   = datetime.date(2026, 9, 26)   # último sábado de septiembre (confirmar con Dirección)

# Umbrales de alerta (de persona.md)
ALERTA_OCUPACION   = 50     # % — enviar propuesta si < este porcentaje
ALERTA_DIAS_ANTES  = 5      # días antes de la función
VIGILANCIA_DIAS    = 10     # monitorear con más atención si < 60%

# ACTUALIZADO 17 jun 2026: miércoles → sábados a las 18:00h, estreno 18 jul 2026
# Fecha de cierre pendiente confirmar con Dirección (se asume último sábado de sep)
FUNCIONES_S2 = [
    datetime.date(2026, 7, 18),   # estreno
    datetime.date(2026, 7, 25),
    datetime.date(2026, 8,  1),
    datetime.date(2026, 8,  8),
    datetime.date(2026, 8, 15),
    datetime.date(2026, 8, 22),
    datetime.date(2026, 8, 29),
    datetime.date(2026, 9,  5),
    datetime.date(2026, 9, 12),
    datetime.date(2026, 9, 19),
    datetime.date(2026, 9, 26),
]


# ═══════════════════════════════════════════════════════════════════════════════
# 1. FETCH — Boletera
# ═══════════════════════════════════════════════════════════════════════════════

def ping_boletera() -> bool:
    """Verifica que la boletera responde."""
    try:
        r = requests.get(f"{BOLETERA_URL}/api/{TEATRO_ID}/funciones", timeout=8)
        return r.ok
    except Exception:
        return False


def get_funciones() -> list[dict]:
    """Lista de funciones desde /api/{tid}/funciones."""
    r = requests.get(f"{BOLETERA_URL}/api/{TEATRO_ID}/funciones", timeout=10)
    r.raise_for_status()
    return r.json()


def get_disponibilidad(fecha_str: str) -> dict:
    """Disponibilidad de una función específica."""
    r = requests.get(
        f"{BOLETERA_URL}/api/{TEATRO_ID}/disponibilidad",
        params={"fecha": fecha_str},
        timeout=10,
    )
    r.raise_for_status()
    return r.json()


def get_reporte_ventas(desde: str, hasta: str) -> dict | None:
    """
    Reporte de ventas con datos reales (endpoint pendiente — Agente 13).
    Retorna None si aún no existe.
    """
    if not BOLETERA_TOKEN:
        return None
    try:
        r = requests.get(
            f"{BOLETERA_REPORTE_URL}/api/reporte",
            headers={"Authorization": f"Bearer {BOLETERA_TOKEN}"},
            params={"desde": desde, "hasta": hasta},
            timeout=10,
        )
        if r.ok:
            return r.json()
        return None
    except Exception:
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# 2. ANÁLISIS DE OCUPACIÓN
# ═══════════════════════════════════════════════════════════════════════════════

def build_inventory_snapshot() -> dict:
    """
    Consolida disponibilidad de todas las funciones activas.
    Fuente de verdad para alertas y reporte.
    """
    hoy = datetime.date.today()
    funciones_data = []

    # Intentar leer de la API
    try:
        raw_funciones = get_funciones()
        api_ok = True
    except Exception as e:
        api_ok = False
        raw_funciones = []
        return {
            "status": "error",
            "error": str(e),
            "boletera_caida": True,
            "funciones": [],
        }

    # Mapear fechas conocidas a datos de la API
    fn_map: dict[str, dict] = {}
    for fn in raw_funciones:
        fecha_str = (fn.get("fecha_iso") or fn.get("fecha", ""))[:10]
        if fecha_str:
            fn_map[fecha_str] = fn

    for fecha in FUNCIONES_S2:
        if fecha < hoy - datetime.timedelta(days=1):
            # Función pasada — incluir solo si hay datos
            pass

        delta = (fecha - hoy).days
        fecha_str = fecha.isoformat()
        fn_raw = fn_map.get(fecha_str, {})

        # Intentar disponibilidad
        try:
            disp = get_disponibilidad(fecha_str)
        except Exception:
            disp = fn_raw  # fallback a datos de funciones

        vendidos    = int(disp.get("vendidos", fn_raw.get("vendidos", 0)))
        total_aforo = int(disp.get("total", fn_raw.get("total", AFORO_VENDIBLE)))
        disponibles = int(disp.get("disponibles", fn_raw.get("disponibles", total_aforo - vendidos)))
        ocupacion   = round(vendidos / total_aforo * 100, 1) if total_aforo else 0
        ingresos_est = vendidos * PRECIO_GENERAL  # estimado base

        # Nivel de alerta
        if delta < 0:
            nivel = "PASADA"
        elif ocupacion >= 80:
            nivel = "🟢"
        elif ocupacion >= 60:
            nivel = "🟡"
        elif ocupacion >= 40:
            nivel = "🟠"
        else:
            nivel = "🔴"

        funciones_data.append({
            "fecha": fecha_str,
            "dias_restantes": delta,
            "vendidos": vendidos,
            "disponibles": disponibles,
            "total_aforo": total_aforo,
            "ocupacion_pct": ocupacion,
            "ingresos_estimados": ingresos_est,
            "nivel": nivel,
        })

    # Estadísticas globales
    activas = [f for f in funciones_data if f["dias_restantes"] >= 0]
    pasadas = [f for f in funciones_data if f["dias_restantes"] < 0]

    total_vendidos = sum(f["vendidos"] for f in funciones_data)
    total_ingresos = sum(f["ingresos_estimados"] for f in funciones_data)

    proxima = min(activas, key=lambda x: x["dias_restantes"]) if activas else None
    mas_debil = min(activas, key=lambda x: x["ocupacion_pct"]) if activas else None
    mas_vendida = max(funciones_data, key=lambda x: x["vendidos"]) if funciones_data else None

    return {
        "status": "ok",
        "timestamp": datetime.datetime.now().isoformat(),
        "funciones": funciones_data,
        "resumen": {
            "total_funciones": len(FUNCIONES_S2),
            "funciones_pasadas": len(pasadas),
            "funciones_activas": len(activas),
            "total_vendidos": total_vendidos,
            "total_ingresos_estimados": total_ingresos,
            "ocupacion_promedio": round(
                sum(f["ocupacion_pct"] for f in activas) / len(activas), 1
            ) if activas else 0,
        },
        "proxima_funcion": proxima,
        "funcion_mas_debil": mas_debil,
        "funcion_mas_vendida": mas_vendida,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 3. REGLAS DE ALERTA
# ═══════════════════════════════════════════════════════════════════════════════

def evaluate_alerts(snapshot: dict) -> list[dict]:
    """
    Evalúa el snapshot y genera lista de alertas con nivel y acción sugerida.
    Solo detecta — no actúa.
    """
    alertas = []

    # Boletera caída
    if snapshot.get("boletera_caida") or snapshot.get("status") == "error":
        alertas.append({
            "nivel": "🔴",
            "tipo": "BOLETERA_CAIDA",
            "mensaje": f"No se pudo conectar a la boletera: {snapshot.get('error', 'sin detalle')}",
            "fecha_funcion": None,
            "dias_restantes": None,
            "accion_sugerida": "Verificar Worker elgorila-api en Cloudflare. Avisar al Agente 13 inmediatamente.",
        })
        return alertas

    funciones = snapshot.get("funciones", [])

    for fn in funciones:
        delta = fn["dias_restantes"]
        ocp = fn["ocupacion_pct"]
        fecha = fn["fecha"]

        # Skip funciones pasadas
        if delta < 0:
            continue

        # 🔴 Función próxima (<= 5 días) con ocupación < 50%
        if delta <= ALERTA_DIAS_ANTES and ocp < ALERTA_OCUPACION:
            alertas.append({
                "nivel": "🔴",
                "tipo": "OCUPACION_CRITICA",
                "mensaje": (
                    f"Función {fecha} ({delta} días): {ocp}% de ocupación "
                    f"({fn['vendidos']}/{fn['total_aforo']} boletos)."
                ),
                "fecha_funcion": fecha,
                "dias_restantes": delta,
                "ocupacion_pct": ocp,
                "accion_sugerida": (
                    "PROPONER a Dirección activar código ESPEJO2 + subir pauta urgente (Meta/Google). "
                    "Agente 03 debe incrementar presupuesto si CPA lo permite. Dirección decide."
                ),
            })

        # 🟡 Función próxima (<= 10 días) con ocupación entre 50-60%
        elif delta <= VIGILANCIA_DIAS and 50 <= ocp < 60:
            alertas.append({
                "nivel": "🟡",
                "tipo": "OCUPACION_VIGILAR",
                "mensaje": (
                    f"Función {fecha} ({delta} días): {ocp}% de ocupación. "
                    f"Monitorear — si baja de 50% antes de la función, activar protocolo."
                ),
                "fecha_funcion": fecha,
                "dias_restantes": delta,
                "ocupacion_pct": ocp,
                "accion_sugerida": (
                    "Aumentar frecuencia de monitoreo a cada 24h. "
                    "Preparar propuesta de ESPEJO2/ACADEMIA para Dirección por si baja más."
                ),
            })

        # 🟠 Función lejana con ocupación < 40% (señal temprana)
        elif delta > VIGILANCIA_DIAS and ocp < 40:
            alertas.append({
                "nivel": "🟠",
                "tipo": "OCUPACION_BAJA_TEMPRANA",
                "mensaje": (
                    f"Función {fecha} ({delta} días): {ocp}% de ocupación. "
                    f"Aún hay tiempo pero el ritmo de ventas es bajo."
                ),
                "fecha_funcion": fecha,
                "dias_restantes": delta,
                "ocupacion_pct": ocp,
                "accion_sugerida": (
                    "Incluir en reporte semanal. Evaluar si las campañas de pauta "
                    "están dirigidas a esta fecha específica."
                ),
            })

    return alertas


# ═══════════════════════════════════════════════════════════════════════════════
# 4. REPORTE
# ═══════════════════════════════════════════════════════════════════════════════

def build_report(snapshot: dict, alertas: list[dict]) -> str:
    """Genera reporte legible del estado de la boletera."""
    hoy = datetime.date.today()
    resumen = snapshot.get("resumen", {})
    proxima = snapshot.get("proxima_funcion") or {}
    debil   = snapshot.get("funcion_mas_debil") or {}

    nivel_general = "🟢"
    if any(a["nivel"] == "🔴" for a in alertas):
        nivel_general = "🔴"
    elif any(a["nivel"] == "🟡" for a in alertas):
        nivel_general = "🟡"
    elif any(a["nivel"] == "🟠" for a in alertas):
        nivel_general = "🟠"

    alertas_txt = ""
    for a in alertas:
        if a["nivel"] in ("🔴", "🟡", "🟠"):
            alertas_txt += (
                f"\n{a['nivel']} [{a['tipo']}]\n"
                f"   {a['mensaje']}\n"
                f"   → {a['accion_sugerida']}\n"
            )
    if not alertas_txt:
        alertas_txt = "Sin alertas. Todas las funciones dentro de parámetros."

    # Tabla de funciones
    tabla = "\n   Fecha          Días  Vendidos  Ocupación  Estado\n"
    tabla += "   " + "─" * 55 + "\n"
    for fn in snapshot.get("funciones", []):
        if fn["dias_restantes"] < -7:
            continue
        marca = "◄ HOY" if fn["dias_restantes"] == 0 else ""
        tabla += (
            f"   {fn['fecha']}  {fn['dias_restantes']:>4}  "
            f"{fn['vendidos']:>6}/{fn['total_aforo']:<6}  "
            f"{fn['ocupacion_pct']:>5.1f}%     {fn['nivel']} {marca}\n"
        )

    return f"""
╔══════════════════════════════════════════════════════════════════╗
║          AGENTE 12 — BOLETERA SYNC                              ║
║          El Gorila S2 · Teatro Wilberto Cantón · Sábados 18h   ║
║          {hoy.strftime('%A %d %b %Y'):<50}║
╚══════════════════════════════════════════════════════════════════╝

ESTADO GENERAL: {nivel_general}

RESUMEN DE TEMPORADA
─────────────────────────────────
Funciones totales:  {resumen.get('total_funciones', 0)} (S2 sábados jul–sep 2026 · 18:00h)
Funciones pasadas:  {resumen.get('funciones_pasadas', 0)}
Funciones activas:  {resumen.get('funciones_activas', 0)}
Total vendidos:     {resumen.get('total_vendidos', 0)} boletos
Ingresos est.:      ${resumen.get('total_ingresos_estimados', 0):,.0f} MXN
Ocupación promedio: {resumen.get('ocupacion_promedio', 0):.1f}% (funciones activas)

PRÓXIMA FUNCIÓN
─────────────────────────────────
Fecha:      {proxima.get('fecha', 'N/D')}
Días:       {proxima.get('dias_restantes', '?')}
Vendidos:   {proxima.get('vendidos', '?')}/{proxima.get('total_aforo', '?')}
Ocupación:  {proxima.get('ocupacion_pct', '?')}%  {proxima.get('nivel', '')}

FUNCIÓN MÁS DÉBIL (activas)
─────────────────────────────────
Fecha:      {debil.get('fecha', 'N/D')}
Días:       {debil.get('dias_restantes', '?')}
Ocupación:  {debil.get('ocupacion_pct', '?')}%  {debil.get('nivel', '')}

INVENTARIO POR FUNCIÓN
────────────────────────────────────────────────────────────────
{tabla}

ALERTAS ACTIVAS
────────────────────────────────────────────────────────────────
{alertas_txt}

NOTA: Datos de /api/reporte {'disponibles (Agente 13)' if BOLETERA_TOKEN else 'PENDIENTES — usando estimados de /api/disponibilidad'}
Generado: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')} | Agente 12 Boletera
────────────────────────────────────────────────────────────────
"""


# ═══════════════════════════════════════════════════════════════════════════════
# 5. NOTIFICACIÓN — Email vía Resend
# ═══════════════════════════════════════════════════════════════════════════════

def send_alert_email(subject: str, body: str, urgente: bool = False) -> bool:
    """Envía email de alerta vía Resend."""
    if not RESEND_API_KEY:
        print(f"⚠️  RESEND_API_KEY no configurada — no se envió email")
        return False

    emoji = "🚨 " if urgente else "🎟️ "
    r = requests.post(
        "https://api.resend.com/emails",
        headers={
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "from": "platea@elgorilateatro.com.mx",
            "to": [ALERT_EMAIL],
            "subject": f"{emoji}{subject}",
            "text": body,
        },
        timeout=15,
    )
    if r.ok:
        print(f"✅ Email enviado a {ALERT_EMAIL}: {subject}")
        return True
    else:
        print(f"❌ Error enviando email: {r.status_code} {r.text[:100]}")
        return False


# ═══════════════════════════════════════════════════════════════════════════════
# 6. MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    silent  = "--silent" in sys.argv
    as_json = "--json" in sys.argv
    hoy = datetime.date.today()

    if not as_json:
        print("🎟️  Agente 12 — Boletera Sync (El Gorila S2)")
        print("=" * 50)
        print(f"   Hoy: {hoy}")

    # ── 1. Verificar que la boletera responde ─────────────────────────────────
    if not as_json:
        print("\n🔌 Verificando boletera...")
    up = ping_boletera()
    if not as_json:
        print(f"   {'✅ OK' if up else '❌ CAÍDA'} — {BOLETERA_URL}")

    # ── 2. Snapshot ───────────────────────────────────────────────────────────
    if not as_json:
        print("\n📦 Cargando inventario...")
    snapshot = build_inventory_snapshot()

    # ── 3. Alertas ────────────────────────────────────────────────────────────
    alertas = evaluate_alerts(snapshot)
    nivel_urgente = any(a["nivel"] == "🔴" for a in alertas)
    nivel_alerta  = any(a["nivel"] in ("🟡", "🟠") for a in alertas)

    if not as_json:
        print(f"   Alertas: {len(alertas)} | Urgentes: {sum(1 for a in alertas if a['nivel'] == '🔴')}")

    # ── 4. Output JSON ────────────────────────────────────────────────────────
    if as_json:
        output = {
            "timestamp": datetime.datetime.now().isoformat(),
            "snapshot": snapshot,
            "alertas": alertas,
            "nivel_general": (
                "🔴" if nivel_urgente else
                "🟡" if nivel_alerta else
                "🟢"
            ),
        }
        print(json.dumps(output, ensure_ascii=False, indent=2, default=str))
        return

    # ── 5. Reporte ────────────────────────────────────────────────────────────
    report = build_report(snapshot, alertas)
    print(report)

    # ── 6. Email ──────────────────────────────────────────────────────────────
    if silent:
        print("⚪ Modo --silent: no se envía email.")
        return

    proxima = snapshot.get("proxima_funcion") or {}
    fecha_prox = proxima.get("fecha", "?")

    if nivel_urgente:
        send_alert_email(
            f"[URGENTE] Boletera El Gorila S2 — función {fecha_prox}",
            report,
            urgente=True,
        )
    elif nivel_alerta:
        send_alert_email(
            f"[Vigilancia] Boletera El Gorila S2 — {hoy.strftime('%d %b')}",
            report,
            urgente=False,
        )
    else:
        print("🟢 Sin alertas — no se envía email.")


if __name__ == "__main__":
    main()
