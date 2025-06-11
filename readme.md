# Chat em Python com Sockets e Threads
Este projeto implementa um sistema de chat robusto utilizando a biblioteca `socket` para a comunicação em rede e `threading` para lidar com múltiplos clientes simultaneamente. A segurança das senhas é garantida pelo uso de hashing com `bcrypt`.

## Funcionalidades

-   **Autenticação Segura:** Cadastro e login de usuários com senhas hasheadas.
-   **Mensagens Diretas (1-para-1):** Envie mensagens privadas para outros usuários.
-   **Mensagens Offline:** Se o destinatário não estiver online, a mensagem é salva no banco de dados e entregue assim que ele se conectar.
-   **Grupos de Conversa:**
    -   Crie grupos de chat.
    -   Adicione outros usuários aos seus grupos.
    -   Envie mensagens que são retransmitidas para todos os membros online do grupo.
-   **Status de Usuário:** Veja a lista de todos os usuários e saiba quem está online ou offline.
-   **Interface de Linha de Comando (CLI):** Interação com o sistema através de um menu simples e intuitivo no terminal.
-   **Persistência de Dados:** Todas as informações de usuários, grupos e mensagens offline são salvas em um banco de dados SQLite (`chat.db`).

## Estrutura do Projeto

chat_app/
├── server/
│ ├── init.py
│ ├── database.py # Gerencia toda a lógica do banco de dados SQLite
│ ├── group.py # Gerencia a lógica de criação e membros de grupos
│ ├── main.py # Ponto de entrada para iniciar o servidor
│ ├── server.py # Lógica principal do servidor (sockets, threads, comandos)
│ └── user.py # Gerencia a lógica de cadastro e autenticação de usuários
│
└── client/
└── client.py # Aplicação cliente para conectar e interagir com o servidor

## Tecnologias Utilizadas

-   **Linguagem:** Python 3
-   **Banco de Dados:** SQLite 3 (biblioteca padrão do Python)
-   **Bibliotecas Externas:**
    -   `bcrypt`: Para hashing seguro de senhas.
-   **Bibliotecas Padrão:**
    -   `socket`: Para comunicação em rede (TCP/IP).
    -   `threading`: Para concorrência e gerenciamento de múltiplos clientes.
    -   `json`: Para serialização de dados entre cliente e servidor.

## Como Executar o Projeto
### Pré-requisitos
-   Ter instalado Python 3.6 ou superior
-   Ter `pip` (gerenciador de pacotes do Python)

### 1. Instalação

1. Clone ou faça o download deste repositório para a sua máquina.
Navegue até a pasta raiz do projeto (`chat_app/`) e instale a única dependência externa:
pip install bcrypt


2. Iniciando o Servidor
Abra um terminal, navegue até a pasta raiz chat_app/, por exemplo:
cd "C:\Users\Lara Letittja\Downloads\Redes Codigos\ChatRedes\chat_app"
Depois:
python -m server.main
Se tudo correr bem, você verá a mensagem:
[Servidor] Escutando em 0.0.0.0:12345

3. Iniciando o Cliente
Abra um novo terminal para cada cliente que você deseja conectar. Navegue até a pasta raiz chat_app/, por exemplo:
cd "C:\Users\Lara Letittja\Downloads\Redes Codigos\ChatRedes\chat_app\client"
python client.py
Repita este passo em quantos terminais quiser para simular uma conversa com múltiplos usuários.
Se tudo correr bem, você passará para o próximo passo:

4. Guia
Ao iniciar o cliente, você terá as seguintes opções:
1 para Cadastro e 2 para criar um novo usuário com um nome e senha.
Login: Após o cadastro, escolha a opção 1 para entrar no sistema.
Uma vez logado, o menu principal aparecerá:
1.Listar usuários e grupos: Mostra todos os usuários cadastrados (com status online/offline) e todos os grupos criados.
2.Iniciar conversa com um usuário: Permite que você entre em um modo de chat direto com outro usuário.
3.Iniciar conversa em um grupo: Permite que você entre em um chat de grupo (você precisa ser membro).
4.Criar um novo grupo: Cria um novo grupo e automaticamente te adiciona como primeiro membro.
5.Adicionar membro a um grupo: Permite adicionar outro usuário a um grupo do qual você já faz parte.
6.Sair: Encerra a conexão com o servidor.

extra1: Para sair de um modo de conversa (direto ou em grupo) e voltar ao menu principal, digite /menu e pressione Enter.
extra2: Toda vez que for iniciar o código apague a memória cash e o banco de dados antigos. 