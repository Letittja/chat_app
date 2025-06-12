class GroupManager:
    #Aqui ele prepara as tabelas
    def __init__(self, db):
        self.db = db
        self.db.create_group_tables() 
    #Cria um grupo novo e já coloca quem criou dentro dele.
    def create_group(self, group_name, creator_username):
        if self.db.group_exists(group_name):
            return False
        
        self.db.create_group(group_name)
        self.db.add_group_member(group_name, creator_username)
        return True
    #Adiciona gente no grupo.
    def add_member(self, group_name, username):
        if not self.db.group_exists(group_name) or not self.db.user_exists(username):
            return False
        self.db.add_group_member(group_name, username)
        return True
    #Lista quem está no grupo e todos os grupos que existem.
    def get_members(self, group_name):
        return self.db.get_group_members(group_name)
    def get_all_groups(self):
        return self.db.get_all_groups()