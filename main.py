#!/bin/env python3
import os
import logging
import sqlite3

import openai

from aiogram import executor
from dotenv import dotenv_values


def load_vars():
    os.environ = os.environ | dotenv_values() | {'DATABASE': sqlite3.connect('db.sqlite3')}


def main():
    load_vars()

    logging.basicConfig(level=logging.INFO)
    openai.api_key = os.environ['OPENAI_TOKEN']
    
    from handlers.bot import dp

    executor.start_polling(
        dp,
        skip_updates=True,
        timeout=0,
        relax=0,
        loop=True,
    )


if __name__ == '__main__':
    main()
