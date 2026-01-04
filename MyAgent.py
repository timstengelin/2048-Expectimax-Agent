from Game2048 import *


class Player(BasePlayer):
    def __init__(self, timeLimit):
        BasePlayer.__init__(self, timeLimit)

        self._nodeCount = 0
        self._parentCount = 0
        self._childCount = 0
        self._depthCount = 0
        self._count = 0

    def findMove(self, state):
        self._count += 1
        actions = self.moveOrder(state)
        bestMove = None
        depth = 1
        while self.timeRemaining():
            self._depthCount += 1
            self._parentCount += 1
            self._nodeCount += 1
            print('Search depth', depth)
            best = float('-inf')
            for a in actions:
                result = state.move(a)
                if not self.timeRemaining(): return
                v = self.chance(result, depth - 1)
                if v is None: return
                if v > best:
                    best = v
                    bestMove = a

            self.setMove(bestMove)
            print('\tBest value', best, bestMove)

            depth += 1

    def maxPlayer(self, state, depth):
        # The max player gets to choose the move
        self._nodeCount += 1
        self._childCount += 1

        if state.gameOver():
            return state.getScore()

        actions = self.moveOrder(state)

        if depth == 0:
            return self.heuristic(state)

        self._parentCount += 1
        best = float('-inf')
        for a in actions:
            if not self.timeRemaining(): return None
            result = state.move(a)
            v = self.chance(result, depth - 1)
            if v is None: return None
            if v > best:
                best = v

        return best

    def chance(self, state, depth):
        self._nodeCount += 1
        self._childCount += 1

        if state.gameOver():
            return state.getScore()

        if depth == 0:
            return self.heuristic(state)

        possibleTiles = state.possibleTiles()
        totalValue = 0
        for (tile_pos, tile_value) in possibleTiles:
            if not self.timeRemaining():
                return None
            result = state.addTile(tile_pos, tile_value)
            if tile_value == 1:
                probability = 0.9
            else:
                probability = 0.1
            value = self.maxPlayer(result, depth - 1)
            if value is None:
                return None
            totalValue += probability * value

        if possibleTiles:
            return totalValue / len(possibleTiles)
        else:
            self.heuristic(state)

    def heuristic(self, state):

        # ----- Constants -----
        BOARD_SIZE = 4
        CORNER_INDICES = (0, 3, 12, 15)
        SNAKE_WEIGHTS \
            = (2048, 1024, 512, 256, 64, 32, 16, 8, 4, 2, 1, 1, 1, 1, 1, 1)

        # ----- Tunable Component Weights -----
        CORNER_BONUS = 10000
        CORNER_PENALTY = -5000
        EMPTY_WEIGHT = 1000
        MONOTONICITY_WEIGHT = 3000
        MERGE_WEIGHT = 2000
        SMOOTHNESS_SCALE = 500

        # ----- Current State -----
        base_game_score = state.getScore()
        tiles = list(state.getBoard())
        max_tile_exponent = max(tiles) if tiles else 0

        # ----- Local Helper Functions -----
        def corner_score() -> float:
            if max_tile_exponent == 0:
                return CORNER_PENALTY
            return CORNER_BONUS if any(tiles[i] == max_tile_exponent for i in
                                       CORNER_INDICES) else CORNER_PENALTY

        def empty_tile_score() -> float:
            return tiles.count(0) * EMPTY_WEIGHT

        def snake_pattern_score() -> float:
            if max_tile_exponent == 0:
                return 0.0
            weighted_sum = sum(
                (2 ** exp) * w for exp, w in zip(tiles, SNAKE_WEIGHTS) if
                exp > 0
            )
            return weighted_sum / float(max_tile_exponent)

        def is_monotonic(seq) -> bool:
            if not seq:
                return True
            non_decr = all(a <= b for a, b in zip(seq, seq[1:]))
            non_incr = all(a >= b for a, b in zip(seq, seq[1:]))
            return non_decr or non_incr

        def monotonicity_score() -> float:
            count = 0
            for i in range(BOARD_SIZE):
                row = tiles[i * BOARD_SIZE: (i + 1) * BOARD_SIZE]
                col = tiles[i:: BOARD_SIZE]
                count += int(is_monotonic(row))
                count += int(is_monotonic(col))
            return MONOTONICITY_WEIGHT * count

        def merge_score() -> float:
            merges = 0
            # horizontal merges
            for r in range(BOARD_SIZE):
                base = r * BOARD_SIZE
                for c in range(BOARD_SIZE - 1):
                    a = tiles[base + c]
                    b = tiles[base + c + 1]
                    if a != 0 and a == b:
                        merges += 1
            # vertical merges
            for c in range(BOARD_SIZE):
                for r in range(BOARD_SIZE - 1):
                    a = tiles[r * BOARD_SIZE + c]
                    b = tiles[(r + 1) * BOARD_SIZE + c]
                    if a != 0 and a == b:
                        merges += 1
            return merges * MERGE_WEIGHT

        def smoothness_score() -> float:
            penalty = 0
            # horizontal differences
            for r in range(BOARD_SIZE):
                base = r * BOARD_SIZE
                for c in range(BOARD_SIZE - 1):
                    a = tiles[base + c]
                    b = tiles[base + c + 1]
                    if a and b:
                        penalty -= abs(a - b)
            # vertical differences
            for c in range(BOARD_SIZE):
                for r in range(BOARD_SIZE - 1):
                    a = tiles[r * BOARD_SIZE + c]
                    b = tiles[(r + 1) * BOARD_SIZE + c]
                    if a and b:
                        penalty -= abs(a - b)
            return penalty * SMOOTHNESS_SCALE

        # ----- Compose Total Score -----
        total_score = (
                base_game_score
                + corner_score()
                + empty_tile_score()
                + snake_pattern_score()
                + monotonicity_score()
                + merge_score()
                + smoothness_score()
        )

        return total_score

    def moveOrder(self, state):
        return state.actions()

    def stats(self):
        print(f'Average depth: {self._depthCount / self._count:.2f}')
        print(f'Branching factor: {self._childCount / self._parentCount:.2f}')
