#!/bin/env python3
import logging

import openai

from aiogram import executor

from bot import Dispatcher
from settings import OPENAI_TOKEN


def main():
    logging.basicConfig(level=logging.INFO)
    openai.api_key = OPENAI_TOKEN

    executor.start_polling(
        Dispatcher,
        skip_updates=True,
        timeout=0,
        relax=0,
        loop=True,
    )


if __name__ == '__main__':
    main()
