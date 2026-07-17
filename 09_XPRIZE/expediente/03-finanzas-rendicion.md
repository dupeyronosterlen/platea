# 💰 Rendición de cuentas financiera

> Esto es lo que los jueces piden como evidencia financiera. Se llena **mes a mes**, no al final.
> Periodo del hackathon: **may, jun, jul, ago 2026**.
> Conversión a USD: usar tipo de cambio del cierre de cada mes y **anotar la tasa usada**.

---

## 1. Total Revenue (clientes terceros arms-length)

Revenue de **público real** comprando boletos (no familia/equipo/relaciones previas).

| Mes | Revenue (MXN) | Tipo de cambio | Revenue (USD) | Fuente / evidencia |
|-----|---------------|----------------|---------------|--------------------|
| Mayo 2026 | | | | |
| Junio 2026 | | | | |
| Julio 2026 | | | | |
| Agosto 2026 (hasta el 17) | | | | |
| **TOTAL** | | | | |

> Fuente recomendada: export de Stripe (boletera elgorilateatro.com.mx) cruzado con GA4 `purchase`.
> Guardar el CSV de Stripe como evidencia (ver `04`).

---

## 2. Total Costs (excluyendo marketing)

Costos del periodo **sin** incluir marketing/adquisición (eso va en la sección 3).
Incluir **una frase** de qué cubren.

| Mes | Costos (USD) | Qué cubren |
|-----|--------------|-----------|
| Mayo 2026 | | |
| Junio 2026 | | |
| Julio 2026 | | |
| Agosto 2026 | | |
| **TOTAL** | | |

**Descripción (1 frase):** _Ej.: "Hosting (Cloudflare), uso de Gemini API / Vertex AI, Stripe fees, Resend."_

---

## 3. Marketing & Customer Acquisition Spend

⚠️ **Hay que declararlo aunque sea $0.**

| Mes | Ad spend Meta (USD) | Ad spend Google (USD) | Otro | Total (USD) |
|-----|---------------------|------------------------|------|-------------|
| Mayo 2026 | | | | |
| Junio 2026 | | | | |
| Julio 2026 | | | | |
| Agosto 2026 | | | | |
| **TOTAL** | | | | |

> Referencia de presupuesto: ~$22,500 MXN/mes en paid media (ver `04_Operaciones/presupuesto-activo.md`).
> Fuente: Meta Ads Manager + Google Ads. Guardar screenshots/exports.

---

## 4. Related-Party Revenue (reportado APARTE)

Revenue de **miembros del equipo, familia, entidades relacionadas o relaciones de cliente preexistentes**.
Se reporta separado para que los jueces vean que el negocio sirve a terceros reales.

| Fecha | Comprador (relación) | Monto (USD) | Nota |
|-------|----------------------|-------------|------|
| | | | |

> Si es $0, dejarlo explícito: "Related-Party Revenue: $0".

---

## 5. Resumen ejecutivo (para la submission)

| Métrica | Valor | Estado |
|---------|-------|--------|
| Total Revenue (arms-length) | $___ USD | ⬜ |
| Total Costs (sin marketing) | $___ USD | ⬜ |
| Marketing Spend | $___ USD | ⬜ |
| Related-Party Revenue | $___ USD | ⬜ |
| Margen / unit economics | | ⬜ |

---

## 6. Notas de método (para responder verificación sin contradicciones)

- **Fuente de verdad de ventas:** Stripe (boletera propia). El CPA se mide en boletera, no en ads.
- **Atribución:** una venta cuenta como atribuible cuando se registra `purchase` en GA4 + orden en Stripe.
- **Doble fuente de conversión Ads:** import de GA4 (`COMPRA_Ga4`, primaria) con valor real. Una sola fuente.
- **Tipo de cambio:** documentar la tasa MXN→USD usada por mes (ej. Banxico FIX del último día del mes).
