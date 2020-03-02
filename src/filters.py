# coding=utf-8

from telegram.ext import BaseFilter
from planning_functions import GameNight


class Vote(BaseFilter):
    name = 'Filters.vote'

    def filter(self, message):
        try:
            possible_votes = GameNight().poll.options
        except AttributeError:
            return False
        if "group" in message.chat.type:
            return bool(message.text in possible_votes)
        else:
            return False
