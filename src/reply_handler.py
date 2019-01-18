# coding=utf-8

from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters)
from telegram import *
from database_functions import *

class ForceReplyJobs(object):
    types_to_indices = {"auth":0, "game_title":1, "game_players":2, "expansion_for":3, "expansion_title":4, "expansion_poll_game":5, "date":6}
    indices_to_types = {0:"auth", 1:"game_title", 2:"game_players", 3:"expansion_for", 4:"expansion_title", 5:"expansion_poll_game", 6:"date"}

    def __init__(self):
        self.message_IDs = [[]]

    def is_set(self, id):
        no_types = len(self.message_IDs)
        for i in range(0,no_types):
            for message_id in self.message_IDs[i]:
                if message_id == id:
                    self.message_IDs[i].remove(message_id)
                    return self.indices_to_types[i]

    def add(self, id, reply_type):
        where = self.types_to_indices[reply_type]
        self.message_IDs[where].append(id)                    



def handle_reply(bot, update):
    print("\n\n\n\nYES IT NOTICED AND THIS WORKED OMG!!!! \n\n\n\n\n\n")
