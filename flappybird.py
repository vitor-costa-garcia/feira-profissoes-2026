import numpy as np
import pygame
from pygame.version import ver

# pygame setup
pygame.init()
screen = pygame.display.set_mode((1920, 1080))

# fontes
font = pygame.font.Font(
    "fonts/PressStart2P-Regular.ttf",
    48
)

small_font = pygame.font.Font(
    "fonts/PressStart2P-Regular.ttf",
    24
)

from src.bird import Bird
from src.env import *
from src.pipe import Pipe

player = Bird(screen)
clock = pygame.time.Clock()

# Variáveis pygame ---------------------------------------
running = True  # Jogo ligado
debug = True
dt = 0  # Fração de tempo entre frames frame (começa em 0)
t = 0  # Contador de frames (Reseta a cada 60)
timer = 0  # Contador de segundos
score = 0
# --------------------------------------------------------

# Variáveis lógica do jogo -------------------------------
pipe_queue = list()
current_pipe = None
# --------------------------------------------------------

while running:
    # Preenchimento da tela (fundo)
    screen.fill("#4dbeff")
   
    # Event listener-------------------------
    for event in pygame.event.get():
        # Botão X da tela
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            # Pulo
            if event.key == pygame.K_SPACE:

                if player.alive:
                    player.jump()

                else:
                    player = Bird(screen)

                    pipe_queue.clear()

                    timer = 0
                    t = 0
                    current_pipe = None
                    score = 0

    # --------------------------------------

    # Atualiza e exibe o pássaro -------------------
    player.update(screen, dt)
    player.draw(screen)
    # ----------------------------------------------

    # Loop de tempo (executa a cada 1 segundo) -----------------------
    if t % 60 == 0:
        if timer % INTERVAL_PIPES_SEC == 0 and (player.alive and player.started):
            # Cria um cano e adiciona na fila de canos
            new_pipe = Pipe(screen)
            pipe_queue.append(new_pipe)

        # Incrementa o temporizador e reseta o contador de ticks
        timer += 1
        t = 0
    # -----------------------------------------------------------------

    # Atualização dos canos -------------------------------------------
    for pipe_q in pipe_queue:
        if player.alive and player.started:
            # Atualiza a posição dos canos
            pipe_q.update(dt)

            # Verifica se houve colisão do pássaro com o cano
            if pipe_q.check_collision(player.hitbox):
                print("COLISÃO!")
                print("score:", score)
                player.alive = False
            
            if (
                not pipe_q.scored
                and pipe_q.up_pipe.x + PIPE_WIDTH < BIRD_X
            ):
                score += 1
                pipe_q.scored = True

        # Exibe os canos na tela
        pipe_q.draw(screen)

    # Remove os canos que saem da tela
    current_pipe = None
    if len(pipe_queue) > 0:
        if pipe_queue[0].finished:
            pipe_queue.pop(0)

        for pip in pipe_queue:
            if pip.up_pipe.x + PIPE_WIDTH + 50 > BIRD_X:
                current_pipe = pip
                break

        # Distancia atual até o proximo cano relevante
        # print(current_pipe.up_pipe.x)

    # -------------------------------------------------------------------
    # score
    score_text = font.render(
        str(score),
        True,
        (255, 255, 255)
    )

    screen.blit(
    score_text,
    score_text.get_rect(
        center=(
            int(screen.get_width() * 0.85),
            int(screen.get_height() * 0.13)
        )
    )
    )    
        
    # texto de game over
    if not player.alive:
        overlay = pygame.Surface(
            (screen.get_width(), screen.get_height()),
            pygame.SRCALPHA
        )

        overlay.fill((0, 0, 0, 150))

        screen.blit(overlay, (0, 0))

        game_over_text = font.render(
            "GAME OVER",
            True,
            (255, 255, 255)
        )

        restart_text = small_font.render(
            "Pressione ESPAÇO para reiniciar",
            True,
            (255, 255, 255)
        )

        screen.blit(
            game_over_text,
            game_over_text.get_rect(
                center=(screen.get_width() // 2, 400)
            )
        )

        screen.blit(
            restart_text,
            restart_text.get_rect(
                center=(screen.get_width() // 2, 500)
            )
        )
    
    # flip() para atualizar o display
    pygame.display.flip()

    # limita FPS em 60
    # dt diferença de tempo entre último frame. Usado para fisica
    dt = clock.tick(60) / 1000
    t += 1

pygame.quit()
