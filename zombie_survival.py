import pygame
import random
import math
import os

pygame.init()

# --------------------------------------------------
# SETTINGS
# --------------------------------------------------

WIDTH = 1100
HEIGHT = 700
FPS = 60

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Zombie Survival")

clock = pygame.time.Clock()

# --------------------------------------------------
# COLORS
# --------------------------------------------------

BLACK = (10, 10, 15)
WHITE = (255, 255, 255)
RED = (220, 50, 50)
GREEN = (50, 220, 80)
DARK_GREEN = (20, 120, 50)
YELLOW = (255, 220, 50)
ORANGE = (255, 140, 40)
BLUE = (50, 150, 255)
PURPLE = (170, 70, 220)
GRAY = (100, 100, 110)
DARK_GRAY = (35, 35, 45)

# --------------------------------------------------
# FONTS
# --------------------------------------------------

font_small = pygame.font.SysFont("arial", 20)
font = pygame.font.SysFont("arial", 28)
font_medium = pygame.font.SysFont("arial", 36, bold=True)
font_big = pygame.font.SysFont("arial", 60, bold=True)
font_title = pygame.font.SysFont("arial", 75, bold=True)

# --------------------------------------------------
# GAME STATES
# --------------------------------------------------

MENU = "menu"
INSTRUCTIONS = "instructions"
GAME = "game"
PAUSE = "pause"
GAME_OVER = "game_over"

game_state = MENU

# --------------------------------------------------
# HIGH SCORE
# --------------------------------------------------

HIGH_SCORE_FILE = "highscore.txt"

def load_high_score():
    try:
        with open(HIGH_SCORE_FILE, "r") as file:
            return int(file.read())
    except:
        return 0

def save_high_score(score):
    try:
        with open(HIGH_SCORE_FILE, "w") as file:
            file.write(str(score))
    except:
        pass

high_score = load_high_score()

# --------------------------------------------------
# SOUND
# --------------------------------------------------

sound_enabled = False

try:
    pygame.mixer.init()
    sound_enabled = True
except:
    sound_enabled = False

def load_sound(filename):
    if not sound_enabled:
        return None

    if os.path.exists(filename):
        try:
            return pygame.mixer.Sound(filename)
        except:
            return None

    return None

shoot_sound = load_sound("shoot.wav")
hit_sound = load_sound("hit.wav")
powerup_sound = load_sound("powerup.wav")
gameover_sound = load_sound("gameover.wav")

def play_sound(sound):
    if sound:
        sound.play()

# --------------------------------------------------
# BUTTON
# --------------------------------------------------

class Button:
    def __init__(self, x, y, w, h, text):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text

    def draw(self):
        mouse = pygame.mouse.get_pos()

        if self.rect.collidepoint(mouse):
            color = BLUE
        else:
            color = DARK_GRAY

        pygame.draw.rect(screen, color, self.rect, border_radius=10)
        pygame.draw.rect(screen, WHITE, self.rect, 2, border_radius=10)

        text_surface = font_medium.render(self.text, True, WHITE)
        text_rect = text_surface.get_rect(center=self.rect.center)

        screen.blit(text_surface, text_rect)

    def clicked(self):
        return self.rect.collidepoint(pygame.mouse.get_pos())

# --------------------------------------------------
# PLAYER
# --------------------------------------------------

class Player:
    def __init__(self):
        self.x = WIDTH // 2
        self.y = HEIGHT // 2

        self.radius = 20

        self.speed = 5

        self.max_health = 100
        self.health = 100

        self.shoot_delay = 180
        self.last_shot = 0

        self.grenades = 3

        self.rapid_fire = False
        self.rapid_fire_end = 0

        self.shield = False
        self.shield_end = 0

        self.speed_boost = False
        self.speed_boost_end = 0

    def update(self):

        keys = pygame.key.get_pressed()

        dx = 0
        dy = 0

        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy -= 1

        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy += 1

        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx -= 1

        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx += 1

        if dx != 0 or dy != 0:

            length = math.sqrt(dx * dx + dy * dy)

            dx /= length
            dy /= length

            current_speed = self.speed

            if self.speed_boost:
                current_speed = 8

            self.x += dx * current_speed
            self.y += dy * current_speed

        self.x = max(self.radius, min(WIDTH - self.radius, self.x))
        self.y = max(self.radius, min(HEIGHT - self.radius, self.y))

        current_time = pygame.time.get_ticks()

        if self.rapid_fire and current_time > self.rapid_fire_end:
            self.rapid_fire = False

        if self.shield and current_time > self.shield_end:
            self.shield = False

        if self.speed_boost and current_time > self.speed_boost_end:
            self.speed_boost = False

    def shoot(self, target_x, target_y):

        current_time = pygame.time.get_ticks()

        delay = self.shoot_delay

        if self.rapid_fire:
            delay = 80

        if current_time - self.last_shot < delay:
            return None

        self.last_shot = current_time

        dx = target_x - self.x
        dy = target_y - self.y

        distance = math.sqrt(dx * dx + dy * dy)

        if distance == 0:
            return None

        dx /= distance
        dy /= distance

        play_sound(shoot_sound)

        return Bullet(self.x, self.y, dx, dy)

    def damage(self, amount):

        if self.shield:
            return

        self.health -= amount

        if self.health < 0:
            self.health = 0

    def draw(self):

        # Shield
        if self.shield:
            pygame.draw.circle(
                screen,
                BLUE,
                (int(self.x), int(self.y)),
                self.radius + 10,
                3
            )

        pygame.draw.circle(
            screen,
            BLUE,
            (int(self.x), int(self.y)),
            self.radius
        )

        # Gun direction
        mouse_x, mouse_y = pygame.mouse.get_pos()

        dx = mouse_x - self.x
        dy = mouse_y - self.y

        distance = math.sqrt(dx * dx + dy * dy)

        if distance > 0:
            dx /= distance
            dy /= distance

        gun_x = self.x + dx * 30
        gun_y = self.y + dy * 30

        pygame.draw.line(
            screen,
            WHITE,
            (self.x, self.y),
            (gun_x, gun_y),
            7
        )

# --------------------------------------------------
# BULLET
# --------------------------------------------------

class Bullet:
    def __init__(self, x, y, dx, dy):

        self.x = x
        self.y = y

        self.dx = dx
        self.dy = dy

        self.speed = 12

        self.radius = 5

        self.active = True

    def update(self):

        self.x += self.dx * self.speed
        self.y += self.dy * self.speed

        if (
            self.x < 0
            or self.x > WIDTH
            or self.y < 0
            or self.y > HEIGHT
        ):
            self.active = False

    def draw(self):

        pygame.draw.circle(
            screen,
            YELLOW,
            (int(self.x), int(self.y)),
            self.radius
        )

# --------------------------------------------------
# ZOMBIE
# --------------------------------------------------

class Zombie:
    def __init__(self, zombie_type, wave):

        side = random.randint(0, 3)

        if side == 0:
            self.x = random.randint(0, WIDTH)
            self.y = -40

        elif side == 1:
            self.x = WIDTH + 40
            self.y = random.randint(0, HEIGHT)

        elif side == 2:
            self.x = random.randint(0, WIDTH)
            self.y = HEIGHT + 40

        else:
            self.x = -40
            self.y = random.randint(0, HEIGHT)

        self.type = zombie_type

        if zombie_type == "normal":

            self.radius = 20
            self.health = 2 + wave // 4
            self.speed = 1.2 + wave * 0.04
            self.damage = 8
            self.points = 10
            self.color = GREEN

        elif zombie_type == "fast":

            self.radius = 15
            self.health = 1 + wave // 6
            self.speed = 2.4 + wave * 0.05
            self.damage = 5
            self.points = 20
            self.color = YELLOW

        elif zombie_type == "tank":

            self.radius = 30
            self.health = 8 + wave
            self.speed = 0.7 + wave * 0.02
            self.damage = 15
            self.points = 50
            self.color = PURPLE

        else:

            self.radius = 45
            self.health = 30 + wave * 3
            self.speed = 0.9 + wave * 0.01
            self.damage = 25
            self.points = 200
            self.color = RED

        self.attack_delay = 700
        self.last_attack = 0

    def update(self, player):

        dx = player.x - self.x
        dy = player.y - self.y

        distance = math.sqrt(dx * dx + dy * dy)

        if distance > 0:

            dx /= distance
            dy /= distance

            self.x += dx * self.speed
            self.y += dy * self.speed

        # Attack player
        if distance < self.radius + player.radius:

            current_time = pygame.time.get_ticks()

            if current_time - self.last_attack > self.attack_delay:

                player.damage(self.damage)

                self.last_attack = current_time

    def draw(self):

        pygame.draw.circle(
            screen,
            self.color,
            (int(self.x), int(self.y)),
            self.radius
        )

        # Eyes
        eye_size = max(3, self.radius // 5)

        pygame.draw.circle(
            screen,
            WHITE,
            (
                int(self.x - self.radius * 0.3),
                int(self.y - self.radius * 0.2)
            ),
            eye_size
        )

        pygame.draw.circle(
            screen,
            WHITE,
            (
                int(self.x + self.radius * 0.3),
                int(self.y - self.radius * 0.2)
            ),
            eye_size
        )

# --------------------------------------------------
# POWER UP
# --------------------------------------------------

class PowerUp:

    TYPES = [
        "health",
        "rapid",
        "shield",
        "speed",
        "grenade"
    ]

    def __init__(self, x, y):

        self.x = x
        self.y = y

        self.radius = 15

        self.type = random.choice(self.TYPES)

        self.spawn_time = pygame.time.get_ticks()

    def draw(self):

        colors = {
            "health": RED,
            "rapid": YELLOW,
            "shield": BLUE,
            "speed": ORANGE,
            "grenade": PURPLE
        }

        color = colors[self.type]

        pygame.draw.circle(
            screen,
            color,
            (int(self.x), int(self.y)),
            self.radius
        )

        letters = {
            "health": "+",
            "rapid": "R",
            "shield": "S",
            "speed": "⚡",
            "grenade": "G"
        }

        text = font_small.render(
            letters[self.type],
            True,
            WHITE
        )

        rect = text.get_rect(
            center=(self.x, self.y)
        )

        screen.blit(text, rect)

    def expired(self):

        return pygame.time.get_ticks() - self.spawn_time > 10000

# --------------------------------------------------
# GLOBAL GAME VARIABLES
# --------------------------------------------------

player = None
bullets = []
zombies = []
powerups = []

score = 0
wave = 1

wave_zombies_remaining = 0
zombies_spawned = 0

wave_start_time = 0

last_zombie_spawn = 0
last_powerup_spawn = 0

game_start_time = 0

# --------------------------------------------------
# START GAME
# --------------------------------------------------

def start_game():

    global player
    global bullets
    global zombies
    global powerups

    global score
    global wave

    global wave_zombies_remaining
    global zombies_spawned

    global wave_start_time
    global last_zombie_spawn
    global last_powerup_spawn
    global game_start_time

    player = Player()

    bullets = []
    zombies = []
    powerups = []

    score = 0

    wave = 1

    wave_zombies_remaining = 8
    zombies_spawned = 0

    wave_start_time = pygame.time.get_ticks()

    last_zombie_spawn = 0
    last_powerup_spawn = pygame.time.get_ticks()

    game_start_time = pygame.time.get_ticks()

# --------------------------------------------------
# SPAWN ZOMBIE
# --------------------------------------------------

def spawn_zombie():

    global zombies_spawned

    if zombies_spawned >= wave_zombies_remaining:
        return

    zombie_type = "normal"

    roll = random.random()

    if wave >= 3 and roll < 0.15:
        zombie_type = "fast"

    if wave >= 5 and roll < 0.08:
        zombie_type = "tank"

    if wave >= 8 and roll < 0.03:
        zombie_type = "boss"

    zombies.append(
        Zombie(zombie_type, wave)
    )

    zombies_spawned += 1

# --------------------------------------------------
# NEXT WAVE
# --------------------------------------------------

def next_wave():

    global wave
    global wave_zombies_remaining
    global zombies_spawned
    global wave_start_time

    wave += 1

    wave_zombies_remaining = 8 + wave * 3

    zombies_spawned = 0

    wave_start_time = pygame.time.get_ticks()

    # Small health reward
    player.health = min(
        player.max_health,
        player.health + 10
    )

# --------------------------------------------------
# USE GRENADE
# --------------------------------------------------

def use_grenade():

    global zombies
    global score

    if player.grenades <= 0:
        return

    player.grenades -= 1

    explosion_radius = 180

    remaining_zombies = []

    for zombie in zombies:

        dx = zombie.x - player.x
        dy = zombie.y - player.y

        distance = math.sqrt(dx * dx + dy * dy)

        if distance <= explosion_radius:

            score += zombie.points

        else:

            remaining_zombies.append(zombie)

    zombies = remaining_zombies

# --------------------------------------------------
# POWER UP EFFECT
# --------------------------------------------------

def collect_powerup(powerup):

    current_time = pygame.time.get_ticks()

    if powerup.type == "health":

        player.health = min(
            player.max_health,
            player.health + 30
        )

    elif powerup.type == "rapid":

        player.rapid_fire = True
        player.rapid_fire_end = current_time + 7000

    elif powerup.type == "shield":

        player.shield = True
        player.shield_end = current_time + 7000

    elif powerup.type == "speed":

        player.speed_boost = True
        player.speed_boost_end = current_time + 7000

    elif powerup.type == "grenade":

        player.grenades += 1

    play_sound(powerup_sound)

# --------------------------------------------------
# COLLISION CHECK
# --------------------------------------------------

def distance_between(x1, y1, x2, y2):

    return math.sqrt(
        (x1 - x2) ** 2 +
        (y1 - y2) ** 2
    )

# --------------------------------------------------
# DRAW BACKGROUND
# --------------------------------------------------

def draw_background():

    screen.fill(BLACK)

    # Grid
    grid_size = 50

    for x in range(0, WIDTH, grid_size):

        pygame.draw.line(
            screen,
            (20, 25, 30),
            (x, 0),
            (x, HEIGHT)
        )

    for y in range(0, HEIGHT, grid_size):

        pygame.draw.line(
            screen,
            (20, 25, 30),
            (0, y),
            (WIDTH, y)
        )

# --------------------------------------------------
# HUD
# --------------------------------------------------

def draw_hud():

    # Health bar
    bar_x = 20
    bar_y = 20
    bar_width = 250
    bar_height = 25

    pygame.draw.rect(
        screen,
        DARK_GRAY,
        (bar_x, bar_y, bar_width, bar_height)
    )

    health_width = int(
        bar_width *
        player.health /
        player.max_health
    )

    pygame.draw.rect(
        screen,
        RED,
        (bar_x, bar_y, health_width, bar_height)
    )

    pygame.draw.rect(
        screen,
        WHITE,
        (bar_x, bar_y, bar_width, bar_height),
        2
    )

    health_text = font_small.render(
        f"Health: {player.health}",
        True,
        WHITE
    )

    screen.blit(
        health_text,
        (bar_x + 5, bar_y + 2)
    )

    score_text = font.render(
        f"Score: {score}",
        True,
        WHITE
    )

    screen.blit(
        score_text,
        (WIDTH - 180, 20)
    )

    wave_text = font.render(
        f"Wave: {wave}",
        True,
        WHITE
    )

    screen.blit(
        wave_text,
        (WIDTH - 180, 55)
    )

    zombie_text = font_small.render(
        f"Zombies: {len(zombies)}",
        True,
        WHITE
    )

    screen.blit(
        zombie_text,
        (WIDTH - 180, 95)
    )

    grenade_text = font_small.render(
        f"Grenades: {player.grenades}  [G]",
        True,
        WHITE
    )

    screen.blit(
        grenade_text,
        (20, 60)
    )

    if player.rapid_fire:

        text = font_small.render(
            "RAPID FIRE!",
            True,
            YELLOW
        )

        screen.blit(
            text,
            (20, 100)
        )

    if player.shield:

        text = font_small.render(
            "SHIELD!",
            True,
            BLUE
        )

        screen.blit(
            text,
            (20, 125)
        )

    if player.speed_boost:

        text = font_small.render(
            "SPEED BOOST!",
            True,
            ORANGE
        )

        screen.blit(
            text,
            (20, 150)
        )

# --------------------------------------------------
# INSTRUCTIONS SCREEN
# --------------------------------------------------

def draw_instructions():

    screen.fill(BLACK)

    title = font_title.render(
        "INSTRUCTIONS",
        True,
        WHITE
    )

    title_rect = title.get_rect(
        center=(WIDTH // 2, 80)
    )

    screen.blit(title, title_rect)

    instructions = [
        "W A S D / Arrow Keys  - Move",
        "Mouse                - Aim",
        "Left Mouse Button    - Shoot",
        "G                      - Use Grenade",
        "ESC                    - Pause",
        "",
        "Defeat zombies to earn points.",
        "Survive increasingly difficult waves.",
        "Collect power-ups to gain special abilities.",
        "",
        "Zombie Types:",
        "Green  - Normal Zombie",
        "Yellow - Fast Zombie",
        "Purple - Tank Zombie",
        "Red    - Boss Zombie"
    ]

    y = 160

    for line in instructions:

        text = font.render(
            line,
            True,
            WHITE
        )

        rect = text.get_rect(
            center=(WIDTH // 2, y)
        )

        screen.blit(text, rect)

        y += 32

    back_button = Button(
        WIDTH // 2 - 100,
        HEIGHT - 90,
        200,
        55,
        "BACK"
    )

    back_button.draw()

    return back_button

# --------------------------------------------------
# MENU
# --------------------------------------------------

def draw_menu():

    screen.fill(BLACK)

    title = font_title.render(
        "ZOMBIE SURVIVAL",
        True,
        GREEN
    )

    title_rect = title.get_rect(
        center=(WIDTH // 2, 130)
    )

    screen.blit(title, title_rect)

    subtitle = font.render(
        "SURVIVE THE HORDE",
        True,
        WHITE
    )

    subtitle_rect = subtitle.get_rect(
        center=(WIDTH // 2, 195)
    )

    screen.blit(subtitle, subtitle_rect)

    start_button = Button(
        WIDTH // 2 - 150,
        280,
        300,
        60,
        "START GAME"
    )

    instruction_button = Button(
        WIDTH // 2 - 150,
        360,
        300,
        60,
        "INSTRUCTIONS"
    )

    exit_button = Button(
        WIDTH // 2 - 150,
        440,
        300,
        60,
        "EXIT"
    )

    start_button.draw()
    instruction_button.draw()
    exit_button.draw()

    high_score_text = font.render(
        f"High Score: {high_score}",
        True,
        YELLOW
    )

    high_score_rect = high_score_text.get_rect(
        center=(WIDTH // 2, 540)
    )

    screen.blit(
        high_score_text,
        high_score_rect
    )

    return start_button, instruction_button, exit_button

# --------------------------------------------------
# PAUSE
# --------------------------------------------------

def draw_pause():

    overlay = pygame.Surface(
        (WIDTH, HEIGHT),
        pygame.SRCALPHA
    )

    overlay.fill((0, 0, 0, 180))

    screen.blit(overlay, (0, 0))

    title = font_title.render(
        "PAUSED",
        True,
        WHITE
    )

    rect = title.get_rect(
        center=(WIDTH // 2, 180)
    )

    screen.blit(title, rect)

    resume_button = Button(
        WIDTH // 2 - 150,
        300,
        300,
        60,
        "RESUME"
    )

    menu_button = Button(
        WIDTH // 2 - 150,
        380,
        300,
        60,
        "MAIN MENU"
    )

    resume_button.draw()
    menu_button.draw()

    return resume_button, menu_button

# --------------------------------------------------
# GAME OVER
# --------------------------------------------------

def draw_game_over():

    screen.fill(BLACK)

    title = font_title.render(
        "GAME OVER",
        True,
        RED
    )

    title_rect = title.get_rect(
        center=(WIDTH // 2, 130)
    )

    screen.blit(title, title_rect)

    score_text = font_medium.render(
        f"Score: {score}",
        True,
        WHITE
    )

    score_rect = score_text.get_rect(
        center=(WIDTH // 2, 230)
    )

    screen.blit(score_text, score_rect)

    wave_text = font_medium.render(
        f"Wave Reached: {wave}",
        True,
        WHITE
    )

    wave_rect = wave_text.get_rect(
        center=(WIDTH // 2, 280)
    )

    screen.blit(wave_text, wave_rect)

    high_text = font_medium.render(
        f"High Score: {high_score}",
        True,
        YELLOW
    )

    high_rect = high_text.get_rect(
        center=(WIDTH // 2, 330)
    )

    screen.blit(high_text, high_rect)

    restart_button = Button(
        WIDTH // 2 - 150,
        420,
        300,
        60,
        "RESTART"
    )

    menu_button = Button(
        WIDTH // 2 - 150,
        500,
        300,
        60,
        "MAIN MENU"
    )

    restart_button.draw()
    menu_button.draw()

    return restart_button, menu_button

# --------------------------------------------------
# MAIN GAME LOOP
# --------------------------------------------------

running = True

while running:

    clock.tick(FPS)

    # ----------------------------------------------
    # EVENTS
    # ----------------------------------------------

    for event in pygame.event.get():

        if event.type == pygame.QUIT:

            running = False

        # ------------------------------------------
        # MENU EVENTS
        # ------------------------------------------

        if game_state == MENU:

            if event.type == pygame.MOUSEBUTTONDOWN:

                start_button, instruction_button, exit_button = draw_menu()

                if start_button.clicked():

                    start_game()

                    game_state = GAME

                elif instruction_button.clicked():

                    game_state = INSTRUCTIONS

                elif exit_button.clicked():

                    running = False

        # ------------------------------------------
        # INSTRUCTIONS EVENTS
        # ------------------------------------------

        elif game_state == INSTRUCTIONS:

            if event.type == pygame.MOUSEBUTTONDOWN:

                back_button = draw_instructions()

                if back_button.clicked():

                    game_state = MENU

            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_ESCAPE:

                    game_state = MENU

        # ------------------------------------------
        # GAME EVENTS
        # ------------------------------------------

        elif game_state == GAME:

            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_ESCAPE:

                    game_state = PAUSE

                elif event.key == pygame.K_g:

                    use_grenade()

            if event.type == pygame.MOUSEBUTTONDOWN:

                if event.button == 1:

                    bullet = player.shoot(
                        *pygame.mouse.get_pos()
                    )

                    if bullet:

                        bullets.append(bullet)

        # ------------------------------------------
        # PAUSE EVENTS
        # ------------------------------------------

        elif game_state == PAUSE:

            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_ESCAPE:

                    game_state = GAME

            if event.type == pygame.MOUSEBUTTONDOWN:

                resume_button, menu_button = draw_pause()

                if resume_button.clicked():

                    game_state = GAME

                elif menu_button.clicked():

                    game_state = MENU

        # ------------------------------------------
        # GAME OVER EVENTS
        # ------------------------------------------

        elif game_state == GAME_OVER:

            if event.type == pygame.MOUSEBUTTONDOWN:

                restart_button, menu_button = draw_game_over()

                if restart_button.clicked():

                    start_game()

                    game_state = GAME

                elif menu_button.clicked():

                    game_state = MENU

    # ------------------------------------------------
    # DRAW MENU
    # ------------------------------------------------

    if game_state == MENU:

        draw_menu()

    # ------------------------------------------------
    # DRAW INSTRUCTIONS
    # ------------------------------------------------

    elif game_state == INSTRUCTIONS:

        draw_instructions()

    # ------------------------------------------------
    # GAME LOGIC
    # ------------------------------------------------

    elif game_state == GAME:

        draw_background()

        player.update()

        current_time = pygame.time.get_ticks()

        # --------------------------------------------
        # SPAWN ZOMBIES
        # --------------------------------------------

        spawn_delay = max(
            250,
            1000 - wave * 30
        )

        if (
            current_time - last_zombie_spawn >= spawn_delay
            and zombies_spawned < wave_zombies_remaining
        ):

            spawn_zombie()

            last_zombie_spawn = current_time

        # --------------------------------------------
        # SPAWN POWERUPS
        # --------------------------------------------

        if current_time - last_powerup_spawn > 8000:

            x = random.randint(50, WIDTH - 50)
            y = random.randint(50, HEIGHT - 50)

            powerups.append(
                PowerUp(x, y)
            )

            last_powerup_spawn = current_time

        # --------------------------------------------
        # UPDATE BULLETS
        # --------------------------------------------

        for bullet in bullets:

            bullet.update()

        # --------------------------------------------
        # UPDATE ZOMBIES
        # --------------------------------------------

        for zombie in zombies:

            zombie.update(player)

        # --------------------------------------------
        # BULLET-ZOMBIE COLLISION
        # --------------------------------------------

        for bullet in bullets:

            if not bullet.active:
                continue

            for zombie in zombies:

                distance = distance_between(
                    bullet.x,
                    bullet.y,
                    zombie.x,
                    zombie.y
                )

                if distance < bullet.radius + zombie.radius:

                    zombie.health -= 1

                    bullet.active = False

                    play_sound(hit_sound)

                    if zombie.health <= 0:

                        score += zombie.points

                    break

        # --------------------------------------------
        # REMOVE DEAD ZOMBIES
        # --------------------------------------------

        zombies = [
            zombie
            for zombie in zombies
            if zombie.health > 0
        ]

        # --------------------------------------------
        # REMOVE INACTIVE BULLETS
        # --------------------------------------------

        bullets = [
            bullet
            for bullet in bullets
            if bullet.active
        ]

        # --------------------------------------------
        # POWERUP COLLECTION
        # --------------------------------------------

        active_powerups = []

        for powerup in powerups:

            if powerup.expired():

                continue

            distance = distance_between(
                player.x,
                player.y,
                powerup.x,
                powerup.y
            )

            if distance < player.radius + powerup.radius:

                collect_powerup(powerup)

            else:

                active_powerups.append(powerup)

        powerups = active_powerups

        # --------------------------------------------
        # WAVE COMPLETE
        # --------------------------------------------

        if (
            zombies_spawned >= wave_zombies_remaining
            and len(zombies) == 0
        ):

            next_wave()

        # --------------------------------------------
        # GAME OVER
        # --------------------------------------------

        if player.health <= 0:

            if score > high_score:

                high_score = score

                save_high_score(high_score)

            play_sound(gameover_sound)

            game_state = GAME_OVER

        # --------------------------------------------
        # DRAW POWERUPS
        # --------------------------------------------

        for powerup in powerups:

            powerup.draw()

        # --------------------------------------------
        # DRAW BULLETS
        # --------------------------------------------

        for bullet in bullets:

            bullet.draw()

        # --------------------------------------------
        # DRAW ZOMBIES
        # --------------------------------------------

        for zombie in zombies:

            zombie.draw()

        # --------------------------------------------
        # DRAW PLAYER
        # --------------------------------------------

        player.draw()

        # --------------------------------------------
        # HUD
        # --------------------------------------------

        draw_hud()

        # --------------------------------------------
        # WAVE MESSAGE
        # --------------------------------------------

        if (
            current_time - wave_start_time < 2000
        ):

            wave_text = font_big.render(
                f"WAVE {wave}",
                True,
                WHITE
            )

            wave_rect = wave_text.get_rect(
                center=(WIDTH // 2, HEIGHT // 2 - 100)
            )

            screen.blit(
                wave_text,
                wave_rect
            )

    # ------------------------------------------------
    # PAUSE SCREEN
    # ------------------------------------------------

    elif game_state == PAUSE:

        draw_pause()

    # ------------------------------------------------
    # GAME OVER SCREEN
    # ------------------------------------------------

    elif game_state == GAME_OVER:

        draw_game_over()

    # ------------------------------------------------
    # UPDATE DISPLAY
    # ------------------------------------------------

    pygame.display.flip()

pygame.quit()