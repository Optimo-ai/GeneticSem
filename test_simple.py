#!/usr/bin/env python3
"""
Simple test to verify scenario creation works
"""
from GA.scenarios import make_sim_factory

def test_scenario(scenario_id):
    print(f"Testing scenario {scenario_id}")
    
    try:
        # Get factory
        factory = make_sim_factory(scenario_id)
        print(f"Factory created: {factory}")
        
        # Create simulation
        sim = factory([10, 10, 10, 10], render=False)
        print(f"Simulation created: {sim}")
        print(f"Roads: {len(sim.roads)}")
        print(f"Traffic signals: {len(sim.traffic_signals)}")
        print(f"Scenario name: {getattr(sim, 'scenario_name', 'Unknown')}")
        print(f"Nodes: {getattr(sim, 'num_nodes', 0)}")
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    for i in range(1, 6):
        print(f"\n{'='*50}")
        success = test_scenario(i)
        print(f"Scenario {i}: {'SUCCESS' if success else 'FAILED'}")
