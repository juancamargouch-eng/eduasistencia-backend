import os

def check_hex():
    with open("all_s3_keys.txt", "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    pattern = "f5-ae44-388183edfea7.jpg"
    for i, line in enumerate(lines):
        if pattern in line:
            clean_line = line.strip()
            print(f"Línea {i+1}: '{clean_line}'")
            print(f"Longitud: {len(clean_line)}")
            print(f"HEX: {clean_line.encode('utf-8').hex()}")
            # Comparar con mi string esperado
            expected = f"eduasistencia/fotos-estudiantes/{pattern}"
            print(f"Expected HEX: {expected.encode('utf-8').hex()}")
            if clean_line == expected:
                print("¡LAS CADENAS SON IDÉNTICAS!")
            else:
                print("¡HAY DIFERENCIAS!")

if __name__ == "__main__":
    check_hex()
