#!/usr/bin/env python3
"""
Dayparting manual para El Gorila S2 — pausa/reactiva ad sets para evitar
que LOWEST_COST_WITHOUT_CAP se coma todo el presupuesto del día en la
madrugada (CPMs baratísimos 2-5am) dejando CERO delivery en la tarde/noche,
que es cuando la audiencia de teatro decide comprar.

Por qué esto y no "Ad Scheduling" nativo de Meta:
La API rechaza `adset_schedule` en ad sets con `daily_budget`
(error_subcode 1487682: "Campaigns with day parting enabled do not support
daily budgets" — requiere lifetime_budget). Cambiar a lifetime_budget es un
cambio estructural mayor (rompe el tracking de gasto diario de agent.py y
el modelo de $750/día de CLAUDE.md). Este script logra el mismo resultado
sin ese riesgo: pausa solo la ventana de madrugada donde el gasto histórico
NO genera conversiones.

Ventana ajustada 8 ago 2026 (dato real, 5 días previos al fix, desglose por
hora vía `hourly_stats_aggregated_by_advertiser_time_zone`): entre 00:00 y
05:59 hora de la cuenta (PT) se gastaron $81 en 5 días sin UNA sola compra,
AddToCart o InitiateCheckout — 0 de 5 conversiones de la cuenta cayeron ahí.
Fuera de esa ventana sí hay conversiones reales a cualquier hora (7am, 11am,
2-3pm, 10pm). Por eso la pausa se acotó a solo 4 horas (2am-6am CDMX) en vez
de las ~10.5h originales (23:30-9am) — se recupera exposición real en la
noche/mañana sin volver a exponerse a la ventana de "CPM barato, cero venta".

Uso:
    python3 dayparting.py --pause    # ejecutar ~02:00 CDMX
    python3 dayparting.py --resume   # ejecutar ~06:00 CDMX
    python3 dayparting.py --status   # ver qué haría, sin tocar nada

Guarda snapshot en dayparting_state.json para SOLO reactivar lo que él
mismo pausó (nunca toca ad sets que ya estaban pausados por otra razón,
ej. AS-TOFU-INTERESES en rotación).
"""
import json
import ssl
import sys
import urllib.request
import urllib.parse
import urllib.error
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent
STATE_FILE = ROOT / "dayparting_state.json"
LOG_FILE = ROOT / "logs" / "dayparting.log"
BASE = "https://graph.facebook.com/v21.0"
ACCOUNT_ID = "act_389427487828383"

# Fix real (7 ago 2026): cuando launchd corre este script (no interactivo, sin
# el entorno del usuario), el Python del framework no encuentra el cert store
# del sistema y truena con SSLCertVerificationError antes de pausar nada —
# causa raíz confirmada del pico de gasto de madrugada del 7 ago (el pause de
# las 23:30 del 6 ago corrió pero crasheó silenciosamente). Se fuerza el
# bundle de certifi explícito en vez de depender del contexto SSL default.
try:
    import certifi
    _SSL_CTX = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    _SSL_CTX = ssl.create_default_context()

# Campañas S2 vivas de venta (funnel completo). Se resuelven a IDs de ad set
# en vivo en cada corrida — no se hardcodean IDs de ad set porque cambian
# (rotación de creativos, nuevos ad sets, etc.)
CAMPAIGN_NAMES = [
    "EG_S2_1-TOFU",
    "EG_S2_2-MOFU",
    "EG_S2_3-BOFU",
    "EG_S2_ZZ-HOT-OFF",  # ex EG_S2_PURCHASE — por si alguien la reenciende
]

# Ad sets que NUNCA debe reactivar --resume (apagados a propósito; el snapshot de
# madrugada puede incluir IDs obsoletos si estuvieron ACTIVE a las 2am).
NEVER_RESUME_IDS = {
    "52530648531626",  # ZZ-OFF-MOFU-ATC
    "52519547042826",  # AS-P1-HOT
    "52530647277826",  # AS-MOFU-LINAJE - ATC (legacy)
    "52530647267026",  # AS-MOFU-JAULAS - ATC (legacy)
    "52530635121626",  # AS-MOFU-ESPEJO - ATC (legacy)
    "52532927982426",  # ZZ-NO-USAR-tibios-v1
    "52532928953626",  # ZZ-NO-USAR-tibios-v3-pre-catalog
}


def load_token():
    env_path = ROOT / ".env"
    vals = {}
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        vals[k.strip()] = v.strip().strip('"').strip("'")
    return vals["SYSTEM_USER_ACCESS_TOKEN"]


def api_get(path, token, **params):
    params["access_token"] = token
    url = f"{BASE}/{path}?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(url, context=_SSL_CTX) as r:
        return json.load(r)


def api_post(obj_id, token, **params):
    params["access_token"] = token
    data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(f"{BASE}/{obj_id}", data=data, method="POST")
    with urllib.request.urlopen(req, context=_SSL_CTX) as r:
        return json.load(r)


def get_relevant_adsets(token):
    """Ad sets ACTIVOS hoy dentro de las campañas del funnel S2."""
    camps = api_get(
        f"{ACCOUNT_ID}/campaigns", token,
        fields="name,effective_status", limit=100,
    )["data"]
    target_ids = {c["id"] for c in camps if c["name"] in CAMPAIGN_NAMES}

    out = []
    for cid in target_ids:
        asets = api_get(
            f"{cid}/adsets", token,
            fields="name,effective_status", limit=100,
        )["data"]
        out.extend(asets)
    return out


def log(msg):
    LOG_FILE.parent.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")


def cmd_status(token):
    adsets = get_relevant_adsets(token)
    log(f"STATUS — {len(adsets)} ad sets en campañas del funnel S2:")
    for a in adsets:
        log(f"  {a['name']:32} {a['effective_status']}")
    if STATE_FILE.exists():
        log(f"Estado guardado (última pausa): {STATE_FILE.read_text()}")
    else:
        log("Sin snapshot de pausa guardado (nada pausado por este script).")


def cmd_pause(token):
    adsets = get_relevant_adsets(token)
    active = [a for a in adsets if a["effective_status"] == "ACTIVE"]
    if not active:
        log("PAUSE: no hay ad sets ACTIVE ahora mismo — nada que pausar.")
        STATE_FILE.write_text(json.dumps({
            "paused_at": datetime.now(timezone.utc).isoformat(),
            "adset_ids": [],
        }, indent=2))
        return

    ids = []
    for a in active:
        try:
            api_post(a["id"], token, status="PAUSED")
            ids.append(a["id"])
            log(f"PAUSE OK: {a['name']} ({a['id']})")
        except urllib.error.HTTPError as e:
            log(f"PAUSE FALLÓ {a['name']}: {e.read().decode()[:300]}")

    STATE_FILE.write_text(json.dumps({
        "paused_at": datetime.now(timezone.utc).isoformat(),
        "adset_ids": ids,
    }, indent=2))
    log(f"PAUSE listo — {len(ids)} ad sets pausados hasta la reactivación de la mañana.")


def cmd_resume(token):
    if not STATE_FILE.exists():
        log("RESUME: no hay snapshot de pausa — no se reactiva nada (evita prender algo que estaba OFF por otra razón).")
        return

    state = json.loads(STATE_FILE.read_text())
    ids = [aid for aid in state.get("adset_ids", []) if aid not in NEVER_RESUME_IDS]
    skipped = [aid for aid in state.get("adset_ids", []) if aid in NEVER_RESUME_IDS]
    if skipped:
        log(f"RESUME: omitiendo {len(skipped)} ad sets en denylist (nunca auto-ON): {skipped}")
    if not ids:
        log("RESUME: snapshot vacío (no había nada activo cuando se pausó) — nada que reactivar.")
        return

    ok = 0
    for aid in ids:
        try:
            api_post(aid, token, status="ACTIVE")
            log(f"RESUME OK: {aid}")
            ok += 1
        except urllib.error.HTTPError as e:
            log(f"RESUME FALLÓ {aid}: {e.read().decode()[:300]}")

    log(f"RESUME listo — {ok}/{len(ids)} ad sets reactivados. Presupuesto del día disponible solo de aquí en adelante (horario CDMX diurno/nocturno, no madrugada).")
    STATE_FILE.write_text(json.dumps({**state, "resumed_at": datetime.now(timezone.utc).isoformat()}, indent=2))


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in ("--pause", "--resume", "--status"):
        print(__doc__)
        sys.exit(1)

    action = sys.argv[1]

    # Interruptor de seguridad: si dayparting_state.json trae {"disabled": true},
    # --pause y --resume no hacen nada. Puesto el 10 ago 2026 porque ese flag ya
    # existía en el estado (escrito el 10 ago, "Dirección: no pausa nocturna") pero el
    # script nunca lo leía — la desactivación no era durable y los jobs launchd
    # se recargaban solos en cada login. --status sí corre, es solo lectura.
    if action in ("--pause", "--resume"):
        try:
            if json.loads(STATE_FILE.read_text()).get("disabled") is True:
                log(f"{action} ABORTADO: dayparting deshabilitado en {STATE_FILE.name}. "
                    f"Quitar 'disabled' de ese archivo para reactivar.")
                sys.exit(0)
        except FileNotFoundError:
            pass
        except (json.JSONDecodeError, OSError) as e:
            log(f"AVISO: no se pudo leer {STATE_FILE.name} ({e}); se continúa.")

    token = load_token()
    if action == "--status":
        cmd_status(token)
    elif action == "--pause":
        cmd_pause(token)
    elif action == "--resume":
        cmd_resume(token)


if __name__ == "__main__":
    main()
