import pandas as pd
import requests
import streamlit as st
from db_docentes import (
    eliminar_integrante,
    guardar_o_actualizar_integrante,
    obtener_bancas_asignadas,
    obtener_datos_delegacion,
    obtener_esquema_formulario,
    obtener_integrantes,
    obtener_modelos_activos,
    preinscribir_escuela,
    registrar_pago_comprobante,
    validar_acceso_docente,
)

st.set_page_config(
    page_title="Portal Docente - Preinscripción y Gestión",
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

API_URL = st.secrets["API_URL"]


def notificar_apps_script(action, data):
    try:
        requests.post(API_URL, json={"action": action, "data": data}, timeout=5)
    except Exception:
        pass


st.title("🏫 Portal de Gestión Escolar — Modelos ONU")

if "docente_autenticado" not in st.session_state:
    st.session_state["docente_autenticado"] = False
    st.session_state["id_delegacion"] = None

# ==========================================
# 1. PANTALLA PÚBLICA: REGISTRO Y LOGIN
# ==========================================
if not st.session_state["docente_autenticado"]:
    subtab_login, subtab_registro = st.tabs(
        ["🔑 Iniciar Sesión", "📝 Preinscripción de Nueva Escuela"]
    )

    # LOGIN CON EMAIL
    with subtab_login:
        st.markdown("### Ingrese con sus Credenciales Institucionales")
        with st.form("form_login_docente"):
            col_l1, col_l2 = st.columns(2)
            with col_l1:
                email_input = st.text_input(
                    "Correo Electrónico del Docente (Código de Delegación):"
                ).strip().lower()
            with col_l2:
                clave_input = st.text_input(
                    "Clave de Acceso (Secret Hash):", type="password"
                ).strip()

            btn_login = st.form_submit_button("Ingresar al Portal")

            if btn_login:
                if not email_input or not clave_input:
                    st.error("Complete ambos campos.")
                else:
                    es_valido, res = validar_acceso_docente(
                        email_input, clave_input
                    )
                    if es_valido:
                        st.session_state["docente_autenticado"] = True
                        st.session_state["id_delegacion"] = email_input
                        st.success("¡Acceso correcto!")
                        st.rerun()
                    else:
                        st.error(res)

    # REGISTRO
    with subtab_registro:
        st.markdown("### Formulario de Preinscripción Institucional")
        modelos_activos = obtener_modelos_activos()
        dict_mod = {m["nombre_visible"]: m["id_modelo"] for m in modelos_activos}

        with st.form("form_preinscripcion"):
            mod_sel = st.selectbox(
                "Seleccione el Modelo al que desea inscribirse:",
                list(dict_mod.keys()),
            )
            col_r1, col_r2 = st.columns(2)
            with col_r1:
                nombre_escuela = st.text_input("Nombre de la Institución *:")
                direccion_escuela = st.text_input("Dirección de la Escuela:")
                cupos_solicitados = st.number_input(
                    "Cupos / Delegaciones estimadas:",
                    min_value=1,
                    max_value=50,
                    value=10,
                )
            with col_r2:
                docente_nombre = st.text_input(
                    "Nombre y Apellido del Docente Responsable *:"
                )
                docente_email = st.text_input("Correo Electrónico del Docente (Será su ID) *:").strip().lower()
                docente_tel = st.text_input("Teléfono Celular de Contacto *:")

            btn_preinscribir = st.form_submit_button(
                "🚀 Confirmar Preinscripción"
            )

            if btn_preinscribir:
                if (
                    not nombre_escuela
                    or not docente_nombre
                    or not docente_email
                    or not docente_tel
                ):
                    st.error(
                        "Complete todos los campos obligatorios marcados con"
                        " *."
                    )
                else:
                    datos_nueva_escuela = {
                        "id_modelo": dict_mod[mod_sel],
                        "nombre_colegio": nombre_escuela,
                        "direccion_escuela": direccion_escuela,
                        "cupos_solicitados": cupos_solicitados,
                        "docente_apellido_nombre": docente_nombre,
                        "docente_email": docente_email,
                        "docente_telefono": docente_tel,
                    }
                    ok, res_reg = preinscribir_escuela(datos_nueva_escuela)
                    if ok:
                        st.success(
                            "🎉 ¡Preinscripción registrada exitosamente!"
                        )
                        st.balloons()
                        st.info(
                            f"**Guarde sus credenciales de acceso:**\n\n- **Código de Delegación (Email):**"
                            f" `{res_reg['id_delegacion']}`\n- **Clave de"
                            f" Acceso:** `{res_reg['secret_hash']}`"
                        )
                        notificar_apps_script(
                            "NUEVA_PREINSCRIPCION",
                            {
                                "id_delegacion": res_reg["id_delegacion"],
                                "docente_email": docente_email,
                            },
                        )
                    else:
                        st.error(res_reg)

    st.stop()

# ==========================================
# 2. PANEL PRIVADO DEL DOCENTE
# ==========================================
id_del = st.session_state["id_delegacion"]
escuela = obtener_datos_delegacion(id_del)
id_modelo = escuela.get("id_modelo", "MONUCBA_2026")

st.sidebar.markdown(
    f"### 🏛️ {escuela.get('nombre_colegio', 'Mi Institución')}"
)
st.sidebar.markdown(f"**Email / Código:** `{id_del}`")
st.sidebar.markdown(
    f"**Estado Legajo:** `{escuela.get('estado', 'PREINSCRIPTO')}`"
)

if st.sidebar.button("Cerrar Sesión"):
    st.session_state["docente_autenticado"] = False
    st.session_state["id_delegacion"] = None
    st.rerun()

tab_nomina, tab_bancas, tab_pagos_doc = st.tabs([
    "👥 Carga de Nómina y Participantes",
    "📌 Países y Bancas Asignadas",
    "💰 Informar Comprobante de Pago",
])

# ------------------------------------------
# CARGA DE NÓMINA
# ------------------------------------------
with tab_nomina:
    st.subheader("👥 Nómina de Estudiantes y Docentes Acompañantes")
    integrantes_actuales = obtener_integrantes(id_del)
    esquema_campos = obtener_esquema_formulario(id_modelo)

    with st.expander("➕ Cargar / Editar Participante"):
        with st.form("form_integrante"):
            col1, col2, col3 = st.columns(3)
            with col1:
                nombre = st.text_input("Nombre:")
                apellido = st.text_input("Apellido:")
            with col2:
                dni = st.text_input("DNI (Sin puntos):").strip()
                rol = st.selectbox(
                    "Rol en el Modelo:",
                    [
                        "Delegado",
                        "Embajador",
                        "Autoridad",
                        "Docente Acompañante",
                    ],
                )
            with col3:
                alergias = st.text_area("Observaciones Médicas / Alergias:")

            respuestas_dinamicas = {}
            if esquema_campos:
                st.markdown("---")
                st.markdown("### 📋 Información Adicional Requerida")
                for campo in esquema_campos:
                    lbl = campo.get("nombre_campo")
                    tipo = campo.get("tipo_dato")
                    req = " *" if campo.get("es_requerido") else ""

                    if tipo == "texto":
                        respuestas_dinamicas[lbl] = st.text_input(f"{lbl}{req}")
                    elif tipo == "numero":
                        respuestas_dinamicas[lbl] = st.number_input(
                            f"{lbl}{req}", min_value=0
                        )
                    elif tipo == "booleano":
                        respuestas_dinamicas[lbl] = st.checkbox(f"{lbl}{req}")
                    elif tipo == "seleccion":
                        opcs = [
                            o.strip()
                            for o in campo.get(
                                "opciones_separadas_por_coma", ""
                            ).split(",")
                            if o.strip()
                        ]
                        respuestas_dinamicas[lbl] = st.selectbox(
                            f"{lbl}{req}", opcs if opcs else ["-"]
                        )

            btn_guardar = st.form_submit_button("💾 Guardar Participante")

            if btn_guardar:
                if not dni or not nombre or not apellido:
                    st.error("DNI, Nombre y Apellido son obligatorios.")
                else:
                    datos_base = {
                        "nombre": nombre,
                        "apellido": apellido,
                        "dni": dni,
                        "rol_mnu": rol,
                        "alergias_medicas": alergias,
                    }
                    ok, msg = guardar_o_actualizar_integrante(
                        id_del, dni, datos_base, respuestas_dinamicas
                    )
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

    st.markdown("---")
    st.markdown("### 📋 Participantes Registrados")
    if integrantes_actuales:
        df_int = pd.DataFrame(integrantes_actuales).astype(str)
        cols_vis = [
            c
            for c in [
                "dni",
                "nombre",
                "apellido",
                "rol_mnu",
                "alergias_medicas",
            ]
            if c in df_int.columns
        ]
        st.dataframe(df_int[cols_vis], use_container_width=True)

        dni_eliminar = st.selectbox(
            "Seleccionar DNI para eliminar:",
            [i.get("dni", i.get("id")) for i in integrantes_actuales],
        )
        if st.button("🗑️ Eliminar Participante"):
            if eliminar_integrante(id_del, dni_eliminar):
                st.success("Participante eliminado.")
                st.rerun()
    else:
        st.info("Aún no ha registrado participantes en la nómina.")

# ------------------------------------------
# BANCAS Y PAGOS
# ------------------------------------------
with tab_bancas:
    st.subheader("📌 Bancas y Países Asignados")
    bancas = obtener_bancas_asignadas(id_del)
    if bancas:
        for b in bancas:
            st.write(
                f"- **{b.get('organo_comite', '-')}** — País:"
                f" **{b.get('pais', '-')}**"
            )
    else:
        st.info("Su institución aún no tiene bancas asignadas.")

with tab_pagos_doc:
    st.subheader("💰 Informar Comprobante de Transferencia / Pago")
    with st.form("form_pago"):
        monto = st.number_input("Monto Transferido ($):", min_value=100)
        url_drive = st.text_input(
            "Enlace al Comprobante en Google Drive / Dropbox:"
        ).strip()
        btn_enviar_pago = st.form_submit_button("🚀 Enviar Comprobante")

        if btn_enviar_pago:
            if not url_drive:
                st.error("Debe ingresar el enlace al comprobante.")
            else:
                ok, idPago = registrar_pago_comprobante(
                    id_del, id_modelo, monto, url_drive
                )
                if ok:
                    notificar_apps_script(
                        "NUEVO_PAGO_REGISTRADO",
                        {"id_delegacion": id_del, "monto": monto},
                    )
                    st.success(
                        f"¡Pago registrado exitosamente! ID de Seguimiento:"
                        f" `{idPago}`"
                    )
                else:
                    st.error("Error al registrar el pago.")
