#!/usr/bin/env python3
"""
Legacy main.py - redirects to main_ga.py for GA-only execution
"""
import sys
import subprocess

if __name__ == '__main__':
    print("This repository now only supports Genetic Algorithm (GA) optimization.")
    print("Please use main_ga.py instead:")
    print("  python main_ga.py --scenario 1 --pop 10 --gens 5 --sim-time 60 --seed 42")
    print("  python visualize_best.py --scenario 1 --sim-time 60")
    print("")
    print("Redirecting to main_ga.py with default parameters...")
    
    # Redirect to main_ga.py with default parameters
    subprocess.run([sys.executable, "main_ga.py", "--scenario", "1", "--pop", "10", "--gens", "5", "--sim-time", "60"])
