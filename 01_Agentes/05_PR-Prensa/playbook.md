# Playbook — PR y Prensa (El Gorila S2)

> 📋 **Pendientes:** ver lo que falta y registrar nuevos en `04_Operaciones/PENDIENTES-MAESTRO.md` (fuente única · `00_Biblias/pendientes-regla-agencia.md`).

> Fuentes operativas: `04_Operaciones/mapas-verdad-agencia.md` · claims: `campanas/ag09-claims-legado.md`
> Presencia IA (Wikidata/Wikipedia/prensa que citan GPT/Gemini): `00_Biblias/presencia-ia-geo.md` · checklist: `campanas/presencia-ia-checklist.md`

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
2. Pitches listos (`agent.py --pitches`) o presets en `enviar_pitch.py`
3. Envío **solo con va de Dirección** vía `enviar_pitch.py --confirm`
4. Bitácora automática: `registro-mails-prensa.md` + tracker

## Proceso
1. Leer fechas vivas (nunca inventar).
2. Elegir **un** gancho editorial de la semana (abajo).
3. Priorizar 5 medios del tracker.
4. Generar pitch corto + asunto (o usar presets).
5. Mostrar a Dirección el texto final.
6. Si Dirección dice **va** → `python3 enviar_pitch.py --preset … --confirm`
   (Resend + curl; BCC a dupeyronosterlen@gmail.com; Reply-To comunicaciones@).
7. Anotar respuesta cuando llegue.

## Envío (Cursor o Terminal)
```bash
# ver sin mandar
python3 01_Agentes/05_PR-Prensa/enviar_pitch.py --preset canal22,once,unam
python3 01_Agentes/05_PR-Prensa/enviar_pitch.py --preset jornada,timeout,chilango,cartelerateatro,revistacentral,adip

# mandar (solo tras va)
python3 01_Agentes/05_PR-Prensa/enviar_pitch.py --preset canal22,once,unam --confirm
python3 01_Agentes/05_PR-Prensa/enviar_pitch.py --preset jornada,timeout,chilango,cartelerateatro,revistacentral,adip --confirm
```

## Bot WA (próximo)
Dirección escribe al CEO: `manda prensa 22` / `va prensa` → n8n llama el mismo script o Resend HTTP.
Hasta que eso exista: Cursor ejecuta el script con tu va.

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
- Si piden “cuánto cuesta el boleto”: general **$400**; INAPAM/estudiante/maestro **$280**; pareja ESPEJO **$600**. Preventa $350 / $245 **cerrada** (25 jul). Leer `produccion.yaml` → `precios` antes de citar un número.
