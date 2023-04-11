from settings import DATABASE, CURSOR


class UserObject:
    def __init__(
        self,
        user_id:int,
        lang: str,
        mode: str=None,
        id: int=None
    ):
        self.id = id
        self.user_id = user_id
        self.mode = mode
        self.lang = lang
        
        sql = '''INSERT OR IGNORE INTO users VALUES (?, ?, ?, ?)'''
        args = (id, user_id, mode, lang)
        CURSOR.execute(sql, args)
        
        DATABASE.commit()
    
    def save(self):
        sql = '''
        UPDATE users
        SET
            id = ?,
            user_id = ?,
            mode = ?,
            lang = ?
        WHERE user_id = ?'''
        args = (self.id, self.user_id, self.mode, self.lang, self.user_id)
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
                    lang=item[3]
                )
            )
        
        return objects

    @staticmethod
    def get(user_id: int) -> UserObject | None:
        sql = 'SELECT id, user_id, mode, lang FROM users WHERE user_id = ?'
        args = (user_id,)
        CURSOR.execute(sql, args)
        
        fetch = CURSOR.fetchone()

        if not fetch:
            return None

        return UserObject(
            id=fetch[0],
            user_id=fetch[1],
            mode=fetch[2],
            lang=fetch[3]
        )
    
    @staticmethod
    def create(user_id, lang):
        return UserObject(user_id, lang)
