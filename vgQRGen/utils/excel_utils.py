"""
Módulo de utilidades para manejo de Excel.

Proporciona funciones auxiliares para manipulación de datos de Excel.
"""

def excel_column_to_index(column_letter: str) -> int:
    """
    Convertir letra de columna de Excel a índice de columna basado en cero.
    
    Args:
        column_letter (str): Letra de columna (por ejemplo, 'A', 'B', 'AA', etc.)
        
    Returns:
        int: Índice de columna basado en cero
        
    Ejemplos:
        'A' -> 0
        'B' -> 1
        'Z' -> 25
        'AA' -> 26
        'AB' -> 27
    """
    column_letter = column_letter.upper().strip()
    result = 0
    for i, char in enumerate(reversed(column_letter)):
        result += (ord(char) - ord('A') + 1) * (26 ** i)
    return result - 1

def index_to_excel_column(index: int) -> str:
    """
    Convertir índice de columna basado en cero a letra de columna de Excel.
    
    Args:
        index (int): Índice de columna basado en cero
        
    Returns:
        str: Letra de columna (por ejemplo, 'A', 'B', 'AA', etc.)
    """
    index += 1
    result = ""
    while index > 0:
        index, remainder = divmod(index - 1, 26)
        result = chr(ord('A') + remainder) + result
    return result