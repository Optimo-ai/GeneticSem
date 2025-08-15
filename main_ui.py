#!/usr/bin/env python3
"""
Main UI for traffic light simulation
Pygame-based menu interface for scenario selection and direct visualization
"""
import pygame
import sys
import threading
import queue
import os
from typing import Optional, Dict, Any

# Import simulation modules
from scenario_setups import get_scenario_setup
from genetic_algorithm import Genetics, Gstate

# Initialize Pygame
pygame.init()

# Constants
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
BACKGROUND_COLOR = (30, 30, 40)
TEXT_COLOR = (255, 255, 255)
BUTTON_COLOR = (70, 70, 90)
BUTTON_HOVER_COLOR = (90, 90, 120)
BUTTON_SELECTED_COLOR = (120, 120, 160)
ACCENT_COLOR = (100, 200, 255)

# Fonts
TITLE_FONT = pygame.font.Font(None, 48)
BUTTON_FONT = pygame.font.Font(None, 32)
PARAM_FONT = pygame.font.Font(None, 24)
STATUS_FONT = pygame.font.Font(None, 28)

class Button:
    def __init__(self, x, y, width, height, text, font=BUTTON_FONT):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.is_hovered = False
        self.is_selected = False
        
    def draw(self, screen):
        color = BUTTON_COLOR
        if self.is_selected:
            color = BUTTON_SELECTED_COLOR
        elif self.is_hovered:
            color = BUTTON_HOVER_COLOR
            
        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, TEXT_COLOR, self.rect, 2)
        
        text_surface = self.font.render(self.text, True, TEXT_COLOR)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)
        
    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                return True
        return False

class TrafficLightUI:
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("AI Traffic Light Controller - Scenario Selector")
        self.clock = pygame.time.Clock()
        self.running = True
        
        # UI State
        self.selected_scenario = 1
        self.sim_time = 60
        
        # Status
        self.status_text = "Select a scenario and click Start Simulation to optimize and visualize traffic"
        self.is_running_sim = False
        self.sim_thread = None
        self.status_queue = queue.Queue()
        self.current_generation = 0
        self.total_generations = 5
        
        # Create buttons
        self._create_buttons()
        
    def _create_buttons(self):
        # Scenario buttons
        self.scenario_buttons = []
        scenarios = [
            "Escenario 1 - 4-way intersection",
            "Escenario 2 - T-junction", 
            "Escenario 3 - Corridor (2 intersecciones)",
            "Escenario 4 - Grid 2×2",
            "Escenario 5 - Arterial (3 intersecciones)"
        ]
        
        start_y = 200
        for i, scenario in enumerate(scenarios):
            button = Button(50, start_y + i * 70, 500, 50, scenario)
            self.scenario_buttons.append(button)
            
        # Action buttons
        self.start_button = Button(600, 400, 180, 50, "Start Simulation")
        self.exit_button = Button(600, 470, 150, 50, "Exit")
        
        # Select first scenario by default
        self.scenario_buttons[0].is_selected = True
        
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_RETURN:
                    if not self.is_running_sim:
                        self.start_simulation()
                elif pygame.K_1 <= event.key <= pygame.K_5:
                    scenario_num = event.key - pygame.K_1
                    self.select_scenario(scenario_num)
                    
            # Handle button clicks
            for i, button in enumerate(self.scenario_buttons):
                if button.handle_event(event):
                    self.select_scenario(i)
                    
            if self.start_button.handle_event(event) and not self.is_running_sim:
                self.start_simulation()
                
            if self.exit_button.handle_event(event):
                self.running = False
                
    def select_scenario(self, scenario_index):
        if 0 <= scenario_index < len(self.scenario_buttons):
            # Deselect all buttons
            for button in self.scenario_buttons:
                button.is_selected = False
            # Select the clicked button
            self.scenario_buttons[scenario_index].is_selected = True
            self.selected_scenario = scenario_index + 1
            
    def start_simulation(self):
        if self.is_running_sim:
            return
            
        self.is_running_sim = True
        self.status_text = f"Starting Scenario {self.selected_scenario}..."
        
        # Start simulation in a separate thread
        self.sim_thread = threading.Thread(
            target=self.run_scenario_simulation,
            args=(self.selected_scenario,)
        )
        self.sim_thread.daemon = True
        self.sim_thread.start()
        
    def run_scenario_simulation(self, scenario):
        try:
            # Phase 1: GA Optimization
            self.status_queue.put(f"Starting GA optimization for Scenario {scenario}...")
            
            from main_ga import optimize_and_save
            
            # Progress callback to update UI
            def progress_callback(generation, total_generations, best_fitness):
                self.status_queue.put(f"GA Generation {generation}/{total_generations} - Best fitness: {best_fitness:.2f}")
            
            # Run GA optimization
            config_path = f"results/best_config_s{scenario}.json"
            
            # Use the updated optimize_and_save function
            result = optimize_and_save(
                scenario=scenario,
                pop=10,
                gens=5,
                sim_time=self.sim_time,
                seed=42,
                out_path=config_path,
                progress_callback=progress_callback
            )
            
            self.status_queue.put("GA optimization completed! Starting visualization...")
            
            # Phase 2: Visualization with optimized config
            self.status_queue.put(f"Starting visualization...")
            
            # Import subprocess to run visualization in separate process
            import subprocess
            import sys
            
            # Run visualization in separate process to avoid pygame conflicts
            cmd = [sys.executable, "visualize_best.py", "--config-path", config_path]
            
            self.status_queue.put(f"Opening simulation window in new process...")
            
            try:
                # Start the visualization process
                process = subprocess.Popen(cmd, cwd=".")
                
                self.status_queue.put(f"Simulation window opened! Close it to return to menu.")
                
                # Wait for the process to complete
                process.wait()
                
                self.status_queue.put("Simulation closed. Ready to run another scenario.")
                
            except Exception as e:
                self.status_queue.put(f"Error opening simulation: {str(e)}")
                
        except Exception as e:
            self.status_queue.put(f"Error: {str(e)}")
        finally:
            self.status_queue.put("SIM_COMPLETE")
            
    def update_status(self):
        # Check for status updates from the simulation thread
        try:
            while True:
                message = self.status_queue.get_nowait()
                if message == "SIM_COMPLETE":
                    self.is_running_sim = False
                    self.current_generation = 0
                elif "GA Generation" in message:
                    # Extract generation info for progress bar
                    parts = message.split("GA Generation ")[1].split("/")
                    if len(parts) >= 2:
                        self.current_generation = int(parts[0])
                        self.total_generations = int(parts[1].split(" ")[0])
                    self.status_text = message
                else:
                    self.status_text = message
        except queue.Empty:
            pass
            
    def draw(self):
        self.screen.fill(BACKGROUND_COLOR)
        
        # Title
        title_text = TITLE_FONT.render("AI Traffic Light Controller", True, ACCENT_COLOR)
        title_rect = title_text.get_rect(center=(WINDOW_WIDTH // 2, 50))
        self.screen.blit(title_text, title_rect)
        
        subtitle_text = PARAM_FONT.render("Select a Scenario to Simulate", True, TEXT_COLOR)
        subtitle_rect = subtitle_text.get_rect(center=(WINDOW_WIDTH // 2, 85))
        self.screen.blit(subtitle_text, subtitle_rect)
        
        # Scenario selection label
        scenario_label = BUTTON_FONT.render("Available Scenarios:", True, TEXT_COLOR)
        self.screen.blit(scenario_label, (50, 160))
        
        # Draw scenario buttons
        for button in self.scenario_buttons:
            button.draw(self.screen)
            
        # Simulation info panel
        info_x = 600
        info_y = 200
        info_label = BUTTON_FONT.render("Simulation Info:", True, TEXT_COLOR)
        self.screen.blit(info_label, (info_x, info_y))
        
        info_texts = [
            f"Selected: Scenario {self.selected_scenario}",
            f"Duration: {self.sim_time} seconds",
            f"Population: 10, Generations: 5",
            f"1. GA Optimization → 2. Visualization"
        ]
        
        for i, text in enumerate(info_texts):
            info_surface = PARAM_FONT.render(text, True, TEXT_COLOR)
            self.screen.blit(info_surface, (info_x, info_y + 40 + i * 25))
            
        # Action buttons
        if not self.is_running_sim:
            self.start_button.draw(self.screen)
        else:
            # Show disabled button
            disabled_rect = pygame.Rect(600, 400, 180, 50)
            pygame.draw.rect(self.screen, (50, 50, 50), disabled_rect)
            pygame.draw.rect(self.screen, (100, 100, 100), disabled_rect, 2)
            text_surface = BUTTON_FONT.render("Running...", True, (150, 150, 150))
            text_rect = text_surface.get_rect(center=disabled_rect.center)
            self.screen.blit(text_surface, text_rect)
            
        self.exit_button.draw(self.screen)
        
        # Status
        status_y = WINDOW_HEIGHT - 120
        status_label = STATUS_FONT.render("Status:", True, ACCENT_COLOR)
        self.screen.blit(status_label, (50, status_y))
        
        status_surface = PARAM_FONT.render(self.status_text, True, TEXT_COLOR)
        self.screen.blit(status_surface, (50, status_y + 30))
        
        # Progress bar for GA optimization
        if self.is_running_sim and self.current_generation > 0:
            progress_y = status_y + 55
            progress_width = 400
            progress_height = 20
            
            # Background bar
            progress_bg = pygame.Rect(50, progress_y, progress_width, progress_height)
            pygame.draw.rect(self.screen, (60, 60, 60), progress_bg)
            pygame.draw.rect(self.screen, TEXT_COLOR, progress_bg, 2)
            
            # Progress fill
            if self.total_generations > 0:
                fill_width = int((self.current_generation / self.total_generations) * progress_width)
                if fill_width > 0:
                    progress_fill = pygame.Rect(50, progress_y, fill_width, progress_height)
                    pygame.draw.rect(self.screen, ACCENT_COLOR, progress_fill)
            
            # Progress text
            progress_text = f"{self.current_generation}/{self.total_generations} generations"
            progress_surface = pygame.font.Font(None, 18).render(progress_text, True, TEXT_COLOR)
            self.screen.blit(progress_surface, (460, progress_y + 2))
        
        # Instructions
        instructions = [
            "Keyboard shortcuts: 1-5 to select scenario, ENTER to start, ESC to exit",
            "Click on scenarios to select, then click Start Simulation to see traffic"
        ]
        
        for i, instruction in enumerate(instructions):
            inst_surface = pygame.font.Font(None, 20).render(instruction, True, (180, 180, 180))
            self.screen.blit(inst_surface, (50, WINDOW_HEIGHT - 50 + i * 20))
        
        pygame.display.flip()
        
    def run(self):
        while self.running:
            self.handle_events()
            self.update_status()
            self.draw()
            self.clock.tick(60)
            
        pygame.quit()
        sys.exit()

def main():
    app = TrafficLightUI()
    app.run()

if __name__ == '__main__':
    main()
