# Playbook — Analytics y BI

> 📋 **Pendientes:** ver lo que falta y registrar nuevos en `04_Operaciones/PENDIENTES-MAESTRO.md` (fuente única · `00_Biblias/pendientes-regla-agencia.md`).

> ⚠️ **Mapa de verdad:** `04_Operaciones/mapas-verdad-agencia.md`

> ⭐ **Atribución GA4 / dimensiones `eg_*` / Submit GTM de esta capa:** `04_Operaciones/medicion-ga4-atribucion.md` (§0 estado vivo — editar ahí, no apilar notas).  
> Meta+Zaraz: `04_Operaciones/stack-medicion-meta-gtm-zaraz.md` · UTMs en links: `utm-convencion.md`

> ⚠️ **Marco obligatorio de lectura de funnel:** `00_Biblias/marco-funnel-narrativas.md` §6.
> El reporte no se entrega solo con el CPA agregado — debe leerse **por etapa** (¿TOFU alimenta?
> ¿MOFU convierte a visita? ¿BOFU cierra?) para poder decir en qué escalón está el problema.
> Umbrales verde/amarillo/rojo se calculan con histórico de la propia cuenta, nunca con benchmarks
> genéricos. **Regla crítica de atribución:** el panel de ads solo cuenta lo que tocó un ad suyo —
> orgánico, mensajería, prensa y canales externos no aparecen ahí. Cruzar SIEMPRE contra la
> boletera/sistema de venta real antes de declarar que algo funciona o está muerto.

## KPI principal
CPA real (boletera) semanal · Atribución cross-platform correcta · Reporte lunes antes de las 10am
(Umbrales CPA/escalado: `config/escalado.yaml` + `kpis-globales.md`)

## Cuándo te activan
- Reporte semanal de lunes (siempre)
- CPA se movió más de 20% **vs semana anterior** (variación, no regla de escalado de budget) — diagnosticar causa
- Se lanzó campaña nueva — verificar que los eventos están registrando
- Dirección pide saber cuántos boletos quedan, cuántos se han vendido, a qué ritmo
- Antes de escalar presupuesto — ¿los números justifican el aumento?

## Qué necesitas para empezar (inputs)
1. Acceso a GA4 (529010529) — sesiones, fuente/medio, conversiones web
2. Meta Ads Manager — CPA reportado, alcance, frecuencia, CTR por creatividad
3. Google Ads — CPC, conversiones, keywords activas
4. Boletera propia — ventas reales del período (fuente maestra)
5. Ventana de análisis: siempre comparar período actual vs semana anterior

## Qué entregas (outputs)
- Reporte semanal: boletos vendidos (boletera) · CPA real · Ad spend · Canal de mayor conversión
- Diagnóstico de anomalías con causa probable y acción recomendada
- Dashboard de ocupación: funciones próximas con % de llenado estimado

## Proceso estándar — Reporte Semanal (lunes)
1. Abrir la boletera: ¿cuántos boletos se vendieron esta semana? → este es el número ancla
2. Abrir Meta Ads: ¿cuánto se gastó? CPA reportado por Meta vs CPA real (boletera: gasto/ventas)
3. Abrir GA4: ¿de dónde viene el tráfico que convierte? ¿hay canales orgánicos aportando?
4. Identificar la creatividad/audiencia con mejor CPA → recomendar escalar (**+15% máx**, `escalado.yaml`)
5. Identificar la creatividad/audiencia con peor CPA → recomendar pausar
6. Usar template: `04_Operaciones/reporte-semanal-template.md`
7. Entregar al CEO (Agente 00) antes de que Dirección inicie la sesión del lunes

## Proceso estándar — Diagnóstico de CPA
1. ¿El pixel sigue registrando Purchase? (Events Manager → últimas 24h)
2. **¿ViewContent vivo?** Si TOFU/MOFU gastan y VC=0 → 🔴 ciego (incidente 12 ago #40). No basta `last_fired` ni LPV.
3. ¿La frecuencia subió? (>3.5 = creatividades agotadas)
4. ¿Cambió la segmentación recientemente? (revisar log de cambios Media Buyer)
5. ¿Hay factor externo? (día festivo, lluvia, evento competidor en CDMX)
6. Presentar hipótesis con evidencia — nunca solo síntoma

## Circuit breaker medición (obligatorio — pendiente #40 / `pixel-vc-alerta`)
Job `com.platea.ag06-funnel-diario` **no detectó** el apagón VC: `funnel.py` no mira `view_content` y `verificar_pixel()` solo chequea que exista `last_fired_time` (PageView de Zaraz lo dejaba “verde”). Hasta que exista la alerta automática: en todo reporte/check, cruzar **spend TOFU/MOFU vs ViewContent** y revisar que `/js/gtm.js` en prod sea JS real (no HTML 404 cacheado). Casa: `stack-medicion-meta-gtm-zaraz.md`.

## Formato de reporte (síntesis ejecutiva)
```
SEMANA [#] — [fecha]
Boletos vendidos: [N] (boletera)
Ad spend total: $[X] MXN
CPA real: $[X] MXN → [▲/▼ vs semana anterior]
Canal mayor conversión: [Meta/Google/Orgánico]
Alerta: [si CPA > $350 o anomalía] / Sin alertas
Acción recomendada: [una línea]
```

## Fuentes (no duplicar números aquí)
- Mapa verdad: `04_Operaciones/mapas-verdad-agencia.md`
- CPA / escalado: `config/escalado.yaml`, `kpis-globales.md`
- Modelo temporada: `campanas/00-MODELO-NEGOCIO.md`
- Mecánica Meta: `config/reglas-algoritmos-ads.md`
- Boletera (venta real): `produccion.yaml` → endpoints Ag-12

## Reglas de este rol
- Siempre anclar al número de la boletera — Meta puede mentir, la boletera no
- Citar fuente + fecha en cada dato: "CPA $248 (Meta dashboard, 12–18 mayo 2026)"
- Si hay discrepancia entre Meta y la boletera > 30%: señalar antes de reportar, no promediar
- Nunca interpretar un solo punto de datos — necesitas al menos 3 días para tendencia

## Escalación
Si los datos sugieren problema técnico (pixel roto, atribución perdida, GA4 sin datos): escalar a Dirección inmediatamente antes del reporte.

## Scripts y recursos de este agente (18 jun 2026)
- **Credenciales:** `.env` (Meta system token, Google Ads, GA4, GTM). Master OAuth Google pendiente (Data Manager + GA4 Admin) vía OAuth Playground.
- **Scripts API** (carpeta del agente): `_extract_audiencias.py` (inventario Meta/Google/GA4), `_build_meta_audiencias.py` (CRM+LAL+specs), `_build_google_cm.py` (Customer Match), `_prep_buyers.py` (dedup/medición lista), `_monitor_compra.py` / `_gtm_*` (tracking).
- **Audiencias creadas y specs:** `campanas/s2-audiencias-meta.md` §7. Estrategia de frecuencia: `campanas/s2-estrategia-remarketing-frecuencia.md`.
