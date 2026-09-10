from app.database import get_connection


class AuthRepository:

    def create_table(self):
        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER NOT NULL UNIQUE,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    status TEXT NOT NULL DEFAULT 'PENDING',
                    requested_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    approved_at TIMESTAMP,
                    approved_by INTEGER,
                    rejected_at TIMESTAMP,
                    rejected_by INTEGER
                )
                """
            )

            connection.commit()

        finally:
            connection.close()

    def get_user_by_telegram_id(
        self,
        telegram_id,
    ):
        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT
                    id,
                    telegram_id,
                    username,
                    first_name,
                    last_name,
                    status,
                    requested_at,
                    approved_at,
                    approved_by,
                    rejected_at,
                    rejected_by
                FROM users
                WHERE telegram_id = ?
                """,
                (telegram_id,),
            )

            row = cursor.fetchone()

            if not row:
                return None

            return dict(row)

        finally:
            connection.close()

    def create_pending_user(
        self,
        telegram_id,
        username,
        first_name,
        last_name,
    ):
        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                INSERT INTO users (
                    telegram_id,
                    username,
                    first_name,
                    last_name,
                    status
                )
                VALUES (?, ?, ?, ?, 'PENDING')
                """,
                (
                    telegram_id,
                    username,
                    first_name,
                    last_name,
                ),
            )

            connection.commit()

            return self.get_user_by_telegram_id(
                telegram_id
            )

        finally:
            connection.close()

    def update_status(
        self,
        telegram_id,
        status,
        admin_id,
    ):
        connection = get_connection()

        try:
            cursor = connection.cursor()

            if status == "APPROVED":
                cursor.execute(
                    """
                    UPDATE users
                    SET
                        status = ?,
                        approved_at = CURRENT_TIMESTAMP,
                        approved_by = ?,
                        rejected_at = NULL,
                        rejected_by = NULL
                    WHERE telegram_id = ?
                    """,
                    (
                        status,
                        admin_id,
                        telegram_id,
                    ),
                )

            elif status == "REJECTED":
                cursor.execute(
                    """
                    UPDATE users
                    SET
                        status = ?,
                        rejected_at = CURRENT_TIMESTAMP,
                        rejected_by = ?,
                        approved_at = NULL,
                        approved_by = NULL
                    WHERE telegram_id = ?
                    """,
                    (
                        status,
                        admin_id,
                        telegram_id,
                    ),
                )

            elif status == "BLOCKED":
                cursor.execute(
                    """
                    UPDATE users
                    SET status = ?
                    WHERE telegram_id = ?
                    """,
                    (
                        status,
                        telegram_id,
                    ),
                )

            else:
                cursor.execute(
                    """
                    UPDATE users
                    SET status = ?
                    WHERE telegram_id = ?
                    """,
                    (
                        status,
                        telegram_id,
                    ),
                )

            connection.commit()

            return self.get_user_by_telegram_id(
                telegram_id
            )

        finally:
            connection.close()

    def get_users_by_status(
        self,
        status,
    ):
        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT
                    id,
                    telegram_id,
                    username,
                    first_name,
                    last_name,
                    status,
                    requested_at,
                    approved_at,
                    approved_by,
                    rejected_at,
                    rejected_by
                FROM users
                WHERE status = ?
                ORDER BY requested_at DESC
                """,
                (status,),
            )

            rows = cursor.fetchall()

            return [
                dict(row)
                for row in rows
            ]

        finally:
            connection.close()

    def get_all_users(self):
        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT
                    id,
                    telegram_id,
                    username,
                    first_name,
                    last_name,
                    status,
                    requested_at,
                    approved_at,
                    approved_by,
                    rejected_at,
                    rejected_by
                FROM users
                ORDER BY requested_at DESC
                """
            )

            rows = cursor.fetchall()

            return [
                dict(row)
                for row in rows
            ]

        finally:
            connection.close()

    def get_user_counts(self):
        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT
                    COUNT(*) AS total,
                    SUM(
                        CASE
                            WHEN status = 'PENDING'
                            THEN 1
                            ELSE 0
                        END
                    ) AS pending,
                    SUM(
                        CASE
                            WHEN status = 'APPROVED'
                            THEN 1
                            ELSE 0
                        END
                    ) AS approved,
                    SUM(
                        CASE
                            WHEN status = 'REJECTED'
                            THEN 1
                            ELSE 0
                        END
                    ) AS rejected,
                    SUM(
                        CASE
                            WHEN status = 'BLOCKED'
                            THEN 1
                            ELSE 0
                        END
                    ) AS blocked
                FROM users
                """
            )

            row = cursor.fetchone()

            return {
                "total": row["total"] or 0,
                "pending": row["pending"] or 0,
                "approved": row["approved"] or 0,
                "rejected": row["rejected"] or 0,
                "blocked": row["blocked"] or 0,
            }

        finally:
            connection.close()