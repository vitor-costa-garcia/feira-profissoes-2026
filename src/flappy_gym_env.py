"""
Gymnasium wrapper around FlappyEnv so it can be trained with stable-baselines3
(which requires the gymnasium.Env interface, not FlappyEnv's custom step/reset).
"""

import gymnasium as gym
import numpy as np
from gymnasium import spaces

from src.env import BIRD_X, PIPE_OPEN_SIZE, PIPE_WIDTH
from src.flappy_env import FlappyEnv

# Peso da recompensa de formato (shaping) baseada na distância vertical até
# o centro da abertura do próximo cano. Mantido pequeno em relação ao bônus
# de passar um cano (+5) para não incentivar "ficar parado no centro" em vez
# de efetivamente atravessar os canos.
DIST_PENALTY_COEF = 0.3

# Penalidade por pular em dois frames consecutivos. Sem isso, o agente
# pode aprender a "segurar o botão" (pular a cada frame), o que é ótimo
# para a física do jogo mas não se parece nada com um jogador humano, que
# fisicamente não consegue apertar espaço 60x por segundo.
CONSECUTIVE_JUMP_PENALTY = 0.2


class FlappyGymEnv(gym.Env):
    """Thin adapter: FlappyEnv.step/reset -> gymnasium.Env.step/reset."""

    metadata = {"render_modes": ["human"], "render_fps": 60}

    def __init__(self, screen=None, render_mode=None):
        super().__init__()
        self.render_mode = render_mode
        self._env = FlappyEnv(screen)

        state = self._env.reset()
        obs_dim = state.shape[0]

        self.observation_space = spaces.Box(
            low=-1.0, high=1.0, shape=(obs_dim,), dtype=np.float32
        )
        self.action_space = spaces.Discrete(2)  # 0 = não pular, 1 = pular

        self._prev_score = 0

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        state = self._env.reset()

        # Força o pássaro a "começar" imediatamente (gravidade ativa desde o
        # frame 0), igual ao Flappy Bird de verdade. Isso elimina de raiz o
        # exploit de ficar parado -- sem isso, started=False significa que
        # pos.y nunca muda e o pássaro fica invencível (ver Bird.update).
        self._env.bird.started = True

        self._prev_score = 0
        self._prev_action = 0
        return state.astype(np.float32), {}

    def _distance_to_gap_center_penalty(self):
        bird = self._env.bird
        screen = self._env.screen
        screen_height = screen.get_height() if screen else 1080
        screen_width = screen.get_width() if screen else 1920

        upcoming = [
            p for p in self._env.pipe_queue if p.up_pipe.x + PIPE_WIDTH >= BIRD_X
        ]
        if len(upcoming) == 0:
            return 0.0

        next_pipe = upcoming[0]
        gap_center_y = next_pipe.pipe_opening

        # Distância vertical normalizada
        dist_y = abs(bird.pos.y - gap_center_y) / screen_height
        dist_y = float(np.clip(dist_y, 0.0, 1.0))

        # CORREÇÃO: Calcula a distância horizontal para servir de "peso"
        # Quanto mais perto o cano estiver (dist_x perto de 0), maior será a penalidade vertical.
        dist_x = (next_pipe.up_pipe.x - BIRD_X) / screen_width
        dist_x = float(np.clip(dist_x, 0.0, 1.0))
        weight = 1.0 - dist_x  # Inverte: perto = peso 1, longe = peso 0

        return DIST_PENALTY_COEF * dist_y * weight

    def _consecutive_jump_penalty(self, action):
        """
        Penaliza pressionar pular em dois frames seguidos, incentivando um
        padrão de flap mais espaçado e humano em vez de segurar o botão.
        """
        if action == 1 and self._prev_action == 1:
            return CONSECUTIVE_JUMP_PENALTY
        return 0.0

    def step(self, action):
        action = int(action)
        state, _reward, done, score = self._env.step(action)

        score_delta = score - self._prev_score
        self._prev_score = score

        if done:
            # Penalidade de morte muito mais severa para anular os pontos acumulados
            reward = -20.0
        elif score_delta > 0:
            # Bônus massivo por passar o cano (o agente PRECISA desejar isso mais que tudo)
            reward = 25.0 * score_delta
        else:
            # Recompensa por frame reduzida para quase zero.
            # Subtraímos a penalidade de distância apenas quando o cano estiver perto.
            reward = 0.01 - self._distance_to_gap_center_penalty()

        reward -= self._consecutive_jump_penalty(action)
        self._prev_action = action

        terminated = bool(done)
        truncated = False
        info = {"score": score}

        return state.astype(np.float32), float(reward), terminated, truncated, info

    def render(self):
        if self.render_mode == "human":
            self._env.render()

    def close(self):
        pass
