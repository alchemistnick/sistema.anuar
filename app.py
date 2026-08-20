import streamlit as st
import requests
import base64

# Configuración de la página
st.set_page_config(
    page_title="Gestión MONUCBA 2026",
    page_icon="🇺🇳",
    layout="wide"
)

# URL de la API de Apps Script
API_URL = "https://script.google.com/macros/s/AKfycbwjrbQ5pDVLSCRTK9zAYtAsic9AbFtj6zrwa-E3C1q5aARd_dJUyWFranw9tRLOKlAlnQ/exec"

st.title("🇺🇳 Sistema Integral de Gestión - MONUCBA 2026")

# Menú lateral
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
# MÓDULO 1: PREINSCRIPCIÓN POR ESCUELA (DESGROSE MONUCBA)
# ---------------------------------------------------------
if menu == "Preinscripción Escuela":
    st.subheader("Ficha de Inscripción por Escuela - MONUCBA 2026")
    
    with st.form("form_registro_monucba"):
        colegio = st.text_input("Nombre de la Institución / Colegio")
        docente = st.text_input("Docente / Tutor Acompañante")
        email = st.text_input("Correo Electrónico de Contacto")
        clave = st.text_input("Creá una Clave Secreta para el Portal", type="password")
        
        st.markdown("---")
        st.markdown("#### Seleccioná la cantidad de Delegaciones por Modalidad")
        
        col1, col2 = st.columns(2)
        with col1:
            del_5 = st.number_input("Sin CS ni ECOSOC (5 delegados: AG1, AG3, AG6)", min_value=0, max_value=5, value=0)
            del_7_ecosoc = st.number_input("Sin CS con ECOSOC (7 delegados: AG1, AG3, AG6, ECOSOC)", min_value=0, max_value=5, value=0)
            del_9_completa = st.number_input("Con CS y ECOSOC (9 delegados: AG1, AG3, AG6, ECOSOC, CS)", min_value=0, max_value=2, value=0)
        
        with col2:
            del_7_cs = st.number_input("Con CS sin ECOSOC (7 delegados: AG1, AG3, AG6, CS)", min_value=0, max_value=2, value=0)
            del_davos = st.number_input("Foro de Davos (Unipersonales)", min_value=0, max_value=5, value=0)
            del_prensa = st.number_input("Comité de Prensa Internacional (3 delegados)", min_value=0, max_value=2, value=0)
            
        tot_alumnos = (del_5 * 5) + (del_7_ecosoc * 7) + (del_9_completa * 9) + (del_7_cs * 7) + (del_davos * 1) + (del_prensa * 3)
        st.info(f"📊 **Total de participantes a inscribir en la nómina:** {tot_alumnos} alumnos/delegados.")
        
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
                        "nombre_colegio": colegio,
                        "docente_cargo": docente,
                        "email_contacto": email,
                        "secret_hash": clave,
                        "cupos_solicitados": tot_alumnos,
                        "desglose_modalidades": f"5d:{del_5} | 7d_eco:{del_7_ecosoc} | 9d:{del_9_completa} | 7d_cs:{del_7_cs} | davos:{del_davos} | prensa:{del_prensa}"
                    }
                }
                
                with st.spinner("Registrando preinscripción en el sistema..."):
                    try:
                        res = requests.post(API_URL, json=payload).json()
                        if res.get("status") == "SUCCESS":
                            st.success(f"¡Preinscripción enviada! Guardá tu ID de Delegación: **{res['data']['id_delegacion']}**")
                        else:
                            st.error(f"Error: {res.get('message')}")
                    except Exception as e:
                        st.error(f"Error de conexión: {e}")

# ---------------------------------------------------------
# MÓDULO 2: CARGA DE COMPROBANTES DE PAGO
# ---------------------------------------------------------
elif menu == "Cargar Comprobante":
    st.subheader("Subida de Comprobantes de Transferencia")
    
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
# MÓDULO 3: CARGA DE NÓMINA Y FICHAS
# ---------------------------------------------------------
elif menu == "Carga de Nómina y Fichas":
    st.subheader("Carga de Participantes y Documentación Médica/Legal")
    st.info("Ingresá los datos de cada participante perteneciente a tu delegación.")
    
    with st.form("form_nomina", clear_on_submit=True):
        id_delegacion = st.text_input("ID de la Delegación (Ej: DEL-001)")
        
        col1, col2 = st.columns(2)
        with col1:
            nombre_completo = st.text_input("Nombre y Apellido del Participante")
            dni = st.text_input("DNI / Documento de Identidad")
            rol_mnu = st.selectbox("Rol en el Modelo", ["DELEGADO", "AUTORIDAD", "PRENSA"])
        
        with col2:
            alergias = st.text_area("Alergias / Indicaciones Médicas / Dieta Especial", value="Ninguna")
        
        st.markdown("---")
        st.markdown("#### Adjuntar Documentación (PDF, JPG, PNG)")
        
        col_doc1, col_doc2 = st.columns(2)
        with col_doc1:
            archivo_ficha = st.file_uploader("Ficha Médica Firmada", type=["pdf", "jpg", "png"], key="ficha")
        with col_doc2:
            archivo_autorizacion = st.file_uploader("Autorización de Imagen / Permiso", type=["pdf", "jpg", "png"], key="aut")
            
        submitted = st.form_submit_button("Guardar Participante")
        
        if submitted:
            if not id_delegacion or not nombre_completo or not dni:
                st.error("Completá los campos obligatorios (ID Delegación, Nombre y DNI).")
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
                        "id_delegacion": id_delegacion,
                        "nombre_completo": nombre_completo,
                        "dni": dni,
                        "rol_mnu": rol_mnu,
                        "alergias_medicas": alergias,
                        "base64_ficha": b64_ficha,
                        "mime_ficha": mime_ficha,
                        "ext_ficha": ext_ficha,
                        "base64_autorizacion": b64_aut,
                        "mime_autorizacion": mime_aut,
                        "ext_autorizacion": ext_aut
                    }
                }

                with st.spinner("Guardando participante y subiendo archivos..."):
                    try:
                        res = requests.post(API_URL, json=payload).json()
                        if res.get("status") == "SUCCESS":
                            st.success(f"¡Participante guardado con éxito! ID: **{res['data']['id_delegado']}**")
                        else:
                            st.error(f"Error al guardar: {res.get('message')}")
                    except Exception as e:
                        st.error(f"Error de conexión: {e}")

# ---------------------------------------------------------
# MÓDULO 4: PANEL ADMIN / SECRETARIADO
# ---------------------------------------------------------
elif menu == "Panel Secretariado (Admin)":
    st.subheader("Panel de Control y Revisión del Secretariado")
    
    admin_pass = st.text_input("Contraseña de Administrador", type="password")
    
    if admin_pass == "Secretaria2026":
        tab1, tab2 = st.tabs(["Revisión de Pagos", "Revisión de Fichas/Nóminas"])
        
        with tab1:
            st.markdown("### Comprobantes de Pago Pendientes")
            if st.button("Actualizar Lista de Pagos"):
                st.rerun()
                
            try:
                res = requests.get(f"{API_URL}?action=GET_PAGOS_PENDIENTES").json()
                pagos = res.get("data", [])
                
                if not pagos:
                    st.success("No hay pagos pendientes de revisión.")
                else:
                    for pago in pagos:
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
