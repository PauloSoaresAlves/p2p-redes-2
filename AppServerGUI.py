import socket
import threading
import json
import PySimpleGUI as sg


class server_persist():
    def __init__(self,endereco,porta):     
      self.clients = {}
      self.log = ""
      self.lock = threading.Lock() #Lock para evitar condições de corrida
      self.endereco = endereco
      self.porta = porta

    #Adição de cliente
    def adicionar_cliente(self,endereco_cliente):
        with self.lock:
            if endereco_cliente not in self.clients.keys():
                self.clients[endereco_cliente] = []
                self.log += f"Cliente adicionado: {endereco_cliente}\n"
                return True
            else:
                self.log += f"Cliente {endereco_cliente} tentou se conectar, porém, já existe na lista de clientes\n"
                return False
            
    #Conversão do dicionário de clientes para array
    def dict_para_array(self):
        arr = []
        for client in self.clients.keys():
          for file in self.clients[client]:
              arr.append([client,file])
        return arr
            
    #Remoção de cliente
    def remover_cliente(self,socket_cliente: socket.socket,endereco_cliente,forced=False):
        with self.lock:
          if endereco_cliente in self.clients:
            self.log += f"Cliente desconectado: {endereco_cliente}\n"
            socket_cliente.send("Desconectado".encode())
            del self.clients[endereco_cliente]
        if forced:
            socket_cliente.close()
                    
    #Listagem de clientes e seus arquivos
    def listar_clientes(self,socket_cliente:socket.socket):
        with self.lock:
          clients_arr = list(map(lambda x: [x,self.clients[x]],self.clients.keys()))
          socket_cliente.send(json.dumps(clients_arr).encode())

    #Adição dos arquivos do cliente
    def adicionar_conteudo_cliente(self,endereco_cliente, lista_musicas):
        with self.lock:
          self.clients[endereco_cliente].extend(lista_musicas)
        
#Função para lidar com as requisições do cliente, cada função é uma thread
#Threads são Daemons, ou seja, são finalizadas quando o programa principal é finalizado
def handle_cliente_request(socket_cliente: socket.socket, endereco_cliente,server_instance: server_persist):
    while True:
        try: 

            #Cliente pode enviar 3 tipos de requisições:
            #1 - Dispor sua lista de arquivos
            #2 - Desconectar
            #3 - Listar nós e seus arquivos

            request = socket_cliente.recv(1024).decode('utf-8').split("|")
            if request[0] == "1":
                json_message = json.loads(request[1])
                lista_musicas = json_message["data"]
                server_instance.adicionar_conteudo_cliente(endereco_cliente, lista_musicas)
            elif request[0] == "2":
                server_instance.remover_cliente(socket_cliente,endereco_cliente)
                break
            elif request[0] == "3":
                server_instance.listar_clientes(socket_cliente)
        except:
            server_instance.remover_cliente(socket_cliente,endereco_cliente,True)
            break   
        
#Função para pegar o endereço IP da máquina
def pegar_ip():
    socket_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Conecta ao servidor DNS do Google
    socket_udp.connect(("8.8.8.8", 80))

    # Pega o endereço IP
    ip_address = socket_udp.getsockname()[0]

    socket_udp.close()

    return ip_address

#Função para lidar com as requisições de novos clientes, cada requisição gera uma thread
def handle_threading(socket_servidor: socket.socket, server_instance:server_persist):
    while True:
        socket_cliente, endereco_cliente = socket_servidor.accept()
        success = server_instance.adicionar_cliente(endereco_cliente)
        if(success):
            #Envia confirmação ao cliente
            socket_cliente.send("Registro bem sucedido!".encode())

            #Pega os dados os arquivos do cliente
            cliente_files = socket_cliente.recv(1024).decode('utf-8').split("|")[1]
            json_message = json.loads(cliente_files)
            lista_musicas = json_message["data"]
            server_instance.adicionar_conteudo_cliente(endereco_cliente,lista_musicas)

            # Criar uma nova thread para lidar com a conexão do cliente
            thread_cliente = threading.Thread(target=handle_cliente_request, args=(socket_cliente, endereco_cliente,server_instance))
            thread_cliente.daemon = True
            thread_cliente.start()
        else:
            socket_cliente.close()
        
#Função para iniciar o servidor            
def start_server():
    socket_servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Define o IP e a porta do servidor
    ip = pegar_ip()
    port = 25542
    socket_servidor.bind((ip, port))
    socket_servidor.listen(5)

    #Instancia uma versão persistente do servidor
    server_instance = server_persist(ip,port)

    # Cria uma thread para lidar com as requisições de novos clientes
    thread_requests = threading.Thread(target=handle_threading, args=(socket_servidor,server_instance))
    thread_requests.daemon = True
    thread_requests.start()

    #Cria o componente de tabela
    toprow = toprow = ['Nó', 'Arquivo']
    table = server_instance.dict_para_array()

    tbl = sg.Table(values=table, headings=toprow,
        auto_size_columns=True,
        display_row_numbers=False,
        justification='center', key='-TABLE-',
        selected_row_colors='red on yellow',
        enable_events=True,
        expand_x=True,
        expand_y=True,
        enable_click_events=True)
    
    #Cria o componente de log
    multiline = sg.Multiline(server_instance.log, size=(60,5), disabled=True)
    
    #Cria a janela
    layout = [[sg.Text(f"Endereço: {server_instance.endereco}:{server_instance.porta}")],
              [tbl],
              [sg.Text("Log do Servidor")],
              [multiline],
              [sg.Button("Fechar Servidor")]]
    window = sg.Window("Server GUI", layout,size=(750, 400), element_justification='c')

    #Loop de eventos da janela
    while(True):
        eventos , valores = window.read( timeout=250 )
        if eventos == sg.WIN_CLOSED or eventos == "Fechar Servidor":
            break
        tbl.update(server_instance.dict_para_array())
        multiline.update(server_instance.log)

if __name__ == '__main__':
    start_server()
