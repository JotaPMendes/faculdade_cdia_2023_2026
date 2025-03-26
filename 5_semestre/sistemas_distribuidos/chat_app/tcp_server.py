import socket
import threading
import json

class TCPServer:
    def __init__(self, host='localhost', port=5000):
        self.host = host  # Iniciar o host
        self.port = port  # Iniciar a porta
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Criar o servidor TCP = SOCK_STREAM
        self.clients = {} # Dicionário que armazena informações dos clientes
        self.lock = threading.Lock() # Garantir consistência ao acessar o dicionário de clientes (ex: thread 1 lê, thread 2 escreve)

    def start(self):
        self.server_socket.bind((self.host, self.port)) # Associar o servidor ao endereço e porta
        self.server_socket.listen(5) # Colocar o servidor para atender somente 5 conexões
        print(f"Servidor TCP iniciado em {self.host}:{self.port}") # Iniciar o servidor

        while True:
            client_socket, address = self.server_socket.accept() # Aceitar uma nova conexão
            print(f"Nova conexão de {address}") # Exibir o endereço do cliente
            
            # Criar thread para cada cliente
            client_thread = threading.Thread(
                target=self.handle_client, 
                args=(client_socket, address)
            )
            client_thread.start() # Iniciar a thread
            
            # Armazenar informações do cliente
            with self.lock:
                self.clients[address] = {
                    'socket': client_socket,
                    'username': f"Usuário_{len(self.clients)}" # Criar um nome de usuário único para o cliente
                }

    def handle_client(self, client_socket, address):
        try:
            while True:
                # Receber mensagem do cliente
                data = client_socket.recv(1024).decode('utf-8')
                if not data:
                    break

                # Processar mensagem
                message = json.loads(data)
                username = self.clients[address]['username']
                
                self.broadcast_message(username, message['content'])
                
        except Exception as e:
            print(f"Erro ao processar mensagem: {e}")
        finally:
            self.remove_client(address)

    def broadcast_message(self, username, message):
        with self.lock:
            for client in self.clients.values():
                try:
                    response = json.dumps({
                        'username': username,
                        'message': message
                    })
                    client['socket'].send(response.encode('utf-8'))
                except:
                    continue

    def remove_client(self, address):
        with self.lock:
            if address in self.clients:
                self.clients[address]['socket'].close()
                del self.clients[address]
                print(f"Cliente {address} desconectado")

if __name__ == "__main__":
    server = TCPServer()
    server.start()