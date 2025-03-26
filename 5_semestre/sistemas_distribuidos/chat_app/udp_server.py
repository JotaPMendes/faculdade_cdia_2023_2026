import socket
import json
import threading
import sys

class UDPServer:
    def __init__(self, host='localhost', port=5001):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.clients = {}
        self.lock = threading.Lock()

    def start(self):
        try:
            self.server_socket.bind((self.host, self.port))
            print(f"Servidor UDP iniciado em {self.host}:{self.port}")
            print("Aguardando conexões...")

            # Thread para receber mensagens
            receive_thread = threading.Thread(target=self.receive_messages)
            receive_thread.daemon = True
            receive_thread.start()

            # Manter o servidor rodando
            while True:
                try:
                    input()  # Aguarda entrada do usuário para encerrar
                except KeyboardInterrupt:
                    print("\nEncerrando servidor...")
                    break

        except Exception as e:
            print(f"Erro ao iniciar servidor: {e}")
        finally:
            self.server_socket.close()

    def receive_messages(self):
        while True:
            try:
                data, address = self.server_socket.recvfrom(1024)
                message = json.loads(data.decode('utf-8'))

                # Registrar novo cliente se necessário
                if address not in self.clients:
                    with self.lock:
                        self.clients[address] = message['username']
                    print(f"Novo cliente conectado: {message['username']} ({address})")
                    # Notificar outros clientes
                    self.broadcast_message("Servidor", f"{message['username']} entrou no chat")

                # Broadcast da mensagem para todos os clientes
                if message['content'] != 'entrou no chat':
                    self.broadcast_message(message['username'], message['content'])

            except json.JSONDecodeError:
                print(f"Mensagem inválida recebida de {address}")
            except Exception as e:
                print(f"Erro ao processar mensagem: {e}")

    def broadcast_message(self, username, message):
        with self.lock:
            dead_clients = []
            for address in self.clients:
                try:
                    response = json.dumps({
                        'username': username,
                        'message': message
                    })
                    self.server_socket.sendto(response.encode('utf-8'), address)
                except:
                    dead_clients.append(address)
                    
            # Remover clientes que não estão mais conectados
            for address in dead_clients:
                username = self.clients.pop(address, "Desconhecido")
                print(f"Cliente {username} ({address}) desconectado")
                self.broadcast_message("Servidor", f"{username} saiu do chat")

if __name__ == "__main__":
    server = UDPServer()
    try:
        server.start()
    except KeyboardInterrupt:
        print("\nServidor encerrado.")