import socket
import threading
import json

# Dicionário para armazenar informações dos clientees
cliente_info = {}

def registrar_cliente(socket_cliente, endereco_cliente):
    cliente_info[endereco_cliente] = []
    print("Novo cliente registrado:", endereco_cliente)

def remover_cliente(socket_cliente, endereco_cliente):
    if endereco_cliente in cliente_info:
        del cliente_info[endereco_cliente]
        print("cliente removido:", endereco_cliente)

def handle_cliente_request(socket_cliente, endereco_cliente):
    while True:
        request = socket_cliente.recv(1024).decode().split("|")
        if request[0] == "3":
            remover_cliente(socket_cliente, endereco_cliente)
            socket_cliente.send("Conexão encerrada.".encode())
            socket_cliente.close()
            break
        elif request[0] == "1":
            socket_cliente.send(str(cliente_info).encode())
# parte que atualiza o dicionário de músicas, não sei se funciona
        elif request[0] == "2":
            json_message = json.loads(request[1:])
            lista_musicas = json_message["data"]
            adicionar_conteudo_cliente(endereco_cliente, lista_musicas)

# atualiza a lista das músicas adicionando as novas músicas fornecidas pelo cliente
def adicionar_conteudo_cliente(endereco_cliente, lista_musicas):
    cliente_info[endereco_cliente].extend(lista_musicas)
    print(cliente_info)
            
def start_server():
    socket_servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socket_servidor.bind(('localhost', 5445))
    socket_servidor.listen(5)

    print("Servidor iniciado. Aguardando conexões...")

    while True:
        socket_cliente, endereco_cliente = socket_servidor.accept()
        registrar_cliente(socket_cliente, endereco_cliente)
        socket_cliente.send("Registro bem-sucedido.".encode())
        # Criar uma nova thread para lidar com a conexão do cliente
        thread_cliente = threading.Thread(target=handle_cliente_request, args=(socket_cliente, endereco_cliente))
        thread_cliente.daemon = True
        thread_cliente.start()

if __name__ == '__main__':
    start_server()