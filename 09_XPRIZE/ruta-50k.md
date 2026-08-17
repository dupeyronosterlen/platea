# Ruta $50k — Build with Gemini XPRIZE
> Objetivo: **maximizar chance de premio de $50,000 USD** (Runner-up ×15 **o** Category prize ×5).
> No apuntamos al $500k. Apuntamos a estar en el **top ~20–30** de submissions creíbles.
> Deadline submission: **17 ago 2026, 1:00 PM PT** · Finales LA: 25 sep (solo top 5 grand).
> Dueño: Ag-15 coordina · Dirección aprueba lo público · Actualizado 16 jul 2026 noche.

---

## 0. Apuesta (honesta)

| Premio | Estrategia |
|--------|------------|
| Runner-up $50k | **Plan A** — mejor score global en Viability + AI-Native + Impact (sin necesitar ser el que más factura) |
| Category $50k | **Plan B** — categoría **Small Business Services**; si el prize es “highest-grossing”, solo gana si nuestro USD arms-length es alto *dentro* de esa categoría (menos controlable) |
| Grand / top 5 | No invertir energía extra — si llega, es bonus |

**Devpost (draft vivo):**  
https://devpost.com/submit-to/29541-build-with-gemini-xprize/manage/submissions/1039169-adpilot-ai-agents-for-meta-google-ads/project_details/edit  
- Nombre registrado: *AdPilot: AI Agents for Meta & Google Ads* (placeholder viejo).  
- **Acción:** renombrar a **Platea** en Project overview (ver §0b). AdPilot = capa Media Buyer, no el producto.

**Hipótesis de victoria $50k:**  
paquete de evidencia **imposible de ignorar** (IA en producción + revenue real + video claro en inglés) mientras el 80% de los ~20k inscritos no termina submission o manda demos sin negocio.

Meta interna de probabilidad: pasar de ~5–10% a **~15–25%** si ejecutamos esta ruta al 100%.

### 0b. Texto para pegar YA en Devpost (Project overview)

**Project name:**
```
Platea: AI Agency That Sells Theater Tickets
```

**Elevator pitch (≤200 chars):**
```
Gemini agents run a real marketing agency for live theater: Meta/Google ads, CPA at the box office, WhatsApp bot. One human approves. Proof: El Gorila season in Mexico City.
```

Luego: **Save & continue** → Project details (repo, Built With, About). Thumbnail: cartel/foto El Gorila (no el placeholder azul).

---

## 1. Categoría (decidir esta semana)

**Elegir: Small Business Services**  
Argumento en 1 línea (EN): *“AI-operated marketing agency that sells tickets for independent theaters — real CPA, real box office.”*

Alternativa solo si Dirección insiste: *Professional Services Access* (agencia = servicio profesional).  
No mezclar categorías en el pitch; una sola historia.

⬜ Dirección confirma categoría: _______________

---

## 2. Tres frentes que mueven el score (igual peso)

### A — Business Viability (revenue limpio)
| # | Acción | Quién | Deadline | Done |
|---|--------|-------|----------|------|
| A1 | Llenar tablas `expediente/03-finanzas-rendicion.md` may–ago (USD + FX anotado) | Ag-06 + Dirección | **25 jul** (parcial) · **10 ago** (casi final) | ⬜ |
| A2 | Export Stripe (CSV) + screenshots dashboard · carpeta `09_XPRIZE/evidencia-finanzas/` | Dirección / Ag-13 | 15 ago CSV | ✅ números; falta screenshot dashboard |
| A3 | Separar **Related-Party** (familia/equipo/pruebas) del revenue arms-length | Ag-06 | 25 jul | ⬜ |
| A4 | Marketing spend Meta+Google declarado (aunque duela) | Ag-03 | 25 jul | ⬜ |
| A5 | 1 frase P&L costs (Cloudflare, Vertex, Resend, Stripe fees) | Ag-15 | 1 ago | ⬜ |
| A6 | Empujar venta real 25 jul→17 ago (la submission necesita historia de temporada viva) | Dirección + Ag-03 | continuo | ⬜ |

**Regla:** número chico y **limpio** > número inflado. Verificación Hacker Fund es seria.

### B — AI-Native Operations (nuestro fuerte — maximizar)
| # | Acción | Quién | Deadline | Done |
|---|--------|-------|----------|------|
| B1 | Screenshots: emails 8:00/8:05 varios días · Ads · Stripe · n8n WF-07 · cockpit | Dirección 5 min/día o Ag-15 | **cada día hasta 10 ago** | ⬜ |
| B2 | Empaquetar logs: `04_Operaciones/logs/` + reportes Ag-03/06/12 + `session_decisions` flushes | Ag-15 | 5 ago | ⬜ |
| B3 | Lista “AI decides / human approves” (1 página EN) — CPA pause, funnel alert, bot routing, PR send | Ag-15 | 1 ago | ⬜ |
| B4 | Repo público `platea` fresco + acceso a `testing@devpost.com` y `judging@hacker.fund` | Ag-15 | 5 ago | ⬜ |
| B5 | Demo path: juez puede ver bot/reportes sin secretos (README-public + instructions EN) | Ag-13/15 | 10 ago | ⬜ |

### C — Category Impact (historia SMB teatral)
| # | Acción | Quién | Deadline | Done |
|---|--------|-------|----------|------|
| C1 | Narrativa 500–1000 palabras EN: problema (teatro ind. sin agencia) → Platea → jobs/impacto | Ag-02 + Dirección | **1 ago** | ⬜ |
| C2 | Párrafo “New Project”: Platea = nuevo post-19 may; boletera = cliente preexistente | Ag-15 | 1 ago | ⬜ |
| C3 | 1 case study cuantificado: CPA $122 · fuga checkout · X boletos S2 · spend | Ag-06 | 5 ago | ⬜ |
| C4 | (Opcional) 1 testimonio de comprador o medio — sin inventar | Dirección | 10 ago | ⬜ |

---

## 3. Video (< 3 min) — el que más mueve runner-up

Guion base: `guion-video-demo.md`. Versión **$50k** = enfatizar **decisiones de IA en vivo**, no estética.

| # | Acción | Quién | Deadline | Done |
|---|--------|-------|----------|------|
| V1 | Capturar 18 jul (prensa) + 25 jul (estreno) — celular OK | Dirección / Ag-08 | 18 y 25 jul | ⬜ |
| V2 | Screen recordings: email auto · funnel.py · Ads · boletera · bot WA | Ag-08/15 | 28 jul | ⬜ |
| V3 | Dirección a cámara: 3 frases EN (o VO EN + subtítulos ES) | Dirección | 1 ago | ⬜ |
| V4 | Corte final <3 min · YouTube público · sin música con copyright | Ag-08 | **8 ago** | ⬜ |
| V5 | Dirección aprueba cut | Dirección | 9 ago | ⬜ |

Sin video = casi cero chance de $50k. Con video mediocre pero real > video lindo vacío.

---

## 4. Submission Devpost (checklist ejecutable)

**Pegar Additional info (jueces):** → [`devpost-additional-info.md`](./devpost-additional-info.md)  
**Pegar About / overview:** → [`devpost-about-platea.md`](./devpost-about-platea.md)  
Si en ago cambian ventas/números: editar **solo** la tabla FINANZAS en `devpost-additional-info.md` + `expediente/03-finanzas-rendicion.md`, luego re-pegar en Devpost.

Tomado de `expediente/01-checklist-submission.md` — solo lo que falta para $50k:

| # | Item | Deadline | Done |
|---|------|----------|------|
| S1 | Categoría confirmada + Corporate ID / individuo / equipo (Dirección) | 25 jul | 🟡 Individual + Small Business Services (draft 17 jul) |
| S2 | Representante autorizado por escrito | 25 jul | ⬜ |
| S3 | Repo URL + shares a testing@ / judging@ | 5 ago | ⬜ |
| S4 | Descripción EN + instrucciones de prueba EN | 10 ago | 🟡 About listo; Additional info listo (textos) |
| S5 | Video URL | 10 ago | ⬜ |
| S6 | Revenue + costs + marketing + related-party uploads | 12 ago | ⬜ placeholders en `devpost-additional-info.md` |
| S7 | Customer evidence (lista compradores anonymizable / consent) | 12 ago | ⬜ |
| S8 | **Submit final** (no tocar después) | **16 ago** (buffer 1 día) | ⬜ |

---

## 5. Calendario condensado

```
17–25 jul   Captura estreno · Stripe/Meta exports · screenshots diarios
25 jul–1 ago  Finanzas parciales · narrativa EN borrador · Dirección decide categoría/entidad
1–8 ago     Video cut · logs empaquetados · repo fresco
8–12 ago    Devpost casi completo · revisión elegibilidad (02)
13–16 ago   Buffer · submit 16 ago
17 ago      Cierre 1pm PT — no más cambios
```

---

## 6. Lo que NO hacemos (para no diluir)

- No pivots de producto “más SaaS” a 3 semanas del close.
- No inventar revenue ni mezclar related-party.
- No gastar semanas en Wikipedia / influencers / features nuevos sin evidencia XPRIZE.
- No tocar boletera en vivo por el hackathon.
- No pelear el $500k en el pitch (el video no diga “we’ll win the grand prize”).

---

## 7. Semáforo semanal (Dirección mira 2 min)

Cada domingo hasta el 16 ago, Ag-15 actualiza una línea aquí:

| Semana | Finanzas | Video | AI evidence | Devpost | Riesgo |
|--------|----------|-------|-------------|---------|--------|
| 20 jul | ⬜ | ⬜ | ⬜ | ⬜ | |
| 27 jul | | | | | |
| 3 ago | | | | | |
| 10 ago | | | | | |
| 16 ago | | | | | SUBMIT |

---

## 8. Las 48 h (hoy 15 ago → cierre **17 ago 1:00 PM PT**)

Hoy es función. Pauta/UTMs no se tocan. XPRIZE tampoco toca boletera.

| # | Quién | Qué | Tiempo |
|---|-------|-----|--------|
| 1 | Dirección | Stripe → Payments → export CSV **19 may–hoy** → `09_XPRIZE/evidencia-finanzas/` + 3 líneas: pruebas/familia/cortesías | 15 min |
| 2 | Dirección | 3 frases a cámara (celular, EN o ES+subs) + 20 s de sala/público si hay función | 20 min |
| 3 | Dirección | Devpost: rename **Platea: AI Agency That Sells Theater Tickets** (hoy dice AdPilot) · categoría Small Business Services · Individual | 10 min |
| 4 | Ag-15 | Pegar About + Additional info (textos ya en `devpost-about-platea.md` / `devpost-additional-info.md`). Números $ solo cuando exista el CSV | esta sesión |
| 5 | Dirección | YouTube unlisted/público del cut &lt;3 min · pegar URL. Sin video casi no hay $50k | hoy/mañana |
| 6 | Dirección | **Submit 16 ago** (buffer). El 17 a la 1pm PT ya no se edita | 16 ago |

Guion: `guion-video-demo.md`. Si no hay cut de 2:45: 90 s reales (problema → CPA taquilla → jobs 8:00 → boletos) gana a un video vacío.

---

## 9. Hipotético “75% de ganar $50k” — qué haría falta (honestidad)

> **Hoy:** ~15–25% si ejecutamos §§1–8 al 100%.  
> **75% no es el plan base.** Es el techo teórico: estar tan por delante del pelotón verificable que casi seguro caes en runner-up **o** category $50k. Con ~20k inscritos y ~20–25 slots de $50k, 75% implica ser **top ~5–10 global**, no “submission completa”.

### Barra hipotética (los tres criterios a la vez)

| Pilar | Plan base ($50k @ ~25%) | Hipotético 75% |
|-------|-------------------------|----------------|
| **Business Viability** | Revenue limpio cientos–bajos miles USD; related-party separado; CPA historia real | **Arms-length ≥ ~$8k–15k USD** en la ventana (o #1–3 de revenue **dentro** de Small Business Services si el category prize es highest-grossing). Stripe impecable. Cero ambigüedad related-party. ≥1 testimonio público verificable. |
| **AI-Native Ops** | Jobs diarios + bot + logs + 1 URL de evidencia | **Prueba jugable para jueces** (demo path sin secretos) + bitácora continua may→ago + Vertex usage visible + lista “AI decided / human approved” con 5+ decisiones reales documentadas. |
| **Category Impact** | Historia SMB teatro clara en EN | Video &lt;3 min **excelente** (IA decidiendo + taquilla + humano en loop) + 1 case study cuantificado (CPA, boletos, spend) + narrativa “agency for indie venues” que un juez recuerde. |

### Ruta numérica (El Gorila como proof) — qué significaría “vender muy bien”

Asumiendo ~$19 USD/boleto preventa (≈$350 MXN @ FIX ~17.4):

| Meta | Boletos arms-length (aprox.) | Revenue USD (aprox.) | Lectura |
|------|------------------------------|----------------------|---------|
| Hoy (17 jul) | ~41 brutos | ~$800 | Draft; falta Stripe |
| Piso competitivo | ~150–250 | ~$3k–5k | Creíble mid-pack |
| Fuerte (empuja a ~35–45%) | ~400–600 | ~$8k–12k | Top decil plausible |
| **Hipotético 75%** | **~700–1,000+** en ventana hackathon **o** 2º producto Platea con retainer de otro teatro | **~$15k+** limpios | Outlier; casi obligatorio + video 9/10 + verificación perfecta |

Gastos: declarar marketing completo (Meta+Google). Margen feo está OK si la historia es “AI mató el CPA malo”. Mentir no.

### Secuencia hasta el 16 ago (si apuntamos al techo)

```
Ahora → 25 jul   Stripe export + related-party · no $0 en Devpost · screens diarios
25 jul → 8 ago   Estreno + empujar ocupación · video cut · demo path jueces
8 → 12 ago       Finanzas finales USD · zip evidencia · testimonio
13 → 16 ago      Relectura elegibilidad (02) · submit buffer · no tocar después
```

### Lo que NO sube a 75% (aunque duela)

- Solo más ads sin ventas Stripe.  
- Inflar related-party en Total Revenue.  
- Pivot a “SaaS genérico” a 3 semanas.  
- Video lindo sin IA viva / sin plata real.

### Decisión de este thread (17 jul)

- Plan oficial: **ruta $50k @ ~25%** (`ruta-50k.md` §§1–8).  
- Techo aspiracional: **esta §9** — solo si la temporada dispara y el paquete de evidencia es impecable.  
- Finanzas: dejar de tratar ventas como $0; usar borrador ~41 boletos / ~$823 y **cerrar con Stripe** (`expediente/03-finanzas-rendicion.md` §0 + `devpost-additional-info.md`).

**Archivos de este cierre:**  
`devpost-additional-info.md` · `devpost-about-platea.md` · `03-finanzas-rendicion.md` · `ruta-50k.md` (este).

---

## 10. Paquete perfecto + 2º cliente (qué planchar ahora vs después)

### Sí: “vender a otros” = Platea cobra a **otra obra**
No es El Gorila revendiendo boletos ajenos. Es: **otro productor** contrata Platea (retainer y/o % del ad spend) para que los agentes vendan *sus* butacas. El Gorila sigue siendo Cliente 0 / laboratorio.

### Orden correcto (no invertir)

```
1) Gorila 100% operacional + evidencia XPRIZE impecable
2) Plantilla de réplica lista (export de insumos)
3) Primer cliente externo real (contrato + plata)
```

Meter cliente 2 **antes** de que Gorila esté estable = diluir el prize y romper ops.  
Excepción única pre-17 ago: si llega un productor con **retainer pagado ya** y fechas firmadas — eso sí trepa Business Viability; si no, no cazar.

### A — Planchado YA (apalanca el paquete XPRIZE sin segundo teatro)

| # | Qué | Dueño | Para cuándo |
|---|-----|-------|-------------|
| 1 | Stripe export + related-party + Devpost $ reales | Dirección + Ag-06 | esta semana |
| 2 | Screens diarios (email 8am, Ads, n8n, boletera) | Dirección 2 min / Ag-15 | continuo → 10 ago |
| 3 | Lista EN “AI decided / human approved” (5+ hechos) | Ag-15 | 1 ago |
| 4 | Demo path jueces (README-public + qué pueden ver sin secretos) | Ag-13/15 | 10 ago |
| 5 | Video &lt;3 min | Dirección captura + Ag-08 | 8 ago |
| 6 | Zip evidencia + shares testing@/judging@ | Ag-15 | 12 ago |
| 7 | 1 testimonio público (comprador o medio) | Dirección | 10 ago |

Eso es el **paquete perfecto del proof**. No requiere obra 2.

### B — Lanzando / endureciendo ops (Gorila → “100% operacional”)

| Señal de “listo para clonar” | Estado hoy |
|------------------------------|------------|
| CPA loop Meta+Google + boletera estable | 🟡 vivo, tokens/ops frágiles a veces |
| Jobs diarios sin babysitting | 🟢 launchd |
| Bot WA clientes confiable | 🟡 OTP / Gemini CEO pendientes menores |
| Plaza + identidad como única fuente de fechas/precios | 🟢 regla venue-agnostic |
| Onboarding B2B documentado | 🟢 ya existe (`06_Workflows/onboarding-cliente-b2b.md` + `08_Plantillas/onboarding-cliente-boceto.md`) — **Fase 2, no activo** |

### C — Export de agencia para otra obra (después de B)

Sí: un **pack de réplica**, no reescribir Platea. Capas:

1. **Insumos del cliente** (carpeta `03_Producciones/<obra>/`, no `09_Clientes/` — esa es la capa
   comercial): `identidad.md`, `plazas/plaza-activa.md`, `produccion.yaml`, assets, precios, accesos
   ads/boletera — el cuestionario boceto ya lista los 7 datos mínimos.
2. **Brain**: copiar playbooks; apuntar agentes a `produccion.yaml` de esa obra vía parámetro
   `--produccion <slug>` (no hardcodear `el-gorila` en Engine).
3. **Engine**: nuevo `TEATRO_ID` / pixel / Ad Account del cliente; **no** mezclar KV ni Stripe del Gorila.  
4. **Contrato**: fee (15–20% ad spend o fijo) + temporada completa — ya en onboarding B2B.

Hasta que B esté verde: solo **pulir** esos docs (1 página EN “How Platea onboards a new show” para jueces). No construir multi-tenant completo pre-submit.

### D — Atajo de revenue sin multi-tenant

Si hace falta plata pre-17 ago sin cliente 2: **más boletos Gorila arms-length** (y canales tipo Teatrando con remisión limpia). Eso es más barato en foco que clonar la agencia a medias.


