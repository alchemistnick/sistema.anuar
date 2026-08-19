import streamlit as st
import requests
import base64

# Configuración de la página
st.set_page_config(
    page_title="Gestión MNU 2026",
    page_icon="🇺🇳",
    layout="wide"
)

# URL de la API de Apps Script
API_URL = "https://script.google.com/macros/s/AKfycby6JFMVAUgRld1h5AaF6iekpbqcQ-vvzFppCpIDcNsuXPBRyuRlxJRDJ-CQDA1jypZ2VA/exec"

st.title("🇺🇳 Sistema Integral de Gestión - MNU 2026")

# Menú principal
menu = st.sidebar.radio(
    "Navegación",
    ["Preinscripción Escuela", "Cargar Comprobante", "Panel Secretariado (Admin)"]
)

# ---------------------------------------------------------
# MÓDULO 1: PREINSCRIPCIÓN
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
                        "secret_hash": clave # Nota: En prod conviene encriptar/hash
                    }
                }
                
                with st.spinner("Procesando registro..."):
                    try:
                        res = requests.post(API_URL, json=payload).json()
                        if res.get("status") == "SUCCESS":
                            id_generado = res["data"]["id_delegacion"]
                            st.success(f"¡Registro exitoso! Guardá tu ID de Delegación: **{id_generado}**")
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
            # Lectura y codificación Base64
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
# MÓDULO 3: PANEL ADMIN / SECRETARIADO
# ---------------------------------------------------------
elif menu == "Panel Secretariado (Admin)":
    st.subheader("Acceso Restringido al Secretariado")
    admin_pass = st.text_input("Contraseña de Administrador", type="password")
    
    if admin_pass == "Secretaria2026": # Modificar clave admin
        st.success("Acceso concedido")
        st.info("Próximamente: Visor directo de pagos y asignación de sorteo presencial.")
    elif admin_pass:
        st.error("Contraseña incorrecta.")
