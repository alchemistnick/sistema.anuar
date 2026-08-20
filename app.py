import streamlit as st
import requests
import base64

# Configuración de la página
st.set_page_config(
    page_title="Gestión MNU 2026",
    page_icon="🇺🇳",
    layout="wide"
)

# Tu URL de Apps Script desplegada
API_URL = "https://script.google.com/macros/s/AKfycbxTrEcoO4wZgPkLYM8FxJl7bkPHYSCCpMeyxsHigv4Tl1tOXs1DG1KlwTTQIZcz3LYPEA/exec"

st.title("🇺🇳 Sistema Integral de Gestión - MNU 2026")

# Menú lateral
menu = st.sidebar.radio(
    "Navegación",
    [
        "Preinscripción Escuela", 
        "Cargar Comprobante", 
        "Carga de Nómina y Fichas"
    ]
)

# ---------------------------------------------------------
# MÓDULO 1: PREINSCRIPCIÓN DE ESCUELA
# ---------------------------------------------------------
if menu == "Preinscripción Escuela":
    st.subheader("Formulario de Registro para Instituciones")
    
    with st.form("form_registro"):
        colegio = st.text_input("Nombre de la Institución / Colegio")
        docente = st.text_input("Docente / Tutor a Cargo")
        email = st.text_input("Correo Electrónico de Contacto")
        cupos = st.number_input("Cantidad de Delegaciones Solicitadas", min_value=1, max_value=5, value=1)
        clave = st.text_input("Crea una Clave Secreta de Acceso", type="password")
        
        submitted = st.form_submit_button("Enviar Registro")
        
        if submitted:
            if not colegio or not docente or not email or not clave:
                st.error("Por favor completá todos los campos obligatorios.")
            else:
                payload = {
                    "action": "REGISTRAR_DELEGACION",
                    "data": {
                        "nombre_colegio": colegio,
                        "docente_cargo": docente,
                        "email_contacto": email,
                        "cupos_solicitados": cupos,
                        "secret_hash": clave
                    }
                }
                
                with st.spinner("Procesando registro..."):
                    try:
                        res = requests.post(API_URL, json=payload).json()
                        if res.get("status") == "SUCCESS":
                            st.success(f"¡Registro exitoso! Guardá tu ID de Delegación: **{res['data']['id_delegacion']}**")
                        else:
                            st.error(f"Error al registrar: {res.get('message')}")
                    except Exception as e:
                        st.error(f"Error de conexión con la API: {e}")

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
                        st.success("Comprobante subido correctamente. En revisión por la organización.")
                    else:
                        st.error(f"Error al subir: {res.get('message')}")
                except Exception as e:
                    st.error(f"Error de conexión: {e}")

# ---------------------------------------------------------
# MÓDULO 3: CARGA DE NÓMINA Y DOCUMENTACIÓN (NUEVO)
# ---------------------------------------------------------
elif menu == "Carga de Nómina y Fichas":
    st.subheader("Carga de Participantes y Documentación Médica/Legal")
    
    st.info("Ingresá los datos de cada estudiante o participante perteneciente a tu delegación.")
    
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
                # Procesar Ficha Médica
                b64_ficha, mime_ficha, ext_ficha = "", "", ""
                if archivo_ficha:
                    b64_ficha = base64.b64encode(archivo_ficha.read()).decode('utf-8')
                    mime_ficha = archivo_ficha.type
                    ext_ficha = archivo_ficha.name.split('.')[-1]

                # Procesar Autorización
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
