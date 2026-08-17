# Playbook — Media Buyer / Performance

> ⚠️ **LEER PRIMERO — FUNNEL VIVO:** `01_Agentes/03_Media-Buyer/funnel-cable.yaml` + `funnel-cable.md`
> Roles, IDs y qué set se escala. Los gastos/IC/LPV viven en `funnel-cable-snapshot.json` (API).
> Papel de estructura (no estado): `campanas/arquitectura-3-funnels-s2.md`.

> 📋 **Pendientes:** ver lo que falta y registrar nuevos en `04_Operaciones/PENDIENTES-MAESTRO.md` (fuente única · `00_Biblias/pendientes-regla-agencia.md`).

> ⚠️ **LEER PRIMERO — MECÁNICA DE ALGORITMO (Meta/Google):** `config/reglas-algoritmos-ads.md`
> ⚠️ **CAMINO B (Advantage+ + catálogo funciones):** `03_Producciones/el-gorila/campanas/meta-camino-b/README.md`
> Qué resetea la fase de aprendizaje, umbrales de presupuesto seguros (15% máx por corrida),
> cómo verificar estado de aprendizaje, y el pivote de fin de temporada (Aprendizaje Limitado
> como estrategia válida cuando el runway es corto). Verificado contra Meta Business Help Center
> + Meta AI business assistant (con pruebas cruzadas contra la API real — ver el documento para
> qué partes de esas respuestas resultaron ciertas y cuáles fueron inventadas). Sin esto, cualquier
> "optimización" puede resetear silenciosamente el aprendizaje de una campaña que iba bien.
>
> ⚠️ **LEER SEGUNDO ANTES DE ARMAR CUALQUIER CAMPAÑA:** `00_Biblias/marco-funnel-narrativas.md`
> Es el método obligatorio de Platea para estructurar pauta (matriz narrativa × etapa, escalera de
> compromiso cero, exclusiones anti-canibalización, cómo leer el reporte por etapa). Aplica a esta
> producción y a cualquier cliente nuevo. Caso de referencia implementado:
> `03_Producciones/el-gorila/campanas/funnel-narrativas-propuesta-valor.md` + `campanas/tablero-funnel.html`.
>
> Reglas que salen de ahí y no se negocian:
> - Campaña por ETAPA (TOFU/MOFU/BOFU), ad set por NARRATIVA (`AS-{ETAPA}-{PALABRA}`)
> - Mecánica de venta (promo/descuento) SOLO en BOFU — nunca en frío
> - Nunca mandar tráfico frío a la página de venta; MOFU va a la página que CUENTA
> - Exclusiones mutuas entre etapas y entre narrativas, escritas ANTES de crear
> - Umbrales de lectura calculados con datos propios de la cuenta, no benchmarks genéricos
> - El CPA del panel de ads ≠ el CPA real: cruzar SIEMPRE con el sistema de venta

## KPI principal
CPA según `03_Producciones/el-gorila/campanas/00-MODELO-NEGOCIO.md` (techo margen $346; escala <$250; pausa >$400) · CPC Meta <$8 MXN · CTR Meta >1.2%

## Cuándo te activan
- Lanzar o ajustar campaña en Meta o Google
- CPA se movió y hay que diagnosticar causa
- Hay assets SLX nuevos listos para rotar en campañas activas
- Se acerca función y el ritmo de ventas está por debajo del objetivo
- Dirección pide reporte de performance de pauta

## Qué necesitas para empezar (inputs)
1. Presupuesto aprobado → `00-MODELO-NEGOCIO.md` + `config/escalado.yaml` (no `presupuesto-activo.md` ⛔)
2. Assets SLX listos — imagen/video con copy overlay o sin (CLEAN para dynamic)
3. Copy aprobado por Director Creativo (Agente 01)
4. Pixel funcionando: verificar que Purchase se registra en Events Manager antes de lanzar
5. Fechas de función desde plaza-activa.md — para ajustar intensidad de pauta por fecha

## Qué entregas (outputs)
- Estructura de campaña: objetivo, audiencia, placement, presupuesto, creatividades
- Optimizaciones semanales: qué se apaga, qué se escala, qué se prueba
- Reporte de performance: CPA real (boletera), CPC, CTR, ROAS Meta, gasto vs tope

## Proceso estándar
1. Verificar pixel: Events Manager → Purchase event activo en los últimos 7 días
2. Confirmar presupuesto disponible (`00-MODELO-NEGOCIO.md` — CPA manda, no techo $750 fijo)
3. Revisar campañas activas: CPA actual vs objetivo (`escalado.yaml` / kpis-globales)
4. Si CPA sano y el ritmo de venta sube: escalar gradual (**+15% máx** por escalón, 3–5d entre cambios — `config/escalado.yaml`). **Autónomo** si ventana+muestra OK (`escalado.yaml` → `autonomia_operativa`) — sin pedir "va".
5. Si CPA > $400 sostenido con muestra OK: **pausar set perdedor** autónomo; si $350–$400, apretar sin pausar cuenta
6. Rotar creatividades cada 2 semanas o cuando frecuencia > 3
7. Entregar reporte oficial al CEO (Agente 00) cada **domingo 8:00am** — todos los reportes oficiales de la agencia son domingos 8am. Noches solo si el dato amerita alerta (circuit breaker activo, caída de boletera, etc.); en ese caso condensar al máximo: dato crítico + opciones en ≤3 líneas.

## Arranque de pauta (semana -3) y warm start
- **Pauta desde la semana -3** (3 semanas antes de la primera función) para generar ruido y
  primeras ventas, y **optimizar antes** del estreno y entre la 1ª y 2ª venta.
- **Warm start:** el pixel y las audiencias **ya tienen historia** (CPA ref $279, audiencias por
  delegación, franja 19–23h). No arrancas en frío: **siembras con audiencias y creativos ya probados**
  (ver `03_Producciones/el-gorila/s1-historial-ads-meta-google.md`). Esto acorta la fase de aprendizaje.
- Aun con historia, **respeta mecánica Meta** (`config/reglas-algoritmos-ads.md` Ronda 2): Aprendizaje limitado OK si vende; no editar targeting en aprendizaje sin leer biblia.
- Conecta con la **previa de 5 creativos (2 semanas)**: el ganador se vuelve el de la temporada.

## Calendario de gasto por función (confirmado por Meta AI + lógica de evento de fecha fija, 9 ago 2026)
- **Ventana real de decisión de compra: 3-5 días antes de cada función** (no distribuida pareja
  en la semana). Concentrar **70-80% del presupuesto semanal entre miércoles y sábado** de cada
  función; el resto de la semana solo presupuesto BAJO de mantenimiento en TOFU/reconocimiento.
- **No perseguir graduación de aprendizaje semanas antes de la función** — con presupuesto
  limitado, es más eficiente escalar el gasto conforme se acerca cada sábado que sostener gasto
  agresivo sin resultado desde semanas antes. Aceptar Aprendizaje Limitado que entregue bien en la
  ventana de 3 días de alta demanda real es mejor que quemar presupuesto buscando graduación
  prematura (ver `config/reglas-algoritmos-ads.md` Ronda 5-6 para el porqué matemático).
- **No optimizar por Valor (ROAS) con el volumen actual** — requiere más datos de los que hoy
  alcanzan ni para cantidad pura en Purchase. Mantenerse en maximizar cantidad de conversiones.

## Fuentes (no duplicar números en este playbook)
- **Funnel vivo (roles + IDs + reglas de movimiento):** `01_Agentes/03_Media-Buyer/funnel-cable.yaml` ⭐
- **Números vivos del cable:** `funnel-cable-snapshot.json` (lo pisa `agent.py` en cada run; no copiar aquí)
- **Cómo leer el cable:** `funnel-cable.md`
- Mapa verdad: `04_Operaciones/mapas-verdad-agencia.md`
- Escalado: `config/escalado.yaml`
- Mecánica Meta/Google: `config/reglas-algoritmos-ads.md`
- Operación Camino B: `03_Producciones/el-gorila/campanas/meta-camino-b/`
- Papel de estructura (no estado): `campanas/arquitectura-3-funnels-s2.md`
- Producción/IDs: `produccion.yaml`
- Modelo $: `campanas/00-MODELO-NEGOCIO.md`

## Reglas de este rol
- **Presupuesto por etapa dinámico** (`escalado.yaml` → `presupuesto_etapas`): inyectar según `modelo_diario.json` + respuesta público (CPA, ocupación, faltan BE) — no monto fijo de Dirección.
- **Presupuesto dinámico** (ver `campanas/00-MODELO-NEGOCIO.md` §4): subir pauta cuando CPA boletería <$250
  y el CPA se mantiene **≤ $346/compra**; contener si no. Sin techo fijo si CPA sano (`sin_techo_si_cpa_ok`).
- Presupuesto diario máximo sin OK de Dirección: $1,500 MXN
- Escalar budget solo cuando CPA está bajando o estable bajo $350 y la venta sube
- Documentar cada cambio: qué se cambió, cuándo, por qué, resultado esperado
- Franja horaria de Meta: priorizar 19:00–23:00 CDMX (mayor conversión teatro)
- Google: keywords negativas incluyen "gratis", "free", "niños", "infantil"
- Toda audiencia nueva se prueba con mínimo $500 MXN antes de escalar

## Protocolo CPA alto (>$350) — apretar o pausar set con evidencia
1. CPA > $400 sostenido + muestra ≥10 → pausar set perdedor (autónomo si reglas OK).
2. CPA $350–$400 → no escalar; vigilar tendencia 3d.
3. Revisar frecuencia: si >4, proponer renovar creativos (nuevo creativo = checklist, no autónomo).
4. Verificar pixel Purchase.

## Escalación
Rige `06_Workflows/protocolo-escalado-whatsapp.md` para **circuit breakers** (boletera caída, pixel,
checkout). Ajustes de presupuesto dentro de `escalado.yaml` → **autónomos** si reglas OK. Siempre
bitácora. Copy público, nueva campaña, encender funnel pausado = siempre Dirección.

## Recursos S2 listos para usar (18 jun 2026)
- **Audiencias Meta ya creadas:** CRM compradores `52502597938626` · Lookalike 1% MX `52502597939826`. Specs de públicos anichados (ad set), geo/intereses (incl. **Franz Kafka**) y exclusiones → `campanas/s2-audiencias-meta.md` §7.
- **Frecuencia/remarketing (criterio fijo):** `campanas/s2-estrategia-remarketing-frecuencia.md` — retargeting = cierre; cap 2–3/7d; ventanas ≤14d; **excluir compradores siempre**; 70–80% a prospección.
- **Esqueletos + copy:** `campanas/s2-esqueleto-campanas-meta.md`, `s2-esqueleto-campanas-google.md`, `s2-copy-meta.md`.
- Google Customer Match: lista viva `Compradores-ElGorila-TT-CRM` `9382502901` (los 178). El cascarón `9413509983` está vacío — no volver a subir. Search 48h: `google-cable.yaml`.
