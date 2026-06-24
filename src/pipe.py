import numpy as np
import pygame

from src.env import (
    BIRD_WIDTH,
    PIPE_MAX_OPEN_Y,
    PIPE_MIN_OPEN_Y,
    PIPE_OPEN_SIZE,
    PIPE_SPEED,
    PIPE_WIDTH,
)


class Pipe:
    def __init__(self, screen):
        self.scored = False
        self.pipe_opening = np.random.randint(PIPE_MIN_OPEN_Y, PIPE_MAX_OPEN_Y)

        # Calculate exactly where the gap starts and ends to make the math easier to read
        gap_top = self.pipe_opening - PIPE_OPEN_SIZE / 2
        gap_bottom = self.pipe_opening + PIPE_OPEN_SIZE / 2

        # Give both pipes a fixed massive height so the image never stretches differently
        self.fixed_height = 800

        # Screen dimensions
        screen_width = screen.get_width() if screen else 1920

        # Top pipe: Starts way off-screen (-fixed_height) and hangs down to gap_top
        self.up_pipe = pygame.Rect(
            screen_width,
            gap_top - self.fixed_height,
            PIPE_WIDTH,
            self.fixed_height,
        )

        # Bottom pipe: Starts at gap_bottom and goes down
        self.down_pipe = pygame.Rect(
            screen_width, gap_bottom, PIPE_WIDTH, self.fixed_height
        )

        self.finished = False

        # Carrega assets internamente apenas se necessário
        self.top_img = None
        self.bottom_img = None
        if screen:
            pipe_img_up = pygame.image.load("sprites/backgrounds/pipe-green.png").convert_alpha()
            pipe_img_down = pygame.transform.rotate(pipe_img_up, 180)

            # PRO TIP: Scale your images ONCE in __init__ instead of every frame in draw().
            # This saves a ton of CPU power!
            self.top_img = pygame.transform.scale(
                pipe_img_down, (PIPE_WIDTH, self.fixed_height)
            )
            self.bottom_img = pygame.transform.scale(
                pipe_img_up, (PIPE_WIDTH, self.fixed_height)
            )

    def update(self, dt):
        self.up_pipe.x -= PIPE_SPEED * dt
        self.down_pipe.x -= PIPE_SPEED * dt

        if self.up_pipe.x <= -PIPE_WIDTH:
            self.finished = True

    def draw(self, screen):
        # Now you just blit the pre-scaled images directly to the Rects
        screen.blit(self.top_img, self.up_pipe.topleft)
        screen.blit(self.bottom_img, self.down_pipe.topleft)

    def check_collision(self, player_rect):
        if (player_rect.x + BIRD_WIDTH < self.up_pipe.x) or (
            player_rect.x > self.up_pipe.x + PIPE_WIDTH
        ):
            return False

        return self.up_pipe.colliderect(player_rect) or self.down_pipe.colliderect(
            player_rect
        )
