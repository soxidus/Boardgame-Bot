# coding=utf-8

from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters)
from telegram import *
from database_functions import *


class ForceReplyJobs(object):
    types_to_indices = {"auth": 0, "game_title": 1, "game_players": 2, "expansion_for": 3, "expansion_title": 4,
                        "expansion_poll_game": 5, "date": 6}
    indices_to_types = {0: "auth", 1: "game_title", 2: "game_players", 3: "expansion_for", 4: "expansion_title",
                        5: "expansion_poll_game", 6: "date"}

    def __init__(self):
        #   we can't append on unknown items, so INIT the Array or find an other Solution
        self.message_IDs = [[], [], [], [], [], [], []]

    def is_set(self, id):
        no_types = len(self.message_IDs)
        for i in range(0, no_types):
            for message_id in self.message_IDs[i]:
                if message_id == id:
                    self.message_IDs[i].remove(message_id)
                    return self.indices_to_types[i]

    def add(self, id, reply_type):
        where = self.types_to_indices[reply_type]
        self.message_IDs[where].append(id)


def init_reply_jobs():
    global reply_jobs
    reply_jobs = ForceReplyJobs()


def handle_reply(bot, update):
    dispatch = {"auth": auth, "game_title": game_title, "game_players": default, "expansion_for": default,
                "expansion_title": default, "expansion_poll_game": default, "date": default}

    try:
        which = reply_jobs.is_set(update.message.reply_to_message.message_id)
    except AttributeError:
        print("Nope")
        return
    dispatch[which].__call__(update)


def auth(update):
    passphrase = "Minze"

    if update.message.text == passphrase:
        if not check_user(update.message.chat_id):
            add_user_auth(update.message.chat_id)
            update.message.reply_text("Super! Wir dürfen jetzt miteinander reden.", reply_markup = ReplyKeyboardRemove())
        else:
            update.message.reply_text("Du musst das Passwort nicht nochmal eingeben... Rede einfach mit mir!")
    else:
        update.message.reply_text("Schade, das hat leider nicht funktioniert. Mach es gut!")
        update.message.chat.leave()


def game_title(update):
        update.message.reply_text("great!!!")


def default(update):
    update.message.reply_to("Ja... Bald...")
