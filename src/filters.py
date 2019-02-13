from telegram.ext import BaseFilter
from planning_functions import (GameNight, Poll)

class Vote(BaseFilter):
    name = 'Filters.vote'

    def filter(self, message):
        try:
            possible_votes = GameNight().poll.options
            return bool(message.text in possible_votes)
        except AttributeError:
            return False

