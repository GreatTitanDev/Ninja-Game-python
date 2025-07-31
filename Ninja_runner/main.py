import pygame, random, json, math
from pygame.locals import *

# Constants
WIDTH, HEIGHT = 700, 400
GROUND_OFFSET = 50
FPS = 60
PLAYER_HEIGHT = 100
JUMP_STRENGTH = 12
GRAVITY = 0.5
MAX_JUMPS = 2
INITIAL_SPEED = 4.0
SPEED_INCREMENT = 0.6
SPEED_INCREASE_RATE = 2  # every 2 points
MAX_SPEED = 15

# Init
pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("The Ninja")
clock = pygame.time.Clock()

# Load Sounds
def load_sound(path):
    try:
        return pygame.mixer.Sound(path)
    except:
        return None

jump_sound = load_sound('sound/jump.wav')
hurt_sound = load_sound(f'sound/{random.choice(["hurt.wav", "hurt1.wav"])}')
lose_sound = load_sound('sound/lose.wav')
bg_sound = load_sound('sound/background.mp3')
if bg_sound: bg_sound.play(-1)

# Load Score
def get_score():
    try:
        with open('score.json', 'r') as f:
            return json.load(f).get('highscore', 0)
    except:
        return 0

def save_score(score):
    try:
        with open('score.json', 'w') as f:
            json.dump({'highscore': score}, f)
    except:
        pass

# Player class
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.x, self.y = 25, HEIGHT - PLAYER_HEIGHT - GROUND_OFFSET
        self.vel_y = 0
        self.jumps_left = MAX_JUMPS
        self.action = 'running'
        self.health = 3
        self.inv_frames = 0
        self.run_sprites = self.load_sprites('images/player/run', 'run', 10)
        self.jump_sprites = self.load_sprites('images/player/jump', 'jump', 10)
        self.index = 0
        self.image = self.run_sprites[0]
        self.rect = self.image.get_rect(topleft=(self.x, self.y))

    def load_sprites(self, folder, prefix, count):
        sprites = []
        for i in range(count):
            img = pygame.image.load(f"{folder}/{prefix}{i}.png").convert_alpha()
            scale = PLAYER_HEIGHT / img.get_height()
            img = pygame.transform.scale(img, (int(img.get_width() * scale), int(img.get_height() * scale)))
            sprites.append(img)
        return sprites

    def update(self):
        self.index = (self.index + 0.2) % 10
        sprite_list = self.run_sprites if self.action == 'running' else self.jump_sprites
        self.image = sprite_list[int(self.index)]

        self.vel_y += GRAVITY
        self.y += self.vel_y

        if self.y >= HEIGHT - PLAYER_HEIGHT - GROUND_OFFSET:
            self.y = HEIGHT - PLAYER_HEIGHT - GROUND_OFFSET
            self.vel_y = 0
            self.jumps_left = MAX_JUMPS
            self.action = 'running'
        else:
            self.action = 'jumping'

        self.rect.topleft = (self.x, self.y)

    def draw(self):
        if self.inv_frames > 0:
            self.inv_frames -= 1
            if self.inv_frames % 10 < 5:
                return
        screen.blit(self.image, self.rect)

    def jump(self):
        if self.jumps_left > 0:
            self.vel_y = -JUMP_STRENGTH
            self.jumps_left -= 1
            if jump_sound: jump_sound.play()

# Obstacle class
class Obstacle(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.images = [pygame.transform.scale(pygame.image.load(f'images/obstacle/ob{i}.png').convert_alpha(), (50, 50)) for i in range(12)]
        self.image = random.choice(self.images)
        self.x = WIDTH
        self.y = HEIGHT - self.image.get_height() - GROUND_OFFSET
        self.rect = self.image.get_rect(topleft=(self.x, self.y))

    def update(self, speed):
        self.x -= speed
        self.rect.topleft = (self.x, self.y)

    def draw(self):
        screen.blit(self.image, (self.x, self.y))

    def reset(self):
        self.image = random.choice(self.images)
        self.x = WIDTH

# Backgrounds
sky = pygame.image.load('images/city/1.png').convert_alpha()
bg_layers = [pygame.image.load(f'images/city/{i}.png').convert_alpha() for i in range(2, 6)]
bg_layers.append(pygame.image.load('images/city/new_city.png').convert_alpha())
parallax_offsets = [0] * len(bg_layers)
bg_tiles = math.ceil(WIDTH / sky.get_width())

# Heart UI
heart_sprites = [pygame.transform.scale(pygame.image.load(f'images/heart/heart{i}.png').convert_alpha(), (30, 30)) for i in range(8)]
heart_index = 0

# Game State
player = Player()
obstacle = Obstacle()
obstacle_group = pygame.sprite.Group(obstacle)
score = 0
speed = INITIAL_SPEED
running = True

# Game Loop
while running:
    clock.tick(FPS)
    screen.fill((0, 0, 0))

    for e in pygame.event.get():
        if e.type == QUIT:
            running = False
        elif e.type == KEYDOWN and e.key == K_SPACE:
            player.jump()

    for i in range(bg_tiles):
        screen.blit(sky, (i * sky.get_width(), 0))
    for i, bg in enumerate(bg_layers):
        for j in range(bg_tiles):
            screen.blit(bg, (j * bg.get_width() + parallax_offsets[i], 0))
        parallax_offsets[i] -= i + 1
        if abs(parallax_offsets[i]) > bg.get_width():
            parallax_offsets[i] = 0

    player.update()
    player.draw()
    obstacle.update(speed)
    obstacle.draw()

    if obstacle.x < -obstacle.image.get_width():
        score += 1
        obstacle.reset()
        if score % SPEED_INCREASE_RATE == 0 and speed < MAX_SPEED:
            speed += SPEED_INCREMENT

    if player.rect.colliderect(obstacle.rect) and player.inv_frames == 0:
        player.health -= 1
        player.inv_frames = 30
        if hurt_sound: hurt_sound.play()
        obstacle.reset()

    heart_sprite = heart_sprites[int(heart_index) % len(heart_sprites)]
    for i in range(player.health):
        screen.blit(heart_sprite, (10 + i * 40, 10))
    heart_index += 0.1

    font = pygame.font.Font(None, 28)
    score_text = font.render(f"Score: {score}", True, (0, 0, 0))
    screen.blit(score_text, (WIDTH - 120, 10))
    high = get_score()
    high_text = font.render(f"High: {max(score, high)}", True, (0, 0, 0))
    screen.blit(high_text, (WIDTH - 120, 35))

    font = pygame.font.Font(None, 20)
    ethiopia_text = font.render("</> Made with love in Ethiopia Dev: Nimona E.</>", True, (255, 255, 255))
    screen.blit(ethiopia_text, (220, 5))

    pygame.display.update()

    while player.health <= 0:
        if bg_sound: bg_sound.set_volume(0)
        if lose_sound: lose_sound.play()
        screen.blit(pygame.image.load('images/bg/new_bg.jpg'), (0, 0))
        over_font = pygame.font.Font(None, 64)
        small_font = pygame.font.Font(None, 32)

        game_over_text = over_font.render("GAME OVER!", True, (255, 0, 0))
        text = small_font.render("Press SPACE to play again.", True, (0, 0, 0))
        high_text = small_font.render(f"High Score: {max(score, high)}", True, (0,0,0))

        screen.blit(game_over_text, game_over_text.get_rect(center=(WIDTH//2, 100)))
        screen.blit(text, text.get_rect(center=(WIDTH//2, 160)))
        screen.blit(high_text, high_text.get_rect(center=(WIDTH//2, 200)))
        font = pygame.font.Font(None, 22)
        text = font.render("</> Developer: Nimona Engida. </>", True, (255, 255, 255))
        screen.blit(text, text.get_rect(center=(WIDTH//2, 389)))
        pygame.display.update()

        if score > high:
            save_score(score)

        for e in pygame.event.get():
            if e.type == QUIT:
                running = False
                player.health = 1
            elif e.type == KEYDOWN and e.key == K_SPACE:
                player = Player()
                obstacle = Obstacle()
                obstacle_group = pygame.sprite.Group(obstacle)
                score = 0
                speed = INITIAL_SPEED
                if bg_sound: bg_sound.set_volume(1.0)
                lose_sound.set_volume(0)

pygame.quit()