import firebase_admin
from firebase_admin import credentials, firestore
import secrets
import streamlit as st

if not firebase_admin._apps:
    cred = credentials.Certificate(dict(st.secrets["firebase"]))
    firebase_admin.initialize_app(cred)

db = firestore.client()

# ==========================================
# 1. AUTENTICACIÓN Y REGISTRO
# ==========================================


def obtener_modelos_activos():
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


def preinscribir_escuela(datos_escuela):
    """Crea una delegación usando el email del docente como ID único."""
    try:
        # Normalizar email como ID primario de la delegación
        docente_email = str(datos_escuela.get("docente_email", "")).strip().lower()

        if not docente_email or "@" not in docente_email:
            return False, "Debe ingresar un correo electrónico válido."

        # Verificar si la escuela/docente ya está preinscripta
        doc_ref = db.collection("delegaciones").document(docente_email)
        if doc_ref.get().exists:
            return False, f"Ya existe una delegación registrada con el correo '{docente_email}'."

        # Generar clave de acceso de 6 caracteres
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
    """Recupera la información completa de la delegación por correo."""
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
    try:
        doc = db.collection("configuracion").document(str(id_modelo)).get()
        if doc.exists:
            return doc.to_dict().get("campos_personalizados", [])
        return []
    except Exception:
        return []


def obtener_bancas_asignadas(docente_email):
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
# 3. GESTIÓN DE NÓMINA
# ==========================================


def obtener_integrantes(docente_email):
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
