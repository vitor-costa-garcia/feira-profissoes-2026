import pygame

# Modo debug
DEBUG = False

# Gravidade
G = 2000
# "Gravidade" angular
ANG_G = 1000

# Fricção do ar
AIR_FRIC = 100
# "Fricção angular" do ar
ANG_AIR_FRIC = 100

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
BIRD_THICK = 50
# Comprimento do pássaro (px)
BIRD_WIDTH = 80
# Posição horizontal que o pássaro fica (px)
BIRD_X = 300

# Sprites Cano (carregados dinamicamente)
PIPE_IMG_UP = None
PIPE_IMG_DOWN = None

def load_assets():
    global PIPE_IMG_UP, PIPE_IMG_DOWN
    if PIPE_IMG_UP is None:
        PIPE_IMG_UP = pygame.image.load("sprites/backgrounds/pipe-green.png").convert_alpha()
        PIPE_IMG_DOWN = pygame.transform.rotate(PIPE_IMG_UP, 180)
