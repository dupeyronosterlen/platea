/**
 * elgorila-reporte — Worker read-only de ventas de la Taquilla.
 *
 * Expone GET /api/reporte para que los agentes de la agencia
 * lean datos reales de ventas sin acceso directo a KV ni a Stripe.
 *
 * KV bindings (mismos namespaces que elgorila-api, solo lectura):
 *   INVENTARIO  → wilberto:funcion:{fecha_iso}, wilberto:funciones:activas
 *   VENTAS      → (no usado actualmente, binding retenido por compatibilidad)
 *
 * Secret:
 *   REPORTE_TOKEN → Bearer token que deben mandar los agentes
 *
 * Endpoints:
 *   GET /api/reporte                    → reporte global (todas las funciones activas/pasadas)
 *   GET /api/reporte?desde=YYYY-MM-DD  → filtrar desde fecha
 *   GET /api/reporte?hasta=YYYY-MM-DD  → filtrar hasta fecha
 *   GET /api/reporte?funcion=YYYY-MM-DD → solo una función
 *   GET /health                         → check sin auth
 *
 * Estructura KV INVENTARIO (key: wilberto:funcion:{fecha_iso}):
 *   { version, bloqueado, holds, secciones: { [secId]: { total, vendidos, reservados } } }
 *   Fix 2026-07-01: vendidos = sum(Object.values(inv.secciones)) — no filtrar por secId.
 */

const CORS_HEADERS = {
  "Access-Control-Allow-Origin": "*",
  "Content-Type": "application/json",
};

// Fechas hardcodeadas S2 como fallback si wilberto:funciones:activas no está en KV
// Act. 2026-07-11: temporada termina el 19 sep (ya no hay función el 26 sep) — Dirección.
// ⚠️ Cambio solo en fuente; falta redeploy del worker (Ag-13 con OK de Dirección).
const FUNCIONES_S2_FALLBACK = [
  "2026-07-18", "2026-07-25", "2026-08-01", "2026-08-08",
  "2026-08-15", "2026-08-22", "2026-08-29", "2026-09-05",
  "2026-09-12", "2026-09-19"
];

const TEATRO_ID = "wilberto"; // prefijo real en KV (TEATRO_ALIASES mapea gorila→wilberto en main worker)
const AFORO_DEFAULT = 280;    // butacas vendibles por default

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    // Health check sin auth
    if (url.pathname === "/health") {
      return Response.json({ ok: true, worker: "elgorila-reporte", ts: new Date().toISOString() }, { headers: CORS_HEADERS });
    }

    // Solo GET /api/reporte
    if (url.pathname !== "/api/reporte") {
      return Response.json({ error: "Not found" }, { status: 404, headers: CORS_HEADERS });
    }

    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: CORS_HEADERS });
    }

    if (request.method !== "GET") {
      return Response.json({ error: "Method not allowed" }, { status: 405, headers: CORS_HEADERS });
    }

    // Auth: Bearer token
    const authHeader = request.headers.get("Authorization") || "";
    const token = authHeader.replace("Bearer ", "").trim();
    if (!env.REPORTE_TOKEN || token !== env.REPORTE_TOKEN) {
      return Response.json({ error: "Unauthorized" }, { status: 401, headers: CORS_HEADERS });
    }

    try {
      // 1. Obtener lista de funciones desde INVENTARIO KV (clave: gorila:funciones:activas)
      //    Si no existe, usar las fechas hardcodeadas de S2.
      let funciones = [];
      try {
        // Lee wilberto:funciones:activas (mismo prefix que usa el main worker vía TEATRO_ALIASES)
        const funcionesRaw = await env.INVENTARIO.get(`${TEATRO_ID}:funciones:activas`);
        if (funcionesRaw) {
          const parsed = JSON.parse(funcionesRaw);
          // Acepta tanto array de strings ["2026-07-18", ...]
          // como array de objetos [{ fecha_iso: "2026-07-18" }, ...]
          if (Array.isArray(parsed)) {
            funciones = parsed.map(f => typeof f === "string" ? f : (f.fecha_iso || f.fecha || null)).filter(Boolean);
          }
        }
      } catch (_) {}

      if (!funciones || funciones.length === 0) {
        funciones = FUNCIONES_S2_FALLBACK;
      }

      // 2. Filtros de fecha
      const desde = url.searchParams.get("desde");
      const hasta = url.searchParams.get("hasta");
      const soloFuncion = url.searchParams.get("funcion");

      let funcionesFiltradas = funciones;
      if (soloFuncion) {
        funcionesFiltradas = funciones.filter(f => f === soloFuncion);
      } else {
        if (desde) funcionesFiltradas = funcionesFiltradas.filter(f => f >= desde);
        if (hasta) funcionesFiltradas = funcionesFiltradas.filter(f => f <= hasta);
      }

      // 3. Leer datos de INVENTARIO KV para cada función (clave: gorila:funcion:{fecha})
      const hoy = new Date().toISOString().split("T")[0];
      const resultadosPorFuncion = [];
      let totalVendidos = 0;
      let totalIngresos = 0;
      const totalPorTipo = {};

      for (const fecha of funcionesFiltradas) {
        const kvKey = `${TEATRO_ID}:funcion:${fecha}`;
        let raw = null;
        try {
          raw = await env.INVENTARIO.get(kvKey);
        } catch (_) {}

        if (!raw) {
          // Función sin datos (futura o sin ventas registradas)
          resultadosPorFuncion.push({
            fecha,
            estado: fecha > hoy ? "futura" : "sin_datos",
            vendidos: 0,
            aforo: AFORO_DEFAULT,
            ocupacion_pct: 0,
            ingresos_mxn: 0,
            por_tipo: {},
          });
          continue;
        }

        let datos;
        try {
          datos = JSON.parse(raw);
        } catch (_) {
          resultadosPorFuncion.push({
            fecha,
            estado: "error_parse",
            vendidos: 0,
            aforo: AFORO_DEFAULT,
            ocupacion_pct: 0,
            ingresos_mxn: 0,
            por_tipo: {},
          });
          continue;
        }

        // Estructura KV INVENTARIO (fix 2026-07-01):
        //   { version, bloqueado, holds, secciones: { [secId]: { total, vendidos, reservados } } }
        // Importante: sumar TODAS las secciones sin filtrar por nombre (bug vendidos=0 si filtras).
        let vendidos = 0;
        let aforo = 0;

        if (datos.secciones && typeof datos.secciones === "object") {
          for (const sec of Object.values(datos.secciones)) {
            vendidos += (sec.vendidos || 0);
            aforo += (sec.total || 0);
          }
          if (aforo === 0) aforo = AFORO_DEFAULT;
        } else {
          // Estructura legada plana (pre-migración)
          vendidos = datos.vendidos || 0;
          aforo = datos.aforo || datos.capacidad || datos.total || AFORO_DEFAULT;
        }

        const ocupacion_pct = aforo > 0 ? Math.round((vendidos / aforo) * 1000) / 10 : 0;

        totalVendidos += vendidos;
        // ingresos no se almacenan en INVENTARIO — Stripe los tiene. Dejamos 0.

        resultadosPorFuncion.push({
          fecha,
          estado: fecha < hoy ? "pasada" : fecha === hoy ? "hoy" : "futura",
          vendidos,
          aforo,
          ocupacion_pct,
          ingresos_mxn: 0,   // disponible solo vía Stripe, no en KV INVENTARIO
          por_tipo: {},
        });
      }

      // 4. Métricas globales
      const totalAforo = resultadosPorFuncion.reduce((acc, f) => acc + f.aforo, 0);
      const ocupacionGlobal = totalAforo > 0
        ? Math.round((totalVendidos / totalAforo) * 1000) / 10
        : 0;

      const funcionesPasadas = resultadosPorFuncion.filter(f => f.estado === "pasada");
      const funcionesFuturas = resultadosPorFuncion.filter(f => f.estado === "futura" || f.estado === "sin_datos");
      const proximaFuncion = [...funcionesFuturas]
        .sort((a, b) => a.fecha.localeCompare(b.fecha))[0];

      const respuesta = {
        ok: true,
        generado_en: new Date().toISOString(),
        teatro_id: TEATRO_ID,
        temporada: "s2-wilberto-2026",
        filtros: { desde, hasta, funcion: soloFuncion },

        resumen_global: {
          funciones_total: funcionesFiltradas.length,
          funciones_pasadas: funcionesPasadas.length,
          funciones_futuras: funcionesFuturas.length,
          vendidos_total: totalVendidos,
          aforo_total: totalAforo,
          ocupacion_global_pct: ocupacionGlobal,
        },

        proxima_funcion: proximaFuncion ? {
          fecha: proximaFuncion.fecha,
          vendidos: proximaFuncion.vendidos,
          aforo: proximaFuncion.aforo,
          ocupacion_pct: proximaFuncion.ocupacion_pct,
          dias_restantes: Math.ceil(
            (new Date(proximaFuncion.fecha + "T00:00:00-06:00") - new Date()) / (1000 * 60 * 60 * 24)
          ),
        } : null,

        por_funcion: resultadosPorFuncion,
      };

      return Response.json(respuesta, { headers: CORS_HEADERS });

    } catch (err) {
      console.error("Error en /api/reporte:", err);
      return Response.json(
        { ok: false, error: "Error interno", detalle: err.message },
        { status: 500, headers: CORS_HEADERS }
      );
    }
  },
};
