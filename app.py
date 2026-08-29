import base64
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
# PREINSCRIPCIÓN INSTITUCIONAL SEGÚN MODALIDADES Y COMISIONES
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

    # Obtener la lista de comisiones y secciones parametrizadas
    comites = api_get("GET_PARAMETROS_COMITES", f"&id_modelo={id_modelo_elegido}")

    with st.form("form_preinscripcion"):
        st.markdown("### 🏛️ Datos de la Institución")
        col1, col2 = st.columns(2)
        with col1:
            nombre_colegio = st.text_input(
                "Nombre de la Institución Educativa (con N° de DIPE/CUE):"
            )
            direccion_escuela = st.text_input(
                "Dirección (Localidad, Provincia, País):"
            )
            email_institucional = st.text_input("Correo Electrónico:")
            telefono_institucional = st.text_input("Número de Teléfono:")

        with col2:
            st.markdown("### 👨‍🏫 Datos del Responsable / Docente")
            docente_apellido_nombre = st.text_input("Apellido y Nombre:")
            docente_email = st.text_input("Correo Electrónico Docente:")
            docente_telefono = st.text_input("Teléfono Móvil:")
            secret_hash = st.text_input(
                "Crear Clave de Acceso para la Escuela:", type="password"
            )

        st.markdown("---")
        st.markdown("### 🇺🇳 Datos de las Delegaciones y Comisiones")
        st.caption(
            "Seleccione la cantidad de delegaciones según el tipo de representación deseada:"
        )

        # Mapeo dinámico de secciones según PARAMETROS_COMITES
        desglose_seleccionado = {}
        total_cupos_calculados = 0

        # Si tenemos los comités desde el Sheets, armamos las opciones reales
        if comites:
            # Agrupar por clave_seccion
            secciones = {}
            for c in comites:
                sec = c.get("clave_seccion", "GENERAL")
                if sec not in secciones:
                    secciones[sec] = []
                secciones[sec].append(c)

            for sec_nombre, lista_comites in secciones.items():
                col_sec, col_cant = st.columns([3, 1])
                nombres_comite = ", ".join(
                    [x.get("organo_comite", "") for x in lista_comites]
                )
                integrantes_totales = sum(
                    [int(x.get("integrantes_por_banca", 1)) for x in lista_comites]
                )

                with col_sec:
                    st.write(
                        f"**Sección {sec_nombre}:** {nombres_comite} ({integrantes_totales} participantes por delegación)"
                    )
                with col_cant:
                    cant = st.selectbox(
                        f"Cantidad ({sec_nombre}):",
                        options=[0, 1, 2, 3, 4],
                        key=f"sec_{sec_nombre}",
                    )
                    if cant > 0:
                        desglose_seleccionado[sec_nombre] = cant
                        total_cupos_calculados += cant * integrantes_totales
        else:
            # Caída alternativa con los selectores del PDF si aún no cargó la API
            op_5 = st.selectbox(
                "Sin CS ni ECOSOC - 5 delegados (AG1, AG3, AG6):",
                [0, 1, 2, 3, 4],
            )
            op_7_eco = st.selectbox(
                "Sin CS con ECOSOC - 7 participantes (AG1, AG3, AG6, ECOSOC):",
                [0, 1, 2, 3, 4],
            )
            op_9 = st.selectbox(
                "Con CS y ECOSOC - 9 delegados (AG1, AG3, AG6, ECOSOC, CS):",
                [0, 1, 2, 3, 4],
            )
            op_7_cs = st.selectbox(
                "Con CS sin ECOSOC - 7 delegados (AG1, AG3, AG6, CS):",
                [0, 1, 2, 3, 4],
            )
            op_davos = st.selectbox(
                "Comisión Independiente - Foro de Davos (Unipersonales):",
                [0, 1, 2],
            )
            op_prensa = st.selectbox(
                "Comité de Prensa Internacional (3 delegados):", [0, 1, 2]
            )

            total_cupos_calculados = (
                (op_5 * 5)
                + (op_7_eco * 7)
                + (op_9 * 9)
                + (op_7_cs * 7)
                + (op_davos * 1)
                + (op_prensa * 3)
            )
            desglose_seleccionado = {
                "5_DEL": op_5,
                "7_ECO": op_7_eco,
                "9_CS_ECO": op_9,
                "7_CS": op_7_cs,
                "DAVOS": op_davos,
                "PRENSA": op_prensa,
            }

        st.info(
            f"📊 **Total de participantes a inscribir:** {total_cupos_calculados} estudiantes."
        )

        btn_enviar = st.form_submit_button("Enviar Preinscripción Institucional")

        if btn_enviar:
            if not nombre_colegio or not docente_email or not secret_hash:
                st.error("Por favor completa los campos obligatorios.")
            elif total_cupos_calculados == 0:
                st.error(
                    "Debe seleccionar al menos 1 delegación o comisión para inscribir."
                )
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
                        "cupos_solicitados": total_cupos_calculados,
                        "desglose_modalidades": str(desglose_seleccionado),
                        "secret_hash": secret_hash,
                        "id_modelo": id_modelo_elegido,
                    },
                }
                res = requests.post(API_URL, json=payload).json()
                if res.get("status") == "SUCCESS":
                    st.success(
                        f"¡Preinscripción exitosa! Código de Delegación asignado: **{res.get('data', {}).get('id_delegacion')}**."
                    )
                else:
                    st.error(res.get("message"))
