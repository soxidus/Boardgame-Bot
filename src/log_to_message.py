import io
import sys
import logging
from singleton import Singleton


class LogToMessageFilter(logging.Filter, Singleton):
    ask_chat_type = None
    chat_id = None
    bot = None
    formatter = None

    def set_bot(self, bot):
        self.bot = bot

    def set_chat_id(self, chat_id):
        self.chat_id = chat_id
        self.ask_chat_type = None

    def set_chat_type(self, chat_type):
        self.ask_chat_type = chat_type

    def set_formatter(self, formatter):
        self.formatter = formatter

    def filter(self, record):
        self.formatter.format(record)
        message = '{} - {} - {} - {} - {}'.format(record.asctime, record.name, record.levelname, record.message, record.exc_text)        
        if self.chat_id and self.bot:
            self.bot.send_message(self.chat_id, message)
        else:
            print(message, sys.stderr)
