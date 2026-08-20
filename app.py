import streamlit as st
import requests
import base64

st.set_page_config(
    page_title="Sistema Integral de Gestión - MNU",
    page_icon="🇺🇳",
    layout="wide"
)

# API URL actualizada
API_URL = "https://script.google.com/macros/s/AKfycby8moCFp2NDWnSapd9TaA0OJPERRZf249QwFF9SJuw3QnKmAlc8RCHJdze-o3QTmCXwCA/exec"

st.title("🇺🇳 Plataforma Integral de Gestión de Modelos ONU")

# ---------------------------------------------------------
# DICCIONARIO BASE DE MODELOS
# ---------------------------------------------------------
CONFIG_MODELOS = {
    "MONUCBA 2026": "MONUCBA_2026",
    "MONU Secundarios Local 2026": "MNU_LOCAL_2026",
    "MONU Universitario 2026": "MNU_UNI_2026",
    "Modelo Evento 04": "MODELO_04",
    "Modelo Evento 05": "MODELO_05",
    "Modelo Evento 06": "MODELO_06",
    "Modelo Evento 07": "MODELO_07",
    "Modelo Evento 08": "MODELO_08",
    "Modelo Evento 09": "MODELO_09",
    "Modelo Evento 10": "MODELO_10"
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

# =========================================================
# MÓDULO 1: PREINSCRIPCIÓN (BLOQUES INDEPENDIENTES POR MODELO)
# =========================================================
if menu == "Preinscripción Escuela":
    st.subheader(f"Ficha de Inscripción - {modelo_seleccionado}")
    
    with st.form("form_registro_independiente"):
        colegio = st.text_input("Nombre de la Institución / Colegio")
        docente = st.text_input("Docente / Tutor Acompañante")
        email = st.text_input("Correo Electrónico de Contacto")
        clave = st.text_input("Creá una Clave Secreta para el Portal", type="password")
        
        st.markdown("---")
        st.markdown("#### Selección de Delegaciones y Modalidades")
        
        tot_alumnos = 0
        desglose_str = ""

        # -------------------------------------------------
        # MODELO 1: MONUCBA 2026
        # -------------------------------------------------
        if id_modelo_actual == "MONUCBA_2026":
            col1, col2 = st.columns(2)
            with col1:
                del_5 = st.number_input("Sin CS ni ECOSOC (5 delegados)", min_value=0, max_value=5, value=0, key="m1_del5")
                del_7_eco = st.number_input("Sin CS con ECOSOC (7 delegados)", min_value=0, max_value=5, value=0, key="m1_del7eco")
                del_9_comp = st.number_input("Con CS y ECOSOC (9 delegados)", min_value=0, max_value=2, value=0, key="m1_del9")
            with col2:
                del_7_cs = st.number_input("Con CS sin ECOSOC (7 delegados)", min_value=0, max_value=2, value=0, key="m1_del7cs")
                del_davos = st.number_input("Foro de Davos (Unipersonales)", min_value=0, max_value=5, value=0, key="m1_davos")
                del_prensa = st.number_input("Comité de Prensa (3 delegados)", min_value=0, max_value=2, value=0, key="m1_prensa")
                
            tot_alumnos = (del_5 * 5) + (del_7_eco * 7) + (del_9_comp * 9) + (del_7_cs * 7) + (del_davos * 1) + (del_prensa * 3)
            desglose_str = f"5d:{del_5} | 7d_eco:{del_7_eco} | 9d:{del_9_comp} | 7d_cs:{del_7_cs} | davos:{del_davos} | prensa:{del_prensa}"

        # -------------------------------------------------
        # MODELO 2: MONU SECUNDARIOS LOCAL 2026
        # -------------------------------------------------
        elif id_modelo_actual == "MNU_LOCAL_2026":
            col1, col2 = st.columns(2)
            with col1:
                del_parejas = st.number_input("Delegaciones Generales en Pareja (2 alumnos)", min_value=0, max_value=10, value=0, key="m2_par")
                del_individuales = st.number_input("Comisiones Especiales Individuales (1 alumno)", min_value=0, max_value=5, value=0, key="m2_ind")
            with col2:
                del_prensa_loc = st.number_input("Delegados de Prensa (1 alumno)", min_value=0, max_value=3, value=0, key="m2_pre")
                
            tot_alumnos = (del_parejas * 2) + (del_individuales * 1) + (del_prensa_loc * 1)
            desglose_str = f"parejas:{del_parejas} | individuales:{del_individuales} | prensa:{del_prensa_loc}"

        # -------------------------------------------------
        # MODELO 3: MONU UNIVERSITARIO 2026
        # -------------------------------------------------
        elif id_modelo_actual == "MNU_UNI_2026":
            col1, col2 = st.columns(2)
            with col1:
                embajadores = st.number_input("Bancas de Embajadores (Individual)", min_value=0, max_value=5, value=0, key="m3_emb")
            with col2:
                consejeros = st.number_input("Bancas de Consejeros (Individual)", min_value=0, max_value=5, value=0, key="m3_con")
                
            tot_alumnos = (embajadores * 1) + (consejeros * 1)
            desglose_str = f"embajadores:{embajadores} | consejeros:{consejeros}"

        # -------------------------------------------------
        # MODELO 4: ESTRUCTURA INDEPENDIENTE MODELO 04
        # -------------------------------------------------
        elif id_modelo_actual == "MODELO_04":
            col1, col2 = st.columns(2)
            with col1:
                m4_tipo1 = st.number_input("Delegación Estándar (4 delegados)", min_value=0, max_value=5, value=0, key="m4_t1")
            with col2:
                m4_tipo2 = st.number_input("Delegación VIP (6 delegados)", min_value=0, max_value=2, value=0, key="m4_t2")
                
            tot_alumnos = (m4_tipo1 * 4) + (m4_tipo2 * 6)
            desglose_str = f"estandar:{m4_tipo1} | vip:{m4_tipo2}"

        # -------------------------------------------------
        # MODELO 5: ESTRUCTURA INDEPENDIENTE MODELO 05
        # -------------------------------------------------
        elif id_modelo_actual == "MODELO_05":
            m5_cupos = st.number_input("Cantidad de Parejas de Delegados", min_value=0, max_value=10, value=0, key="m5_cup")
            tot_alumnos = m5_cupos * 2
            desglose_str = f"parejas:{m5_cupos}"

        # -------------------------------------------------
        # MODELO 6: ESTRUCTURA INDEPENDIENTE MODELO 06
        # -------------------------------------------------
        elif id_modelo_actual == "MODELO_06":
            m6_cupos = st.number_input("Cantidad de Delegaciones Unipersonales", min_value=0, max_value=10, value=0, key="m6_cup")
            tot_alumnos = m6_cupos * 1
            desglose_str = f"unipersonales:{m6_cupos}"

        # -------------------------------------------------
        # MODELO 7: ESTRUCTURA INDEPENDIENTE MODELO 07
        # -------------------------------------------------
        elif id_modelo_actual == "MODELO_07":
            m7_cupos = st.number_input("Cantidad de Cupos de Delegación", min_value=0, max_value=10, value=0, key="m7_cup")
            tot_alumnos = m7_cupos * 2
            desglose_str = f"cupos:{m7_cupos}"

        # -------------------------------------------------
        # MODELO 8: ESTRUCTURA INDEPENDIENTE MODELO 08
        # -------------------------------------------------
        elif id_modelo_actual == "MODELO_08":
            m8_cupos = st.number_input("Cantidad de Cupos de Delegación", min_value=0, max_value=10, value=0, key="m8_cup")
            tot_alumnos = m8_cupos * 2
            desglose_str = f"cupos:{m8_cupos}"

        # -------------------------------------------------
        # MODELO 9: ESTRUCTURA INDEPENDIENTE MODELO 09
        # -------------------------------------------------
        elif id_modelo_actual == "MODELO_09":
            m9_cupos = st.number_input("Cantidad de Cupos de Delegación", min_value=0, max_value=10, value=0, key="m9_cup")
            tot_alumnos = m9_cupos * 2
            desglose_str = f"cupos:{m9_cupos}"

        # -------------------------------------------------
        # MODELO 10: ESTRUCTURA INDEPENDIENTE MODELO 10
        # -------------------------------------------------
        elif id_modelo_actual == "MODELO_10":
            m10_cupos = st.number_input("Cantidad de Cupos de Delegación", min_value=0, max_value=10, value=0, key="m10_cup")
            tot_alumnos = m10_cupos * 2
            desglose_str = f"cupos:{m10_cupos}"

        st.info(f"📊 **Total de participantes a inscribir en la nómina:** {tot_alumnos} personas.")
        
        submitted = st.form_submit_button("Enviar Preinscripción")
        
        if submitted:
            if not colegio or not docente or not email or not clave:
                st.error("Por favor completá los datos institucionales obligatorios.")
            elif tot_alumnos == 0:
                st.warning("Debes seleccionar al menos 1 delegación o cupo.")
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
# MÓDULO 3: CARGA DE NÓMINA Y FICHAS
# ---------------------------------------------------------
elif menu == "Carga de Nómina y Fichas":
    st.subheader(f"Carga de Participantes y Documentación - {modelo_seleccionado}")
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
                        "id_modelo": id_modelo_actual,
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
