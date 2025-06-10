# server/group.py
class GroupManager:
    def __init__(self, db):
        # Agora o gerenciador de grupo usa a mesma conexão de banco de dados do servidor
        self.db = db
        self.db.create_group_tables() # Garante que as tabelas de grupo existam

    def create_group(self, group_name, creator_username):
        """Cria um grupo e adiciona o criador como primeiro membro."""
        if self.db.group_exists(group_name):
            return False
        
        self.db.create_group(group_name)
        self.db.add_group_member(group_name, creator_username)
        return True

    def add_member(self, group_name, username):
        if not self.db.group_exists(group_name) or not self.db.user_exists(username):
            return False
        self.db.add_group_member(group_name, username)
        return True

    def get_members(self, group_name):
        return self.db.get_group_members(group_name)

    def get_all_groups(self):
        return self.db.get_all_groups()