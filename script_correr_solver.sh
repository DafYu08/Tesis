for tasa in 37.02; do
    for i in $(seq 1 25); do
        python src/Restricciones_Deseables/Modelo_restricciones_deseables.py $i 0 $tasa
    done
done
