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
    registrar_pago_comprobante,
    validar_acceso_docente,
)

st.set_page_config(
    page_title="Portal Docente - Inscription & Gestión",
    page_icon="🏫",
    layout="wide",
)

API_URL = st.secrets["API_URL"]


def notificar_apps_script(action, data):
    """Dispara correos de notificación vía Apps Script."""
    try:
        requests.post(API_URL, json={"action": action, "data": data}, timeout=5)
    except Exception:
        pass


st.title("🏫 Portal de Gestión Escolar — Modelos ONU")

# ==========================================
# LOGIN DE LA INSTITUCIÓN
# ==========================================
if "docente_autenticado" not in st.session_state:
    st.session_state["docente_autenticado"] = False
    st.session_state["id_delegacion"] = None

if not st.session_state["docente_autenticado"]:
    st.markdown("### 🔑 Iniciar Sesión con Clave Institucional")
    with st.form("form_login_docente"):
        col_l1, col_l2 = st.columns(2)
        with col_l1:
            id_del_input = st.text_input(
                "Código de Delegación / Escuela (ej: DEL-001):"
            ).strip()
        with col_l2:
            clave_input = st.text_input(
                "Clave de Acceso (Secret Hash):", type="password"
            ).strip()

        btn_login = st.form_submit_button("Ingresar al Portal")

        if btn_login:
            if not id_del_input or not clave_input:
                st.error("Por favor complete ambos campos.")
            else:
                es_valido, res = validar_acceso_docente(
                    id_del_input, clave_input
                )
                if es_valido:
                    st.session_state["docente_autenticado"] = True
                    st.session_state["id_delegacion"] = id_del_input
                    st.session_state["datos_escuela"] = res
                    st.success("¡Acceso correcto!")
                    st.rerun()
                else:
                    st.error(res)
    st.stop()

# ==========================================
# PANEL PRINCIPAL DOCENTE
# ==========================================
id_del = st.session_state["id_delegacion"]
escuela = obtener_datos_delegacion(id_del)
id_modelo = escuela.get("id_modelo", "MONUCBA_2026")

st.sidebar.markdown(
    f"### 🏛️ {escuela.get('nombre_colegio', 'Mi Institución')}"
)
st.sidebar.markdown(f"**Código:** `{id_del}`")
st.sidebar.markdown(
    f"**Estado del Legajo:** `{escuela.get('estado', 'REGISTRADO')}`"
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
# 1. CARGA DE NÓMINA CON CAMPOS DINÁMICOS
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

            # RENDERIZADO DINÁMICO DE CAMPOS ADICIONALES (CONFIGURADOS EN SECRETARÍA)
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
# 2. BANCAS ASIGNADAS
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
        st.info(
            "Su institución aún no tiene bancas o países asignados post-sorteo."
        )

# ------------------------------------------
# 3. INFORMACIÓN DE PAGOS
# ------------------------------------------
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
