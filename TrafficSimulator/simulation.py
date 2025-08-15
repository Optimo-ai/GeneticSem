from itertools import chain
from typing import List, Dict, Tuple, Set, Optional

from scipy.spatial import distance

from TrafficSimulator.road import Road
from TrafficSimulator.traffic_signal import TrafficSignal
from TrafficSimulator.vehicle_generator import VehicleGenerator
from TrafficSimulator.window import Window


class Simulation:
    def __init__(self, max_gen: int = None):
        self.t = 0.0  # Time
        self.dt = 1 / 60  # Time step (seconds)
        self.roads: List[Road] = []
        self.generators: List[VehicleGenerator] = []
        self.traffic_signals: List[TrafficSignal] = []

        self.collision_detected: bool = False
        self.n_vehicles_generated: int = 0
        self.n_vehicles_on_map: int = 0

        self._gui: Optional[Window] = None

        self._non_empty_roads: Set[int] = set()
        # To calculate the number of vehicles in the junction, use:
        # n_vehicles_on_map - _inbound_roads vehicles - _outbound_roads vehicles
        self._inbound_roads: Set[int] = set()
        self._outbound_roads: Set[int] = set()

        self._intersections: Dict[int, Set[int]] = {}  # {Road index: [intersecting roads' indexes]}
        self.max_gen: Optional[int] = max_gen  # Vehicle generation limit
        self._waiting_times_sum: float = 0  # for vehicles that completed the journey

    def add_intersections(self, intersections_dict: Dict[int, Set[int]]) -> None:
        self._intersections.update(intersections_dict)

    def add_road(self, start: Tuple[int, int], end: Tuple[int, int]) -> None:
        road = Road(start, end, index=len(self.roads))
        self.roads.append(road)

    def add_roads(self, roads: List[Tuple[int, int]]) -> None:
        for road in roads:
            self.add_road(*road)

    def add_generator(self, vehicle_rate, paths):
        """
        Registra un generador de vehículos.

        Acepta:
        - (peso, [r0, r1, ...])  -> una sola ruta
        - (peso, [[r0, r1,...], [r0, rX,...], ...]) -> varias rutas (se aplanan)
        """
        # Normalizar paths: permitir (peso, [ruta]) y (peso, [[ruta1], [ruta2], ...])
        norm_paths = []
        for weight, roads in paths:
            if isinstance(roads, (list, tuple)) and roads and isinstance(roads[0], (list, tuple)):
                for r in roads:
                    norm_paths.append((weight, list(r)))
            else:
                norm_paths.append((weight, list(roads)))
        paths = norm_paths

        # Guardar el rate con el nombre que el resto del código espera
        self.vehicle_rate = float(vehicle_rate)

        # Crear diccionario de carreteras de entrada y marcar inbound/outbound
        inbound_roads = {}
        for weight, road_path in paths:
            first_road_idx = road_path[0]
            inbound_roads[first_road_idx] = self.roads[first_road_idx]
            self._inbound_roads.add(first_road_idx)
            if len(road_path) > 1:
                last_road_idx = road_path[-1]
                self._outbound_roads.add(last_road_idx)

        # Crear y agregar el generador de vehículos
        generator = VehicleGenerator(vehicle_rate, paths, inbound_roads)
        self.generators.append(generator)

    def add_traffic_signal(self, roads: List[List[int]], cycle: List[Tuple],
                           slow_distance: float, slow_factor: float, stop_distance: float) -> None:
        # Convertir índices de carretera a objetos Road
        road_groups: List[List[Road]] = [[self.roads[i] for i in group] for group in roads]
        traffic_signal = TrafficSignal(road_groups, cycle, slow_distance, slow_factor, stop_distance)
        self.traffic_signals.append(traffic_signal)

    @property
    def gui_closed(self) -> bool:
        """Returns an indicator whether the GUI was closed."""
        return self._gui and self._gui.closed

    @property
    def non_empty_roads(self) -> Set[int]:
        """Returns a set of non-empty road indexes."""
        return self._non_empty_roads

    @property
    def completed(self) -> bool:
        """Whether a terminal state is reached."""
        if self.max_gen:
            return self.collision_detected or (self.n_vehicles_generated == self.max_gen
                                               and not self.n_vehicles_on_map)
        return self.collision_detected

    @property
    def intersections(self) -> Dict[int, Set[int]]:
        """
        Reduces the intersections' dict to non-empty roads.
        :return: {non-empty road index: [non-empty intersecting roads indexes]}
        """
        output: Dict[int, Set[int]] = {}
        non_empty_roads: Set[int] = self._non_empty_roads
        for road in non_empty_roads:
            if road in self._intersections:
                intersecting_roads = self._intersections[road].intersection(non_empty_roads)
                if intersecting_roads:
                    output[road] = intersecting_roads
        return output

    @property
    def current_average_wait_time(self) -> float:
        """Average wait time of vehicles that completed the journey + on-map average."""
        on_map_wait_time = 0.0
        completed_wait_time = 0.0
        n_completed_journey = self.n_vehicles_generated - self.n_vehicles_on_map
        if n_completed_journey:
            completed_wait_time = round(self._waiting_times_sum / n_completed_journey, 2)
        if self.n_vehicles_on_map:
            total_on_map_wait_time = sum(
                vehicle.get_wait_time(self.t) for i in self.non_empty_roads
                for vehicle in self.roads[i].vehicles
            )
            on_map_wait_time = total_on_map_wait_time / self.n_vehicles_on_map
        return completed_wait_time + on_map_wait_time

    @property
    def inbound_roads(self) -> Set[int]:
        return self._inbound_roads

    @property
    def outbound_roads(self) -> Set[int]:
        return self._outbound_roads

    def init_gui(self) -> None:
        """Initializes the GUI and updates the display."""
        if not self._gui:
            self._gui = Window(self)
        self._gui.update()

    def run(self, action: Optional[int] = None) -> None:
        """
        Avanza la simulación un bloque fijo de tiempo (≈3 s).
        Si action es True/1, fuerza un salto inmediato de fase en todos los semáforos
        antes de simular (útil para el GA). El avance por tiempo sigue funcionando.
        """
        n = 180  # 3 s a dt=1/60

        # Si el GA pide "cambiar ya", saltamos una fase en cada señal.
        if action:
            for ts in self.traffic_signals:
                ts.update(None)   # dt=None = salto discreto de fase
            if self._gui:
                self._gui.update()

        self._loop(n)


    def update(self, dt: Optional[float] = None):
        """
        Updates signals, roads, generators, collisions and GUI for one tick.
        """
        dt_local = self.dt if dt is None else float(dt)

        # 1) Avanzar semáforos primero (afecta prioridades/velocidades de los vehículos)
        self._update_signals(dt_local)

        # 2) Actualizar carreteras/vehículos
        for i in list(self._non_empty_roads):
            self.roads[i].update(dt_local, self.t)

        # 3) Generar vehículos
        for gen in self.generators:
            if self.max_gen and self.n_vehicles_generated == self.max_gen:
                break
            road_index = gen.update(self.t, self.n_vehicles_generated)
            if road_index is not None:
                self.n_vehicles_generated += 1
                self.n_vehicles_on_map += 1
                self._non_empty_roads.add(road_index)

        # 4) Salidas de vía / traspasos
        self._check_out_of_bounds_vehicles()

        # 5) Colisiones
        self._detect_collisions()

        # 6) Tiempo
        self.t += dt_local

        # 7) GUI
        if self._gui:
            self._gui.update()

    def _loop(self, n: int) -> None:
        """Performs n simulation updates. Terminates early upon completion or GUI closing."""
        for _ in range(n):
            self.update()
            if self.completed or self.gui_closed:
                return

    def _update_signals(self, dt: float) -> None:
        """Updates all the simulation traffic signals."""
        for traffic_signal in self.traffic_signals:
            # IMPORTANT: TrafficSignal.update debe aceptar dt
            traffic_signal.update(dt)

    def _detect_collisions(self) -> None:
        """Detects collisions by checking all non-empty intersecting vehicle paths."""
        radius = 3
        for main_road, intersecting_roads in self.intersections.items():
            vehicles = self.roads[main_road].vehicles
            intersecting_vehicles = chain.from_iterable(
                self.roads[i].vehicles for i in intersecting_roads
            )
            for vehicle in vehicles:
                for intersecting in intersecting_vehicles:
                    if distance.euclidean(vehicle.position, intersecting.position) < radius:
                        self.collision_detected = True
                        return

    def _check_out_of_bounds_vehicles(self):
        """Check roads for out-of-bounds vehicles, updates self.non_empty_roads."""
        new_non_empty_roads = set()
        new_empty_roads = set()
        for i in list(self._non_empty_roads):
            road = self.roads[i]
            if not road.vehicles:
                new_empty_roads.add(road.index)
                continue

            lead = road.vehicles[0]
            # If first vehicle is out of road bounds
            if lead.x >= road.length:
                # If vehicle has a next road
                if lead.current_road_index + 1 < len(lead.path):
                    # Remove it from its road
                    road.vehicles.popleft()
                    # Reset the position relative to the road
                    lead.x = 0
                    # Add it to the next road
                    lead.current_road_index += 1
                    next_road_index = lead.path[lead.current_road_index]
                    new_non_empty_roads.add(next_road_index)
                    self.roads[next_road_index].vehicles.append(lead)
                    if not road.vehicles:
                        new_empty_roads.add(road.index)
                else:
                    # Journey completed
                    road.vehicles.popleft()
                    if not road.vehicles:
                        new_empty_roads.add(road.index)
                    self.n_vehicles_on_map -= 1
                    self._waiting_times_sum += lead.get_wait_time(self.t)

        self._non_empty_roads.difference_update(new_empty_roads)
        self._non_empty_roads.update(new_non_empty_roads)
