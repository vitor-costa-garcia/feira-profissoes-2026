import os
from typing import Callable

import gymnasium as gym
import numpy as np
import torch
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import (
    BaseCallback,
    CheckpointCallback,
    EvalCallback,
)
from stable_baselines3.common.vec_env import SubprocVecEnv, VecMonitor

from src.flappy_gym_env import FlappyGymEnv


class PortugueseLoggingCallback(BaseCallback):
    """
    Callback que imprime o progresso do treinamento no mesmo formato do
    script antigo de DQN (score médio, recompensa média a cada N episódios),
    e opcionalmente renderiza um episódio de demonstração periodicamente.
    """

    def __init__(
        self,
        log_every_episodes=10,
        render_env=None,
        render_every_episodes=10,
        verbose=0,
    ):
        super().__init__(verbose)
        self.log_every_episodes = log_every_episodes
        self.render_env = render_env
        self.render_every_episodes = render_every_episodes
        self.episode_count = 0
        self.scores = []
        self.episode_rewards = []

    def _on_step(self) -> bool:
        for info in self.locals.get("infos", []):
            if "episode" in info:
                self.episode_count += 1
                self.scores.append(info.get("score", 0))
                self.episode_rewards.append(info["episode"]["r"])

                if self.episode_count % self.log_every_episodes == 0:
                    avg_score = np.mean(self.scores[-self.log_every_episodes :])
                    avg_reward = np.mean(
                        self.episode_rewards[-self.log_every_episodes :]
                    )
                    print(
                        f"Episódio {self.episode_count} | "
                        f"Score: {self.scores[-1]} | "
                        f"Média Score: {avg_score:.2f} | "
                        f"Recompensa Média: {avg_reward:.2f} | "
                        f"Timesteps: {self.num_timesteps}"
                    )

                # CORREÇÃO: Renderiza apenas se não estiver travando workers paralelos
                if (
                    self.render_env is not None
                    and self.episode_count % self.render_every_episodes == 0
                ):
                    self._play_render_episode()

        return True

    def _play_render_episode(self):
        import pygame

        obs, _ = self.render_env.reset()
        done = False
        clock = (
            pygame.time.Clock()
        )  # Limita os frames na exibição para visualização humana

        while not done:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    done = True
                    break

            action, _ = self.model.predict(obs, deterministic=True)
            obs, _reward, terminated, truncated, _info = self.render_env.step(action)
            done = done or terminated or truncated
            self.render_env.render()
            pygame.event.pump()
            clock.tick(60)  # Mantém os 60 FPS visuais sem acelerar descontroladamente


def make_env():
    def _init():
        env = FlappyGymEnv(screen=None)
        env = gym.wrappers.TimeLimit(env, max_episode_steps=72000)  # 60s a 60fps
        return env

    return _init


def linear_schedule(initial_value: float) -> Callable[[float], float]:
    """
    Reduz a taxa de aprendizado linearmente de initial_value até 0
    conforme o progresso do treinamento passa de 1.0 (início) para 0.0 (fim).
    """

    def func(progress_remaining: float) -> float:
        return progress_remaining * initial_value

    return func


def train_ppo(
    total_timesteps=2_000_000,
    n_envs=8,
    render=False,
    log_every_episodes=10,
    save_every_timesteps=100_000,
    models_dir="models",
    resume_path=None,  # <--- NOVO ARGUMENTO
):
    os.makedirs(models_dir, exist_ok=True)

    print("Iniciando treinamento PPO...")
    print(f"Timesteps totais: {total_timesteps}")
    print(f"Ambientes paralelos: {n_envs}")

    env = SubprocVecEnv([make_env() for _ in range(n_envs)])
    env = VecMonitor(env)

    # 🔥 NOVO: Cria um ambiente separado exclusivo para as provas (avaliação)
    eval_env = VecMonitor(SubprocVecEnv([make_env() for _ in range(1)]))

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Dispositivo: {device}")

    # 1. LÓGICA DE CARREGAMENTO DO MODELO
    if resume_path is not None and os.path.exists(resume_path):
        print(f"Continuando treinamento a partir de: {resume_path}")
        # Carrega o modelo antigo e vincula o novo ambiente a ele
        model = PPO.load(resume_path, env=env, device=device)
        reset_timesteps = False  # Diz ao logger para continuar a contagem
    else:
        print("Criando um NOVO modelo PPO do zero...")
        model = PPO(
            "MlpPolicy",
            env,
            verbose=0,
            learning_rate=linear_schedule(3e-4),  # <--- APLICA O SCHEDULE AQUI
            n_steps=2048,  # Aumentado (o modelo coleta mais dados antes de atualizar, reduzindo o ruído)
            batch_size=512,  # Aumentado (atualizações de gradiente mais suaves)
            n_epochs=10,
            gamma=0.999,
            gae_lambda=0.95,
            clip_range=0.15,  # Reduzido de 0.2 (impede que a rede mude drasticamente de uma vez)
            ent_coef=0.0003,  # QUASE ZERO! (O agente para de pular aleatoriamente)
            vf_coef=0.5,
            max_grad_norm=0.5,
            policy_kwargs=dict(net_arch=dict(pi=[64, 64], vf=[64, 64])),
            tensorboard_log=os.path.join(models_dir, "tb_logs"),
            device=device,
        )
        reset_timesteps = True

    render_env = None
    if render:
        import pygame

        from src.env import load_assets

        # Inicialização do Pygame de exibição isolada APÓS a criação do SubprocVecEnv
        pygame.init()
        screen = pygame.display.set_mode((1920, 1080))
        pygame.display.set_caption("Treinamento PPO - Flappy Bird")
        load_assets()
        render_env = FlappyGymEnv(screen=screen, render_mode="human")

    logging_callback = PortugueseLoggingCallback(
        log_every_episodes=log_every_episodes,
        render_env=render_env,
        render_every_episodes=log_every_episodes,
    )

    checkpoint_callback = CheckpointCallback(
        save_freq=max(save_every_timesteps // n_envs, 1),
        save_path=models_dir,
        name_prefix="ppo_model",
    )

    # 🔥 NOVO: Configuração do EvalCallback para salvar o melhor modelo
    eval_callback = EvalCallback(
        eval_env,
        best_model_save_path=models_dir,
        log_path=os.path.join(models_dir, "eval_logs"),
        eval_freq=max(50_000 // n_envs, 1),  # Faz uma prova a cada 50.000 timesteps
        n_eval_episodes=5,  # Joga 5 partidas para tirar a média da nota
        deterministic=True,  # Usa a versão focada do cérebro (sem entropia)
        render=False,
    )

    try:
        model.learn(
            total_timesteps=total_timesteps,
            callback=[
                logging_callback,
                checkpoint_callback,
                eval_callback,
            ],  # Adicione o eval_callback aqui!
            progress_bar=True,
            reset_num_timesteps=reset_timesteps,
        )
    except Exception as e:
        print(f"Erro durante o treinamento: {e}")
        import traceback

        traceback.print_exc()

    model.save(os.path.join(models_dir, "ppo_model_final"))
    print("Treinamento concluído! Modelo salvo: ppo_model_final.zip")

    env.close()
    if render_env is not None:
        import pygame

        pygame.quit()

    return model, logging_callback.scores, logging_callback.episode_rewards


if __name__ == "__main__":
    # Para treinar do zero:
    train_ppo(total_timesteps=5_000_000, render=False)

    # Para CONTINUAR o treinamento:
    # train_ppo(
    #     total_timesteps=4_000_000,  # Quantos passos A MAIS você quer treinar
    #     render=False,
    #     resume_path="models/ppo_model_final.zip",  # Ou um arquivo de checkpoint específico
    # )
