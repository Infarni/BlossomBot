#!/bin/env python3

import ujson
import logging

from aiogram import Bot, Dispatcher, executor, types

from handlers.chatgpt import get_stream


logging.basicConfig(level=logging.INFO)

with open('config.json', 'r') as file:
    config = ujson.loads(file.read())


bot = Bot(token=config['bot']['token'], parse_mode='html')
dp = Dispatcher(bot)

chatgpt_users_messages = {}


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    text = 'Привіт, це поки не закінчений бот, готуйтесь до багів!'

    await bot.send_message(message.from_id, text)


@dp.message_handler(commands=['help'])
async def help(message: types.Message):
    text = '''Тут поки пустовато але працюють пару команд, наприклад:
    /start - Запуск бота.
    /help - Отримати інструкції по використанню бота.
    /chatgpt {request} - Спілкування з ChatGPT.'''
    
    await bot.send_message(message.from_id, text)


@dp.message_handler(commands=['chatgpt'])
async def chat_gpt(message: types.Message):
    user_id = message.from_user.id
    if user_id not in chatgpt_users_messages.keys():
        chatgpt_users_messages[user_id] = []
    
    if len(chatgpt_users_messages[user_id]) > 30:
        del chatgpt_users_messages[user_id][0:20]

    alert = await bot.send_message(message.from_id, 'Завантаження...')

    message_text = message.text.split(' ')[-1]
    
    chatgpt_users_messages[user_id].append({'role': 'user', 'content': message_text})

    stream = get_stream(config, chatgpt_users_messages[user_id])
    
    full_text = ''
    event_text = ''
    for index, event in enumerate(stream):
        if index != 0 and event.data != '[DONE]':
            data = ujson.loads(event.data)['choices'][0]
            
            if data['finish_reason'] != 'stop':
                event_text += data['delta']['content']
                
                if event_text[-2:] == '\n\n':
                    await alert.delete()
                    await bot.send_message(message.from_id, event_text)
                    
                    full_text += event_text
                    event_text = ''
                    
                    alert = await bot.send_message(message.from_id, 'Завантаження...')
            else:
                await alert.delete()
                await bot.send_message(message.from_id, event_text)
                
                full_text += event_text
    
    chatgpt_users_messages[user_id].append({'role': 'assistant', 'content': full_text})


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, timeout=0, relax=0, loop=True)
