import streamlit as st
import requests
import pandas as pd
import base64

st.set_page_config(
    page_title="Inscripción y Gestión Escolar - Modelos ONU",
    page_icon="🏫",
    layout="wide"
)

API_URL = "https://script.google.com/macros/s/AKfycbzbPKv-DdELuHy2FugQ3s6ZENEU1gUwFiDaK05r2t6qaqaUND7bmNqfwOsePnPNYb_hJQ/exec"

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
# - False: Muestra el menú normal de escuelas y oculta la acreditación.
# - True: Muestra exclusivamente la terminal de acreditación presencial.
MODO_SOLO_ACREDITACION = False 

if MODO_SOLO_ACREDITACION:
    menu = st.sidebar.selectbox("Seleccionar Opción:", ["🎫 Acreditación Presencial"])
else:
    menu = st.sidebar.selectbox("Seleccionar Opción:", [
        "🎫 Acreditación Presencial",
        "📝 Preinscripción Institucional", 
        "🔑 Ingreso a Mi Delegación", 
        "💳 Subir Comprobante de Pago", 
        "📋 Carga de Nómina y Documentación"
    ])

# ---------------------------------------------------------
# 1. ACREDITACIÓN PRESENCIAL CON VALIDACIÓN DE MODELO
# ---------------------------------------------------------
if menu == "🎫 Acreditación Presencial":
    st.subheader("🎫 Terminal de Acreditación - Modelos ONU")
     st.write("Este fin de semana estamos de Modelo para una mejor gestión de otros Modelos ONU puede volver el Lunes")
    st.write("Seleccione el Modelo correspondiente e ingrese el DNI del participante para validar su ingreso.")

    modelos = api_get("GET_MODELOS_ACTIVOS")
    if not modelos:
        st.warning("⚠️ No hay modelos activos configurados.")
        st.stop()

    dict_mods = {m["nombre_visible"]: m["id_modelo"] for m in modelos}
    mod_sel = st.selectbox("Seleccionar Modelo ONU para Acreditar:", list(dict_mods.keys()), key="acred_mod")
    id_modelo_acred = dict_mods[mod_sel]

    with st.form("form_acreditacion"):
        dni_ingresado = st.text_input("Número de DNI del Participante:").strip()
        btn_acreditar = st.form_submit_button("Acreditar Ingreso")

        if btn_acreditar:
            if not dni_ingresado:
                st.error("Por favor ingrese un DNI.")
            else:
                with st.spinner("Verificando padrón y modelo..."):
                    try:
                        url = f"{API_URL}?action=VERIFICAR_Y_ACREDITAR&dni={dni_ingresado}&id_modelo={id_modelo_acred}"
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
                            st.write(f"**Modelo:** `{d.get('id_modelo')}`")
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
        st.warning("⚠️ No hay modelos activos.")
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
            secret_hash = st.text_input("Crear Clave de Acceso:", type="password")

        if st.form_submit_button("Enviar Preinscripción"):
            if not nombre_colegio or not docente_email or not secret_hash:
                st.error("Completa los campos obligatorios.")
            else:
                payload = {
                    "action": "REGISTRAR_DELEGACION",
                    "data": {
                        "nombre_colegio": nombre_colegio, "direccion_escuela": direccion_escuela,
                        "email_institucional": email_institucional, "telefono_institucional": telefono_institucional,
                        "docente_apellido_nombre": docente_apellido_nombre, "docente_email": docente_email,
                        "docente_telefono": docente_telefono, "cupos_solicitados": cupos_solicitados,
                        "docentes_acompanantes": docentes_acompanantes, "secret_hash": secret_hash,
                        "id_modelo": id_modelo_elegido
                    }
                }
                res = requests.post(API_URL, json=payload).json()
                if res.get("status") == "SUCCESS":
                    st.success(f"¡Preinscripción exitosa! Código de Delegación: **{res.get('data', {}).get('id_delegacion')}**.")
                else:
                    st.error(res.get('message'))

# ---------------------------------------------------------
# 3. INGRESO A MI DELEGACIÓN
# ---------------------------------------------------------
elif menu == "🔑 Ingreso a Mi Delegación":
    st.subheader("🔑 Estado de mi Institución y Asignaciones")
    with st.form("form_login_escuela"):
        id_del_ingresado = st.text_input("Código de Delegación (Ej: DEL-001):").strip().upper()
        hash_ingresado = st.text_input("Clave de Acceso:", type="password").strip()
        if st.form_submit_button("Consultar Estado"):
            delegaciones = api_get("GET_TODAS_DELEGACIONES")
            escuela = next((d for d in delegaciones if str(d.get("id_delegacion")).strip().upper() == id_del_ingresado and str(d.get("secret_hash")).strip() == hash_ingresado), None)
            if escuela:
                st.success("¡Acceso correcto!")
                st.markdown(f"### 🏛️ {escuela.get('nombre_colegio')}")
                res_asig = requests.get(f"{API_URL}?action=GET_ASIGNACIONES_DELEGACION&id_delegacion={id_del_ingresado}").json()
                for b in res_asig.get("data", []):
                    st.write(f"- **{b.get('organo')}** — País: **{b.get('pais')}** (`ID: {b.get('id_asignacion')}`)")
            else:
                st.error("Datos incorrectos.")

# ---------------------------------------------------------
# 4. SUBIR COMPROBANTE DE PAGO
# ---------------------------------------------------------
elif menu == "💳 Subir Comprobante de Pago":
    st.subheader("💳 Subir Comprobante de Pago")
    with st.form("form_pago"):
        id_del_pago = st.text_input("Código de Delegación:").strip().upper()
        hash_pago = st.text_input("Clave de Acceso:", type="password").strip()
        monto_pago = st.number_input("Monto Abonado ($):", min_value=0.0, format="%.2f")
        archivo_pago = st.file_uploader("Comprobante:", type=["pdf", "png", "jpg", "jpeg"])
        if st.form_submit_button("Enviar Comprobante"):
            if not id_del_pago or not hash_pago or not archivo_pago:
                st.error("Completa todos los campos.")
            else:
                b64 = base64.b64encode(archivo_pago.read()).decode('utf-8')
                payload = {"action": "SUBIR_COMPROBANTE_PAGO", "data": {"id_delegacion": id_del_pago, "secret_hash": hash_pago, "monto": monto_pago, "file_base64": b64, "file_name": archivo_pago.name, "file_mime": archivo_pago.type}}
                res = requests.post(API_URL, json=payload).json()
                if res.get("status") == "SUCCESS": st.success("¡Comprobante subido!")
                else: st.error(res.get('message'))

# ---------------------------------------------------------
# 5. CARGA DE NÓMINA Y DOCUMENTACIÓN
# ---------------------------------------------------------
elif menu == "📋 Carga de Nómina y Documentación":
    st.subheader("📋 Registro de Participantes y Documentación")
    with st.form("form_verif_nomina"):
        id_del_nom = st.text_input("Código de Delegación:").strip().upper()
        hash_nom = st.text_input("Clave de Acceso:", type="password").strip()
        if st.form_submit_button("Verificar"):
            st.session_state['id_del_nom'] = id_del_nom
            st.session_state['hash_nom'] = hash_nom

    if 'id_del_nom' in st.session_state and st.session_state['id_del_nom']:
        id_del_nom = st.session_state['id_del_nom']
        hash_nom = st.session_state.get('hash_nom', '')
        delegaciones = api_get("GET_TODAS_DELEGACIONES")
        escuela = next((d for d in delegaciones if str(d.get("id_delegacion")).strip().upper() == id_del_nom and str(d.get("secret_hash")).strip() == hash_nom), None)
        if escuela:
            res_asig = requests.get(f"{API_URL}?action=GET_ASIGNACIONES_DELEGACION&id_delegacion={id_del_nom}").json()
            bancas_asignadas = res_asig.get("data", [])
            tab_est, tab_doc = st.tabs(["👨‍🎓 Estudiante", "👨‍🏫 Docente"])
            
            with tab_est:
                with st.form("form_est"):
                    dict_bancas = {f"{b.get('organo')} — {b.get('pais')}": b.get('id_asignacion') for b in bancas_asignadas} if bancas_asignadas else {"Sin Asignación": "-"}
                    banca_sel = st.selectbox("Banca:", list(dict_bancas.keys()))
                    id_asig = dict_bancas[banca_sel]
                    nombre = st.text_input("Nombre:")
                    apellido = st.text_input("Apellido:")
                    dni = st.text_input("DNI:")
                    if st.form_submit_button("Guardar"):
                        payload = {"action": "GUARDAR_PARTICIPANTE_NOMINA", "data": {"id_delegacion": id_del_nom, "secret_hash": hash_nom, "id_asignacion": id_asig, "rol_mnu": "Delegado/a", "nombre": nombre, "apellido": apellido, "dni": dni, "alergias_medicas": "Ninguna", "ficha_b64": "", "ficha_name": "", "ficha_mime": "", "aut_b64": "", "aut_name": "", "aut_mime": ""}}
                        res = requests.post(API_URL, json=payload).json()
                        if res.get("status") == "SUCCESS": st.success("Guardado"); st.rerun()
