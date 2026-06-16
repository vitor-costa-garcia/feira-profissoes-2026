import numpy as np
import pygame

from src.env import (
    AIR_FRIC,
    ANG_AIR_FRIC,
    ANG_G,
    BIRD_THICK,
    BIRD_WIDTH,
    BIRD_X,
    DEBUG,
    G,
)


class Bird:
    def __init__(self, screen):
        self.alive = True
        self.started = False

        self.pos = pygame.Vector2(BIRD_X, screen.get_height() / 2 - BIRD_THICK)
        self.vert_speed = 0
        self.vert_acc = G
        self.ang_speed = 0
        self.ang_acc = ANG_G
        self.angle = 0

        self.frames = [
            pygame.image.load("sprites/birds/benedito/benedito-upflap.png").convert_alpha(),
            pygame.image.load("sprites/birds/benedito/benedito-midflap.png").convert_alpha(),
            pygame.image.load("sprites/birds/benedito/benedito-downflap.png").convert_alpha(),
        ]

    def update(self, screen, dt):
        if self.started:
            # Atualizando aceleração e velocidade angular
            self.ang_acc = max(-ANG_G, self.ang_acc - dt * ANG_AIR_FRIC)
            self.ang_speed += self.ang_acc * dt
            # Atualização da rotação
            self.angle = max(-30, self.angle + (self.ang_speed * dt))

            # Atualizando aceleração e velocidade vertical
            self.vert_acc = max(G, self.vert_acc + dt * AIR_FRIC)
            self.vert_speed += self.vert_acc * dt

            # Atualização da posição vertical
            self.pos.y += self.vert_speed * dt + (self.vert_acc * (dt**2)) / 2

        # Mata o passaro se cair no chão
        if self.pos.y >= screen.get_height() - BIRD_THICK:
            self.pos.y = screen.get_height() - BIRD_THICK
            self.alive = False

        # Impede que o pássaro voe para fora da tela
        if self.pos.y <= 40:
            self.pos.y = 40
            self.vert_speed = -50

    def jump(self):
        self.started = True

        # Vertical
        self.vert_speed = -700
        self.vert_acc = -13000

        # Angulos
        self.ang_speed = 10
        self.ang_acc = 10
        self.angle = 30

    def draw(self, screen):
        # Animação simples
        if self.vert_speed < -150:
            bird_img = self.frames[0]
        elif self.vert_speed > 150:
            bird_img = self.frames[2]
        else:
            bird_img = self.frames[1]

        # rect_surface = pygame.Surface((BIRD_WIDTH, BIRD_THICK), pygame.SRCALPHA)
        # rect_surface.fill("red")

        scaled_bird = pygame.transform.scale(bird_img, (BIRD_WIDTH, BIRD_THICK))
        
        # Rotaciona a imagem do pássaro conforme  ele cai ou pula e pega o retângulo para hitbox
        rotated_surface = pygame.transform.rotate(scaled_bird, self.angle)
        rotated_player = rotated_surface.get_rect(center=self.pos)

        # Exibe pássaro na tela
        screen.blit(rotated_surface, rotated_player)

        # Ajuste da hitbox do player
        tighter_hitbox = rotated_player.inflate(-15, -30)
        self.hitbox = tighter_hitbox

        if DEBUG:
            # Hitbox ajustada (USADA DE FATO)
            pygame.draw.rect(screen, (0, 0, 255), tighter_hitbox, 2)

            # Retângulo do player
            pygame.draw.rect(screen, (255, 0, 0), rotated_player, 2)

            pygame.draw.rect(screen, (255, 0, 0), rotated_player, 2)

        
