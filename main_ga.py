#!/usr/bin/env python3
"""
Main GA optimization script with reusable function for UI integration.
"""
import argparse
import json
import random
import os
from pathlib import Path

from genetic_algorithm import GeneticAlgorithmOptimizer
from GA.scenarios import make_sim_factory, get_phases_per_signal
try:
    from GA.scenarios import SCENARIOS
except Exception:
    SCENARIOS = {}

def optimize_and_save(scenario: int, pop: int, gens: int, sim_time: int, seed: int, out_path: str, progress_callback=None) -> dict:
    """
    Run GA optimization and save best config to file.
    """
    random.seed(seed)

    # ensure results dir
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)

    # phases per signal for this scenario (for GA chromosome sizing if needed)
    phases_per_signal = get_phases_per_signal(scenario)
    total_phases = sum(phases_per_signal)

    optimizer = GeneticAlgorithmOptimizer(
        population_size=pop,
        generations=gens,
        solution_length=total_phases  # keep as your GA expects; we’ll align internals in genetic_algorithm.py
    )

    if progress_callback:
        optimizer.progress_callback = progress_callback

    # obtain the simulation factory (callable) for the scenario
    sim_factory = make_sim_factory(scenario)

    best_config, best_fitness = optimizer.run_optimization(
        sim_factory=sim_factory,  # should be a callable: sim = sim_factory(config, render=False)
        sim_time=sim_time,
        seed=seed,
        render=False
    )

    # let optimizer also persist internally if it wants, but save here too:
    optimizer.save_best_config(out_path)

    return {
        'scenario': scenario,
        'best_config': best_config,
        'best_fitness': best_fitness,
        'population_size': pop,
        'generations': gens,
        'sim_time': sim_time,
        'seed': seed
    }


def main():
    parser = argparse.ArgumentParser(description="AI Traffic Lights Controller - Genetic Algorithm")
    parser.add_argument("--scenario", type=int, default=1, help="Scenario number (1..5)")
    parser.add_argument("--pop", type=int, default=20, help="Population size")
    parser.add_argument("--gens", type=int, default=50, help="Number of generations")
    parser.add_argument("--sim-time", type=int, default=60, help="Simulation time in seconds")
    parser.add_argument("--seed", type=int, default=None, help="Random seed (default 42 if omitted)")
    parser.add_argument("--render", action='store_true', help="After optimizing, visualize with Pygame")

    args = parser.parse_args()
    if args.seed is None:
        args.seed = 42

    scen_name = SCENARIOS.get(args.scenario, f"Scenario {args.scenario}")

    print("Starting GA optimization:")
    print(f"  Scenario: {args.scenario} - {scen_name}")
    print(f"  Population: {args.pop}")
    print(f"  Generations: {args.gens}")
    print(f"  Simulation time: {args.sim_time}s")
    print(f"  Seed: {args.seed}")
    print(f"  Render: {args.render}")

    out_path = f"results/best_config_s{args.scenario}.json"

    result = optimize_and_save(
        scenario=args.scenario,
        pop=args.pop,
        gens=args.gens,
        sim_time=args.sim_time,
        seed=args.seed,
        out_path=out_path
    )

    print("\nOptimization completed!")
    print(f"Best fitness: {result['best_fitness']}")
    print(f"Best configuration saved to {out_path}")

    if args.render:
        # chain visualization (optional convenience)
        try:
            from visualize_best import run_visualization
            run_visualization(
                scenario=args.scenario,
                sim_time=args.sim_time,
                config_path=out_path
            )
        except Exception as e:
            print(f"[WARN] Could not auto-open visualization: {e}")
            print("You can run manually:")
            print(f"  python visualize_best.py --scenario {args.scenario} --sim-time {args.sim_time}")


if __name__ == '__main__':
    main()
