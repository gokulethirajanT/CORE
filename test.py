import pandas as pd
variable_info = pd.read_csv('reference/DSB_FDZ_Gesundheit_Variablen.csv')
print(variable_info.columns.tolist())