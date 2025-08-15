#!/usr/bin/env python3
from typing import Callable, List
from TrafficSimulator.graphs import (
    graph1_four_way,
    graph2_t_junction,
    graph3_corridor_two_intersections,
    graph4_grid_2x2,
    graph5_arterial_three,
)

SCENARIOS = {
    1: "4-way",
    2: "T-junction(3 phases)",
    3: "Corridor(2 nodes)",
    4: "Grid 2x2(4 nodes)",
    5: "Arterial(3 nodes)",
}

_BUILDERS = {
    1: graph1_four_way,
    2: graph2_t_junction,
    3: graph3_corridor_two_intersections,
    4: graph4_grid_2x2,
    5: graph5_arterial_three,
}

def _get_build_callable(scenario_id: int):
    if scenario_id not in _BUILDERS:
        raise ValueError(f"Unknown scenario_id={scenario_id}. Use one of {sorted(_BUILDERS.keys())}")
    builder_fn = _BUILDERS[scenario_id]
    build = builder_fn()  # devuelve build(config, render)
    return build

def make_sim_factory(scenario_id: int) -> Callable[[list, bool], "Simulation"]:
    build = _get_build_callable(scenario_id)
    def sim_factory(config, render: bool = False):
        return build(config=config, render=render)
    return sim_factory

def get_phases_per_signal(scenario_id: int) -> List[int]:
    build = _get_build_callable(scenario_id)  # <-- builder, NO el factory
    phases = getattr(build, "phases_per_signal", None)
    return list(phases) if phases else [4]
