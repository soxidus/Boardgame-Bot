# coding=utf-8

import configparser
import os

from telegram import (ReplyKeyboardRemove, ForceReply, ReplyKeyboardMarkup,
                      KeyboardButton)
import database_functions as dbf
import parse_strings as ps
from calendar_export import create_ics_file
from calendarkeyboard import telegramcalendar
from planning_functions import GameNight
from singleton import Singleton
from inline_handler import generate_categories
from query_buffer import QueryBuffer


# keeps track of ForceReplys not being answered
# dictionaries types_to_indices and indices_to_types exist for readability

class ForceReplyJobs(Singleton):
    types_to_indices = {"auth": 0, "game_title": 1, "game_players": 2,
                        "expansion_for": 3, "expansion_title": 4,
                        "expansion_poll_game": 5, "date": 6, "csv": 7,
                        "household": 8, "expansions_list": 9}
    indices_to_types = {0: "auth", 1: "game_title", 2: "game_players",
                        3: "expansion_for", 4: "expansion_title",
                        5: "expansion_poll_game", 6: "date", 7: "csv",
                        8: "household", 9: "expansions_list"}

    def init(self):
        # we can't append on unknown items, so INIT the Array
        self.message_IDs = [[], [], [], [], [], [], [], [], [], []]

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
                    "expansion_poll_game": expansion_poll_game, "date": date,
                    "csv": csv, "household": household,
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
        update.message.bot.delete_message(update.message.chat_id,
                                          update.message.message_id)
        if not dbf.check_user(update.message.chat_id):
            dbf.add_user_auth(update.message.chat_id)
            if update.message.chat_id > 0:
                msg = update.message.bot.send_message(
                        chat_id=update.message.chat_id,
                        text='Super! Wir dürfen jetzt miteinander reden. '
                        'Noch eine Frage: Wohnst du vielleicht mit einem '
                        '(oder mehreren) '
                        'der Gruppenmitglieder zusammen? '
                        'Wenn ja, verrate mir doch bitte den '
                        'entsprechenden Alias(e)! '
                        'Bei mehr als einem Mitbewohner trenne die Aliase '
                        'mit einem Leerzeichen. '
                        'Wenn nicht, dann antworte bitte mit /stop.',
                        reply_markup=ForceReply())
                ForceReplyJobs().add(msg.message_id, "household")
            else:
                update.message.bot.send_message(chat_id=update.message.chat_id,
                                 text='Super! Wir dürfen jetzt '
                                      'miteinander reden.',
                                 reply_markup=ReplyKeyboardRemove())
        else:
            update.message.reply_text("Du musst das Passwort nicht nochmal "
                                      "eingeben... Rede einfach mit mir!",
                                      reply_markup=ReplyKeyboardRemove())
    else:
        update.message.reply_text("Schade, das hat leider nicht funktioniert. "
                                  "Mach es gut!",
                                  reply_markup=ReplyKeyboardRemove())
        update.message.chat.leave()


def household(update):
    if update.message.text == "/stop":
        update.message.reply_text('Okay, ich weiß Bescheid.',
                                  reply_markup=ReplyKeyboardRemove())
    else:
        users = [update.message.from_user.username] + update.message.text.split()
        dbf.add_household(users)
        update.message.reply_text('Okay, ich weiß Bescheid.',
                                  reply_markup=ReplyKeyboardRemove())


# Provided the game title, the bot asks for the maximum player count.
def game_title(update):
    if update.message.text == "/stop":
        ForceReplyJobs().clear_query(
            update.message.reply_to_message.message_id)
        update.message.reply_text('Okay, hier ist nichts passiert.',
                                  reply_markup=ReplyKeyboardRemove())
    else:
        msg = update.message.reply_text(
                'Mit wie vielen Leuten kann man ' + update.message.text +
                ' maximal spielen?\n'
                'Anworte mit EINER Zahl oder einem X, wenn es mit unendlich '
                'vielen gespielt werden kann.\n '
                'Antworte mit /stop, um abzubrechen.',
                reply_markup=ForceReply())
        query = ForceReplyJobs().get_query(update.message.reply_to_message.message_id) + update.message.text
        ForceReplyJobs().clear_query(
            update.message.reply_to_message.message_id)
        ForceReplyJobs().add_with_query(
            msg.message_id, "game_players", query)


# Provided the game title and maximum player count,
# the bot asks for the categories it belongs into.
def game_players(update):
    if update.message.text == "/stop":
        ForceReplyJobs().clear_query(
            update.message.reply_to_message.message_id)
        update.message.reply_text('Okay, hier ist nichts passiert.',
                                  reply_markup=ReplyKeyboardRemove())
    else:
        query = ForceReplyJobs().get_query(update.message.reply_to_message.message_id) + "," + update.message.text + ","
        msg = update.message.reply_text(
                'In welche Kategorien passt ' + ps.parse_csv(query)[2] +
                ' am besten?\n'
                'Wähle so viele, wie du willst, und drücke dann '
                'auf \'Fertig\'.',
                reply_markup=generate_categories(first=True))
        ForceReplyJobs().clear_query(
            update.message.reply_to_message.message_id)
        # not adding a new ForceReply because this happens inline
        QueryBuffer().add(msg.message_id, query)


# given the title of the boardgame, find out the boardgame_uuid
def expansion_for(update):
    if update.message.text == "/stop":
        ForceReplyJobs().clear_query(
            update.message.reply_to_message.message_id)
        update.message.reply_text('Okay, hier ist nichts passiert.',
                                  reply_markup=ReplyKeyboardRemove())
    # find uuid, if owner does not have this game, return
    else:
        query = ForceReplyJobs().get_query(
            update.message.reply_to_message.message_id)
        uuid = dbf.search_uuid(update.message.from_user.username,
                               update.message.text)
        if uuid:
            msg = update.message.reply_text(
                    'Wie heißt deine Erweiterung für ' +
                    update.message.text + '?\n'
                    'Antworte mit /stop, um abzubrechen.',
                    reply_markup=ForceReply())
            query += "," + uuid  # query now has structure new_expansion, <owner>, <uuid>
            ForceReplyJobs().clear_query(
                update.message.reply_to_message.message_id)
            ForceReplyJobs().add_with_query(
                msg.message_id, "expansion_title", query)
        else:
            update.message.reply_text('Mir ist nicht bekannt, dass du dieses '
                                      'Spiel hast. Du kannst es gerne mit '
                                      '/neuesspiel hinzufügen.',
                                      reply_markup=ReplyKeyboardRemove())
            ForceReplyJobs().clear_query(
                update.message.reply_to_message.message_id)


def expansion_title(update):
    if update.message.text == "/stop":
        ForceReplyJobs().clear_query(
            update.message.reply_to_message.message_id)
        update.message.reply_text('Okay, hier ist nichts passiert.',
                                  reply_markup=ReplyKeyboardRemove())
    else:
        query = ForceReplyJobs().get_query(update.message.reply_to_message.message_id) + "," + update.message.text
        # query has now structure new_expansion, <owner>, <uuid>, <exp_title>

        if ps.parse_csv(query)[0] == "new_expansion":
            # the probability of one person having the two expansions of
            # the same title for different games is close to 0, so...
            # just check for owner-exp combination
            known_exp = dbf.search_entries_by_user(
                dbf.choose_database("testdb"), 'expansions',
                update.message.from_user.username)
            for _ in range(len(known_exp)):
                # check whether this title has already been added for this user
                if known_exp[_][0] == update.message.text:
                    update.message.reply_text(
                        "Wusste ich doch: Diese Erweiterung hast du schon "
                        "einmal eingetragen. Viel Spaß noch damit!",
                        reply_markup=ReplyKeyboardRemove())
                    return
            dbf.add_expansion_into_db(ps.parse_values_from_array(
                                        ps.remove_first_string(query)))
            update.message.reply_text(
                "Okay, die Erweiterung wurde hinzugefügt \\o/",
                reply_markup=ReplyKeyboardRemove())
        else:
            pass  # no idea how we got here...
        ForceReplyJobs().clear_query(
            update.message.reply_to_message.message_id)


def expansions_list(update):
    msgtext = 'Du hast folgende Erweiterungen:\n'
    search = dbf.search_expansions_by_game(
                dbf.choose_database("testdb"), 'expansions',
                update.message.from_user.username, update.message.text)
    if search is None:  # user owns game, but no expansions
        update.message.reply_text('Du besitzt keine Erweiterungen zu diesem Spiel. '
                                  'Falls doch, dann ist jetzt ein guter Zeitpunkt, '
                                  'mir das mit /neueerweiterung mitzuteilen!')
    elif not search:  # user doesn't own this game
        update.message.reply_text('Du besitzt dieses Spiel nicht. '
                                  'Falls doch, dann ist jetzt ein guter Zeitpunkt, '
                                  'mir das mit /neuesspiel mitzuteilen!')
    else:
        gamestring = ps.to_messagestring(search)
        msgtext += gamestring
        update.message.reply_text(msgtext)


def expansion_poll_game(update):
    plan = GameNight()
    check = plan.set_poll(update.message.from_user.username,
                          game=update.message.text)
    if check < 0:
        update.message.reply_text(
            'Das war leider nichts. Dies könnte verschiedene Gründe haben:\n\n'
            '(1) Ihr habt kein Datum festgelegt. Holt das mit '
            '/neuertermin nach.\n'
            '(2) Du bist nicht zum Spieleabend angemeldet. '
            'Hole das mit /ich nach.\n'
            '(3) Mir ist nicht bekannt, dass einer der Teilnehmenden eine '
            'Erweiterung für dieses Spiel hat.'
            'Wenn das jedoch der Fall ist, sagt mir mit /neue_erweiterung '
            'Bescheid (natürlich im Privatchat!')
    else:
        keys = []
        for o in plan.poll.options:
            keys.append([KeyboardButton(o)])
        update.message.reply_text('Welche Erweiterung wollt ihr spielen?',
                                  reply_markup=ReplyKeyboardMarkup(
                                      keys, one_time_keyboard=True))


# Parses csv data into the games table of testdb.
# Be careful with this, it could mess up the entire database if someone gets
# confused with a komma.
def csv(update):
    dbf.add_multiple_games_into_db(ps.parse_csv_import(update.message.text))

    update.message.reply_text('OKAY, ich habe die Spiele alle eingetragen.',
                              reply_markup=ReplyKeyboardRemove())


def date(update):
    check = GameNight(update.message.chat.id).set_date(update.message.text)
    if check < 0:
        update.message.reply_text("Melde dich doch einfach mit /ich "
                                  "beim festgelegten Termin an.",
                                  reply_markup=ReplyKeyboardRemove())
    else:
        update.message.bot.set_chat_title(
            update.message.chat.id, 'Spielwiese: ' + update.message.text)
        update.message.reply_text("Okay, schrei einfach /ich, "
                                  "wenn du teilnehmen willst!",
                                  reply_markup=ReplyKeyboardRemove())


def default(update):
    update.message.reply_text("Ja... Bald...",
                              reply_markup=ReplyKeyboardRemove())


# as of now, we only have the calendar as an inline feature
# if that changes, we need to distinguish the kind of inline callback!
def handle_inline(update, context):
    selected, date, user_inp_req = telegramcalendar.process_calendar_selection(update, context)
    if selected:
        if user_inp_req:
            msg = context.bot.send_message(
                chat_id=update.callback_query.message.chat_id,
                text='Okay, wann wollt ihr spielen?',
                reply_markup=ForceReply())
            ForceReplyJobs().add(msg.message_id, "date")
        elif date:
            check = GameNight(chat_id=update.callback_query.message.chat_id).set_date(date.strftime("%d/%m/%Y"))
            if check < 0:
                context.bot.send_message(
                    chat_id=update.callback_query.message.chat_id,
                    text="Melde dich doch einfach mit /ich "
                         "beim festgelegten Termin an.",
                    reply_markup=ReplyKeyboardRemove())
            else:
                context.bot.set_chat_title(
                    update.callback_query.message.chat_id,
                    'Spielwiese: ' + date.strftime("%d/%m/%Y"))
                create_ics_file("Spieleabend", date)
                context.bot.send_message(
                    chat_id=update.callback_query.message.chat_id,
                    text="Okay, schrei einfach /ich, wenn du "
                         "teilnehmen willst!",
                    reply_markup=ReplyKeyboardRemove())
