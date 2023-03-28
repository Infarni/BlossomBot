import requests

import sseclient


def get_stream(config: dict, body: list) -> sseclient.SSEClient:
    token = config['openai']['token']
    
    response = requests.post(
        'https://api.openai.com/v1/chat/completions',
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}'
        },
        json={
            'model': 'gpt-3.5-turbo',
            'messages': body,
            'temperature': 0.7,
            'stream': True
        },
        stream=True
    )

    client = sseclient.SSEClient(response)

    
    return client.events()
