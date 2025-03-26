import socket
import json
import threading
import sys
import random

class ChatClient:
    def __init__(self, host='localhost', tcp_port=5000, udp_port=5001):
        self.host = host # Iniciar o host
        self.tcp_port = tcp_port # Iniciar a porta TCP
        self.udp_port = udp_port # Iniciar a porta UDP
        self.username = None # Iniciar o nome de usuário
        self.tcp_socket = None # Iniciar o socket TCP
        self.udp_socket = None # Iniciar o socket UDP
        self.protocol = None # Iniciar o protocolo
        # Porta local aleatória para o cliente UDP
        self.local_port = random.randint(50000, 60000)

    def connect(self, protocol='tcp'):
        self.protocol = protocol.lower()
        
        try:
            if self.protocol == 'tcp':
                self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Criar o socket TCP
                self.tcp_socket.connect((self.host, self.tcp_port)) # Conectar ao servidor TCP
                print(f"Conectado ao servidor TCP em {self.host}:{self.tcp_port}") # Exibir a conexão
            else:
                self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # Criar o socket UDP
                # Vincular o socket UDP a uma porta local
                self.udp_socket.bind(('', self.local_port))
                print(f"Conectado ao servidor UDP em {self.host}:{self.udp_port}") # Exibir a conexão

            # Solicitar nome de usuário
            self.username = input("Digite seu nome de usuário: ")

            # Se for UDP, enviar uma mensagem inicial para registrar no servidor
            if self.protocol == 'udp':
                data = json.dumps({
                    'username': self.username,
                    'content': 'entrou no chat'
                })
                self.udp_socket.sendto(data.encode('utf-8'), (self.host, self.udp_port))

            # Iniciar thread para receber mensagens
            receive_thread = threading.Thread(target=self.receive_messages)
            receive_thread.daemon = True
            receive_thread.start()

            # Loop principal para enviar mensagens 
            self.send_messages()

        except Exception as e:
            print(f"Erro ao conectar: {e}")
            self.disconnect()

    def send_messages(self):
        while True:
            try:
                message = input()
                if message.lower() == 'quit': # Validação para sair do chat
                    break

                data = json.dumps({
                    'username': self.username,
                    'content': message
                })

                if self.protocol == 'tcp':
                    self.tcp_socket.send(data.encode('utf-8'))
                else:
                    self.udp_socket.sendto(
                        data.encode('utf-8'),
                        (self.host, self.udp_port)
                    )

            except Exception as e:
                print(f"Erro ao enviar mensagem: {e}")
                break

        self.disconnect()

    def receive_messages(self):
        while True:
            try:
                if self.protocol == 'tcp':
                    data = self.tcp_socket.recv(1024).decode('utf-8')
                else:
                    data, _ = self.udp_socket.recvfrom(1024)
                    data = data.decode('utf-8')

                if not data:
                    break

                message = json.loads(data)
                print(f"{message['username']}: {message['message']}")

            except Exception as e:
                print(f"Erro ao receber mensagem: {e}")
                break

        self.disconnect()

    def disconnect(self):
        if self.tcp_socket:
            self.tcp_socket.close()
        if self.udp_socket:
            self.udp_socket.close()
        print("Desconectado do servidor")
        sys.exit()

if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1].lower() not in ['tcp', 'udp']:
        print("Uso: python client.py [tcp|udp]")
        sys.exit(1)

    client = ChatClient()
    client.connect(sys.argv[1])