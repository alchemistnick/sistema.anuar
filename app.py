# MÓDULO DE PREINSCRIPCIÓN ADAPTADO A MONUCBA 2026
if menu == "Preinscripción Escuela":
    st.subheader("Ficha de Inscripción por Escuela - MONUCBA 2026")
    
    with st.form("form_registro_monucba"):
        colegio = st.text_input("Nombre de la Institución / Colegio")
        docente = st.text_input("Docente / Tutor Acompañante")
        email = st.text_input("Correo Electrónico de Contacto")
        clave = st.text_input("Creá una Clave Secreta para el Portal", type="password")
        
        st.markdown("---")
        st.markdown("#### Seleccioná la cantidad de Delegaciones por Modalidad")
        
        col1, col2 = st.columns(2)
        with col1:
            del_5 = st.number_input("Sin CS ni ECOSOC (5 delegados: AG1, AG3, AG6)", min_value=0, max_value=5, value=0)
            del_7_ecosoc = st.number_input("Sin CS con ECOSOC (7 delegados: AG1, AG3, AG6, ECOSOC)", min_value=0, max_value=5, value=0)
            del_9_completa = st.number_input("Con CS y ECOSOC (9 delegados: AG1, AG3, AG6, ECOSOC, CS)", min_value=0, max_value=2, value=0)
        
        with col2:
            del_7_cs = st.number_input("Con CS sin ECOSOC (7 delegados: AG1, AG3, AG6, CS)", min_value=0, max_value=2, value=0)
            del_davos = st.number_input("Foro de Davos (Unipersonales)", min_value=0, max_value=5, value=0)
            del_prensa = st.number_input("Comité de Prensa Internacional (3 delegados)", min_value=0, max_value=2, value=0)
            
        # Cálculo automático de alumnos a cargar
        tot_alumnos = (del_5 * 5) + (del_7_ecosoc * 7) + (del_9_completa * 9) + (del_7_cs * 7) + (del_davos * 1) + (del_prensa * 3)
        st.info(f"📊 **Total de participantes a inscribir en la nómina:** {tot_alumnos} alumnos/delegados.")
        
        submitted = st.form_submit_button("Enviar Preinscripción")
        
        if submitted:
            if not colegio or not docente or not email or not clave:
                st.error("Por favor completá los datos institucionales obligatorios.")
            elif tot_alumnos == 0:
                st.warning("Debes seleccionar al menos 1 delegación en alguna modalidad.")
            else:
                payload = {
                    "action": "REGISTRAR_DELEGACION",
                    "data": {
                        "nombre_colegio": colegio,
                        "docente_cargo": docente,
                        "email_contacto": email,
                        "secret_hash": clave,
                        "cupos_solicitados": tot_alumnos,
                        "desglose_modalidades": f"5d:{del_5} | 7d_eco:{del_7_ecosoc} | 9d:{del_9_completa} | 7d_cs:{del_7_cs} | davos:{del_davos} | prensa:{del_prensa}"
                    }
                }
                
                with st.spinner("Registrando preinscripción en el sistema..."):
                    try:
                        res = requests.post(API_URL, json=payload).json()
                        if res.get("status") == "SUCCESS":
                            st.success(f"¡Preinscripción enviada! ID asignado: **{res['data']['id_delegacion']}**")
                        else:
                            st.error(f"Error: {res.get('message')}")
                    except Exception as e:
                        st.error(f"Error de conexión: {e}")
