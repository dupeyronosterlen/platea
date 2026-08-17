# Devpost — Additional info (jueces / organizadores)
> **Dónde buscar esto el 17 ago 2026:** este archivo.  
> **Overview / About:** `devpost-about-platea.md` · **Ruta $50k:** `ruta-50k.md` · **Finanzas numéricas:** `expediente/03-finanzas-rendicion.md`  
> Draft vivo: submission id `1039169` en Devpost (Build with Gemini).  
> Guardado: **17 jul 2026** · Actualizar números cuando haya export Stripe/Ads (meta: temporada vendiendo bien → maximizar score Business Viability hacia premio **$50k**).

---

## Estado del draft (17 jul)

| Bloque | Estado |
|--------|--------|
| Project overview (name, pitch, About, Built with, Try it out) | Pegado / en curso — ver `devpost-about-platea.md` |
| **Additional info (este archivo)** | Textos listos · **números $ = placeholders** hasta Stripe |
| Video / screens / zip evidencia | Pendiente |
| Submit final | **NO** antes del buffer **16 ago** (cierre 17 ago 1pm PT) |

**Protocolo si se vende bien (jul–ago):**  
1. Export Stripe (pagos confirmados may 19 → ago 17) + Meta/Google spend.  
2. Llenar `expediente/03-finanzas-rendicion.md` (MXN→USD con Banxico FIX por mes).  
3. Separar **Related-Party** (familia/equipo/pruebas Dirección).  
4. Sustituir solo las celdas **FINANZAS** abajo + users/paying — **no reescribir** la narrativa salvo que cambie el modelo.  
5. Actualizar URL de evidencia si hay log/screenshot mejor en el repo.  
6. Recalcular semáforo en `ruta-50k.md` §7.

---

## Campos fijos (pegar tal cual)

### Upload a File
Vacío hasta zip ≤35 MB (`09_XPRIZE/evidencia-finanzas/` + screens). Nombre sugerido: `platea-xprize-evidence-YYYYMMDD.zip`.

### What date did you start this project? (MM-DD-YY)
```
05-19-26
```

### Submitter type
```
Individual
```
Organization name / EIN → vacío (si Dirección cambia a org/equipo: anotar aquí la fecha y el EIN).

### Country of residence
```
Mexico
```

### Which Category are you submitting into?
```
Small Business Services
```

---

## Respuestas de texto (inglés — pegar)

### Explain how your project uses AI to impact the world, specifically in the category you have chosen.
```
Platea uses Gemini agents to run marketing for independent live theaters that cannot afford a traditional agency. In our category (Small Business Services), the impact is concrete: a 325-seat Mexico City production sells tickets while AI monitors Meta/Google spend against real box-office CPA, diagnoses funnel leaks, drafts PR, and answers customers on WhatsApp—with a human approving anything public. The goal is not another ads dashboard; it is giving a small cultural business the operating capacity of a full marketing team so seats fill without burning cash.
```

### Explain the underlying business model of your submission.
```
Platea is an AI-operated marketing agency for live theater. The proof client is El Gorila Season 2 in Mexico City. Revenue during the hackathon is ticket sales sold through our own Stripe checkout (preventa was $350 MXN until 25 Jul opening; regular **$400 MXN**; credential / INAPAM / student / teacher **$280 MXN**; couple code ESPEJO $600 MXN for two). Platea’s product is the agency layer: agents that buy media, measure true CPA at the box office, run CRM/PR workflows, and keep daily ops running. Near-term model: operate one production end-to-end. Medium-term: package the same agent stack as a service for other independent shows (retainer + performance against ticket CPA).
```

### How will you sustain business operations in the future?
```
Sustain from ticket margin on live seasons plus, later, retainers from additional productions. Keep fixed costs low: one human founder, Gemini/Vertex for agent reasoning, Cloudflare Workers + Stripe for ticketing, scheduled Python jobs for monitoring. Kill or pause paid media when box-office CPA exceeds a hard ceiling ($350 MXN). Reinvest only when CPA is healthy. Expand by cloning the agency playbook to new titles—not by hiring a large team first.
```

### Which AI tools have you leveraged while working on this project?
```
Google Gemini via Vertex AI (Google Cloud) for agent reasoning (CEO/assistant paths, PR drafting, analysis); Gemini API calls in production WhatsApp workflows (n8n); supporting tooling for creatives and knowledge (e.g. Graphify over the agency repo). Meta Marketing API and Google Ads API for spend truth; not LLMs themselves.
```

### Explain how your business model shared above is sustainable and viable.
```
(1) Five-year goal: become the default AI marketing ops layer for independent Spanish-language theater and live culture in Mexico/LATAM. Target: multi-production ARR from retainers + performance fees; capture a meaningful share of small productions that today under-market or overpay agencies. TAM is fragmented cultural SMBs that sell tickets locally; we start with one flagship title and expand city by city.
(2) Path to profitability: unit economics are ticket price minus venue/production share minus ad CPA. Profitability improves when CPA stays ≤ ~$350 MXN and occupancy rises across the season. Near term we run lean (one operator + cloud APIs). We expect contribution-positive seasons as paid media stays under kill rules and organic/PR channels mature; full P&L hardens with full Stripe exports through August.
(3) Why achievable: during this hackathon Platea is already live—daily CPA/occupancy/funnel jobs, WhatsApp bot in production, press send path, and real ticket sales on our Stripe boletera for El Gorila S2. First measured Meta window showed CPA ~$122 MXN vs a $350 ceiling. Hypothesis: truthful box-office feedback loops beat vanity dashboards for small venues.
```
> **Si se vende muy bien:** en el punto (3) añadir 1–2 frases con boletos/USD arms-length y CPA promedio del periodo (cifras de `03-finanzas-rendicion.md`). No inventar.

### Please explain how your business operates with AI.
```
Sixteen role-based agents (CEO, Media Buyer, Analytics, PR, Boletera sync, etc.) share playbooks and tools. Scheduled jobs pull ad spend and box-office inventory, compute CPA, and alert when thresholds break. A WhatsApp bot uses Gemini (Vertex) to answer customer questions and escalate to the founder. PR drafts are AI-written and only sent after human “go.” Creatives and ops docs are produced with AI under brand rules. Humans approve irreversible/public actions; AI runs monitoring, drafting, routing, and routine decisions inside guardrails.
```

### Please explain the extent to which AI is live in production and executes key decisions.
```
AI is live every day: launchd jobs run Media Buyer CPA checks, boletera occupancy, and funnel reports; n8n WhatsApp workflows call Gemini/Vertex for real customers; agents have paused/escalated media logic against CPA kill rules; funnel analysis identified checkout conversion as the leak from live APIs. Key irreversible decisions (publish posts, send press, major budget jumps) require founder approval. Routine operational decisions (alert, route, draft, diagnose, recommend pause) execute continuously in production.
```

### Please explain which product from Google Cloud you used during the hackathon and how.
```
Google Cloud Vertex AI — Gemini models for agent reasoning in production (WhatsApp CEO/assistant paths migrated to Vertex for hackathon credits) and for analysis/drafting across the agency. GCP project: agencia-mkt-ia (us-central1). We also use Gemini API requirements via Vertex-hosted Gemini calls rather than non-Google LLMs for core agent turns.
```

### If your project uses an LLM… Gemini API…
```
Primary LLM: Google Gemini (via Vertex AI / Gemini API). Used for: (1) WhatsApp bot reasoning and replies in n8n, (2) CEO/strategy assistant path for the founder, (3) PR pitch drafting, (4) analytical summaries tied to live marketing/ops data. Non-LLM systems (Meta/Google Ads APIs, Stripe, Cloudflare Workers) provide tools and ground truth; Gemini is the reasoning layer that turns that data into actions and messages. We do not rely on non-Gemini LLMs for required agent calls.
```

### URL to your GitHub repo…
```
https://github.com/dupeyronosterlen/platea
```
Confirm shared with `testing@devpost.com` and `judging@hacker.fund` (o repo público con licencia).

### Provide a URL to a file in your repository that shows evidence…
```
https://github.com/dupeyronosterlen/platea/blob/main/09_XPRIZE/evidencia.md
```
> Sustituir cuando exista un log/screenshot más fuerte en el repo público.

### Are you using any pre-existing business resources (before May 19, 2026)?
```
Yes. Pre-existing (declared honestly): (1) the show El Gorila and its brand/assets; (2) the venue relationship for the Mexico City season; (3) the ticketing website and Stripe checkout infrastructure; (4) Season 1 buyer list / CRM seed used for remarketing; (5) historical campaign learnings from prior seasons. How applied: El Gorila is the customer and proof environment for Platea—the NEW Project built after May 19, 2026 (AI agent roster, CPA-as-truth loop, funnel monitor, decision logbook, Vertex-powered bot, PR send path, autonomous morning jobs). The show is not the Project; Platea is.
```

---

## FINANZAS — corte Stripe 15 ago 2026

> Fuente: `expediente/03-finanzas-rendicion.md`. CSV en `evidencia-finanzas/` (PII, no git).
> El $823 del 17 jul era KV×$350 — **no usar**.

| Campo Devpost | Pegar (15 ago) |
|---------------|----------------|
| Total Revenue (USD, arms-length) | **2783** |
| Revenue by Month | May: $0, June: $120, July: $1274, August: $1389 |
| Related-Party Revenue | **24** |
| Total Expenses / COGS | Stripe fees **$119** + cloud/producción TBD |
| Total marketing / acquisition | TBD (export Ads Manager) |
| Users acquired / paying users | **61** unique paying emails (not team) |
| ≤40% un solo cliente | sí (boletos, muchos compradores) |

**Pegar en Devpost:**

```
Total Revenue: 2783
Revenue by Month: May: $0, June: $120, July: $1274, August: $1389
Related-Party Revenue: 24
```

### Explain the revenue shared above
```
Revenue is box-office ticket sales paid through our Stripe checkout on elgorilateatro.com.mx during the hackathon (19 May–15 Aug 2026). Figures are net collected (Paid minus refunds) from the Stripe Payments export, converted to USD with Banxico FIX 31 Jul 17.3288 and 14 Aug 17.0218, and 30 Jun market close 17.468. May: $0. June: $2,100 MXN preventa. July: $22,070 MXN. August to date: $23,640 MXN. Total arms-length: $47,810 MXN / $2,783 USD. 61 unique paying customers; 139 tickets. Related-party ($24 USD) is excluded here: founder QA leftover and a production-friends coupon. Two Season-1 patrons bought again (~$124 USD); they are third parties and included in Total Revenue. Ticket prices in the period: preventa $350, then general $400 / credential $280 / couple ESPEJO $600. One-time payments, not subscriptions.
```
> Al submit: si hay más Paid después del 15 ago, re-correr el CSV y sustituir agosto + total.

### COGS (1 sentence)
```
Direct costs tied to delivering the show and checkout: venue/coproducer share and production labor per performance (from the production ledger), plus Stripe processing fees of $119 USD on ticket sales in this export.
```

### Marketing (1 sentence + explain)
```
Paid acquisition on Meta Ads and Google Ads to drive ticket purchases for El Gorila Season 2, monitored against box-office CPA.
```
```
Marketing spend is Meta + Google ad delivery during the hackathon. Exact USD will be taken from Ads Manager exports converted with the same FX rates by month. Spend is paused or constrained when measured box-office CPA exceeds kill thresholds. Not yet filled from this Stripe file.
```

### Additional expenses (1 sentence)
```
Cloud and ops: Cloudflare Workers hosting, Google Cloud Vertex AI / Gemini usage, Resend email, and n8n automation infrastructure (invoices to attach; Stripe fees listed under COGS).
```

### Level of learning
Elegir en el dropdown la opción más alta disponible (Advanced / Expert / Significant — según UI).

---

## Checklist “ataque $50k” ligado a este formulario

Objetivo interno: maximizar chance del premio **$50k** (runner-up o Category Small Business Services). Odds honestas base ~15–25% si se ejecuta `ruta-50k.md` al 100%; **si la temporada vende fuerte + video + finanzas limpias + evidencia AI continua**, empujar hacia el techo de ese rango (no confundir con “80% de ganar”).

| # | Acción | Deadline | Done |
|---|--------|----------|------|
| 1 | Pegar textos de este archivo en Devpost Additional info | 17 jul ✅ borrador | 🟡 |
| 2 | Carpeta + export Stripe → actualizar tabla FINANZAS | **15 ago** CSV reconciliado | ✅ |
| 3 | Related-party separado | 15 ago: $24 USD (QA + amigos prod.) | ✅ |
| 4 | Zip evidencia + URL archivo repo | 10 ago | ⬜ |
| 5 | Video &lt;3 min + About limpio | 10 ago | ⬜ |
| 6 | Shares testing@ / judging@ | 5 ago | ⬜ |
| 7 | Submit buffer | **16 ago** | ⬜ |

---

*Dueño: Ag-15 · Dirección aprueba números antes de submit final.*
