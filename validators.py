import re


def validate_email(email: str) -> bool:
    """Valida formato de email. Retorna True si es válido o está vacío."""
    if not email:
        return True
    pattern = r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def validate_cedula(cedula: str) -> bool:
    """Valida que la cédula sea numérica y tenga longitud razonable (6-12 dígitos)."""
    if not cedula:
        return False
    return cedula.isdigit() and 6 <= len(cedula) <= 12


def validate_placa(placa: str) -> bool:
    """
    Valida formato de placa colombiana.
    Formatos válidos: ABC123, AB123C, ABC1234
    """
    if not placa:
        return False
    pattern = r"^[A-Z]{3}\d{3}$|^[A-Z]{2}\d{3}[A-Z]$|^[A-Z]{3}\d{4}$"
    return bool(re.match(pattern, placa.upper()))


def validate_phone(phone: str) -> bool:
    """Valida formato de teléfono colombiano (7-10 dígitos). Vacío es válido."""
    if not phone:
        return True
    return phone.isdigit() and 7 <= len(phone) <= 10


def validate_unidad(unidad: str) -> bool:
    """Valida que la unidad/torre/apartamento no esté vacío."""
    return bool(unidad and unidad.strip())


def validate_required(text: str, field_name: str = "campo") -> tuple[bool, str]:
    """Valida que un campo requerido no esté vacío."""
    if not text or not text.strip():
        return False, f"{field_name} es obligatorio"
    return True, ""