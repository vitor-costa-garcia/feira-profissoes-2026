import numpy as np
import pygame
from collections import deque
from src.bird import Bird
from src.pipe import Pipe
from src.env import *


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
        
        return self.get_state()
    
    def get_state(self):
        # Estado: [posição y do pássaro, velocidade vertical, 
        #          distância horizontal até o próximo cano, 
        #          altura do centro da abertura do cano]
        
        screen_height = self.screen.get_height() if self.screen else 1080
        screen_width = self.screen.get_width() if self.screen else 1920
        
        bird_y = self.bird.pos.y / screen_height
        bird_vel = self.bird.vert_speed / 1000
        
        if len(self.pipe_queue) > 0:
            next_pipe = self.pipe_queue[0]
            dist_x = (next_pipe.up_pipe.x - BIRD_X) / screen_width
            pipe_center_y = (next_pipe.up_pipe.y + PIPE_OPEN_SIZE / 2) / screen_height
        else:
            dist_x = 1.0
            pipe_center_y = 0.5
            
        return np.array([bird_y, bird_vel, dist_x, pipe_center_y], dtype=np.float32)
    
    def step(self, action):
        # action: 0 = não pular, 1 = pular
        self.frame_count += 1
        
        if action == 1:
            self.bird.jump()
            
        # Atualiza pássaro
        dt = 1/60
        self.bird.update(self.screen, dt)
        
        # Verifica se o pássaro morreu (chão)
        if not self.bird.alive:
            self.done = True
        
        # Cria novos canos
        if self.frame_count % 120 == 0:  # A cada 2 segundos
            if self.timer % INTERVAL_PIPES_SEC == 0 and (self.bird.alive and self.bird.started):
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
            
        # Recompensa
        reward = 0.5  # Recompensa por sobreviver (aumentado)
        
        if self.done:
            reward = -10  # Penalidade por morrer (reduzida)
        elif self.score > 0:
            reward = 5  # Bônus por passar por um cano (aumentado)
            
        return self.get_state(), reward, self.done, self.score
    
    def render(self):
        # Desenha o jogo (opcional para treinamento)
        self.screen.fill("#4dbeff")
        
        for pipe_q in self.pipe_queue:
            pipe_q.draw(self.screen)
            
        self.bird.draw(self.screen)
        
        pygame.display.flip()
