from settings import DATABASE, CURSOR


def init():
    sql = '''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER NOT NULL PRIMARY KEY,
        user_id INTEGER NOT NULL UNIQUE,
        mode TEXT,
        lang TEXT NOT NULL,
        uses INTEGER DEFAULT 0,
        subscribe_date timestamp
    )
    '''
    CURSOR.execute(sql)

    sql = '''
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER NOT NULL PRIMARY KEY,
        user_id INTEGER NOT NULL,
        role TEXT NOT NULL,
        content TEXT NOT NULL
    )
    '''
    CURSOR.execute(sql)

    DATABASE.commit()
