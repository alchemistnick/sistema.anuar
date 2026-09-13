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

FOLDER_COMPROBANTES = "1-QVd95Y2butIg9DNp3cPuIQI6sII50Rk"
FOLDER_FICHAS = "1VSSud30QL9nSLbfu4jAz-dJ9q2rcRg1E"


def subir_archivo_a_drive_via_script(
    file_bytes, file_name, mime_type, folder_id
):
    try:
        base64_data = base64.b64encode(file_bytes).decode("utf-8")
        payload = {
            "action": "UPLOAD_FILE",
            "fileData": base64_data,
            "fileName": file_name,
            "mimeType": mime_type,
            "folderId": folder_id,
        }
        res = requests.post(
            API_URL, json=payload, timeout=60, allow_redirects=True
        )
        
        try:
            res_json = res.json()
            if res_json.get("status") == "success":
                file_url = res_json.get("fileUrl") or res_json.get("url")
                if file_url:
                    return True, file_url
            else:
                return False, f"Error del Script: {res_json.get('message', 'Desconocido')}"
        except Exception as json_err:
            return False, f"Respuesta inválida del servidor: {res.text[:200]}"
            
    except Exception as e:
        return False, f"Excepción de red al conectar con la API: {e}"


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
        st.error(f"Error al conectar con Firestore: {e}")
        return []


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

        if not docente_email or "@" not in docente_email:
            return False, "Debe ingresar un correo electrónico válido."

        docs_existentes = db.collection("delegaciones").where("docente_email", "==", docente_email).where("id_modelo", "==", id_modelo_nuevo).stream()
        if list(docs_existentes):
            return False, f"El correo '{docente_email}' ya se encuentra preinscripto en este modelo específico."

        id_doc_delegacion = f"{docente_email}_{id_modelo_nuevo}"
        doc_ref = db.collection("delegaciones").document(id_doc_delegacion)

        payload = {
            "id_delegacion": id_doc_delegacion,
            "estado": "PREINSCRIPTO",
            "fecha_registro": firestore.SERVER_TIMESTAMP,
            **datos_escuela,
        }

        doc_ref.set(payload, merge=True)
        return True, id_doc_delegacion
    except Exception as e:
        return False, f"Error al registrar la institución: {e}"


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
            return False, "Clave de acceso incorrecta."
        return False, "El correo electrónico no se encuentra registrado en este modelo."
    except Exception as e:
        return False, f"Error al validar acceso: {e}"


def obtener_bancas_asignadas(id_delegacion_doc):
    try:
        docs = (
            db.collection("delegaciones")
            .document(str(id_delegacion_doc))
            .collection("asignaciones")
            .stream()
        )
        return [doc.to_dict() for doc in docs]
    except Exception:
        return []


def guardar_participante_nomina(id_delegacion_doc, dni, datos_participante):
    try:
        id_asig_raw = str(datos_participante.get("id_asignacion", "general"))
        id_asig_limpio = id_asig_raw.replace(" ", "_").replace("/", "_").lower()
        id_documento_integrante = f"{dni}_{id_asig_limpio}"

        db.collection("delegaciones").document(str(id_delegacion_doc)).collection(
            "integrantes"
        ).document(id_documento_integrante).set(datos_participante, merge=True)
        return True, "Participante guardado correctamente."
    except Exception as e:
        return False, f"Error al guardar participante: {e}"


def registrar_pago_comprobante(id_delegacion_doc, email_doc, id_modelo, monto, drive_url):
    try:
        pago_ref = db.collection("pagos").document()
        payload = {
            "id_delegacion": str(id_delegacion_doc),
            "docente_email": str(email_doc).strip().lower(),
            "id_modelo": str(id_modelo),
            "monto": float(monto),
            "drive_file_url": drive_url,
            "estado_pago": "PENDIENTE",
            "fecha_subida": firestore.SERVER_TIMESTAMP,
        }
        pago_ref.set(payload)
        return True, pago_ref.id
    except Exception as e:
        return False, str(e)


def actualizar_estado_legajo(id_delegacion_doc, estado):
    try:
        db.collection("delegaciones").document(str(id_delegacion_doc)).set(
            {"estado": estado}, merge=True
        )
        return True
    except Exception:
        return False


def notificar_apps_script(action, data):
    try:
        requests.post(API_URL, json={"action": action, "data": data}, timeout=5)
    except Exception:
        pass


st.title("🏫 Portal de Instituciones - Modelos ONU")

if "docente_autenticado" not in st.session_state:
    st.session_state["docente_autenticado"] = False
if "modo_preinscripcion" not in st.session_state:
    st.session_state["modo_preinscripcion"] = False

# ==========================================
# VISTA 1: PREINSCRIPCIÓN A NUEVO MODELO
# ==========================================
if st.session_state["modo_preinscripcion"]:
    st.subheader("📝 Formulario de Preinscripción Escolar")

    if st.button("⬅️ Volver al Inicio de Sesión"):
        st.session_state["modo_preinscripcion"] = False
        st.rerun()

    modelos = obtener_modelos_activos()
    if not modelos:
        st.warning("⚠️ No hay modelos activos en la base de datos.")
        st.stop()

    dict_mods_full = {
        m.get("nombre_visible", m.get("id_modelo")): m for m in modelos
    }
    mod_sel = st.selectbox("Seleccionar Modelo ONU:", list(dict_mods_full.keys()))

    modelo_objeto = dict_mods_full[mod_sel]
    id_modelo_elegido = modelo_objeto.get("id_modelo")
    comites = obtener_parametros_comites(id_modelo_elegido)

    with st.form("form_preinscripcion"):
        st.markdown("### 🏛️ Datos de la Institución (Todos obligatorios)")
        col1, col2 = st.columns(2)
        with col1:
            nombre_colegio = st.text_input("Nombre de la Institución Educativa (con N° DIPE/CUE) *:")
            direccion_escuela = st.text_input("Dirección (Localidad, Provincia, País) *:")
            email_institucional = st.text_input("Correo Electrónico Institucional *:")
            telefono_institucional = st.text_input("Número de Teléfono *:")

        with col2:
            st.markdown("### 👨‍🏫 Datos del Responsable / Docente")
            docente_apellido_nombre = st.text_input("Apellido y Nombre *:")
            docente_email = st.text_input("Correo Electrónico Docente (Será su usuario) *:").strip().lower()
            docente_telefono = st.text_input("Teléfono Móvil *:")
            secret_hash = st.text_input("Crear Clave de Acceso para la Escuela *:", type="password").strip()

        st.markdown("---")
        st.markdown("### 🇺🇳 Datos de las Delegaciones y Comisiones")

        desglose_seleccionado = {}
        total_cupos_calculados = 0
        exclusiones_map = {}

        if comites:
            secciones = {}
            for c in comites:
                sec = str(c.get("clave_seccion", "GENERAL")).strip()
                if sec not in secciones:
                    secciones[sec] = []
                secciones[sec].append(c)
                
                excluye_raw = str(c.get("excluye_secciones", "")).strip()
                if excluye_raw and excluye_raw.lower() != "nan":
                    if sec not in exclusiones_map:
                        exclusiones_map[sec] = set()
                    for e in excluye_raw.split(","):
                        if e.strip():
                            exclusiones_map[sec].add(e.strip())

            for sec_nombre, lista_comites in secciones.items():
                col_sec, col_cant = st.columns([3, 1])
                nombres_comites = ", ".join([str(x.get("organo_comite", "")).strip() for x in lista_comites])
                integrantes_totales = sum([int(x.get("integrantes_por_banca", 1)) for x in lista_comites])

                max_permiso = 4
                for x in lista_comites:
                    val_max = x.get("max_delegaciones_seccion")
                    if val_max is not None and str(val_max).isdigit():
                        max_permiso = int(val_max)
                        break

                opciones_cant = list(range(0, max_permiso + 1))

                with col_sec:
                    st.write(f"**Sección {sec_nombre}:** {nombres_comites} (*{integrantes_totales} participantes por delegación - Máx: {max_permiso}*)")
                with col_cant:
                    cant = st.selectbox(f"Cantidad ({sec_nombre}):", options=opciones_cant, key=f"sec_{sec_nombre}")
                    if cant > 0:
                        desglose_seleccionado[sec_nombre] = cant
                        total_cupos_calculados += cant * integrantes_totales
        else:
            st.warning("⚠️ No se han parametrizado comisiones para este modelo.")

        docentes_acompanantes = st.number_input("Docentes Acompañantes:", min_value=1, value=1, step=1)
        st.info(f"📊 **Total de participantes acumulados:** {total_cupos_calculados} estudiantes.")

        submitted = st.form_submit_button("Enviar Preinscripción Institucional")

        if submitted:
            if not nombre_colegio.strip() or not direccion_escuela.strip() or not email_institucional.strip() or not telefono_institucional.strip() or not docente_apellido_nombre.strip() or not docente_email.strip() or not docente_telefono.strip() or not secret_hash.strip():
                st.error("❌ Todos los campos institucionales y del docente son obligatorios.")
            else:
                error_exclusion = False
                secciones_elegidas = list(desglose_seleccionado.keys())
                
                for sec in secciones_elegidas:
                    if sec in exclusiones_map:
                        for prohibida in exclusiones_map[sec]:
                            if prohibida in secciones_elegidas:
                                st.error(f"❌ **Incompatibilidad detectada:** No puede seleccionar simultáneamente las secciones **'{sec}'** y **'{prohibida}'** ya que se excluyen mutuamente.")
                                error_exclusion = True
                                break
                    if error_exclusion:
                        break

                if not error_exclusion:
                    if total_cupos_calculados == 0:
                        st.error("Seleccione al menos 1 delegación para inscribir.")
                    else:
                        datos_escuela = {
                            "nombre_colegio": nombre_colegio,
                            "direccion_escuela": direccion_escuela,
                            "email_institucional": email_institucional,
                            "telefono_institucional": telefono_institucional,
                            "docente_apellido_nombre": docente_apellido_nombre,
                            "docente_email": docente_email,
                            "docente_telefono": docente_telefono,
                            "cupos_solicitados": total_cupos_calculados,
                            "desglose_modalidades": str(desglose_seleccionado),
                            "docentes_acompanantes": docentes_acompanantes,
                            "secret_hash": secret_hash,
                            "id_modelo": id_modelo_elegido,
                        }
                        ok, msg = preinscribir_escuela(datos_escuela)
                        if ok:
                            st.success(f"¡Preinscripción exitosa! Su usuario de acceso es: **{docente_email}**.")
                            notificar_apps_script("NUEVA_PREINSCRIPCION", {
                                "id_delegacion": msg,
                                "docente_email": docente_email,
                                "desglose": str(desglose_seleccionado)
                            })
                        else:
                            st.error(msg)

# ==========================================
# VISTA 2: PANTALLA DE INICIO DE SESIÓN
# ==========================================
elif not st.session_state["docente_autenticado"]:
    st.subheader("🔑 Inicio de Sesión - Portal de Instituciones")
    st.markdown("Ingrese sus credenciales institucionales para acceder a los módulos de gestión.")

    modelos = obtener_modelos_activos()
    id_modelo_ingreso = ""
    if modelos:
        dict_mods_login = {m.get("nombre_visible", m.get("id_modelo")): m.get("id_modelo") for m in modelos}
        mod_sel_login = st.selectbox("Seleccionar Modelo ONU al que desea ingresar:", list(dict_mods_login.keys()))
        id_modelo_ingreso = dict_mods_login[mod_sel_login]

    with st.form("form_login_escuela"):
        email_doc = st.text_input("Email del Docente Responsable:").strip().lower()
        hash_ingresado = st.text_input("Clave de Acceso:", type="password").strip()

        if st.form_submit_button("Iniciar Sesión"):
            ok, escuela = validar_acceso_docente(email_doc, hash_ingresado, id_modelo_ingreso)
            if ok:
                st.session_state["docente_autenticado"] = True
                st.session_state["id_delegacion_activa"] = escuela.get("id")
                st.session_state["escuela_info"] = escuela
                st.session_state["id_modelo_activo"] = id_modelo_ingreso
                st.success("¡Acceso correcto! Cargando módulos...")
                st.rerun()
            else:
                st.error(escuela)

    st.markdown("---")
    st.markdown("### ¿Desea inscribirse a un Modelo nuevo?")
    if st.button("📝 Inscribirme a un Modelo Nuevo"):
        st.session_state["modo_preinscripcion"] = True
        st.rerun()

# ==========================================
# VISTA 3: MÓDULOS HABILITADOS TRAS EL LOGIN
# ==========================================
else:
    escuela_actual = st.session_state["escuela_info"]
    id_del_activo = st.session_state["id_delegacion_activa"]
    id_modelo_activo = st.session_state.get("id_modelo_activo", "")

    st.sidebar.markdown(f"**🏛️ Institución:** {escuela_actual.get('nombre_colegio')}")
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🧭 Menú de Gestión Segura")

    if st.sidebar.button("📊 Estado de mi Institución", use_container_width=True):
        st.session_state["sub_menu"] = "Estado"
        st.rerun()
    if st.sidebar.button("💳 Subir Comprobante de Pago", use_container_width=True):
        st.session_state["sub_menu"] = "Pago"
        st.rerun()
    if st.sidebar.button("📋 Carga de Nómina y Documentación", use_container_width=True):
        st.session_state["sub_menu"] = "Nomina"
        st.rerun()
    
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Cerrar Sesión", use_container_width=True):
        st.session_state["docente_autenticado"] = False
        st.session_state["id_delegacion_activa"] = None
        st.session_state["escuela_info"] = None
        st.rerun()

    if "sub_menu" not in st.session_state:
        st.session_state["sub_menu"] = "Estado"

    sub_menu = st.session_state["sub_menu"]

    if sub_menu == "Estado":
        st.subheader("🔑 Estado de mi Institución y Asignaciones")
        st.markdown(f"### 🏛️ {escuela_actual.get('nombre_colegio')}")
        st.info(f"Estado actual del legajo: **{escuela_actual.get('estado', 'PREINSCRIPTO')}**")
        
        bancas = obtener_bancas_asignadas(id_del_activo)
        if bancas:
            st.markdown("#### 🌍 Bancas / Países Asignados:")
            for b in bancas:
                st.write(f"- **{b.get('organo_comite', b.get('organo'))}** — País: **{b.get('pais')}**")
        else:
            st.info("Aún no se han publicado las bancas asignadas para tu institución.")

    elif sub_menu == "Pago":
        st.subheader("💳 Subir Comprobante de Pago")
        with st.form("form_pago_seguro"):
            monto_pago = st.number_input("Monto Abonado ($):", min_value=0.0, format="%.2f")
            archivo_comprobante = st.file_uploader("Seleccionar Comprobante de Pago (PDF o Imagen):", type=["pdf", "png", "jpg", "jpeg"])

            if st.form_submit_button("Enviar Comprobante"):
                if not archivo_comprobante:
                    st.error("Adjunta el archivo del comprobante.")
                else:
                    try:
                        with st.spinner("Subiendo comprobante a Google Drive..."):
                            file_bytes = archivo_comprobante.read()
                            file_name = f"Pago_{escuela_actual.get('docente_email')}_{archivo_comprobante.name}"
                            mime_type = archivo_comprobante.type

                            ok_subida, res_url = subir_archivo_a_drive_via_script(
                                file_bytes, file_name, mime_type, FOLDER_COMPROBANTES
                            )

                            if not ok_subida:
                                st.error(f"No se pudo completar la subida del archivo: {res_url}")
                            else:
                                ok_pago, idPago = registrar_pago_comprobante(
                                    id_del_activo, escuela_actual.get('docente_email'), id_modelo_activo, float(monto_pago), res_url
                                )
                                
                                if ok_pago:
                                    st.success(f"¡Comprobante subido y registrado con éxito! ID: `{idPago}`")
                                    notificar_apps_script("NUEVO_PAGO_REGISTRADO", {
                                        "id_delegacion": id_del_activo,
                                        "monto": float(monto_pago),
                                        "drive_url": res_url,
                                    })
                                    st.balloons()
                                else:
                                    st.error(f"Error al registrar en Firestore: {idPago}")
                    except Exception as ex:
                        st.error(f"Error crítico: {ex}")

    elif sub_menu == "Nomina":
        st.subheader("📋 Registro de Participantes y Documentación")
        
        bancas_asignadas = obtener_bancas_asignadas(id_del_activo)
        comites_reglas = obtener_parametros_comites(id_modelo_activo)
        mapa_reglas = {str(c.get("organo_comite")).strip().upper(): c for c in comites_reglas}

        if not bancas_asignadas:
            st.warning("⚠️ Tu institución aún no tiene bancas/países asignados por la organización.")
        else:
            dict_bancas = {f"{b.get('organo_comite', b.get('organo'))} — {b.get('pais')}": b for b in bancas_asignadas}
            banca_sel_nombre = st.selectbox("Seleccionar Banca / Asignación para cargar participante:", list(dict_bancas.keys()))
            banca_objeto = dict_bancas[banca_sel_nombre]

            organo_banca = str(banca_objeto.get("organo_comite", banca_objeto.get("organo"))).strip().upper()
            regla_comite = mapa_reglas.get(organo_banca, {})
            integrantes_permitidos = int(regla_comite.get("integrantes_por_banca", 2))

            st.info(f"📌 El órgano **{organo_banca}** requiere/permite hasta **{integrantes_permitidos} estudiante(s)**. Complete los campos correspondientes a continuación:")

            with st.form("form_estudiante_multiple"):
                estudiantes_datos = []
                
                for i in range(1, integrantes_permitidos + 1):
                    st.markdown(f"#### 👤 Integrante N° {i}")
                    col_a, col_b = st.columns(2)
                    with col_a:
                        nombre = st.text_input(f"Nombre del Estudiante {i}:", key=f"nombre_{i}")
                        apellido = st.text_input(f"Apellido {i}:", key=f"apellido_{i}")
                        dni = st.text_input(f"DNI {i}:", key=f"dni_{i}")
                    with col_b:
                        alergias = st.text_input(f"Alergias / Condición Médica {i}:", value="Ninguna", key=f"alergias_{i}")
                        file_ficha = st.file_uploader(f"Ficha Médica N° {i} (PDF/Imagen):", type=["pdf", "png", "jpg", "jpeg"], key=f"ficha_{i}")
                        file_aut = st.file_uploader(f"Autorización Firmada N° {i} (PDF/Imagen):", type=["pdf", "png", "jpg", "jpeg"], key=f"aut_{i}")

                    comentarios_participante = st.text_area(f"Comentarios / Observaciones sobre el integrante {i} (opcional):", key=f"comentarios_{i}")
                    st.markdown("---")
                    
                    estudiantes_datos.append({
                        "nombre": nombre,
                        "apellido": apellido,
                        "dni": dni,
                        "alergias_medicas": alergias,
                        "file_ficha": file_ficha,
                        "file_aut": file_aut,
                        "comentarios": comentarios_participante
                    })

                if st.form_submit_button("💾 Guardar Todos los Integrantes de esta Banca"):
                    hubo_error = False
                    
                    for idx, est in enumerate(estudiantes_datos, start=1):
                        if not est["nombre"] or not est["apellido"] or not est["dni"]:
                            st.error(f"Por favor complete Nombre, Apellido y DNI del Integrante N° {idx}.")
                            hubo_error = True
                            break

                    if not hubo_error:
                        with st.spinner("Subiendo documentación y guardando integrantes..."):
                            exito_total = True
                            
                            for est in estudiantes_datos:
                                dni_val = est["dni"]
                                ficha_url = ""
                                aut_url = ""

                                if est["file_ficha"]:
                                    ok_f, ficha_url = subir_archivo_a_drive_via_script(
                                        est["file_ficha"].read(), f"Ficha_{dni_val}_{est['file_ficha'].name}", est["file_ficha"].type, FOLDER_FICHAS
                                    )
                                    if not ok_f:
                                        st.error(f"Error subiendo ficha de {est['nombre']}: {ficha_url}")
                                        exito_total = False
                                        break

                                if est["file_aut"]:
                                    ok_a, aut_url = subir_archivo_a_drive_via_script(
                                        est["file_aut"].read(), f"Aut_{dni_val}_{est['file_aut'].name}", est["file_aut"].type, FOLDER_FICHAS
                                    )
                                    if not ok_a:
                                        st.error(f"Error subiendo autorización de {est['nombre']}: {aut_url}")
                                        exito_total = False
                                        break

                                if exito_total:
                                    datos_estudiante = {
                                        "nombre": est["nombre"],
                                        "apellido": est["apellido"],
                                        "dni": dni_val,
                                        "alergias_medicas": est["alergias_medicas"],
                                        "ficha_medica_id": ficha_url,
                                        "autorizacion_id": aut_url,
                                        "comentarios": est["comentarios"],
                                        "rol_mnu": "Delegado/a",
                                        "id_asignacion": banca_objeto.get("id_asignacion", organo_banca),
                                    }
                                    
                                    ok_g, msg_g = guardar_participante_nomina(id_del_activo, dni_val, datos_estudiante)
                                    if not ok_g:
                                        exito_total = False
                                        st.error(f"Error guardando en base de datos con {est['nombre']}: {msg_g}")

                            if exito_total:
                                st.success("✅ ¡Todos los integrantes de la banca fueron guardados con éxito!")
                                st.rerun()

            st.markdown("---")
            st.markdown("### 🚨 Cierre Oficial de Carga")
            if st.button("🔴 CONFIRMAR CARGA COMPLETA DE TODA LA DELEGACIÓN"):
                actualizar_estado_legajo(id_del_activo, "CARGA_COMPLETA")
                notificar_apps_script("CONFIRMAR_CARGA_DOCUMENTACION", {
                    "id_delegacion": id_del_activo,
                    "secret_hash": escuela_actual.get("secret_hash"),
                    "email_docente": escuela_actual.get("docente_email"),
                })
                st.balloons()
                st.success("🎉 ¡Carga de documentación confirmada con éxito!")
