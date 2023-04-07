import os
import requests

import openai
import pytesseract

from io import BytesIO

from PIL import Image


pytesseract.pytesseract.tesseract_cmd = r'/bin/tesseract'


def get_openai_api_keys(token: str):
    response = requests.get(
        url='https://api.openai.com/dashboard/user/api_keys',
        headers={
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
    )

    return response.json()


def create_openai_api_key(token: str):
    response = requests.post(
        url='https://api.openai.com/dashboard/user/api_keys',
        json={'action': 'create'},
        headers={'Authorization': f'Bearer {token}'}
    )

    return response.json()


def delete_openai_api_key(token: str, created_at: int):
    response = requests.post(
        url='https://api.openai.com/dashboard/user/api_keys',
        json={
            'action': 'delete',
            'redacted_key': token,
            'created_at': created_at
        },
        headers={'Authorization': f'Bearer {token}'}
    )

    return response.json()


class OpenAI:
    def __init__(self, lang_code):
        self.messages = [
            {
                'role': 'system',
                'content': f'Language: {lang_code}'
            }
        ]

    def chatgpt(self, prompt):
        self.messages.append({'role': 'user', 'content': prompt})
        completion = openai.ChatCompletion.create(
            model='gpt-3.5-turbo',
            messages=self.messages,
            stream=True
        )

        self.messages.append({'role': 'assistant', 'content': ''})
        for item in completion:
            content = item['choices'][0]['delta'].get('content')
            
            if content:
                self.messages[-1]['content'] += content
                yield content

    def dalle(self, prompt='', image_url=None):
        if image_url:
            response = requests.get(image_url)
            image_path = rf'''media/{image_url.split('/')[-1]}.png'''
            image_file = Image.open(BytesIO(response.content))
            
            width, height = image_file.size
            if width > height:
                image_file.crop(
                    (
                        width / 2 - height / 2,
                        0,
                        width / 2 + height / 2,
                        height 
                    )
                ).save(image_path)
            else:
                image_file.crop(
                    (
                        0,
                        height / 2 - width / 2,
                        width,
                        height / 2 + width / 2
                    )
                ).save(image_path)
                
            image = openai.Image.create_variation(
                image=open(image_path, 'rb'),
                n=1,
            )
            
            os.remove(image_path)
            
            return image.data[0]['url']

        image = openai.Image.create(
            prompt=prompt,
            n=1
        )

        return image.data[0]['url']


class Tesseract:
    def scan(self, image_url, lang='ukr'):
        response = requests.get(image_url)
        image = Image.open(BytesIO(response.content))

        text = pytesseract.image_to_string(image, lang=lang)
        
        return text
