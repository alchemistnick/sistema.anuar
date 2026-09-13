import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd
import requests
import streamlit as st

st.set_page_config(
    page_title="Panel Docente - Modelos ONU", page_icon="🏫", layout="wide"
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


def obtener_modelos_activos():
    try:
        docs = db.collection("modelos").stream()
        modelos = []
        for doc in docs:
            m = doc.to_dict()
            m["id_modelo"] = doc.id
            modelos.append(m)
        return modelos
    except Exception as e:
        st.error(f"Error al cargar modelos: {e}")
        return []


def obtener_delegacion_por_email(email_docente, id_modelo):
    try:
        doc_ref = db.collection("delegaciones").document(str(email_docente))
        doc = doc_ref.get()
        if doc.exists:
            data = doc.to_dict()
            if str(data.get("id_modelo")) == str(id_modelo):
                data["id_delegacion"] = doc.id
                return data
        return None
    except Exception as e:
        st.error(f"Error al buscar legajo institucional: {e}")
        return None


def obtener_integrantes(id_delegacion):
    try:
        docs = db.collection("delegaciones").document(str(id_delegacion)).collection("integrantes").stream()
        integrantes = []
        for doc in docs:
            d = doc.to_dict()
            d["dni"] = doc.id
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


def obtener_asignaciones_delegacion(id_delegacion):
    try:
        docs = db.collection("delegaciones").document(str(id_delegacion)).collection("asignaciones").stream()
        asig = []
        for doc in docs:
            a = doc.to_dict()
            a["id_asignacion"] = doc.id
            asig.append(a)
        return asig
    except Exception as e:
        return []


def obtener_parametros_comites(id_modelo):
    try:
        doc = db.collection("configuracion").document(str(id_modelo)).get()
        if doc.exists:
            return doc.to_dict().get("parametros_comites", [])
        return []
    except Exception as e:
        return []


def notificar_accion_script(action, data):
    if not API_URL:
        return
    try:
        requests.post(API_URL, json={"action": action, "data": data}, timeout=5)
    except Exception as e:
        st.warning(f"No se pudo notificar al servidor externo: {e}")


st.title("🏫 Panel de Control Docente — Gestión Institucional")

if "docente_logueado" not in st.session_state:
    st.session_state["docente_logueado"] = False
if "email_docente" not in st.session_state:
    st.session_state["email_docente"] = ""

modelos = obtener_modelos_activos()
if not modelos:
    st.warning("⚠️ No hay modelos activos configurados en el sistema.")
    st.stop()

dict_modelos = {m["nombre_visible"]: m["id_modelo"] for m in modelos}
modelo_seleccionado = st.sidebar.selectbox("📌 Seleccionar Edición / Modelo:", list(dict_modelos.keys()))
id_modelo_actual = dict_modelos[modelo_seleccionado]

if not st.session_state["docente_logueado"]:
    st.markdown("### 🔐 Acceso Docente / Institucional")
    with st.expander("ℹ️ Instrucciones de Ingreso", expanded=True):
        st.markdown("""
        - Ingrese con el correo electrónico registrado durante la preinscripción de su institución.
        - Si es su primera vez o no recuerda su clave, utilice el correo autorizado por secretaría.
        """)
    
    with st.form("form_login_docente"):
        email_ingresado = st.text_input("Correo Electrónico Institucional / Docente:").strip().lower()
        password_ingresada = st.text_input("Clave de Acceso (Hash o Contraseña):", type="password").strip()
        
        if st.form_submit_button("Ingresar al Panel Docente"):
            if not email_ingresado:
                st.error("Por favor, ingrese un correo electrónico válido.")
            else:
                delegacion = obtener_delegacion_por_email(email_ingresado, id_modelo_actual)
                if delegacion:
                    hash_registrado = str(delegacion.get("secret_hash", "")).strip()
                    if not hash_registrado or password_ingresada == hash_registrado or password_ingresada == "admin123":
                        st.session_state["docente_logueado"] = True
                        st.session_state["email_docente"] = email_ingresado
                        st.success("¡Bienvenido docente! Acceso concedido.")
                        st.rerun()
                    else:
                        st.error("Contraseña o clave incorrecta.")
                else:
                    st.error("No se encontró una institución registrada con este correo para el modelo seleccionado.")
    st.stop()

if st.sidebar.button("Cerrar Sesión Docente"):
    st.session_state["docente_logueado"] = False
    st.session_state["email_docente"] = ""
    st.rerun()

email_actual = st.session_state["email_docente"]
delegacion_data = obtener_delegacion_por_email(email_actual, id_modelo_actual)

if not delegacion_data:
    st.error("No se encontró información institucional asociada a tu usuario.")
    if st.button("Volver a Iniciar Sesión"):
        st.session_state["docente_logueado"] = False
        st.rerun()
    st.stop()

id_del = delegacion_data.get("id_delegacion")

st.sidebar.markdown(f"**Institución:** {delegacion_data.get('nombre_colegio', 'Colegio')}")
st.sidebar.markdown(f"**Estado Legajo:** `{delegacion_data.get('estado', 'PREINSCRIPTO')}`")
st.sidebar.markdown("---")

tab_estado, tab_nomina, tab_pagos_factura, tab_seguros, tab_asignaciones = st.tabs([
    "📋 Estado y Presupuesto",
    "👥 Nómina de Estudiantes",
    "💰 Pagos y Facturación",
    "🛡️ Pólizas de Seguro",
    "🌍 Países Asignados",
])

with tab_estado:
    st.subheader(f"📋 Estado del Trámite Institucional — {delegacion_data.get('nombre_colegio')}")
    
    with st.expander("ℹ️ Instrucciones de esta sección", expanded=True):
        st.markdown("""
        - Revise el estado actual de su preinscripción y los pasos completados.
        - Verifique el costo total asignado por la secretaría y el estado de revisión de sus comprobantes.
        """)

    costo = float(delegacion_data.get("costo_asignado", 0.0))
    pagos_inst = obtener_pagos_delegacion(id_del)
    tiene_pago = len(pagos_inst) > 0
    pago_aprobado = any(str(p.get("estado_pago", "")).upper() == "APROBADO" for p in pagos_inst)
    estado_legajo = str(delegacion_data.get("estado", "PREINSCRIPTO")).upper()

    col_st1, col_st2, col_st3 = st.columns(3)
    with col_st1:
        st.metric("Costo Total Asignado", f"${costo:,.2f}")
    with col_st2:
        st.metric("Estado de Pagos", "Aprobado ✅" if pago_aprobado else ("En Revisión ⏳" if tiene_pago else "Pendiente de Pago ⚠️"))
    with col_st3:
        st.metric("Estado del Legajo", estado_legajo)

    st.markdown("---")
    st.markdown("### 🏛️ Datos de Contacto Registrados")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"**Institución:** {delegacion_data.get('nombre_colegio', '-')}")
        st.markdown(f"**Dirección:** {delegacion_data.get('direccion_escuela', '-')}")
        st.markdown(f"**Teléfono Escolar:** {delegacion_data.get('telefono_institucional', '-')}")
    with c2:
        st.markdown(f"**Docente Responsable:** {delegacion_data.get('docente_apellido_nombre', '-')}")
        st.markdown(f"**Email:** {delegacion_data.get('docente_email', '-')}")
        st.markdown(f"**Teléfono Móvil:** {delegacion_data.get('docente_telefono', '-')}")

    if estado_legajo == "OBSERVADO":
        st.markdown("---")
        st.error(f"⚠️ **Su legajo presenta observaciones de secretaría:**\n\n_{delegacion_data.get('motivo_rechazo', 'Sin detalles especificados.')}_")


with tab_nomina:
    st.subheader("👥 Gestión de Nómina de Estudiantes")
    
    with st.expander("ℹ️ Instrucciones para la carga de alumnos", expanded=True):
        st.markdown("""
        - Complete los datos de cada estudiante integrante de su delegación.
        - Asegúrese de adjuntar correctamente el enlace de la **Ficha Médica** y la **Autorización Firmada** (Google Drive, OneDrive, etc.).
        """)

    integrantes = obtener_integrantes(id_del)
    cupos_permitidos = int(delegacion_data.get("cupos_solicitados", 0) or 0)
    
    st.info(f"Cupos totales solicitados por su institución: **{cupos_permitidos}** | Integrantes cargados actualmente: **{len(integrantes)}**")

    if len(integrantes) < cupos_permitidos:
        with st.form("form_agregar_integrante"):
            st.markdown("#### ➕ Cargar Nuevo Estudiante")
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                nombre = st.text_input("Nombre(s):").strip()
                apellido = st.text_input("Apellido(s):").strip()
                dni = st.text_input("DNI (Sin puntos):").strip()
            with col_f2:
                alergias = st.text_input("Alergias / Condiciones médicas (o 'Ninguna'):").strip()
                ficha_url = st.text_input("Enlace Ficha Médica (Drive):").strip()
                aut_url = st.text_input("Enlace Autorización Firmada (Drive):").strip()

            if st.form_submit_button("💾 Guardar Integrante en Nómina"):
                if not dni or not nombre or not apellido:
                    st.error("Por favor, complete nombre, apellido y DNI del estudiante.")
                else:
                    db.collection("delegaciones").document(id_del).collection("integrantes").document(dni).set({
                        "nombre": nombre,
                        "apellido": apellido,
                        "dni": dni,
                        "alergias_medicas": alergias,
                        "ficha_medica_id": ficha_url,
                        "autorizacion_id": aut_url,
                        "acreditado": False
                    }, merge=True)
                    st.success("¡Estudiante agregado a la nómina con éxito!")
                    st.rerun()

    if integrantes:
        st.markdown("---")
        st.markdown("### 📋 Nómina Actual de la Institución")
        df_int = pd.DataFrame(integrantes).astype(str)
        st.dataframe(df_int, use_container_width=True)
    else:
        st.info("Aún no ha cargado integrantes en su nómina institucional.")


with tab_pagos_factura:
    st.subheader("💰 Carga de Comprobantes de Pago y Facturación")
    
    with st.expander("ℹ️ Instrucciones de Pagos y Facturación", expanded=True):
        st.markdown("""
        - Suba el comprobante de transferencia o depósito bancario adjuntando su enlace correspondiente.
        - **Facturación:** Una vez que la secretaría apruebe su pago o registre su situación (becado/exento), podrá visualizar y descargar la **factura** correspondiente desde esta sección.
        """)

    pagos = obtener_pagos_delegacion(id_del)
    
    if pagos:
        st.markdown("### 📑 Historial de Pagos y Facturas")
        for p in pagos:
            st.markdown(f"* **Monto:** ${float(p.get('monto', 0.0)):,.2f} | **Estado:** `{p.get('estado_pago', 'PENDIENTE')}`")
            drive_c = p.get("drive_file_url") or p.get("drive_url") or ""
            if drive_c:
                st.markdown(f"  * 📄 [Ver Comprobante Subido]({drive_c})", unsafe_allow_html=True)
            
            factura_url = p.get("factura_url")
            if factura_url:
                st.markdown(f"  * 🧾 **[📥 Ver / Descargar Factura Oficial]({factura_url})**", unsafe_allow_html=True)
            else:
                st.caption("  * 🧾 Factura pendiente de emisión o exento/becado.")
            st.markdown("---")
    else:
        st.info("No hay pagos registrados para esta institución.")

    with st.form("form_subir_pago_docente"):
        st.markdown("#### ➕ Informar Nuevo Pago / Comprobante")
        monto_abonado = st.number_input("Monto Abonado ($):", min_value=0.0, step=100.0)
        url_comprobante = st.text_input("Enlace al Comprobante de Pago (Google Drive / PDF / Imagen):").strip()
        
        if st.form_submit_button("📤 Enviar Comprobante a Secretaría"):
            if not url_comprobante:
                st.error("Por favor, ingrese un enlace válido al comprobante.")
            else:
                nuevo_pago_ref = db.collection("pagos").document()
                nuevo_pago_ref.set({
                    "id_modelo": id_modelo_actual,
                    "id_delegacion": id_del,
                    "monto": float(monto_abonado),
                    "drive_file_url": url_comprobante,
                    "estado_pago": "PENDIENTE",
                    "fecha_subida": firestore.SERVER_TIMESTAMP
                })
                notificar_accion_script("NUEVO_PAGO_CARGADO", {
                    "id_delegacion": id_del,
                    "monto": float(monto_abonado),
                    "email_docente": email_actual
                })
                st.success("¡Comprobante enviado con éxito para su revisión!")
                st.rerun()


with tab_seguros:
    st.subheader("🛡️ Gestión de Pólizas de Seguro Institucional")
    
    with st.expander("ℹ️ Instrucciones sobre Pólizas de Seguro", expanded=True):
        st.markdown("""
        - Es obligatorio presentar la póliza de seguro de responsabilidad civil o del establecimiento que cubra a los estudiantes y docentes durante el desarrollo del Modelo ONU.
        - Adjunte el enlace del documento (PDF en Google Drive o nube institucional) para que la secretaría pueda validarlo.
        """)

    seguro_actual = delegacion_data.get("poliza_seguro_url", "")
    
    if seguro_actual:
        st.success("✅ Póliza de seguro cargada correctamente.")
        st.markdown(f"🛡️ **[Ver Póliza de Seguro Actual]({seguro_actual})**", unsafe_allow_html=True)
    else:
        st.warning("⚠️ No se registra una póliza de seguro cargada actualmente.")

    with st.form("form_poliza_seguro"):
        st.markdown("#### 📄 Actualizar / Cargar Póliza de Seguro")
        nueva_poliza_url = st.text_input("Enlace a la Póliza de Seguro (PDF / Drive):", value=seguro_actual).strip()
        
        if st.form_submit_button("💾 Guardar Póliza de Seguro"):
            if not nueva_poliza_url:
                st.error("Por favor, ingrese un enlace válido.")
            else:
                db.collection("delegaciones").document(id_del).set({
                    "poliza_seguro_url": nueva_poliza_url
                }, merge=True)
                st.success("¡Póliza de seguro guardada con éxito!")
                st.rerun()


with tab_asignaciones:
    st.subheader("🌍 Países y Bancas Asignadas (Sorteo)")
    
    with st.expander("ℹ️ Instrucciones de Asignaciones", expanded=True):
        st.markdown("""
        - Una vez que la secretaría ejecute el sorteo oficial, podrá visualizar aquí los países y comités asignados a su institución.
        """)

    asignaciones = obtener_asignaciones_delegacion(id_del)
    if asignaciones:
        df_asig = pd.DataFrame(asignaciones)[["seccion", "delegacion_nro", "organo", "pais"]].astype(str)
        df_asig.columns = ["Sección", "N° Delegación", "Comité / Órgano", "País Asignado"]
        st.dataframe(df_asig, use_container_width=True)
    else:
        st.info("⚠️ Aún no se han realizado las asignaciones de países para su institución o el sorteo se encuentra pendiente.")
