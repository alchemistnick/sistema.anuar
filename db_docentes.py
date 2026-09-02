import secrets
import firebase_admin
from firebase_admin import credentials, firestore
import streamlit as st

# Inicialización Singleton de Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate(dict(st.secrets["firebase"]))
    firebase_admin.initialize_app(cred)

db = firestore.client()

# ==========================================
# 1. AUTENTICACIÓN Y REGISTRO DE ESCUELAS
# ==========================================


def obtener_modelos_activos():
    """Obtiene la lista de modelos desde Firestore."""
    try:
        docs = db.collection("modelos").stream()
        modelos = []
        for doc in docs:
            m = doc.to_dict()
            m["id_modelo"] = doc.id
            modelos.append(m)

        if not modelos:
            return [
                {
                    "id_modelo": "MONUCBA_2026",
                    "nombre_visible": "MONUCBA 2026",
                },
                {"id_modelo": "CATE_2026", "nombre_visible": "Modelo CATE 2026"},
            ]
        return modelos
    except Exception as e:
        st.error(f"Error al cargar modelos desde Firestore: {e}")
        return [
            {"id_modelo": "MONUCBA_2026", "nombre_visible": "MONUCBA 2026"}
        ]


def obtener_configuracion_preinscripcion(id_modelo):
    """Obtiene la configuración y campos personalizados creados desde Secretaría."""
    try:
        doc = db.collection("configuracion").document(str(id_modelo)).get()
        if doc.exists:
            return doc.to_dict()
        return {}
    except Exception as e:
        st.error(f"Error al cargar configuración de preinscripción: {e}")
        return {}


def preinscribir_escuela(datos_escuela):
    """Crea una delegación en Firestore utilizando el email del docente como ID primario."""
    try:
        docente_email = str(datos_escuela.get("docente_email", "")).strip().lower()

        if not docente_email or "@" not in docente_email:
            return False, "Debe ingresar un correo electrónico válido."

        doc_ref = db.collection("delegaciones").document(docente_email)
        if doc_ref.get().exists:
            return False, f"El correo '{docente_email}' ya se encuentra registrado."

        secret_hash = secrets.token_hex(3).upper()

        payload = {
            "id_delegacion": docente_email,
            "secret_hash": secret_hash,
            "estado": "PREINSCRIPTO",
            "fecha_registro": firestore.SERVER_TIMESTAMP,
            **datos_escuela,
        }

        doc_ref.set(payload)

        return True, {
            "id_delegacion": docente_email,
            "secret_hash": secret_hash,
        }
    except Exception as e:
        return False, f"Error al registrar la institución: {e}"


def validar_acceso_docente(docente_email, clave_hash):
    """Verifica el acceso con Email del Docente y Clave Hash."""
    try:
        email_clean = str(docente_email).strip().lower()
        doc = db.collection("delegaciones").document(email_clean).get()
        if doc.exists:
            datos = doc.to_dict()
            if str(datos.get("secret_hash")).strip() == str(clave_hash).strip():
                datos["id"] = doc.id
                return True, datos
            return False, "La clave ingresada es incorrecta."
        return False, "El correo electrónico no se encuentra registrado."
    except Exception as e:
        return False, f"Error al verificar credenciales: {e}"


def obtener_datos_delegacion(docente_email):
    """Obtiene la información completa de la delegación por correo."""
    email_clean = str(docente_email).strip().lower()
    doc = db.collection("delegaciones").document(email_clean).get()
    if doc.exists:
        d = doc.to_dict()
        d["id"] = doc.id
        return d
    return None


# ==========================================
# 2. ESQUEMAS Y BANCAS
# ==========================================


def obtener_esquema_formulario(id_modelo):
    """Recupera la lista de campos personalizados."""
    try:
        doc = db.collection("configuracion").document(str(id_modelo)).get()
        if doc.exists:
            return doc.to_dict().get("campos_personalizados", [])
        return []
    except Exception:
        return []


def obtener_bancas_asignadas(docente_email):
    """Carga las bancas/países asignados a la delegación."""
    try:
        email_clean = str(docente_email).strip().lower()
        docs = (
            db.collection("delegaciones")
            .document(email_clean)
            .collection("asignaciones")
            .stream()
        )
        return [doc.to_dict() for doc in docs]
    except Exception:
        return []


# ==========================================
# 3. GESTIÓN DE NÓMINA (INTEGRANTES)
# ==========================================


def obtener_integrantes(docente_email):
    """Obtiene la lista de integrantes de la delegación."""
    email_clean = str(docente_email).strip().lower()
    docs = (
        db.collection("delegaciones")
        .document(email_clean)
        .collection("integrantes")
        .stream()
    )
    integrantes = []
    for doc in docs:
        d = doc.to_dict()
        d["id"] = doc.id
        integrantes.append(d)
    return integrantes


def guardar_o_actualizar_integrante(
    docente_email, dni, datos_integrante, campos_dinamicos_respuestas
):
    """Guarda un participante en la subcolección integrantes."""
    try:
        email_clean = str(docente_email).strip().lower()
        payload = {**datos_integrante, **campos_dinamicos_respuestas}
        db.collection("delegaciones").document(email_clean).collection(
            "integrantes"
        ).document(str(dni)).set(payload, merge=True)
        return True, "Participante guardado correctamente."
    except Exception as e:
        return False, f"Error al guardar integrante: {e}"


def eliminar_integrante(docente_email, dni):
    """Elimina un participante de la nómina."""
    try:
        email_clean = str(docente_email).strip().lower()
        db.collection("delegaciones").document(email_clean).collection(
            "integrantes"
        ).document(str(dni)).delete()
        return True
    except Exception:
        return False


# ==========================================
# 4. COMPROBANTES DE PAGO
# ==========================================


def registrar_pago_comprobante(docente_email, id_modelo, monto, drive_url):
    """Guarda un comprobante de pago en Firestore."""
    try:
        pago_ref = db.collection("pagos").document()
        payload = {
            "id_delegacion": str(docente_email).strip().lower(),
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
