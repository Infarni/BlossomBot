import os

import requests
import openai

from io import BytesIO

from PIL import Image


class OpenAI:
    @staticmethod
    def chatgpt(messages: list, prompt: str):
        completion = openai.ChatCompletion.create(
            model='gpt-3.5-turbo',
            messages=messages,
            stream=True
        )

        text = ''
        for item in completion:
            content = item['choices'][0]['delta'].get('content')
            
            if content:
                text += content
                yield content

    @staticmethod
    def dalle(prompt='', image_url=None):
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
