import numpy as np
import pygame
from pygame.version import ver
import os

# pygame setup
pygame.init()
screen = pygame.display.set_mode((1920, 1080))

from src.env import load_assets
load_assets()

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
from src.dqn import DQNAgent

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
background_img = pygame.image.load("sprites/backgrounds/background-day.png").convert_alpha()
background_img = pygame.transform.scale(background_img, (1920, 1080))
menu_img = pygame.image.load("sprites/backgrounds/message.png").convert_alpha()
game_over_img = pygame.image.load("sprites/backgrounds/gameover.png").convert_alpha()
# --------------------------------------------------------

# Modo de jogo
game_mode = "human"  # "human" ou "competition"

# Agente DQN
agent = None
robot_bird = None
robot_score = 0
robot_pipe_queue = list()
robot_current_pipe = None
robot_timer = 0
robot_t = 0
robot_frame_count = 0

def get_robot_state():
    if len(pipe_queue) > 0:
        next_pipe = pipe_queue[0]
        dist_x = (next_pipe.up_pipe.x - BIRD_X) / screen.get_width()
        pipe_center_y = (next_pipe.up_pipe.y + PIPE_OPEN_SIZE / 2) / screen.get_height()
    else:
        dist_x = 1.0
        pipe_center_y = 0.5
    
    bird_y = robot_bird.pos.y / screen.get_height()
    bird_vel = robot_bird.vert_speed / 1000
    bird_acc = robot_bird.vert_acc / 10000
    
    return np.array([bird_y, bird_vel, bird_acc, dist_x, pipe_center_y], dtype=np.float32)

def load_dqn_agent():
    global agent
    state_size = 5
    action_size = 2
    agent = DQNAgent(state_size, action_size)
    
    # Tenta carregar modelo treinado
    model_path = "models/dqn_model_final.pth"
    if os.path.exists(model_path):
        agent.load(model_path)
        print(f"Modelo DQN carregado: {model_path}")
    else:
        print("Modelo não encontrado, usando agente não treinado")
    
    agent.epsilon = 0  # Sem exploração durante competição

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
                        load_dqn_agent()
                        robot_bird = Bird(screen)
                        robot_pipe_queue.clear()
                        robot_timer = 0
                        robot_t = 0
                        robot_current_pipe = None
                        robot_score = 0
                        robot_frame_count = 0
                        
                elif game_state == PLAYING:
                    if player.alive:
                        player.jump()
            
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
            (screen.get_width(), screen.get_height()),
            pygame.SRCALPHA
        )
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))
        
        # Mostra logo/menu
        menu_rect = menu_img.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2 - 100))
        screen.blit(menu_img, menu_rect)
        
        # Texto de seleção de modo
        mode_text = small_font.render(
            f"Modo: {game_mode.upper()}",
            True,
            (255, 255, 255)
        )
        screen.blit(
            mode_text,
            mode_text.get_rect(
                center=(screen.get_width() // 2, screen.get_height() // 2 + 50)
            )
        )
        
        # Texto de instruções
        instructions = [
            "Pressione 1 - Modo Humano",
            "Pressione 2 - Modo Competição (vs Robô)",
            "Pressione ESPAÇO para iniciar"
        ]
        
        for i, instruction in enumerate(instructions):
            text = small_font.render(
                instruction,
                True,
                (255, 255, 255)
            )
            screen.blit(
                text,
                text.get_rect(
                    center=(screen.get_width() // 2, screen.get_height() // 2 + 100 + i * 40)
                )
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

        # -------------------------------------------------------------------
        # score humano
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
        
        # Modo competição com robô
        if game_mode == "competition" and robot_bird:
            # Atualiza robô
            robot_frame_count += 1
            
            # Ação do robô
            robot_state = get_robot_state()
            robot_action = agent.act(robot_state, training=False)
            
            if robot_action == 1:
                robot_bird.jump()
            
            # Atualiza pássaro robô
            robot_bird.update(screen, dt)
            
            # Usa os MESMOS canos do humano para ambos
            for pipe_q in pipe_queue:
                if robot_bird.alive and robot_bird.started:
                    # Verifica colisão do robô com os canos
                    if pipe_q.check_collision(robot_bird.get_hitbox()):
                        robot_bird.alive = False
                    
                    # Pontuação do robô (usando a mesma lógica do humano)
                    if not pipe_q.scored and pipe_q.up_pipe.x + PIPE_WIDTH < BIRD_X:
                        robot_score += 1
                        pipe_q.scored = True
            
            # Desenha pássaro robô (transparente)
            robot_bird.draw(screen, tint_color=(255, 255, 255, 128))  # Tint branco com transparência
            
            # Score do robô
            robot_score_text = font.render(
                str(robot_score),
                True,
                (255, 100, 100)
            )
            
            screen.blit(
                robot_score_text,
                robot_score_text.get_rect(
                    center=(
                        int(screen.get_width() * 0.85),
                        int(screen.get_height() * 0.20)
                    )
                )
            )
            
        
        # Mostra game over se o pássaro morreu (jogo congelado)
        if not player.alive:
            overlay = pygame.Surface((screen.get_width(), screen.get_height()), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            screen.blit(overlay, (0, 0))
            
            game_over_text = font.render(
                "GAME OVER",
                True,
                (255, 255, 255)
            )
            
            restart_text = small_font.render(
                "Pressione Y para reiniciar | U para voltar ao menu",
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
            
            if game_mode == "competition":
                result_text = small_font.render(
                    f"Humano: {score} | Robô: {robot_score}",
                    True,
                    (255, 255, 255)
                )
                screen.blit(
                    result_text,
                    result_text.get_rect(
                        center=(screen.get_width() // 2, 550)
                    )
                )

    # flip() para atualizar o display
    pygame.display.flip()

    # limita FPS em 60
    # dt diferença de tempo entre último frame. Usado para fisica
    dt = clock.tick(60) / 1000
    t += 1

pygame.quit()
