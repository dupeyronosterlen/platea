# 🏆 Hackathon — Build with Gemini XPRIZE

> **Carpeta de seguimiento para rendir cuentas y NO descalificarnos.**
> Estado: **INSCRITOS** (Devpost Step 1 y 2 hechos) · **SIN submission final aún** (esperando ventas reales).
> Última actualización: 18 jun 2026 · Dueño: Dirección Dupeyrón.

---

## Qué es esto

Esta carpeta es el **expediente único** del concurso. Aquí va todo lo que los jueces nos pueden pedir
y todo lo que tenemos que ir acumulando mes a mes para no quedar fuera por un detalle administrativo.

**Regla de oro del expediente:** si pasa algo que sirve de evidencia (una venta, una corrida de un agente IA,
un testimonio, un gasto) → se anota AQUÍ el mismo día. Las pruebas no se reconstruyen al final, se acumulan.

---

## El concurso en 30 segundos

| Campo | Dato |
|-------|------|
| Nombre | Build with Gemini XPRIZE |
| Sponsor | XPRIZE · Administrador: Devpost |
| Sitio | xprize.devpost.com |
| **Periodo de submission** | **19 may 2026 (10:00 PT) – 17 ago 2026 (1:00 PM PT)** |
| Juzgamiento | 18 ago – 15 sep 2026 |
| Finalistas / ganadores | ~25 sep 2026 |
| Premio 1° | **$500,000 USD** |
| Premios | 2°: $200k · 3°-5°: $100k · 15 runner-ups: $50k c/u · 5 premios por categoría: $50k c/u |
| Tope | Un proyecto solo puede ganar **un** premio |

---

## Qué es nuestro "Project" (para los jueces)

**Platea** — una agencia de marketing teatral que **opera con IA (Gemini)**. El negocio real que lanzamos
y operamos durante el hackathon. **El Gorila** es el cliente 0 / prueba de concepto: una obra real,
con boletera real (Stripe en producción) y ad spend real.

- **Categoría candidata principal:** Small Business Services *(le da herramientas a un negocio real —la obra— para competir)*.
- **Categoría alternativa:** Entrepreneurship & Job Creation / Professional Services. → **decisión de Dirección pendiente** (ver `02`).
- **Cómo la IA transforma el workflow:** agentes Gemini 2.5 Pro (Vertex AI) analizan métricas Meta/Google,
  diagnostican, recomiendan y ejecutan decisiones de campaña; generación de creativos con Gemini.
- **Requisito Gemini API:** ✅ se cumple — al menos una llamada LLM en producción corre sobre Gemini.
- **Requisito Google Cloud:** ✅ se cumple — Vertex AI / GCP (`agencia-mkt-ia`).

---

## 🚦 Estado rápido de los 3 criterios de juzgamiento

Los 3 pesan **igual**. Hoy estamos así:

| Criterio | Qué piden | Nuestro estado |
|----------|-----------|----------------|
| **Business Viability** | Negocio real, usuarios reales, **revenue real** en los 90 días | 🟡 En riesgo — falta volumen de ventas atribuibles |
| **AI-Native Operations** | La IA corre el negocio en producción y ejecuta decisiones | 🟡 Infra lista, faltan corridas documentadas |
| **Category Impact** | Mover la aguja en la categoría elegida | 🟡 Narrativa lista, falta evidencia de escala |

---

## Mapa de la carpeta

| Archivo | Para qué |
|---------|----------|
| `01-checklist-submission.md` | Todo lo que hay que entregar en Devpost. Checklist vivo. |
| `02-elegibilidad-y-descalificacion.md` | Reglas que nos pueden dejar fuera. **Leer antes de enviar.** |
| `03-finanzas-rendicion.md` | Revenue por mes, costos, marketing spend, related-party. La parte de "rendir cuentas". |
| `04-evidencia-usuarios-y-producto.md` | Usuarios reales, testimonios, logs de IA, screenshots. |
| `05-calendario-deadlines.md` | Fechas que no se pueden pasar. |
| `99-reglas-oficiales.md` | Texto fuente de las Official Rules (referencia literal). |

> **Relacionado:** `04_Operaciones/bitacora-hackathon.md` = bitácora narrativa de corridas de IA
> (qué corrió, qué decidió, qué resultado). Esta carpeta y esa bitácora se complementan;
> la evidencia financiera y de cumplimiento vive aquí.

---

## ⚠️ Top 3 riesgos de descalificación (resumen — detalle en `02`)

1. **"New Projects Only":** el Project debe ser nuevo (creado tras el 19 may 2026). El Gorila/boletera
   **ya existían** → hay que dejar clarísimo en el texto que lo **nuevo** es la agencia IA (Platea), y
   **explicar** qué se reutilizó. No esconderlo: las reglas piden explicarlo.
2. **Idioma:** TODO el material de submission debe estar **en inglés** (o con traducción al inglés:
   video, descripción, instrucciones de prueba). Hoy todo está en español.
3. **Revenue legítimo:** el revenue que cuenta es de **terceros arms-length** (público comprando boletos).
   Ventas a familia / equipo / relaciones previas se reportan **aparte** (related-party). No mezclar.
