#!/usr/bin/env python3
"""
Sync Notion CEO — memoria viva de la agencia
=============================================
Cada mañana escribe en la página-cerebro del CEO (Notion) los números reales del día:
ventas por función (boletera en vivo) + marketing 7d (Meta API). Así el CEO bot de WA
responde siempre con datos frescos y Dirección ve todo en Notion.

- SOLO toca los bloques marcados como automáticos (header "⚡ ESTADO AUTOMÁTICO" y
  líneas que empiezan con "▸"). Lo escrito a mano por humanos/sesiones NO se toca,
  excepto las líneas "VENTAS:" y "CPA REAL:" (legacy 11 jul, superseded por este sync).
- Fuentes: Ag-12 --json (ocupación) · Ag-06 funnel.py --json (Meta 7d).
- Programado: launchd com.platea.ceo-notion-sync · diario 8:07.

Uso: python3 sync_notion_ceo.py
"""
import os, sys, json, subprocess, datetime, requests
from dotenv import load_dotenv

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 01_Agentes/
load_dotenv(os.path.join(BASE, "03_Media-Buyer", ".env"))

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
CEO_PAGE = "391d4176-2a97-81f3-90bc-f0bd25cb1a54"
H = {"Authorization": f"Bearer {NOTION_TOKEN}", "Notion-Version": "2022-06-28",
     "Content-Type": "application/json"}
PY = sys.executable

# prefijos de bloques que este script posee y puede borrar/reescribir
PREFIJOS_AUTO = ("⚡ ESTADO AUTOMÁTICO", "▸", "VENTAS: ", "CPA REAL: ")


def correr_json(cwd, script, *args):
    try:
        out = subprocess.run([PY, script, "--json", *args], cwd=cwd,
                             capture_output=True, text=True, timeout=180)
        return json.loads(out.stdout)
    except Exception as e:
        return {"error": str(e)}


def main():
    hoy = datetime.datetime.now()

    # 1. Datos en vivo
    boletera = correr_json(os.path.join(BASE, "12_Boletera"), "agent.py")
    funnel = correr_json(os.path.join(BASE, "06_Analytics-BI"), "funnel.py")

    lineas = [f"⚡ ESTADO AUTOMÁTICO — actualizado {hoy.strftime('%Y-%m-%d %H:%M')} por sync diario (8:07). Estos números mandan sobre cualquier cifra anterior."]

    fns = (boletera.get("snapshot") or {}).get("funciones", [])
    if fns:
        total = sum(f.get("vendidos", 0) for f in fns)
        detalle = " · ".join(f"{f['fecha'][5:]}: {f['vendidos']}" for f in fns if f.get("vendidos"))
        lineas.append(f"▸ VENTAS boletera (en vivo): {total} boletos acumulados. Por función: {detalle or 'sin ventas aún'}.")
        prox = next((f for f in fns if f.get("dias_restantes", -1) >= 0), None)
        if prox:
            lineas.append(f"▸ PRÓXIMA FUNCIÓN: {prox['fecha']} — {prox['vendidos']} vendidos, {prox['ocupacion_pct']}% de ocupación, faltan {prox['dias_restantes']} días.")
    else:
        lineas.append("▸ VENTAS: boletera no respondió en este sync — usar el email de las 8:03 como respaldo.")

    t = funnel.get("funnel_total") or {}
    if t:
        compras = t.get("compras_meta", 0)
        cpa = f"${t['spend']/compras:.0f}" if compras else "N/D"
        lineas.append(
            f"▸ MARKETING Meta últimos 7 días: ${t.get('spend',0):.0f} MXN gastados · "
            f"{t.get('clicks_link',0)} clicks · {t.get('checkouts',0)} inician pago · "
            f"{compras} compras vía pixel (CPA pixel {cpa}; el CPA real vs boletera va en el email de las 8:00).")
        fuga = funnel.get("fuga_principal")
        if fuga:
            lineas.append(f"▸ FUGA ACTUAL DEL FUNNEL: {fuga.get('diagnostico')} — ataca: {fuga.get('ataque')}.")
    else:
        lineas.append("▸ MARKETING: Meta API no respondió en este sync.")

    # 2. Borrar bloques automáticos anteriores
    borrados, cursor = 0, None
    while True:
        url = f"https://api.notion.com/v1/blocks/{CEO_PAGE}/children?page_size=100"
        if cursor: url += f"&start_cursor={cursor}"
        r = requests.get(url, headers=H, timeout=30).json()
        for b in r.get("results", []):
            tp = b["type"]
            texto = "".join(rt["plain_text"] for rt in b.get(tp, {}).get("rich_text", []))
            if texto.startswith(PREFIJOS_AUTO):
                requests.delete(f"https://api.notion.com/v1/blocks/{b['id']}", headers=H, timeout=30)
                borrados += 1
        if not r.get("has_more"): break
        cursor = r.get("next_cursor")

    # 3. Escribir sección fresca
    children = [{"object": "block", "type": "paragraph",
                 "paragraph": {"rich_text": [{"type": "text", "text": {"content": l[:1990]}}]}}
                for l in lineas]
    r = requests.patch(f"https://api.notion.com/v1/blocks/{CEO_PAGE}/children",
                       headers=H, json={"children": children}, timeout=30)
    print(f"{'✅' if r.ok else '❌'} Sync Notion CEO: {borrados} bloques viejos borrados, {len(children)} escritos. {'' if r.ok else r.text[:200]}")


if __name__ == "__main__":
    main()
