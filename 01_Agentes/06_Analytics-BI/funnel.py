#!/usr/bin/env python3
"""
Agente 06 — Analytics/BI · Funnel Monitor v1
Platea · El Gorila S2

Qué hace (SOLO LECTURA — jamás modifica campañas ni boletera):
  1. Meta Ads API: impresiones → clicks → landing page views → inicios de checkout → compras,
     total y por campaña (últimos N días).
  2. Boletera (worker wilberto): boletos reales acumulados por función.
  3. Diagnostica en qué etapa se fuga el funnel y qué agente debe atacarla.

Uso:
  python funnel.py            → reporte legible (7 días)
  python funnel.py --days 14  → otro período
  python funnel.py --json     → output JSON para otros agentes (00 CEO, 03 Media Buyer)

Fuentes pendientes de conectar (v2):
  - GA4 (comportamiento en sitio) — requiere regenerar GOOGLE_ANALYTICS_REFRESH_TOKEN
  - Stripe read-only (método de pago, fecha exacta de venta)
"""

import os
import sys
import json
import datetime
import requests
from pathlib import Path
from dotenv import load_dotenv

# Reusa el .env del Media Buyer (misma cuenta Meta, misma boletera)
ENV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "03_Media-Buyer", ".env")
load_dotenv(ENV_PATH)


def _bitacora(action: str, result: str, outcome: str = "ok") -> None:
    try:
        ops = Path(__file__).resolve().parents[2] / "04_Operaciones"
        if str(ops) not in sys.path:
            sys.path.insert(0, str(ops))
        from platea_log import log_run
        log_run("06 Analytics", action, result, outcome=outcome, step="ag06")
    except Exception:
        pass


META_TOKEN    = os.getenv("SYSTEM_USER_ACCESS_TOKEN")
AD_ACCOUNT_ID = os.getenv("AD_ACCOUNT_ID", "act_389427487828383")
BOLETERA_URL  = os.getenv("BOLETERA_URL", "https://elgorila-api.dupeyronosterlen.workers.dev")
TEATRO_ID     = os.getenv("TEATRO_ID", "wilberto")
GRAPH         = "https://graph.facebook.com/v21.0"

# action_types de Meta que componen cada etapa del funnel
ACTION_MAP = {
    "clicks_link":   {"link_click"},
    "landing_views": {"landing_page_view"},
    "checkouts":     {"initiate_checkout", "omni_initiated_checkout",
                      "offsite_conversion.fb_pixel_initiate_checkout"},
    "compras_meta":  {"purchase", "omni_purchase",
                      "offsite_conversion.fb_pixel_purchase"},
}

# Benchmarks mínimos sanos (referencia teatro/eventos MX + datos S1 El Gorila)
BENCH = {
    "ctr_pct":           1.0,   # impresiones → clicks
    "lpv_de_clicks_pct": 70.0,  # clicks → llegan al sitio (menos = sitio lento o clicks accidentales)
    "ic_de_lpv_pct":     8.0,   # visitas → inician checkout (menos = la página no convence)
    "compra_de_ic_pct":  20.0,  # checkout → pago (menos = fricción en el pago)
}


def sum_actions(actions: list, wanted: set) -> int:
    total = 0
    for a in actions or []:
        if a.get("action_type") in wanted:
            try:
                total += int(float(a.get("value", 0)))
            except (TypeError, ValueError):
                pass
    return total


def fetch_meta_funnel(days: int) -> dict:
    """Insights por campaña, últimos N días."""
    hoy = datetime.date.today()
    desde = hoy - datetime.timedelta(days=days)
    r = requests.get(
        f"{GRAPH}/{AD_ACCOUNT_ID}/insights",
        params={
            "access_token": META_TOKEN,
            "level": "campaign",
            "fields": "campaign_name,spend,impressions,actions",
            "time_range": json.dumps({"since": str(desde), "until": str(hoy)}),
            "limit": 50,
        },
        timeout=30,
    )
    r.raise_for_status()
    rows = r.json().get("data", [])

    campanas = []
    tot = {"spend": 0.0, "impressions": 0, "clicks_link": 0,
           "landing_views": 0, "checkouts": 0, "compras_meta": 0}
    for row in rows:
        c = {
            "campana": row.get("campaign_name", "?"),
            "spend": round(float(row.get("spend", 0)), 2),
            "impressions": int(row.get("impressions", 0)),
        }
        for stage, wanted in ACTION_MAP.items():
            c[stage] = sum_actions(row.get("actions"), wanted)
        campanas.append(c)
        tot["spend"] += c["spend"]
        for k in ("impressions", "clicks_link", "landing_views", "checkouts", "compras_meta"):
            tot[k] += c[k]
    tot["spend"] = round(tot["spend"], 2)
    return {"desde": str(desde), "hasta": str(hoy), "total": tot, "campanas": campanas}


FRECUENCIA_MAX = 4.0  # regla de Dirección (11 jul): arriba de esto = hostigamiento, alertar


def fetch_frecuencia(days: int) -> list:
    """Alcance y frecuencia por adset — vigila que no hostiguemos a nadie."""
    hoy = datetime.date.today()
    desde = hoy - datetime.timedelta(days=days)
    r = requests.get(
        f"{GRAPH}/{AD_ACCOUNT_ID}/insights",
        params={
            "access_token": META_TOKEN, "level": "adset",
            "fields": "adset_name,reach,frequency",
            "time_range": json.dumps({"since": str(desde), "until": str(hoy)}),
            "limit": 50,
        }, timeout=30)
    r.raise_for_status()
    return [{"adset": row.get("adset_name", "?"),
             "personas": int(row.get("reach", 0)),
             "frecuencia": round(float(row.get("frequency", 0)), 1)}
            for row in r.json().get("data", [])]


def fetch_boletera() -> dict:
    """Boletos reales acumulados por función (solo lectura)."""
    r = requests.get(f"{BOLETERA_URL}/api/{TEATRO_ID}/funciones", timeout=10)
    r.raise_for_status()
    funciones = r.json()
    por_funcion = {}
    for fn in funciones:
        fecha = (fn.get("fecha_iso") or fn.get("fecha", ""))[:10]
        if fecha:
            por_funcion[fecha] = int(fn.get("vendidos", 0))
    return {"por_funcion": por_funcion, "total_acumulado": sum(por_funcion.values())}


def pct(parte: float, todo: float) -> float:
    return round(parte / todo * 100, 2) if todo else 0.0


def diagnose(t: dict) -> list:
    """Compara cada etapa contra benchmark y señala la fuga + quién la ataca."""
    rates = {
        "ctr_pct":           pct(t["clicks_link"], t["impressions"]),
        "lpv_de_clicks_pct": pct(t["landing_views"], t["clicks_link"]),
        "ic_de_lpv_pct":     pct(t["checkouts"], t["landing_views"]),
        "compra_de_ic_pct":  pct(t["compras_meta"], t["checkouts"]),
    }
    ataca = {
        "ctr_pct":           ("Creativos/copy no detienen el scroll", "Ag-01 Creativo + Ag-02 Copy: nuevos hooks"),
        "lpv_de_clicks_pct": ("Se pierden entre el click y el sitio", "Ag-13: velocidad de carga / revisar URL de ads"),
        "ic_de_lpv_pct":     ("Llegan al sitio pero no van a comprar", "Ag-02 + Ag-13: claridad de página, CTA, precio visible"),
        "compra_de_ic_pct":  ("Inician pago y lo abandonan", "Ag-13: fricción del checkout (PRIORIDAD conocida)"),
    }
    hallazgos = []
    for k, rate in rates.items():
        ok = rate >= BENCH[k]
        problema, quien = ataca[k]
        hallazgos.append({
            "etapa": k, "tasa_pct": rate, "benchmark_pct": BENCH[k],
            "estado": "✅" if ok else "🔴",
            "diagnostico": None if ok else problema,
            "ataque": None if ok else quien,
        })
    return hallazgos


def build_text(out: dict) -> str:
    t = out["funnel_total"]
    boletera = out["boletera"]
    lines = [
        "🔎 Agente 06 — Funnel Monitor v1 (solo lectura)",
        "=" * 55,
        f"   Período: {out['periodo']}  ·  Gasto Meta: ${t['spend']:.0f} MXN",
        "",
        f"   Impresiones      {t['impressions']:>8,}",
        f"   Clicks al sitio  {t['clicks_link']:>8,}   CTR {pct(t['clicks_link'], t['impressions'])}%",
        f"   Llegan al sitio  {t['landing_views']:>8,}   {pct(t['landing_views'], t['clicks_link'])}% de los clicks",
        f"   Inician checkout {t['checkouts']:>8,}   {pct(t['checkouts'], t['landing_views'])}% de las visitas",
        f"   Compras (Meta)   {t['compras_meta']:>8,}   {pct(t['compras_meta'], t['checkouts'])}% de los checkouts",
    ]
    if boletera.get("total_acumulado") is not None:
        lines.append(f"   Boletos reales (boletera, acumulado): {boletera['total_acumulado']}")
    lines.append("")
    for h in out["tasas"]:
        linea = f"   {h['estado']} {h['etapa']}: {h['tasa_pct']}% (mínimo sano {h['benchmark_pct']}%)"
        if h["diagnostico"]:
            linea += f" → {h['diagnostico']} · ATACA: {h['ataque']}"
        lines.append(linea)
    if out["fuga_principal"]:
        f = out["fuga_principal"]
        lines.append("")
        lines.append(f"   🎯 FUGA PRINCIPAL: {f['etapa']} — {f['diagnostico']}")
        lines.append(f"      → {f['ataque']}")
    if out.get("frecuencias"):
        lines.append("")
        lines.append(f"   👁️ FRECUENCIA (veces/persona esta semana · regla: alertar si >{FRECUENCIA_MAX:.0f}):")
        for fr in out["frecuencias"]:
            marca = "🔴 HOSTIGAMIENTO — bajar presupuesto o refrescar creativo" if fr["frecuencia"] > FRECUENCIA_MAX else "✅"
            lines.append(f"      {marca} {fr['adset'][:32]}: {fr['frecuencia']}x a {fr['personas']:,} personas")
    lines.append("")
    lines.append("   (solo lectura — este agente nunca modifica nada)")
    return "\n".join(lines)


def send_email(subject: str, body: str) -> bool:
    api_key = os.getenv("RESEND_API_KEY")
    to = os.getenv("ALERT_EMAIL", "elgorilateatro@gmail.com")
    if not api_key:
        return False
    r = requests.post(
        "https://api.resend.com/emails",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "from": "Agente 06 Platea <boletos@elgorilateatro.com.mx>",
            "to": [to],
            "subject": subject,
            "text": body,
        },
        timeout=15,
    )
    return r.ok


def main():
    as_json = "--json" in sys.argv
    do_email = "--email" in sys.argv
    days = 7
    if "--days" in sys.argv:
        try:
            days = int(sys.argv[sys.argv.index("--days") + 1])
        except (IndexError, ValueError):
            pass

    meta = fetch_meta_funnel(days)
    try:
        boletera = fetch_boletera()
    except Exception as e:
        boletera = {"status": "error", "error": str(e)}
    try:
        frecuencias = fetch_frecuencia(days)
    except Exception:
        frecuencias = []

    t = meta["total"]
    hallazgos = diagnose(t)
    fugas = [h for h in hallazgos if h["estado"] == "🔴"]
    out = {
        "timestamp": datetime.datetime.now().isoformat(timespec="seconds"),
        "periodo": f"{meta['desde']} → {meta['hasta']}",
        "funnel_total": t,
        "tasas": hallazgos,
        "fuga_principal": min(fugas, key=lambda h: h["tasa_pct"] / h["benchmark_pct"]) if fugas else None,
        "boletera": boletera,
        "campanas": meta["campanas"],
        "frecuencias": frecuencias,
        "hostigamiento": [f for f in frecuencias if f["frecuencia"] > FRECUENCIA_MAX],
    }

    if as_json:
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return

    texto = build_text(out)
    print(texto)
    if do_email:
        fuga = out["fuga_principal"]
        subject = f"[Funnel] {'🔴 ' + fuga['etapa'] if fuga else '✅ sano'} — El Gorila S2 {out['periodo']}"
        ok = send_email(subject, texto)
        print(f"\n📧 Email: {'enviado' if ok else 'FALLÓ'}")

    fuga = out.get("fuga_principal")
    _bitacora(
        "funnel diario",
        f"periodo {out['periodo']} · fuga={fuga['etapa'] if fuga else 'ninguna'} · email={'sí' if do_email else 'no'}",
        outcome="ok",  # fuga crónica ≠ crisis; JSONL sí, bitácora hackathon no
    )


if __name__ == "__main__":
    main()

