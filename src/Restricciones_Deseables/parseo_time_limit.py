from collections import defaultdict
import matplotlib.pyplot as plt
import os

# Diccionarios para contar instancias por tipo y estado
status_counts = {
    'optimal': defaultdict(int),
    'timelimit': defaultdict(int)
}

# Tasas que estás usando
tasas = [37.02, 30.0, 25.0, 20.0]

# Leer cada archivo y contar el status
for k in range(6):  # tipos de archivo: RD0 a RD5
    for tasa in tasas:
        for j in range(1, 26):  # instancias del 1 al 25
            ruta = f'C:/Users/DAFNE/OneDrive/Documentos/GitHub/Tesis/RESULTADOS/Resultados_finales/RD{k}_{round(tasa)}/instancia{j}_RD{k}_tasa{tasa}'
            if not os.path.exists(ruta):
                continue  # saltar si el archivo no existe

            with open(ruta, 'r') as f:
                for line in f:
                    if line.startswith('Scip Status:'):
                        status = line.strip().split(': ')[1]
                        if status in status_counts:
                            status_counts[status][k] += 1
                        break

# Preparar datos
tipos = list(range(6))
optimal_vals = [status_counts['optimal'][k] for k in tipos]
time_limit_vals = [status_counts['timelimit'][k] for k in tipos]

# Dibujar gráfico
fig, ax = plt.subplots(figsize=(10, 6))
bottom_opt = 0
bottom_tl = 0

total_opt = sum(optimal_vals)
total_tl = sum(time_limit_vals)

# Colores personalizados (opcional)
colores = plt.cm.Set3.colors

# Apilar y etiquetar segmentos
for i, k in enumerate(tipos):
    val_opt = optimal_vals[i]
    val_tl = time_limit_vals[i]

    # Barra 'optimal'
    if val_opt > 0:
        ax.bar('optimal', val_opt, bottom=bottom_opt, color=colores[i], label=f'RD{k}')
        ax.text(
            x='optimal',
            y=bottom_opt + val_opt / 2,
            s=f'RD{k}: {val_opt} ({val_opt / total_opt:.0%})',
            ha='center', va='center', fontsize=9, color='black'
        )
        bottom_opt += val_opt

    # Barra 'time-limit'
    if val_tl > 0:
        ax.bar('time-limit', val_tl, bottom=bottom_tl, color=colores[i], label=f'RD{k}')
        ax.text(
            x='time-limit',
            y=bottom_tl + val_tl / 2,
            s=f'RD{k}: {val_tl} ({val_tl / total_tl:.0%})',
            ha='center', va='center', fontsize=9, color='black'
        )
        bottom_tl += val_tl

# Etiquetas y estilo
ax.set_ylabel('Cantidad de instancias')
ax.set_title('Distribución de finalización del algoritmo (Scip-Status)')
#ax.legend(title='RD', bbox_to_anchor=(1.05, 1), loc='upper left')
plt.tight_layout()
plt.show()
