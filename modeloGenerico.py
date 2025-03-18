import pandas as pd
from pyscipopt import Model

TOLERANCE = 10e-6
inf = 10e7

class InstanciaEstacionServicioModif():
    def __init__(self):
        self.cantidad_max_empleados = 20
        self.cantidad_horas = None
        self.dias_laborales = None
        self.llamados_por_hora = []

    def leer_datos(self, nombre_archivo):
        # Los llamados por hora están en la columna dos del excel
        datos = pd.read_excel(nombre_archivo)

        #Leer la cantidad de horas
        self.cantidad_horas = datos.shape[0]
        self.dias_laborales = int((self.cantidad_horas/24) * 5/7)
        # lista en llamados_por_hora son las C_h
        self.llamados_por_hora = datos.iloc[:, 1].tolist()

def cargar_instancia():

    nombre_archivo = "DEMANDAS/mucho_horario_laboral_finde_media_fuera_poco.xlsx"

    # Crea la instancia vacía
    instancia = InstanciaEstacionServicioModif()

    # Llena la instancia con los datos del archivo de entrada
    instancia.leer_datos(nombre_archivo)

    return instancia

def agregar_elementos_modif(prob, instancia):

    x_dict = {}
    o_dict = {}
    e_dict = {}

    cantHoras = instancia.cantidad_horas
    cantMaxEmpleados = instancia.cantidad_max_empleados

    #Generamos las modificaciones del modelo anterior
    #Se piensan variables parecidas a "Bin Packing, en donde tengo n recipientes y quiero llenar la menor cantidad posible"

    #Creamos las variables e_i, que son 1 si el empleado responde alguna llamada y 0 sino. Intentamos minimizar la suma de las e_i

    for i in range (cantMaxEmpleados):
        e_dict[i] = prob.addVar(vtype = 'B', name = f"e_{i}", lb = 0, ub = 1)

    for i in range(cantMaxEmpleados):
        x_dict[i] = {}
        for h in range(cantHoras):
            x_dict[i][h] = prob.addVar(vtype='B', name=f"x_{i}_{h}", lb=0, ub=1)

    for h in range(cantHoras):
        o_dict[h] = prob.addVar(vtype='C', name=f"o_{h}", lb=0)

    #El empleado i es contratado
    for i in range(cantMaxEmpleados):
        for h in range(cantHoras):
            prob.addCons(x_dict[i][h] <= e_dict[i])

    #Restriccion 0_h: Son los empleados que son contratados y están disponibles para responder llamadas en la hora h
    for h in range(cantHoras):
        o_h = o_dict[h]  # O_h
        suma_x_i_j = 0
        for i in range(cantMaxEmpleados):
            for j in range(max(0, h - 5), h + 1):
                suma_x_i_j += x_dict[i][j]
        prob.addCons(o_h == suma_x_i_j)

    # Cumplir todos los llamados que lleguen
    for h in range(cantHoras):
        prob.addCons( 8 * instancia.llamados_por_hora[h] - 60 * o_dict[h] <= 0 )

    # Restricción: Cada trabajador empieza aprox 5 turnos por semana (y eso en un rato lo voy a restringir más)
    for i in range(cantMaxEmpleados):
        expr = sum(x_dict[i][h] for h in range(cantHoras))
        prob.addCons(expr == instancia.dias_laborales * e_dict[i])

    #Un trabajador no puede iniciar más de un turno en una ventana de 6 horas
    for i in range(cantMaxEmpleados):
        for h in range(cantHoras):
            expr = sum(x_dict[i][j] for j in range(max(0, h - 5), h + 1))
            prob.addCons(expr <= 1)

    '''
    #No se pueden iniciar turnos en las últimas 5 horas
    for i in range(cantMaxEmpleados):
        expr = sum(x_dict[i][h] for h in range(164, 168))
        prob.addCons(expr == 0)
    '''

    #Agregamos la restricción opcional del inciso 4: cada empleado contratado arranca todos sus turnos a la misma hora
    w_dict = {}

    #Creamos las w_ih
    for i in range(cantMaxEmpleados):
        w_dict[i] = {}
        for h in range(24): #Las horas de 0 a 23
            w_dict[i][h] = prob.addVar(vtype='B', name=f"w_{i}_{h}", lb=0, ub=1)

    #Definimos cada w_ih
    for i in range(cantMaxEmpleados):
        for h in range(24):
            suma_x_i_hd = sum(x_dict[i][h + 24 * d] for d in range(int(cantHoras / 24)))  # Sumamos los turnos de cada día
            prob.addCons(instancia.dias_laborales * w_dict[i][h] == suma_x_i_hd)

    #FUNCION OBJETIVO
    prob.setObjective(sum(e_dict[i] for i in e_dict) , "minimize") #Luego del inciso opcional, se mantiene esta función objetivo

    return x_dict, e_dict

def armar_lp(prob, instancia):
    # Agregar las variables
    agregar_elementos_modif(prob, instancia)

    # Escribir el lp a archivo
    prob.writeProblem()

def resolver_lp(prob):
    # Definir los parametros del solver
    prob.setParam("limits/gap", TOLERANCE)
    # Resolver el lp
    prob.optimize()
    print(f"Estado de optimización: {prob.getStatus()}")  # Debugging

def mostrar_resultados(prob, instancia, x_dict, e_dict):

    cantHoras = instancia.cantidad_horas
    # Identificar empleados contratados (e_i = 1)
    indices_empleados_necesarios = [i for i in e_dict if prob.getVal(e_dict[i]) > 0.5]

    cantEmp = len(indices_empleados_necesarios)

    # Para cada empleado contratado, quiero ver en qué horario empiezan sus turnos
    turnos_empleados = {i: [] for i in indices_empleados_necesarios}

    # Obtener los valores óptimos de x_dict[i][h]
    for i in turnos_empleados.keys():
        for h in range(cantHoras):
            if prob.getVal(x_dict[i][h]) > 0.5:  # Si x[i][h] es 1, el turno comienza en h
                turnos_empleados[i].append(h)

    # Convertir a DataFrame para mejor visualización (sugerencia gpt, yo había hecho una matriz pero queda mejor así)
    df_resultados = pd.DataFrame.from_dict(
        turnos_empleados, orient='index'
    ).fillna("")

    df_resultados.index.name = "Empleado"
    df_resultados.columns = [f"Turno {j + 1}" for j in range(df_resultados.shape[1])]

    print("\nHorarios de inicio de turnos por empleado:")
    print(df_resultados.to_string())

    # Mostrar cantidad total de trabajadores necesarios
    print(f"\nCantidad de trabajadores necesarios para atender todas las llamadas: {cantEmp}")

def main():
    # Lectura de datos desde el archivo de entrada
    instancia = cargar_instancia()
    # Definicion del problema
    prob = Model()
    # Definicion del modelo
    x_dict, e_dict = agregar_elementos_modif(prob, instancia)  # Ahora devolvemos x_dict
    # Resolucion del modelo
    resolver_lp(prob)
    empleados_necesarios = prob.getObjVal()
    # Mostrar los resultados
    mostrar_resultados(prob, instancia, x_dict, e_dict)


if __name__ == '__main__':
    main()