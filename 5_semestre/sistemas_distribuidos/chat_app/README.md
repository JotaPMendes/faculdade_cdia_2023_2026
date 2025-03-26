# Chat TCP/UDP - Trabalho de Redes

Esse é um projeto de chat que eu fiz pra mostrar como funciona a comunicação em rede usando TCP e UDP no Python. É bem legal pra entender como as mensagens são enviadas pela internet!

## O que você precisa ter instalado

- Python 3.6 ou mais novo
- Só bibliotecas que já vêm com o Python (socket, threading, json, random)

## Arquivos do projeto

- `tcp_server.py`: O servidor TCP (mais confiável)
- `udp_server.py`: O servidor UDP (mais rapidinho)
- `client.py`: O programa que você usa pra conversar

## O que dá pra fazer

- Conversar com várias pessoas ao mesmo tempo
- Mandar mensagem pra todo mundo do chat
- Ver quando alguém entra ou sai
- Escolher se quer usar TCP ou UDP
- Interface simples no terminal

## Como usar

1. Primeiro, liga o servidor TCP:
```bash
python tcp_server.py
```

2. Depois, em outro terminal, liga o servidor UDP:
```bash
python udp_server.py
```

3. Pra conversar, abre mais terminais e roda:
```bash
# Se quiser usar TCP (mais confiável):
python client.py tcp

# Se quiser usar UDP (mais rápido):
python client.py udp
```

4. Digite seu nome quando pedir

## Comandos do chat

- `quit`: Sai do chat
- Ctrl+C: Fecha o programa
- Qualquer outra coisa que você digitar: Manda como mensagem

## Diferença entre TCP e UDP 

- **TCP (porta 5000)**: 
  - É tipo uma ligação telefônica
  - Garante que a mensagem chega
  - As mensagens chegam na ordem certa
  - É mais lento, mas mais seguro
  - Melhor pra coisas importantes

- **UDP (porta 5001)**:
  - É tipo mandar uma carta
  - Não garante que chega
  - As mensagens podem chegar fora de ordem
  - É mais rápido!
  - Melhor pra jogos e chamadas de vídeo

## Detalhes técnicos

- Usa threads pra conversar com várias pessoas
- Tem locks pra evitar problemas
- Portas aleatórias no UDP (50000-60000)
- Mensagens em formato JSON
- Trata os erros direitinho

## Observações importantes

- TCP usa a porta 5000
- UDP usa a porta 5001
- Roda no seu próprio PC (localhost)
- Dá pra usar em rede mudando o host
- UDP usa portas aleatórias pra não dar conflito
- O servidor guarda quem tá online

## Deu problema? Tenta assim:

1. Vê se os servidores tão rodando
2. Checa se ninguém tá usando as portas
3. Tenta reiniciar os servidores
4. Confere se tá na pasta certa
5. Vê se digitou tcp ou udp certinho depois do arquivo
