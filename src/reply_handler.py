# coding=utf-8

from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove)
import database_functions
import parse_strings
import planning_functions

# keeps track of ForceReplys not being answered
# dictionaries types_to_indices and indices_to_types exist for readability
class ForceReplyJobs(object):
    types_to_indices = {"auth": 0, "game_title": 1, "game_players": 2, "expansion_for": 3, "expansion_title": 4,
                        "expansion_poll_game": 5, "date": 6, "game_max": 7, "csv": 8}
    indices_to_types = {0: "auth", 1: "game_title", 2: "game_players", 3: "expansion_for", 4: "expansion_title",
                        5: "expansion_poll_game", 6: "date", 7: "game_max", 8: "csv"}

    def __init__(self):
        #   we can't append on unknown items, so INIT the Array or find an other Solution
        self.message_IDs = [[], [], [], [], [], [], [], [], []]
        self.query_string = ''

    # Searches through all the Replys we are waiting on if we are waiting on a reply to "id".
    # If found, it returns the type of ForceReplyJob and removes the message from the ForceReplyJobs object.
    def is_set(self, id):
        no_types = len(self.message_IDs)
        for i in range(0, no_types):
            for message_id in self.message_IDs[i]:
                if message_id == id:
                    self.message_IDs[i].remove(message_id)
                    return self.indices_to_types[i]

    # If bot sends a ForceReply, register the message ID because we are waiting on an answer.
    def add(self, id, reply_type):
        where = self.types_to_indices[reply_type]
        self.message_IDs[where].append(id)

    def add_with_query(self, id, reply_type, query):
        where = self.types_to_indices[reply_type]
        self.message_IDs[where].append(id)
        self.query_string += query

    def get_query(self):
        return self.query_string

    def clear_query(self):
        self.query_string = ''


def init_reply_jobs():
    global reply_jobs
    reply_jobs = ForceReplyJobs()

# depending on the type of Reply, call a handler function
def handle_reply(bot, update):
    call_library = {"auth": auth, "game_title": game_title, "game_players": default, "expansion_for": default,
                    "expansion_title": default, "expansion_poll_game": default,
                    "date": default, "game_max": game_max, "csv": csv}

    try:
        which = reply_jobs.is_set(update.message.reply_to_message.message_id)
    except AttributeError:
        print("Reply Handling failed.")
        return

    call_library[which].__call__(update)

# Checks the passphrase and adds the user's chat id into the auth-db if correct.
def auth(update):
    passphrase = "Minze"

    if update.message.text == passphrase:
        if not check_user(update.message.chat_id):
            add_user_auth(update.message.chat_id)
            update.message.reply_text("Super! Wir dürfen jetzt miteinander reden.",
                                      reply_markup=ReplyKeyboardRemove())
        else:
            update.message.reply_text("Du musst das Passwort nicht nochmal eingeben... Rede einfach mit mir!", 
                                        reply_markup=ReplyKeyboardRemove())
    else:
        update.message.reply_text("Schade, das hat leider nicht funktioniert. Mach es gut!",
                                    reply_markup=ReplyKeyboardRemove())
        update.message.chat.leave()

# Provided the game title, the bot asks for the maximum player count.
def game_title(update):
    if update.message.text == "/stop":
        reply_jobs.clear_query()
        update.message.reply_text('Okay, hier ist nichts passiert.',
                                    reply_markup=ReplyKeyboardRemove())
    else:
        msg = update.message.reply_text('Mit wie vielen Leuten kann man ' +
                                        update.message.text +
                                        ' maximal spielen?\n'
                                        'Anworte mit EINER Zahl oder einem X, wenn es mit unendlich vielen gespielt werden '
                                        'kann.\n '
                                        'Antworte mit /stop, um abzubrechen.',
                                        reply_markup=ForceReply())
        reply_jobs.add_with_query(msg.message_id, "game_max", update.message.text)

# Provided the game title and maximum player count, the new game is added into the games table of testdb.
def game_max(update):
    if update.message.text == "/stop":
        reply_jobs.clear_query()
        update.message.reply_text('Okay, hier ist nichts passiert.',
                                    reply_markup=ReplyKeyboardRemove())
    else:
        query = reply_jobs.get_query() + "," + update.message.text + "," + generate_uuid_32()

        if parse_csv(query)[0] == "new_game":
            add_game_into_db(parse_values_from_array(remove_first_string(query)))
            update.message.reply_text("Okay, das Spiel wurde hinzugefügt  \o/", 
                                        reply_markup=ReplyKeyboardRemove())
        else:
            pass
        reply_jobs.clear_query()

# Parses csv data into the games table of testdb. 
# Be careful with this, it could mess up the entire database if someone gets confused with a komma.
def csv(update):
    add_multiple_games_into_db(parse_csv_import(update.message.text))

    update.message.reply_text('OKAY, ich habe die Spiele alle eingetragen.',
                            reply_markup=ReplyKeyboardRemove())

def date(update):
    update.message.reply_text("Okay, schrei einfach /ich, wenn du teilnehmen willst!",
                                reply_markup=ReplyKeyboardRemove())


def default(update):
    update.message.reply_text("Ja... Bald...", 
                            reply_markup=ReplyKeyboardRemove())

