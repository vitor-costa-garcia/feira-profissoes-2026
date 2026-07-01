import os

import numpy as np
import pygame
from pygame.version import ver

# pygame setup
pygame.init()
screen = pygame.display.set_mode((1920, 1080))

from src.env import load_assets

load_assets()

# fontes
font = pygame.font.Font("fonts/PressStart2P-Regular.ttf", 48)

small_font = pygame.font.Font("fonts/PressStart2P-Regular.ttf", 24)

from stable_baselines3 import PPO

from src.bird import Bird
from src.env import *
from src.flappy_env import FlappyEnv
from src.pipe import Pipe

# Estados do jogo
MENU = "menu"
PLAYING = "playing"
GAME_OVER = "game_over"

clock = pygame.time.Clock()

# Variáveis pygame ---------------------------------------
running = True  # Jogo ligado
debug = True
dt = 0  # Fração de tempo entre frames frame (começa em 0)
t = 0  # Contador de frames (Reseta a cada 60)
timer = 0  # Contador de segundos
score = 0
game_state = MENU  # Estado inicial
# --------------------------------------------------------

# Variáveis lógica do jogo -------------------------------
pipe_queue = list()
current_pipe = None
# --------------------------------------------------------

# Assets de menu e game over
background_img = pygame.image.load(
    "sprites/backgrounds/background-day.png"
).convert_alpha()
background_img = pygame.transform.scale(background_img, (1920, 1080))
menu_img = pygame.image.load("sprites/backgrounds/message.png").convert_alpha()
game_over_img = pygame.image.load("sprites/backgrounds/gameover.png").convert_alpha()
# --------------------------------------------------------

# Modo de jogo
game_mode = "human"  # "human" ou "competition"

# Agente PPO
agent = None
robot_bird = None
robot_score = 0
robot_pipe_queue = list()
robot_current_pipe = None
robot_timer = 0
robot_t = 0
robot_frame_count = 0

# Ambiente headless usado APENAS para computar o estado do robô da mesma
# forma exata que foi usado no treinamento (FlappyEnv.get_state()). Seu
# .bird e .pipe_queue são sobrescritos a cada frame para apontar para o
# robot_bird/pipe_queue reais do jogo -- ele nunca chama .step()/.reset()
# durante a partida, é só uma "calculadora" de estado compartilhada.
robot_env = FlappyEnv(None)


def load_ppo_agent():
    global agent

    # Prefere o melhor modelo salvo pelo EvalCallback; usa o final como fallback.
    model_path = "models/best_model.zip"
    if not os.path.exists(model_path):
        print("NAO CARREGOU MELHOR MODELO")
        model_path = "models/ppo_model_final.zip"

    if os.path.exists(model_path):
        agent = PPO.load(model_path)
        print(f"Modelo PPO carregado: {model_path}")
    else:
        agent = None
        print("Modelo PPO não encontrado, robô ficará parado")


while running:
    # Event listener-------------------------
    for event in pygame.event.get():
        # Botão X da tela
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                if game_state == MENU:
                    # Inicia o jogo
                    game_state = PLAYING
                    player = Bird(screen)
                    pipe_queue.clear()
                    timer = 0
                    t = 0
                    current_pipe = None
                    score = 0

                    if game_mode == "competition":
                        load_ppo_agent()
                        robot_bird = Bird(screen)
                        # robot_bird.started = True
                        robot_pipe_queue.clear()
                        robot_timer = 0
                        robot_t = 0
                        robot_current_pipe = None
                        robot_score = 0
                        robot_frame_count = 0

                elif game_state == PLAYING:
                    if player.alive:
                        # 🔥 NOVO: Se o jogo ainda não tinha começado, acorda o robô agora!
                        if (
                            not player.started
                            and game_mode == "competition"
                            and robot_bird
                        ):
                            robot_bird.started = True

                        player.jump()  # O humano dá o pulo dele

            elif event.key == pygame.K_1 and game_state == MENU:
                game_mode = "human"
            elif event.key == pygame.K_2 and game_state == MENU:
                game_mode = "competition"
            elif event.key == pygame.K_y:
                if game_state == PLAYING and not player.alive:
                    # Reinicia o jogo
                    game_state = PLAYING
                    player = Bird(screen)
                    pipe_queue.clear()
                    timer = 0
                    t = 0
                    current_pipe = None
                    score = 0

                    if game_mode == "competition":
                        robot_bird = Bird(screen)
                        # robot_bird.started = True
                        robot_pipe_queue.clear()
                        robot_timer = 0
                        robot_t = 0
                        robot_current_pipe = None
                        robot_score = 0
                        robot_frame_count = 0
            elif event.key == pygame.K_u:
                # Volta para o menu
                game_state = MENU

    # --------------------------------------

    # Desenha fundo
    screen.blit(background_img, (0, 0))

    # MENU STATE
    if game_state == MENU:
        # Overlay escuro
        overlay = pygame.Surface(
            (screen.get_width(), screen.get_height()), pygame.SRCALPHA
        )
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))

        # Mostra logo/menu
        menu_rect = menu_img.get_rect(
            center=(screen.get_width() // 2, screen.get_height() // 2 - 100)
        )
        screen.blit(menu_img, menu_rect)

        # Texto de seleção de modo
        mode_text = small_font.render(
            f"Modo: {game_mode.upper()}", True, (255, 255, 255)
        )
        screen.blit(
            mode_text,
            mode_text.get_rect(
                center=(screen.get_width() // 2, screen.get_height() // 2 + 50)
            ),
        )

        # Texto de instruções
        instructions = [
            "Pressione 1 - Modo Humano",
            "Pressione 2 - Modo Competição (vs Robô)",
            "Pressione ESPAÇO para iniciar",
        ]

        for i, instruction in enumerate(instructions):
            text = small_font.render(instruction, True, (255, 255, 255))
            screen.blit(
                text,
                text.get_rect(
                    center=(
                        screen.get_width() // 2,
                        screen.get_height() // 2 + 100 + i * 40,
                    )
                ),
            )

    # PLAYING STATE
    elif game_state == PLAYING:
        # Preenchimento da tela (fundo)
        screen.fill("#4dbeff")

        # Atualiza e exibe o pássaro humano -------------------
        player.update(screen, dt)
        player.draw(screen)
        # ----------------------------------------------

        # Loop de tempo (executa a cada 1 segundo) -----------------------
        if t % 60 == 0:
            # Volta a depender apenas do humano
            if timer % INTERVAL_PIPES_SEC == 0 and (player.alive and player.started):
                new_pipe = Pipe(screen)
                pipe_queue.append(new_pipe)

            timer += 1
            t = 0
        # -----------------------------------------------------------------

        # Atualização dos canos -------------------------------------------
        for pipe_q in pipe_queue:
            if player.alive and player.started:
                # Canos só se movem se o humano estiver vivo
                pipe_q.update(dt)

            if player.alive and player.started:
                # Verifica colisão humano
                if pipe_q.check_collision(player.hitbox):
                    player.alive = False

                # PONTUAÇÃO HUMANO (Mantém a flag exclusiva)
                if (
                    not getattr(pipe_q, "human_scored", False)
                    and pipe_q.up_pipe.x + PIPE_WIDTH < BIRD_X
                ):
                    score += 1
                    pipe_q.human_scored = True

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

        # -------------------------------------------------------------------
        # score humano
        score_text = font.render(str(score), True, (255, 255, 255))

        screen.blit(
            score_text,
            score_text.get_rect(
                center=(int(screen.get_width() * 0.85), int(screen.get_height() * 0.13))
            ),
        )

        # Modo competição com robô
        if game_mode == "competition" and robot_bird:
            robot_frame_count += 1

            # 🔥 MUDANÇA: O robô só pensa e pula se estiver vivo E o jogo tiver começado
            if agent is not None and robot_bird.alive and robot_bird.started:
                robot_env.bird = robot_bird
                robot_env.pipe_queue = pipe_queue
                robot_state = robot_env.get_state()

                robot_action, _ = agent.predict(robot_state, deterministic=True)
                robot_action = int(robot_action)
            else:
                robot_action = 0

            if robot_action == 1 and robot_bird.alive:
                robot_bird.jump()

            # Atualiza pássaro robô (se estiver morto, a física apenas o fará cair até o chão)
            robot_bird.update(screen, dt)

            # Usa os MESMOS canos do humano para ambos
            for pipe_q in pipe_queue:
                if robot_bird.alive and robot_bird.started:
                    # Verifica colisão do robô com os canos
                    if pipe_q.check_collision(robot_bird.get_hitbox()):
                        robot_bird.alive = False

                    # Pontuação do robô
                    if (
                        getattr(pipe_q, "robot_scored", False) == False
                        and pipe_q.up_pipe.x + PIPE_WIDTH < BIRD_X
                    ):
                        robot_score += 1
                        pipe_q.robot_scored = True

            # 2. Muda a cor do robô e do placar se ele morrer
            if robot_bird.alive:
                bird_tint = (255, 255, 255, 128)  # Transparente normal
                score_color = (255, 100, 100)  # Vermelho vivo
            else:
                bird_tint = (100, 100, 100, 128)  # Escurecido (fantasma)
                score_color = (100, 100, 100)  # Cinza escuro

            robot_bird.draw(screen, tint_color=bird_tint)

            # Score do robô
            robot_score_text = font.render(str(robot_score), True, score_color)
            screen.blit(
                robot_score_text,
                robot_score_text.get_rect(
                    center=(
                        int(screen.get_width() * 0.85),
                        int(screen.get_height() * 0.20),
                    )
                ),
            )

            # 3. Mostra o aviso se o robô morreu
            if not robot_bird.alive:
                warning_text = small_font.render("ROBO ELIMINADO", True, score_color)
                screen.blit(
                    warning_text,
                    warning_text.get_rect(
                        center=(
                            int(screen.get_width() * 0.85),
                            int(
                                screen.get_height() * 0.25
                            ),  # Fica logo abaixo do score do robô
                        )
                    ),
                )

        # Mostra game over se o pássaro morreu (jogo congelado)
        # O Game Over acontece EXCLUSIVAMENTE se o humano morrer.
        if not player.alive:
            overlay = pygame.Surface(
                (screen.get_width(), screen.get_height()), pygame.SRCALPHA
            )
            overlay.fill((0, 0, 0, 150))
            screen.blit(overlay, (0, 0))

            game_over_text = font.render("GAME OVER", True, (255, 255, 255))
            restart_text = small_font.render(
                "Pressione Y para reiniciar | U para voltar ao menu",
                True,
                (255, 255, 255),
            )

            screen.blit(
                game_over_text,
                game_over_text.get_rect(center=(screen.get_width() // 2, 400)),
            )

            screen.blit(
                restart_text,
                restart_text.get_rect(center=(screen.get_width() // 2, 500)),
            )

            if game_mode == "competition":
                result_text = small_font.render(
                    f"Humano: {score} | Robô: {robot_score}", True, (255, 255, 255)
                )
                screen.blit(
                    result_text,
                    result_text.get_rect(center=(screen.get_width() // 2, 550)),
                )

    # flip() para atualizar o display
    pygame.display.flip()

    # limita FPS em 60
    # dt diferença de tempo entre último frame. Usado para fisica
    dt = clock.tick(60) / 1000
    t += 1

pygame.quit()
