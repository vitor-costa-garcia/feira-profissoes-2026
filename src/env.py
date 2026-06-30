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
ANG_AIR_FRIC = 1000

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

# Sprites Cano
PIPE_IMG_UP = pygame.image.load("sprites/backgrounds/pipe-green.png").convert_alpha()
PIPE_IMG_DOWN = pygame.transform.rotate(PIPE_IMG_UP, 180)
#Start img
START_IMG_ORIGINAL = pygame.image.load("sprites/backgrounds/message.png").convert_alpha()
START_IMG = pygame.transform.scale_by(START_IMG_ORIGINAL, 2)
BACKGROUND_IMG = pygame.image.load("sprites/backgrounds/background-main.jpg").convert()
# Carrega a imagem original
GAMEOVER_IMG = pygame.image.load("sprites/backgrounds/gameover.png").convert_alpha()

# Pega o tamanho original da imagem
largura_original = GAMEOVER_IMG.get_width()
altura_original = GAMEOVER_IMG.get_height()
escala = 3
novo_tamanho = (int(largura_original * escala), int(altura_original * escala))
GAMEOVER_IMG = pygame.transform.scale(GAMEOVER_IMG, novo_tamanho)

