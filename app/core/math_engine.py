import struct

def to_float32(val):
    """Simula la precisión de 32-bit (IEEE 754) del motor Source 2."""
    return struct.unpack('f', struct.pack('f', val))[0]

def normalize_input_float(input_float, input_min, input_max):
    """Calcula el porcentaje de desgaste relativo (Nueva fórmula Valve)."""
    rango = input_max - input_min
    if rango == 0: return 0.0
    
    val = (input_float - input_min) / rango
    return to_float32(val)

def calculate_outcome_float(inputs_data, outcome_min, outcome_max):
    """
    Calcula el float de salida aplicando normalización de inputs.
    Args:
        inputs_data: Lista de 10 dicts con keys {'float', 'min_float', 'max_float'}
    """
    if len(inputs_data) != 10:
        raise ValueError(f"Se requieren 10 inputs. Recibidos: {len(inputs_data)}")
    
    normalized_sum = 0.0
    
    # 1. Normalizar cada input según sus propios caps (Filler Killer Update)
    for inp in inputs_data:
        norm = normalize_input_float(inp['float'], inp['min_float'], inp['max_float'])
        normalized_sum += norm
        
    # 2. Promediar y proyectar al rango de salida
    avg_normalized = to_float32(normalized_sum / 10.0)
    outcome_range = to_float32(outcome_max - outcome_min)
    
    raw_outcome = (outcome_range * avg_normalized) + outcome_min
    final_float = to_float32(raw_outcome)
    
    # 3. Aplicar límites (Clamping)
    if final_float < outcome_min: return outcome_min
    if final_float > outcome_max: return outcome_max
    
    return final_float

def get_wear_name(float_value):
    if float_value < 0.07: return "Factory New"
    if float_value < 0.15: return "Minimal Wear"
    if float_value < 0.38: return "Field-Tested"
    if float_value < 0.45: return "Well-Worn"
    return "Battle-Scarred"