import os

from aiogram import Bot, Dispatcher, types
from aiogram.utils.callback_data import CallbackData

from settings import TELEGRAM_BOT_TOKEN
from AI import OpenAI, Tesseract
from models import UserModel

from .filters import (
    IsNotRegisterUserFilter,
    IsRegisterUserFilter,
    IsChatGPTFilter,
    IsDalleFilter,
    IsTesseractFilter
)


bot = Bot(token=TELEGRAM_BOT_TOKEN, parse_mode='html')
dp = Dispatcher(bot)

ai = CallbackData('ai', 'action')


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    text = 'Привіт, це поки не закінчений бот, готуйтесь до багів!'
    await bot.send_message(message.from_id, text)


@dp.message_handler(commands=['help'])
async def help(message: types.Message):
    text = '''
Тут поки пустовато але працюють пару команд, наприклад:
/start - Запуск бота.
/help - Отримати інструкції по використанню бота.
/register - Зареєструвати користувача.
/select - Вибрати нейрону мережу.
'''
    
    await bot.send_message(message.from_id, text)


@dp.message_handler(commands=['register'])
async def register(message: types.Message):
    user = UserModel.get(message.from_user.id)
    if not user:
        UserModel.create(
            message.from_user.id,
            message.from_user.language_code
        )
        
        text = 'Ви були успішно зареєстровані.'
    else:
        text = 'Ви і так зареєстровані.'
    
    await bot.send_message(message.from_id, text)


@dp.message_handler(IsRegisterUserFilter(), commands=['select'])
async def select(message: types.Message):
    markup = types.InlineKeyboardMarkup().add(
        types.InlineKeyboardButton(
            text='chatgpt',
            callback_data=ai.new('chatgpt')
        ),
        types.InlineKeyboardButton(
            text='dall-e',
            callback_data=ai.new('dall-e')
        ),
        types.InlineKeyboardButton(
            text='tesseract',
            callback_data=ai.new('tesseract')
        )
    )
    
    text = 'Виберіть нейрону мережу'
    await bot.send_message(message.from_id, text, reply_markup=markup)


@dp.callback_query_handler(ai.filter())
async def ai_callback_query(call: types.CallbackQuery, callback_data: dict):
    user = UserModel.get(call.from_user.id)
    user.mode = callback_data['action']
    user.save()

    await bot.answer_callback_query(call.id)

    text = f'''Ви вибрали {callback_data['action']}.'''
    await bot.send_message(call.message.chat.id, text)


@dp.message_handler(IsChatGPTFilter(), content_types=['text'])
async def chatgpt(message: types.Message):
    user = UserModel.get(message.from_user.id)
    
    user.append_message('user', message.text)
    
    info = await message.reply('Завантаження...')
    
    text = ''
    assistant_response = ''
    try:
        for sym in OpenAI.chatgpt(user.get_messages(), message.text):
            text += sym
            assistant_response += sym
                
            if '\n' in sym:
                await bot.send_message(message.from_id, text)
                    
                await info.delete()
                info = await message.reply('Завантаження...')
                    
                text = ''
            
        await bot.send_message(message.from_id, text)
        await info.delete()
        
        user.append_message('assistant', assistant_response)
    except:
        await bot.send_message(message.from_id, 'Щось сталось не так...')
        await info.delete()
        
        user.append_message('system', 'Error')


@dp.message_handler(IsDalleFilter(), content_types=['text', 'photo'])
async def dalle(message: types.Message):
    info = await message.reply('Завантаження...')
            
    try:
        if message.content_type == 'photo':
            file = await bot.get_file(message.photo[-1].file_id)
            image_url = f'https://api.telegram.org/file/bot{bot._token}/{file.file_path}'

            variation_image_url = OpenAI.dalle(image_url=image_url)
                    
            await bot.send_photo(message.from_id, variation_image_url)
            await info.delete()
                    
            return

        image_url = OpenAI.dalle(prompt=message.text)
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


@dp.message_handler(IsTesseractFilter(), content_types=['photo'])
async def tesseract(message: types.Message):
    info = await bot.send_message(message.from_id, 'Завантаження...')
    try:
        file = await bot.get_file(message.photo[-1].file_id)
        image_url = f'https://api.telegram.org/file/bot{bot._token}/{file.file_path}'
        text = Tesseract.scan(image_url=image_url)
    except:
        await info.delete()
        await bot.send_message(message.from_id, 'Щось сталось не так...')        
        
        return

    await bot.send_message(message.from_id, text)
    await info.delete()


@dp.message_handler(IsNotRegisterUserFilter())
async def unregistered_user(message: types.Message):
    text = 'Зареєструйтесь будь ласка.'
    await bot.send_message(message.from_id, text)


@dp.message_handler(IsRegisterUserFilter())
async def unregistered_mode(message: types.Message):
    text = 'Я вас не зрозумів. Переконайтесь що ви вибрали режим та вводите коректні дані.'
    await bot.send_message(message.from_id, text)
