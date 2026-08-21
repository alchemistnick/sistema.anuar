/**
 * SISTEMA INTEGRAL MONUCBA / MNU 2026 - BACKEND API
 * URL Web App: "https://script.google.com/macros/s/AKfycbyM7_YhNDZdzKcrrTChJ0hfN_d7nCeQ5WC-y9Uk1VmSGyeKiyqaXxoT3mnJMYTRSqeaDQ/exec"
 */

function doGet(e) {
  try {
    const action = e.parameter.action;
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    
    if (action === "PING") {
      return responderJSON({ status: "SUCCESS", message: "API activa y lista" });
    }

    if (action === "GET_MODELOS_ACTIVOS") {
      const sheet = ss.getSheetByName("PARAMETROS_MODELOS");
      if (!sheet) {
        return responderJSON({ status: "ERROR", message: "Falta la solapa PARAMETROS_MODELOS" });
      }
      const data = obtenerDatosTabla(sheet);
      const activos = data.filter(m => String(m.activo).toUpperCase() === "TRUE");
      return responderJSON({ status: "SUCCESS", data: activos });
    }
    
    if (action === "GET_ORGANOS") {
      const idModelo = e.parameter.id_modelo;
      const sheet = ss.getSheetByName("ORGANOS");
      const data = obtenerDatosTabla(sheet);
      const filtrados = idModelo ? data.filter(row => row.id_modelo === idModelo) : data;
      return responderJSON({ status: "SUCCESS", data: filtrados });
    }

    if (action === "GET_PAISES_MATRIZ") {
      const idModelo = e.parameter.id_modelo;
      const sheet = ss.getSheetByName("ORGANOS");
      const data = obtenerDatosTabla(sheet);
      const filtrados = idModelo ? data.filter(row => row.id_modelo === idModelo) : data;
      const paisesUnicos = [...new Set(filtrados.map(item => item.pais))].filter(Boolean);
      return responderJSON({ status: "SUCCESS", data: paisesUnicos });
    }

    if (action === "GET_PAGOS_PENDIENTES") {
      const sheet = ss.getSheetByName("PAGOS");
      const data = obtenerDatosTabla(sheet);
      const pendientes = data.filter(row => row.estado_pago === "PENDIENTE");
      return responderJSON({ status: "SUCCESS", data: pendientes });
    }

    if (action === "GET_DELEGACIONES_APROBADAS") {
      const idModelo = e.parameter.id_modelo;
      const sheetPagos = ss.getSheetByName("PAGOS");
      const pagos = obtenerDatosTabla(sheetPagos);
      const sheetDel = ss.getSheetByName("DELEGACIONES");
      const delegaciones = obtenerDatosTabla(sheetDel);

      const pagosAprobados = pagos.filter(p => 
        p.estado_pago === "APROBADO" && 
        (!idModelo || p.id_modelo === idModelo)
      );
      
      const idsAprobados = pagosAprobados.map(p => p.id_delegacion);
      const delAprobadas = delegaciones.filter(d => idsAprobados.includes(d.id_delegacion));

      return responderJSON({ status: "SUCCESS", data: delAprobadas });
    }

    if (action === "GET_ASIGNACIONES_DELEGACION") {
      const idDelegacion = e.parameter.id_delegacion;
      const sheetAsig = ss.getSheetByName("ASIGNACIONES");
      const asignaciones = obtenerDatosTabla(sheetAsig);
      const delAsignaciones = asignaciones.filter(a => a.id_delegacion_asignada === idDelegacion);

      return responderJSON({ status: "SUCCESS", data: delAsignaciones });
    }

    if (action === "GET_TODAS_NOMINAS") {
      const idModelo = e.parameter.id_modelo;
      const sheetNom = ss.getSheetByName("NOMINAS");
      const nominas = obtenerDatosTabla(sheetNom);
      const filtradas = idModelo ? nominas.filter(n => n.id_modelo === idModelo) : nominas;
      
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
        registrarAuditoria(ss, payload.usuario || "SISTEMA", "DELEGACION", "REGISTRAR", res.id_delegacion, "OK");
        return responderJSON({ status: "SUCCESS", data: res });
      }
      
      if (action === "SUBIR_COMPROBANTE") {
        const res = guardarComprobanteEnDrive(ss, payload.data);
        registrarAuditoria(ss, payload.data.id_delegacion, "DELEGACION", "SUBIR_PAGO", res.id_pago, "OK");
        return responderJSON({ status: "SUCCESS", data: res });
      }

      if (action === "GUARDAR_NOMINA") {
        const res = guardarNominaYDocumentos(ss, payload.data);
        registrarAuditoria(ss, payload.data.id_delegacion, "DELEGACION", "CARGA_NOMINA", res.id_delegado, "OK");
        return responderJSON({ status: "SUCCESS", data: res });
      }

      if (action === "CAMBIAR_ESTADO_PAGO") {
        const sheet = ss.getSheetByName("PAGOS");
        const rows = sheet.getDataRange().getValues();
        for (let i = 1; i < rows.length; i++) {
          if (rows[i][0] === payload.data.id_pago) {
            sheet.getRange(i + 1, 6).setValue(payload.data.nuevo_estado);
            sheet.getRange(i + 1, 8).setValue(payload.usuario || "ADMIN");
            break;
          }
        }
        registrarAuditoria(ss, payload.usuario || "ADMIN", "ADMIN", "CAMBIAR_ESTADO_PAGO", payload.data.id_pago, payload.data.nuevo_estado);
        return responderJSON({ status: "SUCCESS" });
      }

      if (action === "ASIGNAR_PAIS_AUTOMATICO_DESDE_MATRIZ") {
        const sheetOrganos = ss.getSheetByName("ORGANOS");
        const organosMatriz = obtenerDatosTabla(sheetOrganos);
        const idModelo = payload.data.id_modelo;
        const idDelegacion = payload.data.id_delegacion;
        const paisSorteado = payload.data.pais;
        
        const configuracionPais = organosMatriz.filter(o => 
          String(o.id_modelo).trim() === String(idModelo).trim() && 
          String(o.pais).trim().toLowerCase() === String(paisSorteado).trim().toLowerCase()
        );

        if (configuracionPais.length === 0) {
          return responderJSON({ status: "ERROR", message: `El país '${paisSorteado}' no está configurado en la solapa ORGANOS para este modelo.` });
        }

        const sheetAsig = ss.getSheetByName("ASIGNACIONES");
        let agregados = 0;

        configuracionPais.forEach(item => {
          const cantidadCupos = parseInt(item.integrantes_totales) || 1;
          const organoNombre = item.organo_comite;

          for (let i = 1; i <= cantidadCupos; i++) {
            const idAsig = "ASIG-" + String(sheetAsig.getLastRow()).padStart(3, '0');
            const etiquetaComision = cantidadCupos > 1 ? `${organoNombre} (Banca ${i})` : organoNombre;

            sheetAsig.appendRow([
              idAsig,
              etiquetaComision,
              item.pais,
              idDelegacion,
              idModelo
            ]);
            agregados++;
          }
        });

        registrarAuditoria(ss, payload.usuario || "ADMIN", "ADMIN", "ASIGNAR_PAIS_MATRIZ", idDelegacion, `PAIS: ${paisSorteado} (${agregados} cupos)`);
        return responderJSON({ status: "SUCCESS", cupos_agregados: agregados });
      }

      return responderJSON({ status: "ERROR", message: "Acción POST no reconocida" });

    } catch (err) {
      return responderJSON({ status: "ERROR", message: err.toString() });
    } finally {
      lock.releaseLock();
    }
  } else {
    return responderJSON({ status: "TIMEOUT", message: "Servidor ocupado. Intente nuevamente." });
  }
}

// --- FUNCIONES AUXILIARES ---

function registrarDelegacion(ss, data) {
  const sheet = ss.getSheetByName("DELEGACIONES");
  const lastRow = sheet.getLastRow();
  const idDelegacion = "DEL-" + String(lastRow).padStart(3, '0');
  
  sheet.appendRow([
    idDelegacion,
    data.nombre_colegio,
    data.docente_cargo,
    data.email_contacto,
    data.secret_hash,
    data.cupos_solicitados,
    "REGISTRADO",
    data.desglose_modalidades || "",
    data.id_modelo || "GENERAL"
  ]);
  
  return { id_delegacion: idDelegacion };
}

function guardarComprobanteEnDrive(ss, data) {
  const sheetParams = ss.getSheetByName("PARAMETROS");
  const params = obtenerDatosTabla(sheetParams);
  const paramFolder = params.find(p => p.clave === "ID_CARPETA_DRIVE_COMPROBANTES");
  
  if (!paramFolder || !paramFolder.valor) {
    throw new Error("Falta ID_CARPETA_DRIVE_COMPROBANTES en la solapa PARAMETROS.");
  }

  const folder = DriveApp.getFolderById(paramFolder.valor);
  const blob = Utilities.newBlob(Utilities.base64Decode(data.base64_file), data.mime_type, data.file_name);
  const file = folder.createFile(blob);
  
  const sheetPagos = ss.getSheetByName("PAGOS");
  const idPago = "PAG-" + String(sheetPagos.getLastRow()).padStart(3, '0');
  
  sheetPagos.appendRow([
    idPago,
    data.id_delegacion,
    data.monto,
    file.getId(),
    file.getUrl(),
    "PENDIENTE",
    new Date().toISOString(),
    "-",
    data.id_modelo || "GENERAL"
  ]);
  
  return { id_pago: idPago, file_url: file.getUrl() };
}

function guardarNominaYDocumentos(ss, data) {
  const sheetParams = ss.getSheetByName("PARAMETROS");
  const params = obtenerDatosTabla(sheetParams);
  const paramFolder = params.find(p => p.clave === "ID_CARPETA_DRIVE_FICHAS");
  
  let folderIdFicha = paramFolder ? paramFolder.valor : "";
  if (!folderIdFicha) {
    throw new Error("Falta ID_CARPETA_DRIVE_FICHAS en la solapa PARAMETROS.");
  }

  const folder = DriveApp.getFolderById(folderIdFicha);

  let fichaId = "-";
  if (data.base64_ficha) {
    const blob = Utilities.newBlob(
      Utilities.base64Decode(data.base64_ficha), 
      data.mime_ficha, 
      `FICHA_${data.id_delegacion}_${data.dni}.${data.ext_ficha}`
    );
    fichaId = folder.createFile(blob).getId();
  }

  let autorizacionId = "-";
  if (data.base64_autorizacion) {
    const blob = Utilities.newBlob(
      Utilities.base64Decode(data.base64_autorizacion), 
      data.mime_autorizacion, 
      `AUT_${data.id_delegacion}_${data.dni}.${data.ext_autorizacion}`
    );
    autorizacionId = folder.createFile(blob).getId();
  }

  const sheetNominas = ss.getSheetByName("NOMINAS");
  const idDelegado = `${data.id_delegacion}-${String(sheetNominas.getLastRow()).padStart(2, '0')}`;
  
  sheetNominas.appendRow([
    idDelegado,
    data.id_delegacion,
    data.nombre_completo,
    data.dni,
    data.rol_mnu,
    data.alergias_medicas || "Ninguna",
    fichaId,
    autorizacionId,
    "PENDIENTE",
    false,
    data.id_modelo || "GENERAL"
  ]);

  return { id_delegado: idDelegado };
}

function registrarAuditoria(ss, usuarioId, rol, accion, idRegistro, resultado) {
  const sheet = ss.getSheetByName("AUDITORIA");
  sheet.appendRow([
    new Date().toISOString(),
    usuarioId,
    rol,
    accion,
    idRegistro,
    resultado
  ]);
}

function obtenerDatosTabla(sheet) {
  const rows = sheet.getDataRange().getValues();
  if (rows.length < 2) return [];
  const headers = rows[0];
  return rows.slice(1).map(row => {
    let obj = {};
    headers.forEach((h, i) => { obj[h] = row[i]; });
    return obj;
  });
}

function responderJSON(data) {
  return ContentService.createTextOutput(JSON.stringify(data))
    .setMimeType(ContentService.MimeType.JSON);
}
