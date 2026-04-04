import os

def char_by_char():
    with open("all_s3_keys.txt", "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    pattern = "f5-ae44-388183edfea7.jpg"
    for line in lines:
        if pattern in line:
            real = line.strip()
            # Expected based on .env and student.photo_url
            expected = "eduasistencia/fotos-estudiantes/f5-ae44-388183edfea7.jpg"
            
            print(f"Real:     {list(real)}")
            print(f"Expected: {list(expected)}")
            
            for i, (r, e) in enumerate(zip(real, expected)):
                if r != e:
                    print(f"Diferencia en pos {i}: REAL='{r}' ({ord(r)}) vs EXP='{e}' ({ord(e)})")
                    break
            if len(real) != len(expected):
                print(f"Longitudes diferentes: REAL={len(real)}, EXP={len(expected)}")
            return

if __name__ == "__main__":
    char_by_char()
