# Ataque $50k — análisis 15 ago + checklist

> Cierre Devpost: **17 ago 2026, 1:00 PM PT** (CDMX = 3:00 PM).  
> Prize target: **$50k** (15 runner-ups **o** 1 category Small Business Services). Máximo **un** premio.  
> Stripe corte 15 ago: arms-length **$2,783 USD** · related **$24** · 61 pagadores · 139 boletos.  
> Más boletos hasta el domingo: re-export Stripe y sustituir agosto. No esperar un milagro de ocupación.

---

## 1. Cómo se gana de verdad (reglas vivas)

Fuente: [Official Rules](https://xprize.devpost.com/rules) + [FAQ](https://xprize.devpost.com/details/faq). ~**25,858** inscritos.

**Stage One (pass/fail):** ¿cabe el tema? ¿usa GCP + Gemini en algo desplegado?  
Si el Project se lee como “temporada de El Gorila” o el repo es un caos con secretos → **fuera**, no “puntaje bajo”.

Mapa criterio → archivo (cómo acomodar el inventario): [`criterios-jueces.md`](criterios-jueces.md).

**Stage Two — tres criterios al mismo peso:**

| Criterio | Qué miran | Nuestra posición real |
|----------|-----------|------------------------|
| **Business Viability** | Negocio nuevo post-19 may, usuarios, revenue arms-length, P&L, sostenibilidad | Débil en monto ($2.8k). Fuerte en **limpieza** (Stripe, related-party). El dinero es de **boletos del cliente**, no retainer de agencia. |
| **AI-Native Operations** | IA **viva** ejecutando decisiones, no un demo | **Nuestro mejor pilar** si se empaqueta. Jobs 8:00/8:03/8:05, bot Vertex, CPA vs taquilla, bitácora. |
| **Category Impact** | Small Business Services: herramienta para un negocio de verdad que no puede pagar agencia | Historia memorable (padre, Kafka, 325 butacas, 1 humano). Escala = 1 cliente (nosotros). No inventar obra 2. |

**Category $50k vs runner-up $50k.** Runner-up = top scores globales (peleas con SaaS de más revenue). Category = un solo ganador **dentro** de Small Business Services. Si esa canasta está llena de dashboards y nosotros somos el único “agencia SMB con Stripe + Gemini en producción”, **category puede ser más alcanzable que runner-up**. El video y el encuadre “Platea = Project” deciden eso.

No hay mínimo de revenue (FAQ). $0 en mayo no descalifica. Mentir related-party sí.

---

## 2. Lo que nos puede sacar vs lo que nos deja en el montón

**Descalificación / Stage One fail**

- Project = El Gorila / “nueva temporada”, no Platea. FAQ: *un restaurante no saca un platillo y lo llama negocio nuevo*.
- Devpost sigue llamándose **AdPilot**.
- Submission solo en español.
- Repo no compartido / sin source / con tokens.
- Video con música o marca de terceros.
- No responder verificación en 2 días (18 ago–15 sep).

**Perder sin que te saquen**

- Sin video (jueces no están obligados a testear; el video **es** la prueba).
- Repo público de **17 jul** (un mes de ops reales no está ahí).
- Decir “16 agentes en producción” cuando viven **4 loops + bot + humano**.
- $2.8k sin P&L (ads + GCP + Stripe fees) → parece que escondemos CAC.
- Zip caótico: 40 markdowns en español, CLAUDE.md de 600 líneas, pendientes de pauta.

**No mueve el prize (no gastar horas)**

GBP, Wikidata, GSC, Teatrando $350, UTMs, copy Meta, “16 agentes dormidos”, cliente B2B #2.

---

## 3. Dónde estamos vs la barra $50k

| Palanca | Hoy | Qué sube probabilidad |
|---------|-----|------------------------|
| Encaje reglas | Elegibles (MX, individuo, Vertex) | Renombrar Platea + párrafo New Project (ya escrito) |
| Revenue | $2,783 limpio | Re-export domingo; no vamos a $8k–15k. Compensar con **honestidad + CAC** |
| Related-party | $24 | No tocar salvo familia nueva |
| Video | ⬜ | **Palanca #1 de score** |
| GCP invoices + dashboard Gemini | ⬜ FAQ mínimo | Sin esto, AI-Native es anecdótico |
| Repo público | Congelado 17 jul | Refresh **después** de la limpia de Claude Code |
| “16 agentes” | Overclaim | Decir: **4 jobs + bot Gemini + 1 humano**; el roster es el organigrama |
| Narrativa 500–1000 EN | About existe; falta el bloque “jobs beyond founding team” que pide la home | Escribirlo (actor, coproductor, prensa, taquilla) |
| Testimonio | ⬜ | 1 quote con consentimiento > 0 |
| Marketing spend | TBD | Export Ads: margen feo es OK si CPA es la historia |
| Demo path jueces | README-public flojo / números de julio | `TESTING.md` EN: qué ver en 8 min sin secretos |

**Odds honestas.** Completar el paquete de abajo: posibilidad **real** de estar en el pelotón que sí entregan (la mayoría de 25k no). Gane $50k: **baja–media**, no 50%. El techo sube si: video 90 s nítido + repo que un juez entiende en 1 min + facturas GCP + no overclaim. El techo **no** sube con más docs de agencia.

---

## 4. Qué debe ver un juez en 8 minutos (y qué no)

Orden de lectura típico: **video → About → $ → repo README → un log**.

1. Video: IA decidiendo (mail 8:00 / funnel / bot), no cartel ni Maps.  
2. About: Platea nació después del 19 may; El Gorila es el cliente.  
3. $: 2783 / related 24 / 61 users.  
4. README público: 4 loops, Gemini/Vertex, link a evidencia.  
5. Un archivo de evidencia: `evidencia.md` o un log de `04_Operaciones/reportes/` sanitizado.

Si abren el Dropbox crudo (CLAUDE.md, 99_Skills, pendientes de pauta, IDs de ads) → “desmadre”. Por eso Claude Code limpia **la copia pública**, no toda la agencia viva.

**Claude Code — sí (entrega al jurado)**

- README público EN, números 15 ago, **sin** “16 agentes live”.
- `TESTING.md` EN (qué URL, qué job, qué no tocar).
- 1 página EN: 5 hechos “AI decided / human approved” (CPA, IC fix, dayparting, bot, funnel leak).
- Corrida `build_public_repo.sh` → cero secretos → push a `dupeyronosterlen/platea`.
- No publicar `CLAUDE.md`, `.env`, CSV Stripe, `privado/`.

**Claude Code — no (diluye)**

- Refactors de pauta, GBP, Wiki, 17 playbooks, “dejar la agencia perfecta para obra 2”. Eso es **después** del prize. El prize paga el año para pulir.

---

## 5. Checklist (hoy noche → lunes)

Marcar. Zip **después** de que esto esté verde, no antes.

### A — Esta noche (función 15 ago) · Dirección

- [ ] **20–40 s de celular:** sala / gente / aplauso (sin música de terceros).
- [ ] **3 frases a cámara** (ES ok; subtítulos EN en el corte): problema → Platea/Gemini → CPA en taquilla no en ads.
- [ ] Si hay 2 min: screenshot Stripe dashboard (totales, no lista de emails).

### B — Claude Code (limpia para entregar) · paralelo

- [ ] Roster honesto: live vs playbook.
- [ ] README-public + TESTING.md EN.
- [ ] Lista 5 decisiones IA/humano EN (`09_XPRIZE/ai-decisions.md`).
- [ ] Narrativa 500–1000 EN: day-to-day, human vs AI, jobs **beyond** founder (Humberto, coproductor, prensa, clientes WA).
- [ ] `build_public_repo.sh` + grep secretos + push `platea` (nunca `elgorila`).
- [ ] Share GitHub: `testing@devpost.com` y `judging@hacker.fund` (si el repo se queda público, igual confirmar licencia).

### C — Dirección · domingo 16 (antes de submit)

- [ ] Devpost: **rename Platea** (matar AdPilot) · Individual · **Small Business Services**.
- [ ] Pegar About + Additional info (`devpost-about-platea.md`, `devpost-additional-info.md`).
- [ ] Pegar $ del corte; si hubo más boletos: re-export Stripe → avisar para recortar agosto.
- [ ] GCP: PDFs Billing may–ago + screenshot observabilidad Gemini (FAQ mínimo).
- [ ] Ads Manager: spend Meta+Google may–ago (aunque duela).
- [ ] Video &lt;3 min YouTube/Vimeo **público**, sin soundtrack con copyright.
- [ ] 1 testimonio (comprador o medio) con “sí puedes citarlo”.
- [ ] Representante = Dirección (individuo).

### D — Cursor / Ag-15 · cuando A–C existan (no ahora)

- [ ] Recorte Stripe final.
- [ ] Zip ≤35 MB: PDFs GCP, Ads, screens (emails 8am, n8n, cockpit), **cero** CSV con emails.
- [ ] URL de evidencia en repo (no el CSV).
- [ ] Releer `expediente/02-elegibilidad-y-descalificacion.md` en voz alta.
- [ ] Submit **16 ago**. El 17 a la 1pm PT no se edita.

### E — 18 ago → 15 sep

- [ ] Bandeja del Representante cada día (2 días hábiles).
- [ ] Demo viva: sitio + jobs + bot. No apagar GCP.

---

## 6. Después del prize (aunque no gane)

Eso es “rentarte un año y pulir”: onboarding B2B, 2º cliente, 16 agentes de verdad. **No es el submission.** El submission es un **corte verificable** de lo que ya corre.

Archivos de pegar: `devpost-about-platea.md` · `devpost-additional-info.md` · `expediente/03-finanzas-rendicion.md` · `README-public.md` · este archivo.

Pendientes: `#21` + hijos en `04_Operaciones/PENDIENTES-MAESTRO.md` (hilo `xprize`).

---

## 7. Odds reales — participación, $50k, “consolación”

Fuente: [Devpost live](https://xprize.devpost.com/) **25,858 participants** (15 ago) = gente que dio **Join**, no gente que entregó. Premios oficiales ([reglas](https://xprize.devpost.com/rules) §8): **25 cheques** (1×$500k, 1×$200k, 3×$100k, 15×$50k runner-up, 5×$50k categoría). Máximo **un** premio por Project. **No hay** mención, honorable, merch ni “premio de consolación” en las reglas.

### Embudo (estimación, no dato oficial)

Devpost publica 5–33% registro→submit en hackathons genéricos. Este concurso pide negocio real + Stripe/banco + PDFs GCP + video EN + Gemini: nos sentamos en el **piso**.

| Capa | Orden de magnitud | Qué significa para nosotros |
|------|--------------------|-----------------------------|
| Inscritos | 25,858 | Estar aquí no es mérito. Es un click. |
| Submissions completas | ~5–12% → **~1,300–3,100** | Quien no video / no inglés / no GCP **no entra a Stage Two**. |
| Stage One pass | ~60–80% de lo entregado → **~800–2,500** | Tema + Gemini/GCP. AdPilot-como-feature o El Gorila-como-Project = fail. |
| Paquetes serios (ops + $ + video) | una fracción → **~200–600** | Aquí sí competimos si el paquete de §5 está verde. |
| Cheques | **25** | 20 de 25 son $50k. Top 5 = pitch LA 25 sep (grand). |

Si el paquete está completo y no nos descalifican:

| Premio | Lectura honesta |
|--------|-----------------|
| Grand / top 5 / LA | Muy baja. $2.8k vs SaaS de más revenue. No diseñar el video para “ganar $500k”. |
| Runner-up $50k | **La única vía de cheque creíble.** Score en AI-Native + historia SMB + no overclaim. Baja–media, no 50%. |
| Category Small Business $50k | Oficial: se juzga **dentro** de la categoría con los **mismos 3 criterios**. Marketing en geminixprize.com dice “highest-grossing” — si eso manda, **$2.8k pierde**. No apostar el fin de semana a categoría-por-facturación. |
| Circle / “Agentic Economy” | Aparece en marketing, **no** en la tabla oficial de Devpost. No contar. |

**% bruto:** 25 / 25,858 ≈ **0.10%** de inscritos ganan algo. Inútil: la mayoría no entrega.  
**% si entregamos paquete serio:** 25 / ~400 ≈ **~6%** de ganar *algún* cheque si estamos en esa canasta (y no todos esos 400 son iguales). Eso es techo de “suerte + ejecución”, no promesa.

### Qué sí existe si no hay cheque

- **Gallery Devpost** — todas las submissions públicas al cerrar. Eso es visibilidad, no premio.
- **Licencia de publicity** (reglas §7) — XPRIZE/Devpost *pueden* usar nombre/imagen/video 3 años. Pueden no usarnos. No hay cupo de “featured”.
- **Historia memorable** (padre, Kafka, 325 butacas, Gemini vendiendo butacas en CDMX) — más *featureable* que otro wrapper de ads. Útil para prensa propia y para que un juez recuerde el video. No es un prize.
- **Verificación** (mail ago–sep) — si te escriben, ya estás en el pelotón que miraron. Responder en 2 días. Eso no paga renta.
- **5 finalistas LA** — lo contrario de consolación. No comprar vuelo esperando wildcard.

**Conclusión:** o se arma un paquete que pelee **runner-up $50k**, o se entrega limpio para **no quedar fuera de gallery + no quedar en ridículo**. No hay tercer premio de $5k. La atención se fabrica con el video y el README honesto, no con más carpetas.
