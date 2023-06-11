from datetime import datetime, timedelta

from settings import DATABASE, CURSOR


class UserObject:
    def __init__(
        self,
        user_id: int,
        lang: str,
        mode: str = None,
        id: int = None,
        uses: int = 0,
        premium: bool = False,
        subscribe_date: datetime = None
    ):
        self.id = id
        self.user_id = user_id
        self.mode = mode
        self.lang = lang
        self.uses = uses
        self.subscribe_date = subscribe_date

        sql = '''INSERT OR IGNORE INTO users VALUES (?, ?, ?, ?, ?, ?)'''
        args = (id, user_id, mode, lang, uses, subscribe_date)
        CURSOR.execute(sql, args)

        DATABASE.commit()

    def __check_uses(self):
        if self.premium:
            return True

        sql = 'SELECT uses FROM users WHERE user_id = ?'
        args = (self.user_id,)
        CURSOR.execute(sql, args)

        fetch = CURSOR.fetchone()[0]

        return fetch <= 5

    def __check_subscribe_date(self):
        sql = 'SELECT subscribe_date FROM users WHERE user_id = ?'
        args = (self.user_id,)
        CURSOR.execute(sql, args)

        fetch = CURSOR.fetchall()[0][0]

        if fetch is None:
            return None

        date = datetime.strptime(fetch, '%Y-%m-%d %H:%M:%S.%f')

        return date

    def __check_premium(self):
        if self.subscribe_date is None:
            return False

        date = (self.subscribe_date + timedelta(days=30)).date()

        return datetime.now().date() < date

    def __delete_message(self):
        sql = '''
        DELETE FROM messages
        WHERE user_id = ?
        AND id = (
            SELECT id FROM messages
            WHERE user_id = ?
            ORDER BY id ASC
            LIMIT 1
        )
        '''
        args = (self.user_id, self.user_id)
        CURSOR.execute(sql, args)

        DATABASE.commit()

    def __getattribute__(self, name):
        if name == 'uses':
            return self.__check_uses()
        elif name == 'subscribe_date':
            return self.__check_subscribe_date()
        elif name == 'premium':
            return self.__check_premium()

        return super().__getattribute__(name)

    def update_subscribe_date(self, value: datetime):
        sql = 'UPDATE users SET subscribe_date = ? WHERE user_id = ?'
        args = (value, self.user_id)
        CURSOR.execute(sql, args)

        DATABASE.commit()

    def append_use(self):
        sql = '''
        UPDATE users
        SET
            uses = ?
        WHERE user_id = ?
        '''
        args = (self.uses + 1, self.user_id)
        CURSOR.execute(sql, args)

        DATABASE.commit()

        self.uses += 1

    def save(self):
        sql = '''
        UPDATE users
        SET
            id = ?,
            user_id = ?,
            mode = ?,
            lang = ?,
            uses = ?,
            subscribe_date = ?
        WHERE user_id = ?'''
        args = (
            self.id,
            self.user_id,
            self.mode,
            self.lang,
            self.uses,
            self.subscribe_date,
            self.user_id
        )
        CURSOR.execute(sql, args)

        DATABASE.commit()

    def get_messages(self) -> list:
        sql = 'SELECT role, content FROM messages WHERE user_id = ?'
        CURSOR.execute(sql, (self.user_id,))

        fetch = CURSOR.fetchall()

        messages = []
        for item in fetch:
            messages.append(
                {
                    'role': item[0],
                    'content': item[1]
                }
            )

        return messages

    def append_message(self, role: str, content: str):
        if len(self.get_messages()) > 5:
            self.__delete_message()

        args = (None, self.user_id, role, content)
        sql = 'INSERT INTO messages VALUES (?, ?, ?, ?)'
        CURSOR.execute(sql, args)

        DATABASE.commit()


class UserModel:
    def __init__(self):
        sql = '''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER NOT NULL PRIMARY KEY,
            user_id INTEGER NOT NULL UNIQUE,
            mode TEXT,
            lang TEXT NOT NULL
        )
        '''
        CURSOR.execute(sql)

        DATABASE.commit()

    @staticmethod
    def all() -> list:
        sql = 'SELECT id, user_id, mode, lang FROM users'
        CURSOR.execute(sql)

        fetch = CURSOR.fetchall()

        objects = []
        for item in fetch:
            objects.append(
                UserObject(
                    user_id=item[1],
                    mode=item[2],
                    lang=item[3],
                )
            )

        return objects

    @staticmethod
    def get(user_id: int) -> UserObject | None:
        sql = 'SELECT * FROM users WHERE user_id = ?'
        args = (user_id,)
        CURSOR.execute(sql, args)

        fetch = CURSOR.fetchone()

        if not fetch:
            return None

        return UserObject(
            id=fetch[0],
            user_id=fetch[1],
            mode=fetch[2],
            lang=fetch[3],
            uses=fetch[4],
            subscribe_date=fetch[5]
        )

    @staticmethod
    def create(user_id, lang):
        return UserObject(user_id, lang)
