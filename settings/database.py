import sqlite3

DATABASE = sqlite3.connect('db.sqlite3')
CURSOR = DATABASE.cursor()
