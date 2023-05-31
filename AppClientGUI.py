#TCP Socket Client
import socket
import glob
import json
import os
import PySimpleGUI as sg

def conectar_servidor(server_end):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.connect(server_end)
    response = server_socket.recv(1024).decode()
    if(response):
        paths = glob.glob("./shared/*.txt")
        files = list(map(os.path.basename,paths))
        server_socket.send(("1|"+json.dumps({'data':files})).encode())

        layout = [[sg.Text(response)],[sg.Button("Continuar")]]
        conectou = sg.Window('Conectado com Servidor',layout,size=(180, 80))
        while True:
            eventos , valores = conectou.read()
            if eventos == sg.WIN_CLOSED:
                break
            elif eventos == "Continuar":
                conectou.close()

    return server_socket

def desconectar_servidor(server_socket):
    server_socket.send("2|".encode())
    response = server_socket.recv(1024).decode()
    server_socket.close()
    layout = [[sg.Text(response)],[sg.Button("Fechar")]]

    desconectado = sg.Window('desconectar',layout,size=(180, 80))
    while True:
        eventos , valores = desconectado.read()
        if eventos == sg.WIN_CLOSED:
            break
        elif eventos == "Fechar":
                
            desconectado.close()

def requerer_lista_arquivos(server_socket):
    server_socket.send("3|".encode())
    response = server_socket.recv(1024).decode()
    layout = [[sg.Text("Lista de clientes conectados e seus arquivos:\n" +  response)],[sg.Button("Fechar")]]
    arquivos = sg.Window("Arquivos",layout)
    while True:
        eventos , valores = arquivos.read()
        if eventos == sg.WIN_CLOSED:
            break
        elif eventos == "Fechar":
            arquivos.close()

if __name__ == '__main__':
    server_end = ('localhost', 5445)
    server_socket = conectar_servidor(server_end)
    conectado = True

    while conectado:
        layout = [[sg.Text("Escolha uma das opções")],[sg.Button("Listar arquivos disponíveis")],[sg.Button("Desconectar do servidor")]]

        inicio = sg.Window('Escolha do cliente',layout,size=(250, 100))
        while True:
            eventos , valores = inicio.read()
            if eventos == sg.WIN_CLOSED:
                break
            elif eventos == "Listar arquivos disponíveis":
                inicio.close()
                requerer_lista_arquivos(server_socket)
            elif eventos == "Desconectar do servidor":
                inicio.close()
                desconectar_servidor(server_socket)
                conectado = False
            


#1 - Connect
#2 - Disconnect
#3 - List
#4 - Add