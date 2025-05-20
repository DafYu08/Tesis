from collections import defaultdict
import matplotlib.pyplot as plt
import seaborn as sns
import os
import pandas as pd

# Tasas y tipos deseados
tasas = [37.02, 30.0, 25.0, 20.0]
deseables = [1, 3, 4, 5]

# Lista para acumular los resultados como filas
datos = []

# Leer archivos y extraer gaps
for k in deseables:
    for tasa in tasas:
        for j in range(1, 26):
            ruta = f'C:/Users/DAFNE/OneDrive/Documentos/GitHub/Tesis/RESULTADOS/Resultados_finales/RD{k}_{round(tasa)}/instancia{j}_RD{k}_tasa{tasa}'
            if not os.path.exists(ruta):
                continue

            with open(ruta, 'r') as f:
                for line in f:
                    if line.startswith('Gap:'):
                        try:
                            gap = float(line.strip().split(': ')[1])
                            if 0 <= gap <= 1:  # solo valores válidos
                                valor_gap = float(line.strip().split(': ')[1])
                                datos.append({'RD': f'RD{k}', 'Gap': valor_gap})
                            else:
                                print(f"Gap fuera de rango en RD{k}, tasa {tasa}, instancia {j}: {gap}")
                        except ValueError:
                            print(f"Gap no numérico en RD{k}, tasa {tasa}, instancia {j}: {line.strip()}")
                        break


# Crear DataFrame
df = pd.DataFrame(datos)

# Gráfico
plt.figure(figsize=(10, 6))
ax = sns.boxplot(
    x='RD', y='Gap', data=df, showmeans=True, color='orange',
    meanprops={"marker": "x", "markerfacecolor": "#0a4203", "markeredgecolor": "#0a4203"}
)

ax.set_facecolor("#fff9f2")
plt.gcf().set_facecolor("#fff9f2")
plt.title('Distribución de los Gaps en instancias con Time Limit', color='purple', size=14)
plt.xlabel('Tipo de archivo (RD)', color='purple', size=12)
plt.ylabel('Gap (%)', color='purple', size=12)
plt.xticks(color='#013306')
plt.yticks(color='#013306')
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()
plt.show()
