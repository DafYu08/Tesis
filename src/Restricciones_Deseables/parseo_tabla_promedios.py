from collections import defaultdict
import pandas as pd

if __name__ == '__main__':
    tasas = [37.02, 30.0, 25.0, 20.0]
    rds = range(6)
    filas = {}
    for rd in rds:
        for i in tasas:
            empleados_contratados = 0
            solving_nodes = 0
            solving_time = 0.0
            gap = 0.0
            fila_actual = []
            for j in range(1,26):
                with open(f'C:/Users/DAFNE/OneDrive/Documentos/GitHub/Tesis/RESULTADOS/Resultados_finales/RD{rd}_{round(i)}/instancia{j}_RD{rd}_tasa{i}') as f:
                    content = f.readlines()
                    solving_time += float(content[1].strip().split()[2])
                    solving_nodes += int(content[2].strip().split()[2])
                    gap += float(content[5].strip().split()[1])
                    empleados_contratados += int(content[7].strip().split()[3])
            fila_actual.append(empleados_contratados//25)
            fila_actual.append(solving_nodes//25)
            fila_actual.append(solving_time/25.0)
            fila_actual.append(gap/25.0)
            filas[f'RD{rd}_{i}'] = fila_actual

    # Crear DataFrame
    df = pd.DataFrame.from_dict(filas, orient='index')
    df.columns = ['#Emp', 'Solving Nodes', 'Solving Time', 'Gap']
    print(df)
