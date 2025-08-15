#!/usr/bin/env python3
"""
Simple test to verify basic simulation functionality
"""
import pygame
from TrafficSimulator.Setups.two_way_intersection import two_way_intersection_setup

def test_basic_simulation():
    """Test basic simulation without GA"""
    print("Testing basic simulation...")
    
    # Initialize pygame
    pygame.init()
    
    # Create simulation
    sim = two_way_intersection_setup(50)
    
    print("Initializing GUI...")
    sim.init_gui()
    
    print("Running simulation - you should see vehicles and traffic lights")
    print("Close window to end test")
    
    # Simple loop without GA
    step_count = 0
    while not (sim.gui_closed or sim.completed) and step_count < 1000:
        sim.update()  # Just update simulation
        step_count += 1
        
        # Switch lights every 100 steps
        if step_count % 100 == 0:
            for signal in sim.traffic_signals:
                signal.update()
    
    print(f"Test completed after {step_count} steps")
    if sim.gui_closed:
        print("Window closed by user")
    elif sim.collision_detected:
        print("Collision detected")
    else:
        print("Simulation completed normally")

if __name__ == '__main__':
    test_basic_simulation()
