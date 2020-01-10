# coding=utf-8

import configparser
import os
from random import randrange
from telegram.error import BadRequest
from telegram import (InlineKeyboardButton, InlineKeyboardMarkup,
                      ReplyKeyboardRemove, ForceReply, 
                      KeyboardButton, ReplyKeyboardMarkup)
from calendarkeyboard import telegramcalendar
from planning_functions import GameNight
from query_buffer import QueryBuffer
from parse_strings import single_db_entry_to_string
import reply_handler as rep
import database_functions as dbf
import parse_strings as ps


def handle_inline(bot, update):
    if "CALENDAR" in update.callback_query.data:
        handle_calendar(bot, update)
    elif "CATEGORY" in update.callback_query.data:
        handle_category(bot, update)
    elif "FINDBY" in update.callback_query.data:
        handle_findbycategory(bot, update)
    elif "POLLBY" in update.callback_query.data:
        handle_pollbycategory(bot, update)


def handle_calendar(bot, update):
    selected, date, user_inp_req = telegramcalendar.process_calendar_selection(bot, update)
    if selected:
        if user_inp_req:
            msg = bot.send_message(
                chat_id=update.callback_query.message.chat_id,
                text='Okay, wann wollt ihr spielen?',
                reply_markup=ForceReply())
            rep.ForceReplyJobs().add(msg.message_id, "date")
        elif date:
            check = GameNight(chat_id=update.callback_query.message.chat_id).set_date(date.strftime("%d/%m/%Y"))
            if check < 0:
                bot.send_message(
                    chat_id=update.callback_query.message.chat_id,
                    text="Melde dich doch einfach mit /ich "
                         "beim festgelegten Termin an.",
                    reply_markup=ReplyKeyboardRemove())
            else:
                bot.set_chat_title(
                    update.callback_query.message.chat_id,
                    'Spielwiese: ' + date.strftime("%d/%m/%Y"))
                bot.send_message(
                    chat_id=update.callback_query.message.chat_id,
                    text="Okay, schrei einfach /ich, wenn du "
                         "teilnehmen willst!",
                    reply_markup=ReplyKeyboardRemove())


def handle_category(bot, update):
    update.callback_query.answer()
    category = update.callback_query.data.split(";")[1]
    if category == "none":
        end_of_categories(bot, update, no_category=True)
    elif category == "stop":
        QueryBuffer().clear_query(update.callback_query.message.message_id)
        bot.send_message(
            chat_id=update.callback_query.message.chat_id,
            text='Okay, hier ist nichts passiert.',
            reply_markup=ReplyKeyboardRemove())
    elif category == "done":
        end_of_categories(bot, update)
    elif category == "IGNORE":
        pass
    else:  # we actually got a category, now register it
        if update.callback_query.data.split(";")[2] == "SET":
            query = QueryBuffer().get_query(update.callback_query.message.message_id) + category + "/"
            categories_so_far = ps.parse_csv(query)[-1].split('/')[:-1]  # last one is empty since set ends on /
            QueryBuffer().edit_query(update.callback_query.message.message_id, query)
            # change keyboard layout
            try:
                bot.edit_message_text(text=update.callback_query.message.text,
                                    chat_id=update.callback_query.message.chat_id,
                                    message_id=update.callback_query.message.message_id,
                                    reply_markup=generate_categories(pressed=categories_so_far))
            except BadRequest:
                pass
        elif update.callback_query.data.split(";")[2] == "UNSET":
            query = QueryBuffer().get_query(update.callback_query.message.message_id)
            query_csv = ps.parse_csv(query)
            categories_so_far = query_csv[-1].split('/')[:-1]
            categories_so_far.remove(category)
            categories_string = '/'.join(categories_so_far)
            if len(categories_string) > 0:
                categories_string += '/'
            new_query = ps.csv_to_string(query_csv[:-1]) + ',' + categories_string
            QueryBuffer().edit_query(update.callback_query.message.message_id, new_query)
            # change keyboard layout
            try:
                bot.edit_message_text(text=update.callback_query.message.text,
                                    chat_id=update.callback_query.message.chat_id,
                                    message_id=update.callback_query.message.message_id,
                                    reply_markup=generate_categories(pressed=categories_so_far))
            except BadRequest:
                pass


def end_of_categories(bot, update, no_category=False):
    if no_category:
        query = QueryBuffer().get_query(update.callback_query.message.message_id) + " ," + ps.generate_uuid_32()
    else:  # user pressed "Done"
        query = QueryBuffer().get_query(update.callback_query.message.message_id) + "," + ps.generate_uuid_32()

    if ps.parse_csv(query)[0] == "new_game":
        known_games = dbf.search_entries_by_user(
            dbf.choose_database("testdb"), 'games',
            update.callback_query.from_user.username)
        for _ in range(len(known_games)):
            # check whether this title has already been added for this user
            if known_games[_][0] == ps.parse_csv(query)[2]:
                bot.send_message(
                    chat_id=update.callback_query.message.chat_id,
                    text="Wusste ich doch: Das Spiel hast du schon "
                         "einmal eingetragen. Viel Spaß noch damit!",
                    reply_markup=ReplyKeyboardRemove())
                return
        dbf.add_game_into_db(ps.parse_values_from_array(
                                ps.remove_first_string(query)))
        bot.send_message(
                    chat_id=update.callback_query.message.chat_id,
                    text="Okay, das Spiel wurde hinzugefügt \\o/",
                    reply_markup=ReplyKeyboardRemove())
    else:
        pass
    QueryBuffer().clear_query(
        update.callback_query.message.message_id)


def generate_categories(first=False, pressed=None):
    keyboard = []
    config = configparser.ConfigParser(converters={'list': lambda x: [i.strip() for i in x.split(',')]})
    config_path = os.path.dirname(os.path.realpath(__file__))
    config.read(os.path.join(config_path, "config.ini"))
    categories = config.getlist('GameCategories','categories')  # no, this is no error. getlist is created by converter above
    for cat in categories:
        row = []
        if pressed and (cat in pressed):
            data = ";".join(["CATEGORY",cat,"UNSET"])
            label = cat + " ✓"
            row.append(InlineKeyboardButton(label, callback_data=data))
        else:
            data = ";".join(["CATEGORY",cat,"SET"])
            row.append(InlineKeyboardButton(cat, callback_data=data))
        keyboard.append(row)
    # last row: no statement and /stop button
    row = []
    if first:
        data = ";".join(["CATEGORY","none"])
        row.append(InlineKeyboardButton('keine Angabe', callback_data=data))
    else:
        data = ";".join(["CATEGORY","done"])
        row.append(InlineKeyboardButton('Fertig', callback_data=data))        
    data = ";".join(["CATEGORY","stop"])
    row.append(InlineKeyboardButton('Abbrechen', callback_data=data))
    keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)


def handle_findbycategory(bot, update):
    update.callback_query.answer()
    category = update.callback_query.data.split(";")[1]
    if category == "stop":
        bot.send_message(
            chat_id=update.callback_query.message.chat_id,
            text='Okay, hier ist nichts passiert.',
            reply_markup=ReplyKeyboardRemove())
    elif category == "IGNORE":
        pass
    else:  # got a category
        opt = []
        entries = dbf.get_playable_entries_by_category(
            dbf.choose_database("testdb"), 'games', 'title',
            update.callback_query.from_user.username, category)
        for e in entries:
            opt.append(single_db_entry_to_string(e))
        if opt:
            game = opt[randrange(len(opt))]
            bot.send_message(
                        chat_id=update.callback_query.message.chat_id,
                        text='Wie wäre es mit ' + game + '?',
                        reply_markup=ReplyKeyboardRemove())
        else:
            bot.send_message(
                        chat_id=update.callback_query.message.chat_id,
                        text='Du besitzt kein Spiel dieser Kategorie.',
                        reply_markup=ReplyKeyboardRemove())


def generate_findbycategory():
    keyboard = []
    config = configparser.ConfigParser(converters={'list': lambda x: [i.strip() for i in x.split(',')]})
    config_path = os.path.dirname(os.path.realpath(__file__))
    config.read(os.path.join(config_path, "config.ini"))
    categories = config.getlist('GameCategories','categories')  # no, this is no error. getlist is created by converter above
    for cat in categories:
        row = []
        data = ";".join(["FINDBY",cat])
        row.append(InlineKeyboardButton(cat, callback_data=data))
        keyboard.append(row)
    # last row: no statement and /stop button
    row = []      
    data = ";".join(["FINDBY","IGNORE"])
    row.append(InlineKeyboardButton(' ', callback_data=data))
    data = ";".join(["FINDBY","stop"])
    row.append(InlineKeyboardButton('Abbrechen', callback_data=data))
    keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)


def handle_pollbycategory(bot, update):
    update.callback_query.answer()
    category = update.callback_query.data.split(";")[1]
    if category == "stop":
        bot.send_message(
            chat_id=update.callback_query.message.chat_id,
            text='Okay, hier ist nichts passiert.',
            reply_markup=ReplyKeyboardRemove())
    elif category == "IGNORE":
        pass
    else:  # got a category
        plan = GameNight()
        check = plan.set_poll(update.callback_query.from_user.username,
                            category=category)
        if check < 0:
            bot.send_message(
                        chat_id=update.callback_query.message.chat_id,
                        text='Das war leider nichts. \n'
                             'Habt ihr kein Datum festgelegt? '
                             'Holt das mit /neuertermin nach.\n'
                             'Vielleicht hast du dich auch '
                             'einfach nicht angemeldet? Hole das '
                             'mit /ich nach.',
                        reply_markup=ReplyKeyboardRemove())
        else:
            keys = []
            for o in plan.poll.options:
                keys.append([KeyboardButton(o)])
            bot.send_message(
                        chat_id=update.callback_query.message.chat_id,
                        text='Welches Spiel wollt ihr spielen?',
                        reply_markup=ReplyKeyboardMarkup(
                                        keys, one_time_keyboard=True))


def generate_pollbycategory():
    keyboard = []
    config = configparser.ConfigParser(converters={'list': lambda x: [i.strip() for i in x.split(',')]})
    config_path = os.path.dirname(os.path.realpath(__file__))
    config.read(os.path.join(config_path, "config.ini"))
    categories = config.getlist('GameCategories','categories')  # no, this is no error. getlist is created by converter above
    for cat in categories:
        row = []
        data = ";".join(["POLLBY",cat])
        row.append(InlineKeyboardButton(cat, callback_data=data))
        keyboard.append(row)
    # last row: no statement and /stop button
    row = []      
    data = ";".join(["POLLBY","IGNORE"])
    row.append(InlineKeyboardButton(' ', callback_data=data))
    data = ";".join(["POLLBY","stop"])
    row.append(InlineKeyboardButton('Abbrechen', callback_data=data))
    keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)