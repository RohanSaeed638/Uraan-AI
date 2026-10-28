class UserRepository:

    def get_all(self, db):
        return db.query(User).all()