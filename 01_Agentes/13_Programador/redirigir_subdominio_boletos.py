#!/usr/bin/env python3
"""
Recrear boletos.elgorilateatro.com.mx SOLO como redirección 301 → elgorilateatro.com.mx/boletos

Contexto (31 jul 2026): el subdominio apuntaba por CNAME a la boletera vieja de Ticket Tailor.
Dirección lo borró y hoy da NXDOMAIN. Este script lo vuelve a crear pero SIN origen real: un registro
AAAA al agujero negro `100::` con proxy de Cloudflare encendido, más una Single Redirect Rule que
manda todo a la boletera propia conservando el path y el query string.

Para qué sirve: recuperar cualquier link viejo que ande en circulación (resultados de Google que
GSC seguía reportando, correos de la temporada pasada, material impreso, posts viejos). NO es una
jugada de ventas — el tráfico que se midió del 25 al 29 jul eran bots recibiendo error 530.

REQUISITO — token de Cloudflare (el OAuth de wrangler NO sirve, solo trae `zone (read)`):
  Cloudflare → My Profile → API Tokens → Create Token → Custom token
    Permissions:  Zone · DNS   · Edit
                  Zone · Zone  · Edit      (necesario para las Redirect Rules)
    Zone Resources: Include · Specific zone · elgorilateatro.com.mx
  Copiar el token COMPLETO (Cloudflare solo lo muestra una vez) y guardarlo en
  01_Agentes/13_Programador/.env como:
      CLOUDFLARE_DNS_API_TOKEN=...

Uso:
    python3 redirigir_subdominio_boletos.py              # dry-run: solo dice qué haría
    python3 redirigir_subdominio_boletos.py --aplicar    # ejecuta de verdad
    python3 redirigir_subdominio_boletos.py --verificar  # comprueba el resultado en vivo
"""
import os
import sys
import json
import requests
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass

ZONE_ID   = "c810a86aac2ff1050510debbc192f7fd"   # elgorilateatro.com.mx
SUBDOMAIN = "boletos.elgorilateatro.com.mx"
DESTINO   = "https://elgorilateatro.com.mx/boletos"
API       = "https://api.cloudflare.com/client/v4"

TOKEN = os.getenv("CLOUDFLARE_DNS_API_TOKEN", "").strip()
H = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

APLICAR   = "--aplicar" in sys.argv
VERIFICAR = "--verificar" in sys.argv


def _check(r, que):
    """Levanta con un mensaje legible si la API de Cloudflare devolvió error."""
    try:
        d = r.json()
    except ValueError:
        raise SystemExit(f"❌ {que}: respuesta no-JSON (HTTP {r.status_code})")
    if not d.get("success"):
        raise SystemExit(f"❌ {que}: {json.dumps(d.get('errors'), ensure_ascii=False)}")
    return d["result"]


def validar_token():
    if not TOKEN:
        raise SystemExit(
            "❌ Falta CLOUDFLARE_DNS_API_TOKEN en 01_Agentes/13_Programador/.env\n"
            "   Ver las instrucciones al inicio de este archivo."
        )
    r = requests.get(f"{API}/user/tokens/verify", headers=H, timeout=20)
    if r.status_code != 200 or not r.json().get("success"):
        raise SystemExit(
            f"❌ El token no pasa /user/tokens/verify (HTTP {r.status_code}).\n"
            "   Suele ser que se copió incompleto — Cloudflare solo lo muestra una vez.\n"
            "   Genera uno nuevo con DNS:Edit + Zone:Edit sobre elgorilateatro.com.mx."
        )
    print("✅ Token válido")


def paso_1_dns():
    """AAAA a 100:: con proxy encendido — el patrón estándar para un hostname solo-redirección."""
    r = requests.get(f"{API}/zones/{ZONE_ID}/dns_records",
                     headers=H, params={"name": SUBDOMAIN}, timeout=30)
    existentes = _check(r, "listar DNS")

    if existentes:
        rec = existentes[0]
        print(f"ℹ️  Ya existe {rec['type']} {SUBDOMAIN} → {rec['content']} (proxied={rec.get('proxied')})")
        if rec["type"] == "AAAA" and rec["content"] == "100::" and rec.get("proxied"):
            print("   Ya está como lo queremos, no se toca.")
            return rec["id"]
        print("   ⚠️  Apunta a otra cosa. Revísalo a mano antes de seguir — este script NO lo pisa.")
        raise SystemExit(1)

    payload = {
        "type": "AAAA", "name": SUBDOMAIN, "content": "100::",
        "proxied": True, "ttl": 1,
        "comment": "Solo-redireccion a /boletos. Sin origen real. Ver redirigir_subdominio_boletos.py",
    }
    if not APLICAR:
        print(f"[dry-run] Crearía DNS: AAAA {SUBDOMAIN} → 100:: (proxied)")
        return None
    rec = _check(requests.post(f"{API}/zones/{ZONE_ID}/dns_records",
                               headers=H, json=payload, timeout=30), "crear DNS")
    print(f"✅ DNS creado: AAAA {SUBDOMAIN} → 100:: (proxied)")
    return rec["id"]


def paso_2_redirect():
    """Single Redirect: 301 conservando path + query string."""
    fase = "http_request_dynamic_redirect"
    r = requests.get(f"{API}/zones/{ZONE_ID}/rulesets/phases/{fase}/entrypoint", headers=H, timeout=30)
    ruleset = r.json().get("result") if r.status_code == 200 else None

    regla = {
        "action": "redirect",
        "expression": f'(http.host eq "{SUBDOMAIN}")',
        "description": "boletos.* (Ticket Tailor muerto) -> boletera propia /boletos",
        "action_parameters": {
            "from_value": {
                "status_code": 301,
                "target_url": {
                    # Conserva el path y el query original: /events/123?x=1 -> /boletos/events/123?x=1
                    "expression": f'concat("{DESTINO}", http.request.uri.path, '
                                  f'if(len(http.request.uri.query) > 0, concat("?", http.request.uri.query), ""))'
                },
                "preserve_query_string": False,
            }
        },
    }

    if ruleset and any(x.get("description") == regla["description"]
                       for x in (ruleset.get("rules") or [])):
        print("ℹ️  La regla de redirección ya existe, no se duplica.")
        return

    if not APLICAR:
        print(f"[dry-run] Crearía Redirect Rule 301: {SUBDOMAIN}/* → {DESTINO}/* (conserva path y query)")
        return

    if ruleset:
        _check(requests.post(f"{API}/zones/{ZONE_ID}/rulesets/{ruleset['id']}/rules",
                             headers=H, json=regla, timeout=30), "agregar regla")
    else:
        _check(requests.put(f"{API}/zones/{ZONE_ID}/rulesets/phases/{fase}/entrypoint",
                            headers=H,
                            json={"rules": [regla], "name": "redirects", "kind": "zone", "phase": fase},
                            timeout=30), "crear ruleset")
    print(f"✅ Redirect Rule 301 creada: {SUBDOMAIN}/* → {DESTINO}/*")


def verificar():
    print(f"\n--- Verificación en vivo de {SUBDOMAIN} ---")
    for url in (f"https://{SUBDOMAIN}/", f"https://{SUBDOMAIN}/events/algo-viejo?utm_source=x"):
        try:
            r = requests.get(url, allow_redirects=True, timeout=25)
            cadena = " → ".join([h.url for h in r.history] + [r.url])
            estado = "✅" if "elgorilateatro.com.mx/boletos" in r.url else "⚠️ "
            print(f"{estado} {url}\n     {cadena}  (HTTP {r.status_code})")
        except requests.RequestException as e:
            print(f"❌ {url}\n     {type(e).__name__}: {str(e)[:90]}")
    print("\nSi acabas de aplicar y falla, dale 1-2 minutos: el certificado del subdominio tarda en emitirse.")


if __name__ == "__main__":
    if VERIFICAR:
        verificar()
        sys.exit(0)

    print(f"{'APLICANDO' if APLICAR else 'DRY-RUN (nada se modifica)'} · {SUBDOMAIN} → {DESTINO}\n")
    validar_token()
    paso_1_dns()
    paso_2_redirect()

    if APLICAR:
        print("\nListo. Espera 1-2 min a que salga el certificado y corre:")
        print("  python3 redirigir_subdominio_boletos.py --verificar")
    else:
        print("\nNada se modificó. Para ejecutar de verdad:")
        print("  python3 redirigir_subdominio_boletos.py --aplicar")
