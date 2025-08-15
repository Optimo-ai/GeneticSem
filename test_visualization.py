#!/usr/bin/env python3
"""
Test script to verify that visualization works independently
"""
import pygame
from scenario_setups import get_scenario_setup
from genetic_algorithm import Genetics, Gstate

def test_scenario_visualization(scenario_num=1):
    """Test visualization for a specific scenario"""
    print(f"Testing visualization for scenario {scenario_num}")
    
    # Initialize pygame
    pygame.init()
    
    # Get scenario setup
    setup_func = get_scenario_setup(scenario_num)
    sim = setup_func()
    
    print("Initializing GUI...")
    sim.init_gui()
    
    print("Starting simulation loop...")
    print("You should see a window with roads, vehicles, and traffic lights.")
    print("Close the window to end the test.")
    
    # Run simulation with GA control
    g = Genetics(5, [0, 1])
    
    while not (sim.gui_closed or sim.completed):
        # Use GA to determine traffic light actions
        current_state = Gstate(sim, g.solution_length)
        action_list = g.pick(current_state)
        
        for action in action_list:
            if sim.completed or sim.gui_closed:
                break
            if action == 0:
                sim.run(False)  # Don't switch lights
            else:
                sim.run(True)   # Switch lights
        
        if sim.gui_closed:
            break
    
    if sim.gui_closed:
        print("Window closed by user.")
    elif sim.collision_detected:
        print("Simulation ended due to collision.")
    else:
        print(f"Simulation completed! Average wait time: {sim.current_average_wait_time:.2f}s")

if __name__ == '__main__':
    import sys
    scenario = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    test_scenario_visualization(scenario)
