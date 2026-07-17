# Playbook — PR y Prensa (El Gorila S2)

## KPI
- Contactos hechos / semana (meta: ≥5 mientras Dirección está en producción)
- Respuestas / entrevistas agendadas
- Menciones al aire con UTM prensa (si hay link)

## Cuándo te activan
- Pre-estreno / estreno / aniversario / develación de placa (cuando Dirección fije fecha)
- Dirección pide “ruido” o “entrevistas”
- Cron domingo o `python agent.py --brief`

## Inputs
1. `plaza-activa.md` — fechas reales (prensa 18 jul · público 25 jul · cierre 19 sep)
2. `identidad.md` — sinopsis, premios, ángulo 37 años / Kafka
3. `s2-medios-offline-lista.md` — a quién contactar
4. Presskit URL

## Outputs
1. Brief semanal en `03_Producciones/el-gorila/campanas/pr-briefs/`
2. Pitches listos (radio / TV / prensa) — Dirección copia y envía
3. Actualización del tracker (estatus) cuando Dirección reporte respuesta

## Proceso
1. Leer fechas vivas (nunca inventar).
2. Elegir **un** gancho editorial de la semana (abajo).
3. Priorizar 5 medios del tracker.
4. Generar pitch corto (≤120 palabras) + asunto.
5. Entregar a Dirección — **no enviar**.
6. Si hay OK: Dirección envía; anotar fecha en tracker.

## Ganchos editoriales permitidos (prioridad)

| # | Gancho | Usar cuando | Claim cuidado |
|---|--------|-------------|----------------|
| A | 37 años con el mismo monólogo (desde 1989) | Siempre | Decir “de las trayectorias más largas del teatro mexicano” — **no** “récord mundial” hasta Ag-09 |
| B | Kafka en escena — *Informe para una Academia* | Radio/TV culta | OK |
| C | Estreno temporada Wilberto Cantón (SOGEM) | Hasta 25 jul | Público 25; prensa 18 |
| D | Premios documentados (Sol de Oro, etc.) | Perfiles trayectoria | Solo los de `identidad.md` |
| E | Develación de placa | Solo cuando Dirección confirme fecha | ⛔ No usar 26 sep |

## Reglas
- Regla de oro #7: Dirección aprueba todo mensaje a medios.
- Cortesías a medios: máx 4 / medio; marcar en admin.
- Links: `elgorilateatro.com.mx/boletos?utm_source=prensa&utm_medium=earned&utm_campaign=s2_estreno`
- Si piden “cuánto cuesta el boleto”: preventa $350 hasta 25 jul incl.; regular $400 desde 26 jul; estudiante/INAPAM/maestro $245.
