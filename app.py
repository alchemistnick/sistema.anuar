import base64
import pandas as pd
import requests
import streamlit as st

st.set_page_config(
    page_title="Inscripción y Gestión Escolar - Modelos ONU",
    page_icon="🏫",
    layout="wide",
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

MODO_SOLO_ACREDITACION = False

if MODO_SOLO_ACREDITACION:
    menu = st.sidebar.selectbox(
        "Seleccionar Opción:", ["🎫 Acreditación Presencial"]
    )
else:
    menu = st.sidebar.selectbox(
        "Seleccionar Opción:",
        [
            "📝 Preinscripción Institucional",
            "🔑 Ingreso a Mi Delegación",
            "💳 Subir Comprobante de Pago",
            "📋 Carga de Nómina y Documentación",
        ],
    )

# ---------------------------------------------------------
# 1. PREINSCRIPCIÓN INSTITUCIONAL (Desde PARAMETROS_MODELOS)
# ---------------------------------------------------------
if menu == "📝 Preinscripción Institucional":
    st.subheader("📝 Formulario de Preinscripción Escolar")

    modelos = api_get("GET_MODELOS_ACTIVOS")
    if not modelos:
        st.warning(
            "⚠️ No hay modelos activos configurados en PARAMETROS_MODELOS."
        )
        st.stop()

    dict_mods_full = {
        m.get("nombre_visible", m.get("id_modelo")): m for m in modelos
    }
    mod_sel = st.selectbox(
        "Seleccionar Modelo ONU:", list(dict_mods_full.keys())
    )

    modelo_objeto = dict_mods_full[mod_sel]
    id_modelo_elegido = modelo_objeto.get("id_modelo")

    min_delegaciones = int(modelo_objeto.get("min_delegaciones", 1))
    max_delegaciones = int(modelo_objeto.get("max_delegaciones", 5))

    st.info(
        f"ℹ️ **Modelo:** `{id_modelo_elegido}` — Permite de **{min_delegaciones}** a **{max_delegaciones}** delegaciones."
    )

    with st.form("form_preinscripcion"):
        col1, col2 = st.columns(2)
        with col1:
            nombre_colegio = st.text_input(
                "Nombre de la Institución Educativa:"
            )
            direccion_escuela = st.text_input("Dirección de la Escuela:")
            email_institucional = st.text_input("Email Institucional:")
            telefono_institucional = st.text_input("Teléfono Institucional:")

        with col2:
            docente_apellido_nombre = st.text_input(
                "Apellido y Nombre del Docente Responsable:"
            )
            docente_email = st.text_input("Email del Docente:")
            docente_telefono = st.text_input("Celular del Docente:")

            cantidad_delegaciones = st.number_input(
                "Cantidad de Delegaciones Solicitadas:",
                min_value=min_delegaciones,
                max_value=max_delegaciones,
                value=min_delegaciones,
                step=1,
            )

            docentes_acompanantes = st.number_input(
                "Docentes Acompañantes:", min_value=1, value=1, step=1
            )
            secret_hash = st.text_input(
                "Crear Clave de Acceso:", type="password"
            )

        if st.form_submit_button("Enviar Preinscripción"):
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
                        "cupos_solicitados": cantidad_delegaciones,
                        "docentes_acompanantes": docentes_acompanantes,
                        "secret_hash": secret_hash,
                        "id_modelo": id_modelo_elegido,
                    },
                }
                res = requests.post(API_URL, json=payload).json()
                if res.get("status") == "SUCCESS":
                    st.success(
                        f"¡Preinscripción exitosa! Código de Delegación: **{res.get('data', {}).get('id_delegacion')}**."
                    )
                else:
                    st.error(res.get("message"))

# ---------------------------------------------------------
# 2. CARGA DE NÓMINA (Desde PARAMETROS_COMITES)
# ---------------------------------------------------------
elif menu == "📋 Carga de Nómina y Documentación":
    st.subheader("📋 Registro de Participantes y Documentación")

    with st.form("form_verif_nomina"):
        id_del_nom = st.text_input("Código de Delegación:").strip().upper()
        hash_nom = st.text_input("Clave de Acceso:", type="password").strip()
        if st.form_submit_button("Verificar"):
            st.session_state["id_del_nom"] = id_del_nom
            st.session_state["hash_nom"] = hash_nom

    if "id_del_nom" in st.session_state and st.session_state["id_del_nom"]:
        id_del_nom = st.session_state["id_del_nom"]
        hash_nom = st.session_state.get("hash_nom", "")

        delegaciones = api_get("GET_TODAS_DELEGACIONES")
        escuela = next(
            (
                d
                for d in delegaciones
                if str(d.get("id_delegacion")).strip().upper() == id_del_nom
                and str(d.get("secret_hash")).strip() == hash_nom
            ),
            None,
        )

        if escuela:
            id_modelo = escuela.get("id_modelo", "MUNEJEMPLO_1")

            # 1. Obtener las asignaciones
            res_asig = requests.get(
                f"{API_URL}?action=GET_ASIGNACIONES_DELEGACION&id_delegacion={id_del_nom}"
            ).json()
            bancas_asignadas = res_asig.get("data", [])

            # 2. Consultar PARAMETROS_COMITES
            comites_reglas = api_get(
                "GET_PARAMETROS_COMITES", f"&id_modelo={id_modelo}"
            )
            mapa_reglas = {
                str(c.get("organo_comite")).strip().upper(): c
                for c in comites_reglas
            }

            if not bancas_asignadas:
                st.warning(
                    "⚠️ Tu institución aún no tiene bancas/países asignados."
                )
            else:
                dict_bancas = {
                    f"{b.get('organo')} — {b.get('pais')}": b
                    for b in bancas_asignadas
                }
                banca_sel_nombre = st.selectbox(
                    "Seleccionar Banca / Asignación:", list(dict_bancas.keys())
                )
                banca_objeto = dict_bancas[banca_sel_nombre]

                organo_banca = str(banca_objeto.get("organo")).strip().upper()
                regla_comite = mapa_reglas.get(organo_banca, {})

                integrantes_permitidos = int(
                    regla_comite.get("integrantes_por_banca", 2)
                )

                st.info(
                    f"📌 El órgano **{banca_objeto.get('organo')}** permite hasta **{integrantes_permitidos} estudiante(s)** por país."
                )

                with st.form("form_estudiante"):
                    col_a, col_b = st.columns(2)
                    with col_a:
                        nombre = st.text_input("Nombre del Estudiante:")
                        apellido = st.text_input("Apellido:")
                        dni = st.text_input("DNI:")
                    with col_b:
                        alergias = st.text_input(
                            "Alergias / Condición Médica:", value="Ninguna"
                        )
                        ficha_med = st.file_uploader(
                            "Ficha Médica (PDF/JPG):", type=["pdf", "png", "jpg"]
                        )
                        aut_firmada = st.file_uploader(
                            "Autorización Firmada (PDF/JPG):",
                            type=["pdf", "png", "jpg"],
                        )

                    if st.form_submit_button("Guardar Alumno en Nómina"):
                        if not nombre or not apellido or not dni:
                            st.error("Completa los datos obligatorios.")
                        else:
                            f_b64, f_name, f_mime = "", "", ""
                            a_b64, a_name, a_mime = "", "", ""

                            if ficha_med:
                                f_b64 = base64.b64encode(
                                    ficha_med.read()
                                ).decode("utf-8")
                                f_name, f_mime = ficha_med.name, ficha_med.type

                            if aut_firmada:
                                a_b64 = base64.b64encode(
                                    aut_firmada.read()
                                ).decode("utf-8")
                                a_name, a_mime = (
                                    aut_firmada.name,
                                    aut_firmada.type,
                                )

                            payload = {
                                "action": "GUARDAR_PARTICIPANTE_NOMINA",
                                "data": {
                                    "id_delegacion": id_del_nom,
                                    "secret_hash": hash_nom,
                                    "id_asignacion": banca_objeto.get(
                                        "id_asignacion"
                                    ),
                                    "rol_mnu": "Delegado/a",
                                    "nombre": nombre,
                                    "apellido": apellido,
                                    "dni": dni,
                                    "alergias_medicas": alergias,
                                    "ficha_b64": f_b64,
                                    "ficha_name": f_name,
                                    "ficha_mime": f_mime,
                                    "aut_b64": a_b64,
                                    "aut_name": a_name,
                                    "aut_mime": a_mime,
                                },
                            }
                            res = requests.post(API_URL, json=payload).json()
                            if res.get("status") == "SUCCESS":
                                st.success(
                                    "✅ Estudiante registrado con éxito."
                                )
                                st.rerun()
                            else:
                                st.error(res.get("message"))
