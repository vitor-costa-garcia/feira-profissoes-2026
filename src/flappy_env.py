from collections import deque

import numpy as np
import pygame

from src.bird import Bird
from src.env import *
from src.pipe import Pipe


class FlappyEnv:
    def __init__(self, screen):
        self.screen = screen
        if screen:
            load_assets()  # Garante que assets estão carregados
        self.reset()

    def reset(self):
        self.bird = Bird(self.screen)
        self.pipe_queue = deque()
        self.score = 0
        self.timer = 0
        self.t = 0
        self.current_pipe = None
        self.done = False
        self.frame_count = 0
        self.jump_cooldown = 0

        # 🔥 APAGUE A CRIAÇÃO DO PRIMEIRO CANO AQUI!
        # Deixe o ambiente totalmente limpo. O primeiro cano
        # nascerá naturalmente no loop do step() abaixo.

        return self.get_state()

    def get_state(self):
        screen_height = self.screen.get_height() if self.screen else 1080
        screen_width = self.screen.get_width() if self.screen else 1920

        bird_y = self.bird.pos.y
        bird_y_norm = np.clip(bird_y / screen_height, 0.0, 1.0)

        # Clip velocity/acc so a spike never sends the network an out-of-range value.
        max_vert_speed = getattr(self.bird, "MAX_VERT_SPEED", 1000)
        bird_vel_norm = np.clip(self.bird.vert_speed / max_vert_speed, -1.0, 1.0)

        # Find the pipe(s) genuinely still ahead of the bird, not just queue[0].
        # 🔥 CORREÇÃO: Mantém o foco no cano até que a CAUDA do pássaro tenha passado completamente
        # Subtraímos 50 pixels (ou a largura do pássaro) para garantir uma margem de segurança.

        SAFE_MARGIN = 50
        upcoming = [
            p
            for p in self.pipe_queue
            if p.up_pipe.x + PIPE_WIDTH >= (BIRD_X - SAFE_MARGIN)
        ]
        next_pipe = upcoming[0] if len(upcoming) > 0 else None
        next_next_pipe = upcoming[1] if len(upcoming) > 1 else None

        def pipe_features(pipe):
            if pipe is None:
                # No pipe visible yet -> neutral/safe sentinel values.
                return (1.0, 0.0, 0.0)
            dist_x = np.clip((pipe.up_pipe.x - BIRD_X) / screen_width, -1.0, 1.0)
            gap_top = pipe.pipe_opening - PIPE_OPEN_SIZE / 2
            gap_bottom = pipe.pipe_opening + PIPE_OPEN_SIZE / 2
            # >0 means bird is above the gap top (too high), <0 means below it (fine/needs care)
            dist_to_gap_top = np.clip((bird_y - gap_top) / screen_height, -1.0, 1.0)
            # >0 means bird is below the gap bottom (too low, will hit pipe/ground)
            dist_to_gap_bottom = np.clip(
                (bird_y - gap_bottom) / screen_height, -1.0, 1.0
            )
            return (dist_x, dist_to_gap_top, dist_to_gap_bottom)

        dist_x1, gap_top1, gap_bottom1 = pipe_features(next_pipe)
        dist_x2, gap_top2, gap_bottom2 = pipe_features(next_next_pipe)

        return np.array(
            [
                bird_y_norm,
                bird_vel_norm,
                dist_x1,
                gap_top1,
                gap_bottom1,  # next pipe: how far, and position relative to gap edges
                dist_x2,
                gap_top2,
                gap_bottom2,  # pipe after that: lets the agent plan ahead
            ],
            dtype=np.float32,
        )

    def step(self, action):
        # action: 0 = não pular, 1 = pular
        self.frame_count += 1

        MAX_FRAMES_WITHOUT_START = 180  # ~3 segundos a 60fps
        if not self.bird.started and self.frame_count >= MAX_FRAMES_WITHOUT_START:
            self.done = True
            self.bird.alive = False

        if action == 1:
            self.bird.jump()

        # 1. Salva o score atual para calcular o ganho real de pontos depois
        old_score = self.score

        # Atualiza pássaro
        dt = 1 / 60
        self.bird.update(self.screen, dt)

        # 🔥 MODIFICAÇÃO: Checagem do Teto Letal
        # Se o pássaro tocar ou passar do topo (Y <= 0), ele morre imediatamente
        if self.bird.pos.y <= 0:
            self.bird.pos.y = 0
            self.bird.alive = False
            self.done = True

        # Verifica se o pássaro morreu (chão)
        if not self.bird.alive:
            self.done = True

        # Cria novos canos
        if self.frame_count % 60 == 0:  # A cada 2 segundos
            if self.timer % INTERVAL_PIPES_SEC == 0 and (
                self.bird.alive and self.bird.started
            ):
                new_pipe = Pipe(self.screen)
                self.pipe_queue.append(new_pipe)
            self.timer += 1

        # Atualiza canos
        for pipe_q in self.pipe_queue:
            if self.bird.alive and self.bird.started:
                pipe_q.update(dt)

                # Verifica colisão
                if pipe_q.check_collision(self.bird.get_hitbox()):
                    self.done = True
                    self.bird.alive = False

                # Pontuação
                if not pipe_q.scored and pipe_q.up_pipe.x + PIPE_WIDTH < BIRD_X:
                    self.score += 1
                    pipe_q.scored = True

        # Remove canos que saíram da tela
        if len(self.pipe_queue) > 0 and self.pipe_queue[0].finished:
            self.pipe_queue.popleft()

        # 🔥 LÓGICA DE RECOMPENSA CORRIGIDA (Equilíbrio do PPO)
        reward = 0.01  # Recompensa baixa por frame para evitar o vício de sobrevivência

        if self.done:
            reward = -20.0  # Penalidade forte por bater no teto, cano ou chão
        elif self.score > old_score:
            reward = 25.0  # GANHO ÚNICO: Dá o bônus apenas no frame exato em que cruza o cano

        return self.get_state(), reward, self.done, self.score

    def render(self):
        self.screen.fill("#4dbeff")

        for pipe_q in self.pipe_queue:
            pipe_q.draw(self.screen)

        self.bird.draw(self.screen)

        pygame.display.flip()
