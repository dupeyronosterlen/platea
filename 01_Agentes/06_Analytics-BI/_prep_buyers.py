#!/usr/bin/env python3
"""Prepara y MIDE (sin exponer PII) la lista de compradores para Customer Match.
Solo imprime estadísticas agregadas — ningún dato personal a stdout."""
import csv, re, hashlib
from pathlib import Path

BASE = Path("/Volumes/La Mancha/Elgorila/_PARA-AGENCIA")
BUYERS = BASE / "privado" / "BUYERS FINAL.csv"
LEADS = BASE / "07_Datos" / "leads (1).csv"


def norm_email(e):
    e = (e or "").strip().lower()
    return e if re.match(r"^[^@]+@[^@]+\.[^@]+$", e) else ""


def norm_phone(p):
    if not p:
        return ""
    d = re.sub(r"\D", "", p)
    if not d:
        return ""
    # MX: 10 dígitos -> +52; ya con 52 -> dejar; quitar 0/1 inicial raro
    if len(d) == 10:
        d = "52" + d
    elif len(d) == 12 and d.startswith("52"):
        pass
    elif len(d) == 13 and d.startswith("521"):
        d = "52" + d[3:]
    return "+" + d if 11 <= len(d) <= 13 else ""


# ── BUYERS (boletera) ──
buyers = {}
with open(BUYERS, encoding="utf-8-sig", newline="") as f:
    for row in csv.DictReader(f):
        em = norm_email(row.get("Email"))
        if not em:
            continue
        rec = buyers.setdefault(em, {"phone": "", "fn": "", "ln": "", "zip": ""})
        ph = norm_phone(row.get("Mobile number"))
        if ph and not rec["phone"]:
            rec["phone"] = ph
        if row.get("First Name") and not rec["fn"]:
            rec["fn"] = row["First Name"].strip().lower()
        if row.get("Last Name") and not rec["ln"]:
            rec["ln"] = row["Last Name"].strip().lower()
        if row.get("Postcode / Zip") and not rec["zip"]:
            rec["zip"] = re.sub(r"\s", "", row["Postcode / Zip"])

n = len(buyers)
with_phone = sum(1 for v in buyers.values() if v["phone"])
with_name = sum(1 for v in buyers.values() if v["fn"] and v["ln"])
with_zip = sum(1 for v in buyers.values() if v["zip"])
print("BUYERS FINAL.csv (boletera S1):")
print(f"  · compradores únicos por email: {n}")
print(f"  · con teléfono móvil:           {with_phone}  ({100*with_phone//max(n,1)}%)")
print(f"  · con nombre+apellido:          {with_name}  ({100*with_name//max(n,1)}%)")
print(f"  · con código postal:            {with_zip}  ({100*with_zip//max(n,1)}%)")
print(f"  → identificadores para match: {n} emails + {with_phone} teléfonos + {with_name} nombres")

# ── LEADS (Messenger) ──
le = 0; le_em = 0; le_ph = 0; le_wa = 0
with open(LEADS, encoding="utf-8-sig", newline="") as f:
    for row in csv.DictReader(f):
        le += 1
        if norm_email(row.get("Correo electrónico")):
            le_em += 1
        if norm_phone(row.get("Teléfono")):
            le_ph += 1
        if norm_phone(row.get("Número de WhatsApp")):
            le_wa += 1
print("\nleads (1).csv (Messenger/WhatsApp):")
print(f"  · leads totales: {le}")
print(f"  · con email: {le_em} · con teléfono: {le_ph} · con WhatsApp: {le_wa}")
print("  → la mayoría sin PII subible → mejor usarlos como Custom Audience NATIVA de Meta (mensajería)")

print("\n(El upload real hashea SHA-256 cada identificador; aquí no se imprime ningún dato personal.)")
