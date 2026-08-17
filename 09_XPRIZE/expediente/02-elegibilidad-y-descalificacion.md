# 🛡️ Elegibilidad y riesgos de descalificación

> El objetivo de este archivo: **que no nos saquen por un detalle**.
> Leerlo completo antes de hacer el submission final.

---

## 1. ¿Somos elegibles?

| Condición | ¿Cumplimos? | Nota |
|-----------|-------------|------|
| Individuo en mayoría de edad / equipo / organización <25 empleados | ✅ | |
| No residentes de países sancionados (Rusia, Cuba, Irán, Corea del Norte, Crimea…) | ✅ | México OK |
| No empleados/agentes/jueces del Sponsor o Administrador ni sus familias | ✅ | |
| Representante autorizado nombrado | ⬜ | Dirección (confirmar por escrito) |

**Decisión pendiente — ¿cómo entramos?**
- **Individuo** (Dirección) → premio se paga a Dirección.
- **Equipo** → Dirección es Representante, reparte el premio.
- **Organización** → requiere **Corporate ID** (D4 del checklist) y el premio se paga a la organización.
> 👉 Esto tiene implicaciones fiscales (ver `privado/fiscal/`). **Decisión de Dirección.**

---

## 2. 🔴 Riesgo #1 — "New Projects Only"

**La regla:** los proyectos deben ser **creados de nuevo por el Entrant después del inicio del periodo
(19 may 2026)**. Si se usaron plantillas/frameworks/boilerplates/snippets preexistentes, **hay que explicar**
cómo el Project los utilizó.

**Nuestra situación:** El Gorila, la web y la boletera **ya existían** antes del 19 may. Esto NO nos
descalifica automáticamente, pero hay que encuadrarlo bien:

- ✅ **Lo NUEVO (el Project):** la **agencia de marketing operada por IA (Platea)** — los agentes Gemini,
  los flujos de decisión autónoma, la capa de analítica/optimización con IA. Eso se construyó durante el hackathon.
- ⚙️ **Lo PREEXISTENTE (a declarar):** la boletera/web de El Gorila (infra de venta), assets de la obra,
  historial de campañas S1. → **El Gorila es el cliente/caso de uso, no el Project.**
- 📝 **Acción:** en la descripción de texto, incluir un párrafo honesto: "qué es nuevo / qué se reutilizó".

---

## 3. 🔴 Riesgo #2 — Idioma (inglés obligatorio)

Todo el material de submission debe estar **en inglés** o llevar **traducción al inglés**: video,
descripción de texto, instrucciones de prueba y cualquier otro material.

- Hoy **todo está en español**. → Acción: traducir descripción, subtitular/locutar video en inglés,
  e instrucciones de prueba en inglés.

---

## 4. 🔴 Riesgo #3 — Integridad del revenue

- El revenue que cuenta para "Business Viability" es de **terceros arms-length** (público real comprando boletos).
- Ventas a **familia, miembros del equipo, entidades relacionadas o relaciones de cliente preexistentes**
  → se reportan **por separado** como **Related-Party Revenue**. No inflar el número principal con esto.
- Mentir o mezclar = riesgo de descalificación en verificación. Mejor número honesto y limpio.
- Detalle y tablas en `03-finanzas-rendicion.md`.

---

## 5. Otros motivos de descalificación a vigilar

| Riesgo | Cómo lo evitamos |
|--------|------------------|
| No responder verificación en ≤2 días hábiles | Monitorear bandeja del Representante a diario en periodo de juzgamiento |
| Project no accesible / de pago durante juzgamiento | Mantener web y demo gratis y arriba hasta 15 sep |
| Video con música o marcas de terceros sin permiso | Usar música con licencia / propia; revisar el corte final |
| Repo sin todo el source o no compartido con los correos | Verificar acceso a `testing@devpost.com` y `judging@hacker.fund` |
| IP de terceros en el Submission | Solo assets propios o con permiso |
| Modificar la submission tras el cierre | Cerrar todo antes del 17 ago 1:00 PM PT |
| Conflicto de interés (real o aparente) | N/A — sin relación con Sponsor/Administrador |

---

## 6. Categoría — análisis (decisión de Dirección)

Un Project solo puede ganar **un** premio, pero debemos elegir **al menos una categoría**:

| Categoría | ¿Encaja? | Argumento |
|-----------|----------|-----------|
| **Small Business Services** | ⭐ Fuerte | "Powering everyday businesses with tools to compete and win" — exactamente lo que Platea le da a una producción teatral independiente. |
| **Entrepreneurship & Job Creation** | Medio | Herramientas que ayudan a fundadores/economías; encaja si lo posicionamos como producto para emprendedores creativos. |
| **Professional Services** | Medio | "Connecting everyday people with expert guidance" — la IA da expertise de agencia a quien no puede pagarla. |
| Education & Human Potential | Débil | No es el foco. |
| Money & Financial Access | No | No aplica. |

> **Recomendación:** Small Business Services (mejor fit + categoría con premio propio de $50k).
> **Pendiente:** que Dirección lo confirme.
