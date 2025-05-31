for tasa in 37.02; do
    for i in $(seq 4 25); do
        python src/Restricciones_Deseables/Modelo_restricciones_deseables.py $i 2 $tasa
    done
done

for tasa in 30; do
    for i in $(seq 1 10); do
        python src/Restricciones_Deseables/Modelo_restricciones_deseables.py $i 2 $tasa
    done
done