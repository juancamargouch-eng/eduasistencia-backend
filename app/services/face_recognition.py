import numpy as np

def compare_faces(known_encoding: list, check_encoding: list, tolerance: float = 0.50) -> tuple[bool, float]:
    """
    Compares two face descriptors using Euclidean distance.
    Returns (True, distance) if distance <= tolerance.
    """
    if known_encoding is None or check_encoding is None:
        return False, 1.0
        
    known = np.array(known_encoding)
    check = np.array(check_encoding)
    
    # Calculate Euclidean distance
    dist = np.linalg.norm(known - check)
    print(f"DEBUG: Comparing faces. Distance: {dist}", flush=True)
    return float(dist) <= tolerance, float(dist)
