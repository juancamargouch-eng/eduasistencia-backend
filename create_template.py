import pandas as pd

data = {
    'Nombre': ['Juan Perez', 'Maria Garcia', 'Carlos Lopez'],
    'Grado': ['1ro Primaria', '2do Primaria', '3er Primaria'],
    'Seccion': ['A', 'B', 'C']
}

df = pd.DataFrame(data)
df.to_excel('plantilla_alumnos.xlsx', index=False)
print("Template created: plantilla_alumnos.xlsx")
