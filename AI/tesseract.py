import requests

import pytesseract

from io import BytesIO

from PIL import Image


class Tesseract:
    @staticmethod
    def scan(image_url, lang='ukr'):
        response = requests.get(image_url)
        image = Image.open(BytesIO(response.content))

        text = pytesseract.image_to_string(image, lang=lang)
        
        return text
