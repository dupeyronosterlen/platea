#!/usr/bin/env python3
"""
Agente 08 — Teasers desde campañas (Categoría A)
================================================
Cierra el círculo: lee performance de Meta (SOLO LECTURA) + banco de frases
aprobadas → propone/genera teasers con generar_cartel_teaser.py.

⛔ NO hace:
  - Crear/pausar/editar ads
  - Tocar elgorila / boletera / Workers / Stripe
  - Publicar en IG/FB (Dirección aprueba)

Uso:
  python3 generar_teasers_desde_campanas.py              # Meta 7d + genera top 3
  python3 generar_teasers_desde_campanas.py --dry-run    # solo propone, sin PNG
  python3 generar_teasers_desde_campanas.py --offline    # sin Meta (banco fijo)
  python3 generar_teasers_desde_campanas.py --days 14 --top 2 --formato feed
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

REPO = Path(__file__).resolve().parents[2]
ENV_PATH = REPO / "01_Agentes" / "03_Media-Buyer" / ".env"
TEASER_SCRIPT = Path(__file__).resolve().parent / "generar_cartel_teaser.py"
OUT_DIR = REPO / "05_Activos" / "el-gorila" / "carteles-s2" / "teaser"
PROPUESTAS_DIR = REPO / "05_Activos" / "el-gorila" / "carteles-s2" / "propuestas"
FOTOS = ["20.png", "24.png", "1.png", "21.png", "22.png"]

load_dotenv(ENV_PATH)
META_TOKEN = os.getenv("SYSTEM_USER_ACCESS_TOKEN", "")
AD_ACCOUNT_ID = os.getenv("AD_ACCOUNT_ID", "act_389427487828383")

# Banco de frases teaser (≤8 palabras / tono cartel). Se eligen por match con
# el nombre del ad ganador o, si no hay Meta, por prioridad fija.
BANCO = [
    {
        "id": "invitacion",
        "keys": ["invitacion", "invitación", "invite"],
        "frase": "37 años. Misma jaula.",
        "ancla": None,
        "prioridad": 10,
    },
    {
        "id": "feel",
        "keys": ["feel", "sentir", "emocion"],
        "frase": "No buscaba libertad. Solo una salida.",
        "ancla": None,
        "prioridad": 9,
    },
    {
        "id": "jaulas",
        "keys": ["jaula", "jaulas"],
        "frase": "La jaula era pequeña.",
        "ancla": "37 años en escena",
        "prioridad": 8,
    },
    {
        "id": "kafka",
        "keys": ["kafka", "academia", "informe"],
        "frase": "Kafka. Vivo. En escena.",
        "ancla": None,
        "prioridad": 7,
    },
    {
        "id": "salida",
        "keys": ["salida", "libertad"],
        "frase": "Solo una salida. No libertad.",
        "ancla": None,
        "prioridad": 6,
    },
    {
        "id": "37",
        "keys": ["37", "trayectoria", "anos", "años"],
        "frase": "37 años. El mismo texto.",
        "ancla": None,
        "prioridad": 5,
    },
    {
        "id": "titulo",
        "keys": ["gorila", "purchase", "p1", "comercial"],
        "frase": None,  # usa --solo-titulo
        "ancla": "37 años en escena",
        "prioridad": 3,
    },
]


def _purchases(actions: list | None) -> int:
    for a in actions or []:
        if a.get("action_type") in (
            "purchase",
            "omni_purchase",
            "offsite_conversion.fb_pixel_purchase",
        ):
            return int(float(a.get("value", 0)))
    return 0


def fetch_ads_insights(days: int = 7) -> list[dict]:
    """READ-ONLY: insights a nivel ad. Nunca muta la cuenta."""
    if not META_TOKEN:
        raise RuntimeError("Sin SYSTEM_USER_ACCESS_TOKEN en .env de Ag-03")
    base = f"https://graph.facebook.com/v19.0/{AD_ACCOUNT_ID}/insights"
    params = {
        "access_token": META_TOKEN,
        "date_preset": f"last_{days}d",
        "level": "ad",
        "fields": "ad_name,ad_id,campaign_name,impressions,clicks,spend,ctr,actions",
        "limit": 100,
    }
    r = requests.get(base, params=params, timeout=30)
    r.raise_for_status()
    rows = []
    for row in r.json().get("data", []):
        spend = float(row.get("spend", 0) or 0)
        clicks = int(row.get("clicks", 0) or 0)
        impr = int(row.get("impressions", 0) or 0)
        purch = _purchases(row.get("actions"))
        ctr = float(row.get("ctr", 0) or 0)
        rows.append(
            {
                "ad_name": row.get("ad_name") or "",
                "ad_id": row.get("ad_id"),
                "campaign": row.get("campaign_name") or "",
                "spend": spend,
                "clicks": clicks,
                "impressions": impr,
                "purchases": purch,
                "ctr": ctr,
                # score: compras pesan más; CTR como desempate; spend mínimo para filtrar ruido
                "score": purch * 1000 + ctr * 10 + min(spend, 50),
            }
        )
    rows.sort(key=lambda x: (-x["score"], -x["spend"]))
    return rows


def match_banco(ad_name: str) -> dict | None:
    name = (ad_name or "").lower()
    best = None
    for item in BANCO:
        if any(k in name for k in item["keys"]):
            if best is None or item["prioridad"] > best["prioridad"]:
                best = item
    return best


def pick_candidates(ads: list[dict] | None, top: int) -> list[dict]:
    """Une ads Meta con frases del banco. Si offline/vacío, usa banco por prioridad."""
    chosen: list[dict] = []
    used_ids: set[str] = set()

    if ads:
        for ad in ads:
            if ad["spend"] < 1 and ad["purchases"] == 0 and ad["clicks"] < 5:
                continue
            phrase = match_banco(ad["ad_name"]) or match_banco(ad["campaign"])
            if not phrase or phrase["id"] in used_ids:
                continue
            used_ids.add(phrase["id"])
            chosen.append(
                {
                    "source": "meta",
                    "ad_name": ad["ad_name"],
                    "campaign": ad["campaign"],
                    "spend": ad["spend"],
                    "purchases": ad["purchases"],
                    "ctr": ad["ctr"],
                    "clicks": ad["clicks"],
                    "banco_id": phrase["id"],
                    "frase": phrase["frase"],
                    "ancla": phrase["ancla"],
                }
            )
            if len(chosen) >= top:
                return chosen

    # Relleno / offline
    for phrase in sorted(BANCO, key=lambda x: -x["prioridad"]):
        if phrase["id"] in used_ids:
            continue
        used_ids.add(phrase["id"])
        chosen.append(
            {
                "source": "banco",
                "ad_name": "(sin match Meta)",
                "campaign": "",
                "spend": 0,
                "purchases": 0,
                "ctr": 0,
                "clicks": 0,
                "banco_id": phrase["id"],
                "frase": phrase["frase"],
                "ancla": phrase["ancla"],
            }
        )
        if len(chosen) >= top:
            break
    return chosen


def render_teaser(cand: dict, foto: str, formato: str, dry_run: bool) -> Path | None:
    cmd = [sys.executable, str(TEASER_SCRIPT), "--foto", foto, "--formato", formato]
    if cand["frase"]:
        cmd += ["--frase", cand["frase"]]
        if cand.get("ancla"):
            cmd += ["--ancla", cand["ancla"]]
    else:
        cmd += ["--solo-titulo"]
        if cand.get("ancla"):
            cmd += ["--ancla", cand["ancla"]]

    if dry_run:
        print("  DRY:", " ".join(cmd))
        return None

    subprocess.run(cmd, check=True, cwd=str(TEASER_SCRIPT.parent))
    # localizar último archivo generado con slug de frase
    slug = re.sub(r"[^a-z0-9áéíóúñü]+", "-", (cand["frase"] or "titulo").lower()).strip("-")[:48]
    matches = sorted(OUT_DIR.glob(f"teaser-{slug}-{formato}.png"), key=lambda p: p.stat().st_mtime)
    if not matches and not cand["frase"]:
        matches = sorted(OUT_DIR.glob(f"teaser-titulo-{formato}.png"), key=lambda p: p.stat().st_mtime)
    return matches[-1] if matches else None


def write_proposal(cands: list[dict], outputs: list[dict], days: int) -> Path:
    PROPUESTAS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y-%m-%d_%H%M")
    path = PROPUESTAS_DIR / f"{stamp}_ag08_teasers-desde-campanas.md"
    lines = [
        f"# Propuesta teasers — {stamp}",
        "> Agente: 08  |  Estado: **BORRADOR — requiere OK de Dirección**",
        "> ⛔ No publicado. No toca boletera ni ads.",
        "",
        f"Ventana Meta: últimos **{days}** días (solo lectura).",
        "",
        "| # | Fuente | Ad / campaña | Spend | Purch | CTR | Frase teaser | Archivo |",
        "|---|--------|--------------|-------|-------|-----|--------------|---------|",
    ]
    for i, (c, o) in enumerate(zip(cands, outputs), 1):
        arch = o.get("path") or "(dry-run)"
        if isinstance(arch, Path):
            try:
                arch = arch.relative_to(REPO)
            except ValueError:
                arch = str(arch)
        lines.append(
            f"| {i} | {c['source']} | {c['ad_name'][:40]} | ${c['spend']:.0f} | "
            f"{c['purchases']} | {c['ctr']:.2f}% | {c['frase'] or 'EL GORILA'} | `{arch}` |"
        )
    lines += [
        "",
        "## Siguiente paso",
        "1. Dirección revisa PNGs en `carteles-s2/teaser/`.",
        "2. Si OK → Ag-01 sella / publica (humano).",
        "3. Si no → ajustar `--frase` a mano o ampliar BANCO en este script.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def main():
    p = argparse.ArgumentParser(description="Teasers Categoría A desde campañas (read-only)")
    p.add_argument("--days", type=int, default=7)
    p.add_argument("--top", type=int, default=3)
    p.add_argument("--formato", default="feed", choices=["feed", "square", "story", "all"])
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--offline", action="store_true", help="No llama a Meta; solo banco")
    args = p.parse_args()

    print("🎬 Ag-08 teasers←campañas  ⛔ read-only Meta · salida local")
    ads = None
    if not args.offline:
        try:
            ads = fetch_ads_insights(args.days)
            print(f"  Meta: {len(ads)} ads con insights ({args.days}d)")
            for a in ads[:5]:
                print(
                    f"    · {a['ad_name'][:45]:45} spend=${a['spend']:.0f} "
                    f"purch={a['purchases']} ctr={a['ctr']:.2f}"
                )
        except Exception as e:
            print(f"  ⚠️ Meta no disponible ({e}) — fallback banco")
            ads = None
    else:
        print("  Modo --offline (sin Meta)")

    cands = pick_candidates(ads, args.top)
    if not cands:
        raise SystemExit("Sin candidatos")

    outputs = []
    for i, c in enumerate(cands):
        foto = FOTOS[i % len(FOTOS)]
        print(f"\n→ [{c['banco_id']}] {c['frase'] or 'EL GORILA'}  (foto {foto})")
        path = render_teaser(c, foto, args.formato if args.formato != "all" else "feed", args.dry_run)
        if args.formato == "all" and not args.dry_run:
            for fmt in ("square", "story"):
                render_teaser(c, foto, fmt, False)
        outputs.append({"path": path, "foto": foto})

    prop = write_proposal(cands, outputs, args.days)
    print(f"\n📋 Propuesta: {prop.relative_to(REPO)}")
    print("✅ Listo. Nada publicado. Nada tocado en boletera/ads.")


if __name__ == "__main__":
    main()
