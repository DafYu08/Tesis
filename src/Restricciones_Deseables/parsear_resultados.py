from collections import defaultdict

if __name__ == '__main__':
    tasas = [37.02, 30.0, 25.0, 20.0]
    contador = defaultdict(int)
    cant_empleados_totales = 0
    for i in tasas:
        for j in range(1,26):
            with open(f'C:/Users/DAFNE/OneDrive/Documentos/GitHub/Tesis/RESULTADOS/Resultados_finales/RD4_{round(i)}/instancia{j}_RD4_tasa{i}') as f:
                for _ in range(11):
                    next(f)
                for line in f:
                    cant_empleados_totales += 1
                    cols = line.strip().split()
                    cols[1] = int(cols[1])
                    contador[cols[1] % 24] += 1 #voy a tener un horario nuevo

    print(contador)
    # Calcular el porcentaje que representa cada clave del total
    porcentajes = {k: (v / cant_empleados_totales) * 100 for k, v in contador.items()}

    # Ordenar de mayor a menor según el porcentaje
    ranking = sorted(porcentajes.items(), key=lambda x: x[1], reverse=True)

    # Mostrar los top 20
    print("\nTop claves con mayor porcentaje:")
    for k, pct in ranking[:]:
        print(f"{k}: {pct:.2f}%")
