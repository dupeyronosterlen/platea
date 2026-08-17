# 09_XPRIZE — Build with Gemini · Casa única del concurso
> **Dueño: Agente 15 (Arquitecto de Procesos)** — coordina; Dirección aprueba todo lo público.
> **Deadline: 17 agosto 2026, 1:00 PM PT**
> Creado 10 jul 2026 · Unificado con el expediente de junio el **16 jul 2026** (antes `10_Hackathon-XPRIZE/`).

## Qué se entrega (checklist rápido)

- [x] **C1 — Repo público GitHub** — https://github.com/dupeyronosterlen/platea (refrescado 16 jul; **no** es la boletera)
- [ ] **C3 — Video demo < 3 min** → `guion-video-demo.md`
- [ ] **Formulario de submission** Devpost
  - About / overview → [`devpost-about-platea.md`](devpost-about-platea.md)
  - **Additional info (jueces)** → [`devpost-additional-info.md`](devpost-additional-info.md) ← buscar aquí el 17 ago para actualizar $
- [x] **Evidencia continua** → `evidencia.md`

Checklist completo Devpost: [`expediente/01-checklist-submission.md`](expediente/01-checklist-submission.md)

**Ruta premio $50k (runner-up / categoría):** [`ruta-50k.md`](ruta-50k.md) — plan de ejecución hasta el 17 ago.

**Ataque $50k (15 ago):** [`ataque-50k.md`](ataque-50k.md) — análisis de qué sí mueve el prize + checklist noche/domingo/lunes. Claude Code: leer esto **antes** de “dejar la agencia perfecta”; el jurado ve video + About + $ + README público, no el Dropbox crudo.

**Cómo puntúan (acomodar inventario):** [`criterios-jueces.md`](criterios-jueces.md) — Stage One + 3 tercios iguales. El $ no es la vara. Mapa Devpost ← archivos.

## Mapa de esta carpeta

| Ruta | Rol |
|------|-----|
| `README.md` | Este archivo — entrada |
| `README-public.md` | Texto del README en GitHub público |
| `devpost-about-platea.md` | Texto About / Inspiration… para Devpost |
| `devpost-additional-info.md` | **Additional info** (finanzas, AI, GCP, repo) — actualizar $ con Stripe |
| `devpost-thumbnail-platea-square.png` | Thumbnail submission |
| `evidencia.md` | Índice cronológico de evidencia |
| `guion-video-demo.md` | Guion video &lt;3 min |
| `ruta-50k.md` | Plan ejecución premio $50k |
| `ataque-50k.md` | Análisis + checklist $50k (15 ago) — palancas reales vs ruido |
| `criterios-jueces.md` | Qué puntúan + acomodar lo que hay vs Viability / AI-Native / Impact |
| `sanitizacion-repo.md` | Reglas allowlist / secretos |
| `build_public_repo.sh` | Construye copia sanitizada |
| `expediente/` | Cumplimiento: checklist, finanzas, elegibilidad, deadlines, reglas |
| `platea-public/` | Artefacto local del build (no editar a mano; regenerar con el script) |

**Funnel vivo (Ag-03, no copiar números aquí):** `01_Agentes/03_Media-Buyer/funnel-cable.yaml` + `funnel-cable.md`. Gastos/IC/LPV salen de `funnel-cable-snapshot.json` (API en cada run del agente). Cuando esta carpeta se limpie para el submit, enlazar eso — no pegar spend del chat.

`10_Hackathon-XPRIZE/` queda solo como **stub** que apunta aquí.

## Pitch (corto)

**Platea**: agencia de marketing teatral operada por agentes de IA (Gemini / Vertex) que vende boletos reales de *El Gorila* (CDMX), con un humano en el loop. En construcción y ya en producción.

## Reglas

1. Cero tokens/PII en lo que se publica (este folder va al repo `platea`).
2. Toda evidencia nueva → una línea en `evidencia.md`.
3. Guion video: Dirección aprueba antes de grabar/ensamblar.
4. **Nunca** desplegar boletera desde aquí. Venta = repo `elgorila` / site.
