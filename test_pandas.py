import pandas as pd
import io

try:
    df = pd.DataFrame({'col1': [1, 2], 'col2': [3, 4]})
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    print("Pandas Excel creation successful")
except Exception as e:
    print(f"Pandas Error: {e}")
