#!/usr/bin/env python3
"""Snapshot de pauta + funnel para el canvas 'pauta viva'.

Escribe 01_Agentes/03_Media-Buyer/pauta-vivo.json (Meta + Google + Stripe).
El canvas no puede hacer fetch: se regenera en sesión leyendo este JSON.

  python3 pauta_vivo.py
"""
from __future__ import annotations

import datetime
import json
import os
from collections import defaultdict
from pathlib import Path

import requests
from dotenv import load_dotenv
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / "privado" / "credenciales" / ".env")

TOKEN = os.getenv("SYSTEM_USER_ACCESS_TOKEN")
GRAPH = "https://graph.facebook.com/v21.0"
ACT = "act_389427487828383"
CDMX = ZoneInfo("America/Mexico_City")
STRIPE = os.getenv("STRIPE_RESTRICTED_KEY")
UMBRAL = 245
OUT = Path(__file__).resolve().parent / "pauta-vivo.json"

WATCH = {
    "52529353279826": "AS-TOFU-ESPEJO",
    "52529353292026": "AS-TOFU-JAULAS",
    "52529353307026": "AS-TOFU-LINAJE",
    "52530641689826": "AS-TOFU-ESPEJO-ESTATICOS",
    "52529353558026": "AS-TOFU-INTERESES",
    "52531000456626": "AS-MOFU-1-VC",
    "52529365476226": "AS-MOFU-2-SOCIAL90",
    "52533073748826": "AS-MOFU-2-IC-VIS",
    "52532543021226": "AS-MOFU-3-AFIN",
    "52532934022626": "AS-BOFU-PURCHASE",
    "52519547042826": "AS-P1-HOT",
}


def gget(path: str, **params):
    params["access_token"] = TOKEN
    r = requests.get(f"{GRAPH}{path}", params=params, timeout=60)
    d = r.json()
    if "error" in d:
        raise RuntimeError(path + " " + json.dumps(d["error"], ensure_ascii=False)[:300])
    return d


def pick_actions(actions):
    m = {a["action_type"]: float(a["value"]) for a in (actions or [])}

    def pick(*keys):
        for k in keys:
            if k in m:
                return m[k]
        return 0.0

    return {
        "link_click": pick("link_click"),
        "lpv": pick("landing_page_view"),
        "vc": pick("offsite_conversion.fb_pixel_view_content", "view_content"),
        "ic": pick("offsite_conversion.fb_pixel_initiate_checkout", "initiate_checkout"),
        "atc": pick("offsite_conversion.fb_pixel_add_to_cart", "add_to_cart"),
        "purchase": pick("offsite_conversion.fb_pixel_purchase", "purchase"),
    }


def pull_sets():
    sets = {}
    for aid, name in WATCH.items():
        a = gget(
            f"/{aid}",
            fields="id,name,status,effective_status,daily_budget,optimization_goal,targeting,created_time",
        )
        t = a.get("targeting") or {}
        geo = t.get("geo_locations") or {}
        pins = [
            {
                "lat": c.get("latitude"),
                "lng": c.get("longitude"),
                "r": c.get("radius"),
                "u": c.get("distance_unit"),
            }
            for c in geo.get("custom_locations") or []
        ]
        inc = [x.get("name") or x.get("id") for x in (t.get("custom_audiences") or [])]
        exc = [x.get("name") or x.get("id") for x in (t.get("excluded_custom_audiences") or [])]
        sets[name] = {
            "id": aid,
            "name": a.get("name"),
            "status": a.get("status"),
            "effective": a.get("effective_status"),
            "budget": int(a.get("daily_budget") or 0) / 100,
            "opt": a.get("optimization_goal"),
            "age": [t.get("age_min"), t.get("age_max")],
            "pins": pins,
            "include": inc,
            "exclude": exc,
            "aa": (t.get("targeting_automation") or {}).get("advantage_audience"),
            "created": a.get("created_time"),
        }
    return sets


def pull_insights(preset: str):
    rows = gget(
        f"/{ACT}/insights",
        level="adset",
        date_preset=preset,
        fields="adset_id,adset_name,campaign_name,spend,impressions,clicks,reach,frequency,actions",
        limit=200,
    ).get("data", [])
    out = []
    for r in rows:
        aid = r.get("adset_id")
        if aid not in WATCH:
            continue
        acts = pick_actions(r.get("actions"))
        out.append(
            {
                "id": aid,
                "name": r.get("adset_name"),
                "camp": r.get("campaign_name"),
                "spend": round(float(r.get("spend") or 0), 2),
                "impr": int(r.get("impressions") or 0),
                "clicks": int(r.get("clicks") or 0),
                "reach": int(r.get("reach") or 0),
                "freq": round(float(r.get("frequency") or 0), 2),
                **acts,
            }
        )
    out.sort(key=lambda x: -x["spend"])
    return out


def pull_account(preset: str):
    row = (
        gget(
            f"/{ACT}/insights",
            date_preset=preset,
            fields="spend,impressions,clicks,actions",
            level="account",
        ).get("data")
        or [{}]
    )[0]
    return {
        "spend": float(row.get("spend") or 0),
        "clicks": int(row.get("clicks") or 0),
        **pick_actions(row.get("actions")),
    }


def stripe_paginar(url, params):
    out = []
    while True:
        r = requests.get(url, params=params, auth=(STRIPE, ""), timeout=30)
        r.raise_for_status()
        data = r.json()
        out += data.get("data", [])
        if not data.get("has_more"):
            return out
        params["starting_after"] = out[-1]["id"]


def bucket(o):
    c = (o["camp"] or "").lower()
    s = (o["src"] or "").lower()
    t = (o["term"] or "").lower()
    if "search" in c or (s == "google" and "demand" not in c):
        return "search"
    if "demand" in c:
        return "demandgen"
    if "bofu" in c or "as-bofu" in t:
        return "bofu"
    if "social90" in t:
        return "social90"
    if "tofu" in c or "as-tofu" in t:
        return "tofu"
    if "afin" in t:
        return "afin"
    if "mofu" in c:
        return "mofu"
    if s in ("ig", "fb", "facebook", "instagram"):
        return "meta_org_or_lost_utm"
    if not c and not s:
        return "sin_utm"
    return "otro"


def pull_stripe(now):
    if not STRIPE:
        return {"tot": {}, "by_canal": {}, "orders": []}
    desde = int((now - datetime.timedelta(days=7)).timestamp())
    ses = stripe_paginar(
        "https://api.stripe.com/v1/checkout/sessions",
        {"limit": 100, "created[gte]": desde, "status": "complete"},
    )
    orders = []
    for s in ses:
        if s.get("payment_status") != "paid":
            continue
        md = s.get("metadata") or {}
        qty = int(md.get("cantidad", 1) or 1)
        mxn = (s.get("amount_total") or 0) / 100
        unit = mxn / qty if qty else mxn
        if unit < UMBRAL:
            continue
        created = datetime.datetime.fromtimestamp(s["created"], tz=CDMX)
        orders.append(
            {
                "when": created.strftime("%Y-%m-%d %H:%M"),
                "fn": md.get("fecha", "?"),
                "qty": qty,
                "mxn": mxn,
                "src": md.get("utm_source") or "",
                "camp": md.get("utm_campaign") or "",
                "term": md.get("utm_term") or "",
            }
        )
    agg = defaultdict(lambda: {"n": 0, "qty": 0, "mxn": 0.0})
    for o in orders:
        b = bucket(o)
        agg[b]["n"] += 1
        agg[b]["qty"] += o["qty"]
        agg[b]["mxn"] += o["mxn"]
    return {
        "tot": {
            "ordenes": len(orders),
            "boletos": sum(o["qty"] for o in orders),
            "ingreso": round(sum(o["mxn"] for o in orders), 2),
        },
        "by_canal": {
            k: {"ordenes": v["n"], "boletos": v["qty"], "ingreso": round(v["mxn"], 2)}
            for k, v in agg.items()
        },
        "orders": orders,
    }


def pull_google():
    dev = os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN")
    cid = (os.getenv("GOOGLE_ADS_CUSTOMER_ID") or "2681423694").replace("-", "")
    login = (os.getenv("GOOGLE_ADS_LOGIN_CUSTOMER_ID") or "8974056133").replace("-", "")
    tok = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "client_id": os.getenv("GOOGLE_ADS_CLIENT_ID"),
            "client_secret": os.getenv("GOOGLE_ADS_CLIENT_SECRET"),
            "refresh_token": os.getenv("GOOGLE_ADS_REFRESH_TOKEN"),
            "grant_type": "refresh_token",
        },
        timeout=15,
    )
    tok.raise_for_status()
    gh = {
        "Authorization": f"Bearer {tok.json()['access_token']}",
        "developer-token": dev,
        "login-customer-id": login,
        "Content-Type": "application/json",
    }
    end = datetime.date.today()
    start = end - datetime.timedelta(days=7)

    def gaql(q):
        r = requests.post(
            f"https://googleads.googleapis.com/v22/customers/{cid}/googleAds:search",
            headers=gh,
            json={"query": q},
            timeout=30,
        )
        r.raise_for_status()
        return r.json()

    q = f"""
        SELECT campaign.name, campaign.status, campaign_budget.amount_micros,
               metrics.cost_micros, metrics.clicks, metrics.impressions, metrics.conversions,
               metrics.search_impression_share, metrics.search_budget_lost_impression_share
        FROM campaign
        WHERE campaign.name IN ('EG_S2_SEARCH', 'EG_S2_DEMANDGEN')
          AND segments.date BETWEEN '{start}' AND '{end}'
    """
    gads = {}
    for row in gaql(q).get("results") or []:
        name = row["campaign"]["name"]
        a = gads.setdefault(
            name,
            {
                "status": row["campaign"]["status"],
                "budget": int(row.get("campaignBudget", {}).get("amountMicros") or 0) / 1e6,
                "spend": 0.0,
                "clicks": 0,
                "impr": 0,
                "conv": 0.0,
                "is": None,
                "lost_b": None,
            },
        )
        m = row["metrics"]
        a["spend"] += int(m.get("costMicros") or 0) / 1e6
        a["clicks"] += int(m.get("clicks") or 0)
        a["impr"] += int(m.get("impressions") or 0)
        a["conv"] += float(m.get("conversions") or 0)
        if m.get("searchImpressionShare") is not None:
            a["is"] = float(m["searchImpressionShare"])
        if m.get("searchBudgetLostImpressionShare") is not None:
            a["lost_b"] = float(m["searchBudgetLostImpressionShare"])
    for a in gads.values():
        a["spend"] = round(a["spend"], 2)
        a["conv"] = round(a["conv"], 2)

    q2 = f"""
        SELECT campaign.name, segments.date, metrics.cost_micros, metrics.clicks, metrics.conversions
        FROM campaign
        WHERE campaign.name='EG_S2_SEARCH'
          AND segments.date BETWEEN '{end - datetime.timedelta(days=2)}' AND '{end}'
    """
    daily = []
    for row in gaql(q2).get("results") or []:
        m = row["metrics"]
        daily.append(
            {
                "date": row["segments"]["date"],
                "spend": round(int(m.get("costMicros") or 0) / 1e6, 2),
                "clicks": int(m.get("clicks") or 0),
                "conv": round(float(m.get("conversions") or 0), 2),
            }
        )
    return gads, daily


def main():
    now = datetime.datetime.now(CDMX)
    out = {
        "pulled_at": now.isoformat(timespec="seconds"),
        "sets": pull_sets(),
        "insights": {p: pull_insights(p) for p in ("today", "yesterday", "last_3d", "last_7d")},
        "account": {p: pull_account(p) for p in ("today", "yesterday", "last_7d")},
        "stripe_7d": pull_stripe(now),
        "google": {},
        "google_search_daily": [],
    }
    try:
        gads, daily = pull_google()
        out["google"] = gads
        out["google_search_daily"] = daily
    except Exception as e:
        out["google_error"] = str(e)[:300]
    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {OUT} · {out['pulled_at']}")


if __name__ == "__main__":
    main()
