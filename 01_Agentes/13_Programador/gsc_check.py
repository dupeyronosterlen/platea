#!/usr/bin/env python3
"""Ag-13 — Search Console (solo lectura).

Lista sitemaps e inspecciona URLs. No pide indexación (eso no existe en la API
para páginas normales; el botón del panel es de Dirección si Inspection dice UNKNOWN).

Requiere scope webmasters en el refresh de privado/credenciales/.env.
Si sale ACCESS_TOKEN_SCOPE_INSUFFICIENT: correr _oauth_master.py (Ag-06) una vez.

Uso:
  python3 gsc_check.py
  python3 gsc_check.py --submit-sitemap   # PUT del sitemap.xml (va de Dirección)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / "privado" / "credenciales" / ".env")

SITE = "sc-domain:elgorilateatro.com.mx"
SITEMAP = "https://elgorilateatro.com.mx/sitemap.xml"
INSPECT = [
    "https://elgorilateatro.com.mx/",
    "https://elgorilateatro.com.mx/sobre-la-obra.html",
    "https://elgorilateatro.com.mx/funciones.html",
    "https://elgorilateatro.com.mx/historia-del-gorila.html",
    "https://elgorilateatro.com.mx/presskit/presskit2026.html",
    "https://elgorilateatro.com.mx/programa/v1.html",
    "https://elgorilateatro.com.mx/programa/v2.html",
    "https://elgorilateatro.com.mx/programa/v3.html",
    "https://elgorilateatro.com.mx/programa/v4.html",
]


def access_token() -> str:
    cid = os.getenv("GOOGLE_ADS_CLIENT_ID")
    sec = os.getenv("GOOGLE_ADS_CLIENT_SECRET")
    rt = os.getenv("GOOGLE_MASTER_REFRESH_TOKEN") or os.getenv("GOOGLE_ADS_REFRESH_TOKEN")
    if not all([cid, sec, rt]):
        sys.exit("Faltan GOOGLE_ADS_CLIENT_ID/SECRET o refresh en .env")
    r = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "client_id": cid,
            "client_secret": sec,
            "refresh_token": rt,
            "grant_type": "refresh_token",
        },
        timeout=20,
    )
    tok = r.json().get("access_token")
    if not tok:
        sys.exit(f"oauth_failed {r.status_code}: {r.text[:240]}")
    return tok


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--submit-sitemap", action="store_true")
    args = ap.parse_args()
    token = access_token()
    h = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    enc = requests.utils.quote(SITE, safe="")

    sites = requests.get(
        "https://www.googleapis.com/webmasters/v3/sites", headers=h, timeout=30
    )
    if sites.status_code == 403 and "SCOPE" in sites.text.upper():
        sys.exit(
            "SCOPE_INSUFFICIENT: el refresh no tiene webmasters. "
            "Dirección abre el link de 01_Agentes/06_Analytics-BI/_oauth_master.py una vez."
        )
    sites.raise_for_status()
    print("SITES", json.dumps(sites.json(), ensure_ascii=False, indent=2)[:2000])

    sm = requests.get(
        f"https://www.googleapis.com/webmasters/v3/sites/{enc}/sitemaps",
        headers=h,
        timeout=30,
    )
    print("SITEMAPS", sm.status_code)
    print(sm.text[:3000])

    if args.submit_sitemap:
        put = requests.put(
            f"https://www.googleapis.com/webmasters/v3/sites/{enc}/sitemaps/"
            + requests.utils.quote(SITEMAP, safe=""),
            headers=h,
            timeout=30,
        )
        print("SUBMIT", put.status_code, put.text[:500])

    for url in INSPECT:
        r = requests.post(
            "https://searchconsole.googleapis.com/v1/urlInspection/index:inspect",
            headers=h,
            json={"inspectionUrl": url, "siteUrl": SITE},
            timeout=30,
        )
        body = r.json()
        result = (body.get("inspectionResult") or {}).get("indexStatusResult") or {}
        print(
            json.dumps(
                {
                    "url": url,
                    "http": r.status_code,
                    "verdict": result.get("verdict"),
                    "coverage": result.get("coverageState"),
                    "lastCrawl": result.get("lastCrawlTime"),
                    "robots": result.get("robotsTxtState"),
                    "indexingState": result.get("indexingState"),
                    "err": None if r.ok else body.get("error", body) ,
                },
                ensure_ascii=False,
            )
        )


if __name__ == "__main__":
    main()
