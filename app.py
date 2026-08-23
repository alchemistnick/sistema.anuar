import streamlit as st
import requests
import base64

st.set_page_config(
    page_title="Gestión MNU - Portal Escuelas",
    page_icon="🇺🇳",
    layout="wide"
)

# NUEVA URL DE LA API DE APPS SCRIPT ACTUALIZADA
API_URL = "/**
 * SISTEMA INTEGRAL MONUCBA / MNU 2026 - BACKEND API (Google Apps Script)
 */

function doGet(e) {
  try {
    const action = e.parameter.action;
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    
    if (action === "PING") {
      return responderJSON({ status: "SUCCESS", message: "API activa y conectada" });
    }

    if (action === "GET_MODELOS_ACTIVOS") {
      const sheet = ss.getSheetByName("PARAMETROS_MODELOS");
      if (!sheet) return responderJSON({ status: "ERROR", message: "Falta la solapa PARAMETROS_MODELOS" });
      const data = obtenerDatosTabla(sheet);
      const activos = data.filter(m => String(m.activo).toUpperCase() === "TRUE");
      return responderJSON({ status: "SUCCESS", data: activos });
    }

    if (action === "GET_MODALIDADES_MODELO") {
      const idModelo = e.parameter.id_modelo;
      const sheet = ss.getSheetByName("MODALIDADES_MODELO");
      if (!sheet) return responderJSON({ status: "SUCCESS", data: [] });
      const data = obtenerDatosTabla(sheet);
      const filtrados = data.filter(m => String(m.id_modelo).trim() === String(idModelo).trim());
      return responderJSON({ status: "SUCCESS", data: filtrados });
    }

    if (action === "GET_PAGOS_PENDIENTES") {
      const sheet = ss.getSheetByName("PAGOS");
      if (!sheet) return responderJSON({ status: "SUCCESS", data: [] });
      const data = obtenerDatosTabla(sheet);
      const pendientes = data.filter(row => String(row.estado_pago || "").toUpperCase() === "PENDIENTE");
      return responderJSON({ status: "SUCCESS", data: pendientes });
    }

    if (action === "GET_TODOS_PAGOS") {
      const sheet = ss.getSheetByName("PAGOS");
      if (!sheet) return responderJSON({ status: "SUCCESS", data: [] });
      const data = obtenerDatosTabla(sheet);
      return responderJSON({ status: "SUCCESS", data: data });
    }

    if (action === "GET_TODAS_DELEGACIONES") {
      const idModelo = e.parameter.id_modelo;
      const sheetDel = ss.getSheetByName("DELEGACIONES");
      if (!sheetDel) return responderJSON({ status: "SUCCESS", data: [] });
      const delegaciones = obtenerDatosTabla(sheetDel);
      
      const filtradas = idModelo 
        ? delegaciones.filter(d => String(d.id_modelo || "").trim().toUpperCase() === String(idModelo).trim().toUpperCase()) 
        : delegaciones;

      return responderJSON({ status: "SUCCESS", data: filtradas });
    }

    if (action === "GET_ASIGNACIONES_DELEGACION") {
      const idDelegacion = String(e.parameter.id_delegacion || "").trim().toUpperCase();
      const sheetAsig = ss.getSheetByName("ASIGNACIONES");
      if (!sheetAsig) return responderJSON({ status: "SUCCESS", data: [] });
      
      const rows = sheetAsig.getDataRange().getValues();
      if (rows.length < 2) return responderJSON({ status: "SUCCESS", data: [] });

      let resultados = [];
      for (let i = 1; i < rows.length; i++) {
        const row = rows[i];
        const idAsig = String(row[0] || "").trim();
        const organo = String(row[1] || "").trim();
        const pais = String(row[2] || "").trim();
        const idDelAsig = String(row[3] || "").trim().toUpperCase();
        const idMod = String(row[4] || "").trim();

        if (idDelAsig === idDelegacion || idDelAsig.includes(idDelegacion)) {
          if (idAsig !== "") {
            resultados.push({
              id_asignacion: idAsig,
              organo: organo,
              pais: pais,
              id_delegacion_asignada: idDelAsig,
              id_modelo: idMod
            });
          }
        }
      }

      return responderJSON({ status: "SUCCESS", data: resultados });
    }

    if (action === "GET_TODAS_NOMINAS") {
      const idModelo = e.parameter.id_modelo;
      const sheetNom = ss.getSheetByName("NOMINAS");
      if (!sheetNom) return responderJSON({ status: "SUCCESS", data: [] });
      
      const rows = sheetNom.getDataRange().getValues();
      if (rows.length < 2) return responderJSON({ status: "SUCCESS", data: [] });

      let nominasList = [];
      for (let i = 1; i < rows.length; i++) {
        const r = rows[i];
        if (!r[0]) continue;

        nominasList.push({
          id_delegado: r[0],
          id_delegacion: String(r[1] || "").trim(),
          id_asignacion: r[2] || "-",
          rol_mnu: r[3] || "-",
          nombre: r[4] || "",
          apellido: r[5] || "",
          dni: r[6] || "",
          alergias_medicas: r[7] || "Ninguna",
          ficha_medica_id: r[8] || "-",
          autorizacion_id: r[9] || "-",
          id_modelo: r[10] || "GENERAL"
        });
      }

      const filtradas = idModelo ? nominasList.filter(n => String(n.id_modelo).trim().toUpperCase() === String(idModelo).trim().toUpperCase()) : nominasList;
      return responderJSON({ status: "SUCCESS", data: filtradas });
    }

    return responderJSON({ status: "ERROR", message: "Acción GET no válida" });
    
  } catch (err) {
    return responderJSON({ status: "ERROR", message: err.toString() });
  }
}

function doPost(e) {
  const lock = LockService.getScriptLock();
  
  if (lock.tryLock(10000)) {
    try {
      const payload = JSON.parse(e.postData.contents);
      const action = payload.action;
      const ss = SpreadsheetApp.getActiveSpreadsheet();

      if (action === "REGISTRAR_DELEGACION") {
        const res = registrarDelegacion(ss, payload.data);
        return responderJSON({ status: "SUCCESS", data: res });
      }

      if (action === "CAMBIAR_ESTADO_PAGO") {
        const sheet = ss.getSheetByName("PAGOS");
        const idPago = String(payload.data.id_pago).trim();
        const nuevoEstado = String(payload.data.nuevo_estado).trim().toUpperCase();
        
        const rows = sheet.getDataRange().getValues();
        let headerIdx = 0;
        if (String(rows[0][0]).toLowerCase().includes("columna")) headerIdx = 1;
        
        const headers = rows[headerIdx];
        let colEstadoIdx = headers.findIndex(h => String(h).trim().toLowerCase() === "estado_pago" || String(h).trim().toLowerCase() === "estado");
        if (colEstadoIdx === -1) colEstadoIdx = 5;

        let filaEncontrada = -1;
        let idDelegacionAsociada = "";
        let montoPago = "";

        for (let i = headerIdx + 1; i < rows.length; i++) {
          if (String(rows[i][0]).trim() === idPago) {
            filaEncontrada = i + 1;
            idDelegacionAsociada = String(rows[i][1]).trim();
            montoPago = rows[i][2];
            break;
          }
        }

        if (filaEncontrada !== -1) {
          sheet.getRange(filaEncontrada, colEstadoIdx + 1).setValue(nuevoEstado);

          if (idDelegacionAsociada) {
            const sheetDel = ss.getSheetByName("DELEGACIONES");
            const delegaciones = obtenerDatosTabla(sheetDel);
            const del = delegaciones.find(d => String(d.id_delegacion).trim().toUpperCase() === idDelegacionAsociada.toUpperCase());

            if (del && del.docente_email) {
              const asunto = `Actualización de Estado de Pago (${idPago}) - Modelos ONU`;
              const cuerpoHtml = `
                <div style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
                  <h2 style="color: ${nuevoEstado === 'APROBADO' ? '#27ae60' : '#c0392b'};">Estado de Pago: ${nuevoEstado}</h2>
                  <p>Estimado/a <b>${del.docente_apellido_nombre}</b>,</p>
                  <p>El pago de la institución <b>${del.nombre_colegio}</b> por un monto de $${montoPago} fue actualizado a: <b>${nuevoEstado}</b>.</p>
                  ${nuevoEstado === 'APROBADO' ? '<p>🎉 ¡Ya podés ingresar a la plataforma con tu correo y contraseña para ver tus asignaciones!</p>' : ''}
                  <p>Atentamente,<br><b>Secretariado - Modelos ONU</b></p>
                </div>
              `;
              enviarMailSeguro(ss, del.docente_email, asunto, cuerpoHtml);
            }
          }
          return responderJSON({ status: "SUCCESS", message: `Pago actualizado` });
        }
        return responderJSON({ status: "ERROR", message: "Pago no encontrado" });
      }

      if (action === "SUBIR_COMPROBANTE_PAGO") {
        const sheetDel = ss.getSheetByName("DELEGACIONES");
        const delegaciones = obtenerDatosTabla(sheetDel);
        const del = delegaciones.find(d => 
          String(d.id_delegacion).trim().toUpperCase() === String(payload.data.id_delegacion).trim().toUpperCase() && 
          String(d.secret_hash).trim() === String(payload.data.secret_hash).trim()
        );

        if (!del) return responderJSON({ status: "ERROR", message: "Código o clave incorrecta." });

        const folder = DriveApp.getRootFolder();
        const blob = Utilities.newBlob(Utilities.base64Decode(payload.data.file_base64), payload.data.file_mime, payload.data.file_name);
        const file = folder.createFile(blob);
        file.setSharing(DriveApp.Access.ANYONE_WITH_LINK, DriveApp.Permission.VIEW);

        const sheetPagos = ss.getSheetByName("PAGOS");
        const idPago = "PAGO-" + String(sheetPagos.getLastRow() + 1).padStart(4, '0');

        sheetPagos.appendRow([
          idPago, del.id_delegacion, payload.data.monto, file.getId(), file.getUrl(), "PENDIENTE", new Date().toISOString(), "", del.id_modelo || "GENERAL"
        ]);

        return responderJSON({ status: "SUCCESS", message: "Comprobante subido." });
      }

      if (action === "GUARDAR_PARTICIPANTE_NOMINA") {
        const sheetDel = ss.getSheetByName("DELEGACIONES");
        const delegaciones = obtenerDatosTabla(sheetDel);
        const del = delegaciones.find(d => 
          String(d.id_delegacion).trim().toUpperCase() === String(payload.data.id_delegacion).trim().toUpperCase() && 
          String(d.secret_hash).trim() === String(payload.data.secret_hash).trim()
        );

        if (!del) return responderJSON({ status: "ERROR", message: "Autenticación fallida." });

        const folder = DriveApp.getRootFolder();
        let fichaId = "-", autId = "-";

        if (payload.data.ficha_b64) {
          const fileF = folder.createFile(Utilities.newBlob(Utilities.base64Decode(payload.data.ficha_b64), payload.data.ficha_mime, payload.data.ficha_name));
          fichaId = fileF.getId();
        }
        if (payload.data.aut_b64) {
          const fileA = folder.createFile(Utilities.newBlob(Utilities.base64Decode(payload.data.aut_b64), payload.data.aut_mime, payload.data.aut_name));
          autId = fileA.getId();
        }

        const sheetNom = ss.getSheetByName("NOMINAS");
        const idDelegado = "DELG-" + String(sheetNom.getLastRow() + 1).padStart(4, '0');

        sheetNom.appendRow([
          idDelegado, del.id_delegacion, payload.data.id_asignacion || "-", payload.data.rol_mnu || "-", payload.data.nombre, payload.data.apellido, payload.data.dni, payload.data.alergias_medicas || "Ninguna", fichaId, autId, payload.data.id_modelo || "GENERAL"
        ]);

        return responderJSON({ status: "SUCCESS", message: "Participante registrado" });
      }

      if (action === "CONFIRMAR_CARGA_DOCUMENTACION") {
        const sheetDel = ss.getSheetByName("DELEGACIONES");
        const rows = sheetDel.getDataRange().getValues();
        let filaEncontrada = -1;

        for (let i = 1; i < rows.length; i++) {
          if (String(rows[i][0]).trim().toUpperCase() === String(payload.data.id_delegacion).trim().toUpperCase() &&
              String(rows[i][8]).trim() === String(payload.data.secret_hash).trim()) {
            filaEncontrada = i + 1;
            break;
          }
        }

        if (filaEncontrada !== -1) {
          sheetDel.getRange(filaEncontrada, 11).setValue("DOCUMENTACION_COMPLETA");
          return responderJSON({ status: "SUCCESS", message: "Documentación confirmada." });
        }
        return responderJSON({ status: "ERROR", message: "Credenciales inválidas." });
      }

      if (action === "APROBAR_LEGAJO_ESCUELA") {
        const sheetDel = ss.getSheetByName("DELEGACIONES");
        const idDel = String(payload.data.id_delegacion).trim().toUpperCase();
        
        const rowsDel = sheetDel.getDataRange().getValues();
        let filaDel = -1;
        let infoEscuela = null;

        for (let i = 1; i < rowsDel.length; i++) {
          if (String(rowsDel[i][0]).trim().toUpperCase() === idDel) {
            filaDel = i + 1;
            infoEscuela = {
              nombre: rowsDel[i][1],
              responsable: rowsDel[i][5],
              email: rowsDel[i][6]
            };
            break;
          }
        }

        if (filaDel !== -1) {
          sheetDel.getRange(filaDel, 11).setValue("APROBADO_FINAL");

          const sheetNom = ss.getSheetByName("NOMINAS");
          const rowsNom = sheetNom.getDataRange().getValues();
          let alumnosAprobados = [];

          for (let j = 1; j < rowsNom.length; j++) {
            if (String(rowsNom[j][1]).trim().toUpperCase() === idDel) {
              alumnosAprobados.push({
                nombre: rowsNom[j][4],
                apellido: rowsNom[j][5],
                dni: rowsNom[j][6],
                banca: rowsNom[j][3]
              });
            }
          }

          if (infoEscuela && infoEscuela.email) {
            let listaHtml = "";
            alumnosAprobados.forEach((a) => {
              listaHtml += `<li><b>${a.nombre} ${a.apellido}</b> (DNI: ${a.dni}) — Banca: <i>${a.banca}</i></li>`;
            });

            const asunto = `¡Legajo Aprobado y Validado! - Modelos ONU (${idDel})`;
            const cuerpoHtml = `
              <div style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
                <h2 style="color: #27ae60;">¡Documentación y Legajo Aprobados Finales!</h2>
                <p>Estimado/a <b>${infoEscuela.responsable}</b>,</p>
                <p>El equipo de secretariado ha auditado y aprobado de forma definitiva la documentación y los legajos de la institución <b>${infoEscuela.nombre}</b>.</p>
                
                <div style="background-color: #f4f6f9; padding: 15px; border-left: 4px solid #27ae60; margin: 20px 0;">
                  <p style="margin: 0;"><b>Total de estudiantes acreditados en el evento:</b> ${alumnosAprobados.length}</p>
                </div>

                <h3 style="color: #2c3e50;">📋 Nómina y Bancas Aprobadas:</h3>
                <ul>
                  ${listaHtml}
                </ul>

                <p>¡Todo listo para el Modelo! Nos comunicaremos próximamente con las últimas novedades.</p>
                <p>Atentamente,<br><b>Equipo de Secretariado - Modelos ONU</b></p>
              </div>
            `;
            enviarMailSeguro(ss, infoEscuela.email, asunto, cuerpoHtml);
          }

          return responderJSON({ status: "SUCCESS", message: "Legajo aprobado y correo enviado correctamente." });
        } else {
          return responderJSON({ status: "ERROR", message: "Delegación no encontrada." });
        }
      }

      if (action === "RECHAZAR_LEGAJO_ESCUELA") {
        const sheetDel = ss.getSheetByName("DELEGACIONES");
        const idDel = String(payload.data.id_delegacion).trim().toUpperCase();
        const motivo = String(payload.data.motivo || "No especificado").trim();
        
        const rows = sheetDel.getDataRange().getValues();
        let headerIdx = 0;
        if (String(rows[0][0]).toLowerCase().includes("columna")) headerIdx = 1;
        
        const headers = rows[headerIdx].map(h => String(h).trim().toLowerCase());
        const colIdIdx = headers.findIndex(h => h.includes("id_delegacion") || h.includes("id"));
        const colEmailIdx = headers.findIndex(h => h.includes("docente_email") || h.includes("email"));
        const colNomIdx = headers.findIndex(h => h.includes("docente_apellido") || h.includes("responsable"));
        const colEscuelaIdx = headers.findIndex(h => h.includes("nombre_colegio") || h.includes("colegio"));
        const colEstadoIdx = headers.findIndex(h => h.includes("estado"));

        let filaDel = -1;
        let infoEscuela = null;

        for (let i = headerIdx + 1; i < rows.length; i++) {
          if (String(rows[i][colIdIdx >= 0 ? colIdIdx : 0]).trim().toUpperCase() === idDel) {
            filaDel = i + 1;
            infoEscuela = {
              nombre: rows[i][colEscuelaIdx >= 0 ? colEscuelaIdx : 1],
              responsable: rows[i][colNomIdx >= 0 ? colNomIdx : 5],
              email: rows[i][colEmailIdx >= 0 ? colEmailIdx : 6]
            };
            break;
          }
        }

        if (filaDel !== -1) {
          if (colEstadoIdx >= 0) {
            sheetDel.getRange(filaDel, colEstadoIdx + 1).setValue("RECHAZADO_LEGAJO");
          }

          if (infoEscuela && infoEscuela.email) {
            const asunto = `Observaciones en su Legajo - Modelos ONU (${idDel})`;
            const cuerpoHtml = `
              <div style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
                <h2 style="color: #c0392b;">⚠️ Observaciones en la Documentación</h2>
                <p>Estimado/a <b>${infoEscuela.responsable}</b>,</p>
                <p>El equipo de secretariado ha revisado la documentación y el legajo de la institución <b>${infoEscuela.nombre}</b>, y se requiere realizar correcciones.</p>
                
                <div style="background-color: #fadbd8; padding: 15px; border-left: 4px solid #c0392b; margin: 20px 0;">
                  <p style="margin: 0;"><b>Motivo / Correcciones solicitadas:</b><br>${motivo}</p>
                </div>

                <p>Por favor, ingrese nuevamente a la plataforma para actualizar los datos o archivos correspondientes.</p>
                <p>Atentamente,<br><b>Equipo de Secretariado - Modelos ONU</b></p>
              </div>
            `;
            enviarMailSeguro(ss, infoEscuela.email, asunto, cuerpoHtml);
          }

          return responderJSON({ status: "SUCCESS", message: "Legajo rechazado y correo de notificación enviado." });
        } else {
          return responderJSON({ status: "ERROR", message: "Delegación no encontrada." });
        }
      }

      return responderJSON({ status: "ERROR", message: "Acción no válida" });

    } catch (err) {
      return responderJSON({ status: "ERROR", message: err.toString() });
    } finally {
      lock.releaseLock();
    }
  } else {
    return responderJSON({ status: "TIMEOUT", message: "Servidor ocupado." });
  }
}

function enviarMailSeguro(ssParam, destinatario, asunto, cuerpoHtml) {
  const ss = ssParam || SpreadsheetApp.getActiveSpreadsheet();
  const sheetCola = ss.getSheetByName("COLA_MAILS");

  try {
    GmailApp.sendEmail(destinatario, asunto, "", { 
      htmlBody: cuerpoHtml, 
      name: "Secretariado - Modelos ONU" 
    });
  } catch (err) {
    if (sheetCola) {
      sheetCola.appendRow([destinatario, asunto, cuerpoHtml, new Date().toISOString()]);
    }
  }
}

function procesarColaMails(ss) {
  const sheetCola = ss.getSheetByName("COLA_MAILS");
  if (!sheetCola || sheetCola.getLastRow() < 2) return;

  const rows = sheetCola.getDataRange().getValues();
  let filasAEliminar = [];

  for (let i = rows.length - 1; i >= 1; i--) {
    try {
      GmailApp.sendEmail(rows[i][0], rows[i][1], "", { 
        htmlBody: rows[i][2], 
        name: "Secretariado - Modelos ONU" 
      });
      filasAEliminar.push(i + 1);
    } catch (e) {
      break;
    }
  }

  filasAEliminar.sort((a, b) => b - a).forEach(fila => sheetCola.deleteRow(fila));
}

function registrarDelegacion(ss, data) {
  const sheet = ss.getSheetByName("DELEGACIONES");
  const idDelegacion = "DEL-" + String(sheet.getLastRow()).padStart(3, '0');
  
  sheet.appendRow([
    idDelegacion, data.nombre_colegio, data.direccion_escuela, data.email_institucional, data.telefono_institucional, data.docente_apellido_nombre, data.docente_email, data.docente_telefono, data.secret_hash, data.cupos_solicitados, "REGISTRADO", data.desglose_modalidades || "", data.id_modelo || "GENERAL", data.docentes_acompanantes || 1, ""
  ]);

  const cuerpoHtml = `
    <div style="font-family: Arial, sans-serif; color: #333;">
      <h2 style="color: #0b5394;">¡Preinscripción Exitosa!</h2>
      <p>Estimado/a <b>${data.docente_apellido_nombre}</b>,</p>
      <p>Su institución <b>${data.nombre_colegio}</b> se registró correctamente.</p>
      <p><b>Código de Delegación:</b> <span style="color: #d9534f; font-size:16px;">${idDelegacion}</span></p>
      <p><b>Clave de Acceso:</b> ${data.secret_hash}</p>
    </div>
  `;
  enviarMailSeguro(ss, data.docente_email, `Preinscripción Exitosa - ${idDelegacion}`, cuerpoHtml);
  return { id_delegacion: idDelegacion };
}

function obtenerDatosTabla(sheet) {
  const rows = sheet.getDataRange().getValues();
  if (rows.length < 2) return [];
  let headerIndex = 0;
  if (String(rows[0][0]).toLowerCase().includes("columna")) headerIndex = 1;
  if (rows.length <= headerIndex + 1) return [];

  const headers = rows[headerIndex];
  return rows.slice(headerIndex + 1).map(row => {
    let obj = {};
    headers.forEach((h, i) => { if (h) obj[String(h).trim()] = row[i]; });
    return obj;
  });
}

function responderJSON(data) {
  return ContentService.createTextOutput(JSON.stringify(data)).setMimeType(ContentService.MimeType.JSON);
}

function importarAsignacionesDesdeExcel() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const idModeloDefault = "MONUCBA";

  const sheetOrigen = ss.getSheetByName("ASIGNACIONES_EXCEL");
  if (!sheetOrigen) return;

  const sheetOrganos = ss.getSheetByName("ORGANOS");
  const rowsOrganos = sheetOrganos.getDataRange().getValues();
  
  const organosMatriz = [];
  for (let i = 1; i < rowsOrganos.length; i++) {
    const r = rowsOrganos[i];
    if (r[1] || r[2]) {
      organosMatriz.push({
        fila: i + 1,
        id_modelo: String(r[0] || idModeloDefault).trim(),
        pais: String(r[1] || r[2] || "").trim(),
        organo_comite: String(r[2] || r[1] || "").trim(),
        integrantes_totales: parseInt(r[3]) || 1
      });
    }
  }

  function normalizarTexto(txt) {
    return String(txt || "").toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/\s+/g, " ").trim();
  }

  const sheetDel = ss.getSheetByName("DELEGACIONES");
  const delegaciones = obtenerDatosTabla(sheetDel);
  const mapaEscuelas = {};
  
  delegaciones.forEach(d => {
    const nom = d.nombre_colegio || d.escuela || d.institucion;
    if (nom) mapaEscuelas[normalizarTexto(nom)] = String(d.id_delegacion).trim().toUpperCase();
  });

  const rowsOrigen = sheetOrigen.getDataRange().getValues();
  let sheetAsig = ss.getSheetByName("ASIGNACIONES");
  if (!sheetAsig) sheetAsig = ss.insertSheet("ASIGNACIONES");
  sheetAsig.clear();

  let filasAsignaciones = [["id_asignacion", "organo", "pais", "id_delegacion_asignada", "id_modelo"]];
  let contadorAsig = 1;

  sheetOrganos.getRange("E2:E").clearContent();

  for (let i = 1; i < rowsOrigen.length; i++) {
    const val1 = String(rowsOrigen[i][0] || "").trim();
    const val2 = String(rowsOrigen[i][1] || "").trim();

    if (!val1 || !val2 || val1.toLowerCase().includes("colegio") || val1.toLowerCase().includes("pais")) continue;

    let colegioRaw = val1;
    let paisRaw = val2;

    if (mapaEscuelas[normalizarTexto(val2)] || !mapaEscuelas[normalizarTexto(val1)]) {
      colegioRaw = val2;
      paisRaw = val1;
    }

    const idDel = mapaEscuelas[normalizarTexto(colegioRaw)] || colegioRaw;
    const paisLimpio = paisRaw.replace(/\s*\(\d+\)/g, "").replace(/\s+\d+$/g, "").trim();

    const comitesDelPais = organosMatriz.filter(o => normalizarTexto(o.pais) === normalizarTexto(paisLimpio));

    if (comitesDelPais.length > 0) {
      comitesDelPais.forEach(item => {
        const cantBancas = parseInt(item.integrantes_totales) || 1;
        const nombreComite = item.organo_comite;

        for (let b = 1; b <= cantBancas; b++) {
          const etiqueta = cantBancas > 1 ? `${nombreComite} (Banca ${b})` : nombreComite;
          const idAsig = "ASIG-" + String(contadorAsig++).padStart(4, '0');
          
          filasAsignaciones.push([idAsig, etiqueta, item.pais, idDel, item.id_modelo]);
          sheetOrganos.getRange(item.fila, 5).setValue(idAsig);
        }
      });
    } else {
      const idAsig = "ASIG-" + String(contadorAsig++).padStart(4, '0');
      filasAsignaciones.push([idAsig, "Representación Asignada", paisLimpio, idDel, idModeloDefault]);
    }
  }

  if (filasAsignaciones.length > 1) {
    sheetAsig.getRange(1, 1, filasAsignaciones.length, 5).setValues(filasAsignaciones);
  }

  Logger.log(`✅ [Importación Exitosa] Solapas sincronizadas correctamente.`);
}"

@st.cache_data(ttl=60)
def cargar_modelos_activos():
    try:
        res = requests.get(f"{API_URL}?action=GET_MODELOS_ACTIVOS").json()
        if res.get("status") == "SUCCESS":
            modelos = res.get("data", [])
            return {m["nombre_visible"]: m["id_modelo"] for m in modelos}
        return {}
    except Exception:
        return {}

@st.cache_data(ttl=60)
def cargar_modalidades_modelo(id_modelo):
    try:
        res = requests.get(f"{API_URL}?action=GET_MODALIDADES_MODELO&id_modelo={id_modelo}").json()
        if res.get("status") == "SUCCESS":
            return res.get("data", [])
        return []
    except Exception:
        return []

@st.cache_data(ttl=30)
def cargar_todas_delegaciones_cached(id_modelo):
    try:
        res = requests.get(f"{API_URL}?action=GET_TODAS_DELEGACIONES&id_modelo={id_modelo}").json()
        if res.get("status") == "SUCCESS":
            return res.get("data", [])
        return []
    except Exception:
        return []

st.title("🇺🇳 Portal de Inscripción y Carga - Modelos ONU")

CONFIG_MODELOS = cargar_modelos_activos()

st.sidebar.markdown("### 🌐 Selección de Evento")

if not CONFIG_MODELOS:
    st.sidebar.warning("⚠️ No hay modelos activos configurados en la planilla.")
    st.stop()
else:
    modelo_seleccionado = st.sidebar.selectbox("Elegí el Modelo a Gestionar:", list(CONFIG_MODELOS.keys()))
    id_modelo_actual = CONFIG_MODELOS[modelo_seleccionado]

st.sidebar.markdown("---")

menu = st.sidebar.radio(
    "Navegación",
    [
        "1. Preinscripción Escuela", 
        "2. Cargar Comprobante", 
        "3. Carga de Nómina y Fichas"
    ]
)

# ---------------------------------------------------------
# MÓDULO 1: PREINSCRIPCIÓN ESCUELA
# ---------------------------------------------------------
if menu == "1. Preinscripción Escuela":
    st.subheader(f"Ficha de Preinscripción por Escuela - {modelo_seleccionado}")
    modalidades_evento = cargar_modalidades_modelo(id_modelo_actual)

    with st.form("form_registro_unificado"):
        st.markdown("### 🏛️ DATOS DE LA INSTITUCIÓN")
        colegio = st.text_input("Nombre de la Escuela *")
        direccion = st.text_input("Dirección (Localidad, Provincia, País) *")
        
        col_inst1, col_inst2 = st.columns(2)
        with col_inst1:
            email_inst = st.text_input("Correo electrónico institucional *")
        with col_inst2:
            tel_inst = st.text_input("Número de teléfono de la escuela *")
        
        st.markdown("---")
        st.markdown("### 👤 DATOS DEL RESPONSABLE / PROFESOR A CARGO")
        
        docente_ape_nom = st.text_input("Apellido y Nombre del Responsable *")
        
        col_doc1, col_doc2 = st.columns(2)
        with col_doc1:
            docente_email = st.text_input("Correo electrónico personal/docente (Usuario de Acceso) *")
        with col_doc2:
            docente_tel = st.text_input("Número de teléfono móvil *")

        col_sec1, col_sec2 = st.columns(2)
        with col_sec1:
            cant_docentes = st.number_input("Cantidad TOTAL de Docentes Acompañantes que asistirán:", min_value=1, max_value=10, value=1)
        with col_sec2:
            clave = st.text_input("Creá una Clave Secreta para acceder al Portal *", type="password")
        
        st.markdown("---")
        st.markdown("### 🇺🇳 DATOS DE LAS DELEGACIONES")
        
        respuestas_modalidades = {}
        tot_alumnos = 0
        
        cols = st.columns(2)
        for idx, mod in enumerate(modalidades_evento):
            col_curr = cols[idx % 2]
            with col_curr:
                lbl = f"{mod['etiqueta_visible']} ({mod['delegados_por_unidad']} delegados/unidad)"
                cant = st.number_input(
                    lbl, 
                    min_value=0, 
                    max_value=int(mod.get('max_permitido', 5)), 
                    value=0, 
                    key=f"new_{id_modelo_actual}_{mod['clave_modalidad']}"
                )
                respuestas_modalidades[mod['clave_modalidad']] = cant
                tot_alumnos += cant * int(mod['delegados_por_unidad'])
                
        desglose_str = " | ".join([f"{k}:{v}" for k, v in respuestas_modalidades.items()])

        st.info(f"📊 **Total de participantes a inscribir:** {tot_alumnos} estudiantes + {cant_docentes} docente(s) acompañante(s).")
        
        submitted = st.form_submit_button("Enviar Preinscripción")
        
        if submitted:
            if not colegio or not direccion or not email_inst or not tel_inst or not docente_ape_nom or not docente_email or not docente_tel or not clave:
                st.error("Por favor completá todos los campos obligatorios (*).")
            elif tot_alumnos == 0:
                st.warning("Debés seleccionar al menos 1 delegación en alguna modalidad.")
            else:
                payload = {
                    "action": "REGISTRAR_DELEGACION",
                    "data": {
                        "id_modelo": id_modelo_actual,
                        "nombre_colegio": colegio,
                        "direccion_escuela": direccion,
                        "email_institucional": email_inst,
                        "telefono_institucional": tel_inst,
                        "docente_apellido_nombre": docente_ape_nom,
                        "docente_email": docente_email,
                        "docente_telefono": docente_tel,
                        "docentes_acompanantes": cant_docentes,
                        "secret_hash": clave,
                        "cupos_solicitados": tot_alumnos,
                        "desglose_modalidades": desglose_str
                    }
                }
                
                with st.spinner("Registrando preinscripción..."):
                    try:
                        res = requests.post(API_URL, json=payload).json()
                        if res.get("status") == "SUCCESS":
                            st.success(f"¡Preinscripción enviada con éxito para **{modelo_seleccionado}**! Código de delegación: **{res['data']['id_delegacion']}**")
                        else:
                            st.error(f"Error: {res.get('message')}")
                    except Exception as e:
                        st.error(f"Error de conexión: {e}")

# ---------------------------------------------------------
# MÓDULO 2: CARGAR COMPROBANTE DE PAGO
# ---------------------------------------------------------
elif menu == "2. Cargar Comprobante":
    st.subheader(f"Acreditación de Pago - {modelo_seleccionado}")
    
    with st.form("form_pago"):
        id_del = st.text_input("Código de Delegación (Ej: DEL-001) *")
        clave = st.text_input("Clave Secreta de la Escuela *", type="password")
        monto = st.number_input("Monto Transferido ($) *", min_value=1.0, step=100.0)
        archivo = st.file_uploader("Adjuntar Comprobante (PDF o Imagen) *", type=["pdf", "png", "jpg", "jpeg"])
        
        btn_pago = st.form_submit_button("Subir Comprobante")
        
        if btn_pago:
            if not id_del or not clave or not archivo:
                st.error("Completá todos los campos obligatorios.")
            else:
                file_bytes = archivo.read()
                base64_file = base64.b64encode(file_bytes).decode('utf-8')
                
                payload = {
                    "action": "SUBIR_COMPROBANTE_PAGO",
                    "data": {
                        "id_delegacion": id_del.strip().upper(),
                        "secret_hash": clave,
                        "monto": monto,
                        "file_base64": base64_file,
                        "file_name": archivo.name,
                        "file_mime": archivo.type
                    }
                }
                with st.spinner("Subiendo comprobante a Drive..."):
                    try:
                        res = requests.post(API_URL, json=payload).json()
                        if res.get("status") == "SUCCESS":
                            st.success("¡Comprobante recibido! Queda en revisión por el Secretariado.")
                        else:
                            st.error(f"Error: {res.get('message')}")
                    except Exception as e:
                        st.error(f"Error de conexión: {e}")

# ---------------------------------------------------------
# MÓDULO 3: CARGA DE NÓMINA Y FICHAS (LOGIN PRIVADO + CONFIRMACIÓN)
# ---------------------------------------------------------
elif menu == "3. Carga de Nómina y Fichas":
    st.subheader(f"Nómina de Participantes y Documentación - {modelo_seleccionado}")
    
    if "escuela_sesion" not in st.session_state:
        st.markdown("Ingresá las credenciales asignadas a tu institución para acceder al sistema.")
        
        with st.form("form_login_escuela"):
            input_email = st.text_input("📧 Correo Electrónico (Docente o Institucional):")
            input_pass = st.text_input("🔑 Contraseña Secreta:", type="password")
            btn_login = st.form_submit_button("Iniciar Sesión")

        if btn_login:
            if not input_email or not input_pass:
                st.error("Por favor completá ambos campos.")
            else:
                with st.spinner("Verificando credenciales..."):
                    delegaciones = cargar_todas_delegaciones_cached(id_modelo_actual)
                    
                    escuela_encontrada = None
                    email_clean = input_email.strip().lower()

                    for e in delegaciones:
                        mail_docente = str(e.get("docente_email", "")).strip().lower()
                        mail_inst = str(e.get("email_institucional", "")).strip().lower()
                        
                        if email_clean == mail_docente or email_clean == mail_inst:
                            escuela_encontrada = e
                            break

                    if not escuela_encontrada:
                        st.error("❌ Credenciales inválidas.")
                    else:
                        clave_guardada = str(escuela_encontrada.get("secret_hash", "")).strip()
                        if input_pass.strip() != clave_guardada:
                            st.error("❌ Credenciales inválidas.")
                        else:
                            st.session_state["escuela_sesion"] = escuela_encontrada
                            st.success("¡Sesión iniciada correctamente!")
                            st.rerun()

    else:
        escuela_activa = st.session_state["escuela_sesion"]
        id_del_seleccionado = escuela_activa.get("id_delegacion")

        col_s1, col_s2 = st.columns([3, 1])
        with col_s1:
            st.info(f"🏫 Institución conectada: **{escuela_activa.get('nombre_colegio')}**")
        with col_s2:
            if st.button("Cerrar Sesión"):
                del st.session_state["escuela_sesion"]
                st.rerun()

        try:
            res_asig = requests.get(f"{API_URL}?action=GET_ASIGNACIONES_DELEGACION&id_delegacion={id_del_seleccionado}").json()
            asignaciones = res_asig.get("data", [])

            if not asignaciones:
                st.warning("Aún no se registran bancas de países asignadas para tu institución.")
            else:
                st.write(f"📋 **Bancas / Lugares Asignados ({len(asignaciones)}):**")

                for asig in asignaciones:
                    with st.expander(f"📌 {asig.get('organo')} — País / Representación: **{asig.get('pais')}**"):
                        with st.form(f"form_nom_{asig.get('id_asignacion')}"):
                            nombre = st.text_input("Nombre del Estudiante *")
                            apellido = st.text_input("Apellido del Estudiante *")
                            dni = st.text_input("DNI / Pasaporte *")
                            alergias = st.text_area("Alergias o Indicaciones Médicas", value="Ninguna")
                            
                            ficha_file = st.file_uploader("Ficha Médica (PDF/Imagen) *", type=["pdf", "png", "jpg", "jpeg"], key=f"f_{asig.get('id_asignacion')}")
                            aut_file = st.file_uploader("Autorización de Imagen (PDF/Imagen) *", type=["pdf", "png", "jpg", "jpeg"], key=f"a_{asig.get('id_asignacion')}")
                            
                            btn_nom = st.form_submit_button("Guardar Alumno")
                            
                            if btn_nom:
                                if not nombre or not apellido or not dni:
                                    st.error("Nombre, Apellido y DNI son obligatorios.")
                                else:
                                    f_b64, a_b64 = "", ""
                                    f_name, a_name = "", ""
                                    f_mime, a_mime = "", ""
                                    
                                    if ficha_file:
                                        f_b64 = base64.b64encode(ficha_file.read()).decode('utf-8')
                                        f_name = ficha_file.name
                                        f_mime = ficha_file.type
                                    if aut_file:
                                        a_b64 = base64.b64encode(aut_file.read()).decode('utf-8')
                                        a_name = aut_file.name
                                        a_mime = aut_file.type
                                        
                                    payload = {
                                        "action": "GUARDAR_PARTICIPANTE_NOMINA",
                                        "data": {
                                            "id_delegacion": id_del_seleccionado,
                                            "secret_hash": escuela_activa.get("secret_hash"),
                                            "id_modelo": id_modelo_actual,
                                            "id_asignacion": asig.get("id_asignacion"),
                                            "rol_mnu": f"{asig.get('organo')} - {asig.get('pais')}",
                                            "nombre": nombre,
                                            "apellido": apellido,
                                            "dni": dni,
                                            "alergias_medicas": alergias,
                                            "ficha_b64": f_b64, "ficha_name": f_name, "ficha_mime": f_mime,
                                            "aut_b64": a_b64, "aut_name": a_name, "aut_mime": a_mime
                                        }
                                    }
                                    res_save = requests.post(API_URL, json=payload).json()
                                    if res_save.get("status") == "SUCCESS":
                                        st.success("¡Alumno cargado con éxito!")
                                    else:
                                        st.error(f"Error: {res_save.get('message')}")

                # --- BOTÓN DE CONFIRMACIÓN DE CARGA TOTAL DE DOCUMENTACIÓN ---
                st.markdown("---")
                st.markdown("### 🏁 Finalización del Proceso")
                
                estado_actual = str(escuela_activa.get("estado", "REGISTRADO")).upper()
                
                if estado_actual == "DOCUMENTACION_COMPLETA":
                    st.success("✅ Ya confirmaste la carga total de tu documentación. El secretariado la está verificando.")
                else:
                    st.warning("⚠️ Una vez que hayas cargado a todos los participantes con sus fichas y autorizaciones, hacé clic en el botón para notificar al secretariado.")
                    if st.button("📤 Confirmar Carga Total de Documentación"):
                        payload_conf = {
                            "action": "CONFIRMAR_CARGA_DOCUMENTACION",
                            "data": {
                                "id_delegacion": id_del_seleccionado,
                                "secret_hash": escuela_activa.get("secret_hash")
                            }
                        }
                        with st.spinner("Enviando confirmación..."):
                            try:
                                res_conf = requests.post(API_URL, json=payload_conf).json()
                                if res_conf.get("status") == "SUCCESS":
                                    st.success("¡Documentación confirmada con éxito! Se ha notificado al equipo organizador.")
                                    # Actualizamos temporalmente el estado en la sesión para refrescar la vista
                                    escuela_activa["estado"] = "DOCUMENTACION_COMPLETA"
                                    st.rerun()
                                else:
                                    st.error(f"Error: {res_conf.get('message')}")
                            except Exception as e:
                                st.error(f"Error de conexión: {e}")

        except Exception as e:
            st.error(f"Error de conexión al obtener asignaciones: {e}")
