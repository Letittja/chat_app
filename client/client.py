import socket
import threading
import json
import os

running = True #Interruptor do cliente

#Orelha do cliente
def receive_messages(sock):
    global running
    while running:
        try:
            data_raw = sock.recv(4096) #Aqui ele recebe a informação, 4096/4 KB é o tamanho máximo de bites que tem que ser 2^n, nesse caso 2^12
            if not data_raw: #Se ele não recebe nada ele manda a mensagem de erro e quebra a conexão
                print("\n[INFO] Conexão perdida com o servidor.")
                break

            #Se não ele abre a "caixinha" e decodifica no "dicionário" 
            response = json.loads(data_raw.decode('utf-8'))
            
            #Aqui ele começa a fazer as verificações do tipo de mensagem para fazer o print correto
            #Mensagem DM
            if response.get('type') == 'chat_message':
                print(f"\n[DM de {response['sender']}]: {response['message']}")
            #Mensagem de grupo
            elif response.get('type') == 'group_message':
                print(f"\n[{response['group']} | {response['sender']}]: {response['message']}")
            #Outros tipos (ERROR, SUCESS, WARNING)
            else:
                status = response.get('status', 'info')
                message = response.get('message', '')
                
                if status == 'error':
                    print(f"\n[ERRO] {message}")
                elif status == 'success':
                    print(f"\n[SUCESSO] {message}")
                else:
                    print(f"\n[INFO] {message}")
        #Se der erro por quebra de conexão
        except (ConnectionResetError, json.JSONDecodeError):
            if running:
                print("\n[ERRO] Erro de comunicação com o servidor.")
            break
        except Exception as e:
            if running:
                print(f"\n[ERRO] Ocorreu um erro inesperado: {e}")
            break
    #Quando o laço se encerra
    print("\nSessão de recebimento encerrada.")
    running = False
#Boca do cliente
def send_json(sock, data):
    global running
    try:
        #Empacota os dados com json e envia para o servidor
        sock.send(json.dumps(data).encode('utf-8')) #Esse utf-8 transforma o texto em bytes
    except ConnectionResetError:
        running = False
        print("\n[ERRO] Não foi possível enviar dados. A conexão foi perdida.")
#Modo conversa
def start_chat_mode(sock):
    print("\nVocê está no modo de conversa. \nSe deseja voltar digite '/menu' e você será levado ao menu principal.")
    while running:
        #Pega a mensagem digitada e envia para o chat
        msg = input()
        if not running:
             break
        if msg == '/menu':#Se a mensagem for essa ele retorna ao menu inicial
            send_json(sock, {"command": "leave_chat"})
            print("Voltando ao menu...")
            break
        
        send_json(sock, {"command": "send_message", "message": msg})
#Menu principal
def main_menu(sock):
    global running
    while running:
        print("\n------- MENU PRINCIPAL -------")
        print("1. Listar usuários e grupos")
        print("2. Iniciar uma conversa DM")
        print("3. Iniciar uma conversa em grupo")
        print("4. Criar um novo grupo")
        print("5. Adicionar membro a um grupo")
        print("6. Sair")

        choice = input("O que gostaria de fazer?\nR: ")

        if not running:
            break

        if choice == '1':
            send_json(sock, {"command": "list_all"})
        
        elif choice == '2':
            target_user = input("\nCom quem deseja conversar?\nR: ")
            if target_user:
                send_json(sock, {"command": "select_chat", "target_user": target_user})
                print(f"Pedido para conversar com '{target_user}' enviado. Entrando na DM...")
                start_chat_mode(sock)

        elif choice == '3':
            target_group = input("\nQual o grupo que você deseja mandar mensagem?\nR: ")
            if target_group:
                send_json(sock, {"command": "select_chat", "target_group": target_group})
                print(f"Pedido para entrar na conversa do grupo '{target_group}' enviado. Entrando no grupo...")
                start_chat_mode(sock)

        elif choice == '4':
            group_name = input("\nQual o nome do novo grupo?\nR: ")
            if group_name:
                send_json(sock, {"command": "create_group", "group_name": group_name})
        
        elif choice == '5':
            group_name = input("\nQual o grupo?\nR: ")
            user_to_add = input(f"\nQual usuário você quer adicionar ao grupo '{group_name}'?\nR: ")
            if group_name and user_to_add:
                send_json(sock, {
                    "command": "add_member_to_group",
                    "group_name": group_name,
                    "user_to_add": user_to_add
                })

        elif choice == '6':
            running = False
            sock.close()
            print("Desconectando...")
            break
        else:
            print("[ERRO] Opção inválida.")
#Função principal que liga o client ao Host
def main():
    host = '127.0.0.1'
    port = 12345
    #Cria o canal que fala com o servidor
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)#AF_INET IPV4 e SOCK_STREAM é ligação confiável tipo TCP
    #Aqui ele tenta conectar o client ao Host através da porta e o IP
    try:
        client_socket.connect((host, port))
    except ConnectionRefusedError:#Se recusar(Host desconectado)
        print("[ERRO] Não foi possível conectar ao servidor. \nEle está offline ou o endereço/porta está incorreto.")
        return

    while True: #Tela de cadastro e login
        action = input("Digite '1' para Login ou '2' para Cadastro: ")
        username = input("Nome de usuário: ")
        password = input("Senha: ")

        if action == '1':
            auth_command = 'login'
        elif action == '2':
            auth_command = 'register'
        else:
            print("[ERRO] Ação inválida.")
            continue
        #Aqui ele envia para o servidor e espera a resposta
        send_json(client_socket, {
            "command": auth_command,
            "username": username,
            "password": password
        })

        try:
            #Espera uma resposta do servidor depois do login/cadastro
            response_raw = client_socket.recv(1024)#Numero de bites menor, pois é só do servidor 1KB, 2^10
            #Se não receber nada significa que o servidor caiu 
            if not response_raw:
                print("[ERRO] Servidor encerrou a conexão inesperadamente.")
                return
            #Converte os bytes da resposta para texto e depois dicionário python
            response = json.loads(response_raw.decode('utf-8'))
            print(f"\n[{response['status'].upper()}] {response['message']}")
            #Se o login deu certo ele sai do loop e vai para o menu principal
            if response['status'] == 'success' and auth_command == 'login':
                break
        #Se deu erro na comunicação, ele avisa e para tudo.
        except (json.JSONDecodeError, ConnectionResetError):
             print("[ERRO] Falha na comunicação durante a autenticação.")
             return
    #Realiza as threads para receber as mensagens(Orelha que escuta o servidor o tempo todo)
    receiver_thread = threading.Thread(target=receive_messages, args=(client_socket,))
    receiver_thread.daemon = True#Se o programa principal terminar ele encerra a thread
    receiver_thread.start()#Orelha do servidor
    #Enquanto a orelha escuta, o programa mostra o menu para digitar
    main_menu(client_socket)
    #Espera 1 segundo para a orelha terminar a conexão
    receiver_thread.join(timeout=1)
    print("Programa cliente encerrado.")
    os._exit(0)

if __name__ == "__main__":
    main()