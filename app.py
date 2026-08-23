import streamlit as st
import requests
import pandas as pd
import base64

st.set_page_config(
    page_title="Inscripción y Gestión Escolar - Modelos ONU",
    page_icon="🏫",
    layout="wide"
)

API_URL = "https://script.google.com/macros/s/AKfycbzF4ouR-7Z6fEkT9W4df9nTEWLKyC8uS-PqE-xfm1JdW459GRFoxRkEVAx0Zb-5bSZVPQ/exec"

def api_get(action, params=""):
    try:
        url = f"{API_URL}?action={action}{params}"
        res = requests.get(url).json()
        if res.get("status") == "SUCCESS":
            return res.get("data", [])
        return []
    except Exception:
        return []

st.title("🏫 Portal de Instituciones - Modelos ONU")

# 🎛️ INTERRUPTOR DE MODO EVENTO
# - Si está en False: Muestra el menú normal de escuelas y oculta la acreditación.
# - Si está en True: Bloquea todo lo demás y deja activa exclusivamente la terminal de acreditación.
MODO_SOLO_ACREDITACION = False 

# Definición dinámica del menú según el interruptor
if MODO_SOLO_ACREDITACION:
    menu = st.sidebar.selectbox("Seleccionar Opción:", [
        "🎫 Acreditación Presencial"
    ])
else:
    menu = st.sidebar.selectbox("Seleccionar Opción:", [
        "📝 Preinscripción Institucional", 
        "🔑 Ingreso a Mi Delegación", 
        "💳 Subir Comprobante de Pago", 
        "📋 Carga de Nómina y Documentación"
    ])

# ---------------------------------------------------------
# 1. ACREDITACIÓN PRESENCIAL
# ---------------------------------------------------------
if menu == "🎫 Acreditación Presencial":
    st.subheader("🎫 Terminal de Acreditación - Modelos ONU")
    st.write("Ingrese el DNI del participante (estudiante o docente acompañante) para registrar su ingreso al evento.")

    with st.form("form_acreditacion"):
        dni_ingresado = st.text_input("Número de DNI del Participante:").strip()
        btn_acreditar = st.form_submit_button("Acreditar Ingreso")

        if btn_acreditar:
            if not dni_ingresado:
                st.error("Por favor ingrese un DNI.")
            else:
                with st.spinner("Verificando en padrón oficial..."):
                    try:
                        url = f"{API_URL}?action=VERIFICAR_Y_ACREDITAR&dni={dni_ingresado}"
                        res = requests.get(url).json()
                        if res.get("status") == "SUCCESS":
                            d = res.get("data", {})
                            st.success("✅ ¡ACREDITADO CON ÉXITO!")
                            st.markdown("---")
                            st.markdown(f"### 👤 {d.get('nombre')} {d.get('apellido')}")
                            st.write(f"**DNI:** `{d.get('dni')}`")
                            st.write(f"**Institución:** {d.get('nombre_colegio')}")
                            st.write(f"**Rol / Cargo:** `{d.get('rol_mnu')}`")
                            st.write(f"**Banca / Asignación:** {d.get('id_asignacion')}")
                        else:
                            st.error(f"❌ {res.get('message')}")
                    except Exception as e:
                        st.error(f"Error de conexión: {e}")

# ---------------------------------------------------------
# 2. PREINSCRIPCIÓN INSTITUCIONAL
# ---------------------------------------------------------
elif menu == "📝 Preinscripción Institucional":
    st.subheader("📝 Formulario de Preinscripción Escolar")
    
    modelos = api_get("GET_MODELOS_ACTIVOS")
    if not modelos:
        st.warning("⚠️ No hay modelos activos configurados en este momento.")
        st.stop()
        
    dict_mods = {m["nombre_visible"]: m["id_modelo"] for m in modelos}
    mod_sel = st.selectbox("Seleccionar Modelo ONU:", list(dict_mods.keys()))
    id_modelo_elegido = dict_mods[mod_sel]

    with st.form("form_preinscripcion"):
        col1, col2 = st.columns(2)
        with col1:
            nombre_colegio = st.text_input("Nombre de la Institución Educativa:")
            direccion_escuela = st.text_input("Dirección de la Escuela:")
            email_institucional = st.text_input("Email Institucional:")
            telefono_institucional = st.text_input("Teléfono Institucional:")
        with col2:
            docente_apellido_nombre = st.text_input("Apellido y Nombre del Docente Responsable:")
            docente_email = st.text_input("Email del Docente:")
            docente_telefono = st.text_input("Celular del Docente:")
            cupos_solicitados = st.number_input("Cupos Solicitados (Delegados):", min_value=1, value=5)
            docentes_acompanantes = st.number_input("Docentes Acompañantes:", min_value=1, value=1)
            secret_hash = st.text_input("Crear Clave de Acceso (Contraseña numérica o texto):", type="password")

        btn_enviar = st.form_submit_button("Enviar Preinscripción")
        if btn_enviar:
            if not nombre_colegio or not docente_email or not secret_hash:
                st.error("Por favor completa los campos obligatorios.")
            else:
                payload = {
                    "action": "REGISTRAR_DELEGACION",
                    "data": {
                        "nombre_colegio": nombre_colegio, 
                        "direccion_escuela": direccion_escuela,
                        "email_institucional": email_institucional, 
                        "telefono_institucional": telefono_institucional,
                        "docente_apellido_nombre": docente_apellido_nombre, 
                        "docente_email": docente_email,
                        "docente_telefono": docente_telefono, 
                        "cupos_solicitados": cupos_solicitados,
                        "docentes_acompanantes": docentes_acompanantes, 
                        "secret_hash": secret_hash,
                        "id_modelo": id_modelo_elegido
                    }
                }
                with st.spinner("Registrando institución..."):
                    try:
                        res = requests.post(API_URL, json=payload).json()
                        if res.get("status") == "SUCCESS":
                            data_res = res.get("data", {})
                            st.success(f"¡Preinscripción exitosa! Tu Código de Delegación es: **{data_res.get('id_delegacion')}**. Guardá este código y tu clave para ingresar.")
                        else:
                            st.error(f"Error: {res.get('message')}")
                    except Exception as e:
                        st.error(f"Error de conexión: {e}")

# ---------------------------------------------------------
# 3. INGRESO A MI DELEGACIÓN
# ---------------------------------------------------------
elif menu == "🔑 Ingreso a Mi Delegación":
    st.subheader("🔑 Estado de mi Institución y Asignaciones")
    
    with st.form("form_login_escuela"):
        id_del_ingresado = st.text_input("Código de Delegación (Ej: DEL-001):").strip().upper()
        hash_ingresado = st.text_input("Clave de Acceso:", type="password").strip()
        btn_login = st.form_submit_button("Consultar Estado")

        if btn_login:
            delegaciones = api_get("GET_TODAS_DELEGACIONES")
            escuela_encontrada = next((d for d in delegaciones if str(d.get("id_delegacion")).strip().upper() == id_del_ingresado and str(d.get("secret_hash")).strip() == hash_ingresado), None)
            
            if escuela_encontrada:
                st.success("¡Acceso correcto!")
                st.markdown(f"### 🏛️ {escuela_encontrada.get('nombre_colegio')}")
                st.write(f"**Docente Responsable:** {escuela_encontrada.get('docente_apellido_nombre')}")
                st.write(f"**Estado de Documentación:** `{escuela_encontrada.get('estado', 'REGISTRADO')}`")
                
                st.markdown("---")
                st.markdown("### 📌 Bancas y Países Asignados")
                res_asig = requests.get(f"{API_URL}?action=GET_ASIGNACIONES_DELEGACION&id_delegacion={id_del_ingresado}").json()
                bancas_escuela = res_asig.get("data", [])
                
                if not bancas_escuela:
                    st.info("Tu institución aún no tiene bancas asignadas.")
                else:
                    for b in bancas_escuela:
                        st.write(f"- **{b.get('organo')}** — País: **{b.get('pais')}** (`ID Asignación: {b.get('id_asignacion')}`)")
            else:
                st.error("Código de delegación o clave incorrectos.")

# ---------------------------------------------------------
# 4. SUBIR COMPROBANTE DE PAGO
# ---------------------------------------------------------
elif menu == "💳 Subir Comprobante de Pago":
    st.subheader("💳 Subir Comprobante de Pago o Arancel")
    
    with st.form("form_pago"):
        id_del_pago = st.text_input("Código de Delegación (Ej: DEL-001):").strip().upper()
        hash_pago = st.text_input("Clave de Acceso:", type="password").strip()
        monto_pago = st.number_input("Monto Abonado ($):", min_value=0.0, format="%.2f")
        archivo_pago = st.file_uploader("Adjuntar Comprobante (PDF o Imagen):", type=["pdf", "png", "jpg", "jpeg"])
        btn_subir_pago = st.form_submit_button("Enviar Comprobante")

        if btn_subir_pago:
            if not id_del_pago or not hash_pago or not archivo_pago:
                st.error("Completa todos los campos obligatorios y adjunta el archivo.")
            else:
                file_b64 = base64.b64encode(archivo_pago.read()).decode('utf-8')
                payload = {
                    "action": "SUBIR_COMPROBANTE_PAGO",
                    "data": {
                        "id_delegacion": id_del_pago, 
                        "secret_hash": hash_pago, 
                        "monto": monto_pago, 
                        "file_base64": file_b64, 
                        "file_name": archivo_pago.name, 
                        "file_mime": archivo_pago.type
                    }
                }
                with st.spinner("Subiendo comprobante..."):
                    try:
                        res = requests.post(API_URL, json=payload).json()
                        if res.get("status") == "SUCCESS": 
                            st.success("¡Comprobante subido con éxito! Quedará pendiente de revisión por secretaría.")
                        else: 
                            st.error(f"Error: {res.get('message')}")
                    except Exception as e: 
                        st.error(f"Error de conexión: {e}")

# ---------------------------------------------------------
# 5. CARGA DE NÓMINA Y DOCUMENTACIÓN
# ---------------------------------------------------------
elif menu == "📋 Carga de Nómina y Documentación":
    st.subheader("📋 Registro de Participantes, Docentes y Documentación")
    
    with st.form("form_verif_nomina"):
        id_del_nom = st.text_input("Código de Delegación (Ej: DEL-001):").strip().upper()
        hash_nom = st.text_input("Clave de Acceso:", type="password").strip()
        btn_verificar = st.form_submit_button("Verificar Estado y Cupos")

    if id_del_nom and hash_nom:
        delegaciones = api_get("GET_TODAS_DELEGACIONES")
        escuela = next((d for d in delegaciones if str(d.get("id_delegacion")).strip().upper() == id_del_nom and str(d.get("secret_hash")).strip() == hash_nom), None)
        
        if not escuela:
            st.error("⚠️ Código de delegación o clave incorrectos.")
        else:
            res_asig = requests.get(f"{API_URL}?action=GET_ASIGNACIONES_DELEGACION&id_delegacion={id_del_nom}").json()
            bancas_asignadas = res_asig.get("data", [])
            limite_bancas = len(bancas_asignadas) if len(bancas_asignadas) > 0 else int(escuela.get("cupos_solicitados", 5))
            
            nominas_todas = api_get("GET_TODAS_NOMINAS")
            registros_escuela = [n for n in nominas_todas if str(n.get("id_delegacion")).strip().upper() == id_del_nom]
            alumnos_actuales = [r for r in registros_escuela if r.get("rol_mnu") != "Docente Acompañante"]
            docentes_actuales = [r for r in registros_escuela if r.get("rol_mnu") == "Docente Acompañante"]

            st.info(f"🏛️ **Institución:** {escuela.get('nombre_colegio')} | **Estudiantes cargados:** {len(alumnos_actuales)}/{limite_bancas} | **Docentes cargados:** {len(docentes_actuales)}/{int(escuela.get('docentes_acompanantes', 1))}")

            tab_est, tab_doc = st.tabs(["👨‍🎓 Registrar Estudiante", "👨‍🏫 Registrar Docente"])
            
            with tab_est:
                with st.form("form_agregar_estudiante"):
                    dict_bancas = {f"{b.get('organo')} — {b.get('pais')} (ID: {b.get('id_asignacion')})": b.get('id_asignacion') for b in bancas_asignadas} if bancas_asignadas else {"Sin Asignación Previa": "-"}
                    banca_sel = st.selectbox("Banca Asignada:", list(dict_bancas.keys()))
                    id_asignacion_alum = dict_bancas[banca_sel]
                    
                    rol_mnu = st.selectbox("Rol del Participante:", ["Delegado/a", "Embajador/a"])
                    nombre = st.text_input("Nombre:")
                    apellido = st.text_input("Apellido:")
                    dni = st.text_input("DNI:")
                    alergias_medicas = st.text_input("Alergias / Observaciones Médicas:", value="Ninguna")
                    
                    file_ficha = st.file_uploader("Ficha Médica (PDF o Imagen):", type=["pdf", "jpg", "png"], key="f_est")
                    file_aut = st.file_uploader("Autorización firmada (PDF o Imagen):", type=["pdf", "jpg", "png"], key="a_est")
                    
                    if st.form_submit_button("Guardar Estudiante"):
                        if not nombre or not apellido or not dni:
                            st.error("Completa los campos obligatorios (Nombre, Apellido, DNI).")
                        else:
                            f_b64 = base64.b64encode(file_ficha.read()).decode('utf-8') if file_ficha else ""
                            a_b64 = base64.b64encode(file_aut.read()).decode('utf-8') if file_aut else ""
                            payload = {
                                "action": "GUARDAR_PARTICIPANTE_NOMINA",
                                "data": {
                                    "id_delegacion": id_del_nom, 
                                    "secret_hash": hash_nom, 
                                    "id_asignacion": id_asignacion_alum,
                                    "rol_mnu": rol_mnu, 
                                    "nombre": nombre, 
                                    "apellido": apellido, 
                                    "dni": dni,
                                    "alergias_medicas": alergias_medicas, 
                                    "ficha_b64": f_b64, 
                                    "ficha_name": file_ficha.name if file_ficha else "", 
                                    "ficha_mime": file_ficha.type if file_ficha else "",
                                    "aut_b64": a_b64, 
                                    "aut_name": file_aut.name if file_aut else "", 
                                    "aut_mime": file_aut.type if file_aut else ""
                                }
                            }
                            res = requests.post(API_URL, json=payload).json()
                            if res.get("status") == "SUCCESS": 
                                st.success("¡Estudiante guardado en nómina con éxito!")
                                st.rerun()
                            else: 
                                st.error(res.get('message'))

            with tab_doc:
                with st.form("form_agregar_docente"):
                    nombre_doc = st.text_input("Nombre Docente:")
                    apellido_doc = st.text_input("Apellido Docente:")
                    dni_doc = st.text_input("DNI Docente:")
                    email_doc = st.text_input("Email Docente:")
                    cel_doc = st.text_input("Celular Docente:")
                    file_doc_aut = st.file_uploader("Constancia Institucional / Autorización:", type=["pdf", "jpg", "png"], key="d_aut")
                    
                    if st.form_submit_button("Guardar Docente"):
                        if not nombre_doc or not apellido_doc or not dni_doc or not email_doc:
                            st.error("Completa Nombre, Apellido, DNI y Email del docente.")
                        else:
                            d_b64 = base64.b64encode(file_doc_aut.read()).decode('utf-8') if file_doc_aut else ""
                            payload_doc = {
                                "action": "GUARDAR_PARTICIPANTE_NOMINA",
                                "data": {
                                    "id_delegacion": id_del_nom, 
                                    "secret_hash": hash_nom, 
                                    "id_asignacion": "DOCENTE",
                                    "rol_mnu": "Docente Acompañante", 
                                    "nombre": nombre_doc, 
                                    "apellido": apellido_doc, 
                                    "dni": dni_doc,
                                    "alergias_medicas": f"Email: {email_doc} | Cel: {cel_doc}",
                                    "ficha_b64": "", 
                                    "ficha_name": "", 
                                    "ficha_mime": "",
                                    "aut_b64": d_b64, 
                                    "aut_name": file_doc_aut.name if file_doc_aut else "", 
                                    "aut_mime": file_doc_aut.type if file_doc_aut else ""
                                }
                            }
                            res = requests.post(API_URL, json=payload_doc).json()
                            if res.get("status") == "SUCCESS": 
                                st.success("¡Docente guardado con éxito!")
                                st.rerun()
                            else: 
                                st.error(res.get('message'))

            st.markdown("---")
            if st.button("📌 Finalizar y Enviar Documentación a Revisión"):
                res = requests.post(API_URL, json={"action": "CONFIRMAR_CARGA_DOCUMENTACION", "data": {"id_delegacion": id_del_nom, "secret_hash": hash_nom}}).json()
                if res.get("status") == "SUCCESS": 
                    st.success("¡Documentación enviada a revisión de secretaría con éxito!")
                else: 
                    st.error(res.get('message'))
