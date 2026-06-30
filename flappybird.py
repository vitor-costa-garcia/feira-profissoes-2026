import numpy as np
import pygame
from pygame.version import ver

# pygame setup
pygame.init()
screen = pygame.display.set_mode((1920, 1080))

# fontes
font = pygame.font.Font("fonts/PressStart2P-Regular.ttf", 48)
small_font = pygame.font.Font("fonts/PressStart2P-Regular.ttf", 24)

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

# --- OTIMIZAÇÃO: Criando o filtro escuro apenas UMA vez aqui fora ---
overlay = pygame.Surface((screen.get_width(), screen.get_height()), pygame.SRCALPHA)
overlay.fill((0, 0, 0, 150)) # Cor Preta com 150 de opacidade (Alpha)
# -------------------------------------------------------------------

# Variáveis lógica do jogo -------------------------------
pipe_queue = list()
current_pipe = None
# --------------------------------------------------------


while running:
    # Preenchimento da tela (fundo)
    screen.blit(BACKGROUND_IMG, (0, 0))
    
    # Event listener-------------------------
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                # Se o jogo ainda não começou, inicia ele ao pressionar ESPAÇO
                if not player.started:
                    player.started = True
                elif player.alive:
                    player.jump()
                else:
                    player = Bird(screen)
                    pipe_queue.clear()
                    timer = 0
                    t = 0
                    current_pipe = None
                    score = 0
    # --------------------------------------

   
    if player.started:
        player.update(screen, dt)
        player.draw(screen)
    # ----------------------------------------------

    # Loop de tempo (executa a cada 1 segundo) -----------------------
    if t % 60 == 0:
        if timer % INTERVAL_PIPES_SEC == 0 and (player.alive and player.started):
            new_pipe = Pipe(screen)
            pipe_queue.append(new_pipe)

        timer += 1
        t = 0
    # -----------------------------------------------------------------

    # Atualização dos canos -------------------------------------------
    for pipe_q in pipe_queue:
        if player.alive and player.started:
            pipe_q.update(dt)

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

    # -------------------------------------------------------------------
    # Modificado: O score agora só é renderizado e desenhado se o jogo começou
    if player.started:
        score_text = font.render(str(score), True, (255, 255, 255))
        screen.blit(
            score_text,
            score_text.get_rect(
                center=(int(screen.get_width() * 0.85), int(screen.get_height() * 0.13))
            )
        )    
        
    # Tela de início (Aparece apenas quando não iniciado)
    if not player.started:
        screen.blit(overlay, (0, 0))
        screen.blit(START_IMG, START_IMG.get_rect(center=(screen.get_width() // 2, 500)))
        
    # texto de game over
    if not player.alive and player.started:
        # CORRIGIDO: Desenha o filtro escuro que criamos lá fora
        screen.blit(overlay, (0, 0))

        screen.blit(GAMEOVER_IMG, GAMEOVER_IMG.get_rect(center=(screen.get_width() // 2, 300)))
       
        restart_text = small_font.render("Pressione o espaço para reiniciar", True, (255, 255, 255))

        
        screen.blit(
            restart_text,
            restart_text.get_rect(center=(screen.get_width() // 2, 500))
        )
    
    # flip() para atualizar o display
    pygame.display.flip()

    # limita FPS em 60
    dt = clock.tick(60) / 1000
    t += 1

pygame.quit()