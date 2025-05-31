import pandas as pd
from debugpy.server.cli import switches
from pyscipopt import Model,quicksum
import sys

TOLERANCE = 10e-6
inf = 10e7

class InstanciaEstacionServicioModif():
    def __init__(self):
        self.cantidad_max_empleados = 20
        self.cantidad_horas = None
        self.dias_laborales = None
        self.llamados_por_hora = []

    def leer_datos(self, nombre_archivo, numero_instancia):
        # Los llamados por hora están en la columna dos del excel
        datos = pd.read_excel(nombre_archivo)

        #Leer la cantidad de horas
        self.cantidad_horas = datos.shape[0]
        self.dias_laborales = int((self.cantidad_horas/24) * 5/7)
        # lista en llamados_por_hora son las C_h
        self.llamados_por_hora = datos.iloc[:, numero_instancia].tolist()

def cargar_instancia(numero_instancia):

    nombre_archivo = "C:/Users/DAFNE/OneDrive/Documentos/GitHub/Tesis/DEMANDAS/instancias.xlsx"

    # Crea la instancia vacía
    instancia = InstanciaEstacionServicioModif()

    # Llena la instancia con los datos del archivo de entrada
    instancia.leer_datos(nombre_archivo, numero_instancia)

    return instancia

def agregar_elementos_modif(prob, instancia, RD_elegida: int, tasa_atencion_clientes):
    '''
    MODELO GENERAL
    Creamos las variables e_i, que son 1 si el empleado responde alguna llamada y 0 sino. Intentamos minimizar la suma de las e_i
    Definimos las variables del problema
    '''

    x_dict = {}
    o_dict = {}
    e_dict = {}

    cantHoras = instancia.cantidad_horas
    cantMaxEmpleados = instancia.cantidad_max_empleados

    for i in range (cantMaxEmpleados):
        e_dict[i] = prob.addVar(vtype = 'B', name = f"e_{i}", lb = 0, ub = 1)

    for i in range(cantMaxEmpleados):
        x_dict[i] = {}
        for h in range(cantHoras):
            x_dict[i][h] = prob.addVar(vtype='B', name=f"x_{i}_{h}", lb=0, ub=1)

    for h in range(cantHoras):
        o_dict[h] = prob.addVar(vtype='I', name=f"o_{h}", lb=0)

    #El empleado i es contratado
    for i in range(cantMaxEmpleados):
        for h in range(cantHoras):
            prob.addCons(x_dict[i][h] <= e_dict[i])

    #Restriccion 0_h: Son los empleados que son contratados y están disponibles para responder llamadas en la hora h
    for h in range(cantHoras):
        o_h = o_dict[h]  # O_h
        suma_x_i_j = 0
        for i in range(cantMaxEmpleados):
            for j in range(max(0, h - 7), h + 1):
                suma_x_i_j += x_dict[i][j]
        prob.addCons(o_h == suma_x_i_j)

    # Cubrir la demanda de clientes
    for h in range(cantHoras):
        prob.addCons( (60/tasa_atencion_clientes) * instancia.llamados_por_hora[h] - 60 * o_dict[h] <= 0 )

    #Cada trabajador empieza aporx 5 turnos por semana
    for i in range(cantMaxEmpleados):
        expr = sum(x_dict[i][h] for h in range(cantHoras))
        prob.addCons(expr == instancia.dias_laborales * e_dict[i])

    #Un trabajador no puede iniciar más de un turno en una ventana de 8 horas
    for i in range(cantMaxEmpleados):
        for h in range(cantHoras):
            expr = sum(x_dict[i][j] for j in range(max(0, h - 7), h + 1))
            prob.addCons(expr <= 1)

    # Restricción nueva: cada día cada empleado empieza un solo turno se empieza un solo turno
    for i in range(cantMaxEmpleados):
        for d in range(int(cantHoras / 24)):
            expr = sum(x_dict[i][h + 24*d] for h in range(24))
            prob.addCons(expr <= 1)

    #Restricción nueva: tiene que haber exactamente 2 francos por semana
    for i in range(cantMaxEmpleados):
        for s in range(int(cantHoras / 168)):
            expr = sum(x_dict[i][h + 168*s] for h in range(168)) #suma de los turnos que se arrancan en una semana (que por la restricción anterior es 1 por día)
            prob.addCons(expr <= 5) #Si el empleado fue contratado, por la sabemos que va a ser por igualdad. Sino, va a ser 0. No puede arrancar más de 5
                                    #Obs: la resitricción original no cubría este caso, podían estar todos los francos del mes seguidos.

    '''
    RESTRICCIONES DESEABLES
    '''
    deltas = [0, 0, 0, 0, 0]
    match RD_elegida:
        case 1 | 2:
            deltas[RD_elegida - 1] = 1 / (instancia.dias_laborales * cantMaxEmpleados + 1)
        case 3:
            deltas[RD_elegida - 1] = 1 / ((instancia.cantidad_horas/24) * cantMaxEmpleados + 1)
        case 4:
            deltas[RD_elegida - 1] = 1 / (cantMaxEmpleados + 1)
        case 5:
            deltas[RD_elegida - 1] = 1/ (instancia.dias_laborales * cantMaxEmpleados * 12 + 1) #multiplico por 12 porque es la diferencia más grande que se puede tener con el horario elegido
        case 0:
            deltas[0] = 0

    #Restricción deseable 1: Maximizar la cantidad de veces que un empleado empieza su turno en el mismo horario que el día anterior.
    #Creamos las A_{i,h,d}
    if deltas[0] != 0:
        a_dict = {}
        for i in range(cantMaxEmpleados):
            a_dict[i] = {}
            for h in range(24):
                a_dict[i][h] = {}
                for d in range(1, int(cantHoras / 24)): #las defino a partir del día 2
                    a_dict[i][h][d] = prob.addVar(vtype='B', name=f"a_{i}_{h}_{d}", lb=0, ub=1)
                    prob.addCons(2 * a_dict[i][h][d] <= x_dict[i][h + 24*d] + x_dict[i][h + 24 * (d-1)])
                    prob.addCons(x_dict[i][h + 24*d] + x_dict[i][h + 24 * (d-1)] <= 1 + a_dict[i][h][d])

    #Restricción deseable 2: Maximizar la cantidad de veces que un empleado empieza su turno +/- una hora que en el día anterior.
    if deltas[1] != 0:
        c_dict = {}
        for i in range(cantMaxEmpleados):
            c_dict[i] = {}
            for h in range(24):
                c_dict[i][h] = {}
                for d in range(1, int(cantHoras / 24) - 1):  # las defino a partir del día 2
                    c_dict[i][h][d] = prob.addVar(vtype='B', name=f"a_{i}_{h}_{d}", lb=0, ub=1)
                    expr = x_dict[i][h + 24 * d] + x_dict[i][ (h-1) + 24 * d] + x_dict[i][(h+1) + 24 * d] + x_dict[i][h + 24 * (d - 1)]
                    prob.addCons(2 * c_dict[i][h][d] <= expr)
                    prob.addCons(expr <= 1 + c_dict[i][h][d])

    # Restricción deseable 3: Maximizar la cantidad de veces que un empleado empieza su turno en el mismo horario que el turno anterior
    # (es decir, si en el medio hubo un franco, respetar el horario del turno antes del franco).

    if deltas[2] != 0:
        f_dict = {}
        l_dict = {}

        #Búsqueda del último franco
        for i in range(cantMaxEmpleados):
            f_dict[i] = {}
            l_dict[i] = {}
            for d in range(1, int(cantHoras / 24)):

                # Definimos el franco del día d para empleado i
                f_dict[i][d] = prob.addVar(vtype='I', name=f"f_{i}_{d}", lb=0)
                prob.addCons(f_dict[i][d] == 1 - quicksum(x_dict[i][h + 24 * d] for h in range(24)))
                l_dict[i][d] = {}
                #El último día no franco es exactamente 1 en ese rango
                variables_validas = []
                for k in range(1, 6):  # k = 1 to 5
                    if d - k < 1:
                        continue  # evitamos índices inválidos
                    else:
                        l_dict[i][d][k] = prob.addVar(vtype='B', name=f"l_{i}_{d}_{k}", lb=0, ub=1)
                        variables_validas.append(k)
                        # Restricción: l_{i,d,k} ≤ 1 - f_{i,d-k}
                        prob.addCons(l_dict[i][d][k] <= 1 - f_dict[i][d - k])

                        # Restricciones: l_{i,d,k} ≤ f_{i,d-j} para j = 1,...,k-1
                        for j in range(1, k):
                            if d - j < 1:
                                continue  # evitamos índices inválidos
                            prob.addCons(l_dict[i][d][k] <= f_dict[i][d - j])
                prob.addCons(quicksum(l_dict[i][d][k] for k in variables_validas) <= 1)


        #Estructura de la restricción conociendo el último franco
        s_dict = {}
        m_dict = {}
        for i in range(cantMaxEmpleados):
            s_dict[i] = {}
            m_dict[i] = {}
            for h in range(24):  # comenzamos en 2 ya que miramos hacia atrás
                s_dict[i][h] = {}
                m_dict[i][h] = {}
                for d in range(2, cantHoras // 24):
                    # Variable s_{i,d,h}
                    s_dict[i][h][d] = prob.addVar(vtype='B', name=f"s_{i}_{h}_{d}")

                    # Restricción: s <= x en día d
                    prob.addCons(s_dict[i][h][d] <= x_dict[i][h + 24 * d])

                    # Restricción: s <= 1 - f_{i,d}
                    prob.addCons(s_dict[i][h][d] <= 1 - f_dict[i][d])

                    # Acumulador para la suma de m_{i,d,h,k}
                    m_sum = []
                    m_dict[i][h][d] = {}

                    for k in range(1, 6):
                        if d - k < 1:
                            continue  # evitamos índices negativos

                        # Variable m_{i,d,h,k}
                        m_var = prob.addVar(vtype='B', name=f"m_{i}_{h}_{d}_{k}")
                        m_dict[i][h][d][k] = m_var
                        m_sum.append(m_var)

                        # Turno en el día d-k a la hora h
                        turno_dk_h = h + 24 * (d - k)
                        prob.addCons(2 * m_var <= x_dict[i][turno_dk_h] + l_dict[i][d][k])
                        prob.addCons(x_dict[i][turno_dk_h] + l_dict[i][d][k] <= 1 + m_var)

                    # Restricción: s <= sum_k m_{i,d,h,k}
                    if m_sum: #Acá chillaba no sé por qué
                        prob.addCons(s_dict[i][h][d] <= sum(m_sum))

    #la delta en peor caso queda igual que las anteriores debido a que su reducción en días de corrido es la misma cota
    # Restricción deseable 4: Maximizar la cantidad de empleados que empiezan siempre a la misma hora.
    if deltas[3] != 0:
        w_dict = {}
        # Creamos las w_ih
        for i in range(cantMaxEmpleados):
            w_dict[i] = {}
            for h in range(24):  # Las horas de 0 a 23
                w_dict[i][h] = prob.addVar(vtype='B', name=f"w_{i}_{h}", lb=0, ub=1)
                suma_x_i_hd = sum(
                    x_dict[i][h + 24 * d] for d in range(int(cantHoras / 24)))  # Sumamos los turnos de cada día
                prob.addCons(instancia.dias_laborales * w_dict[i][h] == suma_x_i_hd)

    #Restricción deseable 5: Fijar un horario de entrada para cada empleado, y minimizar las horas totales de diferencia con ese horario de entrada máximo.
    z_i = [0,0,16,16,8,8,7,7,15,15,6,14,13,12,5,17,11,3,19,4]
    if deltas[4] != 0:
        y_dict = {}
        for i in range(cantMaxEmpleados):
            y_dict[i] = {}
            for h in range(24):
                y_dict[i][h] = prob.addVar(vtype='I', name=f"y_{i}_{h}", lb=0)
                prob.addCons(y_dict[i][h] == sum( x_dict[i][h + 24 * d] for d in range(int(cantHoras / 24))))

    #FUNCION OBJETIVO
    objetivo_a = 0
    if deltas[0] != 0:
        objetivo_a = sum(
            sum(
                sum(a_dict[i][h][d] for d in range(1, int(cantHoras / 24)))
                for h in range(24)
            )
            for i in range(cantMaxEmpleados)
        )
    objetivo_c = 0
    if deltas[1] != 0:
        objetivo_c = sum(
            sum(
                sum(c_dict[i][h][d] for d in range(1, int(cantHoras / 24) - 1))
                for h in range(24)
            )
            for i in range(cantMaxEmpleados)
        )
    objetivo_s = 0
    if deltas[2] != 0:
        objetivo_s = sum(
            sum(
                sum(s_dict[i][h][d] for d in range(2, int(cantHoras / 24)))
                for h in range(24)
            )
            for i in range(cantMaxEmpleados)
        )
    objetivo_w = 0
    if deltas[3] != 0:
        objetivo_w = sum(sum(w_dict[i][h] for h in range(24)) for i in range(cantMaxEmpleados))
    objetivo_y = 0
    if deltas[4] != 0:
        objetivo_y = sum(sum(y_dict[i][h] * abs(z_i[i] - h) for h in range(24)) for i in range(cantMaxEmpleados))

    funcion_objetivo = sum(e_dict[i] for i in e_dict) - deltas[0] * objetivo_a - deltas[1] * objetivo_c - deltas[2] * objetivo_s - deltas[3] * objetivo_w + deltas[4] * objetivo_y
    prob.setObjective(funcion_objetivo , "minimize") #Luego del inciso opcional, se mantiene esta función objetivo

    return x_dict, e_dict

def resolver_lp(prob):
    # Definir los parametros del solver
    prob.setParam("limits/gap", TOLERANCE)
    prob.setParam("limits/time", 1800) #Media hora por instancia y cada parámetro
    # Resolver el lp
    prob.optimize()

def mostrar_resultados(prob: Model, instancia, x_dict, e_dict):

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

    df_resultados = pd.DataFrame.from_dict(
        turnos_empleados, orient='index'
    ).fillna("")

    df_resultados.index.name = "Empleado"
    df_resultados.columns = [f"Turno {j + 1}" for j in range(df_resultados.shape[1])]

    with open(f'C:/Users/DAFNE/OneDrive/Documentos/GitHub/Tesis/RESULTADOS/Resultados_finales/RD{RD_elegida}_{int(tasa_atencion_clientes)}/instancia{numero_instancia}_RD{RD_elegida}_tasa{tasa_atencion_clientes}', 'w') as f:

        f.write(f"Scip Status: {prob.getStatus()}\n")
        f.write(f"Solving Time: {prob.getSolvingTime()}\n")
        f.write(f"Solving Nodes: {prob.getNNodes()}\n")
        f.write(f"Primal Bound: {prob.getPrimalbound()}\n")
        f.write(f"Dual Bound: {prob.getDualbound()}\n")
        f.write(f"Gap: {prob.getGap()}\n")

        # Mostrar cantidad total de trabajadores necesarios
        f.write(f"\nCantidad de trabajadores: {cantEmp}")

        f.write("\nHorarios de inicio de turnos por empleado:\n")
        f.write(df_resultados.to_string())

def main(numero_instancia, RD_elegida, tasa_atencion_clientes):
    # Lectura de datos desde el archivo de entrada
    instancia = cargar_instancia(numero_instancia)
    # Definicion del problema
    prob = Model()
    # Definicion del modelo
    x_dict, e_dict = agregar_elementos_modif(prob, instancia, RD_elegida, tasa_atencion_clientes)  # Ahora devolvemos x_dict
    # Resolucion del modelo
    resolver_lp(prob)
    # Mostrar los resultados
    mostrar_resultados(prob, instancia, x_dict, e_dict)

if __name__ == '__main__':
    print(f"Arguments count: {len(sys.argv)}")
    assert len(sys.argv) == 4
    numero_instancia = int(sys.argv[1])
    RD_elegida = int(sys.argv[2])
    tasa_atencion_clientes = float(sys.argv[3])
    assert numero_instancia >= 1 and numero_instancia <= 25
    assert RD_elegida >= 0 and RD_elegida <= 5
    assert tasa_atencion_clientes in {37.02, 30.0, 25.0, 20.0}
    main(numero_instancia= numero_instancia, RD_elegida = RD_elegida, tasa_atencion_clientes = tasa_atencion_clientes)

