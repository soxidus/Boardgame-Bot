# coding=utf-8

from telegram import (ReplyKeyboardRemove, ForceReply)
from database_functions import *
from planning_functions import GameNight
from singleton import Singleton


# keeps track of ForceReplys not being answered
# dictionaries types_to_indices and indices_to_types exist for readability
# TODO: At some point, we should implement periodic deletion of old message_ID entries!!
class ForceReplyJobs(Singleton):
    types_to_indices = {"auth": 0, "game_title": 1, "game_players": 2, "expansion_for": 3, "expansion_title": 4,
                        "expansion_poll_game": 5, "date": 6, "csv": 7}
    indices_to_types = {0: "auth", 1: "game_title", 2: "game_players", 3: "expansion_for", 4: "expansion_title",
                        5: "expansion_poll_game", 6: "date", 7: "csv"}

    def init(self):
        # we can't append on unknown items, so INIT the Array or find an other Solution
        self.message_IDs = [[], [], [], [], [], [], [], []]
        # self.queries is a table of mid's we're waiting on, and the query that has been collected so far (used for neues_spiel and neue_erweiterung)
        self.queries = []

    # Searches through all the Replys we are waiting on if we are waiting on a reply to "reply_to_id".
    # If found, it returns the type of ForceReplyJob and removes the message from the ForceReplyJobs object.
    def is_set(self, reply_to_id):
        no_types = len(self.message_IDs)
        for i in range(0, no_types):
            for message_id in self.message_IDs[i]:
                if message_id == reply_to_id:
                    self.message_IDs[i].remove(message_id)
                    return self.indices_to_types[i]

    # If bot sends a ForceReply, register the message ID because we are waiting on an answer.
    def add(self, reply_to_id, reply_type):
        where = self.types_to_indices[reply_type]
        self.message_IDs[where].append(reply_to_id)

    def add_with_query(self, reply_to_id, reply_type, query):
        where = self.types_to_indices[reply_type]
        self.message_IDs[where].append(reply_to_id)
        self.queries.append([reply_to_id, query])

    def get_query(self, reply_to_id):
        for entry in self.queries:
            if entry[0] == reply_to_id:
                return entry[1]

    def clear_query(self, reply_to_id):
        for entry in self.queries:
            if entry[0] == reply_to_id:
                self.queries.remove(entry)


# depending on the type of Reply, call a handler function
def handle_reply(bot, update):
    call_library = {"auth": auth, "game_title": game_title, "game_players": game_players, "expansion_for": default,
                    "expansion_title": default, "expansion_poll_game": default,
                    "date": date, "csv": csv}

    try:
        which = ForceReplyJobs().is_set(update.message.reply_to_message.message_id)
    except AttributeError:
        print("Reply Handling failed.")
    else:
        try:
            call_library[which].__call__(update)
        except KeyError: # this is what happens to normal text
            pass


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
        ForceReplyJobs().clear_query(update.message.reply_to_message.message_id)
        update.message.reply_text('Okay, hier ist nichts passiert.',
                                  reply_markup=ReplyKeyboardRemove())
    else:
        msg = update.message.reply_text('Mit wie vielen Leuten kann man ' +
                                        update.message.text +
                                        ' maximal spielen?\n'
                                        'Anworte mit EINER Zahl oder einem X, wenn es mit unendlich vielen gespielt '
                                        'werden '
                                        'kann.\n '
                                        'Antworte mit /stop, um abzubrechen.',
                                        reply_markup=ForceReply())
        query = ForceReplyJobs().get_query(update.message.reply_to_message.message_id) + update.message.text
        ForceReplyJobs().clear_query(update.message.reply_to_message.message_id)
        ForceReplyJobs().add_with_query(msg.message_id, "game_players", query)


# Provided the game title and maximum player count, the new game is added into the games table of testdb.
def game_players(update):
    if update.message.text == "/stop":
        ForceReplyJobs().clear_query(update.message.reply_to_message.message_id)
        update.message.reply_text('Okay, hier ist nichts passiert.',
                                  reply_markup=ReplyKeyboardRemove())
    else:
        query = ForceReplyJobs().get_query(update.message.reply_to_message.message_id) + "," + update.message.text + "," + generate_uuid_32()

        if parse_csv(query)[0] == "new_game":
            known_games = search_entries_by_user(choose_database("testdb"), 'games', update.message.from_user.username)
            for _ in range(len(known_games)):
                if known_games[_][0] == parse_csv(query)[2]: # check whether this title has already been added for this user
                    update.message.reply_text("Wusste ich doch: Das Spiel hast du schon einmal eingetragen. Viel Spaß noch damit!",
                                              reply_markup=ReplyKeyboardRemove())
                    return
            add_game_into_db(parse_values_from_array(remove_first_string(query)))
            update.message.reply_text("Okay, das Spiel wurde hinzugefügt \\o/",
                                      reply_markup=ReplyKeyboardRemove())
        else:
            pass
        ForceReplyJobs().clear_query(update.message.reply_to_message.message_id)


# Parses csv data into the games table of testdb.
# Be careful with this, it could mess up the entire database if someone gets confused with a komma.
def csv(update):
    add_multiple_games_into_db(parse_csv_import(update.message.text))

    update.message.reply_text('OKAY, ich habe die Spiele alle eingetragen.',
                              reply_markup=ReplyKeyboardRemove())


def date(update):
    check = GameNight().set_date(update.message.text)
    if check < 0:
        update.message.reply_text("Melde dich doch einfach mit /ich beim festgelegten Termin an.",
                                  reply_markup=ReplyKeyboardRemove())
    else:
        update.message.bot.set_chat_title(update.message.chat.id, 'Spielwiese am ' + update.message.text)
        update.message.reply_text("Okay, schrei einfach /ich, wenn du teilnehmen willst!",
                                  reply_markup=ReplyKeyboardRemove())


def default(update):
    update.message.reply_text("Ja... Bald...",
                              reply_markup=ReplyKeyboardRemove())
