import base64
import requests
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore

st.set_page_config(
    page_title="Portal de Instituciones - Modelos ONU", page_icon="🏫", layout="wide"
)

hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

if not firebase_admin._apps:
    cred = credentials.Certificate(dict(st.secrets["firebase"]))
    firebase_admin.initialize_app(cred)

db = firestore.client()
API_URL = st.secrets["API_URL"]


def verificar_credenciales(email, secret_hash):
    try:
        doc = db.collection("delegaciones").document(str(email)).get()
        if doc.exists:
            data = doc.to_dict()
            if str(data.get("secret_hash", "")).strip() == str(secret_hash).strip():
                return data
        return None
    except Exception as e:
        st.error(f"Error al verificar credenciales: {e}")
        return None


def obtener_asignaciones_delegacion(id_delegacion):
    try:
        docs = db.collection("delegaciones").document(str(id_delegacion)).collection("asignaciones").stream()
        asignaciones = []
        for doc in docs:
            a = doc.to_dict()
            a["id_asignacion"] = doc.id
            asignaciones.append(a)
        return asignaciones
    except Exception as e:
        return []


def obtener_parametros_comites_modelo(id_modelo):
    try:
        doc = db.collection("configuracion").document(str(id_modelo)).get()
        if doc.exists:
            return doc.to_dict().get("parametros_comites", [])
        return []
    except Exception as e:
        return []


def obtener_integrantes_delegacion(id_delegacion):
    try:
        docs = db.collection("delegaciones").document(str(id_delegacion)).collection("integrantes").stream()
        integrantes = []
        for doc in docs:
            d = doc.to_dict()
            d["id"] = doc.id
            integrantes.append(d)
        return integrantes
    except Exception as e:
        return []


def obtener_pagos_delegacion(id_delegacion):
    try:
        docs = db.collection("pagos").where("id_delegacion", "==", str(id_delegacion)).stream()
        pagos = []
        for doc in docs:
            p = doc.to_dict()
            p["id_pago"] = doc.id
            pagos.append(p)
        return pagos
    except Exception as e:
        return []


def subir_archivo_a_drive(file_bytes, file_name, mime_type, folder_id):
    try:
        b64_data = base64.b64encode(file_bytes).decode("utf-8")
        payload = {
            "action": "UPLOAD_FILE",
            "fileName": file_name,
            "mimeType": mime_type,
            "fileData": b64_data,
            "folderId": folder_id
        }
        response = requests.post(API_URL, json=payload, timeout=20)
        res_json = response.json()
        if res_json.get("status") == "success":
            return res_json.get("fileUrl")
        return None
    except Exception as e:
        st.error(f"Error al subir archivo: {e}")
        return None


def notificar_accion(action, data):
    if not API_URL:
        return
    try:
        requests.post(API_URL, json={"action": action, "data": data}, timeout=5)
    except Exception:
        pass


st.title("🏫 Portal de Instituciones y Docentes — Modelos ONU")

if "docente_autenticado" not in st.session_state:
    st.session_state["docente_autenticado"] = False
    st.session_state["datos_delegacion"] = None

if not st.session_state["docente_autenticado"]:
    st.markdown("### 🔑 Iniciar Sesión Institucional")
    with st.form("form_login_docente"):
        email_ingresado = st.text_input("Correo Electrónico (Registrado):").strip().lower()
        hash_ingresado = st.text_input("Clave Hash de Acceso:", type="password").strip()
        
        if st.form_submit_button("Ingresar al Portal"):
            delegacion_data = verificar_credenciales(email_ingresado, hash_ingresado)
            if delegacion_data:
                st.session_state["docente_autenticado"] = True
                st.session_state["datos_delegacion"] = delegacion_data
                st.success("¡Bienvenido/a al portal institucional!")
                st.rerun()
            else:
                st.error("Credenciales inválidas. Verifique su correo y clave hash.")
    st.stop()

# Si ya está logueado
delegacion = st.session_state["datos_delegacion"]
id_del = delegacion.get("id_delegacion") or delegacion.get("docente_email")
id_modelo = delegacion.get("id_modelo")

st.sidebar.markdown(f"**🏛️ Institución:** {delegacion.get('nombre_colegio', '-')}")
st.sidebar.markdown(f"**👤 Docente:** {delegacion.get('docente_apellido_nombre', '-')}")
st.sidebar.markdown(f"**📌 Modelo:** `{id_modelo}`")
st.sidebar.markdown("---")

if st.sidebar.button("Cerrar Sesión"):
    st.session_state["docente_autenticado"] = False
    st.session_state["datos_delegacion"] = None
    st.rerun()

menu_docente = st.selectbox(
    "Seleccionar Opción:",
    ["📋 Carga de Nómina y Documentación", "💰 Gestión de Pagos y Presupuesto"]
)

if menu_docente == "📋 Carga de Nómina y Documentación":
    st.subheader("📋 Carga de Integrantes por Banca Asignada")

    asignaciones = obtener_asignaciones_delegacion(id_del)
    if not asignaciones:
        st.warning("⚠️ Su institución aún no tiene países o bancas asignadas por el secretariado (el sorteo está pendiente o en proceso).")
    else:
        parametros_comites = obtener_parametros_comites_modelo(id_modelo)
        mapa_limite_integrantes = {str(c.get("organo_comite")).strip(): int(c.get("integrantes_por_banca", 1)) for c in parametros_comites}

        opciones_banca = {}
        for a in asignaciones:
            org = a.get("organo", "")
            pais = a.get("pais", "")
            label = f"{org} — {pais}"
            opciones_banca[label] = a

        banca_elegida_label = st.selectbox("Seleccionar Banca / Asignación para cargar participante:", list(opciones_banca.keys()))
        banca_seleccionada = opciones_banca[banca_elegida_label]
        
        organo_actual = banca_seleccionada.get("organo", "")
        limite_permitido = mapa_limite_integrantes.get(organo_actual, 1)

        st.info(f"📌 El órgano **{organo_actual}** permite hasta **{limite_permitido} estudiante(s)**.")

        # Verificar cuántos hay cargados en esta banca específica
        integrantes_actuales = obtener_integrantes_delegacion(id_del)
        integrantes_en_banca = [i for i in integrantes_actuales if i.get("id_asignacion") == organo_actual or i.get("pais") == banca_seleccionada.get("pais")]

        if len(integrantes_en_banca) >= limite_permitido:
            st.success(f"✅ Ya se completó el cupo de {limite_permitido} estudiante(s) para esta banca ({banca_elegida_label}).")
            with st.expander("Ver estudiantes cargados en esta banca"):
                for est in integrantes_en_banca:
                    st.write(f"- **{est.get('nombre')} {est.get('apellido')}** (DNI: {est.get('dni')})")
        else:
            with st.form("form_carga_integrante"):
                col_f1, col_f2 = st.columns(2)
                with col_f1:
                    nombre = st.text_input("Nombre del Estudiante:")
                    apellido = st.text_input("Apellido:")
                    dni = st.text_input("DNI:")
                with col_f2:
                    alergias = st.text_input("Alergias / Condición Médica (opcional):", value="Ninguna")
                    file_ficha = st.file_uploader("Ficha Médica (PDF/Imagen):", type=["pdf", "png", "jpg", "jpeg"])
                    file_aut = st.file_uploader("Autorización Firmada (PDF/Imagen):", type=["pdf", "png", "jpg", "jpeg"])

                comentarios = st.text_area("Comentarios / Observaciones sobre este participante (opcional):")

                if st.form_submit_button("💾 Guardar Participante en Nómina"):
                    if not nombre or not apellido or not dni:
                        st.error("Por favor,complete Nombre, Apellido y DNI.")
                    else:
                        folder_id = delegacion.get("drive_folder_id", "")
                        ficha_url = ""
                        autorizacion_url = ""

                        if file_ficha:
                            ficha_bytes = file_ficha.read()
                            ficha_url = subir_archivo_a_drive(ficha_bytes, f"Ficha_{dni}_{nombre}.pdf", file_ficha.type, folder_id) or ""

                        if file_aut:
                            aut_bytes = file_aut.read()
                            autorizacion_url = subir_archivo_a_drive(aut_bytes, f"Autorizacion_{dni}_{nombre}.pdf", file_aut.type, folder_id) or ""

                        # CORRECCIÓN CLAVE: ID Único combinando DNI y Órgano/Banca para evitar sobreescrituras en bancas dobles
                        org_limpio = str(organo_actual).replace(" ", "_").replace("/", "_").lower()
                        id_documento_estudiante = f"{dni}_{org_limpio}"

                        payload_estudiante = {
                            "nombre": nombre.strip(),
                            "apellido": apellido.strip(),
                            "dni": dni.strip(),
                            "id_asignacion": organo_actual,
                            "pais": banca_seleccionada.get("pais", ""),
                            "alergias_medicas": alergias.strip(),
                            "comentarios": comentarios.strip(),
                            "ficha_medica_id": ficha_url,
                            "autorizacion_id": autorizacion_url,
                            "acreditado": False
                        }

                        db.collection("delegaciones").document(id_del).collection("integrantes").document(id_documento_estudiante).set(payload_estudiante, merge=True)
                        st.success("¡Estudiante guardado con éxito en la nómina!")
                        st.rerun()

        st.markdown("---")
        st.subheader("👥 Listado General de Integrantes Cargados")
        todos_integrantes = obtener_integrantes_delegacion(id_del)
        if todos_integrantes:
            df_nom = pd.DataFrame(todos_integrantes).astype(str)
            st.dataframe(df_nom, use_container_width=True)
            
            if st.button("🚀 Enviar Legajo / Cerrar Carga para Auditoría"):
                db.collection("delegaciones").document(id_del).set({"estado": "DOCUMENTACION_COMPLETA"}, merge=True)
                notificar_accion("CONFIRMAR_CARGA_DOCUMENTACION", {
                    "id_delegacion": id_del,
                    "email_docente": delegacion.get("docente_email", "")
                })
                st.success("¡Legajo enviado a secretaría con éxito!")
                st.rerun()
        else:
            st.info("No hay integrantes registrados todavía.")

elif menu_docente == "💰 Gestión de Pagos y Presupuesto":
    st.subheader("💰 Presupuesto Asignado y Comprobantes")

    costo_asignado = float(delegacion.get("costo_asignado", 0.0))
    st.markdown(f"### 💵 Monto Total a Abonar: **${costo_asignado:,.2f}**")

    pagos_reg = obtener_pagos_delegacion(id_del)
    if pagos_reg:
        st.markdown("#### Comprobantes Subidos:")
        for p in pagos_reg:
            st.write(f"- Monto: **${p.get('monto', 0):,.2f}** | Estado: `{p.get('estado_pago', 'PENDIENTE')}` | [Ver Comprobante]({p.get('drive_file_url', '#')})")
    else:
        st.info("Aún no ha registrado pagos.")

    st.markdown("---")
    st.markdown("#### 📤 Subir Nuevo Comprobante de Pago")
    with st.form("form_subir_pago"):
        monto_abonado = st.number_input("Monto Abonado ($):", min_value=0.0, step=100.0)
        file_comprobante = st.file_uploader("Adjuntar Comprobante (PDF/Imagen):", type=["pdf", "png", "jpg", "jpeg"])

        if st.form_submit_button("📤 Enviar Comprobante a Secretaría"):
            if not file_comprobante or monto_abonado <= 0:
                st.error("Ingrese un monto válido y adjunte el archivo del comprobante.")
            else:
                folder_id = delegacion.get("drive_folder_id", "")
                comp_bytes = file_comprobante.read()
                comp_url = subir_archivo_a_drive(comp_bytes, f"Pago_{id_del}.pdf", file_comprobante.type, folder_id)

                if comp_url:
                    pago_id = f"pago_{id_del}_{int(requests.get('https://api.ipify.org').status_code or 0) + 1000}"
                    pago_payload = {
                        "id_modelo": id_modelo,
                        "id_delegacion": id_del,
                        "monto": float(monto_abonado),
                        "drive_file_url": comp_url,
                        "estado_pago": "PENDIENTE",
                        "fecha_subida": firestore.SERVER_TIMESTAMP
                    }
                    db.collection("pagos").document(pago_id).set(pago_payload)
                    notificar_accion("NUEVO_PAGO_REGISTRADO", {
                        "id_delegacion": id_del,
                        "monto": float(monto_abonado),
                        "drive_url": comp_url
                    })
                    st.success("¡Comprobante subido y enviado correctamente!")
                    st.rerun()
                else:
                    st.error("Error al subir el archivo a Google Drive.")
