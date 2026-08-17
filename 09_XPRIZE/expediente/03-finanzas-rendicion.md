# 💰 Rendición de cuentas financiera

> Periodo hackathon: **19 may – 17 ago 2026**. Corte de este archivo: **15 ago 2026**.
> Fuente de ventas: Stripe Live `09_XPRIZE/evidencia-finanzas/unified_payments.csv` (PII, no git).
> Método: `evidencia-finanzas/METODO.md`. Dirección aprueba antes de submit.

---

## 0. Corte 15 ago 2026 — Stripe reconciliado

65 cargos `Paid` + 20 `Refunded` en el CSV (136 filas crudas; el resto Failed / incompleto).
En la ventana del concurso, neto cobrado **$48,220 MXN** antes de clasificar related-party.

Related-party duro (founder QA + amigos de producción): **$410 MXN**.
Arms-length (público pagando en checkout): **$47,810 MXN**.

El estimado del 17 jul (41×$350 ≈ $823 USD) **queda invalidado**. Era asientos de KV, no pagos.

---

## 1. Total Revenue (terceros arms-length)

Pagos Stripe netos **menos** founder/QA y cupón “Amigos de producción”.

| Mes | Revenue (MXN) | Tipo de cambio | Revenue (USD) | Fuente |
|-----|---------------|----------------|---------------|--------|
| Mayo 2026 (desde 19) | 0 | — | **0.00** | Stripe: 0 Paid |
| Junio 2026 | 2,100.00 | 17.468 (cierre 30 jun) | **120.22** | 3 pagos preventa $700×2 boletos |
| Julio 2026 | 22,070.00 | 17.3288 Banxico FIX 31 jul | **1,273.60** | 31 pagos |
| Agosto 2026 (al 15) | 23,640.00 | 17.0218 Banxico FIX 14 ago | **1,388.81** | 29 pagos |
| **TOTAL** | **47,810.00** | | **2,782.63** | |

Transacciones arms-length: **63**. Boletos en line-items (neto > 0, no related): **139**.
Compradores únicos (email, neto > 0, no related): **61**.

Nota (no restado): 2 emails de la lista S1 recompraron en S2 por **$2,145 MXN (~$124 USD)**. No son familia. Si Dirección quiere aplicar el FAQ “pre-existing customers” al pie de la letra, restar Julio −$1,273.60 + $1,149.82 y Total → **~$2,659 USD**. Recomendación: **dejarlos en el Total** y decirlo en Explain.

---

## 2. Total Costs (excluyendo marketing)

Aún incompleto (falta Vertex/Cloudflare/Resend y costos de función). Lo que **sí** sale de Stripe:

| Mes | Stripe fees (MXN) | USD | Qué cubren |
|-----|-------------------|-----|------------|
| Mayo | 0 | 0 | — |
| Junio | 149.40 | 8.55 | Comisión Stripe (incluye intentos QA reembolsados) |
| Julio | 923.47 | 53.29 | Comisión Stripe |
| Agosto (al 15) | 976.44 | 57.36 | Comisión Stripe |
| **Subtotal fees** | **2,049.31** | **119.20** | |

**Descripción (1 frase):** Stripe processing fees on ticket checkout; Google Cloud Vertex/Gemini, Cloudflare Workers, and Resend to be added from invoices before submit.

Renta/producción por función: **no** está en este CSV. Si Devpost pide P&L completo, Dirección suma del Excel de reparto (fuera de este repo).

---

## 3. Marketing & Customer Acquisition Spend

⚠️ Obligatorio aunque sea $0. **Aún no hay export Meta/Google en USD.** No inventar.

| Mes | Ad spend Meta (USD) | Ad spend Google (USD) | Otro | Total (USD) |
|-----|---------------------|------------------------|------|-------------|
| Mayo 2026 | TBD | TBD | 0 | TBD |
| Junio 2026 | TBD | TBD | 0 | TBD |
| Julio 2026 | TBD | TBD | 0 | TBD |
| Agosto 2026 | TBD | TBD | 0 | TBD |
| **TOTAL** | | | | TBD |

Fuente: Ads Manager exports × mismas tasas FX. Ag-03 tiene gasto diario en MXN; falta corte del periodo.

---

## 4. Related-Party Revenue (APARTE)

| Fecha | Relación | MXN neto | USD | Nota |
|-------|----------|----------|-----|------|
| 7 jul 2026 | Founder QA (PRUEBA99) | 10.00 | 0.58 | No se reembolsó |
| 1 ago 2026 | Cupón amigos de producción | 400.00 | 23.50 | 2 boletos |
| jun–ago | Founder QA (resto) | 0.00 | 0.00 | Reembolsado (neto 0) |
| **TOTAL** | | **410.00** | **24.08** | |

No incluir en Total Revenue.

---

## 5. Resumen ejecutivo (submission)

| Métrica | Valor | Estado |
|---------|-------|--------|
| Total Revenue (arms-length) | **$2,782.63 USD** | ✅ Stripe 15 ago |
| Total Costs (sin marketing) | $119.20 fees + cloud TBD | 🟡 |
| Marketing Spend | TBD Ads Manager | ⬜ |
| Related-Party Revenue | **$24.08 USD** | ✅ |
| Paying users (únicos, no related) | **61** | ✅ |
| Tickets paid (no related) | **139** | ✅ |

Pegar en Devpost (enteros):

```
Total Revenue: 2783
Revenue by Month: May: $0, June: $120, July: $1274, August: $1389
Related-Party Revenue: 24
```

---

## 6. Notas de método (verificación)

- **Fuente de verdad de ventas:** Stripe Paid neto. KV/ocupación ≠ revenue.
- **Related-party:** founder/QA + amigos de producción. Familia del actor sin cargo Stripe en este corte.
- **S1 recompras:** 2 terceros, ~$124 USD, incluidos en Total salvo instrucción de Dirección.
- **FX:** Banxico FIX 31 jul y 14 ago; junio cierre Frankfurter 17.468 (anotar en Explain).
- **Agosto** se actualiza si hay más Paid antes del 17 ago 1:00 PM PT.
