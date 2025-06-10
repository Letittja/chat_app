import socket
import threading
import json
import os
import sys

running = True

def receive_messages(sock):
    """Lida com as mensagens recebidas do servidor."""
    global running
    while running:
        try:
            data_raw = sock.recv(4096)
            if not data_raw:
                print("\n[INFO] Conexão perdida com o servidor.")
                break

            response = json.loads(data_raw.decode('utf-8'))
            
            if response.get('type') == 'chat_message':
                print(f"\n[DM de {response['sender']}]: {response['message']}")
            elif response.get('type') == 'group_message':
                print(f"\n[{response['group']} | {response['sender']}]: {response['message']}")
            else:
                status = response.get('status', 'info')
                message = response.get('message', '')
                
                if status == 'error':
                    print(f"\n[ERRO] {message}")
                elif status == 'success':
                    print(f"\n[SUCESSO] {message}")
                else:
                    print(f"\n[INFO] {message}")

        except (ConnectionResetError, json.JSONDecodeError):
            if running:
                print("\n[ERRO] Erro de comunicação com o servidor.")
            break
        except Exception as e:
            if running:
                print(f"\n[ERRO] Ocorreu um erro inesperado: {e}")
            break
    
    print("\nSessão de recebimento encerrada.")
    running = False


def send_json(sock, data):
    """Função auxiliar para enviar dados JSON."""
    global running
    try:
        sock.send(json.dumps(data).encode('utf-8'))
    except ConnectionResetError:
        running = False
        print("\n[ERRO] Não foi possível enviar dados. A conexão foi perdida.")


def start_chat_mode(sock):
    """Entra no modo de conversa, onde o input do usuário é enviado como mensagem."""
    print("\nVocê está no modo de conversa. Digite '/menu' para voltar ao menu principal.")
    while running:
        msg = input()
        if not running:
             break
        if msg == '/menu':
            send_json(sock, {"command": "leave_chat"})
            print("Voltando ao menu...")
            break
        
        send_json(sock, {"command": "send_message", "message": msg})


def main_menu(sock):
    """Exibe o menu principal e lida com as escolhas do usuário."""
    global running
    while running:
        print("\n--- MENU PRINCIPAL ---")
        print("1. Listar usuários e grupos")
        print("2. Iniciar conversa com um usuário")
        print("3. Iniciar conversa em um grupo")
        print("4. Criar um novo grupo")
        print("5. Adicionar membro a um grupo")
        print("6. Sair")

        choice = input("Escolha uma opção: ")

        if not running:
            break

        if choice == '1':
            send_json(sock, {"command": "list_all"})
        
        elif choice == '2':
            target_user = input("Digite o nome do usuário com quem deseja conversar: ")
            if target_user:
                send_json(sock, {"command": "select_chat", "target_user": target_user})
                print(f"Pedido para conversar com '{target_user}' enviado. Entrando no modo de conversa...")
                start_chat_mode(sock)

        elif choice == '3':
            target_group = input("Digite o nome do grupo para entrar na conversa: ")
            if target_group:
                send_json(sock, {"command": "select_chat", "target_group": target_group})
                print(f"Pedido para entrar na conversa do grupo '{target_group}' enviado. Entrando no modo de conversa...")
                start_chat_mode(sock)

        elif choice == '4':
            group_name = input("Digite o nome do novo grupo: ")
            if group_name:
                send_json(sock, {"command": "create_group", "group_name": group_name})
        
        elif choice == '5':
            group_name = input("Digite o nome do grupo: ")
            user_to_add = input(f"Digite o nome do usuário para adicionar ao grupo '{group_name}': ")
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


def main():
    host = '127.0.0.1'
    port = 12345
    
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect((host, port))
    except ConnectionRefusedError:
        print("[ERRO] Não foi possível conectar ao servidor. Ele está offline ou o endereço/porta está incorreto.")
        return

    while True:
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
        
        send_json(client_socket, {
            "command": auth_command,
            "username": username,
            "password": password
        })

        try:
            response_raw = client_socket.recv(1024)
            if not response_raw:
                print("[ERRO] Servidor encerrou a conexão inesperadamente.")
                return
            response = json.loads(response_raw.decode('utf-8'))
            
            print(f"\n[{response['status'].upper()}] {response['message']}")

            if response['status'] == 'success' and auth_command == 'login':
                break
        except (json.JSONDecodeError, ConnectionResetError):
             print("[ERRO] Falha na comunicação durante a autenticação.")
             return

    receiver_thread = threading.Thread(target=receive_messages, args=(client_socket,))
    receiver_thread.daemon = True
    receiver_thread.start()

    main_menu(client_socket)
    
    receiver_thread.join(timeout=1)
    print("Programa cliente encerrado.")
    os._exit(0)


if __name__ == "__main__":
    main()