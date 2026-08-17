# 📎 Evidencia de usuarios y de producto corriendo

> Lo que demuestra que (a) hay **usuarios reales** y (b) el producto IA **corre en producción de forma continua**.
> Se acumula durante todo el hackathon. Las pruebas no se reconstruyen al final.

---

## 1. Evidencia de usuarios reales

Los jueces piden: número de usuarios individuales + **breakdown de quiénes son** + testimonios.

| Métrica | Valor | Fuente | Fecha de corte |
|---------|-------|--------|----------------|
| Usuarios únicos (compradores) | | Stripe / GA4 | |
| Boletos vendidos | | Stripe | |
| Sesiones / visitantes web | | GA4 (property 529010529) | |
| Breakdown de quiénes son | | Audiencias Meta/GA4 | |

**Breakdown (quiénes son nuestros usuarios):**
- _Ej.: público de teatro CDMX, 25–55 años, interés en cultura; recompradores S1; descuento estudiante/INAPAM._

> ⚠️ **Consentimiento:** asegurarse de que los usuarios saben que su info puede compartirse con los jueces
> (las reglas lo exigen). No compartir PII sin base para ello.

---

## 2. Testimonios / feedback de clientes

| Fecha | Cliente (con consentimiento) | Testimonio / feedback | Formato (texto/captura/video) |
|-------|------------------------------|------------------------|-------------------------------|
| | | | |

> Pedir feedback en el email post-compra (Resend) o en sala. Guardar capturas.

---

## 3. Evidencia de producto corriendo (AI-Native Operations)

Esto sustenta el criterio "la IA corre el negocio". Acumular:

| Tipo de evidencia | Dónde se guarda | Estado |
|-------------------|------------------|--------|
| **Logs de ejecución de agentes** (Media Buyer, CEO, Analytics…) | `04_Operaciones/reportes/` | ⬜ |
| **Registros de uso de API** (Gemini / Vertex AI) | Screenshot consola GCP `agencia-mkt-ia` | ⬜ |
| **Screenshots de dashboards** (GA4, Meta, Google Ads) | esta carpeta `/evidencia/` | ⬜ |
| **Decisiones ejecutadas por IA** (diagnóstico → acción → resultado) | `bitacora-hackathon.md` | ⬜ |
| **Creativos generados por IA** (Gorila Digital / Gemini) | `05_Activos/el-gorila/` | ⬜ |

> Objetivo narrativo: demostrar que los **playbooks corren en producción de forma continua**,
> no una demo aislada. Una corrida por semana documentada vale más que un screenshot bonito.

---

## 4. Acceso de prueba para jueces

| Elemento | Detalle | Estado |
|----------|---------|--------|
| URL del producto / demo | elgorilateatro.com.mx | ⬜ |
| ¿Privado? Credenciales en instrucciones de prueba | N/A si es público | ⬜ |
| Repo de código | (definir público vs privado compartido) | ⬜ |
| Instrucciones de prueba **en inglés** | | ⬜ |
| Gratis y accesible hasta 15 sep 2026 | | ⬜ |

---

## 5. Carpeta de adjuntos

Guardar los archivos pesados (CSVs, screenshots, exports) en una subcarpeta `evidencia/` dentro de
`09_XPRIZE/evidencia/` (o la carpeta que indiquen) y referenciarlos desde las tablas de arriba con su nombre y fecha.

