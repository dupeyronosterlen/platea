#!/usr/bin/env python3
"""
Guarda el API Token de Cloudflare en .env — pero solo si Cloudflare lo acepta.

Existe porque el 18 jul 2026 se pegó un token incompleto, se guardó igual, y el error
no se descubrió hasta el 31 jul. Este script lo valida ANTES de escribirlo: si el token
está mal, no toca el archivo y te lo dice de inmediato.

Uso (en tu Terminal):
    python3 guardar_token_cloudflare.py

Te va a pedir el token. Pégalo y dale Enter — no se ve mientras lo escribes (es normal,
así no queda en el historial de la terminal).
"""
import os
import re
import sys
from getpass import getpass
from pathlib import Path

import requests

ENV      = Path(__file__).parent / ".env"
ZONE_ID  = "c810a86aac2ff1050510debbc192f7fd"   # elgorilateatro.com.mx
CLAVE    = "CLOUDFLARE_DNS_API_TOKEN"


def main():
    print("\n  Token de Cloudflare para elgorilateatro.com.mx")
    print("  " + "─" * 52)
    print("  Pégalo y dale Enter. No se va a ver mientras escribes.\n")

    token = getpass("  Token: ").strip()
    if not token:
        print("\n  ❌ No pegaste nada. Cancelado, no se tocó el archivo.\n")
        return 1

    print(f"\n  Recibí {len(token)} caracteres. Preguntándole a Cloudflare...\n")
    H = {"Authorization": f"Bearer {token}"}

    # 1. ¿El token existe y está activo?
    try:
        r = requests.get("https://api.cloudflare.com/client/v4/user/tokens/verify",
                         headers=H, timeout=20)
    except requests.RequestException as e:
        print(f"  ❌ No me pude conectar a Cloudflare: {e}\n")
        return 1

    if r.status_code != 200 or not r.json().get("success"):
        print("  ❌ Cloudflare RECHAZA este token.")
        print("     Casi siempre es que se copió incompleto — Cloudflare solo lo enseña")
        print("     una vez, y si cerraste esa pantalla hay que generar otro.")
        print("\n     NO se tocó el archivo .env.\n")
        return 1
    print("  ✅ El token es válido y está activo.")

    # 2. ¿Alcanza para lo que necesitamos (leer/escribir DNS de esta zona)?
    r2 = requests.get(f"https://api.cloudflare.com/client/v4/zones/{ZONE_ID}/dns_records",
                      headers=H, params={"per_page": 1}, timeout=20)
    if r2.status_code != 200 or not r2.json().get("success"):
        print("\n  ⚠️  El token sirve, pero NO tiene acceso al DNS de elgorilateatro.com.mx.")
        print("     Al crearlo faltó darle permisos, o se limitó a otra zona.")
        print("     Necesita:  Zone · DNS · Edit   +   Zone · Zone · Edit")
        print("     y en Zone Resources: Include · Specific zone · elgorilateatro.com.mx")
        print("\n     NO se tocó el archivo .env.\n")
        return 1
    print("  ✅ Tiene acceso al DNS de elgorilateatro.com.mx.")

    # 3. Guardar, reemplazando la línea vieja y borrando el aviso de "pendiente".
    texto = ENV.read_text() if ENV.exists() else ""
    texto = re.sub(r"(?m)^#\s*⚠️\s*PENDIENTE 18 jul 2026:.*?(?=^[A-Z_]+=)", "", texto, flags=re.S)
    linea = f"{CLAVE}={token}"
    if re.search(rf"(?m)^{CLAVE}=.*$", texto):
        texto = re.sub(rf"(?m)^{CLAVE}=.*$", linea, texto)
    else:
        texto = texto.rstrip("\n") + f"\n{linea}\n"

    ENV.write_text(texto)
    os.chmod(ENV, 0o600)
    print(f"  ✅ Guardado en {ENV.name} (permisos 600, solo tú lo puedes leer).")

    print("\n  " + "─" * 52)
    print("  Listo. Ya puedes correr la redirección:\n")
    print("      python3 redirigir_subdominio_boletos.py            (prueba, no cambia nada)")
    print("      python3 redirigir_subdominio_boletos.py --aplicar  (lo hace de verdad)\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
