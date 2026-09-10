from app.repositories.auth_repository import AuthRepository


class AuthService:

    STATUS_PENDING = "PENDING"
    STATUS_APPROVED = "APPROVED"
    STATUS_REJECTED = "REJECTED"
    STATUS_BLOCKED = "BLOCKED"

    def __init__(self):
        self.repository = AuthRepository()

    def initialize(self):
        self.repository.create_table()

    def get_user(
        self,
        telegram_id,
    ):
        return self.repository.get_user_by_telegram_id(
            telegram_id
        )

    def register_user(
        self,
        telegram_id,
        username,
        first_name,
        last_name,
    ):
        existing_user = self.get_user(
            telegram_id
        )

        if existing_user:
            return existing_user

        return self.repository.create_pending_user(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
        )

    def approve_user(
        self,
        telegram_id,
        admin_id,
    ):
        return self.repository.update_status(
            telegram_id=telegram_id,
            status=self.STATUS_APPROVED,
            admin_id=admin_id,
        )

    def reject_user(
        self,
        telegram_id,
        admin_id,
    ):
        return self.repository.update_status(
            telegram_id=telegram_id,
            status=self.STATUS_REJECTED,
            admin_id=admin_id,
        )

    def block_user(
        self,
        telegram_id,
        admin_id,
    ):
        return self.repository.update_status(
            telegram_id=telegram_id,
            status=self.STATUS_BLOCKED,
            admin_id=admin_id,
        )

    def get_users_by_status(
        self,
        status,
    ):
        return self.repository.get_users_by_status(
            status
        )

    def get_all_users(self):
        return self.repository.get_all_users()

    def get_user_counts(self):
        return self.repository.get_user_counts()