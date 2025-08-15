import random
import json
import os
from typing import List, Dict, Tuple, Optional

# Nota: dejamos importes de RL fuera para no arrastrar dependencias viejas.
# El GA NO dependerá de Gstate/Genetics ni de Setups de RL.

class GeneticAlgorithmOptimizer:
    """
    Main GA optimizer for traffic light control (parameter tuning).
    - 'individual' representa una configuración compacta (lista de números)
      que el sim_factory sabrá traducir a fases/tiempos por intersección.
    """

    def __init__(self, population_size: int = 20, generations: int = 50, solution_length: int = 5):
        self.population_size = population_size
        self.generations = generations
        self.solution_length = solution_length
        self.best_config: Optional[list] = None
        self.best_fitness: float = float("-inf")
        self.progress_callback = None

    # -------------------------
    # Inicialización y GA básico
    # -------------------------
    def initialize_population(self) -> List[List[int]]:
        """
        Inicializa población aleatoria.
        Cada gen ~ tiempo 'green' en segundos [5, 90].
        (El amarillo lo puede fijar el builder o derivarse; si el builder
         requiere otra convención, lo mapea internamente.)
        """
        population = []
        for _ in range(self.population_size):
            individual = [random.randint(5, 90) for _ in range(self.solution_length)]
            population.append(individual)
        return population

    def crossover(self, parent1: List[int], parent2: List[int]) -> List[int]:
        """Crossover 1 punto."""
        if len(parent1) != len(parent2) or len(parent1) < 2:
            return parent1[:]
        cp = random.randint(1, len(parent1) - 1)
        return parent1[:cp] + parent2[cp:]

    def mutate(self, individual: List[int], mutation_rate: float = 0.1) -> List[int]:
        """Mutación con clamp a [5, 90]."""
        child = individual[:]
        for i in range(len(child)):
            if random.random() < mutation_rate:
                # jitter +/- 10s
                delta = random.randint(-10, 10)
                child[i] = max(5, min(90, child[i] + delta))
        return child

    # -------------------------
    # Bucle principal de optimización
    # -------------------------
    def run_optimization(self, sim_factory, sim_time: int = 60, seed: Optional[int] = None, render: bool = False):
        """
        Ejecuta el GA.
        - sim_factory: callable (config:list, render:bool) -> Simulation
        - sim_time: segundos de simulación por evaluación (headless)
        - render: siempre False en GA; la visual se hace aparte
        """
        if seed is not None:
            random.seed(seed)

        print(f"Starting GA optimization with {self.population_size} population, {self.generations} generations")

        population = self.initialize_population()

        for gen in range(self.generations):
            print(f"Generation {gen + 1}/{self.generations}")
            scored = []
            for indiv in population:
                fit = self.evaluate_fitness(indiv, sim_factory, sim_time, render=False)
                scored.append((indiv, fit))

            # Mejor de la generación
            scored.sort(key=lambda x: x[1], reverse=True)  # mayor fitness = mejor
            best_indiv, best_fit = scored[0]

            if best_fit > self.best_fitness:
                self.best_fitness = best_fit
                self.best_config = best_indiv[:]

            print(f"Best fitness in generation {gen + 1}: {best_fit}")

            if self.progress_callback:
                # Callback opcional: puedes enviar dict si tu UI lo espera
                try:
                    self.progress_callback(gen + 1, self.generations, best_fit)
                except Exception:
                    pass

            # Siguiente generación (elitismo simple + cruces)
            if gen < self.generations - 1:
                parents = [ind for ind, _ in scored[: max(2, self.population_size // 2)]]
                new_pop = parents[:]  # elitismo: mantener top
                while len(new_pop) < self.population_size:
                    p1 = random.choice(parents)
                    p2 = random.choice(parents)
                    child = self.crossover(p1, p2)
                    child = self.mutate(child, mutation_rate=0.1)
                    new_pop.append(child)
                population = new_pop

        return self.best_config, self.best_fitness

    # -------------------------
    # Evaluación de fitness
    # -------------------------
    def evaluate_fitness(self, individual: List[int], sim_factory, sim_time: int, render: bool = False) -> float:
        """
        Crea la simulación con la config propuesta y la ejecuta headless sim_time segundos.
        Se intenta avanzar el tiempo de forma genérica:
          - run_step(dt) si existe
          - update(dt) si existe
          - run(False) como fallback (avanza un tick)
        Fitness (maximizar):
            + flujo (vehículos completados / tiempo)
            - espera promedio
            - colisiones (penalización fuerte)
        """
        try:
            # Construir simulación para esta config
            sim = sim_factory(individual, render=render)

            # dt heurístico
            dt = getattr(sim, "dt", None)
            if not isinstance(dt, (int, float)) or dt <= 0:
                dt = 0.5  # 0.5s por tick si no hay dt expuesto

            t = 0.0
            # Métricas robustas
            get_done = lambda s: (
                getattr(s, "vehicles_done", None)
                if hasattr(s, "vehicles_done")
                else max(0, getattr(s, "n_vehicles_generated", 0) - getattr(s, "n_vehicles_on_map", 0))
            )

            while t < sim_time and not getattr(sim, "gui_closed", False) and not getattr(sim, "collision_detected", False):
                # Avance genérico
                if hasattr(sim, "run_step"):
                    sim.run_step(dt)
                elif hasattr(sim, "update"):
                    sim.update(dt)
                elif hasattr(sim, "run"):
                    # 'run' sin parámetro o con False para "tick" neutro
                    try:
                        sim.run(False)
                    except TypeError:
                        sim.run()
                else:
                    # No hay manera obvia de avanzar: salir con mal fitness
                    return -1.0

                t += dt

            # Recolectar métricas
            avg_wait = float(getattr(sim, "current_average_wait_time", 0.0))
            done = float(get_done(sim))
            collided = 1.0 if getattr(sim, "collision_detected", False) else 0.0

            # Fitness: mayor es mejor
            flow = done / max(sim_time, 1.0)
            fitness = (1.0 * flow) - (2.0 * avg_wait) - (1000.0 * collided)
            # Check if enough vehicles were generated
            generated = getattr(sim, "n_vehicles_generated", 0)
            if generated < 3:
                return -10_000  # penaliza ejecuciones sin tráfico
            
            return fitness

        except Exception as e:
            print(f"Error in simulation: {e}")
            return -1.0

    # -------------------------
    # Persistencia
    # -------------------------
    def save_best_config(self, filepath: str = "results/best_config.json"):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        data = {
            "best_config": self.best_config,
            "best_fitness": self.best_fitness,
            "optimization_params": {
                "population_size": self.population_size,
                "generations": self.generations,
                "solution_length": self.solution_length,
            },
        }
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
        print(f"Best configuration saved to {filepath}")
