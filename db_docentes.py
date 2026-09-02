import firebase_admin
from firebase_admin import credentials, firestore
import streamlit as st

# Inicialización Singleton de Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate(dict(st.secrets["firebase"]))
    firebase_admin.initialize_app(cred)

db = firestore.client()

# ==========================================
# 1. PARÁMETROS Y MODELOS (SOLO DESDE SECRETARÍA)
# ==========================================


def obtener_modelos_activos():
    """Recupera la lista de modelos reales registrados desde Secretaría."""
    try:
        docs = db.collection("modelos").stream()
        modelos = []
        for doc in docs:
            m = doc.to_dict()
            m["id_modelo"] = doc.id
            modelos.append(m)
        return modelos
    except Exception as e:
        st.error(f"Error al conectar con Firestore para obtener modelos: {e}")
        return []


def obtener_parametros_comites(id_modelo):
    """Obtiene la lista exacta de comités/secciones configurada para este modelo."""
    try:
        doc = db.collection("configuracion").document(str(id_modelo)).get()
        if doc.exists:
            return doc.to_dict().get("parametros_comites", [])
        return []
    except Exception as e:
        st.error(f"Error al consultar parámetros de comités: {e}")
        return []


# ==========================================
# 2. PREINSCRIPCIÓN DE ESCUELAS
# ==========================================


def preinscribir_escuela(datos_escuela):
    """Registra la delegación usando el email del docente como ID primario."""
    try:
        docente_email = str(datos_escuela.get("docente_email", "")).strip().lower()

        if not docente_email or "@" not in docente_email:
            return False, "Debe ingresar un correo electrónico válido."

        doc_ref = db.collection("delegaciones").document(docente_email)
        if doc_ref.get().exists:
            return (
                False,
                f"El correo '{docente_email}' ya se encuentra preinscripto.",
            )

        payload = {
            "id_delegacion": docente_email,
            "estado": "PREINSCRIPTO",
            "fecha_registro": firestore.SERVER_TIMESTAMP,
            **datos_escuela,
        }

        doc_ref.set(payload)
        return True, docente_email
    except Exception as e:
        return False, f"Error al registrar la institución: {e}"


def validar_acceso_docente(email_doc, hash_ingresado):
    """Valida las credenciales con el email docente y contraseña elegida."""
    try:
        email_clean = str(email_doc).strip().lower()
        doc = db.collection("delegaciones").document(email_clean).get()
        if doc.exists:
            datos = doc.to_dict()
            if str(datos.get("secret_hash")).strip() == str(hash_ingresado).strip():
                datos["id"] = doc.id
                return True, datos
            return False, "Clave de acceso incorrecta."
        return False, "El correo electrónico no se encuentra registrado."
    except Exception as e:
        return False, f"Error al validar acceso: {e}"


# ==========================================
# 3. ASIGNACIONES Y NÓMINA DE PARTICIPANTES
# ==========================================


def obtener_bancas_asignadas(email_doc):
    """Carga las bancas/países asignados a esta delegación."""
    try:
        email_clean = str(email_doc).strip().lower()
        docs = (
            db.collection("delegaciones")
            .document(email_clean)
            .collection("asignaciones")
            .stream()
        )
        return [doc.to_dict() for doc in docs]
    except Exception:
        return []


def guardar_participante_nomina(email_doc, dni, datos_participante):
    """Guarda o actualiza un estudiante en la nómina en Firestore."""
    try:
        email_clean = str(email_doc).strip().lower()
        db.collection("delegaciones").document(email_clean).collection(
            "integrantes"
        ).document(str(dni)).set(datos_participante, merge=True)
        return True, "Participante guardado correctamente."
    except Exception as e:
        return False, f"Error al guardar participante: {e}"


def registrar_pago_comprobante(email_doc, id_modelo, monto, drive_url):
    """Registra una transferencia en la colección de pagos."""
    try:
        pago_ref = db.collection("pagos").document()
        payload = {
            "id_delegacion": str(email_doc).strip().lower(),
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


def actualizar_estado_legajo(email_doc, estado):
    """Actualiza el estado de la delegación."""
    try:
        email_clean = str(email_doc).strip().lower()
        db.collection("delegaciones").document(email_clean).set(
            {"estado": estado}, merge=True
        )
        return True
    except Exception:
        return False
