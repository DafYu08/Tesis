import numpy as np
import pandas as pd
import os

def generar_demanda(cant_dias, dias_mas_demanda, horas_mas_demanda):
    # Definir las horas totales
    total_horas = cant_dias * 24
    horas = np.arange(1, total_horas + 1)

    # Determinar el día de la semana
    dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    dias = np.array([dias_semana[(h // 24) % 7] for h in range(total_horas)])

    # Determinar la hora del reloj
    horas_reloj = np.array([h % 24 for h in range(total_horas)])

    # Generar la demanda de llamadas
    demanda = np.zeros(total_horas, dtype=int)

    for i in range(total_horas):
        dia_actual = (i // 24) % 7  # Día de la semana en índice (0=Lunes, 6=Domingo)
        hora_actual = i % 24  # Hora del día (0-23)

        if dia_actual in dias_mas_demanda:
            if hora_actual in horas_mas_demanda:
                demanda[i] = np.random.randint(20, 50)  # Alta demanda
            else:
                demanda[i] = np.random.randint(5, 15)  # Media demanda
        else:
            if hora_actual in horas_mas_demanda:
                demanda[i] = np.random.randint(10, 20)  # Media demanda
            else:
                demanda[i] = np.random.randint(0, 10)  # Baja demanda

    # Crear DataFrame
    df = pd.DataFrame({
        "Hora": horas,
        "Llamadas": demanda,
        "Día": dias,
        "Hora_formato": horas_reloj
    })

    # Crear carpeta si no existe
    carpeta_salida = "C:/Users/DAFNE/OneDrive/Documentos/GitHub/Tesis/DEMANDAS"
    os.makedirs(carpeta_salida, exist_ok=True)

    # Generar nombre único para el archivo
    nombre = "vie_sa_mediodia_tarde"
    archivo_salida = os.path.join(carpeta_salida, f"{nombre}.xlsx")

    # Guardar en Excel
    df.to_excel(archivo_salida, index=False)

    return df, archivo_salida


# Ejemplo de uso
dias = 7
horas_pico = np.array([10, 11, 12, 18, 19, 20])  # Horas de más demanda
dias_alta_demanda = np.array([4, 5])  # Viernes y Sábado

df_demanda, archivo_generado = generar_demanda(dias, dias_alta_demanda, horas_pico)
print(f"Archivo guardado en: {archivo_generado}")

'''
Idea de esta semana: 
- Investigar según trabajadores/internet cuáles son los días de mayor y menor demanda en el negocio.
- Generar datos sintéticos según las investigaciones intuitivas/registros para 1 mes.
- Utilizar la técnica de Bootstrap para samplear de estos datos sintéticos.
- Predecir, utilizando Random Forest (aclarar por qué), la distribución mensual promedio de los datos, generando un dataset_promedio.
- Correr el modelo con estos datos promedio y las restricciones actuales, y comparar resultados con otras instancias.



'''
