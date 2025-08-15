#!/usr/bin/env python3
"""
Visualization script for best GA configurations (render=True).
- No usa RL (Genetics/Gstate).
- Usa el mismo sim_factory(config, render) que el GA.
"""

import argparse
import json
import os
import time
from typing import Optional, List

import pygame  # aseguramos reloj/event loop
from GA.scenarios import make_sim_factory, SCENARIOS


def _load_best_config(config_path: Optional[str]) -> Optional[List[int]]:
    """Devuelve la lista de tiempos (best_config) o None si no existe."""
    if not config_path or not os.path.exists(config_path):
        return None
    with open(config_path, "r") as f:
        data = json.load(f)
    # aceptar tanto {"best_config":[...]} como lista directa
    if isinstance(data, dict) and "best_config" in data:
        return data["best_config"]
    if isinstance(data, list):
        return data
    return None


def _pick_default_config_path(scenario: int) -> str:
    p1 = f"results/best_config_s{scenario}.json"
    p2 = "results/best_config.json"
    return p1 if os.path.exists(p1) else p2


def _advance_sim(sim, dt: float):
    """Avanza un tick de simulación con la API disponible."""
    if hasattr(sim, "run_step"):
        sim.run_step(dt)
    elif hasattr(sim, "update"):
        sim.update(dt)
    elif hasattr(sim, "run"):
        try:
            # algunas impls usan run(False) como 'tick' sin cambio de fase
            sim.run(False)
        except TypeError:
            sim.run()
    else:
        raise RuntimeError("Simulation object has no step method (run_step/update/run).")


def run_visualization(scenario: int, sim_time: int = 60, config_path: Optional[str] = None, config: Optional[List[int]] = None):
    """Función reutilizable (llamada por main_ga.py si pasas --render)."""
    scen_name = SCENARIOS.get(scenario, f"Scenario {scenario}")
    if config is None:
        if config_path is None:
            config_path = _pick_default_config_path(scenario)
        config = _load_best_config(config_path)

    print("Starting visualization:")
    print(f"  Scenario: {scenario} — {scen_name}")
    print(f"  Simulation time: {sim_time}s")
    if config_path:
        print(f"  Config file: {config_path}")
        if config is None:
            print("  [WARN] Config file missing/invalid; proceeding with default timings.")

    # Crear simulación con render=True
    sim_factory = make_sim_factory(scenario)
    sim = sim_factory(config, render=True)

    # Si el motor requiere init_gui explícito:
    if hasattr(sim, "init_gui"):
        try:
            sim.init_gui()
        except Exception:
            # si ya estaba inicializada o no hace falta, seguimos
            pass

    clock = pygame.time.Clock()
    elapsed = 0.0

    print("Running simulation… (ESC o cerrar ventana para salir)")
    while elapsed < sim_time and not getattr(sim, "gui_closed", False) and not getattr(sim, "collision_detected", False):
        # Gestionar eventos básicos de ventana
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                setattr(sim, "gui_closed", True)
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                setattr(sim, "gui_closed", True)

        dt = clock.tick(60) / 1000.0  # 60 FPS
        try:
            _advance_sim(sim, dt)
        except Exception as e:
            print(f"[ERROR] Step failed: {e}")
            break

        # Si el motor expone dibujado explícito
        if hasattr(sim, "draw") and callable(getattr(sim, "draw")):
            try:
                sim.draw()
            except Exception:
                pass
        elif hasattr(sim, "render") and callable(getattr(sim, "render")):
            try:
                sim.render()
            except Exception:
                pass

        pygame.display.flip()
        elapsed += dt

    # Métricas finales
    avg_wait = float(getattr(sim, "current_average_wait_time", 0.0))
    done = float(
        getattr(sim, "vehicles_done", None)
        if hasattr(sim, "vehicles_done")
        else max(0, getattr(sim, "n_vehicles_generated", 0) - getattr(sim, "n_vehicles_on_map", 0))
    )
    collided = bool(getattr(sim, "collision_detected", False))
    if getattr(sim, "gui_closed", False):
        print("Window closed by user.")
    elif collided:
        print("Simulation ended due to collision.")
    else:
        print(f"Simulation completed! Vehicles done: {done:.0f} | Average wait: {avg_wait:.2f}s")


def main():
    parser = argparse.ArgumentParser(description="Visualize best GA configuration")
    parser.add_argument("--scenario", type=int, default=1, help="Scenario number (1..5)")
    parser.add_argument("--sim-time", type=int, default=60, help="Simulation time in seconds")
    parser.add_argument("--config", type=str, default=None, help="Path to configuration file")
    parser.add_argument("--config-path", type=str, default=None, help="Path to configuration file (alias)")
    args = parser.parse_args()

    # Elegir config_path si no se pasó
    cfg_path = args.config or args.config_path or _pick_default_config_path(args.scenario)

    run_visualization(
        scenario=args.scenario,
        sim_time=args.sim_time,
        config_path=cfg_path,
        config=None,
    )


if __name__ == "__main__":
    main()
