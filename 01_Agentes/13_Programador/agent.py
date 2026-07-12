#!/usr/bin/env python3
"""
Agente 13 — Programador / Vigilante del Sistema
Platea · El Gorila S2 · jul–sep 2026

Qué hace:
  1. Verifica que el checkout y la boletera estén en pie
  2. Detecta intermitencia en tracking (analytics.js vs GTM)
  3. Propone código de fixes — nunca hace deploy solo
  4. Genera propuesta de /api/reporte para Agente 12/03

REGLA ABSOLUTA: detecta + propone, Dirección aprueba, LUEGO se deploya.

Uso:
  python agent.py                     → check de salud completo
  python agent.py --tracking          → diagnóstico detallado del tracking bug
  python agent.py --proponer-reporte  → genera código para /api/reporte (propuesta)
  python agent.py --json              → output JSON para consumo de otros agentes

Env (.env de Agente 03):
  BOLETERA_URL          → https://elgorila-api.dupeyronosterlen.workers.dev
  BOLETERA_READ_TOKEN   → token si /api/reporte ya existe
  RESEND_API_KEY        → para alertas email
  GCP_PROJECT           → agencia-mkt-ia
  GEMINI_MODEL          → gemini-2.5-pro
  GOOGLE_APPLICATION_CREDENTIALS
"""

import os
import sys
import json
import datetime
import requests
from dotenv import load_dotenv
from pathlib import Path

# Cargar .env de Agente 03 (fuente centralizada)
ENV_PATH = Path(__file__).parent.parent / "03_Media-Buyer" / ".env"
load_dotenv(ENV_PATH)

# ─── CONFIG ──────────────────────────────────────────────────────────────────
BOLETERA_URL       = os.getenv("BOLETERA_URL", "https://elgorila-api.dupeyronosterlen.workers.dev")
BOLETERA_TOKEN     = os.getenv("BOLETERA_READ_TOKEN", "")
RESEND_API_KEY     = os.getenv("RESEND_API_KEY")
ALERT_EMAIL        = os.getenv("ALERT_EMAIL", "elgorilateatro@gmail.com")
SITIO_URL          = "https://elgorilateatro.com.mx"
CHECKOUT_URL       = "https://elgorilateatro.com.mx/boletos"
GTM_ID             = "GTM-P4BDXRN9"
GA4_ID             = "G-NXF8093MDJ"

# Endpoints a monitorear
ENDPOINTS = [
    {"nombre": "Sitio principal",   "url": f"{SITIO_URL}",              "metodo": "GET", "espera": 200},
    {"nombre": "Página boletos",    "url": f"{CHECKOUT_URL}",           "metodo": "GET", "espera": 200},
    {"nombre": "Worker API",        "url": f"{BOLETERA_URL}/api/funciones", "metodo": "GET", "espera": 200},
    {"nombre": "/api/disponibilidad","url": f"{BOLETERA_URL}/api/disponibilidad?fecha=2026-07-18", "metodo": "GET", "espera": 200},
    {"nombre": "/api/reporte (auth)","url": f"https://elgorila-reporte.dupeyronosterlen.workers.dev/api/reporte",
     "metodo": "GET", "espera": 200, "token": True},
]


# ═══════════════════════════════════════════════════════════════════════════════
# 1. HEALTH CHECK — endpoints
# ═══════════════════════════════════════════════════════════════════════════════

def check_endpoint(ep: dict) -> dict:
    headers = {}
    if ep.get("token") and BOLETERA_TOKEN:
        headers["Authorization"] = f"Bearer {BOLETERA_TOKEN}"
    try:
        r = requests.get(ep["url"], headers=headers, timeout=10, allow_redirects=True)
        ok = r.status_code < 400
        return {
            "nombre": ep["nombre"],
            "url": ep["url"],
            "status": r.status_code,
            "ok": ok,
            "latencia_ms": int(r.elapsed.total_seconds() * 1000),
            "error": None,
        }
    except requests.exceptions.ConnectionError:
        return {"nombre": ep["nombre"], "url": ep["url"], "status": 0, "ok": False,
                "latencia_ms": None, "error": "ConnectionError — sin respuesta"}
    except requests.exceptions.Timeout:
        return {"nombre": ep["nombre"], "url": ep["url"], "status": 0, "ok": False,
                "latencia_ms": None, "error": "Timeout >10s"}
    except Exception as e:
        return {"nombre": ep["nombre"], "url": ep["url"], "status": 0, "ok": False,
                "latencia_ms": None, "error": str(e)}


def run_health_check() -> dict:
    resultados = [check_endpoint(ep) for ep in ENDPOINTS]
    caidos = [r for r in resultados if not r["ok"]]
    # /api/reporte sin token es esperado — no es error real
    caidos_reales = [
        r for r in caidos
        if "/api/reporte" not in r["url"] or BOLETERA_TOKEN
    ]
    return {
        "timestamp": datetime.datetime.now().isoformat(),
        "endpoints": resultados,
        "total": len(resultados),
        "ok": len([r for r in resultados if r["ok"]]),
        "caidos": len(caidos_reales),
        "nivel": "🔴" if caidos_reales else "🟢",
        "caidos_detalle": caidos_reales,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 2. DIAGNÓSTICO DE TRACKING BUG
# ═══════════════════════════════════════════════════════════════════════════════

DIAGNOSTICO_TRACKING = """
╔══════════════════════════════════════════════════════════════════╗
║  AGENTE 13 — DIAGNÓSTICO: TRACKING INTERMITENTE                ║
║  Tarea abierta 2026-06-17 · Prioridad 🔴 ALTA                  ║
╚══════════════════════════════════════════════════════════════════╝

SÍNTOMA VERIFICADO (Agente 06 · 17 jun 2026)
────────────────────────────────────────────────
Dos compras completadas el mismo día:
  CERT-ORD-A091C9EE82E5 → NO registró `purchase` en GA4
  CERT-ORD-1EEFB1EAA7BA → SÍ registró `purchase` en GA4
= INTERMITENTE, no falla total.

CAUSA RAÍZ (hipótesis fuerte · confirmada en sesión 17 jun ~21:39h)
────────────────────────────────────────────────
El sitio tiene DOS cargadores de tracking en paralelo:

  1. GTM (GTM-P4BDXRN9) → page_view + eventos custom
     ESTADO: ✅ confiable, dispara siempre.

  2. web/js/analytics.js → carga su propio gtag.js + configura GA4/GAds
     Maneja TODA la cadena de ecommerce (view_item → purchase)
     ESTADO: ❌ falla cuando gtag.js no inicializa antes de checkout.session.completed

El hook confirmacion.js llama ElGorilaAnalytics.purchase() correctamente,
pero si analytics.js aún no cargó, el objeto no existe → silent fail.

FIX PROPUESTO (para revisión de Dirección antes de deployar)
────────────────────────────────────────────────
OPCIÓN A (recomendada) — Mover purchase a GTM vía dataLayer:
  En confirmacion.js, antes del call a ElGorilaAnalytics.purchase():

    window.dataLayer = window.dataLayer || [];
    window.dataLayer.push({
      event: 'purchase_elgorila',
      transaction_id: orden.id,
      value: orden.total / 100,
      currency: 'MXN',
      items: [{ item_name: 'Boleto El Gorila', quantity: orden.cantidad }]
    });

  Luego configurar un tag GA4 Event en GTM que escuche 'purchase_elgorila'.
  GTM ya está inicializado antes que analytics.js → elimina la carrera.

OPCIÓN B (parche rápido) — Guard en analytics.js:
  Envolver el call en confirmacion.js:

    if (window.ElGorilaAnalytics) {
      ElGorilaAnalytics.purchase(...);
    } else {
      // fallback directo
      gtag('event', 'purchase', { transaction_id: orden.id, value: ... });
    }

  Riesgo: si gtag tampoco cargó, sigue fallando.

RECOMENDACIÓN
────────────────────────────────────────────────
Opción A es más robusta. GTM ya controla los demás eventos y se carga primero.
Mover purchase a GTM elimina la dependencia de race condition con analytics.js.

REPO DEL SITIO
────────────────────────────────────────────────
Local: ~/Dropbox/P. Gorila/3. Boletaje/WEB/ElGorila-Boletaje/
Archivo a editar: web/js/confirmacion.js (línea ~264)
Complemento: GTM workspace → nuevo Tag "GA4 - purchase" / Trigger custom event

SIGUIENTE PASO (Dirección aprueba → Agente 13 implementa)
────────────────────────────────────────────────
1. Dirección revisa Opción A vs B
2. Dirección aprueba: "hazlo en confirmacion.js + GTM"
3. Agente 13 genera el diff completo
4. Dirección revisa el diff
5. Deploy a producción

Estado: PROPUESTA LISTA — esperando aprobación de Dirección
"""


# ═══════════════════════════════════════════════════════════════════════════════
# 3. PROPUESTA /api/reporte
# ═══════════════════════════════════════════════════════════════════════════════

PROPUESTA_API_REPORTE = """
╔══════════════════════════════════════════════════════════════════╗
║  AGENTE 13 — PROPUESTA: /api/reporte                           ║
║  Endpoint requerido por Agentes 12 (Boletera) y 03 (Media)     ║
╚══════════════════════════════════════════════════════════════════╝

PROPÓSITO
────────────────────────────────────────────────
Endpoint GET /api/reporte en el worker elgorila-reporte.dupeyronosterlen.workers.dev
que retorna ventas reales desde KV de Stripe, con autenticación por Bearer token.

CONTRATO DE LA API
────────────────────────────────────────────────
GET /api/reporte?desde=2026-07-01&hasta=2026-07-18
Authorization: Bearer {BOLETERA_READ_TOKEN}

Response 200:
{
  "desde": "2026-07-01",
  "hasta": "2026-07-18",
  "total_ventas": 45,
  "total_ingresos_mxn": 14350,
  "promedio_boletos_por_orden": 1.8,
  "desglose_por_tipo": {
    "general": { "cantidad": 38, "ingresos": 13300 },
    "academia": { "cantidad": 7,  "ingresos": 1715 }
  },
  "ventas_por_dia": [
    { "fecha": "2026-07-01", "ventas": 3, "ingresos": 1050 },
    ...
  ],
  "ultima_venta": "2026-07-17T22:34:00Z"
}

CÓDIGO WORKER (Cloudflare Workers · TypeScript)
────────────────────────────────────────────────
// Agregar en el worker existente (elgorila-reporte/src/index.ts):

async function handleReporte(request: Request, env: Env): Promise<Response> {
  // Auth
  const token = request.headers.get('Authorization')?.replace('Bearer ', '');
  if (token !== env.BOLETERA_READ_TOKEN) {
    return new Response(JSON.stringify({ error: 'Unauthorized' }), {
      status: 401, headers: { 'Content-Type': 'application/json' }
    });
  }

  const url = new URL(request.url);
  const desde = url.searchParams.get('desde') || '2026-07-01';
  const hasta = url.searchParams.get('hasta') || new Date().toISOString().slice(0, 10);

  // Leer órdenes del KV (ya las escribe el webhook de Stripe)
  const { keys } = await env.KV.list({ prefix: 'orden:' });
  const ordenes = [];
  for (const key of keys) {
    const raw = await env.KV.get(key.name, 'json') as any;
    if (!raw) continue;
    const fecha = raw.created_at?.slice(0, 10);
    if (fecha >= desde && fecha <= hasta) ordenes.push(raw);
  }

  // Calcular resumen
  let total_ventas = 0, total_ingresos = 0;
  const por_tipo: Record<string, { cantidad: number, ingresos: number }> = {};
  const por_dia: Record<string, { ventas: number, ingresos: number }> = {};

  for (const o of ordenes) {
    const qty = o.quantity || 1;
    const amt = (o.amount_total || 0) / 100;
    const tipo = o.tipo_descuento || 'general';
    const dia = o.created_at?.slice(0, 10) || desde;

    total_ventas += qty;
    total_ingresos += amt;

    if (!por_tipo[tipo]) por_tipo[tipo] = { cantidad: 0, ingresos: 0 };
    por_tipo[tipo].cantidad += qty;
    por_tipo[tipo].ingresos += amt;

    if (!por_dia[dia]) por_dia[dia] = { ventas: 0, ingresos: 0 };
    por_dia[dia].ventas += qty;
    por_dia[dia].ingresos += amt;
  }

  return new Response(JSON.stringify({
    desde, hasta,
    total_ventas,
    total_ingresos_mxn: Math.round(total_ingresos),
    promedio_boletos_por_orden: ordenes.length ? +(total_ventas / ordenes.length).toFixed(2) : 0,
    desglose_por_tipo: por_tipo,
    ventas_por_dia: Object.entries(por_dia)
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([fecha, d]) => ({ fecha, ...d })),
    ultima_venta: ordenes.sort((a, b) =>
      (b.created_at || '').localeCompare(a.created_at || '')
    )[0]?.created_at || null,
    generado: new Date().toISOString(),
  }, null, 2), {
    status: 200,
    headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' }
  });
}

TAMBIÉN AGREGAR al env (wrangler.toml):
  [vars]
  BOLETERA_READ_TOKEN = "<valor real en .env de Ag-03/Ag-12 - nunca hardcodear aqui (redactado 11 jul)>"

SIGUIENTE PASO
────────────────────────────────────────────────
Dirección revisa el código → aprueba → Agente 13 lo inserta en el repo y hace deploy.
Una vez deployado: escribir BOLETERA_REPORTE_URL en .env y el Agente 12 ya lee datos reales.

Estado: PROPUESTA LISTA — esperando aprobación de Dirección
"""


# ═══════════════════════════════════════════════════════════════════════════════
# 4. REPORTE DE SALUD
# ═══════════════════════════════════════════════════════════════════════════════

def build_health_report(health: dict) -> str:
    hoy = datetime.datetime.now()
    nivel = health["nivel"]
    n_ok = health["ok"]
    n_total = health["total"]
    caidos = health["caidos_detalle"]

    tabla = ""
    for ep in health["endpoints"]:
        est = "✅" if ep["ok"] else "❌"
        lat = f"{ep['latencia_ms']}ms" if ep["latencia_ms"] else "—"
        err = f"  [{ep['error']}]" if ep.get("error") else ""
        tabla += f"  {est}  {ep['nombre']:<30} {lat:<8}  HTTP {ep['status']}{err}\n"

    alertas = ""
    if caidos:
        alertas = "\nALERTAS\n" + "─" * 60 + "\n"
        for c in caidos:
            alertas += f"  ❌ {c['nombre']}: {c.get('error', f'HTTP {c[\"status\"]}')}\n"
            alertas += f"     URL: {c['url']}\n"
            alertas += "     → Avisar a Dirección. No modificar producción sin aprobación.\n\n"
    else:
        alertas = "\n✅ Todos los sistemas en pie. Sin alertas.\n"

    reporte_status = (
        "✅ Disponible" if BOLETERA_TOKEN else
        "⚠️ PENDIENTE — código listo, Dirección debe aprobar deploy"
    )

    return f"""
╔══════════════════════════════════════════════════════════════════╗
║          AGENTE 13 — PROGRAMADOR / VIGILANTE DEL SISTEMA       ║
║          El Gorila S2 · {hoy.strftime('%Y-%m-%d %H:%M'):<40}║
╚══════════════════════════════════════════════════════════════════╝

ESTADO GENERAL: {nivel}  ({n_ok}/{n_total} endpoints OK)

ENDPOINTS
────────────────────────────────────────────────────────────────
{tabla}
/api/reporte (con auth): {reporte_status}

{alertas}

TAREAS ABIERTAS (propuestas — esperando aprobación de Dirección)
────────────────────────────────────────────────────────────────
  🔴 [TRACKING BUG] purchase intermitente en GA4/analytics.js
     → Ejecutar: python agent.py --tracking para ver la propuesta completa
     → Fix propuesto: mover purchase event a GTM dataLayer

  🟡 [/api/reporte] Endpoint de ventas para Agentes 12 y 03
     → Ejecutar: python agent.py --proponer-reporte para ver el código
     → Una vez aprobado: 1 deploy en Cloudflare Workers

REGLA: detecta + propone. Dirección aprueba. LUEGO se deploya.
────────────────────────────────────────────────────────────────
Generado: {hoy.strftime('%Y-%m-%d %H:%M')} | Agente 13 Programador
"""


# ═══════════════════════════════════════════════════════════════════════════════
# 5. NOTIFICACIÓN
# ═══════════════════════════════════════════════════════════════════════════════

def send_alert(subject: str, body: str) -> bool:
    if not RESEND_API_KEY:
        print("⚠️  RESEND_API_KEY no configurada — email no enviado")
        return False
    r = requests.post(
        "https://api.resend.com/emails",
        headers={"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json"},
        json={"from": "platea@elgorilateatro.com.mx", "to": [ALERT_EMAIL],
              "subject": f"🚨 {subject}", "text": body},
        timeout=15,
    )
    ok = r.ok
    print(f"{'✅' if ok else '❌'} Email {'enviado' if ok else 'fallido'}: {subject}")
    return ok


# ═══════════════════════════════════════════════════════════════════════════════
# 6. MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    args = sys.argv[1:]

    if "--tracking" in args:
        print(DIAGNOSTICO_TRACKING)
        return

    if "--proponer-reporte" in args:
        print(PROPUESTA_API_REPORTE)
        return

    as_json = "--json" in args
    silent = "--silent" in args

    if not as_json:
        print("🔧 Agente 13 — Vigilante del Sistema (El Gorila S2)")
        print("=" * 55)

    health = run_health_check()

    if as_json:
        print(json.dumps(health, ensure_ascii=False, indent=2, default=str))
        return

    report = build_health_report(health)
    print(report)

    if silent:
        return

    # Email solo si hay caídos reales
    if health["caidos"] > 0:
        caidos_nombres = [c["nombre"] for c in health["caidos_detalle"]]
        send_alert(
            f"Sistema caído — El Gorila: {', '.join(caidos_nombres)}",
            report,
        )
    else:
        print("🟢 Sin alertas — no se envía email.")


if __name__ == "__main__":
    main()
