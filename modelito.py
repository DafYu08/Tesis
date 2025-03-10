import sys
import pandas as pd
from pyscipopt import Model, scip, quicksum
from recordclass import recordclass
import openpyxl

TOLERANCE = 10e-6

class InstanciaEstacionServicio:
    def __init__(self):
        self.cantidad_trabajadores = 7
        self.cantidad_horas = 168
        self.llamados_por_hora = []

    def leer_datos(self, nombre_archivo):
        # Los llamados por hora están en la columna dos del excel
        datos = pd.read_excel(nombre_archivo)

        # lista en llamados_por_hora son las C_h
        self.llamados_por_hora = datos.iloc[:, 1].tolist()

def cargar_instancia():

    nombre_archivo = "demanda.xlsx"

    # Crea la instancia vacía
    instancia = InstanciaEstacionServicio()

    # Llena la instancia con los datos del archivo de entrada
    instancia.leer_datos(nombre_archivo)

    return instancia

def agregar_elementos(prob, instancia):

    x_dict = {}
    o_dict = {}
    z_dict = {}
    cantHoras = instancia.cantidad_horas
    cantEmp = instancia.cantidad_trabajadores

    for i in range(cantEmp):
        x_dict[i] = {}
        for h in range(cantHoras):
            x_dict[i][h] = prob.addVar(vtype='B', name=f"x_{i}_{h}", lb=0, ub=1)

    for h in range(cantHoras):
        o_dict[h] = prob.addVar(vtype='C', name=f"o_{h}", lb=0)

    for h in range(cantHoras):
        z_dict[h] = prob.addVar(vtype='C', name=f"z_{h}", lb=0)

    #Restriccion 0_h
    #restriccion_0_h = {}
    for h in range(instancia.cantidad_horas):
        o_h = o_dict[h]  # O_h
        suma_x_i_j = 0
        for i in range(instancia.cantidad_trabajadores):
            for j in range(max(0, h - 5), h + 1):
                suma_x_i_j += x_dict[i][j]
        #restriccion_0_h[h] = prob.addCons(o_h == suma_x_i_j)  # Se debe cumplir que O_h - sum(x_{i,j}) = 0
        prob.addCons(o_h == suma_x_i_j)

    # Restricción de z_h
    for h in range(instancia.cantidad_horas):
        prob.addCons(z_dict[h] + 60 * o_dict[h] >= 8 * instancia.llamados_por_hora[h])
        prob.addCons(z_dict[h] >= 0)


    # Restricción: Cada trabajador empieza 5 turnos
    for i in range(instancia.cantidad_trabajadores):
        expr = sum(x_dict[i][h] for h in range(instancia.cantidad_horas))
        prob.addCons(expr == 5)

    #Un trabajador no puede iniciar más de un turno en una ventana de 6 horas
    for i in range(instancia.cantidad_trabajadores):
        for h in range(instancia.cantidad_horas):
            expr = sum(x_dict[i][j] for j in range(max(0, h - 5), h + 1))
            prob.addCons(expr <= 1)

    #No se pueden iniciar turnos en las últimas 5 horas
    for i in range(instancia.cantidad_trabajadores):
        expr = sum(x_dict[i][h] for h in range(164, 168))
        prob.addCons(expr == 0)

    #FUNCION OBJETIVO
    prob.setObjective(sum(z_dict[h] for h in range(instancia.cantidad_horas)), "minimize")

    return x_dict

def armar_lp(prob, instancia):
    # Agregar las variables
    agregar_elementos(prob, instancia)

    # Escribir el lp a archivo
    prob.writeProblem()

def resolver_lp(prob):
    # Definir los parametros del solver
    prob.setParam("limits/gap", TOLERANCE)
    # Resolver el lp
    prob.optimize()


def mostrar_resultados(prob, instancia, x_dict):
    """
    Extrae los horarios en los que cada trabajador inicia su turno
    y los muestra en formato de matriz.
    """
    cantEmp = instancia.cantidad_trabajadores
    cantHoras = instancia.cantidad_horas

    # Inicializar una lista vacía para cada empleado
    turnos_empleados = {i: [] for i in range(cantEmp)}

    # Obtener los valores óptimos de x_dict[i][h]
    for i in range(cantEmp):
        for h in range(cantHoras):
            if prob.getVal(x_dict[i][h]) > 0.5:  # Si x[i][h] es 1, el turno comienza en h
                turnos_empleados[i].append(h)

    # Convertir a DataFrame para mejor visualización
    df_resultados = pd.DataFrame.from_dict(turnos_empleados, orient='index')
    df_resultados.index.name = "Empleado"
    df_resultados.columns = [f"Turno {j + 1}" for j in range(5)]

    print("\nHorarios de inicio de turnos por empleado:")
    print(df_resultados.to_string())


def main():
    # Lectura de datos desde el archivo de entrada
    instancia = cargar_instancia()

    # Definicion del problema
    prob = Model()
    print(instancia.llamados_por_hora)
    # Definicion del modelo
    x_dict = agregar_elementos(prob, instancia)  # Ahora devolvemos x_dict

    # Resolucion del modelo
    resolver_lp(prob)

    # Mostrar los resultados
    mostrar_resultados(prob, instancia, x_dict)

    obj_val = prob.getObjVal()
    print(f"Obj. Valor: {obj_val}")

if __name__ == '__main__':
    main()

