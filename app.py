import streamlit as st
import requests
import pandas as pd
import base64

st.set_page_config(
    page_title="Inscripción y Gestión Escolar - Modelos ONU",
    page_icon="🏫",
    layout="wide"
)

API_URL = "https://script.google.com/macros/s/AKfycbwHMPNXP7WizfswDjmTmNvTReNQUy9uvpSTTk-lpsc2DNXQojhg2ssSbyKfPQdPKUoBhQ/exec"

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

menu = st.sidebar.selectbox("Seleccionar Opción:", [
    "📝 Preinscripción Institucional", 
    "🔑 Ingreso a Mi Delegación", 
    "💳 Subir Comprobante de Pago", 
    "📋 Carga de Nómina y Documentación"
])

# ---------------------------------------------------------
# 1. PREINSCRIPCIÓN INSTITUCIONAL
# ---------------------------------------------------------
if menu == "📝 Preinscripción Institucional":
    st.subheader("📝 Formulario de Preinscripción Escolar")
    
    modelos = api_get("GET_MODELOS_ACTIVOS")
    if not modelos:
        st.warning("⚠️ No hay modelos activos en este momento.")
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
                        "secret_hash": secret_hash,
                        "id_modelo": id_modelo_elegido
                    }
                }
                with st.spinner("Registrando institución y enviando correo..."):
                    try:
                        res = requests.post(API_URL, json=payload).json()
                        if res.get("status") == "SUCCESS":
                            data_res = res.get("data", {})
                            st.success(f"¡Preinscripción exitosa! Tu Código de Delegación es: **{data_res.get('id_delegacion')}**. Guardalo junto a tu contraseña para ingresar al sistema.")
                        else:
                            st.error(f"Error: {res.get('message')}")
                    except Exception as e:
                        st.error(f"Error de conexión: {e}")

# ---------------------------------------------------------
# 2. INGRESO A MI DELEGACIÓN
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
                st.markdown("---")
                st.markdown(f"### 🏛️ {escuela_encontrada.get('nombre_colegio')}")
                st.write(f"**Responsable:** {escuela_encontrada.get('docente_apellido_nombre')}")
                st.write(f"**Estado del Legajo:** `{escuela_encontrada.get('estado', 'REGISTRADO')}`")
                st.write(f"**Cupos Solicitados:** {escuela_encontrada.get('cupos_solicitados')}")

                st.markdown("### 🌍 Bancas y Países Asignados")
                res_asig = requests.get(f"{API_URL}?action=GET_ASIGNACIONES_DELEGACION&id_delegacion={id_del_ingresado}").json()
                bancas = res_asig.get("data", [])

                if not bancas:
                    st.info("Aún no hay bancas asignadas para tu institución.")
                else:
                    for b in bancas:
                        st.write(f"- **{b.get('organo')}** — País: **{b.get('pais')}** (`ID: {b.get('id_asignacion')}`)")
            else:
                st.error("Código de delegación o clave incorrectos.")

# ---------------------------------------------------------
# 3. SUBIR COMPROBANTE DE PAGO
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
                st.error("Completa todos los campos obligatorios y adjunta el comprobante.")
            else:
                file_bytes = archivo_pago.read()
                file_b64 = base64.b64encode(file_bytes).decode('utf-8')
                
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

                with st.spinner("Subiendo comprobante a Google Drive..."):
                    try:
                        res = requests.post(API_URL, json=payload).json()
                        if res.get("status") == "SUCCESS":
                            st.success("¡Comprobante subido correctamente! Quedará pendiente de aprobación por el secretariado.")
                        else:
                            st.error(f"Error: {res.get('message')}")
                    except Exception as e:
                        st.error(f"Error de conexión: {e}")

# ---------------------------------------------------------
# 4. CARGA DE NÓMINA Y DOCUMENTACIÓN
# ---------------------------------------------------------
elif menu == "📋 Carga de Nómina y Documentación":
    st.subheader("📋 Registro de Participantes y Fichas Médicas/Autorizaciones")

    st.write("Ingrese sus credenciales institucionales para verificar sus asignaciones y cupos permitidos antes de cargar la nómina.")

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
            # Obtener asignaciones / bancas permitidas
            res_asig = requests.get(f"{API_URL}?action=GET_ASIGNACIONES_DELEGACION&id_delegacion={id_del_nom}").json()
            bancas_asignadas = res_asig.get("data", [])
            limite_bancas = len(bancas_asignadas) if len(bancas_asignadas) > 0 else int(escuela.get("cupos_solicitados", 5))

            # Obtener alumnos ya cargados en nómina
            nominas_todas = api_get("GET_TODAS_NOMINAS")
            alumnos_actuales = [n for n in nominas_todas if str(n.get("id_delegacion")).strip().upper() == id_del_nom]
            cargados_count = len(alumnos_actuales)

            st.markdown("---")
            col_info1, col_info2 = st.columns(2)
            with col_info1:
                st.info(f"🏛️ **Institución:** {escuela.get('nombre_colegio')}")
                st.markdown(f"**Cupos / Bancas Asignadas:** `{limite_bancas}`")
            with col_info2:
                st.markdown(f"**Participantes ya cargados:** `{cargados_count} / {limite_bancas}`")

            if cargados_count > 0:
                st.markdown("### 📋 Alumnos ya registrados:")
                for idx, alu in enumerate(alumnos_actuales):
                    st.write(f"{idx+1}. **{alu.get('nombre')} {alu.get('apellido')}** (DNI: {alu.get('dni')}) — *Banca:* {alu.get('rol_mnu')}")

            st.markdown("---")

            if cargados_count >= limite_bancas:
                st.warning(f"⚠️ Has alcanzado el límite máximo de {limite_bancas} participantes permitidos para tu institución.")
            else:
                st.markdown("### ➕ Registrar Nuevo Participante")
                with st.form("form_agregar_participante"):
                    
                    # Si tiene bancas asignadas, permitimos seleccionarla de la lista
                    if bancas_asignadas:
                        dict_bancas = {f"{b.get('organo')} — {b.get('pais')} (ID: {b.get('id_asignacion')})": b.get('id_asignacion') for b in bancas_asignadas}
                        banca_sel = st.selectbox("Seleccionar Banca / Representación Asignada:", list(dict_bancas.keys()))
                        id_asignacion_alum = dict_bancas[banca_sel]
                        rol_mnu = st.selectbox("Rol en el Órgano:", ["Delegado/a", "Embajador/a", "Autoridad"])
                    else:
                        id_asignacion_alum = "-"
                        rol_mnu = st.text_input("Rol / Cargo o Comisión (Ej: Embajador - Bahrein):")

                    nombre = st.text_input("Nombre:")
                    apellido = st.text_input("Apellido:")
                    dni = st.text_input("DNI:")
                    alergias_medicas = st.text_input("Observaciones o Alergias Médicas (Escribir 'Ninguna' si no posee):", value="Ninguna")

                    st.markdown("### Documentación Adjunta (PDF o Imagen)")
                    file_ficha = st.file_uploader("Ficha Médica Firmada:", type=["pdf", "jpg", "png"], key="ficha")
                    file_aut = st.file_uploader("Autorización de Menores / Padres:", type=["pdf", "jpg", "png"], key="aut")

                    btn_guardar_alumno = st.form_submit_button("Guardar Participante en Nómina")

                    if btn_guardar_alumno:
                        if not nombre or not apellido or not dni:
                            st.error("Por favor completa los datos obligatorios del alumno.")
                        else:
                            ficha_b64, ficha_name, ficha_mime = "", "", ""
                            aut_b64, aut_name, aut_mime = "", "", ""

                            if file_ficha:
                                ficha_b64 = base64.b64encode(file_ficha.read()).decode('utf-8')
                                ficha_name = file_ficha.name
                                ficha_mime = file_ficha.type

                            if file_aut:
                                aut_b64 = base64.b64encode(file_aut.read()).decode('utf-8')
                                aut_name = file_aut.name
                                aut_mime = file_aut.type

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
                                    "ficha_b64": ficha_b64,
                                    "ficha_name": ficha_name,
                                    "ficha_mime": ficha_mime,
                                    "aut_b64": aut_b64,
                                    "aut_name": aut_name,
                                    "aut_mime": aut_mime
                                }
                            }

                            with st.spinner("Subiendo archivos a Drive y guardando participante..."):
                                try:
                                    res = requests.post(API_URL, json=payload).json()
                                    if res.get("status") == "SUCCESS":
                                        st.success("¡Participante guardado con éxito en la nómina!")
                                        st.rerun()
                                    else:
                                        st.error(f"Error: {res.get('message')}")
                                except Exception as e:
                                    st.error(f"Error de conexión: {e}")

            st.markdown("---")
            if st.button("📌 Finalizar y Enviar Documentación a Revisión"):
                payload_fin = {
                    "action": "CONFIRMAR_CARGA_DOCUMENTACION",
                    "data": {
                        "id_delegacion": id_del_nom,
                        "secret_hash": hash_nom
                    }
                }
                try:
                    res = requests.post(API_URL, json=payload_fin).json()
                    if res.get("status") == "SUCCESS":
                        st.success("¡Documentación enviada a revisión con éxito!")
                    else:
                        st.error(f"Error: {res.get('message')}")
                except Exception as e:
                    st.error(f"Error: {e}")
