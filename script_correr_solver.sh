for i in $(seq 6 25); do
    python src/Restricciones_Deseables/Modelo_restricciones_deseables.py $i 5 30
done

for tasa in 25 20; do
    for i in $(seq 1 25); do
        python src/Restricciones_Deseables/Modelo_restricciones_deseables.py $i 5 $tasa
    done
done
