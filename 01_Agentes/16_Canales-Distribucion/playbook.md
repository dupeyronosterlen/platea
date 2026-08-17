# Playbook — Agente 16 · Canales de Distribución

> 📋 **Pendientes:** ver lo que falta y registrar nuevos en `04_Operaciones/PENDIENTES-MAESTRO.md` (fuente única · `00_Biblias/pendientes-regla-agencia.md`).

> Fuentes operativas: `04_Operaciones/mapas-verdad-agencia.md` · precios/canales: `produccion.yaml` → `canales_externos`

## 1. Prospección
Mantener `03_Producciones/<obra>/canales/panorama-canales.md` con los candidatos evaluados,
priorizados (alta/media/descartado) y con la razón de cada prioridad. No contactar un canal nuevo
sin antes registrarlo ahí — así queda historial de por qué se descartó o priorizó algo (evita
contradicciones como la de Ticketmaster, ver `canales/Ticketmaster/README.md`).

## 2. Antes de llenar cualquier documento
Leer, en este orden:
1. `03_Producciones/<obra>/produccion.yaml` → sección `precios` (precio vigente, no el de
   preventa si ya pasó) y sección `canales_externos` (si el canal ya existe, ver su estado).
2. El `README.md` del canal (si ya existe) para no repetir datos de contacto que ya se tienen.

Nunca usar una cifra que solo viste en un chat de WhatsApp, un correo viejo, o de memoria — si no
está en `produccion.yaml`, se verifica con Dirección antes de escribirla en un formulario externo.

## 3. Alta de un canal nuevo
1. Copiar `03_Producciones/_PLANTILLA-CANAL/` a `03_Producciones/<obra>/canales/<slug-canal>/`.
2. Llenar los documentos que pida la plataforma (ficha de la obra, datos de pago) con los datos
   verificados en el paso 2.
3. Llenar el `README.md` del canal con sus secciones fijas: Contacto, Envíos (a quién, qué
   adjuntos, desde qué correo), Esquema de precio/comisión (verificado contra las reglas propias
   de la plataforma, no asumido), Cupo, Estado, Pendientes.
4. Pedir a Ag-08 (skill `cartel-diseno-teoria`) el arte en las medidas exactas que pida la
   plataforma — nunca reciclar un arte existente a ojo sin confirmar medidas.
5. Reunir todo en `canales/<slug-canal>/PARA-ENVIAR/`.

## 4. Envío
Ag-16 arma el paquete completo y, si aplica, redacta el/los correos. **Nunca se envía sin el "va"
explícito de Dirección** (regla de oro #1). Si se usa la integración de Gmail vía MCP, hoy solo permite
crear borradores sin adjuntos (limitación conocida, 26 jul 2026) — Dirección adjunta los archivos y
revisa el remitente antes de enviar.

## 5. Cierre
Al confirmar que Dirección envió (o publicó) algo:
1. Registrar la decisión en `config/session_decisions.json` (protocolo de cierre, CLAUDE.md §11).
2. Actualizar el estado del canal en `produccion.yaml` → `canales_externos`.
3. Actualizar el `README.md` del canal (sección Estado + Pendientes de seguimiento).

## 6. Sincronización continua (el paso que faltaba)
Cada vez que cambie cualquier precio, fecha, dato de elenco o de venue en `produccion.yaml`:
1. Revisar `canales/README.md` (índice maestro) para listar todos los canales con estado
   "activo" o "en proceso".
2. Para cada uno, revisar si su `README.md` o los documentos ya enviados citan el dato que cambió.
3. Si el canal permite actualizar datos después del alta (la mayoría tiene un correo de
   "modificaciones futuras"), avisar a Dirección para que lo reenvíe.
4. Si el CLAUDE.md raíz también cita ese dato (ej. §2 tabla de precios), corregirlo ahí también —
   no asumir que otra sesión ya lo hizo.

## 7. Cierre de plaza (renta terminada o última función)

El reloj **Plaza** se apaga. El de **Entidad** no. Biblia: `00_Biblias/presencia-ia-geo.md` §4.
Checklist de la obra: `campanas/presencia-ia-checklist.md` columna Baja.

1. Inventariar `canales/README.md` en estado activo/enviado.
2. Cada README debe tener **contacto de baja** — si no está, no se dio de alta bien.
3. GBP/Bing/Apple: borrar Posts y quitar venue de la descripción. **No** borrar el perfil
   de productora. Si alguien creó pin visitable en el teatro rentado: cerrar *ese* listado.
4. Actualizar `produccion.yaml` → `canales_externos` a `cerrado`.
5. Avisar a Ag-13 (`llms.txt` + schema Event) y Ag-05 (Wikidata P276 con fecha fin).

## 8. Reconciliar canales huérfanos existentes (tarea única, ya en curso)
Al crear este agente (26 jul 2026) se encontraron canales con materiales pero sin dueño ni
registro claro de qué se envió:
- `canales/Ticketmaster/` — contradice `panorama-canales.md` (que lo marca como descartado).
  Pendiente que Dirección aclare el estado real antes de tratarlo como canal activo o cerrarlo.
Cualquier carpeta nueva que aparezca dentro de `canales/` sin `README.md` debe tratarse igual:
documentar el hallazgo, no asumir que está resuelto ni que está descartado.
