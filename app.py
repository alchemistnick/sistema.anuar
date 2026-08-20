import streamlit as st
import requests
import base64

st.set_page_config(
    page_title="Sistema Integral de Gestión - MNU",
    page_icon="🇺🇳",
    layout="wide"
)

API_URL = "https://script.google.com/macros/s/AKfycbzCGIacvzBScHWMVOcXJGF-f01asxtpR7Xks6U1VojuAlMpjZu0LB_uG8xaJDfekJU4Rw/exec"

st.title("🇺🇳 Plataforma Integral de Gestión de Modelos ONU")

CONFIG_MODELOS = {
    f"MUNEJEMPLO{i}": f"MUNEJEMPLO_{i}" for i in range(1, 11)
}

st.sidebar.markdown("### 🌐 Selección de Evento")
modelo_seleccionado = st.sidebar.selectbox("Elegí el Modelo a Gestionar:", list(CONFIG_MODELOS.keys()))
id_modelo_actual = CONFIG_MODELOS[modelo_seleccionado]

st.sidebar.markdown("---")

menu = st.sidebar.radio(
    "Navegación",
    [
        "Preinscripción Escuela", 
        "Cargar Comprobante", 
        "Carga de Nómina y Fichas",
        "Panel Secretariado (Admin)"
    ]
)

# ---------------------------------------------------------
# MÓDULO 1: PREINSCRIPCIÓN
# ---------------------------------------------------------
if menu == "Preinscripción Escuela":
    st.subheader(f"Ficha de Inscripción por Escuela - {modelo_seleccionado}")
    
    with st.form("form_registro_unificado"):
        colegio = st.text_input("Nombre de la Institución / Colegio")
        docente = st.text_input("Docente / Tutor Acompañante")
        email = st.text_input("Correo Electrónico de Contacto")
        clave = st.text_input("Creá una Clave Secreta para el Portal", type="password")
        
        st.markdown("---")
        st.markdown("#### Seleccioná la cantidad de Delegaciones por Modalidad")
        
        col1, col2 = st.columns(2)
        with col1:
            del_5 = st.number_input("Sin CS ni ECOSOC (5 delegados)", min_value=0, max_value=5, value=0, key=f"{id_modelo_actual}_del5")
            del_7_eco = st.number_input("Sin CS con ECOSOC (7 delegados)", min_value=0, max_value=5, value=0, key=f"{id_modelo_actual}_del7eco")
            del_9_comp = st.number_input("Con CS y ECOSOC (9 delegados)", min_value=0, max_value=2, value=0, key=f"{id_modelo_actual}_del9")
        with col2:
            del_7_cs = st.number_input("Con CS sin ECOSOC (7 delegados)", min_value=0, max_value=2, value=0, key=f"{id_modelo_actual}_del7cs")
            del_davos = st.number_input("Foro de Davos (Unipersonales)", min_value=0, max_value=5, value=0, key=f"{id_modelo_actual}_davos")
            del_prensa = st.number_input("Comité de Prensa (3 delegados)", min_value=0, max_value=2, value=0, key=f"{id_modelo_actual}_prensa")
            
        tot_alumnos = (del_5 * 5) + (del_7_eco * 7) + (del_9_comp * 9) + (del_7_cs * 7) + (del_davos * 1) + (del_prensa * 3)
        desglose_str = f"5d:{del_5} | 7d_eco:{del_7_eco} | 9d:{del_9_comp} | 7d_cs:{del_7_cs} | davos:{del_davos} | prensa:{del_prensa}"

        st.info(f"📊 **Total de participantes a inscribir en la nómina:** {tot_alumnos} personas.")
        
        submitted = st.form_submit_button("Enviar Preinscripción")
        
        if submitted:
            if not colegio or not docente or not email or not clave:
                st.error("Por favor completá los datos institucionales obligatorios.")
            elif tot_alumnos == 0:
                st.warning("Debes seleccionar al menos 1 delegación en alguna modalidad.")
            else:
                payload = {
                    "action": "REGISTRAR_DELEGACION",
                    "data": {
                        "id_modelo": id_modelo_actual,
                        "nombre_colegio": colegio,
                        "docente_cargo": docente,
                        "email_contacto": email,
                        "secret_hash": clave,
                        "cupos_solicitados": tot_alumnos,
                        "desglose_modalidades": desglose_str
                    }
                }
                
                with st.spinner("Registrando preinscripción en el sistema..."):
                    try:
                        res = requests.post(API_URL, json=payload).json()
                        if res.get("status") == "SUCCESS":
                            st.success(f"¡Preinscripción enviada para **{modelo_seleccionado}**! ID asignado: **{res['data']['id_delegacion']}**")
                        else:
                            st.error(f"Error: {res.get('message')}")
                    except Exception as e:
                        st.error(f"Error de conexión: {e}")

# ---------------------------------------------------------
# MÓDULO 2: CARGA DE COMPROBANTES DE PAGO
# ---------------------------------------------------------
elif menu == "Cargar Comprobante":
    st.subheader(f"Subida de Comprobantes - {modelo_seleccionado}")
    
    id_delegacion = st.text_input("Ingresá tu ID de Delegación (Ej: DEL-001)")
    monto = st.number_input("Monto Transferido ($)", min_value=100)
    archivo = st.file_uploader("Adjuntá el comprobante (JPG, PNG o PDF)", type=["jpg", "png", "pdf"])
    
    if st.button("Subir Comprobante"):
        if not id_delegacion or not archivo:
            st.warning("Completá tu ID y adjuntá el archivo.")
        else:
            bytes_file = archivo.read()
            base64_file = base64.b64encode(bytes_file).decode('utf-8')
            
            payload = {
                "action": "SUBIR_COMPROBANTE",
                "data": {
                    "id_modelo": id_modelo_actual,
                    "id_delegacion": id_delegacion,
                    "monto": monto,
                    "file_name": archivo.name,
                    "mime_type": archivo.type,
                    "base64_file": base64_file
                }
            }
            
            with st.spinner("Subiendo archivo a Google Drive..."):
                try:
                    res = requests.post(API_URL, json=payload).json()
                    if res.get("status") == "SUCCESS":
                        st.success("Comprobante subido correctamente. En revisión por el Secretariado.")
                    else:
                        st.error(f"Error al subir: {res.get('message')}")
                except Exception as e:
                    st.error(f"Error de conexión: {e}")

# ---------------------------------------------------------
# MÓDULO 3: NÓMINA (SALUDO PERSONALIZADO Y CASILLEROS EXACTOS)
# ---------------------------------------------------------
elif menu == "Carga de Nómina y Fichas":
    st.subheader(f"Carga de Nómina y Fichas Médicas / Permisos - {modelo_seleccionado}")
    
    with st.spinner("Cargando delegaciones habilitadas..."):
        try:
            res_del = requests.get(f"{API_URL}?action=GET_DELEGACIONES_APROBADAS&id_modelo={id_modelo_actual}").json()
            delegaciones_aprobadas = res_del.get("data", [])
        except Exception as e:
            delegaciones_aprobadas = []
            st.error(f"Error al consultar el servidor: {e}")

    if not delegaciones_aprobadas:
        st.warning("⚠️ No hay delegaciones con pago **APROBADO** para este modelo aún.")
    else:
        opciones_del = {f"{d['id_delegacion']} - {d['nombre_colegio']}": d for d in delegaciones_aprobadas}
        del_seleccionada_label = st.selectbox("Seleccioná tu Delegación / Escuela Aprobada:", list(opciones_del.keys()))
        delegacion_actual = opciones_del[del_seleccionada_label]
        id_delegacion_sel = delegacion_actual['id_delegacion']

        st.markdown("---")
        st.markdown("#### 🔒 Autenticación de Seguridad")
        
        col_auth1, col_auth2 = st.columns(2)
        with col_auth1:
            email_ingresado = st.text_input("Correo Electrónico de Contacto:", key=f"auth_email_{id_delegacion_sel}")
        with col_auth2:
            clave_ingresada = st.text_input("Contraseña Secreta:", type="password", key=f"auth_pass_{id_delegacion_sel}")

        if email_ingresado and clave_ingresada:
            email_valido = email_ingresado.strip().lower() == str(delegacion_actual.get('email_contacto', '')).strip().lower()
            clave_valida = clave_ingresada == str(delegacion_actual.get('secret_hash', ''))

            if email_valido and clave_valida:
                # 1. SALUDO PERSONALIZADO AL DOCENTE
                nombre_docente = delegacion_actual.get('docente_cargo', 'Docente/Tutor')
                nombre_colegio = delegacion_actual.get('nombre_colegio', '')
                
                st.success(f"👋 **¡Hola, {nombre_docente}!** Bienvenido/a al portal de carga de **{nombre_colegio}**.")
                
                # 2. CARGA DE ASIGNACIONES PARAMETRIZADAS
                try:
                    res_asig = requests.get(f"{API_URL}?action=GET_ASIGNACIONES_DELEGACION&id_delegacion={id_delegacion_sel}").json()
                    asignaciones = res_asig.get("data", [])
                except Exception as e:
                    asignaciones = []
                    st.error(f"Error al consultar asignaciones: {e}")

                if not asignaciones:
                    st.info("ℹ️ Tu pago está APROBADO, pero el Secretariado todavía no asignó la matriz de países/comités a tu delegación.")
                else:
                    cant_cupos = len(asignaciones)
                    st.markdown(f"📋 **Tenés asignados {cant_cupos} lugares/representaciones en total.** A continuación podés cargar a los alumnos participantes:")
                    
                    # 3. LISTADO EXACTO DE CASILLEROS PARAMETRIZADOS
                    for idx, asig in enumerate(asignaciones, 1):
                        cargo_label = f"Lugar #{idx}: {asig.get('organo', 'Comité')} - {asig.get('pais', 'País/Representación')}"
                        
                        with st.expander(f"📌 {cargo_label}", expanded=False):
                            with st.form(f"form_participante_{id_delegacion_sel}_{idx}", clear_on_submit=True):
                                col1, col2 = st.columns(2)
                                with col1:
                                    nombre_completo = st.text_input("Nombre y Apellido del Participante", key=f"nom_{idx}")
                                    dni = st.text_input("DNI / Documento de Identidad", key=f"dni_{idx}")
                                    rol_mnu = st.selectbox("Rol", ["DELEGADO", "AUTORIDAD", "PRENSA"], key=f"rol_{idx}")
                                
                                with col2:
                                    alergias = st.text_area("Alergias / Dieta Especial / Indicaciones Médicas", value="Ninguna", key=f"ale_{idx}")
                                
                                st.markdown("##### Adjuntar Documentación")
                                col_doc1, col_doc2 = st.columns(2)
                                with col_doc1:
                                    archivo_ficha = st.file_uploader("Ficha Médica Firmada", type=["pdf", "jpg", "png"], key=f"ficha_{idx}")
                                with col_doc2:
                                    archivo_autorizacion = st.file_uploader("Autorización de Imagen / Permiso", type=["pdf", "jpg", "png"], key=f"aut_{idx}")
                                    
                                submitted = st.form_submit_button(f"Guardar {cargo_label}")
                                
                                if submitted:
                                    if not nombre_completo or not dni:
                                        st.error("Completá Nombre y DNI.")
                                    else:
                                        b64_ficha, mime_ficha, ext_ficha = "", "", ""
                                        if archivo_ficha:
                                            b64_ficha = base64.b64encode(archivo_ficha.read()).decode('utf-8')
                                            mime_ficha = archivo_ficha.type
                                            ext_ficha = archivo_ficha.name.split('.')[-1]

                                        b64_aut, mime_aut, ext_aut = "", "", ""
                                        if archivo_autorizacion:
                                            b64_aut = base64.b64encode(archivo_autorizacion.read()).decode('utf-8')
                                            mime_aut = archivo_autorizacion.type
                                            ext_aut = archivo_autorizacion.name.split('.')[-1]

                                        payload = {
                                            "action": "GUARDAR_NOMINA",
                                            "data": {
                                                "id_modelo": id_modelo_actual,
                                                "id_delegacion": id_delegacion_sel,
                                                "nombre_completo": nombre_completo,
                                                "dni": dni,
                                                "rol_mnu": f"{rol_mnu} ({asig.get('organo')} - {asig.get('pais')})",
                                                "alergias_medicas": alergias,
                                                "base64_ficha": b64_ficha,
                                                "mime_ficha": mime_ficha,
                                                "ext_ficha": ext_ficha,
                                                "base64_autorizacion": b64_aut,
                                                "mime_autorizacion": mime_aut,
                                                "ext_autorizacion": ext_aut
                                            }
                                        }

                                        with st.spinner("Guardando datos y archivos..."):
                                            try:
                                                res = requests.post(API_URL, json=payload).json()
                                                if res.get("status") == "SUCCESS":
                                                    st.success(f"¡Cargado con éxito para **{cargo_label}**!")
                                                else:
                                                    st.error(f"Error: {res.get('message')}")
                                            except Exception as e:
                                                st.error(f"Error de conexión: {e}")
            else:
                st.error("❌ El correo o la contraseña ingresados son incorrectos para esta delegación.")
        else:
            st.info("👈 Por favor ingresá las credenciales para acceder a la lista de participantes asignados.")

# ---------------------------------------------------------
# MÓDULO 4: PANEL ADMIN / SECRETARIADO
# ---------------------------------------------------------
elif menu == "Panel Secretariado (Admin)":
    st.subheader(f"Panel de Control - {modelo_seleccionado}")
    
    admin_pass = st.text_input("Contraseña de Administrador", type="password")
    
    if admin_pass == "Secretaria2026":
        tab1, tab2 = st.tabs(["Revisión de Pagos", "Revisión de Fichas/Nóminas"])
        
        with tab1:
            st.markdown(f"### Comprobantes Pendientes ({modelo_seleccionado})")
            if st.button("Actualizar Lista de Pagos"):
                st.rerun()
                
            try:
                res = requests.get(f"{API_URL}?action=GET_PAGOS_PENDIENTES").json()
                pagos = res.get("data", [])
                
                pagos_filtrados = [p for p in pagos if p.get("id_modelo") == id_modelo_actual or not p.get("id_modelo")]
                
                if not pagos_filtrados:
                    st.success(f"No hay pagos pendientes para {modelo_seleccionado}.")
                else:
                    for pago in pagos_filtrados:
                        with st.expander(f"Pago {pago['id_pago']} - Delegación: {pago['id_delegacion']} - ${pago['monto']}"):
                            col_a, col_b = st.columns([2, 1])
                            with col_a:
                                st.write(f"**Fecha Subida:** {pago['fecha_subida']}")
                                if pago.get('drive_file_url') and pago['drive_file_url'] != "-":
                                    st.markdown(f"[📄 Ver Comprobante en Google Drive]({pago['drive_file_url']})", unsafe_allow_html=True)
                            
                            with col_b:
                                if st.button("Aprobar Pago", key=f"app_{pago['id_pago']}"):
                                    payload = {
                                        "action": "CAMBIAR_ESTADO_PAGO",
                                        "usuario": "ADMIN",
                                        "data": {"id_pago": pago['id_pago'], "nuevo_estado": "APROBADO"}
                                    }
                                    r = requests.post(API_URL, json=payload).json()
                                    if r.get("status") == "SUCCESS":
                                        st.success("Pago Aprobado")
                                        st.rerun()

                                if st.button("Rechazar Pago", key=f"rej_{pago['id_pago']}"):
                                    payload = {
                                        "action": "CAMBIAR_ESTADO_PAGO",
                                        "usuario": "ADMIN",
                                        "data": {"id_pago": pago['id_pago'], "nuevo_estado": "RECHAZADO"}
                                    }
                                    r = requests.post(API_URL, json=payload).json()
                                    if r.get("status") == "SUCCESS":
                                        st.warning("Pago Rechazado")
                                        st.rerun()
            except Exception as e:
                st.error(f"Error al cargar pagos: {e}")

        with tab2:
            st.info("Vista de revisión de fichas médicas y autorizaciones.")
            
    elif admin_pass:
        st.error("Contraseña incorrecta.")
