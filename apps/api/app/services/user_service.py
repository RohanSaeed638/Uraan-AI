from app.repositories.user_repository import UserRepository
class UserService:

    def __init__(self):
        self.repo = UserRepository()

    def get_users(self, db):
        return self.repo.get_all(db)