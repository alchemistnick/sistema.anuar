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
    """Recupera la lista de modelos activos desde Firestore."""
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
    """Crea un documento de delegación con ID automático y genera un secret_hash de acceso."""
    try:
        secret_hash = secrets.token_hex(3).upper()

        ref_del = db.collection("delegaciones").document()
        id_delegacion = f"DEL-{ref_del.id[:5].upper()}"

        payload = {
            "id_delegacion": id_delegacion,
            "secret_hash": secret_hash,
            "estado": "PREINSCRIPTO",
            "fecha_registro": firestore.SERVER_TIMESTAMP,
            **datos_escuela,
        }

        db.collection("delegaciones").document(id_delegacion).set(payload)

        return True, {
            "id_delegacion": id_delegacion,
            "secret_hash": secret_hash,
        }
    except Exception as e:
        return False, f"Error al registrar la institución: {e}"


def validar_acceso_docente(id_delegacion, clave_hash):
    """Verifica si el código de delegación y clave coinciden en Firestore."""
    try:
        doc = db.collection("delegaciones").document(str(id_delegacion)).get()
        if doc.exists:
            datos = doc.to_dict()
            if str(datos.get("secret_hash")).strip() == str(clave_hash).strip():
                datos["id"] = doc.id
                return True, datos
            return False, "La clave ingresada es incorrecta."
        return False, "El código de delegación no existe."
    except Exception as e:
        return False, f"Error al verificar credenciales: {e}"


def obtener_datos_delegacion(id_delegacion):
    """Recupera la información completa de la escuela."""
    doc = db.collection("delegaciones").document(str(id_delegacion)).get()
    if doc.exists:
        d = doc.to_dict()
        d["id"] = doc.id
        return d
    return None


# ==========================================
# 2. ESQUEMA DINÁMICO Y BANCAS
# ==========================================


def obtener_esquema_formulario(id_modelo):
    """Carga los campos personalizados creados desde la app de Secretaría."""
    try:
        doc = db.collection("configuracion").document(str(id_modelo)).get()
        if doc.exists:
            return doc.to_dict().get("campos_personalizados", [])
        return []
    except Exception:
        return []


def obtener_bancas_asignadas(id_delegacion):
    """Carga las bancas/países asignados a la delegación."""
    try:
        docs = (
            db.collection("delegaciones")
            .document(str(id_delegacion))
            .collection("asignaciones")
            .stream()
        )
        return [doc.to_dict() for doc in docs]
    except Exception:
        return []


# ==========================================
# 3. GESTIÓN DE NÓMINA (INTEGRANTES)
# ==========================================


def obtener_integrantes(id_delegacion):
    """Obtiene la lista de estudiantes y docentes cargados."""
    docs = (
        db.collection("delegaciones")
        .document(str(id_delegacion))
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
    id_delegacion, dni, datos_integrante, campos_dinamicos_respuestas
):
    """Guarda o actualiza un participante en la subcolección de la delegación."""
    try:
        payload = {**datos_integrante, **campos_dinamicos_respuestas}
        db.collection("delegaciones").document(str(id_delegacion)).collection(
            "integrantes"
        ).document(str(dni)).set(payload, merge=True)
        return True, "Participante guardado correctamente."
    except Exception as e:
        return False, f"Error al guardar integrante: {e}"


def eliminar_integrante(id_delegacion, dni):
    """Elimina un integrante de la nómina."""
    try:
        db.collection("delegaciones").document(str(id_delegacion)).collection(
            "integrantes"
        ).document(str(dni)).delete()
        return True
    except Exception:
        return False


# ==========================================
# 4. CARGA DE COMPROBANTES DE PAGO
# ==========================================


def registrar_pago_comprobante(id_delegacion, id_modelo, monto, drive_url):
    """Registra una transferencia en la colección de pagos."""
    try:
        pago_ref = db.collection("pagos").document()
        payload = {
            "id_delegacion": str(id_delegacion),
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
