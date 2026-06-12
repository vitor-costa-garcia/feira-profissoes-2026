# Example file showing a circle moving on screen
import numpy as np
import pygame
from pygame.version import ver

# pygame setup
pygame.init()
screen = pygame.display.set_mode((1920, 1080))
clock = pygame.time.Clock()
running = True
dt = 0
t = 0
timer = 0

G = 2000
ANG_G = 1000
AIR_FRIC = 10000
ANG_AIR_FRIC = 10000
INTERVAL_PIPES_SEC = 2
PIPE_OPEN_SIZE = 240
PIPE_WIDTH = 150
PIPE_SPEED = 300

BIRD_THICK = 60
BIRD_WIDTH = 100

pipe_opening_y = 360
player_speed = 0
player_acc = G
pipe_queue = list()

player_ang_speed = 10
player_ang_acc = -10000
player_angle = 0
player_alive = True
player_started = False
current_pipe = None

player_pos = pygame.Vector2(200, screen.get_height() / 2 - BIRD_THICK)


class Pipe:
    def __init__(self, screen, pipe_opening_y):
        self.up_pipe = pygame.Rect(
            screen.get_width(),
            0,
            PIPE_WIDTH,
            pipe_opening_y - PIPE_OPEN_SIZE / 2,
        )
        self.down_pipe = pygame.Rect(
            screen.get_width(), pipe_opening_y + PIPE_OPEN_SIZE / 2, PIPE_WIDTH, 1000
        )

        self.finished = False

    def update(self, dt):
        self.up_pipe.x -= PIPE_SPEED * dt
        self.down_pipe.x -= PIPE_SPEED * dt

        if self.up_pipe.x <= -PIPE_WIDTH:
            self.finished = True

    def draw(self, screen):
        # Bottom pipe
        bottom_pipe_scaled = pygame.transform.scale(
            pipe_img, (self.down_pipe.width, self.down_pipe.height)
        )

        # Top pipe (rotated 180°)
        top_pipe_scaled = pygame.transform.scale(
            pipe_img_up, (self.up_pipe.width, self.up_pipe.height)
        )

        screen.blit(top_pipe_scaled, self.up_pipe.topleft)
        screen.blit(bottom_pipe_scaled, self.down_pipe.topleft)

    def check_collision(self, player_rect):
        if (player_rect.x + BIRD_WIDTH < self.up_pipe.x) or (
            player_rect.x > self.up_pipe.x + PIPE_WIDTH
        ):
            return False

        return self.up_pipe.colliderect(player_rect) or self.down_pipe.colliderect(
            player_rect
        )


player_image = pygame.image.load("sprites/mascote_uel.png").convert_alpha()
pipe_img = pygame.image.load("sprites/pipe-green.png").convert_alpha()
pipe_img_up = pygame.transform.rotate(pipe_img, 180)

while running:
    # poll for events
    # pygame.QUIT event means the user clicked X to close your window
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # fill the screen with a color to wipe away anything from last frame
    screen.fill("#4dbeff")

    # ----------- PLAYER
    rect_surface = pygame.Surface((BIRD_WIDTH, BIRD_THICK), pygame.SRCALPHA)
    rect_surface.fill("red")

    if player_started:
        player_ang_acc = max(-ANG_G, player_ang_acc - dt * ANG_AIR_FRIC)
        player_ang_speed += player_ang_acc * dt
        player_angle = max(-30, player_angle + (player_ang_speed * dt))

    rotated_surface = pygame.transform.rotate(player_image, player_angle)

    rotated_player = rotated_surface.get_rect(center=player_pos)

    screen.blit(rotated_surface, rotated_player)
    # -------------

    # Pipe spawning loop
    if t % 60 == 0:
        if timer % INTERVAL_PIPES_SEC == 0 and player_alive and player_started:
            # Chooses a random opening point
            pipe_opening_y = np.random.randint(200, 600)

            # Creates a new pipe and adds it to the queue
            new_pipe = Pipe(screen, pipe_opening_y)
            pipe_queue.append(new_pipe)

        timer += 1
        t = 0
        print(timer)

    # Updates all pipes position and draws them to screen
    for pipe_q in pipe_queue:
        if player_alive and player_started:
            # Pipes only move if player is still alive
            pipe_q.update(dt)
            if pipe_q.check_collision(rotated_player):
                print("COLISÃO!")
                player_alive = False

        # Draws the pipes onto the screem
        pipe_q.draw(screen)

    # Delete pipes out of the screen
    if len(pipe_queue) > 0:
        if pipe_queue[0].finished:
            pipe_queue.pop(0)

    # Key listener for jump
    keys = pygame.key.get_pressed()
    if keys[pygame.K_b] and player_alive:
        player_started = True
        player_speed = -300
        player_acc = -12000
        player_ang_acc = 10
        player_angle = 30
        player_ang_speed = 10

    if player_started:
        player_speed += player_acc * dt
        player_pos.y += player_speed * dt + (player_acc * (dt**2)) / 2
        player_acc = max(G, player_acc + dt * AIR_FRIC)

    if player_pos.y >= screen.get_height() - BIRD_THICK:
        player_pos.y = screen.get_height() - BIRD_THICK
        player_alive = False

    if player_pos.y <= 40:
        player_pos.y = 40
        player_speed = -50

    # flip() the display to put your work on screen
    pygame.display.flip()

    # limits FPS to 60
    # dt is delta time in seconds since last frame, used for framerate-
    # independent physics.
    dt = clock.tick(60) / 1000
    t += 1

pygame.quit()
