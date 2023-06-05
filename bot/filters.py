from aiogram import types
from aiogram.dispatcher.filters import Filter

from models import UserModel
from settings import OWNER_ID


class IsAdminFilter(Filter):
    key = 'is_admin'
    
    async def check(self, message: types.Message):
        return message.from_user.id == OWNER_ID


class IsNotRegisterUserFilter(Filter):
    key = 'is_not_register_user'
    
    async def check(self, message: types.Message):
        return not UserModel.get(message.from_user.id)


class IsRegisterUserFilter(Filter):
    key = 'is_register_user'
    
    async def check(self, message: types.Message):
        return UserModel.get(message.from_user.id)


class IsAICheck(Filter):
    key = ''
    ai = ''
    
    async def check(self, message: types.Message):
        user = UserModel.get(message.from_user.id)
        
        if user:
            return user.mode == self.ai
        
        return False


class IsSubscribeFilter(IsAICheck):
    key = 'is_mode_subscribe'
    ai = 'subscribe'


class IsChatGPTFilter(IsAICheck):
    key = 'is_mode_chatgpt'
    ai = 'chatgpt'


class IsDalleFilter(IsAICheck):
    key = 'is_mode_dall-e'
    ai = 'dall-e'


class IsTesseractFilter(IsAICheck):
    key = 'is_mode_tesseract'
    ai = 'tesseract'


class IsSpeechRecognition(IsAICheck):
    key = 'is_mode_speech_recognition'
    ai = 'speech_recognition'
