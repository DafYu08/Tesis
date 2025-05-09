for tasa in 37.02 30 25 20; do
    for i in $(seq 1 25); do
        python src/Restricciones_Deseables/Modelo_restricciones_deseables.py $i 3 $tasa
    done
done
