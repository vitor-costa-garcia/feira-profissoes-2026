import numpy as np
from src.flappy_env import FlappyEnv
from src.dqn import DQNAgent


def train_dqn(episodes=1000, render=False):
    # Inicializa pygame apenas se for renderizar
    screen = None
    if render:
        import pygame
        from src.env import load_assets
        pygame.init()
        screen = pygame.display.set_mode((1920, 1080))
        pygame.display.set_caption("Treinamento DQN - Flappy Bird")
        load_assets()
    
    # Cria ambiente e agente
    env = FlappyEnv(screen)
    state_size = 4  # [bird_y, bird_vel, dist_x, pipe_center_y]
    action_size = 2  # [0: não pular, 1: pular]
    agent = DQNAgent(state_size, action_size)
    
    # Métricas
    scores = []
    episode_rewards = []
    
    print("Iniciando treinamento DQN...")
    print(f"Episódios: {episodes}")
    print(f"Dispositivo: {agent.device}")
    
    for episode in range(episodes):
        try:
            state = env.reset()
            total_reward = 0
            done = False
            step_count = 0
            
            while not done:
                step_count += 1
                # Seleciona ação
                action = agent.act(state, training=True)
                
                # Executa ação
                next_state, reward, done, score = env.step(action)
                total_reward += reward
                
                # Armazena experiência
                agent.remember(state, action, reward, next_state, done)
                
                # Treina
                loss = agent.train()
                
                state = next_state
                
                # Safety: limita steps por episódio
                if step_count > 10000:
                    print(f"Episódio {episode} excedeu limite de steps ({step_count})")
                    done = True
                
                # Renderiza apenas se habilitado
                if render and episode % 10 == 0:
                    env.render()
                    pygame.event.pump()
        except Exception as e:
            print(f"Erro no episódio {episode}: {e}")
            import traceback
            traceback.print_exc()
            break
        
        scores.append(score)
        episode_rewards.append(total_reward)
        
        # Atualiza rede target a cada 10 episódios
        if episode % 10 == 0:
            agent.update_target_network()
        
        # Salva modelo a cada 50 episódios
        if episode % 50 == 0 and episode > 0:
            agent.save(f"models/dqn_model_{episode}.pth")
            print(f"Modelo salvo: dqn_model_{episode}.pth")
        
        # Progresso
        if episode % 10 == 0:
            avg_score = np.mean(scores[-10:])
            avg_reward = np.mean(episode_rewards[-10:])
            print(f"Episódio {episode}/{episodes} | Score: {score} | Média: {avg_score:.2f} | Recompensa: {total_reward:.2f} | Epsilon: {agent.epsilon:.3f}")
    
    # Salva modelo final
    agent.save("models/dqn_model_final.pth")
    print("Treinamento concluído! Modelo salvo: dqn_model_final.pth")
    
    if render:
        import pygame
        pygame.quit()
    
    return agent, scores, episode_rewards


if __name__ == "__main__":
    train_dqn(episodes=500, render=False)
