from typing import List, Tuple, Optional, Union
import math

Number = Union[int, float]
BoolMask = Tuple[bool, ...]


class TrafficSignal:
    """
    Flexible traffic signal:
    - roads: admite lista de ints (IDs) o lista de listas (grupos) con ints u objetos Road.
      Se normaliza internamente a lista-de-listas.
    - cycle:
        * lista de duraciones por fase: [10, 12, 8, ...]  (secuencial, 1 grupo verde por fase)
        * ó lista de máscaras booleanas por fase: [(True, False, ...), ...]
    - update(dt):
        * con dt: respeta duraciones (si hay); si no, avanza 1 fase cuando se llame.
        * sin dt: avanza 1 fase por llamada.
    """

    def __init__(
        self,
        roads: List,
        cycle: List[Union[Number, BoolMask, List[bool]]],
        slow_distance: float,
        slow_factor: float,
        stop_distance: float,
    ):
        # --- Normalizar roads a lista-de-listas ---
        # Ejemplos válidos de entrada:
        #   [0,2,4]           -> [[0],[2],[4]]
        #   [[0],[2,6],[4]]   -> tal cual
        #   [[roadA],[roadB]] -> tal cual (objetos Road)
        self.roads: List[List] = self._normalize_roads(roads)

        self.slow_distance: float = float(slow_distance)
        self.slow_factor: float = float(slow_factor)
        self.stop_distance: float = float(stop_distance)

        # --- Preparar ciclo ---
        # Si 'cycle' es lista de números -> duraciones por fase (una por grupo)
        # Si 'cycle' es lista de bools/tuplas -> máscaras por fase
        self._num_groups: int = len(self.roads)
        self._durations: Optional[List[float]] = None
        self._mask_cycle: List[BoolMask] = []

        self._parse_cycle(cycle)

        # Estado de fase
        self.current_cycle_index: int = 0
        self._time_in_phase: float = 0.0
        self.prev_update_time: float = 0.0

        # Intentar registrar la señal en cada road si son objetos con .set_traffic_signal
        for gi, group in enumerate(self.roads):
            for road in group:
                # Si es un objeto Road, tendrá este método; si es int (ID), lo ignora.
                if hasattr(road, "set_traffic_signal"):
                    try:
                        road.set_traffic_signal(self, gi)
                    except Exception:
                        # Si el motor lo hace más tarde (p.ej. Simulation.add_traffic_signal),
                        # simplemente lo omitimos aquí.
                        pass

    # -------------------- Helpers --------------------

    def _normalize_roads(self, roads_in: List) -> List[List]:
        if not isinstance(roads_in, list):
            raise TypeError("roads must be a list or list-of-lists")

        # Lista plana de ints/roads -> envolver cada uno
        if all(not isinstance(r, list) for r in roads_in):
            return [[r] for r in roads_in]

        # Ya es lista-de-listas: asegurar que cada grupo sea lista
        groups: List[List] = []
        for grp in roads_in:
            groups.append(list(grp) if isinstance(grp, (list, tuple)) else [grp])
        return groups

    def _parse_cycle(self, cycle: List[Union[Number, BoolMask, List[bool]]]) -> None:
        if not isinstance(cycle, list) or len(cycle) == 0:
            # Fallback: 1s por grupo en round-robin
            self._durations = [1.0 for _ in range(self._num_groups)]
            self._mask_cycle = [self._one_hot(i, self._num_groups) for i in range(self._num_groups)]
            return

        # ¿Es lista de números?
        if all(isinstance(c, (int, float)) for c in cycle):
            # Duraciones por fase (una por grupo), saneando NaN/inf/<=0
            durs: List[float] = []
            for x in cycle:
                try:
                    v = float(x)
                except Exception:
                    v = 3.0
                if not math.isfinite(v) or v <= 0.0:
                    v = 3.0  # valor por defecto seguro
                v = max(1.0, min(v, 60.0))
                durs.append(v)

            # Ajuste al número de grupos
            if len(durs) >= self._num_groups:
                durs = durs[: self._num_groups]
            else:
                durs += [durs[-1]] * (self._num_groups - len(durs))

            self._durations = durs
            # Máscara: una fase por grupo en orden
            self._mask_cycle = [self._one_hot(i, self._num_groups) for i in range(self._num_groups)]
            return

        # ¿Es lista de máscaras booleanas?
        masks: List[BoolMask] = []
        ok_masks = True
        for item in cycle:
            if isinstance(item, tuple):
                mask = item
            elif isinstance(item, list):
                mask = tuple(bool(x) for x in item)
            else:
                ok_masks = False
                break
            masks.append(mask)

        if ok_masks and all(len(m) == self._num_groups for m in masks):
            self._mask_cycle = masks
            self._durations = None  # sin tiempos (paso discreto por update())
            return

        # Fallback final: usar round-robin
        self._durations = [1.0 for _ in range(self._num_groups)]
        self._mask_cycle = [self._one_hot(i, self._num_groups) for i in range(self._num_groups)]

    @staticmethod
    def _one_hot(idx: int, n: int) -> BoolMask:
        return tuple(True if i == idx else False for i in range(n))

    # -------------------- API pública --------------------

    @property
    def current_cycle(self) -> BoolMask:
        """Devuelve la máscara booleana de la fase actual (True=grupo habilitado)."""
        return self._mask_cycle[self.current_cycle_index]

    def next_phase(self) -> None:
        self.current_cycle_index = (self.current_cycle_index + 1) % len(self._mask_cycle)
        self._time_in_phase = 0.0

    def update(self, dt: Optional[Number] = None) -> None:
        """
        Avanza el ciclo:
        - Si dt está definido y hay duraciones -> acumula y pasa de fase cuando toca.
        - Si dt está definido y NO hay duraciones -> avanza 1 fase cuando se llama.
        - Si dt es None -> avanza 1 fase discreta.
        """
        if dt is None:
            self.next_phase()
            return

        try:
            dtf = float(dt)
        except Exception:
            dtf = 0.0

        if dtf <= 0.0:
            # Nada de tiempo avanzado -> no hacemos cambio
            return

        if self._durations is None:
            # Sin tiempos definidos: tratamos cada llamada con dt como “salto” de fase
            self.next_phase()
            return

        # Con tiempos: avanzar según duración
        self._time_in_phase += dtf
        curr_dur = self._durations[self.current_cycle_index]
        if self._time_in_phase >= curr_dur:
            # Pasar de fase, arrastrando el exceso por si dt es grande
            self._time_in_phase -= curr_dur
            self.next_phase()
