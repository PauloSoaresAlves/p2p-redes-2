#TCP Socket Client
import socket
import glob
import json
import os

def conectar_servidor(server_end):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.connect(server_end)
    response = server_socket.recv(1024).decode()
    if(response):
        print(response)
        paths = glob.glob("./shared/*.txt")
        files = list(map(os.path.basename,paths))
        server_socket.send(("1|"+json.dumps({'data':files})).encode())

    return server_socket

def desconectar_servidor(server_socket):
    server_socket.send("2|".encode())
    response = server_socket.recv(1024).decode()
    print(response)
    server_socket.close()

def requerer_lista_arquivos(server_socket):
    server_socket.send("3|".encode())
    response = server_socket.recv(1024).decode()
    print("Lista de clientes conectados e seus arquivos:\n", response)

if __name__ == '__main__':
    server_end = ('localhost', 5445)
    server_socket = conectar_servidor(server_end)

    while True:
        print("Selecione uma das seguintes opções:")
        print("1 - Listar arquivos disponíveis")
        print("2 - Desconectar do servidor")
        user_input = input()
        if (user_input == "1"):
            requerer_lista_arquivos(server_socket)
        elif (user_input == "2"):
            desconectar_servidor(server_socket)
            break
        else:
            print("Opção selecionada não é valida!")



#1 - Connect
#2 - Disconnect
#3 - List
#4 - Add
