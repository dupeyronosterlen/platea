# Criterios de jueces — cómo acomodar lo que ya tenemos

> **Leer esto al llegar a `09_XPRIZE/`.** No es el checklist de clics (`ataque-50k.md`); es **qué puntúan** y **en qué archivo / bloque de Devpost va cada pieza**.
> Contrato: [Official Rules §6](https://xprize.devpost.com/rules) · FAQ: [details/faq](https://xprize.devpost.com/details/faq).
> Submit: **16 ago** · Cierre: **17 ago 2026, 1:00 PM PT**. Categoría: **Small Business Services**. Project = **Platea**, no El Gorila.

El $ **no** es la vara. Es evidencia de que el negocio existe. Tres criterios al **mismo peso**. Empate: primero Viability, luego AI-Native, luego Impact. Los jueces **no están obligados a testear**: video + texto + imágenes pueden ser todo el score.

---

## Stage One — pass/fail (si fallas, no hay puntaje)

| Pregunta | Cómo acomodar lo que hay | Si se ve así, sales |
|----------|--------------------------|---------------------|
| ¿El Project es un negocio de IA **nuevo** (post 19 may)? | About + Additional: Platea = agencia. El Gorila = cliente / prueba. Párrafo new vs pre-existing ya está en `devpost-about-platea.md` y `devpost-additional-info.md`. | Devpost sigue **AdPilot**. Pitch = “temporada / boletera / Maps”. |
| ¿Gemini + GCP en algo **desplegado**? | Bot WA Vertex · jobs que razonan con Gemini · PDFs Billing + screenshot observabilidad (`xprize-gcp`). | Solo Meta Ads sin Vertex. Cero invoices. |
| ¿Inglés + video + repo sin secretos? | About EN · video &lt;3 min público · `build_public_repo.sh`. | Solo español. Música de terceros. `.env` en GitHub. |

---

## Stage Two — acomodar el inventario en los 3 tercios

Orden de lectura de un juez (~8 min): **video → About → $ → README público → un log**.

### 1/3 Business Viability — negocio real, no “quién facturó más”

**Letra:** lanzar negocio en el hackathon, usuarios reales, revenue real; miran **el $ de los 90 días** *y* **si el modelo se sostiene**. FAQ: no hay mínimo; mayo $0 no descalifica; más profit **no** sube el score solo.

**Qué tenemos (corte 15 ago)**

| Pieza | Dato | Dónde vive | Dónde pegarlo |
|-------|------|------------|---------------|
| Curva | May $0 → Jun $120 → Jul $1,274 → Ago $1,389 | `expediente/03-finanzas-rendicion.md` | Additional info → Revenue by Month |
| Total arms-length | **$2,783 USD** ($47,810 MXN) | idem + `devpost-additional-info.md` | Total Revenue |
| Usuarios | 61 emails pagadores · 139 boletos · 63 txs | idem | User evidence |
| Related-party | **$24** (QA $10 + amigos $400) | idem | Related-Party **aparte**. No mezclar. |
| Modelo / techo CPA | $350 boletera; kill si se pasa | `00-MODELO-NEGOCIO.md` (no copiar al repo público entero) | Additional: sustainability + 1 frase P&L |
| Fees Stripe | $119 USD | `03-finanzas-rendicion.md` | Total Costs (parcial) |
| Ads | TBD — export Manager | `xprize-gcp` | Marketing spend **aunque duela** |
| GCP | TBD invoices | `xprize-gcp` | Product running + costs |

**Cómo venderlo:** la **curva ×10 jun→jul**, no el TAM. Un cliente (nosotros) = prueba de agencia, no 16 cuentas. Próximo paso = clonar obra 2. No inflar.

**Aún falta para este tercio:** screenshot Stripe totales (no lista emails) · export Ads · invoices GCP · 1 testimonio con consentimiento.

---

### 2/3 AI-Native Operations — **nuestro tercio fuerte** (70% del esfuerzo restante)

**Letra:** la IA está **en producción y ejecuta decisiones clave**.

**Qué tenemos (no inventar 16 agentes live)**

Lo que **corre**: 4 jobs mañana + bot WA Vertex + 1 humano. El roster de 17 es organigrama.

| Decisión que la IA/sistema tomó | Evidencia | Dónde acomodar |
|--------------------------------|-----------|----------------|
| CPA = taquilla Stripe, no pixel | Ag-03 8:00 · `funnel-cable-snapshot.json` · mails | Video 20–40 s + `ai-decisions.md` (por escribir, `xprize-narrativa`) |
| Fuga = checkout, no el anuncio | Ag-06 `funnel.py` 8:05 | Video + About “Challenges” |
| Dayparting PT vs CDMX | `dayparting.py` + jobs pause/resume | Video / 1 screen · no explicar timezone 2 min |
| Bot responde fechas/precios (Vertex) | WF-07 · n8n | Video cliente (sin PII) o demo |
| Humano aprueba lo público | Regla de oro · bitácora | Narrativa 500–1000: human vs AI |

**Dónde va**

| Artefacto | Archivo | Rol |
|-----------|---------|-----|
| Video &lt;3 min | `guion-video-demo.md` → YouTube/Vimeo | **Instrumento principal de los 3 tercios** |
| README público | `README-public.md` → GitHub `platea` | 4 loops, no “16 live” |
| Testing EN | `TESTING.md` (Claude Code, `xprize-repo`) | Juez que sí testeé |
| Logs | `04_Operaciones/reportes/` sanitizados en zip | Product evidence FAQ |
| 5 hechos IA/humano | `ai-decisions.md` (faltante) | Additional + About |

**Prohibido en este tercio:** “16 agentes en producción”. Repo congelado 17 jul sin refresh. Video de la función **sin** pantalla de agente.

---

### 3/3 Category Impact — redefinir, no escala

**Letra:** mover la aguja en Small Business **o** redefiniendo cómo se hace, **o** con adopción a escala. Nosotros **no** tenemos escala (1 obra, 61 buyers). El camino es **redefinir**: pyme cultural sin presupuesto de agencia opera media + funnel + PR + WhatsApp con Gemini.

**Qué tenemos**

| Pieza | Dónde | Cómo acomodar |
|-------|-------|----------------|
| Historia (padre, Kafka, 325 butacas, 1 humano) | `devpost-about-platea.md` Inspiration | Primeras 15 s del video + About |
| Categoría | Additional: `Small Business Services` | Un solo pitch; no Professional Services a la vez |
| Jobs **más allá** del founder | Humberto, coproductor, prensa, taquilla, clientes bot | Bloque 500–1000 palabras (home Devpost) — `xprize-narrativa` |
| Impacto concreto | CPA techo, boletos pagados, bot | Additional “how AI impacts the category” (texto ya escrito) |

**Prohibido:** “16 teatros / LATAM / default de la cultura”. Eso mata credibilidad de Impact.

---

## Mapa Devpost ← archivos (pegar, no reescribir de memoria)

| Campo Devpost | Archivo | Criterio que alimenta |
|---------------|---------|------------------------|
| Project name | `ruta-50k.md` §0b → **Platea: AI Agency That Sells Theater Tickets** | Stage One |
| Elevator | idem | Stage One + Impact |
| About / Inspiration… | `devpost-about-platea.md` | Los tres |
| Additional info (AI, model, $) | `devpost-additional-info.md` | Viability + Impact |
| Números $ (corte) | `expediente/03-finanzas-rendicion.md` | Viability |
| Método Stripe | `evidencia-finanzas/METODO.md` | Verificación |
| Video | `guion-video-demo.md` | Los tres (prioridad AI-Native) |
| Repo | `README-public.md` + `sanitizacion-repo.md` + `build_public_repo.sh` | AI-Native + Stage One |
| Elegibilidad / no DQ | `expediente/02-elegibilidad-y-descalificacion.md` | Stage One |
| Checklist clics 15–17 ago | `ataque-50k.md` + pendientes `#21` | Operación |
| Odds / consolación | `ataque-50k.md` §7 | No es para jueces |

Zip (`xprize-zip`): PDFs GCP, Ads, screens 8am/n8n/cockpit. **Cero** CSV con emails. Después de video + repo + GCP, no antes.

---

## Dónde empujar el score (resto del fin de semana)

| Tercio | Peso | Estado | Empuje |
|--------|------|--------|--------|
| AI-Native | 1/3 | Fuerte si se **ve** | Video + 5 hechos + README honesto |
| Viability | 1/3 | Curva limpia, monto chico | Empaquetar $, related-party, Ads, kill CPA. No perseguir milagro de ocupación. |
| Impact | 1/3 | Historia lista, escala no | Narrativa EN + jobs beyond founder. No TAM. |

**70% del esfuerzo restante → AI-Native.** El $ ya está. Impact se escribe. Viability se pega limpio.

Verificación 18 ago–15 sep: bandeja Dirección, 2 días hábiles (`xprize-juzgar`).
