# coding=utf-8

import configparser
import os
from mysql.connector.errors import IntegrityError
from telegram import (ReplyKeyboardRemove, ForceReply, ReplyKeyboardMarkup,
                      KeyboardButton, ParseMode)
from telegram.error import BadRequest
import database_functions as dbf
import parse_strings as ps
from log_to_message import LogToMessageFilter
from calendarkeyboard import telegramcalendar
from planning_functions import GameNight
from singleton import Singleton
from inline_handler import (generate_categories, generate_household, generate_debug, generate_csv_import)
from query_buffer import QueryBuffer
from error_handler import handle_bot_not_admin
from parse_strings import read_json


# keeps track of ForceReplys not being answered
# dictionaries types_to_indices and indices_to_types exist for readability

class ForceReplyJobs(Singleton):
    types_to_indices = {"auth": 0, "game_title": 1, "game_players": 2,
                        "expansion_for": 3, "expansion_title": 4,
                        "expansion_poll_game": 5, "date": 6, "csv": 7,
                        "expansions_list": 8}
    indices_to_types = {0: "auth", 1: "game_title", 2: "game_players",
                        3: "expansion_for", 4: "expansion_title",
                        5: "expansion_poll_game", 6: "date", 7: "csv",
                        8: "expansions_list"}

    def init(self):
        # we can't append on unknown items, so INIT the Array
        self.message_IDs = [[], [], [], [], [], [], [], [], []]

    # Searches through all the Replys we are waiting on if we are
    # waiting on a reply to "reply_to_id".
    # If found, it returns the type of ForceReplyJob and removes
    # the message from the ForceReplyJobs object.
    def is_set(self, reply_to_id):
        no_types = len(self.message_IDs)
        for i in range(0, no_types):
            for message_id in self.message_IDs[i]:
                if message_id == reply_to_id:
                    self.message_IDs[i].remove(message_id)
                    return self.indices_to_types[i]

    # If bot sends a ForceReply, register the message ID because
    # we are waiting on an answer.
    def add(self, reply_to_id, reply_type):
        where = self.types_to_indices[reply_type]
        if len(self.message_IDs[where]) >= 100:  # maybe a 100x100 matrix is too big? no idea...
            self.message_IDs[where] = self.message_IDs[where][50:]
        self.message_IDs[where].append(reply_to_id)

    def add_with_query(self, reply_to_id, reply_type, query):
        where = self.types_to_indices[reply_type]
        if len(self.message_IDs[where]) >= 100:  # maybe a 100x100 matrix is too big? no idea...
            self.message_IDs[where] = self.message_IDs[where][50:]
        self.message_IDs[where].append(reply_to_id)
        QueryBuffer().add(reply_to_id, query)

    def get_query(self, reply_to_id):
        return QueryBuffer().get_query(reply_to_id)

    def clear_query(self, reply_to_id):
        QueryBuffer().clear_query(reply_to_id)

    def edit_query(self, reply_to_id, query):
        QueryBuffer().edit_query(reply_to_id, query)


# depending on the type of Reply, call a handler function
def handle_reply(update, context):
    call_library = {"auth": auth, "game_title": game_title,
                    "game_players": game_players,
                    "expansion_for": expansion_for,
                    "expansion_title": expansion_title,
                    "expansion_poll_game": expansion_poll_game,
                    "date": date,
                    "csv": csv,
                    "expansions_list": expansions_list}

    try:
        which = ForceReplyJobs().is_set(
                    update.message.reply_to_message.message_id)
    except AttributeError:
        pass
    else:  # no exception
        try:
            call_library[which].__call__(update)
        except KeyError:  # this is what happens to normal text
            pass


# Checks the passphrase and adds the user's chat id
# into the auth-db if correct.
def auth(update):
    config = configparser.ConfigParser()
    config_path = os.path.dirname(os.path.realpath(__file__))
    config.read(os.path.join(config_path, "config.ini"))
    passphrase = config['Authentication']['password']

    if update.message.text == passphrase:
        try:
            update.message.bot.delete_message(update.message.chat_id,
                                              update.message.message_id)
        except BadRequest:
            handle_bot_not_admin(update.message.bot, update.message.chat_id)
        if not dbf.check_user(update.message.chat_id):
            if update.message.chat_id > 0:
                dbf.add_user_auth(update.message.chat_id, name=update.message.from_user.username)
                try:
                    msg = update.message.bot.send_message(
                            chat_id=update.message.chat_id,
                            text=read_json(["reply_handler", "auth", "ask_household"]),
                            reply_markup=generate_household(update.message.from_user.username, first=True))
                    query = "household," + update.message.from_user.username + ","
                    QueryBuffer().add(msg.message_id, query)
                except IndexError:  # first user
                    update.message.bot.send_message(chat_id=update.message.chat_id,
                                                    text=read_json(["reply_handler", "auth", "can_talk_now"]),
                                                    reply_markup=ReplyKeyboardRemove())
                    if LogToMessageFilter().ask_chat_type == "private":
                        update.message.bot.send_message(chat_id=update.message.chat_id,
                                                        text=read_json(["reply_handler", "auth", "ask_debug"]),
                                                        reply_markup=generate_debug())
            else:
                dbf.add_user_auth(update.message.chat_id)
                update.message.bot.send_message(chat_id=update.message.chat_id,
                                                text=read_json(["reply_handler", "auth", "can_talk_now"]),
                                                reply_markup=ReplyKeyboardRemove())
                if LogToMessageFilter().ask_chat_type == "group":
                    update.message.bot.send_message(chat_id=update.message.chat_id,
                                                    text=read_json(["reply_handler", "auth", "ask_debug"]),
                                                    reply_markup=generate_debug())
        else:
            update.message.reply_text(read_json(["reply_handler", "auth", "no_auth_needed"]),
                                      reply_markup=ReplyKeyboardRemove())
    else:
        update.message.reply_text(read_json(["reply_handler", "auth", "error_auth"]),
                                  reply_markup=ReplyKeyboardRemove())
        update.message.chat.leave()


# Provided the game title, the bot asks for the maximum player count.
def game_title(update):
    if "/stop" in update.message.text:
        ForceReplyJobs().clear_query(
            update.message.reply_to_message.message_id)
        update.message.reply_text(read_json(["reply_handler", "stop_interaction"]),
                                  reply_markup=ReplyKeyboardRemove())
    else:
        msg = update.message.reply_text(
                read_json(["reply_handler", "game_no_players"]).format(title=update.message.text),
                reply_markup=ForceReply())
        query = ForceReplyJobs().get_query(update.message.reply_to_message.message_id) + update.message.text
        ForceReplyJobs().clear_query(
            update.message.reply_to_message.message_id)
        ForceReplyJobs().add_with_query(
            msg.message_id, "game_players", query)


# Provided the game title and maximum player count,
# the bot asks for the categories it belongs into.
def game_players(update):
    if "/stop" in update.message.text:
        ForceReplyJobs().clear_query(
            update.message.reply_to_message.message_id)
        update.message.reply_text(read_json(["reply_handler", "stop_interaction"]),
                                  reply_markup=ReplyKeyboardRemove())
    else:
        query = ForceReplyJobs().get_query(update.message.reply_to_message.message_id) + "," + update.message.text + ","
        msg = update.message.reply_text(
                read_json(["reply_handler", "game_what_categories"]).format(title=ps.parse_csv_to_array(query)[2]),
                reply_markup=generate_categories(first=True))
        ForceReplyJobs().clear_query(
            update.message.reply_to_message.message_id)
        # not adding a new ForceReply because this happens inline
        QueryBuffer().add(msg.message_id, query)


# given the title of the boardgame, find out the boardgame_uuid
def expansion_for(update):
    if "/stop" in update.message.text:
        ForceReplyJobs().clear_query(
            update.message.reply_to_message.message_id)
        update.message.reply_text(read_json(["reply_handler", "stop_interaction"]),
                                  reply_markup=ReplyKeyboardRemove())
    # find uuid, if owner does not have this game, return
    else:
        query = ForceReplyJobs().get_query(
            update.message.reply_to_message.message_id)
        uuid = dbf.search_uuid(update.message.from_user.username,
                               update.message.text)
        if uuid:
            msg = update.message.reply_text(
                    read_json(["reply_handler", "expansion_for", "expansion_title"]).format(game=update.message.text),
                    reply_markup=ForceReply())
            query += "," + uuid  # query now has structure new_expansion, <owner>, <uuid>
            ForceReplyJobs().clear_query(
                update.message.reply_to_message.message_id)
            ForceReplyJobs().add_with_query(
                msg.message_id, "expansion_title", query)
        else:
            update.message.reply_text(read_json(["reply_handler", "expansion_for", "error_no_game"]),
                                      reply_markup=ReplyKeyboardRemove())
            ForceReplyJobs().clear_query(
                update.message.reply_to_message.message_id)


def expansion_title(update):
    if "/stop" in update.message.text:
        ForceReplyJobs().clear_query(
            update.message.reply_to_message.message_id)
        update.message.reply_text(read_json(["reply_handler", "stop_interaction"]),
                                  reply_markup=ReplyKeyboardRemove())
    else:
        query = ForceReplyJobs().get_query(update.message.reply_to_message.message_id) + "," + update.message.text
        # query has now structure new_expansion, <owner>, <uuid>, <exp_title>

        if ps.parse_csv_to_array(query)[0] == "new_expansion":
            try:
                dbf.add_expansion_into_db(ps.parse_csv_to_array(
                                            ps.remove_first_string(query)))
                # dbf.add_expansion_into_db(ps.parse_values_from_query(
                #                             ps.remove_first_string(query)))
            except IntegrityError:
                update.message.reply_text(
                        read_json(["reply_handler", "expansion_title", "known_expansion"]),
                        reply_markup=ReplyKeyboardRemove())
                return
            update.message.reply_text(
                read_json(["reply_handler", "expansion_title", "added_expansion"]),
                reply_markup=ReplyKeyboardRemove())
        else:
            pass  # no idea how we got here...
        ForceReplyJobs().clear_query(
            update.message.reply_to_message.message_id)


def expansions_list(update):
    if "/stop" in update.message.text:
        update.message.reply_text(read_json(["reply_handler", "stop_interaction"]),
                                  reply_markup=ReplyKeyboardRemove())
    else:
        msgtext = read_json(["reply_handler", "expansions_list", "expansions"])
        search = dbf.search_expansions_by_game(
                    update.message.from_user.username, update.message.text)
        if search is None:  # user owns game, but no expansions
            update.message.reply_text(read_json(["reply_handler", "expansions_list", "no_expansions"]))
        elif not search:  # user doesn't own this game
            update.message.reply_text(read_json(["reply_handler", "expansions_list", "error_no_game"]))
        else:
            gamestring = ps.parse_db_entries_to_messagestring(search)
            msgtext += gamestring
            update.message.reply_text(msgtext)


def expansion_poll_game(update):
    if "/stop" in update.message.text:
        update.message.reply_text(read_json(["reply_handler", "stop_interaction"]),
                                  reply_markup=ReplyKeyboardRemove())
    else:
        plan = GameNight()
        check = plan.set_poll(update.message.from_user.username,
                              game=update.message.text)
        if check < 0:
            update.message.reply_text(
                read_json(["reply_handler", "expansion_poll_game", "error_no_poll_expansion"]))
        else:
            keys = []
            for o in plan.poll.options:
                keys.append([KeyboardButton(o)])
            update.message.reply_text(read_json(["reply_handler", "expansion_poll_game", "what_expansion"]),
                                      reply_markup=ReplyKeyboardMarkup(
                                                    keys, one_time_keyboard=True))


# Parses csv data into the games table of datadb.
# Be careful with this, it could mess up the entire database if someone gets
# confused with a komma.
def csv(update):
    dbf.add_multiple_games_into_db(ps.parse_csv_import(update.message.text))
    old_msg_id = ForceReplyJobs().get_query(update.message.reply_to_message.message_id)
    if old_msg_id:  # have sent a message before
        ForceReplyJobs().clear_query(update.message.reply_to_message.message_id)
        update.message.bot.delete_message(update.message.chat_id, old_msg_id)
    last_line = ps.get_last_line(update.message.text)
    # "." and "-" must be escaped with "\" in MarkdownV2, "\" must be escaped in str
    msg = update.message.reply_text(read_json(["reply_handler", "csv"]).format(last_line=last_line),
                                    parse_mode=ParseMode.MARKDOWN_V2,
                                    reply_markup=generate_csv_import(update.message.reply_to_message.message_id))
    ForceReplyJobs().add_with_query(update.message.reply_to_message.message_id, "csv", str(msg.message_id))


def date(update):
    if "/stop" in update.message.text:
        update.message.reply_text(read_json(["reply_handler", "stop_interaction"]),
                                  reply_markup=ReplyKeyboardRemove())
    else:
        check = GameNight(update.message.chat.id).set_date(update.message.text)
        if check < 0:
            update.message.reply_text(read_json(["reply_handler", "date", "have_date_already"]),
                                      reply_markup=ReplyKeyboardRemove())
        else:
            config = configparser.ConfigParser()
            config_path = os.path.dirname(os.path.realpath(__file__))
            config.read(os.path.join(config_path, "config.ini"))
            title = config['GroupDetails']['title']
            try:
                update.message.bot.set_chat_title(
                    update.message.chat.id, title + ': ' + update.message.text)
            except BadRequest:
                handle_bot_not_admin(update.message.bot, update.message.chat.id)
            update.message.reply_text(read_json(["reply_handler", "date", "date_set"]),
                                      reply_markup=ReplyKeyboardRemove())


def default(update):
    update.message.reply_text(read_json(["reply_handler", "default"]),
                              reply_markup=ReplyKeyboardRemove())
