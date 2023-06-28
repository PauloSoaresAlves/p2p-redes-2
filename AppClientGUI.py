#TCP Socket Client
import io
import queue
import socket
import glob
import json
import os
import threading
import time
import PySimpleGUI as sg
import pyaudio
import soundfile as sf
import wave
from pydub import AudioSegment

class client_persist():
    def __init__(self,id):
        self.id = id
        self.paused = False
        self.lock = threading.Lock()
        self.song = ""

def conectar_servidor(server_end,client_instance: client_persist):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.connect(server_end)
    response = server_socket.recv(1024).decode('utf-8')
    if(response):
        types = (f'./shared_{client_instance.id}/*.mp3', f'./shared_{client_instance.id}/*.wav', f'./shared_{client_instance.id}/*.ogg')
        musicfiles = []
        for files in types:
            for file in glob.glob(files):
                musicfiles.append(os.path.basename(file))

        server_socket.send(("1|"+json.dumps({'data':musicfiles})).encode())

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
    response = server_socket.recv(1024).decode('utf-8')
    server_socket.close()
    layout = [[sg.Text(response)],[sg.Button("Fechar")]]

    desconectado = sg.Window('desconectar',layout,size=(180, 80))
    while True:
        eventos , valores = desconectado.read()
        if eventos == sg.WIN_CLOSED:
            break
        elif eventos == "Fechar":
                
            desconectado.close()

def requerer_lista_arquivos(server_socket: socket.socket, listener_port: str):
    server_socket.send("3|".encode())
    response = server_socket.recv(1024).decode('utf-8')

    clients = json.loads(response)
    
    #Inicia a GUI de lista de arquivos
    table = []
    toprow = ['Nó', 'Arquivo']

    for client in clients:
        for file in client[1]:
            table.append([client[0],file])

    def firstElem(elem):
        return elem[0]
    
    table.sort(key=firstElem)
   
    tbl = sg.Table(values=table, headings=toprow,
        auto_size_columns=True,
        display_row_numbers=False,
        justification='center', key='-TABLE-',
        selected_row_colors='red on yellow',
        enable_events=True,
        expand_x=True,
        expand_y=True,
        enable_click_events=True)

    layout = [[sg.Text("Lista de clientes conectados e seus arquivos:")],
               [tbl],
              [sg.Button("Fechar")]]
    arquivos = sg.Window("Arquivos",layout,size=(750, 300), element_justification='c')

    #Roda a GUI de Lista de Arquivos
    while True:
        eventos , valores = arquivos.read()
        if eventos == sg.WIN_CLOSED:
            break
        elif eventos == "Fechar":
            arquivos.close()
        elif eventos == "-TABLE-":
            requerer_arquivo(table[valores['-TABLE-'][0]],listener_port)
            sg.popup(f"Now playing: {table[valores['-TABLE-'][0]][1]}")

def requerer_arquivo(row: list, listener_port: str):
    message = f"{listener_port}|{row[1]}"
    server_end = (row[0][0], row[0][1])
    client_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_server.sendto(message.encode(), server_end)

                        
def recieve_audio(my_address, my_port,client_instance: client_persist):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.setsockopt(socket.SOL_SOCKET,socket.SO_RCVBUF,65536)
    client_socket.bind((my_address, my_port))
    pa = pyaudio.PyAudio()
    CHUNK = 65536
    q = queue.Queue()
    stream = pa.open(format=pyaudio.paInt16,
                channels=2,
                rate=48000,
                output=True)
    while True:
        data, addr = (client_socket.recvfrom(1024))
        decoded_data = data.decode()
        if decoded_data == "O arquivo requisitado não está mais presente":
            sg.popup(decoded_data)
            continue
        else:
            song_config = json.loads(decoded_data)
            stream = pa.open(format=pyaudio.paInt16,
                channels=song_config['channels'],
                rate=song_config['sample_rate'],
                output=True)
            while True:
                data, addr = (client_socket.recvfrom(CHUNK))
                if not data:
                    break
                if (q.qsize() > 25):
                    stream.write(q.get())
                q.put(data)
        

def listen_client(my_address, my_port,client_instance: client_persist):
    client_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_server.setsockopt(socket.SOL_SOCKET,socket.SO_RCVBUF,65536)
    client_server.bind((my_address, my_port))
    while True:
        data, addr = client_server.recvfrom(1024)
        reciever_port, filename = data.decode().split("|")
        if filename not in os.listdir(f'./shared_{client_instance.id}'):
            client_server.sendto("O arquivo requisitado não está mais presente".encode(),(addr[0], int(reciever_port)))
            continue
        else:
            if filename.endswith(".mp3"):
                mp3_data = open(f"./shared_{client_instance.id}/{filename}", 'rb').read()
                audio_segment = AudioSegment.from_mp3(io.BytesIO(mp3_data))
                wav_data = audio_segment.export(format='wav').read()
            else:
                wav_data = open(f"./shared_{client_instance.id}/{filename}", 'rb').read()
            wv = wave.open(io.BytesIO(wav_data), 'rb')
            chunk_size = 1024
            sample_rate = wv.getframerate()
            channels = wv.getnchannels()
            client_server.sendto(json.dumps({'channels':channels,'sample_rate':sample_rate}).encode(),(addr[0], int(reciever_port)))
            while True:
                chunk= wv.readframes(chunk_size)
                client_server.sendto(chunk,(addr[0], int(reciever_port)))
                time.sleep(0.7*chunk_size/sample_rate)
        

def start_client():
    #Cria a pasta de arquivos compartilhados
    dir = os.listdir("./")
    if "shared_1" not in dir:
        client_instance = client_persist(1) 
        os.mkdir(f"./shared_{client_instance.id}")
    else:
        client_instance = client_persist(int(dir[-1].split("_")[1]))
    try:
        os.mkdir(f"./shared_{client_instance.id+1}")
    except:
        pass

    #Layout Inicial da GUI
    layout = [[sg.VPush()],
              [sg.Text("Insira o IP e a Porta do Servidor no formato IP:PORTA")],
            [sg.Input('', enable_events=True, key='-INPUT-', font=('Arial Bold', 20), expand_x=True, justification='left')],
            [sg.Text("", key="error_text", text_color="#FF6600")],
            [sg.Button('Ok', key='-OK-', font=('Arial Bold', 20)),
            sg.Button('Exit', font=('Arial Bold', 20))],
            [sg.VPush()]]
    
    #inicia a GUI de conexão ao server
    window = sg.Window('Server Connection', layout, size=(750, 300), element_justification='c')
    error_text = window["error_text"]
    
    #Roda a GUI de conexão ao server
    server_socket = None
    while server_socket == None:
        event, values = window.read()
        ip,port = ["",""]
        listener_port = ""
        if event == '-OK-':
            try:  
                ip,port = values["-INPUT-"].split(":")
                server_end = (ip, int(port))
                server_socket = conectar_servidor(server_end, client_instance)
                my_address=server_socket.getsockname()
                listener_port = str(my_address[1])[1:]
                client_listener_thread = threading.Thread(target=listen_client, args=(my_address[0], my_address[1],client_instance))
                client_listener_thread.daemon = True
                client_listener_thread.start()
                client_reciever_thread = threading.Thread(target=recieve_audio, args=(my_address[0], int(listener_port),client_instance))
                client_reciever_thread.daemon = True
                client_reciever_thread.start()
                window.close()
            except ValueError:
                error_text.update(f"Erro: IP ou porta do servidor são invalidos!")
            except:
                error_text.update(f"Erro: não foi possível se conectar a {ip}:{port}!")
        elif event == sg.WIN_CLOSED or event == 'Exit':
            window.close()
            break
     
    conectado = True
    if server_socket != None:

        #Roda a GUI de Opções do cliente
        while conectado:
            layout = [[sg.Text("Escolha uma das opções")],
                      [sg.VPush()],
                      [sg.Button("Listar arquivos disponíveis")],
                      [sg.Button("Desconectar do servidor")],
                      [sg.VPush()]]
            window = sg.Window("Choose Action", layout,size=(750, 300), element_justification='c')
            eventos , valores = window.read()
            if eventos == sg.WIN_CLOSED:
                desconectar_servidor(server_socket)
                break
            elif eventos == "Listar arquivos disponíveis":
                window.close()
                requerer_lista_arquivos(server_socket,listener_port)
            elif eventos == "Desconectar do servidor":
                window.close()
                desconectar_servidor(server_socket)
                conectado = False

if __name__ == '__main__':
    start_client()
        
