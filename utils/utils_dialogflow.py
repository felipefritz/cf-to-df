import unidecode

def clean_display_name(name: str):
    """Convert special chars to valid chars or -
    
    Returns:
        Información converted to Informacion
    """
    # Convertir caracteres no ASCII a su equivalente más cercano en ASCII
    cleaned_name = unidecode.unidecode(name)
    # only valid chars or -
    cleaned_name = ''.join(ch for ch in cleaned_name if ch.isalnum() or ch == '-')
    return cleaned_name