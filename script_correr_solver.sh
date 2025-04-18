for i in $(seq 13 25); do
    python src/Restricciones_Deseables/Modelo_restricciones_deseables.py $i 5 25
done
	
for i in $(seq 1 25); do
    python src/Restricciones_Deseables/Modelo_restricciones_deseables.py $i 5 20
done


