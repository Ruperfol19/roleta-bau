# Roleta do Baú

Uma roleta de sorteio em Python com um baú no centro. Clique no baú, a roleta gira e você tenta a sorte nos prêmios mais raros. Cada prêmio tem uma animação própria.

Projeto de entretenimento, sem dinheiro real e sem qualquer ligação com a Epic Games ou o Fortnite.

## Conteúdo

| Arquivo | O que faz |
|---|---|
| `roleta_bau.py` | A roleta com baú, 7 prêmios, animações e painel de prêmios |
| `contador_baus.py` | Contador de baús em overlay (janela sempre no topo, com atalhos globais) |
| `bot_roleta.py` | Bot que gira a roleta milhares de vezes, sem animação, e salva os itens |

## Requisitos

- Python 3.8 ou mais novo (com `tkinter`, que já vem no instalador oficial do Python)
- Só o contador precisa de uma biblioteca extra:

```
pip install -r requirements.txt
```

## Roleta

```
python roleta_bau.py
```

Clique no baú para girar. O progresso é salvo em `roleta_save.json`.

| Prêmio | Chance |
|---|---|
| Skin de Ouro | 1 em 1.562.500 |
| Token Dourado | 1 em 137.500 |
| Veículo + Decalque | 1 em 7.813 |
| Picareta ou Mochila | 1 em 568 |
| Música | 1 em 391 |
| Tela de Wallpaper | 1 em 272 |
| Item de Elementais | 1 em 127 |

Cada prêmio é sorteado de forma independente a cada giro, usando `random.SystemRandom`. Se mais de um sair no mesmo giro, vale o mais raro. As chances ficam na lista `PREMIOS` no topo do `roleta_bau.py`.

Para ver todas as animações sem esperar a sorte, mude `TESTE = False` para `TESTE = True` no topo do arquivo e use as teclas de 1 a 7.

## Bot

```
python bot_roleta.py
python bot_roleta.py --giros 137500
python bot_roleta.py --sem-salvar
```

Por padrão faz 14.000 giros sem animação e grava:

- `roleta_save.json`: soma o resultado ao save da roleta
- `bot_itens.json`: lista de todos os itens ganhos, giro a giro
- `bot_relatorio.txt`: relatório da última execução

Feche a roleta antes de rodar o bot, senão ela sobrescreve o save com os números antigos.

## Contador de baús (overlay)

```
python contador_baus.py
python contador_baus.py --total 1234
```

Janela sem borda, sempre no topo, que soma um baú a cada atalho e toca uma animação.

| Tecla | Ação |
|---|---|
| F8 | +1 baú |
| F7 | -1 baú |
| F6 | zera a contagem da sessão |
| F10 | liga/desliga o modo mover (arraste a janela) |
| F12 | fecha o contador |

As teclas podem ser trocadas nas constantes do topo do arquivo. O total e a posição da janela ficam em `contador_baus.json`.

Para aparecer por cima de um jogo, use o modo de janela "Tela cheia em janela" ou "Em janela". No modo "Tela cheia" exclusivo nenhum overlay consegue aparecer. No Windows a janela deixa o mouse atravessar e não rouba o foco. O contador só escuta as teclas e desenha uma janela, sem ler nem alterar o jogo. Em Linux com Wayland os atalhos globais não funcionam.
