import pygame
import sys
import math
import random
import secrets
from pygame.locals import *

pygame.init()

# ── Display ────────────────────────────────────────────────────────────────────
SCREEN = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
DISPLAY_W, DISPLAY_H = SCREEN.get_size()
pygame.display.set_caption("Memory Puzzle")
CLOCK = pygame.time.Clock()
FPS = 60

# ── Colors ─────────────────────────────────────────────────────────────────────
BLACK       = (0,   0,   0)
WHITE       = (255, 255, 255)
CARD_BACK   = (72,  130, 90)
CARD_FRONT  = (255, 255, 255)
CARD_BORDER = (50,  100, 65)
HOVER_COL   = (100, 170, 115)
MATCH_GLOW  = (80,  230, 120)
HUD_BG      = (0,   0,   0,  120)   # RGBA
TIMER_GREEN = (60,  210, 100)
TIMER_YEL   = (230, 200,  50)
TIMER_RED   = (230,  70,  70)
STAR_GOLD   = (255, 200,  30)
STAR_EMPTY  = (160, 160, 160)

# ── Fonts ──────────────────────────────────────────────────────────────────────
TITLE_FONT = pygame.font.Font(None, 84)
SUB_FONT   = pygame.font.Font(None, 48)
UI_FONT    = pygame.font.Font(None, 34)
SMALL_FONT = pygame.font.Font(None, 26)

EMOJI_FONT_PATH = r"C:\Windows\Fonts\seguiemj.ttf"

# ── Themes & Levels ────────────────────────────────────────────────────────────
THEMES = {
    "Fruits":  ["🍎","🍌","🍇","🍉","🍒","🍍","🥝","🍑","🍋","🍐"],
    "Animals": ["🐶","🐱","🐼","🐵","🐸","🦊","🐯","🦁","🐰","🐷"],
    "Emoji":   ["😀","😁","😂","🤣","😊","😎","😍","🤩","🤖","👻"],
}
LEVELS = {
    "1 - EASY   (4x4)":   (4,  4,  60),
    "2 - MEDIUM (6x6)":   (6,  6,  50),
    "3 - HARD   (8x8)":   (8,  8,  40),
    "4 - EXTREME(10x10)": (10, 10, 35),
}

theme_keys   = list(THEMES.keys())
theme_index  = 0
current_theme = theme_keys[theme_index]

# ── Gradient background helper ─────────────────────────────────────────────────
_grad_cache: dict = {}

def draw_gradient(surface, top_col, bot_col):
    key = (top_col, bot_col, surface.get_width(), surface.get_height())
    if key not in _grad_cache:
        w, h = surface.get_width(), surface.get_height()
        grad = pygame.Surface((w, h))
        for y in range(h):
            t = y / h
            r = int(top_col[0] + (bot_col[0]-top_col[0])*t)
            g = int(top_col[1] + (bot_col[1]-top_col[1])*t)
            b = int(top_col[2] + (bot_col[2]-top_col[2])*t)
            pygame.draw.line(grad, (r,g,b), (0,y), (w,y))
        _grad_cache[key] = grad
    surface.blit(_grad_cache[key], (0,0))

GRAD_TOP = (25,  50,  35)
GRAD_BOT = (10,  25,  20)

# ── Utility ────────────────────────────────────────────────────────────────────
def draw_center(text, y, font, color=WHITE, surface=None):
    if surface is None:
        surface = SCREEN
    surf = font.render(text, True, color)
    rect = surf.get_rect(center=(DISPLAY_W//2, y))
    surface.blit(surf, rect)

def fade_in(top=(0,0,0), speed=15, delay=8):
    s = pygame.Surface((DISPLAY_W, DISPLAY_H))
    s.fill(top)
    for a in range(255, -1, -speed):
        draw_gradient(SCREEN, GRAD_TOP, GRAD_BOT)
        s.set_alpha(a)
        SCREEN.blit(s, (0,0))
        pygame.display.flip()
        pygame.time.delay(delay)

emoji_cache: dict = {}

def safe_emoji_render(emoji, size, cache=emoji_cache):
    key = (emoji, int(size))
    if key in cache:
        return cache[key]
    try:
        f = pygame.font.Font(EMOJI_FONT_PATH, int(size))
    except Exception:
        f = pygame.font.Font(None, int(size))
    s = f.render(emoji, True, BLACK)
    cache[key] = s
    return s

# ── Rounded-rect helper ────────────────────────────────────────────────────────
def draw_rounded_rect(surface, rect, color, radius=10, alpha=255):
    if alpha < 255:
        tmp = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        pygame.draw.rect(tmp, (*color, alpha), tmp.get_rect(), border_radius=radius)
        surface.blit(tmp, rect.topleft)
    else:
        pygame.draw.rect(surface, color, rect, border_radius=radius)

# ── Card shadow + back pattern + front ────────────────────────────────────────
def draw_card_static(surface, rect, revealed, board_val, BOX, hovering, glow=False, shake_offset=0):
    rx = rect.x + shake_offset

    # Shadow
    shadow = pygame.Rect(rx+4, rect.y+4, rect.width, rect.height)
    draw_rounded_rect(surface, shadow, (0,0,0), 10, 80)

    face_rect = pygame.Rect(rx, rect.y, rect.width, rect.height)

    if revealed:
        # White front
        draw_rounded_rect(surface, face_rect, CARD_FRONT, 10)
        if glow:
            for g in range(3,0,-1):
                gr = pygame.Rect(rx-g*3, rect.y-g*3, rect.width+g*6, rect.height+g*6)
                draw_rounded_rect(surface, gr, MATCH_GLOW, 12, 80-g*20)
        e = safe_emoji_render(board_val, BOX*0.60)
        er = e.get_rect(center=face_rect.center)
        surface.blit(e, er)
    else:
        col = HOVER_COL if hovering else CARD_BACK
        draw_rounded_rect(surface, face_rect, col, 10)

        # Diamond / grid pattern on back
        pattern_surf = pygame.Surface((face_rect.width, face_rect.height), pygame.SRCALPHA)
        spacing = max(12, BOX//5)
        for px in range(0, face_rect.width+spacing, spacing):
            for py in range(0, face_rect.height+spacing, spacing):
                pygame.draw.circle(pattern_surf, (255,255,255,35), (px,py), 2)
        for d in range(-face_rect.height, face_rect.width+face_rect.height, spacing*2):
            pygame.draw.line(pattern_surf, (255,255,255,20),
                             (d, 0), (d+face_rect.height, face_rect.height), 1)
        surface.blit(pattern_surf, face_rect.topleft)

        # "?" label
        ql = SMALL_FONT.render("?", True, (200, 255, 210))
        qr = ql.get_rect(center=face_rect.center)
        surface.blit(ql, qr)

    # Border
    pygame.draw.rect(surface, CARD_BORDER, face_rect, 2, border_radius=10)


# ── Flip animation ─────────────────────────────────────────────────────────────
FLIP_SPEED = 0.09

def draw_card_flip(surface, rect, revealed, board_val, BOX, hovering, progress, shake_offset=0):
    rx = rect.x + shake_offset
    p = progress
    if p < 0.5:
        scale = 1.0 - p*2
        show_front = False
    else:
        scale = (p-0.5)*2
        show_front = True

    w = max(2, int(rect.width*scale))
    cx = rx + rect.width//2
    anim = pygame.Rect(cx - w//2, rect.y, w, rect.height)

    shadow = pygame.Rect(anim.x+4, anim.y+4, anim.width, anim.height)
    draw_rounded_rect(surface, shadow, (0,0,0), 10, 60)

    if show_front:
        draw_rounded_rect(surface, anim, CARD_FRONT, 8)
        if scale > 0.3:
            e = safe_emoji_render(board_val, BOX*0.60)
            sw2 = max(1, int(e.get_width()*scale))
            sh2 = e.get_height()
            try:
                es = pygame.transform.scale(e, (sw2, sh2))
            except Exception:
                es = e
            er = es.get_rect(center=anim.center)
            surface.blit(es, er)
    else:
        draw_rounded_rect(surface, anim, CARD_BACK, 8)
        pattern_surf = pygame.Surface((anim.width, anim.height), pygame.SRCALPHA)
        spacing = max(10, BOX//5)
        for ppx in range(0, anim.width+spacing, spacing):
            for ppy in range(0, anim.height+spacing, spacing):
                pygame.draw.circle(pattern_surf, (255,255,255,35), (ppx,ppy), 2)
        surface.blit(pattern_surf, anim.topleft)

    pygame.draw.rect(surface, CARD_BORDER, anim, 2, border_radius=8)


# ── HUD ────────────────────────────────────────────────────────────────────────
HUD_H = 80
HUD_PAD = 12

def draw_hud(level_label, theme, remaining_ms, total_ms, moves, total_pairs):
    # Semi-transparent pill
    hud_rect = pygame.Rect(20, 10, DISPLAY_W-40, HUD_H)
    draw_rounded_rect(SCREEN, hud_rect, (0,0,0), 16, 140)

    # Level & theme
    lt = UI_FONT.render(f"  {level_label}  •  {theme}", True, (180,255,190))
    SCREEN.blit(lt, (hud_rect.x+16, hud_rect.y+12))

    # Time text
    secs = remaining_ms // 1000
    tc = TIMER_RED if remaining_ms < total_ms*0.25 else (TIMER_YEL if remaining_ms < total_ms*0.55 else TIMER_GREEN)
    ts = UI_FONT.render(f"⏱ {secs}s", True, tc)
    SCREEN.blit(ts, (hud_rect.x+16, hud_rect.y+42))

    # Moves (red if > 2× pairs)
    mc = (230,80,80) if moves > total_pairs*2 else (180,255,190)
    ms_surf = UI_FONT.render(f"Moves: {moves}", True, mc)
    SCREEN.blit(ms_surf, (hud_rect.right - ms_surf.get_width() - 16, hud_rect.y+12))

    esc_s = SMALL_FONT.render("ESC = quit", True, (130,180,140))
    SCREEN.blit(esc_s, (hud_rect.right - esc_s.get_width() - 16, hud_rect.y+46))

    # Timer bar
    bar_rect = pygame.Rect(hud_rect.x+16, hud_rect.bottom+6, hud_rect.width-32, 10)
    pygame.draw.rect(SCREEN, (50,50,50), bar_rect, border_radius=5)
    ratio = remaining_ms / total_ms
    fill_w = max(0, int(bar_rect.width * ratio))
    fill_rect = pygame.Rect(bar_rect.x, bar_rect.y, fill_w, bar_rect.height)
    pygame.draw.rect(SCREEN, tc, fill_rect, border_radius=5)
    pygame.draw.rect(SCREEN, (80,80,80), bar_rect, 1, border_radius=5)


# ── Confetti ───────────────────────────────────────────────────────────────────
class Confetti:
    COLORS = [(255,80,80),(255,200,50),(80,220,120),(80,180,255),(200,80,255),(255,140,30)]
    def __init__(self):
        self.x = random.randint(0, DISPLAY_W)
        self.y = random.randint(-60, -10)
        self.vx = random.uniform(-1.5, 1.5)
        self.vy = random.uniform(3, 7)
        self.rot = random.uniform(0, 360)
        self.rot_v = random.uniform(-5, 5)
        self.w = random.randint(8, 18)
        self.h = random.randint(5, 12)
        self.col = random.choice(self.COLORS)
        self.alpha = 255

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.rot += self.rot_v
        if self.y > DISPLAY_H + 20:
            self.y = random.randint(-60, -10)
            self.x = random.randint(0, DISPLAY_W)

    def draw(self, surface):
        s = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        s.fill((*self.col, 200))
        rot_s = pygame.transform.rotate(s, self.rot)
        surface.blit(rot_s, rot_s.get_rect(center=(int(self.x), int(self.y))))


# ── Star rating ────────────────────────────────────────────────────────────────
def get_stars(moves, total_pairs):
    if moves <= total_pairs:        return 3
    elif moves <= total_pairs * 2:  return 2
    else:                           return 1

def draw_stars(cx, y, stars):
    SIZE = 52
    gap  = 10
    total_w = 3*(SIZE+gap)
    sx = cx - total_w//2
    for i in range(3):
        col = STAR_GOLD if i < stars else STAR_EMPTY
        pts = []
        for sp in range(5):
            outer_a = math.radians(sp*72 - 90)
            inner_a = math.radians(sp*72 - 90 + 36)
            pts.append((sx + SIZE//2 + int(SIZE*0.48*math.cos(outer_a)),
                        y  + SIZE//2 + int(SIZE*0.48*math.sin(outer_a))))
            pts.append((sx + SIZE//2 + int(SIZE*0.20*math.cos(inner_a)),
                        y  + SIZE//2 + int(SIZE*0.20*math.sin(inner_a))))
        pygame.draw.polygon(SCREEN, col, pts)
        pygame.draw.polygon(SCREEN, (200,150,0) if i<stars else (100,100,100), pts, 2)
        sx += SIZE + gap


# ── Floating emoji background (menu) ──────────────────────────────────────────
class FloatingEmoji:
    def __init__(self, theme):
        pool = THEMES[theme]
        self.emoji = random.choice(pool)
        self.x = random.randint(0, DISPLAY_W)
        self.y = random.uniform(0, DISPLAY_H)
        self.vy = random.uniform(0.3, 0.9)
        self.alpha = random.randint(30, 80)
        self.size = random.randint(52, 100)

    def update(self):
        self.y += self.vy
        if self.y > DISPLAY_H + 80:
            self.y = -80
            self.x = random.randint(0, DISPLAY_W)

    def draw(self, surface):
        e = safe_emoji_render(self.emoji, self.size)
        tmp = e.copy()
        tmp.set_alpha(self.alpha)
        surface.blit(tmp, (int(self.x), int(self.y)))


# ── Menu screen ────────────────────────────────────────────────────────────────
def menu_screen():
    global theme_index, current_theme
    fade_in()

    floaters = [FloatingEmoji(current_theme) for _ in range(18)]
    level_keys = list(LEVELS.keys())
    hover_idx  = -1
    selected_idx = 0          # highlighted difficulty

    while True:
        draw_gradient(SCREEN, GRAD_TOP, GRAD_BOT)

        # Floating emoji bg
        for f in floaters:
            f.update()
            f.draw(SCREEN)

        # Title
        title_surf = TITLE_FONT.render("🍉 MEMORY PUZZLE 🍉", True, (120, 240, 140))
        ts_shadow  = TITLE_FONT.render("🍉 MEMORY PUZZLE 🍉", True, (0, 0, 0))
        tr = title_surf.get_rect(center=(DISPLAY_W//2, 110))
        SCREEN.blit(ts_shadow, tr.move(3,3))
        SCREEN.blit(title_surf, tr)

        # Theme strip
        theme_y = 195
        draw_center(f"Theme:  {current_theme}   ( T = cycle )", theme_y, SUB_FONT, (180, 255, 190))
        sample = THEMES[current_theme][:6]
        start_x = DISPLAY_W//2 - (len(sample)*64)//2
        for i, ic in enumerate(sample):
            s = safe_emoji_render(ic, 50)
            SCREEN.blit(s, s.get_rect(center=(start_x + i*64 + 32, theme_y+52)))

        # Difficulty list
        diff_y_base = 310
        draw_center("Choose Difficulty", diff_y_base, UI_FONT, (140, 210, 160))
        mx, my = pygame.mouse.get_pos()
        hover_idx = -1

        for i, label in enumerate(level_keys):
            row_y = diff_y_base + 48 + i*54
            box_w, box_h = 520, 44
            box_rect = pygame.Rect(DISPLAY_W//2 - box_w//2, row_y - box_h//2, box_w, box_h)

            if box_rect.collidepoint(mx, my):
                hover_idx = i

            is_sel   = (i == selected_idx)
            is_hover = (i == hover_idx)

            if is_sel:
                draw_rounded_rect(SCREEN, box_rect, (60, 160, 80), 12, 210)
                pygame.draw.rect(SCREEN, (120, 230, 140), box_rect, 2, border_radius=12)
            elif is_hover:
                draw_rounded_rect(SCREEN, box_rect, (40, 100, 55), 12, 180)

            col = WHITE if is_sel else ((200,255,210) if is_hover else (150, 200, 160))
            lbl_s = UI_FONT.render(label, True, col)
            SCREEN.blit(lbl_s, lbl_s.get_rect(center=box_rect.center))

        draw_center("ESC = Quit", DISPLAY_H - 50, SMALL_FONT, (100, 160, 120))
        pygame.display.update()

        for e in pygame.event.get():
            if e.type == QUIT:
                pygame.quit(); sys.exit()
            if e.type == KEYDOWN:
                if e.key == K_ESCAPE:
                    pygame.quit(); sys.exit()
                if e.key == K_t:
                    theme_index = (theme_index+1) % len(theme_keys)
                    current_theme = theme_keys[theme_index]
                    floaters = [FloatingEmoji(current_theme) for _ in range(18)]
                if e.key in (K_1, K_2, K_3, K_4):
                    selected_idx = {K_1:0,K_2:1,K_3:2,K_4:3}[e.key]
                    label = level_keys[selected_idx]
                    W, H, ts = LEVELS[label]
                    return current_theme, label, W, H, ts
                if e.key in (K_UP, K_DOWN):
                    selected_idx = (selected_idx + (-1 if e.key==K_UP else 1)) % 4
                if e.key == K_RETURN:
                    label = level_keys[selected_idx]
                    W, H, ts = LEVELS[label]
                    return current_theme, label, W, H, ts
            if e.type == MOUSEBUTTONUP:
                if hover_idx >= 0:
                    selected_idx = hover_idx
                    label = level_keys[selected_idx]
                    W, H, ts = LEVELS[label]
                    return current_theme, label, W, H, ts

        CLOCK.tick(FPS)


# ── Board helpers ──────────────────────────────────────────────────────────────
def compute_box_and_gap(W, H):
    GAP   = 10
    top_pad = HUD_H + 30 + 20
    max_w = DISPLAY_W * 0.85
    max_h = DISPLAY_H - top_pad - 40
    box_w = (max_w - (W-1)*GAP) / W
    box_h = (max_h - (H-1)*GAP) / H
    return max(30, int(min(box_w, box_h))), GAP

def generate_board(W, H, theme):
    needed = (W*H)//2
    pool   = THEMES[theme].copy()
    while len(pool) < needed:
        pool += pool
    rng  = secrets.SystemRandom()
    rng.shuffle(pool)
    icons = pool[:needed]*2
    rng.shuffle(icons)
    board, idx = [], 0
    for x in range(W):
        col = []
        for y in range(H):
            col.append(icons[idx]); idx += 1
        board.append(col)
    return board

def get_start_pos(W, H, BOX, GAP):
    total_w = W*BOX + (W-1)*GAP
    total_h = H*BOX + (H-1)*GAP
    sx = (DISPLAY_W - total_w)//2
    sy = HUD_H + 30 + (DISPLAY_H - HUD_H - 30 - total_h)//2
    return sx, sy


# ── Play level ─────────────────────────────────────────────────────────────────
def play_level(theme, level_label, W, H, time_seconds):
    BOX, GAP  = compute_box_and_gap(W, H)
    sx, sy    = get_start_pos(W, H, BOX, GAP)
    board     = generate_board(W, H, theme)
    revealed  = [[False]*H for _ in range(W)]
    matched   = [[False]*H for _ in range(W)]   # permanently matched
    first     = None
    matches   = 0
    total_pairs = (W*H)//2
    moves     = 0

    # Flip states
    flip_states:dict = {}          # (x,y) -> progress 0..1
    flip_back_queue:list = []
    flip_back_timer  = 0
    FLIP_BACK_DELAY  = 580

    # Match glow state
    glow_set:set = set()
    glow_timer   = 0
    GLOW_DUR     = 500             # ms

    # Shake state
    shake_cards: dict = {}         # (x,y) -> (phase, amplitude)
    SHAKE_DUR = 350                # ms per shake card
    SHAKE_AMP = 6

    # Initial reveal
    reveal_all   = True
    reveal_start = pygame.time.get_ticks()

    time_left_ms = time_seconds * 1000
    total_ms     = time_left_ms
    start_ticks  = pygame.time.get_ticks()

    # Fade in
    fade = pygame.Surface((DISPLAY_W, DISPLAY_H))
    fade.fill(BLACK)
    for a in range(200, -1, -20):
        draw_gradient(SCREEN, GRAD_TOP, GRAD_BOT)
        fade.set_alpha(a)
        SCREEN.blit(fade, (0,0))
        pygame.display.flip()
        pygame.time.delay(10)

    while True:
        dt = CLOCK.tick(FPS)

        elapsed      = pygame.time.get_ticks() - start_ticks
        remaining_ms = max(0, time_left_ms - elapsed)
        if remaining_ms == 0:
            return False, 0, moves

        # Advance flips
        done = []
        for pos in list(flip_states):
            flip_states[pos] = min(1.0, flip_states[pos] + FLIP_SPEED)
            if flip_states[pos] >= 1.0:
                done.append(pos)
        for pos in done:
            del flip_states[pos]

        # Flip-back timer
        if flip_back_queue:
            flip_back_timer -= dt
            if flip_back_timer <= 0:
                for pos in flip_back_queue:
                    x,y = pos
                    revealed[x][y] = False
                    flip_states[pos] = 0.0
                flip_back_queue.clear()

        # Glow timer
        if glow_set and pygame.time.get_ticks() - glow_timer > GLOW_DUR:
            glow_set.clear()

        # Shake update
        shake_offs = {}
        dead_shakes = []
        for pos, (start_t, amp) in list(shake_cards.items()):
            age = pygame.time.get_ticks() - start_t
            if age > SHAKE_DUR:
                dead_shakes.append(pos)
            else:
                phase = age / SHAKE_DUR
                offset = int(amp * math.sin(phase * math.pi * 5) * (1 - phase))
                shake_offs[pos] = offset
        for pos in dead_shakes:
            del shake_cards[pos]

        # ── Draw ──────────────────────────────────────────────────────────────
        draw_gradient(SCREEN, GRAD_TOP, GRAD_BOT)
        draw_hud(level_label, theme, remaining_ms, total_ms, moves, total_pairs)

        mx, my = pygame.mouse.get_pos()
        for x in range(W):
            for y in range(H):
                left = sx + x*(BOX+GAP)
                top  = sy + y*(BOX+GAP)
                rect = pygame.Rect(left, top, BOX, BOX)
                hovering = rect.collidepoint(mx,my) and not reveal_all and not flip_back_queue
                flip_prog = flip_states.get((x,y), None)
                glowing   = (x,y) in glow_set
                shk_off   = shake_offs.get((x,y), 0)

                if reveal_all:
                    draw_card_static(SCREEN, rect, True, board[x][y], BOX, False)
                elif flip_prog is not None:
                    draw_card_flip(SCREEN, rect, revealed[x][y], board[x][y], BOX, hovering, flip_prog, shk_off)
                else:
                    draw_card_static(SCREEN, rect, revealed[x][y], board[x][y], BOX, hovering, glowing, shk_off)

        if reveal_all and pygame.time.get_ticks() - reveal_start > 1100:
            reveal_all = False

        pygame.display.update()

        # ── Events ────────────────────────────────────────────────────────────
        for e in pygame.event.get():
            if e.type == QUIT:
                pygame.quit(); sys.exit()
            if e.type == KEYDOWN and e.key == K_ESCAPE:
                pygame.quit(); sys.exit()
            if e.type == MOUSEBUTTONUP and not reveal_all and not flip_back_queue:
                px, py = e.pos
                bx = by = None
                for ix in range(W):
                    for iy in range(H):
                        r = pygame.Rect(sx+ix*(BOX+GAP), sy+iy*(BOX+GAP), BOX, BOX)
                        if r.collidepoint(px,py):
                            bx, by = ix, iy
                if bx is not None and not revealed[bx][by] and (bx,by) not in flip_states:
                    flip_states[(bx,by)] = 0.0
                    revealed[bx][by] = True
                    if first is None:
                        first = (bx,by)
                    else:
                        fx,fy = first
                        moves += 1
                        if board[fx][fy] == board[bx][by]:
                            matches += 1
                            matched[fx][fy] = True
                            matched[bx][by] = True
                            glow_set.add((fx,fy))
                            glow_set.add((bx,by))
                            glow_timer = pygame.time.get_ticks()
                        else:
                            flip_back_queue.extend([(fx,fy),(bx,by)])
                            flip_back_timer = FLIP_BACK_DELAY
                            now = pygame.time.get_ticks()
                            shake_cards[(fx,fy)] = (now, SHAKE_AMP)
                            shake_cards[(bx,by)] = (now, SHAKE_AMP)
                        first = None

        if matches == total_pairs:
            return True, remaining_ms//1000, moves


# ── Button helper ──────────────────────────────────────────────────────────────
def draw_button(rect, label, hover, font=UI_FONT):
    col = (80,200,100) if hover else (50,140,70)
    draw_rounded_rect(SCREEN, rect, col, 14, 230)
    if hover:
        pygame.draw.rect(SCREEN, (120,240,140), rect, 2, border_radius=14)
    lbl = font.render(label, True, WHITE)
    SCREEN.blit(lbl, lbl.get_rect(center=rect.center))


# ── Win screen ─────────────────────────────────────────────────────────────────
def win_screen(remaining_s, moves, total_pairs):
    confetti = [Confetti() for _ in range(160)]
    stars    = get_stars(moves, total_pairs)

    btn_w, btn_h = 260, 54
    btn_play   = pygame.Rect(DISPLAY_W//2 - btn_w - 20, DISPLAY_H//2 + 120, btn_w, btn_h)
    btn_quit   = pygame.Rect(DISPLAY_W//2 + 20,          DISPLAY_H//2 + 120, btn_w, btn_h)

    while True:
        draw_gradient(SCREEN, (15,50,20), (5,25,10))
        for c in confetti:
            c.update(); c.draw(SCREEN)

        # Panel
        panel = pygame.Rect(DISPLAY_W//2-340, DISPLAY_H//2-170, 680, 340)
        draw_rounded_rect(SCREEN, panel, (20,60,30), 20, 210)
        pygame.draw.rect(SCREEN, (80,200,100), panel, 2, border_radius=20)

        draw_center("🎉 LEVEL CLEARED! 🎉", DISPLAY_H//2 - 110, SUB_FONT, (120,255,140))
        draw_stars(DISPLAY_W//2, DISPLAY_H//2 - 60, stars)
        draw_center(f"Time left: {remaining_s}s    Moves: {moves}", DISPLAY_H//2 + 30, UI_FONT, (200,255,210))

        star_labels = {3:"Perfect!", 2:"Great job!", 1:"Good effort!"}
        draw_center(star_labels[stars], DISPLAY_H//2 + 68, SUB_FONT,
                    STAR_GOLD if stars==3 else ((180,220,180) if stars==2 else (180,180,180)))

        mx, my = pygame.mouse.get_pos()
        draw_button(btn_play, "▶  Play Again", btn_play.collidepoint(mx,my))
        draw_button(btn_quit, "✕  Quit",       btn_quit.collidepoint(mx,my))

        pygame.display.update()

        for e in pygame.event.get():
            if e.type == QUIT:
                pygame.quit(); sys.exit()
            if e.type == KEYDOWN:
                if e.key == K_ESCAPE:
                    pygame.quit(); sys.exit()
                if e.key == K_RETURN:
                    return True
            if e.type == MOUSEBUTTONUP:
                if btn_play.collidepoint(e.pos): return True
                if btn_quit.collidepoint(e.pos):
                    pygame.quit(); sys.exit()

        CLOCK.tick(FPS)


# ── Lose screen ────────────────────────────────────────────────────────────────
def lose_screen(moves, total_pairs):
    stars = get_stars(moves, total_pairs)

    btn_w, btn_h = 260, 54
    btn_retry = pygame.Rect(DISPLAY_W//2 - btn_w - 20, DISPLAY_H//2 + 110, btn_w, btn_h)
    btn_quit  = pygame.Rect(DISPLAY_W//2 + 20,          DISPLAY_H//2 + 110, btn_w, btn_h)

    while True:
        draw_gradient(SCREEN, (50,15,15), (25,5,5))

        panel = pygame.Rect(DISPLAY_W//2-320, DISPLAY_H//2-160, 640, 310)
        draw_rounded_rect(SCREEN, panel, (60,20,20), 20, 210)
        pygame.draw.rect(SCREEN, (200,70,70), panel, 2, border_radius=20)

        draw_center("⛔ TIME'S UP ⛔", DISPLAY_H//2 - 100, SUB_FONT, (255,120,120))
        draw_stars(DISPLAY_W//2, DISPLAY_H//2 - 55, stars)
        draw_center(f"Moves made: {moves}", DISPLAY_H//2 + 20, UI_FONT, (255,200,200))
        draw_center("Better luck next time!", DISPLAY_H//2 + 58, UI_FONT, (200,160,160))

        mx, my = pygame.mouse.get_pos()
        draw_button(btn_retry, "↺  Try Again", btn_retry.collidepoint(mx,my))
        draw_button(btn_quit,  "✕  Quit",      btn_quit.collidepoint(mx,my))

        pygame.display.update()

        for e in pygame.event.get():
            if e.type == QUIT:
                pygame.quit(); sys.exit()
            if e.type == KEYDOWN:
                if e.key == K_ESCAPE:
                    pygame.quit(); sys.exit()
                if e.key == K_RETURN:
                    return True
            if e.type == MOUSEBUTTONUP:
                if btn_retry.collidepoint(e.pos): return True
                if btn_quit.collidepoint(e.pos):
                    pygame.quit(); sys.exit()

        CLOCK.tick(FPS)


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    while True:
        theme, level_label, W, H, tsec = menu_screen()
        total_pairs = (W*H)//2
        success, remaining, moves = play_level(theme, level_label, W, H, tsec)
        if success:
            win_screen(remaining, moves, total_pairs)
        else:
            lose_screen(moves, total_pairs)

if __name__ == "__main__":
    main()