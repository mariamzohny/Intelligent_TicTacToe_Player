import os
import sys
import pygame
from ai_logic import TicTacToeAI, EMPTY

pygame.init()
pygame.font.init()

# -----------------------------
# Window / theme
# -----------------------------
W, H = 600, 750
FPS = 60
PINK = (235, 93, 170)
PINK2 = (247, 143, 202)
PINK_DARK = (185, 52, 132)
WHITE = (255, 255, 255)
BLACK = (42, 27, 39)

BASE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(BASE, "assets")
SOUNDS_DIR = os.path.join(ASSETS, "sounds")

SCREEN = pygame.display.set_mode((W, H))
pygame.display.set_caption("Intelligent Tic-Tac-Toe Player")
CLOCK = pygame.time.Clock()


def font(size, bold=False):
    for name in ["Trebuchet MS", "Arial Rounded MT Bold", "Verdana", "Arial"]:
        try:
            f = pygame.font.SysFont(name, size, bold=bold)
            if f:
                return f
        except Exception:
            pass
    return pygame.font.Font(None, size)


F_TITLE = font(34, True)
F_BIG = font(28, True)
F_MID = font(22, True)
F_SMALL = font(17, False)
F_TINY = font(14, False)


# -----------------------------
# Images
# -----------------------------
def load_bg(name):
    path = os.path.join(ASSETS, name)
    image = pygame.image.load(path).convert()
    # The prepared JPG files are already composed as 600x750 backgrounds.
    # Scaling them directly keeps every page visually consistent.
    return pygame.transform.smoothscale(image, (W, H))


HOME_BG = load_bg("home_bg.jpg")
GAME_BG = load_bg("game_bg.jpg")
RESULT_BG = load_bg("result_bg.jpg")
END_BG = load_bg("end_bg.jpg")


# -----------------------------
# Audio
# -----------------------------
AUDIO_OK = False
SOUNDS = {}
SOUND_ON = True

try:
    if not pygame.mixer.get_init():
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

    for key, filename in {
        "click": "click.wav",
        "move": "move.wav",
        "win": "win.wav",
        "lose": "lose.wav",
        "draw": "draw.wav",
    }.items():
        path = os.path.join(SOUNDS_DIR, filename)
        if os.path.exists(path):
            SOUNDS[key] = pygame.mixer.Sound(path)

    music_path = os.path.join(SOUNDS_DIR, "music.wav")
    if os.path.exists(music_path):
        pygame.mixer.music.load(music_path)
        pygame.mixer.music.set_volume(0.20)
        pygame.mixer.music.play(-1)

    for key, sound in SOUNDS.items():
        if key == "move":
            sound.set_volume(0.45)
        elif key == "click":
            sound.set_volume(0.35)
        else:
            sound.set_volume(0.60)

    AUDIO_OK = True
except pygame.error:
    AUDIO_OK = False


def play_sound(name):
    if AUDIO_OK and SOUND_ON and name in SOUNDS:
        SOUNDS[name].play()


def toggle_sound():
    global SOUND_ON
    SOUND_ON = not SOUND_ON
    if AUDIO_OK:
        pygame.mixer.music.set_volume(0.20 if SOUND_ON else 0.0)


# -----------------------------
# UI helpers
# -----------------------------
def center_text(text, fnt, color, y, shadow=False):
    surf = fnt.render(text, True, color)
    rect = surf.get_rect(center=(W // 2, y))
    if shadow:
        shadow_surf = fnt.render(text, True, (35, 15, 29))
        shadow_rect = shadow_surf.get_rect(center=(W // 2 + 2, y + 2))
        SCREEN.blit(shadow_surf, shadow_rect)
    SCREEN.blit(surf, rect)


def wrapped(text, fnt, color, rect, spacing=5, shadow=False):
    words = text.split()
    line = ""
    lines = []
    for word in words:
        test = (line + " " + word).strip()
        if fnt.size(test)[0] <= rect.width:
            line = test
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)

    y = rect.top
    for ln in lines:
        surf = fnt.render(ln, True, color)
        pos = surf.get_rect(center=(rect.centerx, y + surf.get_height() // 2))
        if shadow:
            sh = fnt.render(ln, True, (35, 15, 29))
            sh_pos = sh.get_rect(center=(rect.centerx + 2, y + surf.get_height() // 2 + 2))
            SCREEN.blit(sh, sh_pos)
        SCREEN.blit(surf, pos)
        y += surf.get_height() + spacing


class Button:
    def __init__(self, rect, text, action, small=False):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.action = action
        self.selected = False
        self.small = small

    def draw(self):
        hover = self.rect.collidepoint(pygame.mouse.get_pos())
        color = PINK_DARK if hover or self.selected else PINK2
        pygame.draw.rect(SCREEN, WHITE, self.rect.inflate(5, 5), border_radius=self.rect.height // 2)
        pygame.draw.rect(SCREEN, color, self.rect, border_radius=self.rect.height // 2)
        f = F_SMALL if self.small else F_MID
        text = f.render(self.text, True, WHITE)
        SCREEN.blit(text, text.get_rect(center=self.rect.center))

    def event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.rect.collidepoint(event.pos):
            play_sound("click")
            self.action()
            return True
        return False


class GameApp:
    def __init__(self):
        self.state = "SETUP"
        self.player_mark = "X"
        self.difficulty = "Hard"
        self.start_choice = "You"
        self.ai = TicTacToeAI()
        self.turn = self.ai.player if self.start_choice == "You" else self.ai.ai
        self.result = None
        self.ai_due = 0
        self.result_due = 0
        self.result_sound_played = False
        self.make_buttons()

    def make_buttons(self):
        self.home_buttons = []
        self.setup_buttons = [
            Button((75, 235, 210, 58), "Play as X", lambda: self.pick_mark("X")),
            Button((315, 235, 210, 58), "Play as O", lambda: self.pick_mark("O")),
            Button((54, 390, 150, 54), "Easy", lambda: self.pick_diff("Easy"), True),
            Button((225, 390, 150, 54), "Medium", lambda: self.pick_diff("Medium"), True),
            Button((396, 390, 150, 54), "Hard", lambda: self.pick_diff("Hard"), True),
            Button((92, 525, 195, 56), "You Start", lambda: self.pick_start("You"), True),
            Button((313, 525, 195, 56), "Opponent Starts", lambda: self.pick_start("Opponent"), True),
            Button((170, 640, 260, 60), "Start Game", self.start_game),
            Button((492, 18, 90, 40), "SOUND", toggle_sound, True),
        ]
        self.game_buttons = [
            Button((496, 18, 86, 38), "SOUND", toggle_sound, True),
        ]
        self.result_buttons = [
            Button((125, 565, 350, 58), "Play Again", self.to_setup),
            Button((380, 685, 180, 44), "End Game", self.to_end, True),
        ]
        self.end_buttons = [
            Button((145, 625, 310, 56), "Main Menu", self.to_setup),
            Button((425, 700, 150, 36), "Exit Game", self.exit_game, True),
        ]
        self.update_selected()

    def update_selected(self):
        for b in self.setup_buttons:
            b.selected = (
                b.text == f"Play as {self.player_mark}"
                or b.text == self.difficulty
                or (b.text == "You Start" and self.start_choice == "You")
                or (b.text == "Opponent Starts" and self.start_choice == "Opponent")
            )

    def to_home(self):
        self.to_setup()

    def to_setup(self):
        self.state = "SETUP"
        self.update_selected()

    def to_end(self):
        self.state = "END"

    def exit_game(self):
        pygame.quit()
        sys.exit()

    def pick_mark(self, mark):
        self.player_mark = mark
        self.update_selected()

    def pick_diff(self, difficulty):
        self.difficulty = difficulty
        self.update_selected()

    def pick_start(self, who):
        self.start_choice = who
        self.update_selected()

    def start_game(self):
        self.ai.reset(self.player_mark, self.difficulty)
        # Respect the explicit Who starts? choice regardless of X/O.
        # If Opponent starts, Opponent immediately owns the first turn.
        self.turn = self.ai.player if self.start_choice == "You" else self.ai.ai
        self.result = None
        self.result_due = 0
        self.result_sound_played = False
        self.state = "GAME"
        if self.turn == self.ai.ai:
            self.ai_due = pygame.time.get_ticks() + 500

    def result_text(self):
        if self.result == "Draw":
            return "It's a Draw!"
        if self.result == self.ai.player:
            return "You Win!"
        return "Opponent Wins!"

    def finish_if_needed(self):
        winner = self.ai.winner(self.ai.board)
        if not winner:
            return False

        self.result = winner
        # Stay on the gameplay page for five seconds first.
        self.result_due = pygame.time.get_ticks() + 5000

        if not self.result_sound_played:
            if winner == "Draw":
                play_sound("draw")
            elif winner == self.ai.player:
                play_sound("win")
            else:
                play_sound("lose")
            self.result_sound_played = True
        return True

    def ai_move(self):
        move = self.ai.choose_move()
        if move:
            r, c = move
            self.ai.board[r][c] = self.ai.ai
            play_sound("move")
        if not self.finish_if_needed():
            self.turn = self.ai.player

    def click_board(self, pos):
        bx, by, size = 105, 260, 390
        if self.result is not None:
            return
        if not (bx <= pos[0] < bx + size and by <= pos[1] < by + size):
            return
        if self.turn != self.ai.player:
            return

        cs = size // 3
        col = (pos[0] - bx) // cs
        row = (pos[1] - by) // cs
        if self.ai.board[row][col] == EMPTY:
            self.ai.board[row][col] = self.ai.player
            play_sound("move")
            if not self.finish_if_needed():
                self.turn = self.ai.ai
                self.ai_due = pygame.time.get_ticks() + 450

    def handle(self, event):
        if event.type == pygame.QUIT:
            self.exit_game()

        buttons = {
            "HOME": self.home_buttons,
            "SETUP": self.setup_buttons,
            "GAME": self.game_buttons,
            "RESULT": self.result_buttons,
            "END": self.end_buttons,
        }[self.state]

        for button in buttons:
            if button.event(event):
                return

        if self.state == "GAME" and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.click_board(event.pos)

    def update(self):
        now = pygame.time.get_ticks()

        if self.state == "GAME" and self.result is None and self.turn == self.ai.ai and now >= self.ai_due:
            self.ai_due = 10**12
            self.ai_move()

        # Five seconds after the result appears on the gameplay screen,
        # automatically open the Play Again page.
        if self.state == "GAME" and self.result is not None and self.result_due and now >= self.result_due:
            self.state = "RESULT"

    # -------------------------
    # Pages
    # -------------------------
    def draw_home(self):
        self.draw_setup()

    def draw_setup(self):
        # The selection screen is now the very first page shown to the user.
        SCREEN.blit(HOME_BG, (0, 0))
        shade = pygame.Surface((W, H), pygame.SRCALPHA)
        shade.fill((38, 10, 31, 90))
        SCREEN.blit(shade, (0, 0))

        center_text("Let's enjoy!", F_TITLE, WHITE, 105, shadow=True)
        center_text("Choose your mark:", F_BIG, WHITE, 175, shadow=True)
        center_text("Difficulty", F_BIG, WHITE, 345, shadow=True)
        center_text("Who starts?", F_BIG, WHITE, 485, shadow=True)

        for button in self.setup_buttons:
            button.draw()

    def draw_board(self):
        bx, by, size = 105, 260, 390
        cs = size // 3
        panel = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.rect(panel, (255, 245, 252, 172), panel.get_rect(), border_radius=26)
        SCREEN.blit(panel, (bx, by))

        for i in (1, 2):
            pygame.draw.line(SCREEN, WHITE, (bx + i * cs, by + 18), (bx + i * cs, by + size - 18), 7)
            pygame.draw.line(SCREEN, WHITE, (bx + 18, by + i * cs), (bx + size - 18, by + i * cs), 7)

        for r in range(3):
            for c in range(3):
                mark = self.ai.board[r][c]
                if not mark:
                    continue
                cx = bx + c * cs + cs // 2
                cy = by + r * cs + cs // 2
                if mark == "X":
                    d = 38
                    pygame.draw.line(SCREEN, PINK_DARK, (cx - d, cy - d), (cx + d, cy + d), 10)
                    pygame.draw.line(SCREEN, PINK_DARK, (cx + d, cy - d), (cx - d, cy + d), 10)
                else:
                    pygame.draw.circle(SCREEN, PINK_DARK, (cx, cy), 44, 10)

        pygame.draw.rect(SCREEN, WHITE, (bx, by, size, size), width=3, border_radius=26)

    def draw_game(self):
        SCREEN.blit(GAME_BG, (0, 0))
        top = pygame.Surface((W, 170), pygame.SRCALPHA)
        top.fill((54, 18, 46, 92))
        SCREEN.blit(top, (0, 0))

        center_text("Tic Tac Toe", F_TITLE, WHITE, 50)
        center_text(
            f"You: {self.ai.player}    Opponent: {self.ai.ai}    •    {self.difficulty}    •    {self.start_choice} starts",
            F_SMALL,
            WHITE,
            100,
        )

        if self.result is None:
            status = "Your turn" if self.turn == self.ai.player else "Opponent's turn..."
            center_text(status, F_MID, WHITE, 140)
        else:
            center_text(self.result_text(), F_TITLE, WHITE, 700, shadow=True)

        for button in self.game_buttons:
            button.draw()
        self.draw_board()

    def draw_result(self):
        # Keep the prepared zoomed-out result background exactly as before.
        SCREEN.blit(RESULT_BG, (0, 0))
        shade = pygame.Surface((W, H), pygame.SRCALPHA)
        shade.fill((35, 9, 29, 68))
        SCREEN.blit(shade, (0, 0))

        # Result wording uses Opponent everywhere, never "AI".
        center_text(self.result_text(), F_TITLE, WHITE, 485, shadow=True)
        for button in self.result_buttons:
            button.draw()

    def draw_end(self):
        SCREEN.blit(END_BG, (0, 0))
        shade = pygame.Surface((W, H), pygame.SRCALPHA)
        shade.fill((31, 8, 27, 64))
        SCREEN.blit(shade, (0, 0))
        center_text("Thanks for Playing!", F_TITLE, WHITE, 530, shadow=True)
        center_text("See you again soon!", F_MID, WHITE, 575, shadow=True)
        for button in self.end_buttons:
            button.draw()

    def draw(self):
        {
            "HOME": self.draw_home,
            "SETUP": self.draw_setup,
            "GAME": self.draw_game,
            "RESULT": self.draw_result,
            "END": self.draw_end,
        }[self.state]()


def main():
    app = GameApp()
    while True:
        CLOCK.tick(FPS)
        for event in pygame.event.get():
            app.handle(event)
        app.update()
        app.draw()
        pygame.display.flip()


if __name__ == "__main__":
    main()
