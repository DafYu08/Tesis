for i in $(seq 20 25); do
    python src/Restricciones_Deseables/Modelo_restricciones_deseables.py $i 3 37.02
done


for tasa in 30 25 20; do
    for i in $(seq 1 25); do
        python src/Restricciones_Deseables/Modelo_restricciones_deseables.py $i 3 $tasa
    done
done
