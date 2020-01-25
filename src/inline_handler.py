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
from calendar_export import create_ics_file
import reply_handler as rep
import database_functions as dbf
import parse_strings as ps


def handle_inline(update, context):
    if "CALENDAR" in update.callback_query.data:
        handle_calendar(update, context)
    elif "CATEGORY" in update.callback_query.data:
        handle_category(update, context)
    elif "FINDBY" in update.callback_query.data:
        handle_findbycategory(update, context)
    elif "POLLBY" in update.callback_query.data:
        handle_pollbycategory(update, context)
    elif "SETTING" in update.callback_query.data:
        handle_settings(update, context)


def handle_calendar(update, context):
    selected, date, user_inp_req = telegramcalendar.process_calendar_selection(update, context)
    if selected:
        if user_inp_req:
            msg = context.bot.send_message(
                chat_id=update.callback_query.message.chat_id,
                text='Okay, wann wollt ihr spielen?',
                reply_markup=ForceReply())
            rep.ForceReplyJobs().add(msg.message_id, "date")
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
                filename = create_ics_file("Spieleabend", date)
                GameNight(chat_id=update.callback_query.message.chat_id).set_cal_file(filename)
                context.bot.send_message(
                    chat_id=update.callback_query.message.chat_id,
                    text="Okay, schrei einfach /ich, wenn du "
                         "teilnehmen willst!",
                    reply_markup=ReplyKeyboardRemove())


def handle_category(update, context):
    update.callback_query.answer()
    category = update.callback_query.data.split(";")[1]
    if category == "none":
        end_of_categories(bot, update, no_category=True)
    elif category == "stop":
        QueryBuffer().clear_query(update.callback_query.message.message_id)
        context.bot.send_message(
            chat_id=update.callback_query.message.chat_id,
            text='Okay, hier ist nichts passiert.',
            reply_markup=ReplyKeyboardRemove())
    elif category == "done":
        end_of_categories(update, context)
    elif category == "IGNORE":
        pass
    else:  # we actually got a category, now register it
        if update.callback_query.data.split(";")[2] == "SET":
            query = QueryBuffer().get_query(update.callback_query.message.message_id) + category + "/"
            categories_so_far = ps.parse_csv(query)[-1].split('/')[:-1]  # last one is empty since set ends on /
            QueryBuffer().edit_query(update.callback_query.message.message_id, query)
            # change keyboard layout
            try:
                context.bot.edit_message_text(text=update.callback_query.message.text,
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
                context.bot.edit_message_text(text=update.callback_query.message.text,
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
                context.bot.send_message(
                    chat_id=update.callback_query.message.chat_id,
                    text="Wusste ich doch: Das Spiel hast du schon "
                         "einmal eingetragen. Viel Spaß noch damit!",
                    reply_markup=ReplyKeyboardRemove())
                return
        dbf.add_game_into_db(ps.parse_values_from_array(
                                ps.remove_first_string(query)))
        context.bot.send_message(
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


def handle_findbycategory(update, context):
    update.callback_query.answer()
    category = update.callback_query.data.split(";")[1]
    if category == "stop":
        context.bot.send_message(
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
            context.bot.send_message(
                        chat_id=update.callback_query.message.chat_id,
                        text='Wie wäre es mit ' + game + '?',
                        reply_markup=ReplyKeyboardRemove())
        else:
            context.bot.send_message(
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


def handle_pollbycategory(update, context):
    update.callback_query.answer()
    category = update.callback_query.data.split(";")[1]
    if category == "stop":
        context.bot.send_message(
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
            context.bot.send_message(
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
            context.bot.send_message(
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


def handle_settings(update, context):
    update.callback_query.answer()
    setting = update.callback_query.data.split(";")[1]
    if setting == "stop":
        QueryBuffer().clear_query(update.callback_query.message.message_id)
        context.bot.send_message(
            chat_id=update.callback_query.message.chat_id,
            text='Okay, hier ist nichts passiert.',
            reply_markup=ReplyKeyboardRemove())
    elif setting == "done":
        end_of_settings(update, context)
    else:  # we actually got a setting, now register it
        if update.callback_query.data.split(";")[2] == "SET":
            query = QueryBuffer().get_query(update.callback_query.message.message_id) + setting + "/"
            settings_so_far = ps.parse_csv(query)[-1].split('/')[:-1]  # last one is empty since set ends on /
            QueryBuffer().edit_query(update.callback_query.message.message_id, query)
            # change keyboard layout
            try:
                context.bot.edit_message_text(text=update.callback_query.message.text,
                                    chat_id=update.callback_query.message.chat_id,
                                    message_id=update.callback_query.message.message_id,
                                    reply_markup=generate_settings(to_set=settings_so_far))
            except BadRequest:
                pass
        elif update.callback_query.data.split(";")[2] == "UNSET":
            query = QueryBuffer().get_query(update.callback_query.message.message_id)
            query_csv = ps.parse_csv(query)
            settings_so_far = query_csv[-1].split('/')[:-1]
            settings_so_far.remove(setting)
            settings_string = '/'.join(settings_so_far)
            if len(settings_string) > 0:
                settings_string += '/'
            new_query = ps.csv_to_string(query_csv[:-1]) + ',' + settings_string
            QueryBuffer().edit_query(update.callback_query.message.message_id, new_query)
            # change keyboard layout
            try:
                context.bot.edit_message_text(text=update.callback_query.message.text,
                                    chat_id=update.callback_query.message.chat_id,
                                    message_id=update.callback_query.message.message_id,
                                    reply_markup=generate_settings(to_set=settings_so_far))
            except BadRequest:
                pass


def end_of_settings(update, context):
    query = QueryBuffer().get_query(update.callback_query.message.message_id)
    # query looks like: setting,username,notify_participation/notify_vote/
    possible_settings = ['notify_participation', 'notify_vote']
    if ps.parse_csv(query)[0] == "settings":
        to_set = ps.parse_csv(query)[-1].split('/')[:-1]
        to_unset = []
        for _ in possible_settings:
            if _ not in to_set:
                to_unset.append(_)
        user = ps.parse_csv(query)[1]
        dbf.update_settings(user, to_set, to_unset)
        context.bot.send_message(
                    chat_id=update.callback_query.message.chat_id,
                    text="Okay, ich habe mir deine Einstellungen vermerkt.",
                    reply_markup=ReplyKeyboardRemove())
    else:
        pass
    QueryBuffer().clear_query(
        update.callback_query.message.message_id)


# when generated the first time, set "first" and "user" to look up the current settings
# also, store in init_array the settings already set to initialize query buffer
# later, just keep track of what the user selected up until now
def generate_settings(to_set=None, first=None, user=None, init_array=None):
    if first:
        current_settings = dbf.search_single_entry(dbf.choose_database("testdb"), "settings", "user", user)[0][1:]   
    keyboard = []
    settings = {'Benachrichtigung bei Teilnahme am Spieleabend' : 'notify_participation', 'Benachrichtigung bei Abstimmung' : 'notify_vote'}
    if first:
        index = 0
        for (key, value) in settings.items():
            row = []
            if current_settings[index]==1:
                data = ";".join(["SETTING",value,"UNSET"])
                label = key + " ✓"
                row.append(InlineKeyboardButton(label, callback_data=data))
                # init query buffer
                init_array.append(value)
            else:
                data = ";".join(["SETTING",value,"SET"])
                row.append(InlineKeyboardButton(key, callback_data=data))
            keyboard.append(row)
            index += 1
    else:
        for (key, value) in settings.items():
            row = []
            if to_set and (value in to_set):
                data = ";".join(["SETTING",value,"UNSET"])
                label = key + " ✓"
                row.append(InlineKeyboardButton(label, callback_data=data))
            else:
                data = ";".join(["SETTING",value,"SET"])
                row.append(InlineKeyboardButton(key, callback_data=data))
            keyboard.append(row)
    # last row: done and /stop button
    row = []
    data = ";".join(["SETTING","done"])
    row.append(InlineKeyboardButton('Fertig', callback_data=data))        
    data = ";".join(["SETTING","stop"])
    row.append(InlineKeyboardButton('Abbrechen', callback_data=data))
    keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)