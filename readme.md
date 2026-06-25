# Flappy Bird 🐦

Projeto desenvolvido para a **Feira de Profissões 2026** do curso de **Ciência de Dados e Inteligência Artificial** da Universidade Estadual de Londrina (UEL).

Este projeto consiste na implementação em python do jogo Flappy Bird com a identidade visual da UEL 💚

O projeto busca implementar uma **política treinada com aprendizado por reforço utilizando o algoritmo DQN**, que combina o algoritmo clássico Q-learning com redes neurais artificiais. A ideia é que ouvintes da feira de profissões, público majoritariamente composto por estudantes do ensino médio, possam interagir com a apresentação e competir tanto com o agente treinado, quanto entre seus colegas.

---

## Como rodar 🎮

1 - [Instale o python (na versão 3.12)](https://www.python.org/downloads/release/python-3129/)
![download python 3.12](/sprites/prints/download-py.png)

2 - Clone o repositório

3 - requirements.txt com o comando:

```bash
 py -3.12 -m pip install -r requirements.txt
```

4 - Após instalar as dependências, execute o treinamento: 
```bash
 py -3.12 train_dqn.py
```

O treinamento irá:
- Treinar por 500 episódios (configurável)
- Salvar checkpoints a cada 50 episódios em `models/dqn_model_{episodio}.pth`
- Salvar o modelo final em `models/dqn_model_final.pth`
- Mostrar progresso no console

5 - Após o treinamento, execute o jogo: 
```bash
 py -3.12 flappybird_competition.py       
```

No menu:
- Pressione **1** para modo Humano (jogo normal)
- Pressione **2** para modo Competição (vs Robô DQN)
- Pressione **ESPAÇO** para iniciar


## Estrutura do Projeto ⭐

- `flappybird.py` - Jogo original 
- `flappybird_competition.py` - Jogo com modo de competição (humano vs robô)
- `train_dqn.py` - Script para treinar o agente DQN
- `src/flappy_env.py` - Ambiente do jogo para o agente
- `src/dqn.py` - Implementação do DQN (rede neural, replay memory, agente)
- `models/` - Diretório para salvar modelos treinados

## Como Funciona o DQN 🤖

### Estado (4 valores)
- Posição Y do pássaro (normalizada)
- Velocidade vertical (normalizada)
- Distância horizontal até o próximo cano (normalizada)
- Altura do centro da abertura do cano (normalizada)

### Ações (2)
- 0: Não pular
- 1: Pular

### Recompensa
- +0.1 por frame sobrevivido
- +1.0 por passar por um cano
- -100 por morrer

### Notas

- O modelo treinado pode demorar várias horas para atingir um bom desempenho
- Se não houver modelo treinado, o robô jogará aleatoriamente
- Você pode ajustar o número de episódios em `train_dqn.py`
- O modo competição usa os mesmos canos para ambos os jogadores para justiça