import base64
import firebase_admin
from firebase_admin import credentials, firestore
import requests
import streamlit as st

st.set_page_config(
    page_title="Inscripción y Gestión Escolar - Modelos ONU",
    page_icon="🏫",
    layout="wide",
)

modern_styling = """
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .block-container { padding-top: 1rem; padding-bottom: 2rem; }
    div.stForm { border-radius: 16px; padding: 24px; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08); border: 1px solid rgba(128, 128, 128, 0.2); }
    .stButton > button { border-radius: 12px; font-weight: 600; letter-spacing: 0.3px; }
    </style>
"""
st.markdown(modern_styling, unsafe_allow_html=True)


@st.cache_resource
def inicializar_firebase():
    if not firebase_admin._apps:
        cred = credentials.Certificate(dict(st.secrets["firebase"]))
        firebase_admin.initialize_app(cred)
    return firestore.client()


db = inicializar_firebase()

try:
    API_URL = st.secrets.get("API_URL") or st.secrets["api"]["URL"]
except Exception:
    API_URL = ""

try:
    FOLDER_COMPROBANTES = st.secrets.get("folder_comprobantes") or st.secrets["drive"]["folder_comprobantes"]
except Exception:
    FOLDER_COMPROBANTES = "1-QVd95Y2butIg9DNp3cPuIQI6sII50Rk"

try:
    FOLDER_FICHAS = st.secrets.get("folder_fichas") or st.secrets["drive"]["folder_fichas"]
except Exception:
    FOLDER_FICHAS = "1VSSud30QL9nSLbfu4jAz-dJ9q2rcRg1E"

try:
    FOLDER_SEGUROS = st.secrets.get("folder_seguros") or st.secrets["drive"].get("folder_seguros", "1-QVd95Y2butIg9DNp3cPuIQI6sII50Rk")
except Exception:
    FOLDER_SEGUROS = "1-QVd95Y2butIg9DNp3cPuIQI6sII50Rk"


def mostrar_encabezado_portal():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(
            """
            <div style="text-align: center; padding: 15px; background: linear-gradient(135deg, rgba(30, 41, 59, 0.05) 0%, rgba(51, 65, 85, 0.1) 100%); border-radius: 16px; border: 1px solid rgba(128, 128, 128, 0.15); margin-bottom: 1rem;">
                <h2 style="margin: 0; font-size: 1.6rem; font-weight: 900;">ANU-AR</h2>
                <p style="margin: 2px 0 0 0; font-size: 0.85rem; font-weight: 600; opacity: 0.6;">MODELOS DE NACIONES UNIDAS</p>
            </div>
            """,
            unsafe_allow_html=True
        )


def subir_archivo_a_drive_via_script(file_bytes, file_name, mime_type, folder_id):
    try:
        base64_data = base64.b64encode(file_bytes).decode("utf-8")
        payload = {"action": "UPLOAD_FILE", "fileData": base64_data, "fileName": file_name, "mimeType": mime_type, "folderId": folder_id}
        res = requests.post(API_URL, json=payload, timeout=60, allow_redirects=True)
        res_json = res.json()
        if res_json.get("status") == "success":
            return True, res_json.get("fileUrl") or res_json.get("url")
        return False, f"Error: {res_json.get('message', 'Desconocido')}"
    except Exception as e:
        return False, f"Excepción: {e}"


@st.cache_data(ttl=600)
def obtener_modelos_activos():
    try:
        docs = db.collection("modelos").stream()
        return [{**doc.to_dict(), "id_modelo": doc.id} for doc in docs]
    except Exception:
        return []


@st.cache_data(ttl=600)
def obtener_parametros_comites(id_modelo):
    try:
        doc = db.collection("configuracion").document(str(id_modelo)).get()
        if doc.exists:
            return doc.to_dict().get("parametros_comites", [])
        return []
    except Exception:
        return []


def preinscribir_escuela(datos_escuela):
    try:
        docente_email = str(datos_escuela.get("docente_email", "")).strip().lower()
        id_modelo_nuevo = str(datos_escuela.get("id_modelo", ""))
        id_doc_delegacion = f"{docente_email}_{id_modelo_nuevo}"
        
        db.collection("delegaciones").document(id_doc_delegacion).set({
            "id_delegacion": id_doc_delegacion,
            "estado": "PREINSCRIPTO",
            "costo_asignado": 0.0,
            "fecha_registro": firestore.SERVER_TIMESTAMP,
            **datos_escuela,
        }, merge=True)
        return True, id_doc_delegacion
    except Exception as e:
        return False, f"Error: {e}"


def validar_acceso_docente(email_doc, hash_ingresado, id_modelo_login=""):
    try:
        email_clean = str(email_doc).strip().lower()
        query = db.collection("delegaciones").where("docente_email", "==", email_clean)
        if id_modelo_login:
            query = query.where("id_modelo", "==", str(id_modelo_login))
        docs = list(query.stream())
        if docs:
            for doc in docs:
                datos = doc.to_dict()
                if str(datos.get("secret_hash")).strip() == str(hash_ingresado).strip():
                    datos["id"] = doc.id
                    return True, datos
            return False, "Clave incorrecta."
        return False, "Correo no registrado."
    except Exception as e:
        return False, f"Error: {e}"


@st.cache_data(ttl=30)
def obtener_bancas_asignadas(id_delegacion_doc):
    try:
        docs = db.collection("delegaciones").document(str(id_delegacion_doc)).collection("asignaciones").stream()
        return [doc.to_dict() for doc in docs]
    except Exception:
        return []


def obtener_pagos_delegacion(id_delegacion_doc):
    try:
        docs = db.collection("pagos").where("id_delegacion", "==", str(id_delegacion_doc)).stream()
        return [{**doc.to_dict(), "id_pago": doc.id} for doc in docs]
    except Exception:
        return []


mostrar_encabezado_portal()

if "docente_autenticado" not in st.session_state:
    st.session_state["docente_autenticado"] = False
if "modo_preinscripcion" not in st.session_state:
    st.session_state["modo_preinscripcion"] = False

if "limpiar_formulario" in st.session_state and st.session_state["limpiar_formulario"]:
    st.session_state["limpiar_formulario"] = False
    st.rerun()

if st.session_state["modo_preinscripcion"]:
    st.subheader("📝 Preinscripción Escolar")
    if st.button("⬅️ Volver"):
        st.session_state["modo_preinscripcion"] = False
        st.rerun()

    modelos = obtener_modelos_activos()
    dict_mods_full = {m.get("nombre_visible", m.get("id_modelo")): m for m in modelos}
    mod_sel = st.selectbox("Seleccionar Modelo ONU:", list(dict_mods_full.keys()))
    modelo_objeto = dict_mods_full[mod_sel]
    id_modelo_elegido = modelo_objeto.get("id_modelo")
    comites = obtener_parametros_comites(id_modelo_elegido)

    with st.form("form_preinscripcion_limpio"):
        nombre_colegio = st.text_input("Institución Educativa *:")
        direccion_escuela = st.text_input("Dirección *:")
        email_institucional = st.text_input("Correo Institucional *:")
        telefono_institucional = st.text_input("Teléfono *:")
        docente_apellido_nombre = st.text_input("Responsable (Apellido y Nombre) *:")
        docente_email = st.text_input("Correo Docente (Usuario) *:").strip().lower()
        docente_telefono = st.text_input("Teléfono Móvil *:")
        secret_hash = st.text_input("Clave de Acceso *:", type="password").strip()

        st.markdown("---")
        st.markdown("### 🏛️ Desglose de Delegaciones por Sección")

        desglose_seleccionado = {}
        total_cupos = 0
        if comites:
            secciones_agrupadas = {}
            for c in comites:
                sec = str(c.get("clave_seccion", "GENERAL")).strip()
                organo = str(c.get("organo_comite", "")).strip()
                integrantes = int(c.get("integrantes_por_banca", 1))
                
                if sec not in secciones_agrupadas:
                    secciones_agrupadas[sec] = {
                        "detalles_organos": []
                    }
                secciones_agrupadas[sec]["detalles_organos"].append(f"{organo} ({integrantes} int.)")

            for idx, (sec, datos_sec) in enumerate(secciones_agrupadas.items()):
                lista_organos_int = ", ".join(datos_sec["detalles_organos"])
                
                st.markdown(f"**Sección / Modalidad:** `{sec}` | **Órganos e integrantes:** *{lista_organos_int}*")
                cant = st.number_input(f"Cantidad delegaciones sección {sec}:", min_value=0, value=0, key=f"sec_{sec}_{idx}")
                
                if cant > 0:
                    desglose_seleccionado[sec] = cant
                    integrantes_seccion = sum(int(c.get("integrantes_por_banca", 1)) for c in comites if str(c.get("clave_seccion", "")).strip() == sec)
                    total_cupos += cant * integrantes_seccion
        else:
            st.warning("⚠️ No hay comités configurados para este modelo todavía.")

        st.markdown(f"**📊 Total estimado de participantes / cupos solicitados:** `{total_cupos}`")
        st.markdown("---")

        if st.form_submit_button("Enviar Preinscripción"):
            if not all([nombre_colegio, docente_email, secret_hash]) or total_cupos == 0:
                st.error("Complete todos los campos obligatorios y seleccione al menos 1 delegación.")
            else:
                ok, msg = preinscribir_escuela({
                    "nombre_colegio": nombre_colegio, "direccion_escuela": direccion_escuela,
                    "email_institucional": email_institucional, "telefono_institucional": telefono_institucional,
                    "docente_apellido_nombre": docente_apellido_nombre, "docente_email": docente_email,
                    "docente_telefono": docente_telefono, "cupos_solicitados": total_cupos,
                    "desglose_modalidades": str(desglose_seleccionado), "secret_hash": secret_hash,
                    "id_modelo": id_modelo_elegido
                })
                if ok:
                    st.success("¡Preinscripción exitosa! Ya puedes iniciar sesión.")
                    st.session_state["limpiar_formulario"] = True
                    st.session_state["modo_preinscripcion"] = False
                    st.rerun()
                else:
                    st.error(msg)

elif not st.session_state["docente_autenticado"]:
    st.subheader("🔑 Inicio de Sesión Docente")
    modelos = obtener_modelos_activos()
    dict_mods_login = {m.get("nombre_visible", m.get("id_modelo")): m.get("id_modelo") for m in modelos}
    mod_sel_login = st.selectbox("Modelo ONU:", list(dict_mods_login.keys()))
    id_modelo_ingreso = dict_mods_login[mod_sel_login]

    with st.form("form_login_docente_limpio"):
        email_doc = st.text_input("Correo Docente:").strip().lower()
        hash_ingresado = st.text_input("Clave de Acceso:", type="password").strip()

        if st.form_submit_button("Iniciar Sesión"):
            ok, escuela = validar_acceso_docente(email_doc, hash_ingresado, id_modelo_ingreso)
            if ok:
                st.session_state["docente_autenticado"] = True
                st.session_state["id_delegacion_activa"] = escuela.get("id")
                st.session_state["escuela_info"] = escuela
                st.session_state["id_modelo_activo"] = id_modelo_ingreso
                st.rerun()
            else:
                st.error(escuela)

    if st.button("📝 Registrar nueva institución / Modelo"):
        st.session_state["modo_preinscripcion"] = True
        st.rerun()

else:
    escuela_actual = st.session_state["escuela_info"]
    id_del_activo = st.session_state["id_delegacion_activa"]
    
    doc_actualizado = db.collection("delegaciones").document(id_del_activo).get()
    if doc_actualizado.exists:
        escuela_actual = doc_actualizado.to_dict()

    costo_asignado = float(escuela_actual.get("costo_asignado", 0.0))
    bancas_asignadas = obtener_bancas_asignadas(id_del_activo)
    tiene_bancas = len(bancas_asignadas) > 0

    st.sidebar.markdown(f"**🏛️ Institución:** {escuela_actual.get('nombre_colegio')}")
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🧭 Menú Institucional (Secuenciado)")

    st.sidebar.button("📊 Estado de mi Institución", use_container_width=True)
    
    if costo_asignado > 0:
        if st.sidebar.button("💳 Pagos y Facturación", use_container_width=True):
            st.session_state["sub_menu"] = "Pago"
            st.rerun()
    else:
        st.sidebar.markdown("🔒 **Pagos:** *(Habilitado al recibir presupuesto)*")

    if st.sidebar.button("🛡️ Póliza de Seguro", use_container_width=True):
        st.session_state["sub_menu"] = "Seguro"
        st.rerun()

    if tiene_bancas:
        if st.sidebar.button("📋 Carga de Nómina y Alumnos", use_container_width=True):
            st.session_state["sub_menu"] = "Nomina"
            st.rerun()
    else:
        st.sidebar.markdown("🔒 **Nómina:** *(Habilitado tras el Sorteo)*")

    if st.sidebar.button("🚪 Cerrar Sesión", use_container_width=True):
        st.session_state["docente_autenticado"] = False
        st.rerun()

    sub_menu = st.session_state.get("sub_menu", "Estado")

    if sub_menu == "Estado":
        st.subheader("🔑 Estado del Trámite Institucional")
        st.info(f"Estado del legajo: **{escuela_actual.get('estado', 'PREINSCRIPTO')}**")
        st.metric("Costo Total Asignado", f"${costo_asignado:,.2f}")
        
        if bancas_asignadas:
            st.markdown("#### 🌍 Bancas / Países Asignados:")
            for b in bancas_asignadas:
                st.write(f"- **{b.get('organo_comite', b.get('organo'))}** — País: **{b.get('pais')}**")
        else:
            st.warning("⏳ Las bancas y países se habilitarán una vez que la secretaría ejecute el sorteo oficial.")

    elif sub_menu == "Pago" and costo_asignado > 0:
        st.subheader("💳 Pagos y Facturación")
        pagos = obtener_pagos_delegacion(id_del_activo)
        for p in pagos:
            st.write(f"- Monto: ${p.get('monto')} | Estado: `{p.get('estado_pago')}`")
            if p.get("factura_url"):
                st.markdown(f"🧾 **[Ver Factura Oficial]({p.get('factura_url')})**", unsafe_allow_html=True)

        with st.form("form_pago_limpio"):
            monto_pago = st.number_input("Monto Abonado ($):", min_value=0.0, value=costo_asignado)
            archivo_comprobante = st.file_uploader("Comprobante de Pago (PDF/Imagen):", type=["pdf", "png", "jpg", "jpeg"])
            if st.form_submit_button("Enviar Comprobante"):
                if archivo_comprobante:
                    ok_sub, url_com = subir_archivo_a_drive_via_script(archivo_comprobante.read(), archivo_comprobante.name, archivo_comprobante.type, FOLDER_COMPROBANTES)
                    if ok_sub:
                        db.collection("pagos").add({
                            "id_delegacion": id_del_activo, "docente_email": escuela_actual.get("docente_email"),
                            "id_modelo": st.session_state["id_modelo_activo"], "monto": float(monto_pago),
                            "drive_file_url": url_com, "estado_pago": "PENDIENTE", "fecha_subida": firestore.SERVER_TIMESTAMP
                        })
                        st.success("¡Comprobante enviado con éxito!")
                        st.session_state["limpiar_formulario"] = True
                        st.rerun()

    elif sub_menu == "Seguro":
        st.subheader("🛡️ Póliza de Seguro Institucional")
        seguro_actual = escuela_actual.get("poliza_seguro_url", "")
        if seguro_actual:
            st.markdown(f"🛡️ **[Ver Póliza Cargada]({seguro_actual})**", unsafe_allow_html=True)

        with st.form("form_seguro_limpio"):
            archivo_seguro = st.file_uploader("Póliza de Seguro (PDF/Imagen):", type=["pdf", "png", "jpg", "jpeg"])
            if st.form_submit_button("Subir Póliza"):
                if archivo_seguro:
                    ok_sub, url_seg = subir_archivo_a_drive_via_script(archivo_seguro.read(), archivo_seguro.name, archivo_seguro.type, FOLDER_SEGUROS)
                    if ok_sub:
                        db.collection("delegaciones").document(id_del_activo).set({"poliza_seguro_url": url_seg}, merge=True)
                        st.success("¡Póliza registrada con éxito!")
                        st.session_state["limpiar_formulario"] = True
                        st.rerun()

    elif sub_menu == "Nomina" and tiene_bancas:
        st.subheader("📋 Carga de Estudiantes por Banca Asignada")
        dict_bancas = {f"{b.get('organo_comite', b.get('organo'))} — {b.get('pais')}": b for b in bancas_asignadas}
        banca_sel_nombre = st.selectbox("Seleccionar Banca:", list(dict_bancas.keys()))
        banca_objeto = dict_bancas[banca_sel_nombre]

        with st.form("form_nomina_limpia"):
            nombre = st.text_input("Nombre del Estudiante:")
            apellido = st.text_input("Apellido:")
            dni = st.text_input("DNI:")
            alergias = st.text_input("Alergias / Condiciones médicas:", value="Ninguna")
            file_ficha = st.file_uploader("Ficha Médica:", type=["pdf", "png", "jpg", "jpeg"])
            file_aut = st.file_uploader("Autorización Firmada:", type=["pdf", "png", "jpg", "jpeg"])

            if st.form_submit_button("Guardar Estudiante"):
                if not nombre or not apellido or not dni:
                    st.error("Complete nombre, apellido y DNI.")
                else:
                    ficha_url, aut_url = "", ""
                    if file_ficha:
                        _, ficha_url = subir_archivo_a_drive_via_script(file_ficha.read(), file_ficha.name, file_ficha.type, FOLDER_FICHAS)
                    if file_aut:
                        _, aut_url = subir_archivo_a_drive_via_script(file_aut.read(), file_aut.name, file_aut.type, FOLDER_FICHAS)

                    id_integ = f"{dni}_{banca_objeto.get('organo', 'banca')}".replace(" ", "_").lower()
                    db.collection("delegaciones").document(id_del_activo).collection("integrantes").document(id_integ).set({
                        "nombre": nombre, "apellido": apellido, "dni": dni,
                        "alergias_medicas": alergias, "ficha_medica_id": ficha_url,
                        "autorizacion_id": aut_url, "id_asignacion": banca_objeto.get("organo")
                    }, merge=True)
                    st.success("¡Estudiante guardado en nómina con éxito!")
                    st.session_state["limpiar_formulario"] = True
                    st.rerun()
