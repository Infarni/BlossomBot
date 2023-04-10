import os
import sqlite3

import AI

from settings import DATABASE


database = DATABASE
cursor = database.cursor()


class Messages:
    def __init__(self, user_id):
        self.__user_id = user_id
    
    def __getitem__(self, slice):
        return self.get()

    def get(self):
        sql = 'SELECT role, content FROM messages WHERE user_id = ?'
        cursor.execute(sql, (self.__user_id,))
        
        fetch = cursor.fetchall()
        
        result = []
        for item in fetch:
            result.append(
                {
                    'role': item[0],
                    'content': item[1]
                }
            )
            
        return result

    def append(self, object):
        args = (None, self.__user_id, object['role'], object['content'])
        
        sql = 'INSERT INTO messages VALUES (?, ?, ?, ?)'
        cursor.execute(sql, args)
        
        database.commit()


class User(AI.OpenAI, AI.Tesseract):
    def __init__(self, user_id: int, lang: str):
        super().__init__(lang)

        self.user_id = user_id
        self.lang = lang

        sql = 'INSERT OR IGNORE INTO users VALUES (?, ?, ?, ?)'
        cursor.execute(sql, (None, self.user_id, None, self.lang))
        
        self.messages = Messages(self.user_id)

        database.commit()
    
    def __eq__(self, value):
        return self.mode == value
    
    def __setattr__(self, name, value):
        if name == 'mode':
            sql = 'UPDATE users SET mode = ? WHERE user_id = ?'
            cursor.execute(sql, (value, self.user_id))
            
            database.commit()
        
        self.__dict__[name] = value
    
    def __getattr__(self, name):
        if name == 'mode':
            sql = 'SELECT mode FROM users WHERE user_id = ?'
            cursor.execute(sql, (self.user_id,))
            
            fetch = cursor.fetchone()
            
            return fetch[0]

        elif name == 'messages':
            return self.__messages.get()
        
        return self.__dict__[name]
