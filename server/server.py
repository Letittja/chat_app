import socket
import threading
import json

from .database import Database
from .user import UserManager
from .group import GroupManager

class ChatServer:
    #Cria o monitor de bate-papo, pega o IP e a porta
    def __init__(self, host='0.0.0.0', port=12345):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #Dicionários de quem está conectado, quem está online e com quem cada um está falando.
        self.clients = {}  
        self.users_online = {}
        self.chat_context = {} 
        #Ligação com o banco de dados
        self.db = Database()
        self.user_manager = UserManager(self.db)
        self.group_manager = GroupManager(self.db)
        print("[Servidor] Gerenciadores de banco de dados, usuários e grupos inicializados.")
    #Liga o servidor e fica esperando alguém se conectar
    def start(self):
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print(f"[Servidor] Escutando em {self.host}:{self.port}")

        while True:
            #Cria uma thread para cada novo membro
            client_socket, addr = self.server_socket.accept()
            print(f"[Nova Conexão] Conexão de {addr} estabelecida.")
            thread = threading.Thread(target=self.handle_client, args=(client_socket,))
            thread.start()
    #Empacota uma mensagem em JSON e envia para o cliente
    def send_json(self, sock, data):
        """Função auxiliar para codificar e enviar dados JSON."""
        try:
            sock.send(json.dumps(data).encode('utf-8'))
        except (ConnectionResetError, BrokenPipeError):
            pass 
    #Faz login, recebe mensagens, guardar offline, criar grupo, etc.
    def handle_client(self, client_socket):
        username = None
        try:
            while True:
                auth_data_raw = client_socket.recv(1024).decode('utf-8')
                if not auth_data_raw:
                    print("[Autenticação] Cliente desconectou antes de autenticar.")
                    return
                
                auth_data = json.loads(auth_data_raw)
                user = auth_data.get('username')
                pwd = auth_data.get('password')
                command = auth_data.get('command')

                if command == 'register':
                    if user and pwd and self.user_manager.register(user, pwd):
                        self.send_json(client_socket, {"status": "success", "message": "Cadastro realizado com sucesso! Faça o login."})
                    else:
                        self.send_json(client_socket, {"status": "error", "message": "Nome de usuário já existe ou dados inválidos."})
                
                elif command == 'login':
                    if user and pwd and self.user_manager.authenticate(user, pwd):
                        if user in self.users_online:
                            self.send_json(client_socket, {"status": "error", "message": "Este usuário já está logado."})
                            continue
                        
                        username = user
                        self.clients[client_socket] = username
                        self.users_online[username] = client_socket
                        self.send_json(client_socket, {"status": "success", "message": f"Login realizado com sucesso! Bem-vindo, {username}."})
                        print(f"[Autenticação] Usuário '{username}' logado.")
                        
                        offline_msgs = self.db.get_and_delete_messages_for(username)
                        if offline_msgs:
                            self.send_json(client_socket, {"status": "info", "message": "Você tem novas mensagens!"})
                            for sender, msg_text in offline_msgs:
                                self.send_json(client_socket, {"type": "chat_message", "sender": sender, "message": msg_text})
                        
                        break
                    else:
                        self.send_json(client_socket, {"status": "error", "message": "Nome de usuário ou senha inválidos."})
                else:
                    self.send_json(client_socket, {"status": "error", "message": "Comando de autenticação inválido."})

            while True:
                message_raw = client_socket.recv(4096).decode('utf-8')
                if not message_raw:
                    break 

                data = json.loads(message_raw)
                command = data.get('command')

                if command == 'list_all':
                    users = self.db.get_all_users()
                    groups = self.group_manager.get_all_groups()
                    user_list_str = "\n".join(f"- {u} {'(online)' if u in self.users_online else '(offline)'}" for u in users)
                    group_list_str = "\n".join(f"- {g}" for g in groups) if groups else "Nenhum grupo criado."
                    full_message = f"--- USUÁRIOS ---\n{user_list_str}\n\n--- GRUPOS ---\n{group_list_str}"
                    self.send_json(client_socket, {"status": "info", "message": full_message})

                elif command == 'send_message':
                    context = self.chat_context.get(username)
                    if not context:
                        self.send_json(client_socket, {"status": "error", "message": "Você não está em uma conversa. Use o menu para selecionar um chat."})
                        continue
                    
                    target_type = context['type']
                    target_name = context['target']
                    message_text = data['message']
                    
                    if target_type == 'user':
                        if target_name in self.users_online:
                            self.send_json(self.users_online[target_name], {"type": "chat_message", "sender": username, "message": message_text})
                        else:
                            self.db.save_message(username, target_name, message_text)
                            self.send_json(client_socket, {"status": "info", "message": f"'{target_name}' está offline. A mensagem será entregue quando ele(a) se conectar."})
                    
                    elif target_type == 'group':
                        members = self.group_manager.get_members(target_name)
                        for member in members:
                            if member != username and member in self.users_online:
                                self.send_json(self.users_online[member], {"type": "group_message", "group": target_name, "sender": username, "message": message_text})
                
                elif command == 'select_chat':
                    target_user = data.get('target_user')
                    target_group = data.get('target_group')

                    if target_user:
                        if self.db.user_exists(target_user):
                            self.chat_context[username] = {'type': 'user', 'target': target_user}
                            self.send_json(client_socket, {"status": "success", "message": f"Contexto de chat alterado para o usuário '{target_user}'."})
                        else:
                            self.send_json(client_socket, {"status": "error", "message": f"Usuário '{target_user}' não encontrado."})
                    
                    elif target_group:
                        if self.db.group_exists(target_group):
                            if username in self.group_manager.get_members(target_group):
                                self.chat_context[username] = {'type': 'group', 'target': target_group}
                                self.send_json(client_socket, {"status": "success", "message": f"Contexto de chat alterado para o grupo '{target_group}'."})
                            else:
                                self.send_json(client_socket, {"status": "error", "message": f"Você não é membro do grupo '{target_group}'."})
                        else:
                            self.send_json(client_socket, {"status": "error", "message": f"Grupo '{target_group}' não encontrado."})
                
                elif command == 'create_group':
                    group_name = data.get('group_name')
                    if group_name:
                        if self.group_manager.create_group(group_name, username):
                             self.send_json(client_socket, {"status": "success", "message": f"Grupo '{group_name}' criado com sucesso! Você foi adicionado como primeiro membro."})
                        else:
                             self.send_json(client_socket, {"status": "error", "message": f"Grupo '{group_name}' já existe."})
                    else:
                        self.send_json(client_socket, {"status": "error", "message": "Nome do grupo não fornecido."})

                elif command == 'add_member_to_group':
                    group_name = data.get('group_name')
                    user_to_add = data.get('user_to_add')

                    if not group_name or not user_to_add:
                        self.send_json(client_socket, {"status": "error", "message": "Nome do grupo e do usuário são obrigatórios."})
                    elif not self.db.group_exists(group_name):
                        self.send_json(client_socket, {"status": "error", "message": f"O grupo '{group_name}' não existe."})
                    elif not self.db.user_exists(user_to_add):
                        self.send_json(client_socket, {"status": "error", "message": f"O usuário '{user_to_add}' não existe."})
                    elif username not in self.group_manager.get_members(group_name):
                        self.send_json(client_socket, {"status": "error", "message": "Você não é membro deste grupo e não pode adicionar novos usuários."})
                    else:
                        self.group_manager.add_member(group_name, user_to_add)
                        self.send_json(client_socket, {"status": "success", "message": f"Usuário '{user_to_add}' adicionado ao grupo '{group_name}' com sucesso."})
                
                elif command == 'leave_chat':
                    if username in self.chat_context:
                        del self.chat_context[username]
                    self.send_json(client_socket, {"status": "info", "message": "Você saiu do modo de conversa."})

        except (ConnectionResetError, json.JSONDecodeError, UnicodeDecodeError) as e:
            print(f"[Aviso] Conexão com '{username or 'cliente não autenticado'}' foi perdida de forma inesperada. Causa: {e}")
        except Exception as e:
            print(f"[ERRO] Ocorreu um erro com o cliente '{username}': {e}")
        finally:
            if username:
                print(f"[Desconexão] Usuário '{username}' desconectado.")
                if username in self.users_online: del self.users_online[username]
                if username in self.chat_context: del self.chat_context[username]
            if client_socket in self.clients: del self.clients[client_socket]
            client_socket.close()
#Inicia o servidor
if __name__ == "__main__":
    chat_server = ChatServer()
    chat_server.start()