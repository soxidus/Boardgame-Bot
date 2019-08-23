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
        else:
            return bool(message.text in possible_votes)
