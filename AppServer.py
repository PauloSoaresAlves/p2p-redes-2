import socket

# Dicionário para armazenar informações dos clientes
client_info = {}

def register_client(client_socket, client_address):
    client_info[client_address] = []
    print("Novo cliente registrado:", client_address)

def unregister_client(client_socket, client_address):
    if client_address in client_info:
        del client_info[client_address]
        print("Cliente removido:", client_address)

def handle_client_request(client_socket, client_address):
    while True:
        request = client_socket.recv(1024).decode()
        if request == "QUIT":
            unregister_client(client_socket, client_address)
            client_socket.send("Conexão encerrada.".encode())
            client_socket.close()
            break
        elif request == "LIST":
            client_socket.send(str(client_info).encode())

def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('localhost', 5445))
    server_socket.listen(5)

    print("Servidor iniciado. Aguardando conexões...")

    while True:
        client_socket, client_address = server_socket.accept()
        register_client(client_socket, client_address)
        client_socket.send("Registro bem-sucedido.".encode())
        handle_client_request(client_socket, client_address)

if __name__ == '__main__':
    start_server()