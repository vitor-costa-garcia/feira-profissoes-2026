import pygame

# Modo debug
DEBUG = False

# Gravidade
G = 2000
# "Gravidade" angular
ANG_G = 1000

# Fricção do ar
AIR_FRIC = 10000
# "Fricção angular" do ar
ANG_AIR_FRIC = 10000

# Intervalo de tempo entre canos (s)
INTERVAL_PIPES_SEC = 2

# Tamanho abertura do cano (px)
PIPE_OPEN_SIZE = 240
# Grossura do cano (px)
PIPE_WIDTH = 150
# Velocidade do cano (px)
PIPE_SPEED = 300
# Intervalo para berturas possíveis dos canos
PIPE_MIN_OPEN_Y = 280
PIPE_MAX_OPEN_Y = 880

# Grossura do pássaro (px)
BIRD_THICK = 40
# Comprimento do pássaro (px)
BIRD_WIDTH = 100
# Posição horizontal que o pássaro fica (px)
BIRD_X = 250

# Sprites Cano
PIPE_IMG_UP = pygame.image.load("sprites/pipe-green.png").convert_alpha()
PIPE_IMG_DOWN = pygame.transform.rotate(PIPE_IMG_UP, 180)

# Sprite pássaro
BIRD_IMG = pygame.image.load("sprites/mascote_uel.png").convert_alpha()
