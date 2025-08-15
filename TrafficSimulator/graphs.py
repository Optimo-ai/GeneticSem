#!/usr/bin/env python3
"""
Traffic graph builders for different scenarios.
Each builder creates a unique geometry with distinct coordinates and topology.
"""
from TrafficSimulator.simulation import Simulation


def graph1_four_way():
    """4-way intersection con conectores internos y rutas planas"""
    def build(config=None, render=False):
        sim = Simulation()

        a, b, length = 2, 12, 60  # separaciones de carril y longitud de brazos

        # Puntos cerca de la intersección (dos carriles por eje)
        WEST_RIGHT_START = (-b - length,  a); WEST_RIGHT = (-b,  a)   # entra desde O
        WEST_LEFT_START  = (-b - length, -a); WEST_LEFT  = (-b, -a)   # sale hacia O

        EAST_RIGHT_START = ( b + length, -a); EAST_RIGHT = ( b, -a)   # entra desde E
        EAST_LEFT_START  = ( b + length,  a); EAST_LEFT  = ( b,  a)   # sale hacia E

        NORTH_RIGHT_START = (-a, -b - length); NORTH_RIGHT = (-a, -b) # entra desde N
        NORTH_LEFT_START  = ( a, -b - length); NORTH_LEFT  = ( a, -b) # sale hacia N

        SOUTH_RIGHT_START = ( a,  b + length); SOUTH_RIGHT = ( a,  b) # entra desde S
        SOUTH_LEFT_START  = (-a,  b + length); SOUTH_LEFT  = (-a,  b) # sale hacia S

        # 0–7: entradas/salidas; 8–19: conectores internos
        ROADS = [
            (WEST_RIGHT_START, WEST_RIGHT),     # 0  W in
            (EAST_RIGHT_START, EAST_RIGHT),     # 1  E in
            (NORTH_RIGHT_START, NORTH_RIGHT),   # 2  N in
            (SOUTH_RIGHT_START, SOUTH_RIGHT),   # 3  S in

            (WEST_LEFT, WEST_LEFT_START),       # 4  W out
            (EAST_LEFT, EAST_LEFT_START),       # 5  E out
            (NORTH_LEFT, NORTH_LEFT_START),     # 6  N out
            (SOUTH_LEFT, SOUTH_LEFT_START),     # 7  S out

            # Conectores “rectos”
            (WEST_RIGHT,  EAST_LEFT),           # 8  W→E
            (EAST_RIGHT,  WEST_LEFT),           # 9  E→W
            (NORTH_RIGHT, SOUTH_LEFT),          # 10 N→S
            (SOUTH_RIGHT, NORTH_LEFT),          # 11 S→N

            # Giros
            (WEST_RIGHT,  NORTH_LEFT),          # 12 W→N
            (WEST_RIGHT,  SOUTH_LEFT),          # 13 W→S
            (EAST_RIGHT,  NORTH_LEFT),          # 14 E→N
            (EAST_RIGHT,  SOUTH_LEFT),          # 15 E→S
            (NORTH_RIGHT, EAST_LEFT),           # 16 N→E
            (NORTH_RIGHT, WEST_LEFT),           # 17 N→W
            (SOUTH_RIGHT, EAST_LEFT),           # 18 S→E
            (SOUTH_RIGHT, WEST_LEFT),           # 19 S→W
        ]
        sim.add_roads(ROADS)

        # Intersecciones (conflictos centro)
        INTERSECTIONS = {
            8: {10,11,12,13,14,15,16,17,18,19},
            9: {10,11,12,13,14,15,16,17,18,19},
            10:{8,9,12,13,14,15,16,17,18,19},
            11:{8,9,12,13,14,15,16,17,18,19},
            12:{8,9,10,11,15,18}, 13:{8,9,10,11,14,16},
            14:{8,9,10,11,13,17}, 15:{8,9,10,11,12,19},
            16:{8,9,10,11,13,19}, 17:{8,9,10,11,12,18},
            18:{8,9,10,11,12,17}, 19:{8,9,10,11,14,16},
        }
        sim.add_intersections(INTERSECTIONS)

        # Grupos de semáforo (uno por dirección de entrada → 4 fases)
        SIGNAL_ROADS = [[0], [1], [2], [3]]
        phases = (config[:4] if isinstance(config, list) and len(config) >= 4 else [10, 10, 10, 10])
        sim.add_traffic_signal(SIGNAL_ROADS, phases, 120, 0.4, 20)

        # Rutas planas (peso, [r0, r1, ...])
        PATHS = [
            (3, [0,  8, 5]),   # W→E
            (2, [0, 12, 6]),   # W→N
            (2, [0, 13, 7]),   # W→S

            (3, [1,  9, 4]),   # E→W
            (2, [1, 14, 6]),   # E→N
            (2, [1, 15, 7]),   # E→S

            (3, [2, 10, 7]),   # N→S
            (2, [2, 16, 5]),   # N→E
            (2, [2, 17, 4]),   # N→W

            (3, [3, 11, 6]),   # S→N
            (2, [3, 18, 5]),   # S→E
            (2, [3, 19, 4]),   # S→W
        ]
        # MÁS AUTOS
        sim.add_generator(25, PATHS)

        sim.scenario_name = "4-way"
        sim.num_nodes = 1
        sim.num_roads = len(ROADS)
        return sim

    build.phases_per_signal = [4]
    return build


def graph2_t_junction():
    """T-junction (sin brazo Este) con conectores internos y rutas planas"""
    def build(config=None, render=False):
        sim = Simulation()

        a, b, length = 2, 12, 60

        WEST_RIGHT_START = (-b - length,  a); WEST_RIGHT = (-b,  a)
        WEST_LEFT_START  = (-b - length, -a); WEST_LEFT  = (-b, -a)
        SOUTH_RIGHT_START = ( a,  b + length); SOUTH_RIGHT = ( a,  b)
        SOUTH_LEFT_START  = (-a,  b + length); SOUTH_LEFT  = (-a,  b)
        EAST_RIGHT_START  = ( b + length, -a); EAST_RIGHT = ( b, -a)
        EAST_LEFT_START   = ( b + length,  a); EAST_LEFT  = ( b,  a)

        ROADS = [
            (WEST_RIGHT_START, WEST_RIGHT),   # 0  W in
            (SOUTH_RIGHT_START, SOUTH_RIGHT), # 1  S in
            (EAST_RIGHT_START, EAST_RIGHT),   # 2  E in

            (WEST_LEFT, WEST_LEFT_START),     # 3  W out
            (SOUTH_LEFT, SOUTH_LEFT_START),   # 4  S out
            (EAST_LEFT, EAST_LEFT_START),     # 5  E out

            (WEST_RIGHT, EAST_LEFT),          # 6  W→E
            (EAST_RIGHT, WEST_LEFT),          # 7  E→W
            (SOUTH_RIGHT, WEST_LEFT),         # 8  S→W
            (SOUTH_RIGHT, EAST_LEFT),         # 9  S→E
        ]
        sim.add_roads(ROADS)

        INTERSECTIONS = {6: {8, 9}, 7: {8, 9}, 8: {6, 7}, 9: {6, 7}}
        sim.add_intersections(INTERSECTIONS)

        # 2 grupos: (W/E) y (S). 4 fases con all-red entre verdes
        SIGNAL_ROADS = [[0, 2], [1]]
        phases = (config[:4] if isinstance(config, list) and len(config) >= 4 else [10, 10, 10, 10])
        sim.add_traffic_signal(SIGNAL_ROADS, phases, 120, 0.4, 20)

        PATHS = [
            (3, [0, 6, 5]),  # W→E
            (3, [2, 7, 3]),  # E→W
            (2, [1, 8, 3]),  # S→W
            (2, [1, 9, 5]),  # S→E
        ]
        # MÁS AUTOS
        sim.add_generator(20, PATHS)

        sim.scenario_name = "T-junction"
        sim.num_nodes = 1
        sim.num_roads = len(ROADS)
        return sim

    build.phases_per_signal = [3]
    return build


def graph3_corridor_two_intersections():
    """Corridor with 2 intersections in line"""
    def build(config=None, render=False):
        sim = Simulation()

        ax, ay = 420, 360
        bx, by = 860, 360
        L = 300

        roads = [
            ((ax, ay - L), (ax, ay)),      # 0:  N -> A (in)
            ((ax, ay), (ax, ay - L)),      # 1:  A -> N (out)
            ((ax, ay + L), (ax, ay)),      # 2:  S -> A (in)
            ((ax, ay), (ax, ay + L)),      # 3:  A -> S (out)
            ((ax - L, ay), (ax, ay)),      # 4:  W -> A (in)
            ((ax, ay), (ax - L, ay)),      # 5:  A -> W (out)
            ((ax, ay), (bx, by)),          # 6:  A -> B (outbound from A)
            ((bx, by), (ax, ay)),          # 7:  B -> A (in to A)
            ((bx, by - L), (bx, by)),      # 8:  N -> B (in)
            ((bx, by), (bx, by - L)),      # 9:  B -> N (out)
            ((bx, by + L), (bx, by)),      # 10: S -> B (in)
            ((bx, by), (bx, by + L)),      # 11: B -> S (out)
            ((bx + L, by), (bx, by)),      # 12: E -> B (in)
            ((bx, by), (bx + L, by)),      # 13: B -> E (out)
        ]
        sim.add_roads(roads)

        sim.add_intersections({
            0: {2, 4, 6}, 1: {3, 5, 7}, 2: {0, 4, 6}, 3: {1, 5, 7},
            4: {0, 2, 6}, 5: {1, 3, 7}, 6: {0, 2, 4, 8, 10, 12}, 7: {1, 3, 5, 9, 11, 13},
            8: {6, 10, 12}, 9: {7, 11, 13}, 10: {6, 8, 12}, 11: {7, 9, 13},
            12: {6, 8, 10}, 13: {7, 9, 11}
        })

        # Señal en A: inbound a A = 0 (N), 2 (S), 4 (W), 7 (desde B)
        SIGNAL_ROADS_A = [[0], [2], [4], [7]]
        phases_a = (config[:4] if isinstance(config, list) and len(config) >= 4 else [10, 10, 10, 10])
        sim.add_traffic_signal(SIGNAL_ROADS_A, phases_a, 50, 0.4, 15)

        # Señal en B: inbound a B = 8 (N), 10 (S), 12 (E), 6 (desde A)
        SIGNAL_ROADS_B = [[8], [10], [12], [6]]
        phases_b = (config[4:8] if isinstance(config, list) and len(config) >= 8 else [10, 10, 10, 10])
        sim.add_traffic_signal(SIGNAL_ROADS_B, phases_b, 50, 0.4, 15)

        # Generadores (MÁS AUTOS)
        sim.add_generator(0.90, [
            (1, [[0, 3, 7, 9], [0, 3, 7, 11], [0, 3, 7, 13]]),
            (1, [[2, 1, 7, 9], [2, 1, 7, 11], [2, 1, 7, 13]]),
            (1, [[4, 1, 7, 9], [4, 1, 7, 11], [4, 1, 7, 13]]),
            (1, [[8, 11], [8, 13], [8, 6, 1], [8, 6, 3], [8, 6, 5]]),
            (1, [[10, 9], [10, 13], [10, 6, 1], [10, 6, 3], [10, 6, 5]]),
            (1, [[12, 9], [12, 11], [12, 6, 1], [12, 6, 3], [12, 6, 5]]),
        ])

        sim.scenario_name = "Corridor(2)"
        sim.num_nodes = 2
        sim.num_roads = 14
        return sim

    build.phases_per_signal = [4, 4]
    return build


def graph4_grid_2x2():
    """Grid 2x2 - 4 nodes"""
    def build(config=None, render=False):
        sim = Simulation()

        tl_x, tl_y = 420, 260
        tr_x, tr_y = 860, 260
        bl_x, bl_y = 420, 460
        br_x, br_y = 860, 460
        L = 200

        roads = [
            # TL external
            ((tl_x, tl_y - L), (tl_x, tl_y)),      # 0  N->TL (in)
            ((tl_x, tl_y), (tl_x, tl_y - L)),      # 1  out
            ((tl_x - L, tl_y), (tl_x, tl_y)),      # 2  W->TL (in)
            ((tl_x, tl_y), (tl_x - L, tl_y)),      # 3  out

            # TR external
            ((tr_x, tr_y - L), (tr_x, tr_y)),      # 4  N->TR (in)
            ((tr_x, tr_y), (tr_x, tr_y - L)),      # 5  out
            ((tr_x + L, tr_y), (tr_x, tr_y)),      # 6  E->TR (in)
            ((tr_x, tr_y), (tr_x + L, tr_y)),      # 7  out

            # BL external
            ((bl_x, bl_y + L), (bl_x, bl_y)),      # 8  S->BL (in)
            ((bl_x, bl_y), (bl_x, bl_y + L)),      # 9  out
            ((bl_x - L, bl_y), (bl_x, bl_y)),      # 10 W->BL (in)
            ((bl_x, bl_y), (bl_x - L, bl_y)),      # 11 out

            # BR external
            ((br_x, br_y + L), (br_x, br_y)),      # 12 S->BR (in)
            ((br_x, br_y), (br_x, br_y + L)),      # 13 out
            ((br_x + L, br_y), (br_x, br_y)),      # 14 E->BR (in)
            ((br_x, br_y), (br_x + L, br_y)),      # 15 out

            # Internal connections
            ((tl_x, tl_y), (tr_x, tr_y)),          # 16 TL->TR (out)
            ((tr_x, tr_y), (tl_x, tl_y)),          # 17 TR->TL (in to TL)
            ((tl_x, tl_y), (bl_x, bl_y)),          # 18 TL->BL (out)
            ((bl_x, bl_y), (tl_x, tl_y)),          # 19 BL->TL (in to TL)
            ((tr_x, tr_y), (br_x, br_y)),          # 20 TR->BR (in to BR)
            ((br_x, br_y), (tr_x, tr_y)),          # 21 BR->TR (in to TR)
            ((bl_x, bl_y), (br_x, br_y)),          # 22 BL->BR (in to BR)
            ((br_x, br_y), (bl_x, bl_y)),          # 23 BR->BL (in to BL)
        ]
        sim.add_roads(roads)

        sim.add_intersections({
            # TL
            0: {2, 17, 19}, 1: {3, 16, 18}, 2: {0, 17, 19}, 3: {1, 16, 18},
            16: {1,3,20,22}, 17: {0,2,21,23}, 18: {1,3,20,22}, 19: {0,2,21,23},
            # TR
            4: {6, 16, 21}, 5: {7, 17, 20}, 6: {4, 16, 21}, 7: {5, 17, 20},
            20: {5,7,12,22}, 21: {4,6,13,23},
            # BL
            8: {10, 19, 23}, 9: {11, 18, 22}, 10: {8, 19, 23}, 11: {9, 18, 22},
            22: {9,11,13,20}, 23: {8,10,12,21},
            # BR
            12: {14, 20, 22}, 13: {15, 21, 23}, 14: {12, 20, 22}, 15: {13, 21, 23}
        })

        # Señales por nodo (inbound groups)
        SIGNAL_TL = [[0], [2], [17], [19]]
        SIGNAL_TR = [[4], [6], [16], [21]]
        SIGNAL_BL = [[8], [10], [19], [23]]
        SIGNAL_BR = [[12], [14], [20], [22]]

        phases = (config if isinstance(config, list) else [])
        phases_tl = phases[0:4] if len(phases) >= 4 else [10,10,10,10]
        phases_tr = phases[4:8] if len(phases) >= 8 else [10,10,10,10]
        phases_bl = phases[8:12] if len(phases) >= 12 else [10,10,10,10]
        phases_br = phases[12:16] if len(phases) >= 16 else [10,10,10,10]

        sim.add_traffic_signal(SIGNAL_TL, phases_tl, 50, 0.4, 15)
        sim.add_traffic_signal(SIGNAL_TR, phases_tr, 50, 0.4, 15)
        sim.add_traffic_signal(SIGNAL_BL, phases_bl, 50, 0.4, 15)
        sim.add_traffic_signal(SIGNAL_BR, phases_br, 50, 0.4, 15)

        # Generadores (MÁS AUTOS)
        sim.add_generator(0.80, [
            (1, [[0, 1, 17, 5], [0, 1, 17, 7], [0, 1, 17, 16, 21, 13], [0, 1, 17, 16, 21, 15]]),
            (1, [[4, 5, 16, 1], [4, 5, 16, 3], [4, 5, 16, 17, 19, 9], [4, 5, 16, 17, 19, 11]]),
            (1, [[2, 3, 19, 9], [2, 3, 19, 11], [2, 3, 19, 18, 23, 13], [2, 3, 19, 18, 23, 15]]),
            (1, [[6, 7, 21, 13], [6, 7, 21, 15], [6, 7, 21, 20, 22, 9], [6, 7, 21, 20, 22, 11]]),
            (1, [[10, 11, 18, 1], [10, 11, 18, 3], [10, 11, 18, 19, 17, 5], [10, 11, 18, 19, 17, 7]]),
            (1, [[8, 9, 23, 13], [8, 9, 23, 15], [8, 9, 23, 20, 16, 1], [8, 9, 23, 20, 16, 3]]),
            (1, [[12, 13, 22, 9], [12, 13, 22, 11], [12, 13, 22, 18, 17, 5], [12, 13, 22, 18, 17, 7]]),
            (1, [[14, 15, 20, 1], [14, 15, 20, 3], [14, 15, 20, 16, 19, 9], [14, 15, 20, 16, 19, 11]]),
        ])

        sim.scenario_name = "Grid2x2"
        sim.num_nodes = 4
        sim.num_roads = 24
        return sim

    build.phases_per_signal = [4, 4, 4, 4]
    return build


def graph5_arterial_three():
    """Arterial with 3 intersections"""
    def build(config=None, render=False):
        sim = Simulation()

        tx, ty = 640, 180
        mx, my = 640, 360
        bx, by = 640, 540
        S = 250  # side length

        roads = [
            # Top
            ((tx, ty - 200), (tx, ty)),         # 0  N->Top (in)
            ((tx, ty), (tx, ty - 200)),         # 1  out
            ((tx + S, ty), (tx, ty)),           # 2  E->Top (in)
            ((tx, ty), (tx + S, ty)),           # 3  out

            # Middle
            ((mx + S, my), (mx, my)),           # 4  E->Mid (in)
            ((mx, my), (mx + S, my)),           # 5  out
            ((mx - S, my), (mx, my)),           # 6  W->Mid (in)
            ((mx, my), (mx - S, my)),           # 7  out

            # Bottom
            ((bx, by + 200), (bx, by)),         # 8  S->Bot (in)
            ((bx, by), (bx, by + 200)),         # 9  out
            ((bx + S, by), (bx, by)),           # 10 E->Bot (in)
            ((bx, by), (bx + S, by)),           # 11 out

            # Arterial connections
            ((tx, ty), (mx, my)),               # 12 Top->Mid (out)
            ((mx, my), (tx, ty)),               # 13 Mid->Top (in to Top)
            ((mx, my), (bx, by)),               # 14 Mid->Bot (out to Bot)
            ((bx, by), (mx, my)),               # 15 Bot->Mid (in to Mid)
        ]
        sim.add_roads(roads)

        sim.add_intersections({
            0: {2, 13}, 1: {3, 12}, 2: {0, 13}, 3: {1, 12},
            12: {1,3,4,6,14}, 13: {0,2,5,7,15},
            4: {6,13,14}, 5: {7,12,15}, 6: {4,12,14}, 7: {5,13,15},
            14: {4,6,12,8,10}, 15: {5,7,13,9,11},
            8: {10,15}, 9: {11,14}, 10: {8,15}, 11: {9,14}
        })

        phases = (config if isinstance(config, list) else [])
        # Top node inbound groups: 0 (N), 2 (E), 13 (Mid->Top)
        SIGNAL_TOP = [[0], [2], [13]]
        phases_top = phases[0:3] if len(phases) >= 3 else [10, 10, 10]
        sim.add_traffic_signal(SIGNAL_TOP, phases_top, 50, 0.4, 15)

        # Mid node inbound groups: 4 (E), 6 (W), 12 (Top->Mid), 15 (Bot->Mid)
        SIGNAL_MID = [[4], [6], [12], [15]]
        phases_mid = phases[3:7] if len(phases) >= 7 else [10, 10, 10, 10]
        sim.add_traffic_signal(SIGNAL_MID, phases_mid, 50, 0.4, 15)

        # Bottom node inbound groups: 8 (S), 10 (E), 14 (Mid->Bot)
        SIGNAL_BOT = [[8], [10], [14]]
        phases_bot = phases[7:10] if len(phases) >= 10 else [10, 10, 10]
        sim.add_traffic_signal(SIGNAL_BOT, phases_bot, 50, 0.4, 15)

        # Generadores (MÁS AUTOS)
        sim.add_generator(0.90, [
            (1, [[0, 1, 13, 5], [0, 1, 13, 7], [0, 1, 13, 15, 9], [0, 1, 13, 15, 11]]),
            (1, [[2, 3, 12, 5], [2, 3, 12, 7], [2, 3, 12, 15, 9], [2, 3, 12, 15, 11]]),
            (1, [[4, 5, 15, 9], [4, 5, 15, 11], [4, 5, 12, 1], [4, 5, 12, 3]]),
            (1, [[6, 7, 12, 1], [6, 7, 12, 3], [6, 7, 15, 9], [6, 7, 15, 11]]),
            (1, [[8, 9, 14, 5], [8, 9, 14, 7], [8, 9, 14, 12, 1], [8, 9, 14, 12, 3]]),
            (1, [[10, 11, 14, 5], [10, 11, 14, 7], [10, 11, 14, 12, 1], [10, 11, 14, 12, 3]]),
        ])

        sim.scenario_name = "Arterial(3)"
        sim.num_nodes = 3
        sim.num_roads = 16
        return sim

    build.phases_per_signal = [3, 4, 3]
    return build
