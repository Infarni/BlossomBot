#!/bin/env python3
import os
import logging
import sqlite3

import openai

from aiogram import executor

from bot import dp
from settings import OPENAI_TOKEN


def main():
    logging.basicConfig(level=logging.INFO)
    openai.api_key = OPENAI_TOKEN

    executor.start_polling(
        dp,
        skip_updates=True,
        timeout=0,
        relax=0,
        loop=True,
    )


if __name__ == '__main__':
    main()
