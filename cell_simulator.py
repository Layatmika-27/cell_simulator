"""
cell_simulator.py

An interactive biological-style cell simulator using pygame.

✨ Features:
- Cells move randomly and steer toward nearby food.
- Smooth glowing visuals with subtle "breathing" animation.
- Food spawns by clicking or pressing F.
- Cells eat, gain energy, reproduce, and die naturally.
- Optional timed auto food spawn (commented out).
- Clean UI for stats and controls.

Author: Your Name
"""

import pygame
import random
import math
from collections import deque

# -------------------- CONFIG --------------------
WIDTH, HEIGHT = 900, 600
FPS = 60

BACKGROUND_TOP = (15, 20, 30)
BACKGROUND_BOTTOM = (30, 40, 60)
FOOD_COLOR = (255, 200, 80)
FOOD_RADIUS = 4

INITIAL_CELLS = 8
CELL_MIN_RADIUS = 8
CELL_MAX_RADIUS = 18
CELL_BASE_SPEED = 1.0
ENERGY_LOSS_PER_SEC = 1.0
ENERGY_FROM_FOOD = 20
SPLIT_ENERGY_THRESHOLD = 60
SPLIT_ENERGY_COST = 30
MAX_ENERGY = 100

FOOD_PER_SPAWN = 3
MAX_FOOD = 200
CELL_SENSE_RADIUS = 120
CELL_MAX_TURN = 0.25

FONT_SIZE = 18
# ------------------------------------------------

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Cell Simulator 🧫")
clock = pygame.time.Clock()
font = pygame.font.Font(None, FONT_SIZE)

# -------------------- UTILITY --------------------
def lerp(a, b, t):
    return a + (b - a) * t

def gradient_bg(surface, top, bottom):
    for y in range(surface.get_height()):
        r = int(lerp(top[0], bottom[0], y / surface.get_height()))
        g = int(lerp(top[1], bottom[1], y / surface.get_height()))
        b = int(lerp(top[2], bottom[2], y / surface.get_height()))
        pygame.draw.line(surface, (r, g, b), (0, y), (surface.get_width(), y))

# -------------------- CLASSES --------------------
class Food:
    def __init__(self, x, y):
        self.x = x
        self.y = y

class Cell:
    def __init__(self, x, y, radius=None):
        self.x = x
        self.y = y
        self.radius = radius if radius else random.randint(CELL_MIN_RADIUS, CELL_MAX_RADIUS)
        self.base_radius = self.radius
        self.angle = random.random() * 2 * math.pi
        self.speed = CELL_BASE_SPEED * (1.0 + (CELL_MAX_RADIUS - self.radius) / (CELL_MAX_RADIUS * 2))
        self.energy = random.uniform(20, 50)
        self.color = (
            random.randint(80, 255),
            random.randint(80, 255),
            random.randint(80, 255),
        )
        self.trail = deque(maxlen=8)
        self.time_offset = random.uniform(0, 2 * math.pi)  # breathing offset

    def update(self, dt, foods, all_cells, time):
        self.energy -= ENERGY_LOSS_PER_SEC * dt
        if self.energy > MAX_ENERGY:
            self.energy = MAX_ENERGY

        # Steering toward nearby food
        target = None
        min_d = float("inf")
        for f in foods:
            d = (f.x - self.x) ** 2 + (f.y - self.y) ** 2
            if d < min_d and d <= CELL_SENSE_RADIUS ** 2:
                min_d = d
                target = f

        if not target:
            self.angle += random.uniform(-0.02, 0.02)
        else:
            desired = math.atan2(target.y - self.y, target.x - self.x)
            diff = (desired - self.angle + math.pi) % (2 * math.pi) - math.pi
            turn = max(-CELL_MAX_TURN, min(CELL_MAX_TURN, diff))
            self.angle += turn

        # Move
        self.x += math.cos(self.angle) * self.speed
        self.y += math.sin(self.angle) * self.speed

        # Bounce off walls
        margin = 5
        if self.x < margin:
            self.x = margin; self.angle = random.uniform(-math.pi/2, math.pi/2)
        if self.x > WIDTH - margin:
            self.x = WIDTH - margin; self.angle = random.uniform(math.pi/2, 3*math.pi/2)
        if self.y < margin:
            self.y = margin; self.angle = random.uniform(0, math.pi)
        if self.y > HEIGHT - margin:
            self.y = HEIGHT - margin; self.angle = random.uniform(-math.pi, 0)

        # Trail
        self.trail.append((self.x, self.y))

        # Eating food
        for i, f in enumerate(foods):
            dx = f.x - self.x; dy = f.y - self.y
            if dx*dx + dy*dy <= (self.radius + FOOD_RADIUS) ** 2:
                del foods[i]
                self.energy += ENERGY_FROM_FOOD
                return "ate"
        return None

    def can_split(self):
        return self.energy >= SPLIT_ENERGY_THRESHOLD and self.radius >= CELL_MIN_RADIUS + 1

    def split(self):
        child_energy = self.energy / 2.0 - SPLIT_ENERGY_COST / 2.0
        self.energy = self.energy / 2.0 - SPLIT_ENERGY_COST / 2.0
        if self.energy < 5:
            self.energy += child_energy
            return None
        nx = self.x + random.uniform(-self.radius*2, self.radius*2)
        ny = self.y + random.uniform(-self.radius*2, self.radius*2)
        child = Cell(nx, ny, radius=max(CELL_MIN_RADIUS, int(self.radius * 0.9)))
        child.energy = max(5, child_energy)
        child.color = (
            min(255, max(0, self.color[0] + random.randint(-20, 20))),
            min(255, max(0, self.color[1] + random.randint(-20, 20))),
            min(255, max(0, self.color[2] + random.randint(-20, 20))),
        )
        return child

    def is_dead(self):
        return self.energy <= 0 or self.radius <= 0

    def draw(self, surf, time):
        # Breathing effect
        breathe = 1 + 0.08 * math.sin(time * 3 + self.time_offset)
        self.radius = int(self.base_radius * breathe)

        # Glow circle
        size = self.radius * 4
        circle_surf = pygame.Surface((size, size), pygame.SRCALPHA)
        center = size // 2

        for r in range(self.radius, 0, -1):
            color_factor = r / self.radius
            col = (
                max(0, min(255, int(self.color[0] * color_factor + 40))),
                max(0, min(255, int(self.color[1] * color_factor + 40))),
                max(0, min(255, int(self.color[2] * color_factor + 40))),
                int(255 * (color_factor ** 1.5)),
            )
            pygame.draw.circle(circle_surf, col, (center, center), r)

        pygame.draw.circle(circle_surf, (*self.color, 60), (center, center), int(self.radius * 1.5))
        surf.blit(circle_surf, (int(self.x - center), int(self.y - center)), special_flags=pygame.BLEND_PREMULTIPLIED)

        # Eye
        ex = int(self.x + math.cos(self.angle) * self.radius * 0.4)
        ey = int(self.y + math.sin(self.angle) * self.radius * 0.4)
        pygame.draw.circle(surf, (20, 20, 20), (ex, ey), max(2, self.radius // 4))

        # Energy bar
        bar_w = int(self.radius * 1.8)
        bar_h = 5
        bx = int(self.x - bar_w / 2)
        by = int(self.y + self.radius + 8)
        pygame.draw.rect(surf, (60, 60, 60), (bx, by, bar_w, bar_h), border_radius=3)
        fill_w = int(bar_w * (max(0, min(MAX_ENERGY, self.energy)) / MAX_ENERGY))
        pygame.draw.rect(surf, (80, 255, 120), (bx, by, fill_w, bar_h), border_radius=3)

# -------------------- SIMULATION --------------------
cells = [Cell(random.uniform(50, WIDTH-50), random.uniform(50, HEIGHT-50)) for _ in range(INITIAL_CELLS)]
foods = []
total_births = 0
paused = False
speed_multiplier = 1.0
time_accum = 0
food_timer = 0  # For optional auto spawn

# -------------------- MAIN LOOP --------------------
running = True
while running:
    dt_ms = clock.tick(FPS)
    dt = (dt_ms / 1000.0) * speed_multiplier
    time_accum += dt

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                paused = not paused
            elif event.key == pygame.K_UP:
                speed_multiplier = min(4.0, speed_multiplier + 0.25)
            elif event.key == pygame.K_DOWN:
                speed_multiplier = max(0.25, speed_multiplier - 0.25)
            elif event.key == pygame.K_r:
                cells.clear(); foods.clear(); total_births = 0
                cells = [Cell(random.uniform(50, WIDTH-50), random.uniform(50, HEIGHT-50)) for _ in range(INITIAL_CELLS)]
            elif event.key == pygame.K_f:
                for _ in range(10):
                    foods.append(Food(random.uniform(20, WIDTH-20), random.uniform(20, HEIGHT-20)))
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            foods.append(Food(mx, my))

    # -------------------- OPTIONAL AUTO FOOD --------------------
    # Uncomment this block to enable automatic food spawning every few seconds
    """
    food_timer += dt
    if food_timer > 5 and len(foods) < MAX_FOOD:
        for _ in range(random.randint(2, 6)):
            foods.append(Food(random.uniform(20, WIDTH-20), random.uniform(20, HEIGHT-20)))
        food_timer = 0
    """

    if not paused:
        new_cells = []
        dead_indices = []
        for i, c in enumerate(cells):
            result = c.update(dt, foods, cells, time_accum)
            if c.can_split() and random.random() < 0.02:
                child = c.split()
                if child:
                    new_cells.append(child)
                    total_births += 1
            if c.is_dead():
                dead_indices.append(i)
        if dead_indices:
            cells = [c for idx, c in enumerate(cells) if idx not in dead_indices]
        cells.extend(new_cells)

    # ---------- DRAW ----------
    bg = pygame.Surface((WIDTH, HEIGHT))
    gradient_bg(bg, BACKGROUND_TOP, BACKGROUND_BOTTOM)
    screen.blit(bg, (0, 0))

    for f in foods:
        pygame.draw.circle(screen, FOOD_COLOR, (int(f.x), int(f.y)), FOOD_RADIUS)

    for c in sorted(cells, key=lambda c: c.radius):
        c.draw(screen, time_accum)

    txt1 = font.render(f"Population: {len(cells)}   Births: {total_births}   Food: {len(foods)}", True, (230, 230, 230))
    txt2 = font.render(f"Speed x{speed_multiplier:.2f}   Pause: {'ON' if paused else 'OFF'}", True, (200, 200, 200))
    txt3 = font.render("SPACE: Pause | UP/DOWN: Speed | Click/F: Add Food | R: Reset", True, (180, 180, 180))
    screen.blit(txt1, (10, 8))
    screen.blit(txt2, (10, 28))
    screen.blit(txt3, (10, 50))

    hint = font.render("Cells breathe, eat, and multiply — watch the colony thrive!", True, (160, 160, 160))
    screen.blit(hint, (10, HEIGHT - 26))

    pygame.display.flip()

pygame.quit()

