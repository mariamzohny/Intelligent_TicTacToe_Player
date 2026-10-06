import math
import random

EMPTY = ""


class TicTacToeAI:
    def __init__(self):
        self.board = [[EMPTY for _ in range(3)] for _ in range(3)]
        self.player = "X"
        self.ai = "O"
        self.difficulty = "Hard"

    def reset(self, player="X", difficulty="Hard"):
        self.board = [[EMPTY for _ in range(3)] for _ in range(3)]
        self.player = player
        self.ai = "O" if player == "X" else "X"
        self.difficulty = difficulty

    @staticmethod
    def winner(board):
        lines = [
            board[0], board[1], board[2],
            [board[0][0], board[1][0], board[2][0]],
            [board[0][1], board[1][1], board[2][1]],
            [board[0][2], board[1][2], board[2][2]],
            [board[0][0], board[1][1], board[2][2]],
            [board[0][2], board[1][1], board[2][0]],
        ]
        for line in lines:
            if line[0] and line[0] == line[1] == line[2]:
                return line[0]
        if all(cell for row in board for cell in row):
            return "Draw"
        return None

    @staticmethod
    def moves(board):
        return [(r, c) for r in range(3) for c in range(3) if board[r][c] == EMPTY]

    def heuristic(self, board):
        score = 0
        lines = [
            board[0], board[1], board[2],
            [board[0][0], board[1][0], board[2][0]],
            [board[0][1], board[1][1], board[2][1]],
            [board[0][2], board[1][2], board[2][2]],
            [board[0][0], board[1][1], board[2][2]],
            [board[0][2], board[1][1], board[2][0]],
        ]
        for line in lines:
            a = line.count(self.ai)
            p = line.count(self.player)
            e = line.count(EMPTY)
            if a and p:
                continue
            if a == 2 and e == 1:
                score += 15
            elif a == 1 and e == 2:
                score += 4
            if p == 2 and e == 1:
                score -= 18
            elif p == 1 and e == 2:
                score -= 5
        if board[1][1] == self.ai:
            score += 5
        elif board[1][1] == self.player:
            score -= 5
        for r, c in ((0, 0), (0, 2), (2, 0), (2, 2)):
            if board[r][c] == self.ai:
                score += 2
            elif board[r][c] == self.player:
                score -= 2
        return score

    def minimax(self, board, depth, maximizing, alpha, beta, depth_limit=None):
        w = self.winner(board)
        if w == self.ai:
            return 100 - depth, None
        if w == self.player:
            return depth - 100, None
        if w == "Draw":
            return 0, None
        if depth_limit is not None and depth >= depth_limit:
            return self.heuristic(board), None

        best_move = None
        if maximizing:
            best = -math.inf
            for r, c in self.moves(board):
                board[r][c] = self.ai
                val, _ = self.minimax(board, depth + 1, False, alpha, beta, depth_limit)
                board[r][c] = EMPTY
                if val > best:
                    best, best_move = val, (r, c)
                alpha = max(alpha, best)
                if beta <= alpha:
                    break
            return best, best_move

        best = math.inf
        for r, c in self.moves(board):
            board[r][c] = self.player
            val, _ = self.minimax(board, depth + 1, True, alpha, beta, depth_limit)
            board[r][c] = EMPTY
            if val < best:
                best, best_move = val, (r, c)
            beta = min(beta, best)
            if beta <= alpha:
                break
        return best, best_move

    def tactical_win(self):
        for r, c in self.moves(self.board):
            self.board[r][c] = self.ai
            if self.winner(self.board) == self.ai:
                self.board[r][c] = EMPTY
                return r, c
            self.board[r][c] = EMPTY
        return None

    def tactical_block(self):
        for r, c in self.moves(self.board):
            self.board[r][c] = self.player
            if self.winner(self.board) == self.player:
                self.board[r][c] = EMPTY
                return r, c
            self.board[r][c] = EMPTY
        return None

    def easy_move(self, available):
        # Easy deliberately gives the player room to win:
        # avoid blocking a player's immediate win whenever another move exists,
        # and avoid completing Opponent's own line unless forced.
        block = self.tactical_block()
        win = self.tactical_win()
        candidates = available[:]

        if block in candidates and len(candidates) > 1:
            candidates.remove(block)
        if win in candidates and len(candidates) > 1:
            candidates.remove(win)

        # Prefer edges first (usually weaker than center/corners in tic-tac-toe).
        edges = [m for m in candidates if m in ((0, 1), (1, 0), (1, 2), (2, 1))]
        if edges:
            return random.choice(edges)
        return random.choice(candidates or available)

    def choose_move(self):
        available = self.moves(self.board)
        if not available:
            return None

        if self.difficulty == "Easy":
            return self.easy_move(available)

        if self.difficulty == "Medium":
            # Medium is tactical, but intentionally not perfect every turn.
            win = self.tactical_win()
            if win:
                return win
            block = self.tactical_block()
            if block and random.random() < 0.85:
                return block
            if random.random() < 0.75:
                _, move = self.minimax([r[:] for r in self.board], 0, True, -math.inf, math.inf, 3)
                if move:
                    return move
            return random.choice(available)

        # Hard: full-depth minimax + alpha-beta pruning. This is optimal play.
        # A perfect opponent can force a draw, so Opponent cannot mathematically
        # guarantee a win every game, but she will never intentionally make a losing move.
        _, move = self.minimax([r[:] for r in self.board], 0, True, -math.inf, math.inf, None)
        return move or random.choice(available)
