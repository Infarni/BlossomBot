import os
import sqlite3

from aiogram import Bot, Dispatcher, types
from aiogram.utils.callback_data import CallbackData

from .user import User
from settings import DATABASE, TELEGRAM_BOT_TOKEN

database = DATABASE
cursor = database.cursor()

class CustomBot(Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        sql = '''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER NOT NULL PRIMARY KEY,
            user_id INTEGER NOT NULL UNIQUE,
            mode TEXT,
            lang TEXT NOT NULL
        )
        '''
        cursor.execute(sql)
                
        sql = '''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER NOT NULL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL
        )
        '''
        cursor.execute(sql)
                
        database.commit()
        
        sql = 'SELECT user_id, lang FROM users'
        cursor.execute(sql)
        
        fetch = cursor.fetchall()

        self.users = {}
        for item in fetch:
            self.users[item[0]] = User(item[0], item[1])


bot = CustomBot(token=TELEGRAM_BOT_TOKEN, parse_mode='html')
dp = Dispatcher(bot)


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    user_id = message.from_user.id
    lang = message.from_user.language_code
    if not bot.users.get(message.from_user.id):
        bot.users[user_id] = User(user_id, lang)

    text = 'Привіт, це поки не закінчений бот, готуйтесь до багів!'
    await bot.send_message(message.from_id, text)


@dp.message_handler(commands=['help'])
async def help(message: types.Message):
    text = '''
Тут поки пустовато але працюють пару команд, наприклад:
/start - Запуск бота.
/help - Отримати інструкції по використанню бота.
/select - Вибрати нейрону мережу
'''
    
    await bot.send_message(message.from_id, text)


@dp.message_handler(commands=['select'])
async def select(message: types.Message):
    markup = types.InlineKeyboardMarkup().add(
        types.InlineKeyboardButton(
            text='chatgpt',
            callback_data='chatgpt'
        ),
        types.InlineKeyboardButton(
            text='dall-e',
            callback_data='dall-e'
        ),
        types.InlineKeyboardButton(
            text='tesseract',
            callback_data='tesseract'
        )
    )
    
    text = 'Виберіть нейрону мережу'
    await bot.send_message(message.from_id, text, reply_markup=markup)


@dp.callback_query_handler(lambda call: call.data == 'chatgpt')
async def chatgpt_callback_query(call: types.CallbackQuery):
    user_id = call.from_user.id
    bot.users[user_id].mode = 'chatgpt'

    await bot.answer_callback_query(call.id)

    text = 'Ви вибрали chatgpt. Пишіть в цей чат для взаємодії.'
    await bot.send_message(user_id, text)


@dp.callback_query_handler(lambda call: call.data == 'dall-e')
async def dalle_callback_query(call: types.CallbackQuery):
    user_id = call.from_user.id
    bot.users[user_id].mode = 'dall-e'

    await bot.answer_callback_query(call.id)

    text = '''
Ви вибрали dall-e. Пишіть в цей чат для взаємодії.
\n\nМайте на увазі що dall-e потребує великий prompt для генерації чогось конкретного
'''
    await bot.send_message(user_id, text)


@dp.callback_query_handler(lambda call: call.data == 'tesseract')
async def tesseract_callback_query(call: types.CallbackQuery):
    user_id = call.from_user.id
    bot.users[user_id].mode = 'tesseract'

    await bot.answer_callback_query(call.id)

    text = '''
Ви вибрали tesseract. Відішліть фото в цей чат для взаємодії.
Це нейромережа для сканування тексту з фото
(Тимчасово доступна тільки Українська мова)
'''
    await bot.send_message(user_id, text)


@dp.message_handler(
    lambda message: bot.users.get(message.from_user.id) == 'chatgpt',
    content_types=['text']
)
async def chatgpt(message: types.Message):
    user = bot.users[message.from_user.id]
    
    info = await message.reply('Завантаження...')
    
    text = ''
    try:
        for sym in user.chatgpt(message.text):
            text += sym
                
            if '\n' in sym:
                await bot.send_message(message.from_id, text)
                    
                await info.delete()
                info = await message.reply('Завантаження...')
                    
                text = ''
            
        await bot.send_message(message.from_id, text)
        await info.delete()
    except:
        await bot.send_message(message.from_id, 'Щось сталось не так...')
        await info.delete()


@dp.message_handler(
    lambda message: bot.users.get(message.from_user.id) == 'dall-e',
    content_types=['text', 'photo']
)
async def dalle(message: types.Message):
    user = bot.users[message.from_user.id]
        
    info = await message.reply('Завантаження...')
            
    try:
        if message.content_type == 'photo':
            file = await bot.get_file(message.photo[-1].file_id)
            image_url = f'https://api.telegram.org/file/bot{bot._token}/{file.file_path}'

            variation_image_url = user.dalle(image_url=image_url)
            
            await bot.send_photo(message.from_id, variation_image_url)
            await info.delete()
            
            return

        image_url = user.dalle(prompt=message.text)
    except:
        if message.content_type == 'photo':
            text = 'Зображення має бути квадратним та меньшим 4MB'
        else:
            text = 'Щось пішло не так...'

        await bot.send_message(message.from_id, text)
        await info.delete()
        
        return

    await bot.send_photo(message.from_id, image_url)
    await info.delete()


@dp.message_handler(
    lambda message: bot.users.get(message.from_user.id) == 'tesseract',
    content_types=['photo'],
)
async def tesseract(message: types.Message):
    user = bot.users[message.from_user.id]
        
    info = await bot.send_message(message.from_id, 'Завантаження...')
    # try:
    file = await bot.get_file(message.photo[-1].file_id)
    image_url = f'https://api.telegram.org/file/bot{bot._token}/{file.file_path}'
    text = user.scan(image_url)
    # except:
    #     await info.delete()
    #     await bot.send_message(message.from_id, 'Щось сталось не так...')        
        
    #     return

    await bot.send_message(message.from_id, text)
    await info.delete()


@dp.message_handler()
async def chat(message: types.Message):
    text = 'Ви не вибрали нейрону мережу'
    await bot.send_message(message.from_id, text)