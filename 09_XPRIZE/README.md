# 09_XPRIZE — Build with Gemini · Casa única del concurso
> **Dueño: Agente 15 (Arquitecto de Procesos)** — coordina; Dirección aprueba todo lo público.
> **Deadline: 17 agosto 2026, 1:00 PM PT**
> Creado 10 jul 2026 · Unificado con el expediente de junio el **16 jul 2026** (antes `10_Hackathon-XPRIZE/`).

## Qué se entrega (checklist rápido)

- [x] **C1 — Repo público GitHub** — https://github.com/dupeyronosterlen/platea (refrescado 16 jul; **no** es la boletera)
- [ ] **C3 — Video demo < 3 min** → `guion-video-demo.md`
- [ ] **Formulario de submission** Devpost
- [x] **Evidencia continua** → `evidencia.md`

Checklist completo Devpost: [`expediente/01-checklist-submission.md`](expediente/01-checklist-submission.md)

## Mapa de esta carpeta

| Ruta | Rol |
|------|-----|
| `README.md` | Este archivo — entrada |
| `README-public.md` | Texto del README en GitHub público |
| `evidencia.md` | Índice cronológico de evidencia |
| `guion-video-demo.md` | Guion video &lt;3 min |
| `sanitizacion-repo.md` | Reglas allowlist / secretos |
| `build_public_repo.sh` | Construye copia sanitizada |
| `expediente/` | Cumplimiento: checklist, finanzas, elegibilidad, deadlines, reglas |
| `platea-public/` | Artefacto local del build (no editar a mano; regenerar con el script) |

`10_Hackathon-XPRIZE/` queda solo como **stub** que apunta aquí.

## Pitch (corto)

**Platea**: agencia de marketing teatral operada por agentes de IA (Gemini / Vertex) que vende boletos reales de *El Gorila* (CDMX), con un humano en el loop. En construcción y ya en producción.

## Reglas

1. Cero tokens/PII en lo que se publica (este folder va al repo `platea`).
2. Toda evidencia nueva → una línea en `evidencia.md`.
3. Guion video: Dirección aprueba antes de grabar/ensamblar.
4. **Nunca** desplegar boletera desde aquí. Venta = repo `elgorila` / site.
