#TCP Socket Client
import socket

def register_server(server_address):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(server_address)

    client_socket.send("REGISTER".encode())
    response = client_socket.recv(1024).decode()
    print(response)

    return client_socket

def unregister_server(client_socket):
    client_socket.send("QUIT".encode())
    response = client_socket.recv(1024).decode()
    print(response)
    client_socket.close()

def request_server_list(client_socket):
    client_socket.send("LIST".encode())
    response = client_socket.recv(1024).decode()
    print("Lista de clientes conectados e seus arquivos:\n", response)

if __name__ == '__main__':
    server_address = ('localhost', 5445)
    client_socket = register_server(server_address)

    while True:
        user_input = input("Digite 'list' para solicitar a lista de clientes ou 'quit' para encerrar: ")
        if user_input == "list":
            request_server_list(client_socket)
        elif user_input == "quit":
            unregister_server(client_socket)
            break