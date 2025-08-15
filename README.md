GeneticSem

Sistema de simulación de tráfico con control de semáforos optimizado por Algoritmos Genéticos (GA) y visualización en Pygame.  
Permite probar distintos escenarios (cruces, corredores y mallas) y guardar la mejor configuración de tiempos por fase.

Características

- 🧬 Optimización GA de tiempos de semáforo por escenario.
- 🚗 Generación configurable de vehículos con rutas y pesos.
- 🖥️ Visualización en tiempo real (Pygame).
- 📊 Métricas básicas: vehículos completados y tiempo medio de espera.

Requisitos

- Python 3.10 (recomendado)
- Paquetes: `numpy`, `scipy`, `pygame`

Instalación rápida:
```bash
pip install -r requirements.txt

El proyecto no es 100% funcional.

1) Ejecutar GA (optimización)
python .\main_ga.py --scenario 2 --pop 20 --gens 10 --sim-time 60 --seed 7

Esto entrena el GA para el escenario 2 y guarda la mejor configuración en: results/best_config_s2.json

2) Visualizar la mejor configuración
python .\visualize_best.py --scenario 2 --sim-time 60

Problemas comunes (Troubleshooting):

1) “Los semáforos no cambian de color / los autos no avanzan”
Verifica:

TrafficSimulator/simulation.py → en update() se llama antes a self._update_signals(dt_local).

TrafficSimulator/traffic_signal.py → update(dt) incrementa el tiempo y llama a next_phase() cuando dt acumulado supera la duración de la fase actual.

graphs.py → los grupos de entrada coinciden con las vías entrantes (IDs correctos) y el número de fases encaja con la cantidad de grupos (o máscaras).

No dejes tiempos 0 o negativos en ciclos. El código normaliza valores no válidos, pero lo ideal es poner duraciones > 0.

2) “El GA da siempre el mismo fitness / -10000”

Asegúrate de que hay tráfico suficiente (rates razonables en add_generator).

Revisa que no haya colisiones inmediatas por intersecciones mal definidas.

Prueba --gens y --pop más altos y semilla distinta (--seed).

3) “Se cierra la ventana al instante”

Revisa mensajes en consola: puede ser colisión (collision_detected) o cierre (ESC).

Aumenta --sim-time.

By: EM.


