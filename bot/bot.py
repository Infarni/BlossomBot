import os
import requests

import soundfile

from datetime import datetime

from aiogram import Bot, Dispatcher, types
from aiogram.utils.callback_data import CallbackData

from settings import TELEGRAM_BOT_TOKEN, OWNER_ID

from AI.open_ai import OpenAI
from AI.tesseract import Tesseract
from AI.speech_recognition import SpeechRecognition

from models import UserModel

from .filters import (
    IsAdminFilter,
    IsNotRegisterUserFilter,
    IsRegisterUserFilter,
    IsSubscribeFilter,
    IsChatGPTFilter,
    IsDalleFilter,
    IsTesseractFilter,
    IsSpeechRecognition
)


bot = Bot(token=TELEGRAM_BOT_TOKEN, parse_mode='html')
dp = Dispatcher(bot)

ai = CallbackData('ai', 'action')
permit_request = CallbackData('permit_request', 'action')


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    text = 'Привіт, це поки не закінчений бот, готуйтесь до багів!'
    await bot.send_message(message.from_id, text)


@dp.message_handler(commands=['help'])
async def help(message: types.Message):
    text = '''
Тут поки пустовато але працюють пару команд, наприклад:
/start - Запуск бота
/help - Отримати інструкції по використанню бота
/register - Зареєструвати користувача
/select - Вибрати нейрону мережу
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
        
        text = 'Ви були успішно зареєстровані'
    else:
        text = 'Ви і так зареєстровані'
    
    await bot.send_message(message.from_id, text)


@dp.message_handler(IsRegisterUserFilter(), commands=['subscribe'])
async def subscribe(message: types.Message):
    user = UserModel.get(message.from_user.id)
    user.mode = 'subscribe'
    user.save()
    
    text = '''Надішліть будь ласка фото або квитанцію разом з командою /subscribe
Потрібно надіслати 1 грн на картку Монобанку
Номер картки: `4441 1144 6265 7238`'''
    await bot.send_message(message.from_id, text, parse_mode='MarkdownV2')


@dp.message_handler(IsSubscribeFilter(), content_types=['photo', 'document'])
async def subscribe_handler(message: types.Message):
    user = UserModel.get(message.from_user.id)

    if user.premium:
        text = f'У вас вже є преміум\. Термін підписки закінчиться {user.subscribe_date}'

        await bot.send_message(message.from_id, text)

        return
    
    text = '''Заявку на місячну підписку подано
Ви отримаєте повідомлення коли її буде схвалено'''

    await bot.send_message(message.from_id, text)
    
    if message.content_type == 'photo':
        photo = message.photo[-1].file_id
        
        markup = types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton(
                text=f'Схвалити',
                callback_data=permit_request.new(message.from_user.id)
            )
        )
        
        await bot.send_photo(OWNER_ID, photo, reply_markup=markup)

        return
    
    document = message.document.file_id
   
    markup = types.InlineKeyboardMarkup().add(
        types.InlineKeyboardButton(
            text=f'Схвалити',
            callback_data=permit_request.new(message.from_user.id)
        )
    )
            
    await bot.send_document(OWNER_ID, document, reply_markup=markup)
    
    return


@dp.callback_query_handler(permit_request.filter())
async def permit_request_callback_query(call: types.CallbackQuery, callback_data: dict):
    user = UserModel.get(call.from_user.id)
    user.update_subscribe_date(datetime.now())

    await bot.answer_callback_query(call.id)
    await call.message.delete()
    
    text = 'Вашу заявку на підписку успішно схвалено'
    await bot.send_message(int(callback_data['action']), text)

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
        ),
        types.InlineKeyboardButton(
            text='speech_recognition',
            callback_data=ai.new('speech_recognition')
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

    text = f'''Ви вибрали {callback_data['action']}'''
    await bot.send_message(call.message.chat.id, text)


@dp.message_handler(IsChatGPTFilter(), content_types=['text'])
async def chatgpt(message: types.Message):
    user = UserModel.get(message.from_user.id)
    
    if not user.uses:
        await message.reply('У вас закінчились використання')
        
        return

    user.append_message('user', message.text)
    
    info = await message.reply('Завантаження')
    
    text = ''
    assistant_response = ''
    try:
        for sym in OpenAI.chatgpt(user.get_messages(), message.text):
            text += sym
            assistant_response += sym
                
            if '\n' in sym:
                await bot.send_message(message.from_id, text)
                    
                await info.delete()
                info = await message.reply('Завантаження')
                    
                text = ''

        if text:
            await bot.send_message(message.from_id, text)
            await info.delete()
        
        user.append_message('assistant', assistant_response)
        user.append_use()
    except Exception:
        await bot.send_message(message.from_id, 'Щось сталось не так')
        await info.delete()
        
        user.append_message('system', 'Error')


@dp.message_handler(IsDalleFilter(), content_types=['text', 'photo'])
async def dalle(message: types.Message):
    user = UserModel.get(message.from_user.id)

    if not user.uses:
        await message.reply('У вас закінчились використання')
        
        return

    info = await message.reply('Завантаження')
            
    try:
        if message.content_type == 'photo':
            file = await bot.get_file(message.photo[-1].file_id)
            image_url = f'https://api.telegram.org/file/bot{bot._token}/{file.file_path}'

            variation_image_url = OpenAI.dalle(image_url=image_url)
                    
            await bot.send_photo(message.from_id, variation_image_url)
            await info.delete()
            
            user.append_use()
                    
            return

        image_url = OpenAI.dalle(prompt=message.text)
    except Exception:
        if message.content_type == 'photo':
            text = 'Зображення має бути квадратним та меньшим 4MB'
        else:
            text = 'Щось пішло не так'

        await bot.send_message(message.from_id, text)
        await info.delete()
        
        return

    await bot.send_photo(message.from_id, image_url)
    await info.delete()
    user.append_use()


@dp.message_handler(IsTesseractFilter(), content_types=['photo'])
async def tesseract(message: types.Message):
    user = UserModel.get(message.from_user.id)

    if not user.uses:
        await message.reply('У вас закінчились використання')
        
        return
    
    user.append_use()

    info = await bot.send_message(message.from_id, 'Завантаження')
    try:
        file = await bot.get_file(message.photo[-1].file_id)
        image_url = f'https://api.telegram.org/file/bot{bot._token}/{file.file_path}'
        text = Tesseract.scan(image_url=image_url)
        user.append_use()
    except Exception:
        await info.delete()
        await bot.send_message(message.from_id, 'Щось сталось не так')        
        
        return

    await bot.send_message(message.from_id, text)
    await info.delete()
    user.append_use()


@dp.message_handler(IsSpeechRecognition(), content_types=['voice'])
async def speech_recognition(message: types.Message):
    user = UserModel.get(message.from_user.id)

    if not user.uses:
        await message.reply('У вас закінчились використання')

        return

    user.append_use()

    info = await bot.send_message(message.from_id, 'Завантаження')
    try:
        voice = await message.voice.get_url()
        voice_path = f'''tmp-{voice.split('/')[-1]}'''
        voice_wav_path = voice_path + 'wav'

        with open(voice_path, 'wb') as file:
            response = requests.get(voice)
            file.write(response.content)

        audio, samplerate = soundfile.read(voice_path)

        soundfile.write(voice_wav_path, audio, samplerate, format='WAV')

        text = SpeechRecognition.convert(voice_wav_path)

        os.remove(voice_path)
        os.remove(voice_wav_path)

        user.append_use()
    except Exception:
        await info.delete()
        await bot.send_message(message.from_id, 'Щось сталось не так')

        return

    await bot.send_message(message.from_id, text)
    await info.delete()
    user.append_use()


@dp.message_handler(IsAdminFilter(), commands=['permit'])
async def permit(message: types.Message):
    text = 'Done'
    
    await bot.send_message(message.from_id, text)


@dp.message_handler(IsNotRegisterUserFilter())
async def unregistered_user(message: types.Message):
    text = 'Зареєструйтесь будь ласка'
    await bot.send_message(message.from_id, text)


@dp.message_handler(IsRegisterUserFilter())
async def unregistered_mode(message: types.Message):
    text = 'Я вас не зрозумів. Переконайтесь що ви вибрали режим та вводите коректні дані'
    await bot.send_message(message.from_id, text)
